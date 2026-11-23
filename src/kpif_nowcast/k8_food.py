"""K8: a model for the food component (SCB TAB6628 contribution), variants V1-V4.

Preregistered in docs/auto2/k8/hypotes.md. Target = food contribution minus its seasonal + 12-month
trend base (the same base as in J2 V2 and the live model). The predicted residual c_hat is added to J2 V2's
food part; in y/y that is k * c_hat with k = index(t-1)/index(t-12). Totals:

- k8_fixed, k8_ridge, k8_ridge_nr: 0.5*rb_updated + 0.5*(j2 + k*c_hat) = avg + 0.5*k*c_hat (reference 50/50)
- k8_ens_ridge: k2_avg_ens_s + 0.5*k*c_hat(k8_ridge) (reference k2_avg_ens_s)

Information set for target t (deadline = day 4 of t+1): food contributions up to t-1, every driver as known
at the deadline via observations.as_of (PPI to t-1, IMF/FRED to t-2, NIER and KIX to t), SEK/USD monthly
means of complete months. Training rows s < t are built the same way, from what was known at deadline(s).

Run: python -m kpif_nowcast.k8_food
"""

from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

from kpif_nowcast import observations as obsmod
from kpif_nowcast.baselines import seasonal_trend_additive
from kpif_nowcast.riksbank_benchmark import deadline

TRAIN_START = "2005-01"
MIN_TRAIN = 36
IMF_KEYS = ["wheat_usd", "beef_usd", "pork_usd", "poultry_usd", "sugar_usd", "coffee_usd", "cocoa_usd",
            "palm_oil_usd", "soy_oil_usd", "rapeseed_oil_usd", "sunflower_oil_usd"]
# driver -> (first lag, revised). Six lags from the first one: the six most recent available months.
DRIVERS = {
    "ppi_hm": (1, True),
    "ppi_imp": (1, True),
    "cmd_sek": (2, True),
    "kix": (0, False),
    "ki_groc": (0, False),
    "ki_food": (0, False),
}
SOURCE = {"ppi_hm": "ppi_hmpi_food", "ppi_imp": "ppi_impi_food", "kix": "kix",
          "ki_groc": "ki_prices_grocery", "ki_food": "ki_prices_food_industry"}
LEVEL = {"ki_groc", "ki_food"}  # net balances: levels; the rest 100*dlog m/m
N_LAGS = 6
VARIANTS = ["k8_fixed", "k8_ridge", "k8_ridge_nr", "k8_ens_ridge"]
REFERENCE = {"k8_fixed": "avg_5050", "k8_ridge": "avg_5050", "k8_ridge_nr": "avg_5050",
             "k8_ens_ridge": "k2_avg_ens_s"}
FOOD_SOURCE = {"k8_fixed": "k8_fixed", "k8_ridge": "k8_ridge", "k8_ridge_nr": "k8_ridge_nr",
               "k8_ens_ridge": "k8_ridge"}
REVISED_VARIANTS = {"k8_fixed", "k8_ridge", "k8_ens_ridge"}


# ------------------------------------------------------------------ inputs


def sekusd_daily() -> pd.Series:
    """Riksbank SEK per USD daily fixings from the newest raw cache (no download)."""
    from kpif_nowcast.sources import rawcache
    from kpif_nowcast.sources.riksbank import RAW_DIR

    payload = json.loads(rawcache.require(RAW_DIR, "riksbank_SEKUSDPMI").read_text(encoding="utf-8"))
    return pd.Series({pd.Timestamp(o["date"]): float(o["value"]) for o in payload}).sort_index()


def _dlog(s: pd.Series) -> pd.Series:
    s = s.sort_index()
    s = s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="M"))
    return 100 * np.log(s).diff()


