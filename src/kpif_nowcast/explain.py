"""K3: explained forecasts. Per target month: contributions per KPIF component, a news decomposition
of the change from last month's outcome, the last miss, the shadow models' differences from the live
model, J5's EWMA band as uncertainty (proposal), and, once the outcome is out, the error per component.

No new model variants: everything here is an exact accounting identity over forecasts that already
exist (the live model component_fuel_el_v1, J2 V2 `j2_el_dev`, J1 C1 50/50, optionally K2's
candidate `k2_avg_ens_s`). forecast.py and forecasts/<month>.json are not touched.

Identities (k = I[t-1] / I[t-12], effects e_c in pp of KPIF m/m from TAB6628, f_c the component forecast):
    forecast m/m (pp)          = sum_c f_c,   f_c = trend_c + season_c (+ el + fuel for energy)
    yy_hat[t] - yy[t-1]         = sum_c k * (f_c[t] - e_c[t-12]) + rest
    yy_hat[t] - yy[t] (error)   = sum_c k * (f_c[t] - e_c[t])    + rest
`rest` = SCB's rounding of the effects (sum_c e_c vs the index m/m) and of the official y/y (0.1).

Information set for t: everything in section "forecast" uses KPIF/components to t-1, energy prices for
t, Riksbank vintages published before t's deadline (day 4 of t+1). The "outcome" section uses t itself
and is only filled in once t is published. Tested in tests/test_explain.py.

Run: python -m kpif_nowcast.explain [--months 24] [--no-k2] [--docs]
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from kpif_nowcast.baselines import seasonal_trend_additive
from kpif_nowcast.component_model import ENERGY, ENERGY_FUEL_ONLY, component_forecast
from kpif_nowcast.forecast import FORECAST_DIR
from kpif_nowcast.j2_el import build_j2_features, j2_forecast
from kpif_nowcast.j5_intervals import EWMA_LAMBDA, interval_for
from kpif_nowcast.riksbank_benchmark import deadline, riksbank_at_deadline
from kpif_nowcast.shadow import _NO_CONTRACTS, Inputs

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "outputs" / "explain"
DOCS_DIR = REPO / "docs" / "auto2" / "k3"
COMPONENTS = ["energy", "services", "goods", "food", "capital_stock"]
NAME_SV = {"energy": "energi", "services": "tjänster", "goods": "varor", "food": "livsmedel",
           "capital_stock": "kapitalstock"}
MONTH_SV = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september",
            "oktober", "november", "december"]
LIVE = "comp_fuel_el"
K2_NAME = "k2_avg_ens_s"
J5_METHOD = "j5_ewma"


# ------------------------------------------------------------------ model history


@dataclass
class History:
    """All forecast series and accounting pieces, computed once from one set of inputs."""

    inp: Inputs
    effects: pd.DataFrame  # TAB6628 effects per component, pp, including the unpublished next month (NaN)
    trend: pd.DataFrame  # 12-month mean of effects up to t-1
    season: pd.DataFrame  # seasonal deviation (baseline minus trend)
    live: pd.DataFrame  # component_forecast with ENERGY (live model)
    fuel_only: pd.DataFrame  # component_forecast with ENERGY_FUEL_ONLY (long history, J5's point forecast)
    j2: pd.DataFrame  # J2 V2
    j2f: pd.DataFrame
    rb: pd.DataFrame  # Riksbank at deadline incl. rb_updated
    index: pd.Series  # KPIF index, extended by one month
    yy_official: pd.Series


def build_history(inp: Inputs) -> History:
    effects = inp.comps.pivot(index="month", columns="component", values="effect_month")
    effects = effects.reindex(pd.period_range(effects.index.min(), effects.index.max() + 1, freq="M"))
    trend = effects.rolling(12).mean().shift(1)
    base = effects.apply(seasonal_trend_additive)
    season = base - trend
    index = inp.kpif["index"]
    live = component_forecast(index, inp.comps, inp.feats, {"energy": ENERGY})
    fuel_only = component_forecast(index, inp.comps, inp.feats, {"energy": ENERGY_FUEL_ONLY})
    j2f = build_j2_features(inp.feats, _NO_CONTRACTS, pd.Series(dtype=float, index=pd.PeriodIndex([], freq="M")))
    j2 = j2_forecast(index, inp.comps, j2f, "j2_el_dev")
    rb = riksbank_at_deadline(inp.rb_fc, j2.index, inp.kpif["yy_official"])
    idx = index.reindex(pd.period_range(index.index.min(), index.index.max() + 1, freq="M"))
    return History(inp, effects, trend, season, live, fuel_only, j2, j2f, rb, idx, inp.kpif["yy_official"])


def _k(h: History, t: pd.Period) -> float:
    return float(h.index[t - 1] / h.index[t - 12])


def _yy_index(h: History, t: pd.Period) -> float:
    return float((h.index[t] / h.index[t - 12] - 1) * 100)


def _mm_index_pp(h: History, t: pd.Period) -> float:
    return float((h.index[t] / h.index[t - 1] - 1) * 100)


def _fc(h: History, model: str) -> pd.DataFrame:
    return {"comp_fuel_el": h.live, "comp_fuel": h.fuel_only}[model]


def component_parts(h: History, t: pd.Period, model: str = LIVE) -> dict[str, dict]:
    """Per component: forecast m/m contribution split into trend, season and energy drivers."""
    res = _fc(h, model).loc[t]
    out = {}
    for c in COMPONENTS:
        d = {"mm_pp": float(res[f"fc_{c}"]), "trend_pp": float(h.trend.at[t, c]),
             "season_pp": float(h.season.at[t, c])}
        if c == "energy":
            for col, label in (("el_chg", "el_pp"), ("fuel_chg", "fuel_pp")):
                b = res.get(f"energy:b_{col}", np.nan)
                d[label] = float(b * h.inp.feats.at[t, col]) if pd.notna(b) else 0.0
                d[f"b_{col}"] = float(b) if pd.notna(b) else None
        out[c] = d
    return out


def error_parts(h: History, t: pd.Period, fc: dict[str, float], yy_hat: float) -> dict:
    """Error (forecast - outcome) of a component forecast for t, split per component. Needs t published."""
    k = _k(h, t)
    eff = {c: float(h.effects.at[t, c]) for c in COMPONENTS}
    actual = float(h.yy_official[t])
    parts = {c: k * (fc[c] - eff[c]) for c in COMPONENTS}
    total = yy_hat - actual
    return {"actual_yy": actual, "error_yy": total, "per_component_yy": parts,
            "actual_mm_pp": {c: eff[c] for c in COMPONENTS}, "rest_yy": total - sum(parts.values())}


def live_errors(h: History, through: pd.Period) -> pd.Series:
    """J5 convention (outcome - forecast) for months <= through: live model where it exists, comp_fuel before."""
    act = h.yy_official.loc[:through]
    live = (act - h.live["yy_hat"].reindex(act.index)).dropna()
    fuel = (act - h.fuel_only["yy_hat"].reindex(act.index)).dropna()
    first = live.index.min() if len(live) else through + 1
    return pd.concat([fuel.loc[: first - 1], live]).sort_index()


def j5_band(h: History, t: pd.Period, yy_hat: float) -> dict | None:
    """J5 U4 (EWMA-scaled empirical quantiles) around the live forecast; past errors of months <= t-1 only."""
    past = live_errors(h, t - 1)
    if len(past) < 36:
        return None
    q = interval_for(J5_METHOD, past.to_numpy(), np.empty((len(past), 0)), np.empty(0))
    return {
        "method": f"{J5_METHOD} (J5 U4, lambda={EWMA_LAMBDA})",
        "n_past": int(len(past)),
        "past_errors": f"{past.index.min()}..{past.index.max()} (comp_fuel före {h.live['yy_hat'].dropna().index.min()}, "
                       "sedan den skarpa modellen)",
        "band_50": [yy_hat + q[0.25], yy_hat + q[0.75]],
        "band_80": [yy_hat + q[0.10], yy_hat + q[0.90]],
        "band_90": [yy_hat + q[0.05], yy_hat + q[0.95]],
    }


# ------------------------------------------------------------------ explanation of one month


def explain_month(h: History, t: pd.Period, k2: dict | None = None, info: dict | None = None) -> dict:
    """Explanation of the live forecast for t. Everything except `outcome` uses only data known at t's deadline."""
    if t not in h.live.index or pd.isna(h.live.at[t, "yy_hat"]):
        raise ValueError(f"no live forecast for {t}")
    live = h.live.loc[t]
    yy_hat, mm_hat = float(live["yy_hat"]), float(live["mm_hat_pp"])
    k = _k(h, t)
    prev_yy = float(h.yy_official[t - 1])
    parts = component_parts(h, t)
    fc = {c: parts[c]["mm_pp"] for c in COMPONENTS}

    # change from last month's published y/y, per component (base effect vs the same month last year)
    last_year = {c: float(h.effects.at[t - 12, c]) for c in COMPONENTS}
    change = {c: k * (fc[c] - last_year[c]) for c in COMPONENTS}
    change_rest = (yy_hat - prev_yy) - sum(change.values())
    # same change split by driver: a normal month (trend + season, all components) vs last year's month,
    # electricity, fuel
    e = parts["energy"]
    drivers = {
        "normal_vs_last_year": k * sum(parts[c]["trend_pp"] + parts[c]["season_pp"] - last_year[c] for c in COMPONENTS),
        "el": k * e["el_pp"],
        "fuel": k * e["fuel_pp"],
    }
    drivers["rest"] = (yy_hat - prev_yy) - sum(drivers.values())

    feats = h.inp.feats
    inputs = {"el_spot_sek_kwh": float(feats.at[t, "el_spot"]), "el_chg_sek_kwh": float(feats.at[t, "el_chg"]),
              "fuel_proxy_brent_sek": float(feats.at[t, "brent_sek"]), "fuel_chg_log": float(feats.at[t, "fuel_chg"])}
    if info:
        inputs.update({k_: info[k_] for k_ in ("el_days", "fuel_last_day") if k_ in info})

    # last miss: the live model's forecast for t-1 against the outcome (published mid-month t)
    last_miss = None
    if t - 1 in h.live.index and pd.notna(h.live.at[t - 1, "yy_hat"]):
        p = component_parts(h, t - 1)
        ep = error_parts(h, t - 1, {c: p[c]["mm_pp"] for c in COMPONENTS}, float(h.live.at[t - 1, "yy_hat"]))
        last_miss = {"month": str(t - 1), "forecast_yy": float(h.live.at[t - 1, "yy_hat"]), **ep}

    # shadows
    shadows = {}
    rb = h.rb.loc[t] if t in h.rb.index else None
    if t in h.j2.index and pd.notna(h.j2.at[t, "yy_hat"]):
        j2 = h.j2.loc[t]
        j2_energy = float(j2["fc_energy"])
        j2_el = float(j2["b_el_dev"] * h.j2f.at[t, "el_dev"])
        j2_fuel = float(j2["b_fuel_chg"] * h.j2f.at[t, "fuel_chg"])
        shadows["j2_el_dev"] = {
            "forecast_yy": float(j2["yy_hat"]), "diff_vs_live_yy": float(j2["yy_hat"]) - yy_hat,
            "energy_mm_pp": j2_energy, "el_pp": j2_el, "fuel_pp": j2_fuel,
            "el_dev_sek_kwh": float(h.j2f.at[t, "el_dev"]),
            # only the energy correction differs from the live model
            "diff_from_el_yy": k * (j2_el - e["el_pp"]), "diff_from_fuel_yy": k * (j2_fuel - e["fuel_pp"]),
        }
        if rb is not None and pd.notna(rb["rb_updated"]):
            miss = float(rb["rb_updated"] - rb["riksbank"])
            avg = 0.5 * float(rb["rb_updated"]) + 0.5 * float(j2["yy_hat"])
            shadows["rb_updated"] = {"forecast_yy": float(rb["rb_updated"]), "riksbank_yy": float(rb["riksbank"]),
                                     "policy_round": str(rb["rb_round"]), "months_since_cutoff": int(rb["rb_months_ahead"]),
                                     "last_miss_pp": miss}
            shadows["j1_comb_equal"] = {
                "forecast_yy": avg, "diff_vs_live_yy": avg - yy_hat,
                # 50/50 - live = 0.5 (RB_t - live) + 0.5 last RB miss + 0.5 (J2 - live)
                "from_riksbank_path": 0.5 * (float(rb["riksbank"]) - yy_hat),
                "from_last_rb_miss": 0.5 * miss,
                "from_j2": 0.5 * (float(j2["yy_hat"]) - yy_hat),
            }
    if k2 is not None:
        shadows[K2_NAME] = k2

    out = {
        "target_month": str(t),
        "deadline": deadline(t).date().isoformat(),
        "model": "component_fuel_el_v1",
        "information_set": {"kpif_through": str(t - 1), "energy_prices_for": str(t),
                            "riksbank_vintage": str(rb["rb_round"]) if rb is not None else None},
        "forecast": {"yy": yy_hat, "mm_pp": mm_hat, "last_known_month": str(t - 1), "last_known_yy": prev_yy,
                     "change_yy": yy_hat - prev_yy, "k_index_ratio": k},
        "components": {c: {**parts[c], "same_month_last_year_pp": last_year[c], "change_yy": change[c]}
                       for c in COMPONENTS},
        "change_rest_yy": change_rest,
        "drivers_change_yy": drivers,
        "inputs": inputs,
        "uncertainty": j5_band(h, t, yy_hat),
        "last_miss": last_miss,
        "shadows": shadows,
        "outcome": None,
    }
    if t in h.yy_official.index and pd.notna(h.yy_official.get(t)) and t in h.effects.index \
            and h.effects.loc[t].notna().all():
        out["outcome"] = error_parts(h, t, fc, yy_hat)
        band = out["uncertainty"]
        if band:
            a = out["outcome"]["actual_yy"]
            out["outcome"]["inside_band"] = {lvl: bool(band[f"band_{lvl}"][0] <= a <= band[f"band_{lvl}"][1])
                                             for lvl in (50, 80, 90)}
        for name, s in shadows.items():
            if "forecast_yy" in s:
                out["outcome"].setdefault("shadow_errors_yy", {})[name] = s["forecast_yy"] - out["outcome"]["actual_yy"]
    out["text"] = text_forecast(out, info)
    out["text_outcome"] = text_outcome(out) if out["outcome"] else []
    return out


