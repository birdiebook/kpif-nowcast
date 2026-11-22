"""Phase 4 backtest: bottom-up component model vs phase 3, baselines and the Riksbank.

Run: python -m kpif_nowcast.backtest_phase4
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from kpif_nowcast.backtest import OUT_DIR, score
from kpif_nowcast.baselines import all_baselines, seasonal_trend_additive
from kpif_nowcast.component_model import component_forecast
from kpif_nowcast.data import load_components, load_kpif, load_riksbank_forecasts
from kpif_nowcast.features import load_features
from kpif_nowcast.models import expanding_energy_model
from kpif_nowcast.riksbank_benchmark import riksbank_at_deadline


def main() -> None:
    kpif, comps, feats = load_kpif(), load_components(), load_features()
    index, actual = kpif["index"], kpif["yy_official"]

    preds = all_baselines(index)[["naive_yy", "seasonal_trend_5y"]]
    preds = preds.join(riksbank_at_deadline(load_riksbank_forecasts(), kpif.index)[["riksbank"]])
    preds["phase3_fuel"] = expanding_energy_model(index, feats, ["fuel_chg"], "2001-01")["yy_hat"]
    preds["phase3_fuel_el"] = expanding_energy_model(index, feats, ["fuel_chg", "el_chg"], "2021-12")["yy_hat"]

    comp_fuel = component_forecast(index, comps, feats, ["fuel_chg"], "2005-01")
    comp_both = component_forecast(index, comps, feats, ["fuel_chg", "el_chg"], "2021-12")
    preds["comp_fuel"] = comp_fuel["yy_hat"]
    preds["comp_fuel_el"] = comp_both["yy_hat"]

    periods = {
        "2015-2026 (fuel-only models)": ("2015-01", ["riksbank", "seasonal_trend_5y", "phase3_fuel", "comp_fuel"]),
        "2024-2026 (all models, common sample)": ("2024-01", list(preds)),
    }
    report = []
    for label, (start, cols) in periods.items():
        p = preds.loc[pd.Period(start, "M"):, cols].dropna()
        table = score(actual, p)
        report.append(f"## {label}\n\n{table.round(3).to_markdown()}\n")
        print(f"\n{label}\n{table.round(3)}")

    # Component-level error, 2024-2026: where does the best model still miss?
    effects = comps.pivot(index="month", columns="component", values="effect_month")
    fc = comp_both.filter(like="fc_").rename(columns=lambda c: c[3:])
    comp_err = (fc - effects).loc[pd.Period("2024-01", "M"):].dropna()
    base_err = (effects.apply(seasonal_trend_additive) - effects).loc[comp_err.index]
    mae = pd.DataFrame({"baseline": base_err.abs().mean(), "comp_fuel_el": comp_err.abs().mean()}).round(3)
    report.append(f"## Component MAE 2024-2026 (pp of KPIF m/m)\n\n{mae.to_markdown()}\n")
    print(f"\nComponent MAE 2024-2026:\n{mae}")
    print(f"\nEnergy coefficients (latest): {comp_both[['b_fuel_chg', 'b_el_chg']].iloc[-1].round(4).to_dict()}")
    (OUT_DIR / "phase4_scores.md").write_text("\n".join(report), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(11, 5))
    comp_err.plot(kind="bar", stacked=True, ax=ax, width=0.85)
    ax.set_xticklabels([str(p) for p in comp_err.index], rotation=90, fontsize=7)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("forecast - outcome, pp of KPIF m/m")
    ax.set_title("Component model errors by component, 2024-2026")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "phase4_component_errors.png", dpi=120)


if __name__ == "__main__":
    main()
