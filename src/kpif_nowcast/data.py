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


COMPONENTS = {
    "TXKS": "services",
    "KS": "capital_stock",
    "LIVS": "food",
    "NRG": "energy",
    "VXLIVSNRG": "goods",
}
COMPONENT_CODES = {
    "0000084S": "index",
    "0000084V": "mm_official",
    "0000084W": "weight",  # year-to-month weight (per mille), fixed within a calendar year
    "0000084R": "effect_month",  # contribution to KPIF's monthly change, pp
}


def build_components() -> pd.DataFrame:
    """KPIF analysis groups (TAB6628), long format: month, component, index, mm, weight, effect."""
    long = scb.fetch_table(
        "TAB6628",
        {"VaruTjanstegrupp": ",".join(COMPONENTS), "ContentsCode": ",".join(COMPONENT_CODES), "Tid": "*"},
    )
    long["component"] = long["VaruTjanstegrupp"].map(COMPONENTS)
    long["series"] = long["ContentsCode"].map(COMPONENT_CODES)
    wide = long.pivot_table(index=["Tid", "component"], columns="series", values="value").reset_index()
    wide["month"] = scb.month_to_period(wide["Tid"])
    return wide.drop(columns="Tid").sort_values(["component", "month"])[
        ["month", "component", "index", "mm_official", "weight", "effect_month"]
    ]


def load_components() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "components.csv")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    return df


def build_riksbank_forecasts() -> pd.DataFrame:
    return riksbank.fetch_forecasts("SEMCPIFNAYNA")


def refresh() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    kpif = build_kpif()
    kpif.to_csv(PROCESSED_DIR / "kpif.csv")
    comp = build_components()
    comp.to_csv(PROCESSED_DIR / "components.csv", index=False)
    print(f"Components: {sorted(comp['component'].unique())}, {comp['month'].min()}..{comp['month'].max()}")
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
