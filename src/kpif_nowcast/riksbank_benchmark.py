"""Riksbank KPIF forecast as it was known at our forecast deadline.

For target month t the deadline is day 4 of month t+1. We use the latest
vintage published strictly before the deadline, and only if t is a forecast
in that vintage (t after its cutoff), never an outcome.

`rb_updated` ("Riksbank + latest miss") shifts that vintage's path by its known
miss for t-1:

    rb_updated_t = RB_t + (KPIF_yy_{t-1} - RB_{t-1})

The vintage is usually 2-3 months old at our deadline, and inflation is
persistent, so last month's miss is a good guess for this month's. No parameter
is estimated. Information set: KPIF y/y for t-1 is published mid-month t, well
before the deadline. When the vintage's cutoff is t-1 itself (1 month since
cutoff), RB_{t-1} is not a forecast and rb_updated equals RB_t.
"""

from __future__ import annotations

import pandas as pd

DEADLINE_DAY = 4


def deadline(month: pd.Period) -> pd.Timestamp:
    return (month + 1).to_timestamp() + pd.Timedelta(days=DEADLINE_DAY - 1)


def riksbank_at_deadline(
    forecasts: pd.DataFrame, months: pd.PeriodIndex, actual_yy: pd.Series | None = None
) -> pd.DataFrame:
    """Per target month: the vintage's forecast for t ("riksbank") and for t-1 ("rb_prev"),
    months since the vintage's cutoff ("rb_months_ahead"), and, if `actual_yy` is given, "rb_updated"."""
    vintages = (
        forecasts[["policy_round", "cutoff", "published"]].drop_duplicates().sort_values("published")
    )
    rows = []
    for t in months:
        usable = vintages[(vintages["published"] < deadline(t)) & (vintages["cutoff"] < t)]
        if usable.empty:
            continue
        v = usable.iloc[-1]
        path = forecasts[forecasts["policy_round"] == v["policy_round"]].set_index("month")["value"]
        if t not in path.index:
            continue
        months_ahead = (t - v["cutoff"]).n
        rows.append(
            {
                "month": t,
                "riksbank": path[t],
                # t-1 is a forecast in this vintage only if the cutoff is before t-1
                "rb_prev": path.get(t - 1) if months_ahead > 1 else None,
                "rb_round": v["policy_round"],
                "rb_months_ahead": months_ahead,
            }
        )
    columns = ["month", "riksbank", "rb_prev", "rb_round", "rb_months_ahead"]
    rb = pd.DataFrame(rows, columns=columns).set_index("month")
    rb["rb_prev"] = rb["rb_prev"].astype(float)
    if actual_yy is not None:
        miss_prev = actual_yy.reindex(rb.index - 1).to_numpy() - rb["rb_prev"]
        rb["rb_updated"] = rb["riksbank"] + miss_prev.where(rb["rb_months_ahead"] > 1, 0.0)
    return rb
