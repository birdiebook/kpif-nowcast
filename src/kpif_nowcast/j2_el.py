"""J2: the electricity correction on long history (2012-), variants V1-V5.

Preregistered in docs/auto/j2/hypotes.md. Every variant is the component model
(seasonal + 12-month trend per component) with an expanding-window OLS correction
of the energy component's error, trained from 2012-01. Other components are unchanged.

Information set for target t: KPIF/components up to t-1, electricity and fuel for t
(known at the deadline, day 4 of t+1), share of variable contracts up to t-1
(TAB3571 for month m is published ~23rd of m+1).

Run: python -m kpif_nowcast.j2_el
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from kpif_nowcast.baselines import seasonal_trend_additive, yy_from_mm
from kpif_nowcast.component_model import Correction, fit_correction

TRAIN_START = "2012-01"
SEASON_YEARS = 5
VARIANTS = {
    "j2_el_raw": dict(cols=["fuel_chg", "el_chg"], energy_base="seasonal"),
    "j2_el_dev": dict(cols=["fuel_chg", "el_dev"], energy_base="seasonal"),
    "j2_el_trendbase": dict(cols=["fuel_chg", "el_chg"], energy_base="trend"),
    "j2_el_dev_var": dict(cols=["fuel_chg", "el_dev_var"], energy_base="seasonal"),
    "j2_el_dev_se3": dict(cols=["fuel_chg", "el_dev_se3"], energy_base="seasonal"),
}
REVISED_FEATURES = {"el_dev_var"}  # built from TAB3571, revised after publication


def same_month_dev(x: pd.Series, years: int = SEASON_YEARS) -> pd.Series:
    """x_t minus the mean of x at t-12, ..., t-12*years (those available, at least one). Past only."""
    lags = pd.concat([x.shift(12 * k) for k in range(1, years + 1)], axis=1)
    return x - lags.mean(axis=1)


def variable_share(contracts: pd.DataFrame) -> pd.Series:
    """Share (%) of variable + hourly-price contracts, whole country, by month."""
    c = contracts[(contracts["zone"] == "00") & contracts["contract"].isin(["rorligt", "timpris"])]
    return c.groupby("month")["share"].sum(min_count=1)


def zone_monthly_spot(zone: str, last_day: date = date(2026, 10, 31)) -> pd.Series:
    """Monthly mean spot price for one zone (SEK/kWh), complete months only, from the local caches."""
    from kpif_nowcast.features import electricity_daily  # local import: reads caches

    daily = electricity_daily()[zone]
    daily = daily[daily.index <= pd.Timestamp(last_day)]
    g = daily.groupby(daily.index.to_period("M"))
    m = g.mean()
    return m[g.size() >= 28]


def build_j2_features(feats: pd.DataFrame, contracts: pd.DataFrame, se3_spot: pd.Series) -> pd.DataFrame:
    """Derived regressors. Each row t uses only rows <= t of feats/se3_spot and rows <= t-1 of contracts."""
    out = feats[["fuel_chg", "el_chg"]].copy()
    out["el_dev"] = same_month_dev(out["el_chg"])
    share = variable_share(contracts).reindex(out.index)
    # t-1 for target t; before the first published month (2013-04) back-fill the first known value.
    # Back-filled rows are training rows before 2015 only, and that value is published by 2013-05.
    share_l1 = share.shift(1)
    first = share.first_valid_index()
    if first is not None:
        share_l1.loc[: first] = share_l1.loc[: first].fillna(share.loc[first])
    out["var_share_l1"] = share_l1
    out["el_dev_var"] = out["el_dev"] * share_l1 / 100
    se3_chg = se3_spot.reindex(out.index).diff()
    out["el_dev_se3"] = same_month_dev(se3_chg)
    return out


def j2_forecast(index: pd.Series, components: pd.DataFrame, j2feats: pd.DataFrame, variant: str) -> pd.DataFrame:
    """Component forecast with the variant's energy correction; returns mm_hat_pp and yy_hat per month."""
    v = VARIANTS[variant]
    effects = components.pivot(index="month", columns="component", values="effect_month")
    effects = effects.reindex(pd.period_range(effects.index.min(), effects.index.max() + 1, freq="M"))
    base = effects.apply(seasonal_trend_additive)
    if v["energy_base"] == "trend":
        base["energy"] = effects["energy"].rolling(12).mean().shift(1)
    corr = fit_correction(effects["energy"] - base["energy"], j2feats, Correction(v["cols"], TRAIN_START))
    fc = base.copy()
    fc["energy"] = base["energy"] + corr["correction"]
    fc = fc.reindex(base.index.intersection(corr.index))
    out = pd.DataFrame({"mm_hat_pp": fc.sum(axis=1), "fc_energy": fc["energy"]})
    idx = index.reindex(pd.period_range(index.index.min(), index.index.max() + 1, freq="M"))
    out["yy_hat"] = yy_from_mm(idx, (out["mm_hat_pp"] / 100).reindex(idx.index)).reindex(out.index)
    return out.join(corr.drop(columns="correction"))


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjusted p-values."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, running, out = len(items), 0.0, {}
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def main() -> None:
    from kpif_nowcast.backtest import BENCHMARK, build_predictions, score
    from kpif_nowcast.data import load_components, load_el_contracts, load_kpif
    from kpif_nowcast.evaluation import dm_test, log_run
    from kpif_nowcast.features import load_features

    preds, actual, rb = build_predictions()
    kpif, comps = load_kpif(), load_components()
    j2f = build_j2_features(load_features(), load_el_contracts(), zone_monthly_spot("SE3"))
    results = {name: j2_forecast(kpif["index"], comps, j2f, name) for name in VARIANTS}
    for name, res in results.items():
        preds[name] = res["yy_hat"]

    ref = "comp_fuel"
    cols = [BENCHMARK, ref, "riksbank", *VARIANTS]
    lines, log_rows = [], []
    for label, start, end in [("2015-2026", "2015-01", "2026-10"), ("2024-2026 (used)", "2024-01", "2026-10")]:
        p = preds.loc[pd.Period(start, "M"): pd.Period(end, "M"), cols]
        p = p[actual.reindex(p.index).notna()].dropna()
        err = p.sub(actual.reindex(p.index), axis=0)
        table = score(actual, p)
        raw_ref, raw_rb = {}, {}
        for m in VARIANTS:
            raw_ref[m] = dm_test(err[m].to_numpy(), err[ref].to_numpy()).p
            raw_rb[m] = dm_test(err[m].to_numpy(), err[BENCHMARK].to_numpy()).p
        holm_ref = holm(raw_ref)
        for m in table.index:
            if m in VARIANTS:
                table.loc[m, "diff_vs_comp_fuel"] = table.loc[m, "MAE"] - table.loc[ref, "MAE"]
                table.loc[m, "dm_p_vs_comp_fuel"] = raw_ref[m]
                table.loc[m, "holm_p_vs_comp_fuel"] = holm_ref[m]
                table.loc[m, "dm_p_vs_rb_updated"] = raw_rb[m]
            elif m != BENCHMARK:
                table.loc[m, "dm_p_vs_rb_updated"] = dm_test(err[m].to_numpy(), err[BENCHMARK].to_numpy()).p
        for m, row in table.iterrows():
            log_rows.append({"variant": m, "period": label, "n": int(row["n"]), "MAE": round(row["MAE"], 4),
                             "dm_p_vs_rb_updated": round(row.get("dm_p_vs_rb_updated", float("nan")), 4)})
        lines.append(f"## {label} (n={len(p)})\n\n{table.round(3).to_markdown()}\n")
        print(f"\n{label} n={len(p)}\n{table.round(3)}")

    # MAE by Riksbank vintage age, 2015-2026, for the reference and the variants
    p = preds.loc["2015-01":"2026-10", cols].dropna()
    p = p[actual.reindex(p.index).notna()]
    age = rb["rb_months_ahead"].reindex(p.index)
    by_age = p.sub(actual.reindex(p.index), axis=0).abs().groupby(age).mean().assign(n=age.value_counts())
    lines.append(f"## MAE by months since Riksbank cutoff, 2015-2026\n\n{by_age.round(3).to_markdown()}\n")
    # January only
    jan = p[p.index.month == 1]
    jmae = jan.sub(actual.reindex(jan.index), axis=0).abs().mean().round(3)
    lines.append(f"## January only, 2015-2026 (n={len(jan)})\n\n{jmae.to_frame('MAE').to_markdown()}\n")
    coefs = {n: r.filter(like="b_").iloc[-1] for n, r in results.items()}
    lines.append(f"## Latest energy coefficients\n\n{pd.DataFrame(coefs).round(4).to_markdown()}\n")
    print(by_age.round(3), jmae, pd.DataFrame(coefs).round(4), sep="\n\n")
    path = log_run("j2_el", log_rows)
    lines.append(f"Run log: `{path.name}`\n")
    from pathlib import Path

    outdir = Path(__file__).resolve().parents[2] / "docs" / "auto" / "j2"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "results_raw.md").write_text("\n".join(lines), encoding="utf-8")
    preds[cols].join(actual.rename("actual")).to_csv(Path(__file__).resolve().parents[2] / "outputs" / "j2_preds.csv")


if __name__ == "__main__":
    main()
