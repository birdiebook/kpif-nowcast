"""Naive baseline forecasts for KPIF.

Information set for target month t: the KPIF index up to and including t-1.
(The forecast is locked before SCB's flash estimate, ~day 4 of month t+1;
by then the final figure for t-1 has been published, but not t.)

Every baseline forecasts the month-on-month change for t, which is turned
into a y/y forecast via the known index at t-1 and t-12.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def mm_change(index: pd.Series) -> pd.Series:
    return index / index.shift(1) - 1


def yy_from_mm(index: pd.Series, mm_hat: pd.Series) -> pd.Series:
    """Index forecast for t = index[t-1] * (1 + mm_hat[t]); y/y vs index[t-12]. In percent."""
    index_hat = index.shift(1) * (1 + mm_hat)
    return (index_hat / index.shift(12) - 1) * 100


def naive_yy(index: pd.Series) -> pd.Series:
    """Next month's y/y equals last month's y/y."""
    yy = (index / index.shift(12) - 1) * 100
    return yy.shift(1)


def seasonal_last_year(index: pd.Series) -> pd.Series:
    """This month's m/m equals the same month last year."""
    return yy_from_mm(index, mm_change(index).shift(12))


def seasonal_mean(index: pd.Series, years: int = 5) -> pd.Series:
    """This month's m/m equals the average of the same calendar month over the last `years` years."""
    mm = mm_change(index)
    lags = pd.concat([mm.shift(12 * k) for k in range(1, years + 1)], axis=1)
    return yy_from_mm(index, lags.mean(axis=1))


def seasonal_trend(index: pd.Series, years: int = 5) -> pd.Series:
    """Seasonal pattern + current trend.

    m/m forecast = (average m/m over the last 12 months)
                 + (how much this calendar month has typically deviated from
                    its 12-month average over the last `years` years).
    Captures both "January is usually low" and "inflation is currently high".
    """
    mm = mm_change(index)
    trend_12m = mm.rolling(12).mean()
    deviation = mm - trend_12m
    seasonal = pd.concat([deviation.shift(12 * k) for k in range(1, years + 1)], axis=1).mean(axis=1)
    return yy_from_mm(index, trend_12m.shift(1) + seasonal)


# seasonal_last_year is mathematically identical to naive_yy (repeating last
# year's m/m for month t keeps the 12-month window's sum unchanged), so it is
# kept as a function for reference but not reported.
BASELINES = {
    "naive_yy": naive_yy,
    "seasonal_mean_5y": seasonal_mean,
    "seasonal_trend_5y": seasonal_trend,
}


def all_baselines(index: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({name: fn(index) for name, fn in BASELINES.items()}).replace([np.inf, -np.inf], np.nan)
