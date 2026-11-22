"""Versioned observations: (series, period, value, known_from).

Why: for longer horizons we use series that are published with a delay (the
"ragged edge") and later revised (GDP indicator, seasonally adjusted LFS).
A backtest must only see what was known on the forecast date. `as_of(series, date)`
returns exactly that.

How known_from is set:
- First time a series is loaded (backfill): known_from = period end + typical
  publication lag. Values are today's vintage – SCB's API has no history of
  vintages – so revisions leak into the backfill. Flagged with source="backfill".
- Later fetches: a new period gets min(period end + lag, fetch date); a changed
  value (revision) gets known_from = fetch date. So from now on, the table
  records real vintages.

Storage: data/observations.parquet (not committed, rebuilt by `python -m kpif_nowcast.observations`).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

PATH = Path(__file__).resolve().parents[2] / "data" / "observations.parquet"
COLUMNS = ["series", "period", "value", "known_from", "source", "fetched_at"]

def lag_days(series: str) -> int:
    """Publication lag (days after period end) from the data catalog."""
    from kpif_nowcast.catalog import by_key

    return by_key()[series].lag_days


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


def load() -> pd.DataFrame:
    if not PATH.exists():
        return _empty()
    df = pd.read_parquet(PATH)
    df["known_from"] = pd.to_datetime(df["known_from"])
    return df


def save(df: pd.DataFrame) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PATH, index=False)


def default_known_from(series: str, periods: pd.PeriodIndex) -> pd.DatetimeIndex:
    lag = pd.Timedelta(days=lag_days(series))
    return (periods + 1).to_timestamp() - pd.Timedelta(days=1) + lag


def upsert(series: str, values: pd.Series, fetched_at: date | None = None) -> int:
    """Add a fetched vintage of a monthly series (index: Period[M]). Returns rows added."""
    fetched = pd.Timestamp(fetched_at or date.today())
    values = values.dropna().sort_index()
    table = load()
    existing = table[table["series"] == series]
    is_backfill = existing.empty

    latest = (
        existing.sort_values("known_from").groupby("period")["value"].last()
        if not is_backfill
        else pd.Series(dtype=float)
    )
    periods = pd.PeriodIndex(values.index, freq="M")
    default_kf = pd.Series(default_known_from(series, periods), index=values.index)

    rows = []
    for p, v in values.items():
        key = str(p)
        if key not in latest.index:
            kf = default_kf[p] if is_backfill else min(default_kf[p], fetched)
            rows.append((series, key, float(v), kf, "backfill" if is_backfill else "fetch", fetched))
        elif not np.isclose(latest[key], v, rtol=0, atol=1e-9):
            rows.append((series, key, float(v), fetched, "revision", fetched))
    if rows:
        new = pd.DataFrame(rows, columns=COLUMNS)
        table = new if table.empty else pd.concat([table, new], ignore_index=True)
        save(table)
    return len(rows)


def as_of(series: str, when: pd.Timestamp | str, table: pd.DataFrame | None = None) -> pd.Series:
    """Values of `series` as they were known on `when` (latest vintage with known_from <= when)."""
    table = load() if table is None else table
    when = pd.Timestamp(when)
    t = table[(table["series"] == series) & (table["known_from"] <= when)]
    if t.empty:
        return pd.Series(dtype=float, name=series)
    s = t.sort_values("known_from").groupby("period")["value"].last()
    s.index = pd.PeriodIndex(s.index, freq="M")
    return s.sort_index().rename(series)


# ---------------------------------------------------------------- fetching


def refresh(keys: list[str] | None = None) -> dict[str, str]:
    """Fetch every catalog series (or `keys`) into the table. One failing source doesn't stop the rest."""
    from kpif_nowcast.catalog import CATALOG

    status = {}
    for spec in CATALOG:
        if keys and spec.key not in keys:
            continue
        try:
            values = spec.fetch()
            values.index = pd.PeriodIndex(values.index, freq="M")
            n = upsert(spec.key, values)
            status[spec.key] = f"ok +{n} ({values.index.min()}..{values.index.max()})"
        except Exception as exc:  # noqa: BLE001 - report and continue
            status[spec.key] = f"FAILED: {type(exc).__name__}: {str(exc)[:120]}"
        print(f"{spec.key:24s} {status[spec.key]}")
    t = load()
    print(f"\n{len(t)} rows, {t['series'].nunique()} series; sources: {t['source'].value_counts().to_dict()}")
    return status


if __name__ == "__main__":
    import sys

    refresh(sys.argv[1:] or None)
