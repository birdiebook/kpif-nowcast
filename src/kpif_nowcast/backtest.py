"""Phase 2 backtest: naive baselines vs the Riksbank, KPIF y/y one month ahead.

Run: python -m kpif_nowcast.backtest
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from kpif_nowcast.baselines import all_baselines
from kpif_nowcast.data import load_kpif, load_riksbank_forecasts
from kpif_nowcast.riksbank_benchmark import riksbank_at_deadline

OUT_DIR = Path(__file__).resolve().parents[2] / "outputs"


def score(actual: pd.Series, forecasts: pd.DataFrame) -> pd.DataFrame:
    """MAE/RMSE in percentage points, and how often the forecast rounds to SCB's one-decimal figure."""
    out = {}
    actual = actual.reindex(forecasts.index)
    for name in forecasts:
        err = (forecasts[name] - actual).dropna()
        hit = (forecasts[name].round(1) == actual.round(1))[err.index]
        out[name] = {
            "MAE": err.abs().mean(),
            "RMSE": np.sqrt((err**2).mean()),
            "bias": err.mean(),
            "exact_hit_%": 100 * hit.mean(),
            "n": len(err),
        }
    return pd.DataFrame(out).T.sort_values("MAE")


def main() -> None:
    kpif = load_kpif()
    actual = kpif["yy_official"]
    preds = all_baselines(kpif["index"])

    rb = riksbank_at_deadline(load_riksbank_forecasts(), kpif.index)
    preds = preds.join(rb[["riksbank"]])

    periods = {
        "1995-2026 (baselines only)": ("1995-01", None, [c for c in preds if c != "riksbank"]),
        "2015-2026 (vs Riksbank)": ("2015-01", None, list(preds)),
        "2022-2023 (inflation shock)": ("2022-01", "2023-12", list(preds)),
        "2024-2026 (latest)": ("2024-01", None, list(preds)),
    }

    OUT_DIR.mkdir(exist_ok=True)
    report = []
    for label, (start, end, cols) in periods.items():
        sl = slice(pd.Period(start, "M"), pd.Period(end, "M") if end else None)
        p = preds.loc[sl, cols]
        if "riksbank" in cols:
            p = p.dropna(subset=["riksbank"])  # common sample
        table = score(actual.loc[sl], p)
        report.append(f"## {label}\n\n{table.round(3).to_markdown()}\n")
        print(f"\n{label}\n{table.round(3)}")

    (OUT_DIR / "phase2_scores.md").write_text("\n".join(report), encoding="utf-8")

    recent = preds.loc[pd.Period("2021-01", "M"):].join(actual.rename("actual"))
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(recent.index.to_timestamp(), recent["actual"], color="black", lw=2, label="KPIF y/y (outcome)")
    for col in ["seasonal_trend_5y", "naive_yy", "riksbank"]:
        ax.plot(recent.index.to_timestamp(), recent[col], lw=1.2, label=col)
    ax.set_ylabel("% y/y")
    ax.set_title("KPIF one month ahead: baselines vs Riksbank")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "phase2_forecasts.png", dpi=120)

    rb.join(actual.rename("actual")).to_csv(OUT_DIR / "riksbank_at_deadline.csv")
    print(f"\nRiksbank months-ahead distribution:\n{rb['rb_months_ahead'].value_counts().sort_index()}")


if __name__ == "__main__":
    main()
