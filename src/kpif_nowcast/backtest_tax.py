"""Phase 4b backtest: does a known-tax-changes calendar help?

Tax effect per month = KPIF m/m minus KPIF at constant taxes m/m (SCB TAB6592).
Run: python -m kpif_nowcast.backtest_tax
"""

from __future__ import annotations

import pandas as pd

from kpif_nowcast.backtest import OUT_DIR, score
from kpif_nowcast.baselines import all_baselines
from kpif_nowcast.component_model import ENERGY, ENERGY_FUEL_ONLY, component_forecast
from kpif_nowcast.data import load_components, load_kpif, load_riksbank_forecasts, load_tax_effects
from kpif_nowcast.features import load_features
from kpif_nowcast.riksbank_benchmark import riksbank_at_deadline


def main() -> None:
    kpif, comps, feats, tax = load_kpif(), load_components(), load_features(), load_tax_effects()
    index, actual = kpif["index"], kpif["yy_official"]

    preds = all_baselines(index)[["naive_yy", "seasonal_trend_5y"]]
    preds = preds.join(riksbank_at_deadline(load_riksbank_forecasts(), kpif.index)[["riksbank"]])
    preds["comp_fuel"] = component_forecast(index, comps, feats, {"energy": ENERGY_FUEL_ONLY})["yy_hat"]
    preds["comp_fuel+tax"] = component_forecast(index, comps, feats, {"energy": ENERGY_FUEL_ONLY}, tax)["yy_hat"]
    preds["comp_fuel_el"] = component_forecast(index, comps, feats, {"energy": ENERGY})["yy_hat"]
    best = component_forecast(index, comps, feats, {"energy": ENERGY}, tax)
    preds["comp_fuel_el+tax"] = best["yy_hat"]

    periods = {
        "2015-2026 (fuel-only energy)": ("2015-01", ["riksbank", "seasonal_trend_5y", "comp_fuel", "comp_fuel+tax"]),
        "2024-2026 (all models, common sample)": ("2024-01", list(preds)),
    }
    report = []
    for label, (start, cols) in periods.items():
        p = preds.loc[pd.Period(start, "M"):, cols].dropna()
        table = score(actual, p)
        report.append(f"## {label}\n\n{table.round(3).to_markdown()}\n")
        print(f"\n{label}\n{table.round(3)}")

    err = (preds[["riksbank", "comp_fuel_el", "comp_fuel_el+tax"]].sub(actual, axis=0)).loc["2024-01":].dropna()
    big = err.loc[err["comp_fuel_el"].abs().sort_values(ascending=False).index[:8]].round(2)
    big["tax_effect"] = best["tax_effect"].reindex(big.index).round(2)
    report.append(f"## Largest misses 2024-2026 (forecast - outcome, pp y/y)\n\n{big.to_markdown()}\n")
    print(f"\nLargest misses:\n{big}")
    (OUT_DIR / "phase4b_tax_scores.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
