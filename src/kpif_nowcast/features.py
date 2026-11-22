"""Monthly features for the KPIF nowcast.

Every feature for target month t must be observable at the deadline (day 4 of t+1):
- electricity: full month t spot prices (published the day before delivery) -> OK
- fuel proxy: Brent in SEK, days 1-25 of t (mirrors SCB's measurement window) -> OK
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from kpif_nowcast.sources import elpris, fred, riksbank

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

# Rough split of household electricity use between the southern zones. SE1/SE2
# (north, ~10-15% of households, prices usually close to SE3 or lower) are left out
# for now. ASSUMPTION – to be replaced with consumption-based weights.
ZONE_WEIGHTS = {"SE3": 0.7, "SE4": 0.3}

FUEL_WINDOW_LAST_DAY = 25


def electricity_monthly() -> pd.DataFrame:
    """Monthly mean spot price per zone and a weighted average (SEK/kWh)."""
    daily = pd.concat([elpris.daily_prices(z) for z in ZONE_WEIGHTS], axis=1)
    monthly = daily.groupby(daily.index.to_period("M")).mean()
    monthly = monthly[daily.groupby(daily.index.to_period("M")).size() >= 28]  # complete months only
    monthly["el_spot"] = sum(monthly[z] * w for z, w in ZONE_WEIGHTS.items())
    return monthly


def fuel_proxy_monthly() -> pd.Series:
    """Brent crude in SEK per barrel, mean over days 1-25 of each month."""
    brent = fred.fetch_series("DCOILBRENTEU")
    usdsek = riksbank.fetch_swea("SEKUSDPMI")
    df = pd.concat([brent, usdsek], axis=1).dropna()
    df = df[df.index.day <= FUEL_WINDOW_LAST_DAY]
    sek = df["DCOILBRENTEU"] * df["SEKUSDPMI"]
    return sek.groupby(sek.index.to_period("M")).mean().rename("brent_sek")


def build_features() -> pd.DataFrame:
    el = electricity_monthly()
    fuel = fuel_proxy_monthly()
    feats = pd.DataFrame(index=fuel.index)
    feats["brent_sek"] = fuel
    feats["fuel_chg"] = np.log(fuel).diff()  # log change vs previous month
    feats = feats.join(el[["el_spot"]])
    feats["el_chg"] = feats["el_spot"].diff()  # SEK/kWh change (spot can be near zero, so no log)
    feats.index.name = "month"
    return feats


def refresh() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    f = build_features()
    f.to_csv(PROCESSED_DIR / "features.csv")
    print(f.dropna().tail())


def load_features() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "features.csv")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    return df.set_index("month")


if __name__ == "__main__":
    refresh()
