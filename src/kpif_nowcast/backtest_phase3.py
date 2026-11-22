"""Phase 3 backtest: does adding energy prices beat the baselines and the Riksbank?

Run: python -m kpif_nowcast.backtest_phase3
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from kpif_nowcast.backtest import OUT_DIR, score
from kpif_nowcast.baselines import all_baselines
from kpif_nowcast.data import load_kpif, load_riksbank_forecasts
from kpif_nowcast.features import load_features
from kpif_nowcast.models import expanding_energy_model
from kpif_nowcast.riksbank_benchmark import riksbank_at_deadline


def main() -> None:
    kpif = load_kpif()
    index, actual = kpif["index"], kpif["yy_official"]
    feats = load_features()

    preds = all_baselines(index)[["naive_yy", "seasonal_trend_5y"]]
    preds = preds.join(riksbank_at_deadline(load_riksbank_forecasts(), kpif.index)[["riksbank"]])

    # Fuel only: Brent history allows training from 2001.
    fuel = expanding_energy_model(index, feats, ["fuel_chg"], train_start="2001-01")
    # Fuel + electricity: spot data from 2021-11, so first change is 2021-12.
    both = expanding_energy_model(index, feats, ["fuel_chg", "el_chg"], train_start="2021-12")
    preds["model_fuel"] = fuel["yy_hat"]
    preds["model_fuel_el"] = both["yy_hat"]

    periods = {
        "2015-2026 (fuel model vs Riksbank)": ("2015-01", ["naive_yy", "seasonal_trend_5y", "riksbank", "model_fuel"]),
        "2024-2026 (all models, common sample)": ("2024-01", list(preds)),
    }
    report = []
    for label, (start, cols) in periods.items():
        p = preds.loc[pd.Period(start, "M"):, cols].dropna()
        table = score(actual, p)
        report.append(f"## {label}\n\n{table.round(3).to_markdown()}\n")
        print(f"\n{label}\n{table.round(3)}")

    coefs = both[["b_fuel_chg", "b_el_chg", "n_train"]].iloc[[0, len(both) // 2, -1]]
    report.append(f"## Coefficients, fuel+el model (start, middle, latest)\n\n{coefs.round(4).to_markdown()}\n")
    print(f"\nCoefficients fuel+el:\n{coefs.round(4)}")
    print(f"\nLatest fuel-only coefficient: {fuel['b_fuel_chg'].iloc[-1]:.4f}")
    (OUT_DIR / "phase3_scores.md").write_text("\n".join(report), encoding="utf-8")

    recent = preds.loc[pd.Period("2024-01", "M"):].join(actual.rename("actual"))
    fig, ax = plt.subplots(figsize=(11, 5))
    t = recent.index.to_timestamp()
    ax.plot(t, recent["actual"], color="black", lw=2, label="KPIF y/y (outcome)")
    for col in ["seasonal_trend_5y", "riksbank", "model_fuel_el"]:
        ax.plot(t, recent[col], lw=1.3, label=col)
    ax.set_ylabel("% y/y")
    ax.set_title("KPIF one month ahead, 2024-2026: energy model vs baseline and Riksbank")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "phase3_forecasts.png", dpi=120)


if __name__ == "__main__":
    main()