def driver_series(when: pd.Timestamp, tables: dict[str, pd.DataFrame], fx_daily: pd.Series) -> dict[str, pd.Series]:
    """Transformed driver series (index Period[M]) as known on `when`."""
    out = {}
    for name, key in SOURCE.items():
        s = obsmod.as_of(key, when, tables.get(key, pd.DataFrame(columns=obsmod.COLUMNS)))
        out[name] = s if name in LEVEL else (_dlog(s) if len(s) else s)
    imf = [_dlog(s) for k in IMF_KEYS
           if len(s := obsmod.as_of(k, when, tables.get(k, pd.DataFrame(columns=obsmod.COLUMNS))))]
    fx = fx_daily[fx_daily.index <= when]
    g = fx.groupby(fx.index.to_period("M"))
    m = g.mean()
    ends = (m.index + 1).to_timestamp()  # first day after the month: complete month known then
    fxm = m[ends <= when]
    if imf and len(fxm) > 1:
        usd = pd.concat(imf, axis=1).mean(axis=1)
        out["cmd_sek"] = (usd + _dlog(fxm).reindex(usd.index)).dropna()
    else:
        out["cmd_sek"] = pd.Series(dtype=float)
    return out


def _lagmean(s: pd.Series, t: pd.Period, lo: int, n: int) -> float:
    vals = [s.get(t - L, np.nan) for L in range(lo, lo + n)]
    return float(np.mean(vals)) if not np.isnan(vals).any() else np.nan


def row_features(t: pd.Period, drv: dict[str, pd.Series]) -> dict[str, float]:
    """Ridge features (lags + 12-month means) and fixed 'acceleration' features for target t."""
    f = {}
    for name, (lo, _) in DRIVERS.items():
        s = drv[name]
        for L in range(lo, lo + N_LAGS):
            f[f"{name}_l{L}"] = float(s.get(t - L, np.nan))
        f[f"{name}_m12"] = _lagmean(s, t, lo, 12)
        short = 3 if name in ("ppi_hm", "ppi_imp", "ki_groc", "ki_food") else 6
        f[f"fx_{name}"] = _lagmean(s, t, lo, short) - f[f"{name}_m12"]
    return f


def build_food_design(kpif: pd.DataFrame, comps: pd.DataFrame, obs: pd.DataFrame, fx_daily: pd.Series,
                      last: pd.Period | None = None) -> pd.DataFrame:
    """One row per month TRAIN_START..last: food contribution, base, residual, k, and features at deadline."""
    effects = comps.pivot(index="month", columns="component", values="effect_month")
    effects = effects.reindex(pd.period_range(effects.index.min(), effects.index.max() + 1, freq="M"))
    base = seasonal_trend_additive(effects["food"])
    last = last or effects.index.max()
    months = pd.period_range(TRAIN_START, last, freq="M")
    keys = set(SOURCE.values()) | set(IMF_KEYS)
    tables = {k: g for k, g in obs[obs["series"].isin(keys)].groupby("series")}
    rows = {t: row_features(t, driver_series(deadline(t), tables, fx_daily)) for t in months}
    d = pd.DataFrame(rows).T
    d.index = pd.PeriodIndex(d.index, freq="M")
    d.insert(0, "food", effects["food"].reindex(months))
    d.insert(1, "base", base.reindex(months))
    d.insert(2, "resid", d["food"] - d["base"])
    idx = kpif["index"]
    idx = idx.reindex(pd.period_range(idx.index.min(), max(idx.index.max(), last), freq="M"))
    d.insert(3, "k", (idx.shift(1) / idx.shift(12)).reindex(months))
    return d


def ridge_cols(nr: bool = False) -> list[str]:
    return [f"{n}_{s}" for n, (lo, rev) in DRIVERS.items() if not (nr and rev)
            for s in [*(f"l{L}" for L in range(lo, lo + N_LAGS)), "m12"]]


FIXED_COLS = [f"fx_{n}" for n in DRIVERS]


# ------------------------------------------------------------------ estimation


