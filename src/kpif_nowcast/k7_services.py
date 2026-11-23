"""K7: the services component. Robust seasonal (median) and calendar regressors (Easter, January repricing).

Preregistered in docs/auto2/k7/hypotes.md (variants T1-T5). Only J2 V2's services part changes:

- model A: seasonal = median (not mean) of the deviation from the 12-month mean, same calendar month,
  last 5 years; trend unchanged.
- model B: A + expanding-window OLS (no intercept, from 1995-01) of the services residual on
  `easter_dev` (days of the Easter travel window in month t, minus the same-month mean of the 5 prior
  years) and `jan_dev` (January only: services y/y in December minus its mean over the 5 prior Decembers).

j2s = J2 V2 with services model A or B. Variants combine it with rb_updated ("half"), add the whole change
to the 50/50 average ("full"), or add it to K2's `k2_avg_ens_s`.

Information set for target t: components and KPIF up to t-1 (published mid-month t), the calendar,
and whatever J2 V2 / rb_updated / K2 already use at t's deadline.

Run: python -m kpif_nowcast.k7_services
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from kpif_nowcast.baselines import seasonal_trend_additive, yy_from_mm
from kpif_nowcast.component_model import Correction, fit_correction
from kpif_nowcast.j2_el import build_j2_features, j2_forecast, same_month_dev
from kpif_nowcast.j4_detail import easter

SEASON_YEARS = 5
TRAIN_START = "1995-01"
REGS = ["easter_dev", "jan_dev"]
EASTER_WINDOW = (-9, 1)  # Friday before Palm Sunday .. Easter Monday, 11 days
VARIANTS = {
    "k7_med_half": ("A", "half"),
    "k7_med_full": ("A", "full"),
    "k7_cal_half": ("B", "half"),
    "k7_cal_full": ("B", "full"),
    "k7_k2_cal_full": ("B", "k2"),
}
K2_NAME = "k2_avg_ens_s"


# ------------------------------------------------------------------ services model


def seasonal_trend_median(x: pd.Series, years: int = SEASON_YEARS) -> pd.Series:
    """Like baselines.seasonal_trend_additive but the seasonal is the median of the past same-month deviations."""
    trend_12m = x.rolling(12).mean()
    deviation = x - trend_12m
    seasonal = pd.concat([deviation.shift(12 * k) for k in range(1, years + 1)], axis=1).median(axis=1)
    return trend_12m.shift(1) + seasonal


def easter_days(months: pd.PeriodIndex) -> pd.Series:
    """Days of the Easter travel window (Easter -9 .. +1) falling in each month."""
    counts: dict[pd.Period, int] = {}
    for y in sorted({p.year for p in months}):
        e = easter(y)
        for k in range(EASTER_WINDOW[0], EASTER_WINDOW[1] + 1):
            p = pd.Period(e + timedelta(days=k), "M")
            counts[p] = counts.get(p, 0) + 1
    return pd.Series([float(counts.get(p, 0)) for p in months], index=months)


def services_regressors(comps: pd.DataFrame, last: pd.Period) -> pd.DataFrame:
    """easter_dev and jan_dev for months up to `last`. Row t uses the services index up to t-1 only."""
    idx = pd.period_range("1987-01", last, freq="M")
    out = pd.DataFrame(index=idx)
    out["easter_dev"] = same_month_dev(easter_days(idx))
    sidx = comps[comps["component"] == "services"].set_index("month")["index"].reindex(idx)
    yy_prev = ((sidx / sidx.shift(12) - 1) * 100).shift(1)  # y/y of t-1, known at t
    is_jan = pd.Series(idx.month == 1, index=idx)
    out["jan_dev"] = same_month_dev(yy_prev).where(is_jan, 0.0)
    return out


def services_forecast(comps: pd.DataFrame, model: str) -> pd.DataFrame:
    """Services contribution forecasts (pp of KPIF m/m) incl. the unpublished next month.

    Columns: actual, base (J2 V2's services = seasonal_trend_additive), fc (model A or B), and for B the
    coefficients. Forecast for t uses services contributions up to t-1.
    """
    eff = comps[comps["component"] == "services"].set_index("month")["effect_month"]
    eff = eff.reindex(pd.period_range(eff.index.min(), eff.index.max() + 1, freq="M"))
    out = pd.DataFrame({"actual": eff, "base": seasonal_trend_additive(eff), "A": seasonal_trend_median(eff)})
    out["fc"] = out["A"]
    if model == "B":
        regs = services_regressors(comps, eff.index.max())
        corr = fit_correction(eff - out["A"], regs, Correction(REGS, TRAIN_START))
        out = out.join(corr)
        out["fc"] = out["A"] + out["correction"]
    return out


def j2s_forecast(index: pd.Series, comps: pd.DataFrame, j2feats: pd.DataFrame, model: str) -> pd.DataFrame:
    """J2 V2 with services model A or B. Returns j2 and j2s (KPIF y/y) and the services delta (pp m/m)."""
    j2 = j2_forecast(index, comps, j2feats, "j2_el_dev")
    s = services_forecast(comps, model).reindex(j2.index)
    delta = (s["fc"] - s["base"]).rename("delta_pp")
    mm = j2["mm_hat_pp"] + delta
    idx = index.reindex(pd.period_range(index.index.min(), index.index.max() + 1, freq="M"))
    yy = yy_from_mm(idx, (mm / 100).reindex(idx.index)).reindex(j2.index)
    return pd.DataFrame({"j2": j2["yy_hat"], "j2s": yy, "delta_pp": delta}).dropna(subset=["j2s"])


# ------------------------------------------------------------------ variants


def build_k7(kpif, comps, feats, contracts, se3, rb_fc, obs, k2_rows: list[int] | str | None = "all") -> pd.DataFrame:
    """One row per target month: bases, j2s(A/B), the five variants and the outcome.

    k2_rows: "all" computes k2_avg_ens_s for every row, a list only for those row positions, None skips it.
    """
    from kpif_nowcast.j1_hybrid import build_panel

    panel = build_panel(kpif, comps, feats, contracts, se3, rb_fc, obs)
    j2f = build_j2_features(feats, contracts, se3)
    d = pd.DataFrame(index=panel.index)
    d["actual"] = panel["actual"]
    d["rb_updated"] = panel["rb_updated"]
    d["j2"] = panel["j2"]
    d["avg_5050"] = 0.5 * d["rb_updated"] + 0.5 * d["j2"]
    for m in ("A", "B"):
        r = j2s_forecast(kpif["index"], comps, j2f, m).reindex(d.index)
        assert np.allclose(r["j2"], d["j2"], equal_nan=True)
        d[f"j2s_{m}"] = r["j2s"]
        d[f"delta_pp_{m}"] = r["delta_pp"]
    d[K2_NAME] = np.nan
    if k2_rows is not None:
        from kpif_nowcast.k2_ml import K2Runner, build_design

        run = K2Runner(build_design(kpif, comps, feats, contracts, se3, rb_fc, obs, with_catalog=False))
        assert run.d.index.equals(d.index)
        rows = range(len(d)) if k2_rows == "all" else k2_rows
        for i in rows:
            i = i % len(d)
            d.iloc[i, d.columns.get_loc(K2_NAME)] = run.forecast(K2_NAME, i)
    for name, (m, layer) in VARIANTS.items():
        change = d[f"j2s_{m}"] - d["j2"]
        if layer == "half":
            d[name] = 0.5 * d["rb_updated"] + 0.5 * d[f"j2s_{m}"]
        elif layer == "full":
            d[name] = d["avg_5050"] + change
        else:
            d[name] = d[K2_NAME] + change
    return d


BASE_OF = {n: (K2_NAME if layer == "k2" else "avg_5050") for n, (_, layer) in VARIANTS.items()}


# ------------------------------------------------------------------ evaluation


def main() -> None:
    import warnings
    from pathlib import Path

    from kpif_nowcast.data import load_components, load_el_contracts, load_kpif, load_riksbank_forecasts
    from kpif_nowcast.evaluation import dm_test, log_run
    from kpif_nowcast.features import load_features
    from kpif_nowcast.j1_hybrid import dm_one_sided
    from kpif_nowcast.j2_el import holm, zone_monthly_spot
    from kpif_nowcast.observations import load as load_obs

    warnings.filterwarnings("ignore")
    kpif, comps = load_kpif(), load_components()
    d = build_k7(kpif, comps, load_features(), load_el_contracts(), zone_monthly_spot("SE3"),
                 load_riksbank_forecasts(), load_obs())
    actual = d["actual"]
    cols = ["rb_updated", "j2", "avg_5050", K2_NAME, *VARIANTS]
    lines, log_rows = [], []

    def tables(label, start, end="2026-10", holm_on=True):
        p = d.loc[pd.Period(start, "M"): pd.Period(end, "M"), cols]
        p = p[actual.reindex(p.index).notna()].dropna()
        err = p.sub(actual.reindex(p.index), axis=0)
        tab = pd.DataFrame({"MAE": err.abs().mean(), "RMSE": np.sqrt((err ** 2).mean()), "bias": err.mean(),
                            "n": err.count()})
        raw = {}
        for m in VARIANTS:
            b = BASE_OF[m]
            r, p1 = dm_one_sided(err[m].to_numpy(), err[b].to_numpy())
            raw[m] = p1
            tab.loc[m, "base"] = b
            tab.loc[m, "diff_base"] = tab.loc[m, "MAE"] - tab.loc[b, "MAE"]
            tab.loc[m, "p1_base"] = p1
            other = "avg_5050" if b == K2_NAME else K2_NAME
            tab.loc[m, "diff_other"] = tab.loc[m, "MAE"] - tab.loc[other, "MAE"]
            # vs the other reference: one-sided only where nested (k2 variant vs 50/50 is not nested either way)
            tab.loc[m, "p2_other"] = dm_test(err[m].to_numpy(), err[other].to_numpy()).p
            tab.loc[m, "p1_rb_updated"] = dm_one_sided(err[m].to_numpy(), err["rb_updated"].to_numpy())[1]
        h = holm(raw)
        for m in VARIANTS:
            tab.loc[m, "holm_base"] = h[m]
        for m, row in tab.iterrows():
            log_rows.append({"variant": m, "period": label, "n": int(row["n"]), "MAE": round(row["MAE"], 4),
                             "dm_p_vs_rb_updated": round(row.get("p1_rb_updated", float("nan")), 4)})
        lines.append(f"## {label} (n={len(p)}; DM one-sided vs own base, Holm over 5; p2_other two-sided)\n\n"
                     f"{tab.round(3).to_markdown()}\n")
        print(f"\n{label}\n{tab.round(3)}", flush=True)
        return err

    err = tables("2015-02..2026-10 (primary)", "2015-02")
    tables("2018-02..2026-10 (K2 active)", "2018-02")
    tables("2024-01..2026-10 (used, report only)", "2024-01")

    # per year: MAE difference vs own base
    yr = err.abs().groupby(err.index.year).mean()
    per_year = pd.DataFrame({m: yr[m] - yr[BASE_OF[m]] for m in VARIANTS}).assign(n=err.groupby(err.index.year).size())
    per_year.insert(0, "MAE_avg_5050", yr["avg_5050"])
    per_year.insert(1, f"MAE_{K2_NAME}", yr[K2_NAME])
    lines.append(f"## Per year: MAE minus own base's MAE (pp)\n\n{per_year.round(3).to_markdown()}\n")
    print(per_year.round(3))

    # services component itself, pp of KPIF m/m
    rows = []
    sA, sB = services_forecast(comps, "A"), services_forecast(comps, "B")
    for label, a, b in [("2000-01..2009-12 (unseen, clean)", "2000-01", "2009-12"),
                        ("2010-01..2014-12", "2010-01", "2014-12"),
                        ("2015-01..2026-10", "2015-01", "2026-10"),
                        ("2024-01..2026-10 (used)", "2024-01", "2026-10")]:
        s = pd.DataFrame({"actual": sA["actual"], "base": sA["base"], "A": sA["fc"], "B": sB["fc"]}).loc[a:b].dropna()
        e = s[["base", "A", "B"]].sub(s["actual"], axis=0)
        row = {"period": label, "n": len(s), **{f"MAE {c}": e[c].abs().mean() for c in e}}
        for c in ("A", "B"):
            row[f"p1 {c} vs base"] = dm_one_sided(e[c].to_numpy(), e["base"].to_numpy())[1]
        row["p1 B vs A"] = dm_one_sided(e["B"].to_numpy(), e["A"].to_numpy())[1]
        rows.append(row)
    stab = pd.DataFrame(rows).set_index("period")
    lines.append(f"## Services component, MAE in pp of KPIF m/m (DM one-sided)\n\n{stab.round(4).to_markdown()}\n")
    print(stab.round(4))

    # services MAE by calendar month, 2015-2026 and 2000-2009
    for a, b in [("2000-01", "2009-12"), ("2015-01", "2026-10")]:
        s = pd.DataFrame({"actual": sA["actual"], "base": sA["base"], "A": sA["fc"], "B": sB["fc"]}).loc[a:b].dropna()
        e = s[["base", "A", "B"]].sub(s["actual"], axis=0).abs()
        lines.append(f"## Services MAE by calendar month {a}..{b}\n\n{e.groupby(e.index.month).mean().round(3).T.to_markdown()}\n")

    coefs = sB.filter(like="b_").dropna()
    sel = coefs[(coefs.index.month == 12) | (coefs.index == coefs.index.max())]
    lines.append(f"## Model B coefficients (pp per day / per pp of y/y), December each year\n\n{sel.round(4).to_markdown()}\n")
    print(sel.iloc[::4].round(4))

    path = log_run("k7_services", log_rows)
    lines.append(f"Run log: `{path.name}`\n")
    root = Path(__file__).resolve().parents[2]
    out = root / "docs" / "auto2" / "k7"
    out.mkdir(parents=True, exist_ok=True)
    (out / "results_raw.md").write_text("\n".join(lines), encoding="utf-8")
    (root / "outputs").mkdir(exist_ok=True)
    d.to_csv(root / "outputs" / "k7_preds.csv")


if __name__ == "__main__":
    main()
