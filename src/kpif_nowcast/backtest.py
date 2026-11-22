"""Common backtest: baselines, Riksbank, rb_updated and the component models, KPIF y/y one month ahead.

Every model is compared with rb_updated ("Riksbank + latest miss") via one
Diebold-Mariano test, and each run is logged to experiments/runs/<utc>_<name>.csv.
Write the hypothesis and expected sign in docs/beslutslogg.md ("Min gissning innan")
before running a new variant.

Run: python -m kpif_nowcast.backtest [--name <run name>]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from kpif_nowcast.baselines import all_baselines
from kpif_nowcast.component_model import ENERGY, ENERGY_FUEL_ONLY, component_forecast
from kpif_nowcast.data import load_components, load_kpif, load_riksbank_forecasts
from kpif_nowcast.evaluation import dm_test, log_run, metrics
from kpif_nowcast.features import load_features
from kpif_nowcast.riksbank_benchmark import riksbank_at_deadline

OUT_DIR = Path(__file__).resolve().parents[2] / "outputs"
BENCHMARK = "rb_updated"


def score(actual: pd.Series, forecasts: pd.DataFrame) -> pd.DataFrame:
    """MAE/RMSE in percentage points, and how often the forecast rounds to SCB's one-decimal figure."""
    out = {}
    actual = actual.reindex(forecasts.index)
    for name in forecasts:
        err = (forecasts[name] - actual).dropna()
        hit = (forecasts[name].round(1) == actual.round(1))[err.index]
        out[name] = {**metrics(err), "exact_hit_%": 100 * hit.mean()}
    return pd.DataFrame(out).T.sort_values("MAE")


def build_predictions() -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """All forecasts per target month, the outcome, and the Riksbank vintage details."""
    kpif, comps, feats = load_kpif(), load_components(), load_features()
    index, actual = kpif["index"], kpif["yy_official"]
    preds = all_baselines(index)
    rb = riksbank_at_deadline(load_riksbank_forecasts(), kpif.index, actual)
    preds = preds.join(rb[["riksbank", BENCHMARK]])
    preds["comp_fuel"] = component_forecast(index, comps, feats, {"energy": ENERGY_FUEL_ONLY})["yy_hat"]
    preds["comp_fuel_el"] = component_forecast(index, comps, feats, {"energy": ENERGY})["yy_hat"]
    return preds, actual, rb


# Model selection uses the longest possible sample. 2024-2026 has already been used
# for ~50 variants, so it is reported but marked "used": do not pick models on it.
PERIODS = {
    "2015-2026": ("2015-01", ["naive_yy", "seasonal_mean_5y", "seasonal_trend_5y", "riksbank", BENCHMARK, "comp_fuel"]),
    "2024-2026 (used)": ("2024-01", None),
}


def main(name: str = "backtest") -> None:
    preds, actual, rb = build_predictions()

    OUT_DIR.mkdir(exist_ok=True)
    report, log_rows = [], []
    for label, (start, cols) in PERIODS.items():
        p = preds.loc[pd.Period(start, "M"):, cols or list(preds)]
        p = p[actual.reindex(p.index).notna()].dropna()  # common sample with known outcome
        table = score(actual, p)
        err = p.sub(actual.reindex(p.index), axis=0)
        sentences = []
        for model in table.index:
            if model == BENCHMARK:
                table.loc[model, "dm_p"] = float("nan")
                continue
            dm = dm_test(err[model].to_numpy(), err[BENCHMARK].to_numpy())
            table.loc[model, "dm_p"] = dm.p
            sentences.append(dm.sentence(model, BENCHMARK))
        for model, row in table.iterrows():
            log_rows.append({"variant": model, "period": label, "n": int(row["n"]),
                             "MAE": round(row["MAE"], 4), "dm_p_vs_rb_updated": round(row["dm_p"], 4)})
        report.append(f"## {label}\n\n{table.round(3).to_markdown()}\n\n" + "\n".join(f"- {s}" for s in sentences) + "\n")
        print(f"\n{label}\n{table.round(3)}\n" + "\n".join(sentences))

    # Riksbank and rb_updated by months since the vintage's cutoff (at 1 month they are identical)
    sl = rb.loc[pd.Period("2015-01", "M"):].dropna(subset=["riksbank"])
    sl = sl[actual.reindex(sl.index).notna()]
    by_age = (
        sl[["riksbank", BENCHMARK]].sub(actual.reindex(sl.index), axis=0).abs()
        .groupby(sl["rb_months_ahead"]).mean().assign(n=sl.groupby("rb_months_ahead").size())
    )
    report.append(f"## MAE by months since Riksbank cutoff, 2015-2026\n\n{by_age.round(3).to_markdown()}\n")
    print(f"\nMAE by months since Riksbank cutoff, 2015-2026:\n{by_age.round(3)}")

    (OUT_DIR / "backtest_scores.md").write_text("\n".join(report), encoding="utf-8")
    path = log_run(name, log_rows)
    print(f"\nRun logged to {path.relative_to(OUT_DIR.parent)}")

    recent = preds.loc[pd.Period("2021-01", "M"):].join(actual.rename("actual"))
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(recent.index.to_timestamp(), recent["actual"], color="black", lw=2, label="KPIF y/y (outcome)")
    for col in ["naive_yy", "riksbank", BENCHMARK, "comp_fuel_el"]:
        ax.plot(recent.index.to_timestamp(), recent[col], lw=1.2, label=col)
    ax.set_ylabel("% y/y")
    ax.set_title("KPIF one month ahead: models vs Riksbank")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "backtest_forecasts.png", dpi=120)
    rb.join(actual.rename("actual")).to_csv(OUT_DIR / "riksbank_at_deadline.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="backtest", help="short run name, used in the log file name")
    main(parser.parse_args().name)