# ------------------------------------------------------------------ K2 candidate (optional)


def k2_explain(inp: Inputs, months: list[pd.Period]) -> dict[str, dict]:
    """k2_avg_ens_s = 50/50 + 0.5 ridge residual + 0.5 boosting residual; ridge split by feature (exact)."""
    import warnings

    from kpif_nowcast.data import load_el_contracts
    from kpif_nowcast.j2_el import zone_monthly_spot
    from kpif_nowcast.k2_ml import ALL_VARIANTS, K2Runner, build_design, feature_cols
    from kpif_nowcast.observations import load as load_obs

    warnings.filterwarnings("ignore")
    d = build_design(inp.kpif, inp.comps, inp.feats, load_el_contracts(), zone_monthly_spot("SE3"), inp.rb_fc,
                     load_obs(), with_catalog=False)
    run = K2Runner(d)
    v = ALL_VARIANTS[K2_NAME]
    cols = feature_cols(d, v.fset)
    out = {}
    for t in months:
        if t not in d.index:
            continue
        i = d.index.get_loc(t)
        avg = float(d["avg"].iat[i])
        ridge, hgb = run.member(v.base, "ridge", v.fset, i), run.member(v.base, "hgb", v.fset, i)
        rec = {"forecast_yy": run.forecast(K2_NAME, i), "base_5050_yy": avg}
        if ridge is None or hgb is None:
            rec["note"] = "too few training months: forecast = 50/50"
        else:
            x = d[cols].iloc[[i]].to_numpy(dtype=float)
            pipe = ridge[0]
            z = pipe[:-1].transform(x)[0]
            est = pipe[-1]
            contrib = 0.5 * est.coef_ * z
            rec["ridge_half_yy"] = 0.5 * float(pipe.predict(x)[0])
            rec["boosting_half_yy"] = 0.5 * float(hgb[0].predict(x)[0])
            rec["ridge_intercept_half"] = 0.5 * float(est.intercept_)
            top = np.argsort(-np.abs(contrib))[:3]
            rec["top_ridge_features"] = [{"feature": cols[j], "contribution_yy": float(contrib[j])} for j in top]
        out[str(t)] = rec
    return out


