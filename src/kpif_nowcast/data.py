"""Build the processed datasets used by models and backtests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from kpif_nowcast.sources import riksbank, scb

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

KPIF_CODES = {"000007ZN": "index", "000007ZO": "mm_official", "000007ZM": "yy_official"}


def build_kpif() -> pd.DataFrame:
    """Monthly KPIF: index (2020=100) plus SCB's official m/m and y/y (one decimal)."""
    long = scb.fetch_table("TAB6590")
    long["series"] = long["ContentsCode"].map(KPIF_CODES)
    wide = long.pivot(index="Tid", columns="series", values="value")
    wide.index = scb.month_to_period(wide.index.to_series())
    wide = wide.sort_index().astype(float)
    wide.index.name = "month"
    return wide[["index", "mm_official", "yy_official"]]


def build_riksbank_forecasts() -> pd.DataFrame:
    return riksbank.fetch_forecasts("SEMCPIFNAYNA")


def refresh() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    kpif = build_kpif()
    kpif.to_csv(PROCESSED_DIR / "kpif.csv")
    rb = build_riksbank_forecasts()
    rb.to_csv(PROCESSED_DIR / "riksbank_kpif_forecasts.csv", index=False)
    print(f"KPIF: {kpif.index.min()}..{kpif.index.max()} ({len(kpif)} months)")
    print(f"Riksbank: {rb['policy_round'].nunique()} vintages, {rb['policy_round'].min()}..{rb['policy_round'].max()}")


def load_kpif() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "kpif.csv")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    return df.set_index("month")


def load_riksbank_forecasts() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "riksbank_kpif_forecasts.csv")
    df["cutoff"] = pd.PeriodIndex(df["cutoff"], freq="M")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    df["published"] = pd.to_datetime(df["published"])
    return df


if __name__ == "__main__":
    refresh()
