"""Riksbank KPIF forecast as it was known at our forecast deadline.

For target month t the deadline is day 4 of month t+1. We use the latest
vintage published strictly before the deadline, and only if t is a forecast
in that vintage (t after its cutoff), never an outcome.
"""

from __future__ import annotations

import pandas as pd

DEADLINE_DAY = 4


def deadline(month: pd.Period) -> pd.Timestamp:
    return (month + 1).to_timestamp() + pd.Timedelta(days=DEADLINE_DAY - 1)


def riksbank_at_deadline(forecasts: pd.DataFrame, months: pd.PeriodIndex) -> pd.DataFrame:
    vintages = (
        forecasts[["policy_round", "cutoff", "published"]].drop_duplicates().sort_values("published")
    )
    rows = []
    for t in months:
        usable = vintages[(vintages["published"] < deadline(t)) & (vintages["cutoff"] < t)]
        if usable.empty:
            continue
        v = usable.iloc[-1]
        hit = forecasts[(forecasts["policy_round"] == v["policy_round"]) & (forecasts["month"] == t)]
        if hit.empty:
            continue
        rows.append(
            {
                "month": t,
                "riksbank": hit["value"].iloc[0],
                "rb_round": v["policy_round"],
                "rb_months_ahead": (t - v["cutoff"]).n,
            }
        )
    return pd.DataFrame(rows).set_index("month")