# ------------------------------------------------------------------ text (Swedish, for the monthly letter)


def num(x: float, d: int = 1, sign: bool = False) -> str:
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s.replace(".", ",").replace("-", "−")


def month_sv(m: str) -> str:
    p = pd.Period(m, "M")
    return f"{MONTH_SV[p.month - 1]} {p.year}"


def text_forecast(e: dict, info: dict | None = None) -> list[str]:
    f, comps, dr = e["forecast"], e["components"], e["drivers_change_yy"]
    t, prev = month_sv(e["target_month"]), MONTH_SV[pd.Period(f["last_known_month"], "M").month - 1]
    ch = f["change_yy"]
    verb = "oförändrat" if abs(ch) < 0.05 else ("upp" if ch > 0 else "ned")
    lines = [f"**KPIF {t}: prognos {num(f['yy'], 1)} %** ({verb} från {num(f['last_known_yy'], 1)} % i {prev}; "
             f"{num(f['yy'], 2)} med två decimaler, månadsförändring {num(f['mm_pp'], 2, True)} %)."]
    big = max(COMPONENTS, key=lambda c: abs(comps[c]["change_yy"]))
    lines.append(f"Störst bidrag till förändringen i årstakt: {NAME_SV[big]} {num(comps[big]['change_yy'], 2, True)} pe "
                 f"(prognos {num(comps[big]['mm_pp'], 2, True)} pe på månadstakten mot "
                 f"{num(comps[big]['same_month_last_year_pp'], 2, True)} samma månad i fjol).")
    inp = e["inputs"]
    el_word = "steg" if inp["el_chg_sek_kwh"] > 0 else "föll"
    fuel_pct = (math.exp(inp["fuel_chg_log"]) - 1) * 100
    el_days = f" ({inp['el_days']} dagar hittills)" if info and inp.get("el_days") and \
        inp["el_days"] < pd.Period(e["target_month"], "M").days_in_month else ""
    lines.append(f"Elpriset{el_days} {el_word} med {num(abs(inp['el_chg_sek_kwh']), 2)} kr/kWh mot förra månaden "
                 f"({num(inp['el_spot_sek_kwh'], 2)} kr/kWh), vilket ger {num(dr['el'], 2, True)} pe på årstakten; "
                 f"oljepriset i kronor (drivmedel) {num(fuel_pct, 0, True)} % ger {num(dr['fuel'], 2, True)} pe. "
                 f"Säsong och trend mot samma månad i fjol ger {num(dr['normal_vs_last_year'], 2, True)} pe.")
    others = [c for c in COMPONENTS if c != big]
    lines.append("Övriga komponenter (förändring i årstakt): "
                 + ", ".join(f"{NAME_SV[c]} {num(comps[c]['change_yy'], 2, True)}" for c in others) + " pe.")
    u = e["uncertainty"]
    if u:
        lines.append(f"Osäkerhet (J5:s EWMA-band, förslag): 50 % {num(u['band_50'][0])}–{num(u['band_50'][1])} %, "
                     f"80 % {num(u['band_80'][0])}–{num(u['band_80'][1])} %.")
    s = e["shadows"]
    parts = []
    if "j2_el_dev" in s:
        j = s["j2_el_dev"]
        parts.append(f"J2 V2 {num(j['forecast_yy'], 1)} % ({num(j['diff_vs_live_yy'], 2, True)} pe mot skarpa; "
                     f"elen räknas som avvikelse från hur priset brukar ändras samma månad, "
                     f"{num(j['el_dev_sek_kwh'], 2, True)} kr/kWh)")
    if "j1_comb_equal" in s:
        c, r = s["j1_comb_equal"], s["rb_updated"]
        parts.append(f"50/50 {num(c['forecast_yy'], 1)} % ({num(c['diff_vs_live_yy'], 2, True)} pe; Riksbanken "
                     f"{num(r['riksbank_yy'], 1)} % i {r['policy_round']}, senaste miss {num(r['last_miss_pp'], 2, True)} pe "
                     f"ger rb_updated {num(r['forecast_yy'], 1)} %)")
    if K2_NAME in s and "forecast_yy" in s[K2_NAME]:
        k = s[K2_NAME]
        top = k.get("top_ridge_features", [])
        tail = f"; största ridge-bidrag {top[0]['feature']} {num(top[0]['contribution_yy'], 2, True)} pe" if top else ""
        parts.append(f"K2-kandidaten {num(k['forecast_yy'], 1)} % (50/50 {num(k['base_5050_yy'], 2)} "
                     f"{num(k['forecast_yy'] - k['base_5050_yy'], 2, True)} pe{tail})")
    if parts:
        lines.append("Skuggmodeller: " + "; ".join(parts) + ".")
    m = e["last_miss"]
    if m:
        big_m = max(COMPONENTS, key=lambda c: abs(m["per_component_yy"][c]))
        lines.append(f"Senaste miss ({month_sv(m['month'])}): prognos {num(m['forecast_yy'], 2)} %, utfall "
                     f"{num(m['actual_yy'], 1)} %, fel {num(m['error_yy'], 2, True)} pe; störst {NAME_SV[big_m]} "
                     f"{num(m['per_component_yy'][big_m], 2, True)} pe.")
    return lines


