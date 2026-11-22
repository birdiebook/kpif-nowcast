"""Phase 4/4b backtest: bottom-up component models vs phase 3, baselines and the Riksbank.

Run: python -m kpif_nowcast.backtest_phase4
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from kpif_nowcast.backtest import OUT_DIR, score
from kpif_nowcast.baselines import all_baselines, seasonal_trend_additive
from kpif_nowcast.component_model import ENERGY, ENERGY_FUEL_ONLY, component_forecast, ki_corrections
from kpif_nowcast.data import load_components, load_kpif, load_riksbank_forecasts
from kpif_nowcast.features import load_features
from kpif_nowcast.models import expanding_energy_model
from kpif_nowcast.riksbank_benchmark import riksbank_at_deadline


def main() -> None:
    kpif, comps, feats = load_kpif(), load_components(), load_features()
    index, actual = kpif["index"], kpif["yy_official"]

    preds = all_baselines(index)[["naive_yy", "seasonal_trend_5y"]]
    preds = preds.join(riksbank_at_deadline(load_riksbank_forecasts(), kpif.index)[["riksbank"]])
    preds["phase3_fuel_el"] = expanding_energy_model(index, feats, ["fuel_chg", "el_chg"], "2021-12")["yy_hat"]

    models = {
        "comp_fuel": {"energy": ENERGY_FUEL_ONLY},
        "comp_fuel+ki_l1": {"energy": ENERGY_FUEL_ONLY, **ki_corrections("l1")},
        "comp_fuel+ki_dev": {"energy": ENERGY_FUEL_ONLY, **ki_corrections("dev")},
        "comp_fuel_el": {"energy": ENERGY},
        "comp_fuel_el+ki_l1": {"energy": ENERGY, **ki_corrections("l1")},
        "comp_fuel_el+ki_dev": {"energy": ENERGY, **ki_corrections("dev")},
    }
    results = {name: component_forecast(index, comps, feats, spec) for name, spec in models.items()}
    for name, res in results.items():
        preds[name] = res["yy_hat"]

    fuel_only = ["riksbank", "seasonal_trend_5y"] + [m for m in models if "_el" not in m]
    periods = {
        "2015-2026 (fuel-only energy, KI from 2005)": ("2015-01", fuel_only),
        "2024-2026 (all models, common sample)": ("2024-01", list(preds)),
    }
    report = []
    for label, (start, cols) in periods.items():
        p = preds.loc[pd.Period(start, "M"):, cols].dropna()
        table = score(actual, p)
        report.append(f"## {label}\n\n{table.round(3).to_markdown()}\n")
        print(f"\n{label}\n{table.round(3)}")

    # Component-level error, 2024-2026
    effects = comps.pivot(index="month", columns="component", values="effect_month")
    since = pd.Period("2024-01", "M")
    rows = {"baseline": (effects.apply(seasonal_trend_additive) - effects).loc[since:].abs().mean()}
    for name in ["comp_fuel_el", "comp_fuel_el+ki_l1", "comp_fuel_el+ki_dev"]:
        fc = results[name].filter(like="fc_").rename(columns=lambda c: c[3:])
        rows[name] = (fc - effects).loc[since:].dropna().abs().mean()
    mae = pd.DataFrame(rows).round(3)
    report.append(f"## Component MAE 2024-2026 (pp of KPIF m/m)\n\n{mae.to_markdown()}\n")
    print(f"\nComponent MAE 2024-2026:\n{mae}")

    latest = results["comp_fuel_el+ki_l1"].filter(like=":b_").iloc[-1].round(4)
    report.append(f"## Latest coefficients, comp_fuel_el+ki_l1\n\n{latest.to_frame('coef').to_markdown()}\n")
    print(f"\nLatest coefficients:\n{latest}")
    (OUT_DIR / "phase4_scores.md").write_text("\n".join(report), encoding="utf-8")

    best = results["comp_fuel_el+ki_l1"].filter(like="fc_").rename(columns=lambda c: c[3:])
    comp_err = (best - effects).loc[since:].dropna()
    fig, ax = plt.subplots(figsize=(11, 5))
    comp_err.plot(kind="bar", stacked=True, ax=ax, width=0.85)
    ax.set_xticklabels([str(p) for p in comp_err.index], rotation=90, fontsize=7)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("forecast - outcome, pp of KPIF m/m")
    ax.set_title("Component model (fuel+el+KI) errors by component, 2024-2026")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "phase4_component_errors.png", dpi=120)


if __name__ == "__main__":
    main()
