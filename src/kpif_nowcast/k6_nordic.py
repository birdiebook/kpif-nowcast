"""K6: two "only if easy" checks. Preregistered in docs/auto2/k6/hypotes.md.

Part 1 (no variant): how much did the back-calculation to COICOP 2018 change Swedish price groups?
    Eurostat keeps the old HICP dataset (prc_hicp_midx, ECOICOP 1, frozen at 2025-12) next to the new one
    (prc_hicp_minr, COICOP 2018, back-calculated). Comparing them group by group is the closest open
    substitute for vintages of SCB's TAB6613 detail, which do not exist before 2026.

Part 2 (variants N1, N2): J2 V2's electricity method on Finnish and Danish HICP, with coupled Swedish
    bidding zones as spot proxies (SE3 for FI, SE4 for DK).

Information set for target t (part 2): HICP up to t-1, spot price and Brent for t.

Run: python -m kpif_nowcast.k6_nordic
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from kpif_nowcast.baselines import naive_yy, seasonal_trend_additive, yy_from_mm
from kpif_nowcast.component_model import Correction, fit_correction
from kpif_nowcast.sources import rawcache
from kpif_nowcast.sources.eurostat import BASE_URL, _frame

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "k6"
TRAIN_START = "2012-01"
SEASON_YEARS = 5
FUEL_LAST_DAY = 25
VARIANTS = {"k6_fi_el_dev": ("FI", "SE3"), "k6_dk_el_dev": ("DK", "SE4")}
REFERENCE = "seasonal_trend_5y"
EVAL_END = "2026-10"


# ---------- data ----------

def fetch_eurostat(dataset: str, **filters: str) -> pd.DataFrame:
    """Like sources.eurostat.fetch, but cached under data/raw/k6/ and with 3 tries + backoff."""
    tag = hashlib.md5(json.dumps([dataset, filters], sort_keys=True).encode()).hexdigest()[:6]
    hits = sorted(RAW_DIR.glob(f"eurostat_{dataset}_{tag}_*.json"))
    if hits:
        return _frame(json.loads(hits[-1].read_text(encoding="utf-8")))
    if rawcache.offline():
        raise FileNotFoundError(f"offline and no cache for {dataset} {filters}")
    for attempt in range(3):
        try:
            resp = requests.get(f"{BASE_URL}/{dataset}", params={"format": "JSON", "lang": "EN", **filters},
                                timeout=180)
            resp.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(5 * 2 ** attempt)
    payload = resp.json()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"eurostat_{dataset}_{tag}_{date.today():%Y%m%d}.json").write_text(json.dumps(payload),
                                                                                  encoding="utf-8")
    return _frame(payload)


def _wide(df: pd.DataFrame, code_col: str) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.PeriodIndex(df["time"].astype(str), freq="M")
    return df.pivot(index="month", columns=code_col, values="value").sort_index()


def hicp_groups(geo: str, new: bool) -> pd.DataFrame:
    """All HICP sub-indices (2015=100) for one country, old (ECOICOP 1) or new (COICOP 2018) dataset."""
    if new:
        return _wide(fetch_eurostat("prc_hicp_minr", geo=geo, unit="I15"), "coicop18")
    return _wide(fetch_eurostat("prc_hicp_midx", geo=geo, unit="I15"), "coicop")


def hicp_total(geo: str) -> pd.Series:
    df = fetch_eurostat("prc_hicp_minr", geo=geo, unit="I15", coicop18="TOTAL")
    return _wide(df, "coicop18")["TOTAL"].rename(geo)


def hicp_total_old(geo: str) -> pd.Series:
    df = fetch_eurostat("prc_hicp_midx", geo=geo, unit="I15", coicop="CP00")
    return _wide(df, "coicop")["CP00"].rename(geo)


def eur_spot_monthly(zone: str, last_day: date = date(2026, 10, 31)) -> pd.Series:
    """Monthly mean spot price (EUR/kWh) for a Swedish zone, complete months only."""
    from kpif_nowcast.j2_el import zone_monthly_spot
    from kpif_nowcast.sources import riksbank

    sek = zone_monthly_spot(zone, last_day)
    fx = riksbank.fetch_swea("SEKEURPMI")
    fx_m = fx.groupby(pd.DatetimeIndex(fx.index).to_period("M")).mean()
    return (sek / fx_m.reindex(sek.index)).dropna().rename(zone)


def brent_eur_monthly() -> pd.Series:
    """Brent in EUR per barrel, mean of trading days 1-25 (same window as features.fuel_proxy_daily)."""
    from kpif_nowcast.sources import fred, riksbank

    brent = fred.fetch_series("DCOILBRENTEU")
    usd, eur = riksbank.fetch_swea("SEKUSDPMI"), riksbank.fetch_swea("SEKEURPMI")
    df = pd.concat([brent, usd, eur], axis=1, sort=True).dropna()
    df = df[pd.DatetimeIndex(df.index).day <= FUEL_LAST_DAY]
    eur_price = df["DCOILBRENTEU"] * df["SEKUSDPMI"] / df["SEKEURPMI"]
    return eur_price.groupby(pd.DatetimeIndex(eur_price.index).to_period("M")).mean().rename("brent_eur")


# ---------- part 2: model ----------

def same_month_dev(x: pd.Series, years: int = SEASON_YEARS) -> pd.Series:
    lags = pd.concat([x.shift(12 * k) for k in range(1, years + 1)], axis=1)
    return x - lags.mean(axis=1)


def regressors(spot_eur: pd.Series, brent_eur: pd.Series) -> pd.DataFrame:
    """fuel_chg (log change of Brent EUR) and el_dev (EUR/kWh change minus same-month mean). Rows <= t only."""
    idx = spot_eur.index.union(brent_eur.index)
    out = pd.DataFrame(index=idx)
    out["fuel_chg"] = np.log(brent_eur.reindex(idx)).diff()
    out["el_chg"] = spot_eur.reindex(idx).diff()
    out["el_dev"] = same_month_dev(out["el_chg"])
    return out


def nordic_forecast(index: pd.Series, regs: pd.DataFrame) -> pd.DataFrame:
    """Seasonal+trend baseline on HICP m/m (%) and the same plus J2-style correction. y/y forecasts."""
    index = index.dropna()
    full = pd.period_range(index.index.min(), index.index.max() + 1, freq="M")
    idx = index.reindex(full)
    mm = idx.pct_change(fill_method=None) * 100
    base = seasonal_trend_additive(mm)
    corr = fit_correction(mm - base, regs, Correction(["fuel_chg", "el_dev"], TRAIN_START))
    out = pd.DataFrame(index=full)
    out["mm_base"] = base
    out["mm_hat"] = (base + corr["correction"].reindex(full))
    out[REFERENCE] = yy_from_mm(idx, out["mm_base"] / 100)
    out["variant"] = yy_from_mm(idx, out["mm_hat"] / 100)
    out["naive_yy"] = naive_yy(idx)
    out["actual"] = (idx / idx.shift(12) - 1) * 100
    return out.join(corr.drop(columns="correction"))


def holm(pvals: dict[str, float]) -> dict[str, float]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, running, out = len(items), 0.0, {}
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


# ---------- part 1: revision check ----------

def _mm(df: pd.DataFrame) -> pd.DataFrame:
    return df.pct_change(fill_method=None) * 100


def compare(a: pd.Series, b: pd.Series) -> dict:
    x = pd.concat([a, b], axis=1).dropna()
    if len(x) < 24:
        return {"n": len(x), "corr": np.nan, "mad_pp": np.nan, "max_pp": np.nan}
    d = (x.iloc[:, 0] - x.iloc[:, 1]).abs()
    return {"n": len(x), "corr": x.iloc[:, 0].corr(x.iloc[:, 1]), "mad_pp": d.mean(), "max_pp": d.max()}


def revision_check(start: str = "2001-01", end: str = "2025-12") -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Old vs new Swedish HICP groups (m/m %), TAB6613 vs old HICP for energy groups, TAB6613 sum check."""
    from kpif_nowcast.data import load_cpif_detail, load_kpif

    sl = slice(pd.Period(start, "M"), pd.Period(end, "M"))
    old, new = _mm(hicp_groups("SE", new=False)).loc[sl], _mm(hicp_groups("SE", new=True)).loc[sl]
    rows = {}
    for code in sorted(set(old.columns) & set(new.columns)):
        if not code.startswith("CP"):
            continue
        rows[code] = {"digits": len(code) - 2, **compare(old[code], new[code])}
    groups = pd.DataFrame(rows).T.dropna(subset=["corr"])

    detail = load_cpif_detail()
    tab = detail[detail["level"] == 2].pivot(index="month", columns="coicop", values="index")
    tab_mm = _mm(tab).loc[sl]
    energy = {}
    for code in ["04.5", "07.2"]:
        hc = "CP" + code.replace(".", "")
        energy[f"TAB6613 {code} vs HICP old {hc}"] = compare(tab_mm[code], old[hc])
        energy[f"HICP new {hc} vs HICP old {hc}"] = compare(new[hc], old[hc])
    energy = pd.DataFrame(energy).T

    eff_sum = detail[detail["level"] == 2].groupby("month")["effect_month"].sum()
    kpif_mm = load_kpif()["index"].pct_change(fill_method=None) * 100
    d = (eff_sum - kpif_mm).dropna().loc[pd.Period("1988-01", "M"):]
    sum_check = {"n": len(d), "mad_pp": float(d.abs().mean()), "max_pp": float(d.abs().max())}
    return groups, energy, sum_check