def text_outcome(e: dict) -> list[str]:
    o = e["outcome"]
    big = max(COMPONENTS, key=lambda c: abs(o["per_component_yy"][c]))
    s = (f"Utfall {num(o['actual_yy'], 1)} %, fel {num(o['error_yy'], 2, True)} pe "
         f"(positivt = prognosen för hög). Störst: {NAME_SV[big]} {num(o['per_component_yy'][big], 2, True)} pe; "
         + ", ".join(f"{NAME_SV[c]} {num(o['per_component_yy'][c], 2, True)}" for c in COMPONENTS if c != big)
         + f", avrundning {num(o['rest_yy'], 2, True)}.")
    if "inside_band" in o:
        ib = o["inside_band"]
        s += " Inom J5-bandet: " + ", ".join(f"{lvl} % {'ja' if ib[lvl] else 'nej'}" for lvl in (50, 80)) + "."
    return [s]


# ------------------------------------------------------------------ history of errors per component


def error_history(h: History, start: str = "2015-01", end: str | None = None) -> pd.DataFrame:
    """Per published month: y/y error per component for J2 V2 (2015-), and energy for comp_fuel and live."""
    last = h.yy_official.index.max() if end is None else pd.Period(end, "M")
    rows = []
    for t in pd.period_range(start, last, freq="M"):
        if t not in h.j2.index or pd.isna(h.j2.at[t, "yy_hat"]) or h.effects.loc[t].isna().any():
            continue
        k = _k(h, t)
        actual = float(h.yy_official[t])
        r = {"month": t, "actual_yy": actual}
        fc = {c: float(h.trend.at[t, c] + h.season.at[t, c]) for c in COMPONENTS}
        fc["energy"] = float(h.j2.at[t, "fc_energy"])
        for c in COMPONENTS:
            r[f"e_{c}"] = k * (fc[c] - h.effects.at[t, c])
        r["error_yy"] = float(h.j2.at[t, "yy_hat"]) - actual
        r["e_rest"] = r["error_yy"] - sum(r[f"e_{c}"] for c in COMPONENTS)
        for model, tag in (("comp_fuel", "fuel"), ("comp_fuel_el", "live")):
            res = _fc(h, model)
            if t in res.index and pd.notna(res.at[t, "yy_hat"]):
                r[f"e_energy_{tag}"] = k * (float(res.at[t, "fc_energy"]) - h.effects.at[t, "energy"])
                r[f"error_yy_{tag}"] = float(res.at[t, "yy_hat"]) - actual
        rows.append(r)
    return pd.DataFrame(rows).set_index("month")


