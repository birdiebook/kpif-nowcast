"""Publication calendar: when a catalog value was really known (K11 audit, docs/auto2/k11/granskning.md).

`Spec.lag_days` is the usual delay after period end. Some releases come later than usual (holidays,
the euro area flash for December, the 2025 US government shutdown). Those are listed here with their
documented release date, and `known_from` is set to the later of the two:

    known_from = max(period end + lag_days, documented release date)

`enforce()` applies this to the observation table when it is loaded, so every model sees the corrected
dates even if data/observations.parquet was backfilled with older (shorter) lags. It only ever moves
known_from later, never earlier.

Release dates and sources: docs/publiceringskalender.md.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kpif_nowcast.catalog_rents import RELEASES as RENT_NEGOTIATED_RELEASES

EA_FLASH_KEYS = ("ea_flash_total", "ea_flash_energy", "ea_flash_food", "ea_flash_goods", "ea_flash_services")

# Euro area HICP flash released after day 4 of the following month (Eurostat euro-indicator release codes,
# 2-DDMMYYYY-ap). Every other month 2017-08..2026-10 was released on or before day 4 (K11 probe of days 5-7).
EA_FLASH_LATE = {
    "2017-12": "2018-01-05",
    "2019-12": "2020-01-07",
    "2020-12": "2021-01-07",
    "2021-12": "2022-01-07",
    "2022-12": "2023-01-06",
    "2023-12": "2024-01-05",
    "2024-12": "2025-01-07",
    "2025-12": "2026-01-07",
}

# BLS PPI releases delayed by the 2025 lapse in appropriations (BLS, historical release dates, notes 8-11).
BLS_PPI_LATE = {
    "2025-09": "2025-11-25",
    "2025-10": "2026-01-14",
    "2025-11": "2026-01-14",
    "2025-12": "2026-01-30",
}

LATE_RELEASES: dict[str, dict[str, str]] = {
    **{k: EA_FLASH_LATE for k in EA_FLASH_KEYS},
    "freight_ppi_deepsea": BLS_PPI_LATE,
    # L3: years without a verified spring publication -> upload date of the source report (catalog_rents)
    "rent_negotiated": RENT_NEGOTIATED_RELEASES,
}


def release_dates(series: str) -> dict[pd.Period, pd.Timestamp]:
    return {pd.Period(p, "M"): pd.Timestamp(d) for p, d in LATE_RELEASES.get(series, {}).items()}


def known_from(series: str, periods: pd.PeriodIndex, lag_days: int) -> pd.DatetimeIndex:
    """max(period end + lag, documented release date) per period."""
    periods = pd.PeriodIndex(periods, freq="M")
    base = (periods + 1).to_timestamp() - pd.Timedelta(days=1) + pd.Timedelta(days=lag_days)
    late = release_dates(series)
    if not late:
        return pd.DatetimeIndex(base)
    extra = pd.DatetimeIndex([late.get(p, pd.NaT) for p in periods])
    later = np.asarray(extra > base)
    return pd.DatetimeIndex(np.where(later, extra.to_numpy(), base.to_numpy()))


def enforce(table: pd.DataFrame) -> pd.DataFrame:
    """Move known_from of backfill rows (and first-release fetch rows) to at least the documented date."""
    if table.empty:
        return table
    from kpif_nowcast.catalog import by_key

    specs = by_key()
    out = table.copy()
    mask = out["source"].isin(["backfill", "fetch"]) & out["series"].isin(specs.keys())
    if not mask.any():
        return out
    sub = out.loc[mask, ["series", "period"]]
    floor = pd.Series(pd.NaT, index=sub.index, dtype="datetime64[ns]")
    for key, idx in sub.groupby("series").groups.items():
        kf = known_from(key, pd.PeriodIndex(sub.loc[idx, "period"], freq="M"), specs[key].lag_days)
        floor.loc[idx] = kf.to_numpy()
    cur = pd.to_datetime(out.loc[mask, "known_from"])
    # fetch rows were stored as min(default, fetch date): a value seen at fetch time was known then.
    is_fetch = out.loc[mask, "source"] == "fetch"
    fetched = pd.to_datetime(out.loc[mask, "fetched_at"])
    floor = floor.where(~is_fetch, floor.where(floor < fetched, fetched))
    out.loc[mask, "known_from"] = cur.where(cur >= floor, floor)
    return out
