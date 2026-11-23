"""J4: KPIF bottom-up from 43 COICOP level-2 groups (TAB6613), variants D1-D3.

Preregistered in docs/auto/j4/hypotes.md. TAB6613 history before 2026 is SCB's back-calculation to
COICOP 2018, i.e. revised data: any result here is "unconfirmed (revision leakage possible)".
Detail data for t is never used for t: group baselines use contributions up to t-1.

Run: python -m kpif_nowcast.j4_detail
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from kpif_nowcast.baselines import seasonal_trend_additive, yy_from_mm
from kpif_nowcast.component_model import Correction, fit_correction

TRAIN_START = "2012-01"
ENERGY_CORR = {"04.5": ["el_dev"], "07.2": ["fuel_chg"]}
EASTER_CORR = {"07.3": ["easter_dev"], "09.8": ["easter_dev"], "11.2": ["easter_dev"]}
VARIANTS = {
    "j4_detail_base": {},
    "j4_detail_energy": ENERGY_CORR,
    "j4_detail_energy_easter": {**ENERGY_CORR, **EASTER_CORR},
}


def easter(year: int) -> date:
    """Gregorian Easter Sunday (anonymous algorithm)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = ((h + l_ - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def same_month_dev(x: pd.Series, years: int = 5) -> pd.Series:
    lags = pd.concat([x.shift(12 * k) for k in range(1, years + 1)], axis=1)
    return x - lags.mean(axis=1)


def regressors(feats: pd.DataFrame) -> pd.DataFrame:
    """el_dev, fuel_chg and easter_dev per month; row t uses feats rows <= t only (calendar is known)."""
    idx = pd.period_range("1987-01", feats.index.max(), freq="M")
    out = pd.DataFrame(index=idx)
    out["fuel_chg"] = feats["fuel_chg"].reindex(idx)
    out["el_dev"] = same_month_dev(feats["el_chg"].reindex(idx))
    eas = pd.Series([1.0 if easter(p.year).month == p.month else 0.0 for p in idx], index=idx)
    out["easter_dev"] = same_month_dev(eas)
    return out


def group_effects(detail: pd.DataFrame) -> pd.DataFrame:
    g = detail[detail["level"] == 2].pivot(index="month", columns="coicop", values="effect_month")
    return g.fillna(0.0)


def j4_forecast(index: pd.Series, detail: pd.DataFrame, regs: pd.DataFrame, variant: str) -> pd.DataFrame:
    """Per-group forecasts summed to KPIF m/m (pp) and y/y. Forecast for t uses detail up to t-1."""
    eff = group_effects(detail)
    eff = eff.reindex(pd.period_range(eff.index.min(), eff.index.max() + 1, freq="M"))
    base = eff.apply(seasonal_trend_additive)
    fc = base.copy()
    valid = base.index
    for grp, cols in VARIANTS[variant].items():
        corr = fit_correction(eff[grp] - base[grp], regs, Correction(cols, TRAIN_START))
        fc[grp] = base[grp] + corr["correction"]
        valid = valid.intersection(corr.index)
    fc = fc.reindex(valid)
    out = fc.add_prefix("fc_")
    out["mm_hat_pp"] = fc.sum(axis=1, min_count=1)
    idx = index.reindex(pd.period_range(index.index.min(), index.index.max() + 1, freq="M"))
    out["yy_hat"] = yy_from_mm(idx, (out["mm_hat_pp"] / 100).reindex(idx.index)).reindex(out.index)
    return out


def holm(pvals: dict[str, float]) -> dict[str, float]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, running, out = len(items), 0.0, {}
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def main() -> None:
    from pathlib import Path

    from kpif_nowcast.backtest import BENCHMARK, build_predictions, score
    from kpif_nowcast.data import load_cpif_detail, load_kpif
    from kpif_nowcast.evaluation import dm_test, log_run
    from kpif_nowcast.features import load_features

    preds, actual, _ = build_predictions()
    kpif, detail = load_kpif(), load_cpif_detail()
    regs = regressors(load_features())
    results = {v: j4_forecast(kpif["index"], detail, regs, v) for v in VARIANTS}
    for v, r in results.items():
        preds[v] = r["yy_hat"]
    ref = "comp_fuel"
    cols = [BENCHMARK, ref, "riksbank", *VARIANTS]
    lines, log_rows = [], []
    for label, start in [("2015-2026", "2015-01"), ("2024-2026 (used)", "2024-01")]:
        p = preds.loc[pd.Period(start, "M"): pd.Period("2026-10", "M"), cols]
        p = p[actual.reindex(p.index).notna()].dropna()
        err = p.sub(actual.reindex(p.index), axis=0)
        table = score(actual, p)
        raw = {v: dm_test(err[v].to_numpy(), err[ref].to_numpy()).p for v in VARIANTS}
        h = holm(raw)
        for m in table.index:
            if m in VARIANTS:
                table.loc[m, "diff_vs_comp_fuel"] = table.loc[m, "MAE"] - table.loc[ref, "MAE"]
                table.loc[m, "dm_p_vs_comp_fuel"] = raw[m]
                table.loc[m, "holm_p"] = h[m]
            if m != BENCHMARK:
                table.loc[m, "dm_p_vs_rb_updated"] = dm_test(err[m].to_numpy(), err[BENCHMARK].to_numpy()).p
        for m, row in table.iterrows():
            log_rows.append({"variant": m, "period": label, "n": int(row["n"]), "MAE": round(row["MAE"], 4),
                             "dm_p_vs_rb_updated": round(row.get("dm_p_vs_rb_updated", float("nan")), 4)})
        lines.append(f"## {label} (n={len(p)})\n\n{table.round(3).to_markdown()}\n")
        print(f"\n{label} n={len(p)}\n{table.round(3)}")

    # Diagnostics: which groups drive D1's error, 2015-2026 (pp of KPIF m/m)
    eff = group_effects(detail)
    since, until = pd.Period("2015-01", "M"), pd.Period("2026-10", "M")
    for v in ["j4_detail_base", "j4_detail_energy_easter"]:
        fc = results[v].filter(like="fc_").rename(columns=lambda c: c[3:])
        e = (fc - eff.reindex(fc.index)).loc[since:until].dropna(how="all")
        tot = e.sum(axis=1)
        share = e.apply(lambda c: np.cov(c, tot)[0, 1] / tot.var())
        diag = pd.DataFrame({"var_share_%": 100 * share, "MAE_pp": e.abs().mean()})
        labels = detail.drop_duplicates("coicop").set_index("coicop")["label"]
        diag["label"] = labels.reindex(diag.index)
        diag = diag.sort_values("var_share_%", ascending=False).head(15)
        lines.append(f"## Top 15 groups by share of total error variance, {v}, 2015-2026\n\n{diag.round(3).to_markdown()}\n")
        print(diag.round(3))
    path = log_run("j4_detail", log_rows)
    lines.append(f"Run log: `{path.name}`\n")
    root = Path(__file__).resolve().parents[2]
    (root / "docs" / "auto" / "j4" / "results_raw.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