# ---------- run ----------

def main() -> None:
    from kpif_nowcast.evaluation import dm_test, log_run

    lines = ["# K6 results (raw)\n"]

    # Part 1
    groups, energy, sum_check = revision_check()
    lines.append("## Part 1: Swedish HICP old (ECOICOP 1) vs new (COICOP 2018), m/m %, 2001-2025\n")
    lines.append(f"Energy groups:\n\n{energy.round(4).to_markdown()}\n")
    for dg in [2, 3, 4]:
        g = groups[groups["digits"] == dg]
        lines.append(f"Codes with {dg} digits: {len(g)}, median corr {g['corr'].median():.4f}, "
                     f"median MAD {g['mad_pp'].median():.4f} pp, corr < 0.98: {int((g['corr'] < 0.98).sum())}\n")
    g3 = groups[groups["digits"] == 3].sort_values("corr")
    lines.append(f"3-digit groups (TAB6613 level 2), worst 15 by corr:\n\n{g3.head(15).round(4).to_markdown()}\n")
    lines.append(f"TAB6613: sum of 43 level-2 effects vs published KPIF m/m (1988-): {sum_check}\n")
    print(energy.round(4), g3.head(15).round(4), sum_check, sep="\n\n")

    # Part 2
    brent = brent_eur_monthly()
    results, raw_p, log_rows = {}, {}, []
    for name, (geo, zone) in VARIANTS.items():
        idx = hicp_total(geo)
        old = hicp_total_old(geo)
        chk = compare(_mm(idx.to_frame())[geo], _mm(old.to_frame())[geo])
        lines.append(f"## {name}: {geo}, spot proxy {zone}\n\nHICP total new vs old dataset, m/m: {chk}\n")
        res = nordic_forecast(idx, regressors(eur_spot_monthly(zone), brent))
        results[name] = res
        p = res.loc[pd.Period("2015-01", "M"): pd.Period(EVAL_END, "M"), ["variant", REFERENCE, "actual"]].dropna()
        raw_p[name] = dm_test((p["variant"] - p["actual"]).to_numpy(), (p[REFERENCE] - p["actual"]).to_numpy()).p
    holm_p = holm(raw_p)

    for name, res in results.items():
        cols = ["variant", REFERENCE, "naive_yy"]
        for label, start, end in [("2015-2026", "2015-01", EVAL_END), ("2024-2026", "2024-01", EVAL_END),
                                  ("2021-2023", "2021-01", "2023-12"), ("2015-2020", "2015-01", "2020-12")]:
            p = res.loc[pd.Period(start, "M"): pd.Period(end, "M"), [*cols, "actual"]].dropna()
            err = p[cols].sub(p["actual"], axis=0)
            mae = err.abs().mean()
            dm = dm_test(err["variant"].to_numpy(), err[REFERENCE].to_numpy()).p
            row = {"n": len(p), **{f"MAE_{c}": mae[c] for c in cols}, "diff_vs_ref": mae["variant"] - mae[REFERENCE],
                   "dm_p_raw": dm}
            if label == "2015-2026":
                row["holm_p"] = holm_p[name]
            lines.append(f"### {name} {label}\n\n{pd.Series(row).round(4).to_markdown()}\n")
            print(name, label, pd.Series(row).round(4).to_dict())
            for c in cols:
                log_rows.append({"variant": name if c == "variant" else f"{name}:{c}", "period": label,
                                 "n": len(p), "MAE": round(mae[c], 4),
                                 "dm_p_vs_rb_updated": round(dm, 4) if c == "variant" else float("nan")})
        coef = res.filter(like="b_").dropna()
        lines.append(f"Latest coefficients: {coef.iloc[-1].round(4).to_dict()}; "
                     f"2020-12: {coef.loc[pd.Period('2020-12', 'M')].round(4).to_dict()}\n")
    path = log_run("k6_nordic", log_rows)
    lines.append(f"Run log: `{path.name}` (column dm_p_vs_rb_updated holds DM p vs {REFERENCE} here)\n")
    out = ROOT / "docs" / "auto2" / "k6"
    out.mkdir(parents=True, exist_ok=True)
    (out / "results_raw.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