def correction_at(d: pd.DataFrame, i: int, variant: str) -> tuple[float, dict]:
    """Predicted food residual for row i, fitted on rows < i with a published contribution."""
    from kpif_nowcast.k2_ml import fit_nested

    y_all = d["resid"].to_numpy(dtype=float)
    past = np.arange(i)[~np.isnan(y_all[:i])]
    if variant == "k8_fixed":
        X = d[FIXED_COLS].to_numpy(dtype=float)
        ok = past[~np.isnan(X[past]).any(axis=1)]
        if len(ok) < MIN_TRAIN or np.isnan(X[i]).any():
            return 0.0, {}
        A = np.column_stack([np.ones(len(ok)), X[ok]])
        coef = np.linalg.lstsq(A, y_all[ok], rcond=None)[0]
        return float(np.r_[1.0, X[i]] @ coef), dict(zip(["const", *FIXED_COLS], coef))
    cols = ridge_cols(nr=variant == "k8_ridge_nr")
    if len(past) < MIN_TRAIN:
        return 0.0, {}
    X = d[cols].to_numpy(dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model, params = fit_nested("ridge", X[past], y_all[past])
        est = model[-1]
        info = {"alpha": params["alpha"], "intercept": est.intercept_, **dict(zip(cols, est.coef_))}
        return float(model.predict(X[[i]])[0]), info


def corrections(d: pd.DataFrame, months: pd.PeriodIndex, variants=("k8_fixed", "k8_ridge", "k8_ridge_nr"),
                keep_info: bool = False):
    out, info = {}, {}
    for t in months:
        i = d.index.get_loc(t)
        row = {}
        for v in variants:
            row[v], inf = correction_at(d, i, v)
            if keep_info:
                info[(v, t)] = inf
        out[t] = row
    res = pd.DataFrame(out).T
    res.index = pd.PeriodIndex(res.index, freq="M")
    return (res, info) if keep_info else res


def totals(avg: pd.Series, k: pd.Series, corr: pd.DataFrame, ens: pd.Series | None = None) -> pd.DataFrame:
    """Total y/y forecasts per variant: reference + 0.5 * k * c_hat."""
    out = pd.DataFrame(index=corr.index)
    for v in VARIANTS:
        if v == "k8_ens_ridge" and ens is None:
            continue
        ref = ens if v == "k8_ens_ridge" else avg
        out[v] = ref.reindex(corr.index) + 0.5 * k.reindex(corr.index) * corr[FOOD_SOURCE[v]]
    return out


def forecast_at(kpif, comps, obs, fx_daily, panel: pd.DataFrame, t: pd.Period) -> dict[str, float]:
    """Live-style forecast for t (V1-V3 totals and the food corrections), from inputs as given."""
    d = build_food_design(kpif, comps, obs, fx_daily, last=t)
    c = corrections(d, pd.PeriodIndex([t]))
    avg = 0.5 * panel["rb_updated"] + 0.5 * panel["j2"]
    tot = totals(avg, d["k"], c)
    return {**{f"c_{v}": c.at[t, v] for v in c.columns}, **{v: tot.at[t, v] for v in tot.columns}}


# ------------------------------------------------------------------ evaluation


def main() -> None:
    from pathlib import Path

    from kpif_nowcast.data import load_components, load_el_contracts, load_kpif, load_riksbank_forecasts
    from kpif_nowcast.evaluation import dm_test, log_run
    from kpif_nowcast.features import load_features
    from kpif_nowcast.j1_hybrid import build_panel, dm_one_sided
    from kpif_nowcast.j2_el import holm, zone_monthly_spot
    from kpif_nowcast.k2_ml import K2Runner, build_design

    warnings.filterwarnings("ignore")
    kpif, comps, feats, contracts = load_kpif(), load_components(), load_features(), load_el_contracts()
    se3, rb_fc, obs = zone_monthly_spot("SE3"), load_riksbank_forecasts(), obsmod.load()
    fx = sekusd_daily()

    d = build_food_design(kpif, comps, obs, fx, last=pd.Period("2026-10", "M"))
    months = pd.period_range("2015-01", "2026-10", freq="M")
    corr, info = corrections(d, months, keep_info=True)
    print("corrections done", flush=True)

    design = build_design(kpif, comps, feats, contracts, se3, rb_fc, obs, with_catalog=False)
    run = K2Runner(design)
    ens = run.series("k2_avg_ens_s")
    print("k2 ens done", flush=True)
    panel = build_panel(kpif, comps, feats, contracts, se3, rb_fc, obs)
    avg = (0.5 * panel["rb_updated"] + 0.5 * panel["j2"]).rename("avg_5050")
    tot = totals(avg, d["k"], corr, ens)
    preds = pd.concat([avg, ens.rename("k2_avg_ens_s"), panel["rb_updated"], panel["j2"]], axis=1).join(tot, how="inner")
    actual = panel["actual"]

    lines, log_rows = [], []
    screen = {}
    for label, start, end in [("2015-02..2026-10 (primary)", "2015-02", "2026-10"),
                              ("2024-01..2026-10 (used, report only)", "2024-01", "2026-10")]:
        p = preds.loc[pd.Period(start, "M"): pd.Period(end, "M")]
        p = p[actual.reindex(p.index).notna()].dropna()
        err = p.sub(actual.reindex(p.index), axis=0)
        tab = pd.DataFrame({"MAE": err.abs().mean(), "RMSE": np.sqrt((err ** 2).mean()), "bias": err.mean(),
                            "n": err.count()})
        raw = {v: dm_one_sided(err[v].to_numpy(), err[REFERENCE[v]].to_numpy())[1] for v in VARIANTS}
        h = holm(raw)
        for v in VARIANTS:
            tab.loc[v, "reference"] = REFERENCE[v]
            tab.loc[v, "diff_ref"] = tab.loc[v, "MAE"] - tab.loc[REFERENCE[v], "MAE"]
            tab.loc[v, "p1_ref"] = raw[v]
            tab.loc[v, "holm_ref"] = h[v]
            tab.loc[v, "p1_rb_updated"] = dm_one_sided(err[v].to_numpy(), err["rb_updated"].to_numpy())[1]
        screen[label] = tab
        for m, row in tab.iterrows():
            log_rows.append({"variant": m, "period": label, "n": int(row["n"]), "MAE": round(row["MAE"], 4),
                             "dm_p_vs_rb_updated": round(row.get("p1_rb_updated", float("nan")), 4)})
        lines.append(f"## Total KPIF y/y, {label} (n={len(p)}; DM one-sided, H1: lower MAE than reference; "
                     f"Holm over 4)\n\n{tab.round(3).to_markdown()}\n")
        print(f"\n{label}\n{tab.round(3)}", flush=True)

    # per year: diff vs reference
    p = preds.loc["2015-02":"2026-10"]
    p = p[actual.reindex(p.index).notna()].dropna()
    ae = p.sub(actual.reindex(p.index), axis=0).abs()
    yr = ae.groupby(ae.index.year).mean()
    per_year = pd.DataFrame({"n": ae.groupby(ae.index.year).size(), "MAE 50/50": yr["avg_5050"],
                             "MAE k2_ens": yr["k2_avg_ens_s"],
                             **{f"diff {v}": yr[v] - yr[REFERENCE[v]] for v in VARIANTS}})
    lines.append(f"## Per year, total MAE and diff vs reference\n\n{per_year.round(3).to_markdown()}\n")
    print(per_year.round(3), flush=True)

    # food component's own error
    food = d.loc[months]
    fe = pd.DataFrame({"base": food["base"] - food["food"],
                       **{v: food["base"] + corr[v] - food["food"] for v in corr.columns}}).dropna()
    rows = {}
    for label, a, b in [("2015-2026", "2015-01", "2026-10"), ("2015-2019", "2015-01", "2019-12"),
                        ("2020-2021", "2020-01", "2021-12"), ("2022-2023", "2022-01", "2023-12"),
                        ("2024-2026 (used)", "2024-01", "2026-10"), ("2015-2026 excl. 2026-04", "2015-01", "2026-10")]:
        e = fe.loc[a:b]
        if "excl" in label:
            e = e.drop(pd.Period("2026-04", "M"))
        r = {"n": len(e), **{f"MAE {c}": e[c].abs().mean() for c in fe}}
        kk = food["k"].reindex(e.index)
        r.update({f"MAE_yy {c}": (e[c] * kk).abs().mean() for c in fe})
        for v in corr.columns:
            r[f"p1 {v} vs base"] = dm_one_sided(e[v].to_numpy(), e["base"].to_numpy())[1]
        rows[label] = r
    food_tab = pd.DataFrame(rows).T
    lines.append("## Food contribution's own error (pp of KPIF m/m; MAE_yy = k * error, comparable to K3 table 2)\n\n"
                 f"{food_tab.round(4).to_markdown()}\n")
    print(food_tab.round(4).T, flush=True)
    fy = fe.abs().groupby(fe.index.year).mean()
    lines.append(f"## Food contribution MAE per year (pp m/m)\n\n{fy.round(4).to_markdown()}\n")

    # coefficients: fixed variant at the end of selected years, ridge alpha path
    coef_rows = {}
    for t in [pd.Period(f"{y}-12", "M") for y in (2016, 2019, 2022, 2025)] + [pd.Period("2026-10", "M")]:
        coef_rows[str(t)] = info[("k8_fixed", t)]
    lines.append(f"## k8_fixed OLS coefficients (window ending before t)\n\n{pd.DataFrame(coef_rows).round(4).to_markdown()}\n")
    for v in ("k8_ridge", "k8_ridge_nr"):
        rp = pd.DataFrame({t: info[(v, pd.Period(t, "M"))] for t in coef_rows})
        rp.index = rp.index.astype(str)
        top = rp.drop(index=["alpha", "intercept"]).iloc[:, -1].abs().sort_values(ascending=False).index[:12]
        lines.append(f"## {v}: alpha and top-12 raw coefficients (standardised features)\n\n"
                     f"{rp.loc[['alpha', 'intercept', *top]].round(4).to_markdown()}\n")
        alphas = pd.Series([info[(v, t)].get("alpha") for t in months]).value_counts()
        lines.append(f"Chosen alpha, {v} (count of windows): {alphas.to_dict()}\n")
    # correction sizes, two-sided check ridge_nr vs ridge
    lines.append("## Correction size (|0.5*k*c_hat|, pp y/y), 2015-2026\n\n"
                 f"{(0.5 * d['k'].reindex(months).to_numpy()[:, None] * corr).abs().describe().round(4).to_markdown()}\n")
    p = preds.loc["2015-02":"2026-10"]
    p = p[actual.reindex(p.index).notna()].dropna()
    err = p.sub(actual.reindex(p.index), axis=0)
    two = dm_test(err["k8_ridge_nr"].to_numpy(), err["k8_ridge"].to_numpy())
    lines.append(f"Two-sided DM k8_ridge_nr vs k8_ridge (2015-02..2026-10): diff {two.mean_diff:+.4f}, p = {two.p:.3f}\n")

    path = log_run("k8_food", log_rows)
    lines.append(f"Run log: `{path.name}`\n")
    root = Path(__file__).resolve().parents[2]
    out = root / "docs" / "auto2" / "k8"
    out.mkdir(parents=True, exist_ok=True)
    (out / "results_raw.md").write_text("# K8 raw results (generated by `python -m kpif_nowcast.k8_food`)\n\n"
                                        + "\n".join(lines), encoding="utf-8")
    (root / "outputs").mkdir(exist_ok=True)
    preds.join(actual).join(corr.add_prefix("c_")).to_csv(root / "outputs" / "k8_preds.csv")


if __name__ == "__main__":
    main()