def mse_shares(df: pd.DataFrame, cols: list[str], total: str) -> pd.Series:
    """Share of MSE: mean(e_c * e) / mean(e^2); sums to 1 when the parts sum to the total error."""
    e = df[total]
    return pd.Series({c: float((df[c] * e).mean() / (e ** 2).mean()) for c in cols})


PERIODS = [("2015–2019", "2015-01", "2019-12"), ("2020–2021", "2020-01", "2021-12"),
           ("2022–2023", "2022-01", "2023-12"), ("2024–2026", "2024-01", "2026-12"), ("2015–2026", "2015-01", "2026-12")]


def error_tables(hist: pd.DataFrame) -> dict[str, pd.DataFrame]:
    cols = [f"e_{c}" for c in COMPONENTS] + ["e_rest"]
    names = {f"e_{c}": NAME_SV[c] for c in COMPONENTS} | {"e_rest": "avrundning"}
    mae, share, bias = {}, {}, {}
    for label, a, b in PERIODS:
        p = hist.loc[pd.Period(a, "M"): pd.Period(b, "M")]
        mae[label] = {"n": len(p), "MAE total": p["error_yy"].abs().mean(),
                      **{names[c]: p[c].abs().mean() for c in cols}}
        share[label] = mse_shares(p, cols, "error_yy").rename(names)
        bias[label] = {"total": p["error_yy"].mean(), **{names[c]: p[c].mean() for c in cols}}
    yearly = hist.groupby(hist.index.year.rename("år")).agg(
        **{"n": ("error_yy", "size"), "MAE total": ("error_yy", lambda s: s.abs().mean())},
        **{names[c]: (c, lambda s: s.abs().mean()) for c in cols})
    yshare = pd.DataFrame({y: mse_shares(g, cols, "error_yy").rename(names) for y, g in hist.groupby(hist.index.year)}).T
    yshare.index.name = "år"
    energy = {}
    for label, a, b in PERIODS:
        p = hist.loc[pd.Period(a, "M"): pd.Period(b, "M")]
        energy[label] = {"J2 V2 (el_dev)": p["e_energy"].abs().mean(),
                         "comp_fuel (bara drivmedel)": p["e_energy_fuel"].abs().mean(),
                         "skarpa (el_chg, från 2023-12)": p["e_energy_live"].abs().mean(),
                         "n skarpa": int(p["e_energy_live"].notna().sum())}
    return {"mae": pd.DataFrame(mae).T, "share": pd.DataFrame(share).T, "bias": pd.DataFrame(bias).T,
            "yearly": yearly, "yearly_share": yshare, "energy": pd.DataFrame(energy).T}


def error_markdown(hist: pd.DataFrame) -> str:
    tb = error_tables(hist)
    s, y = tb["share"], tb["yearly_share"]
    full = s.loc["2015–2026"].drop("avrundning").sort_values(ascending=False)
    rank = ", ".join(f"{k} {num(100 * v, 0)} %" for k, v in full.items())
    lines = [
        "# Prognosfel per komponent 2015–2026",
        "",
        f"Genererad av `python -m kpif_nowcast.explain --docs` ({hist.index.min()}..{hist.index.max()}, n = {len(hist)}).",
        "Fel = prognos − utfall i årstakt (pe), positivt = för hög prognos. Felet delas exakt upp per komponent: "
        "k · (prognos för komponentens bidrag − SCB:s bidrag), k = index(t−1)/index(t−12). "
        "\"Avrundning\" är SCB:s avrundning av bidragen och av den officiella årstakten (0,1).",
        "",
        "Modell: J2 V2 (`j2_el_dev`), den enda komponentmodellen med el över hela perioden. Tjänster, varor, "
        "livsmedel och kapitalstock prognostiseras identiskt i alla tre komponentmodellerna (säsong + 12-månaderstrend), "
        "så de kolumnerna gäller även den skarpa modellen. Bara energi skiljer (tabell 4).",
        "",
        "## Sammanfattning",
        "",
        f"- **Andel av kvadratfelet (MSE) 2015–2026:** {rank}. Andelen är medel(e_c · e)/medel(e²) och summerar till 100 % "
        "med avrundningen; en komponent vars fel tar ut andra komponenters fel kan få negativ andel.",
    ]
    per = s.drop(index="2015–2026").drop(columns="avrundning")
    lead = {lab: per.loc[lab].idxmax() for lab in per.index}
    lines.append("- **Över tid:** största felkällan per period: "
                 + "; ".join(f"{lab} {lead[lab]} ({num(100 * per.loc[lab, lead[lab]], 0)} %)" for lab in per.index) + ".")
    m = tb["mae"]
    lines.append("- **MAE totalt per period:** " + "; ".join(f"{lab} {num(m.loc[lab, 'MAE total'], 3)} (n = {int(m.loc[lab, 'n'])})"
                                                          for lab in m.index) + ".")
    e = tb["energy"]
    lines.append(f"- **Energi i den skarpa modellen:** genomsnittligt absolut energifel 2024–2026 "
                 f"{num(e.loc['2024–2026', 'skarpa (el_chg, från 2023-12)'], 3)} pe mot J2 V2 "
                 f"{num(e.loc['2024–2026', 'J2 V2 (el_dev)'], 3)} och bara drivmedel "
                 f"{num(e.loc['2024–2026', 'comp_fuel (bara drivmedel)'], 3)} (n = {int(e.loc['2024–2026', 'n skarpa'])}, använd period).")
    lines += ["", "## 1. Andel av kvadratfelet per period (%)", "", (100 * s).round(0).to_markdown(), "",
              "## 2. Genomsnittligt absolut fel per komponent och period (pe i årstakt)", "",
              m.round(3).to_markdown(), "",
              "## 3. Medelfel (bias) per komponent och period (pe, positivt = för hög)", "",
              tb["bias"].round(3).to_markdown(), "",
              "## 4. Energi: genomsnittligt absolut fel i tre komponentmodeller (pe i årstakt)", "",
              e.round(3).to_markdown(), "",
              "## 5. Per år: genomsnittligt absolut fel (pe)", "", tb["yearly"].round(3).to_markdown(), "",
              "## 6. Per år: andel av kvadratfelet (%)", "", (100 * y).round(0).to_markdown(), "",
              "Månadsdata: `outputs/explain/fel_per_komponent.csv` (committas inte).", ""]
    return "\n".join(lines)


# ------------------------------------------------------------------ rendering and run


def _round(x, d: int = 4):
    if isinstance(x, float):
        return None if math.isnan(x) else round(x, d)
    if isinstance(x, dict):
        return {str(k): _round(v, d) for k, v in x.items()}
    if isinstance(x, list):
        return [_round(v, d) for v in x]
    return x


def to_json(e: dict) -> str:
    return json.dumps(_round(e), indent=2, ensure_ascii=False) + "\n"


def month_markdown(e: dict) -> str:
    t = e["target_month"]
    f, c = e["forecast"], e["components"]
    lines = [f"# Förklaring av KPIF-prognosen för {month_sv(t)}", ""]
    lines += [f"- {x}" for x in e["text"]]
    if e["text_outcome"]:
        lines += ["", "**Efter utfall:**", ""] + [f"- {x}" for x in e["text_outcome"]]
    rows = []
    for k in COMPONENTS:
        r = c[k]
        rows.append({"komponent": NAME_SV[k], "prognos m/m (pe)": r["mm_pp"], "trend": r["trend_pp"],
                     "säsong": r["season_pp"], "el": r.get("el_pp", 0.0), "drivmedel": r.get("fuel_pp", 0.0),
                     "samma månad i fjol": r["same_month_last_year_pp"], "bidrag till ändrad årstakt": r["change_yy"]})
    tab = pd.DataFrame(rows).set_index("komponent")
    tab.loc["summa"] = tab.sum()
    tab.loc["summa", "bidrag till ändrad årstakt"] += e["change_rest_yy"]
    lines += ["", "## Bidrag per komponent", "",
              f"Prognos {num(f['yy'], 2)} % i årstakt, {num(f['mm_pp'], 2, True)} % på månaden. Bidragen i pe av KPIF:s "
              f"månadsförändring (TAB6628); sista kolumnen är bidraget till förändringen från {num(f['last_known_yy'], 1)} % "
              f"({f['last_known_month']}), inklusive avrundning {num(e['change_rest_yy'], 3, True)} i summaraden.", "",
              tab.round(3).to_markdown(), ""]
    d = e["drivers_change_yy"]
    lines += ["## Nyhetsdekomposition (förändring i årstakt mot förra utfallet, pe)", "",
              "| källa | pe |", "|---|---|",
              f"| säsong + trend mot samma månad i fjol | {num(d['normal_vs_last_year'], 3, True)} |",
              f"| el | {num(d['el'], 3, True)} |", f"| drivmedel | {num(d['fuel'], 3, True)} |",
              f"| avrundning | {num(d['rest'], 3, True)} |", f"| **summa** | **{num(f['change_yy'], 3, True)}** |", ""]
    s = e["shadows"]
    if s:
        lines += ["## Skuggmodeller mot den skarpa", ""]
        if "j2_el_dev" in s:
            j = s["j2_el_dev"]
            lines.append(f"- J2 V2: {num(j['forecast_yy'], 2)} % ({num(j['diff_vs_live_yy'], 2, True)} pe). Skillnaden "
                         f"kommer bara från energin: el {num(j['diff_from_el_yy'], 2, True)}, drivmedel "
                         f"{num(j['diff_from_fuel_yy'], 2, True)} pe.")
        if "j1_comb_equal" in s:
            q, r = s["j1_comb_equal"], s["rb_updated"]
            lines.append(f"- 50/50: {num(q['forecast_yy'], 2)} % ({num(q['diff_vs_live_yy'], 2, True)} pe) = hälften "
                         f"Riksbankens bana ({r['policy_round']}, {num(r['riksbank_yy'], 2)} %, "
                         f"{r['months_since_cutoff']} mån efter brytpunkt) {num(q['from_riksbank_path'], 2, True)} + "
                         f"hälften senaste Riksbanksmissen {num(q['from_last_rb_miss'], 2, True)} + hälften J2 V2 "
                         f"{num(q['from_j2'], 2, True)} pe.")
        if K2_NAME in s:
            k = s[K2_NAME]
            if "ridge_half_yy" in k:
                feats = ", ".join(f"`{x['feature']}` {num(x['contribution_yy'], 3, True)}" for x in k["top_ridge_features"])
                lines.append(f"- K2 `{K2_NAME}`: {num(k['forecast_yy'], 2)} % = 50/50 {num(k['base_5050_yy'], 2)} + "
                             f"½ ridge {num(k['ridge_half_yy'], 3, True)} + ½ boosting {num(k['boosting_half_yy'], 3, True)} pe. "
                             f"Största ridge-bidrag: {feats}.")
            else:
                lines.append(f"- K2 `{K2_NAME}`: {num(k['forecast_yy'], 2)} % ({k.get('note', '')}).")
        lines.append("")
    u = e["uncertainty"]
    if u:
        lines += ["## Osäkerhet (J5 U4 EWMA, förslag)", "",
                  f"50 % {num(u['band_50'][0], 2)}–{num(u['band_50'][1], 2)}, 80 % {num(u['band_80'][0], 2)}–"
                  f"{num(u['band_80'][1], 2)}, 90 % {num(u['band_90'][0], 2)}–{num(u['band_90'][1], 2)} % "
                  f"({u['n_past']} tidigare fel, {u['past_errors']}).", ""]
    o = e["outcome"]
    if o:
        tab = pd.DataFrame({"prognos m/m (pe)": {NAME_SV[k]: c[k]["mm_pp"] for k in COMPONENTS},
                            "utfall m/m (pe)": {NAME_SV[k]: o["actual_mm_pp"][k] for k in COMPONENTS},
                            "fel i årstakt (pe)": {NAME_SV[k]: o["per_component_yy"][k] for k in COMPONENTS}})
        tab.loc["avrundning"] = [np.nan, np.nan, o["rest_yy"]]
        tab.loc["summa"] = [np.nan, np.nan, o["error_yy"]]
        lines += ["## Fel per komponent efter utfall", "", tab.round(3).to_markdown(), ""]
    live_file = FORECAST_DIR / f"{t}.json"
    if live_file.exists():
        lf = json.loads(live_file.read_text(encoding="utf-8"))
        lines += [f"Skarp prognosfil `forecasts/{t}.json` ({lf.get('status')}, {lf.get('made_at')}): "
                  f"{num(lf['forecast_yy'], 2)} %, el {lf.get('inputs', {}).get('el_days')} dagar, drivmedel till "
                  f"{lf.get('inputs', {}).get('fuel_last_day')}. Förklaringen ovan är samma modell körd med dagens data "
                  f"({num(f['yy'], 2)} %, manuell justering i filen {num(lf.get('manual_adjustment_pp', 0.0), 2, True)} pe); "
                  "övrig skillnad beror på data som kommit efter filens körning (t.ex. fler dagars elpriser).", ""]
    lines += [f"Informationsmängd: KPIF till och med {e['information_set']['kpif_through']}, energipriser för "
              f"{e['information_set']['energy_prices_for']}, Riksbanksbana {e['information_set']['riksbank_vintage']}; "
              f"deadline {e['deadline']}.", ""]
    return "\n".join(lines)


def summary_markdown(exps: list[dict]) -> str:
    rows = []
    for e in exps:
        o, u = e["outcome"], e["uncertainty"]
        big = max(COMPONENTS, key=lambda c: abs(e["components"][c]["change_yy"]))
        r = {"månad": e["target_month"], "prognos": e["forecast"]["yy"], "förra utfallet": e["forecast"]["last_known_yy"],
             "huvuddrivare": f"{NAME_SV[big]} {num(e['components'][big]['change_yy'], 2, True)}",
             "el": e["drivers_change_yy"]["el"], "drivmedel": e["drivers_change_yy"]["fuel"],
             "80 %-band": f"{num(u['band_80'][0])}–{num(u['band_80'][1])}" if u else "",
             "utfall": o["actual_yy"] if o else np.nan, "fel": o["error_yy"] if o else np.nan}
        if o:
            bm = max(COMPONENTS, key=lambda c: abs(o["per_component_yy"][c]))
            r["största felkälla"] = f"{NAME_SV[bm]} {num(o['per_component_yy'][bm], 2, True)}"
            r["J2 V2 fel"] = o.get("shadow_errors_yy", {}).get("j2_el_dev", np.nan)
            r["50/50 fel"] = o.get("shadow_errors_yy", {}).get("j1_comb_equal", np.nan)
        rows.append(r)
    df = pd.DataFrame(rows).set_index("månad")
    done = [e for e in exps if e["outcome"]]
    err = pd.Series([e["outcome"]["error_yy"] for e in done])
    comp_abs = pd.DataFrame([e["outcome"]["per_component_yy"] for e in done]).abs().mean().rename(NAME_SV)
    cov = {lvl: np.mean([e["outcome"]["inside_band"][lvl] for e in done if "inside_band" in e["outcome"]])
           for lvl in (50, 80, 90)}
    main = comp_abs.sort_values(ascending=False)
    sh = {n: np.mean([abs(e["outcome"]["shadow_errors_yy"][n]) for e in done
                      if n in e["outcome"].get("shadow_errors_yy", {})]) for n in ("j2_el_dev", "j1_comb_equal")}
    lines = [
        f"# Förklarade prognoser: {exps[0]['target_month']}..{exps[-1]['target_month']}",
        "",
        "Genererad av `python -m kpif_nowcast.explain --docs`. Skarpa modellens prognos (component_fuel_el_v1) "
        "rekonstruerad med dagens data; fel = prognos − utfall.",
        "",
        "## Huvudbudskap",
        "",
        f"- **{len(done)} månader med utfall:** MAE {num(err.abs().mean(), 3)} pe, medelfel {num(err.mean(), 3, True)} pe "
        f"(skuggor samma månader: J2 V2 {num(sh['j2_el_dev'], 3)}, 50/50 {num(sh['j1_comb_equal'], 3)}). Använd period, "
        "bara rapport.",
        "- **Felet per komponent (genomsnittligt absolut, pe):** " + ", ".join(f"{k} {num(v, 3)}" for k, v in main.items()) + ".",
        f"- **J5-bandets träffsäkerhet:** utfallet inom 50 %-bandet {num(100 * cov[50], 0)} %, 80 % {num(100 * cov[80], 0)} %, "
        f"90 % {num(100 * cov[90], 0)} % av månaderna (n = {len(done)}; litet urval, osäkert).",
        f"- **Senaste prognosen ({exps[-1]['target_month']}):** " + exps[-1]["text"][0].replace("**", ""),
        "",
        "## Månad för månad (pe i årstakt)",
        "",
        df.round(2).to_markdown(),
        "",
        "Per månad: `outputs/explain/<månad>.json` och `.md` (committas inte); exempel i "
        "`docs/auto2/k3/exempel-2026-11.json` och `docs/auto2/k3/forklaring-2026-11.md`.",
        "",
    ]
    return "\n".join(lines)


def run(months: int = 24, with_k2: bool = True, docs: bool = False, inp: Inputs | None = None,
        info: dict | None = None) -> list[dict]:
    """Explain the next unpublished month and the `months` before it; write outputs/explain/."""
    if inp is None:
        from kpif_nowcast.shadow import load_inputs

        inp, info = load_inputs()
    h = build_history(inp)
    target = inp.kpif.index.max() + 1
    ms = list(pd.period_range(target - months, target, freq="M"))
    k2 = {}
    if with_k2:
        try:
            k2 = k2_explain(inp, ms)
        except Exception as exc:  # optional: never block the explanation of the live model
            print(f"K2 explanation skipped: {exc!r}")
    exps = [explain_month(h, t, k2.get(str(t)), info if t == target else None) for t in ms]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = {"generated_at": datetime.now().isoformat(timespec="seconds")}
    for e in exps:
        (OUT_DIR / f"{e['target_month']}.json").write_text(to_json({**e, "run": meta}), encoding="utf-8")
        (OUT_DIR / f"{e['target_month']}.md").write_text(month_markdown(e), encoding="utf-8")
    (OUT_DIR / "sammanstallning.md").write_text(summary_markdown(exps), encoding="utf-8")
    hist = error_history(h)
    hist.to_csv(OUT_DIR / "fel_per_komponent.csv")
    (OUT_DIR / "fel_per_komponent.md").write_text(error_markdown(hist), encoding="utf-8")
    if docs:
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        last = exps[-1]
        (DOCS_DIR / f"exempel-{last['target_month']}.json").write_text(to_json(last), encoding="utf-8")
        (DOCS_DIR / f"forklaring-{last['target_month']}.md").write_text(month_markdown(last), encoding="utf-8")
        (DOCS_DIR / "sammanstallning-24.md").write_text(summary_markdown(exps), encoding="utf-8")
        (DOCS_DIR / "fel_per_komponent.md").write_text(error_markdown(hist), encoding="utf-8")
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    for line in exps[-1]["text"]:
        print(line)
    print(f"Wrote {len(exps)} explanations to {OUT_DIR}")
    return exps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", type=int, default=24)
    parser.add_argument("--no-k2", action="store_true")
    parser.add_argument("--docs", action="store_true", help="also write the committed examples in docs/auto2/k3/")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.offline:
        from kpif_nowcast.pipeline import go_offline

        go_offline()
    run(args.months, not args.no_k2, args.docs)


if __name__ == "__main__":
    main()
