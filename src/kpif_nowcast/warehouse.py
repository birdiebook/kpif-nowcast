"""DuckDB views over data/observations.parquet, and the data-quality checks run by the weekly job.

Views:
- observations : the versioned table as stored (series, period, value, known_from, source, fetched_at)
- obs_latest   : latest vintage per (series, period), with a month number for gap checks
- catalog      : key, freq, lag_days, revised for every catalog series

Each check in CHECKS is a query that returns the violating rows; an empty result = pass.
tests/test_data_quality.py runs them. `python -m kpif_nowcast.warehouse` prints a summary.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from kpif_nowcast.observations import PATH as OBS_PATH

STEP = {"M": 1, "Q": 3, "A": 12}

# Series with a gap in an otherwise complete history, and why it is accepted. Keep this short.
KNOWN_GAPS: dict[str, str] = {
    "rent_change": "SCB TAB6051 has no value for 1981 (missing in the source, checked in the raw response)",
    "ai_use_firms_se": "Eurostat ICT survey did not ask about AI in 2022 (2021, 2023-2025 only)",
    "ai_use_firms_eu": "Eurostat ICT survey did not ask about AI in 2022 (2021, 2023-2025 only)",
}

CHECKS = {
    # one value per vintage: (series, period, known_from) is the key of the versioned table
    "unique_key": """
        select series, period, known_from, count(*) as n
        from observations group by all having count(*) > 1""",
    "no_nulls": """
        select * from observations
        where series is null or period is null or known_from is null or value is null or isnan(value)""",
    "period_format": """
        select distinct series, period from observations where not regexp_full_match(period, '\\d{4}-\\d{2}')""",
    # a value cannot be known before its period has ended, unless the catalog says so with a
    # negative publication lag (e.g. rents, negotiated and published before the year ends)
    "known_from_after_period_end": """
        select o.series, o.period, o.known_from, o.source, c.lag_days from observations o
        join catalog c on c.key = o.series
        where o.known_from < last_day(strptime(o.period || '-01', '%Y-%m-%d'))
                             + to_days(least(c.lag_days, 0))""",
    # a fetched (non-backfill) value can't be dated after the fetch that saw it
    "fetched_known_from_not_after_fetch": """
        select series, period, known_from, fetched_at, source from observations
        where source <> 'backfill' and known_from > fetched_at""",
    # no holes between a series' first and last period, at its catalog frequency
    "no_gaps": """
        with s as (
            select l.series, c.freq, min(m) as first_m, max(m) as last_m, count(*) as n
            from obs_latest l join catalog c on c.key = l.series
            group by all)
        select series, freq, first_m, last_m, n,
               (last_m - first_m) // case freq when 'M' then 1 when 'Q' then 3 else 12 end + 1 as expected
        from s
        where n <> (last_m - first_m) // case freq when 'M' then 1 when 'Q' then 3 else 12 end + 1""",
    # every period sits on the frequency's grid (quarters on Mar/Jun/Sep/Dec, years on Dec)
    "on_frequency_grid": """
        select l.series, c.freq, l.period from obs_latest l join catalog c on c.key = l.series
        where (c.freq = 'Q' and month_no % 3 <> 0) or (c.freq = 'A' and month_no <> 12)""",
    "series_in_catalog": """
        select distinct series from observations where series not in (select key from catalog)""",
}


def catalog_frame() -> pd.DataFrame:
    from kpif_nowcast.catalog import CATALOG

    return pd.DataFrame(
        [{"key": s.key, "freq": s.freq, "lag_days": s.lag_days, "revised": s.revised} for s in CATALOG]
    )


def connect(path: Path | None = None) -> duckdb.DuckDBPyConnection:
    path = Path(path or OBS_PATH)
    con = duckdb.connect()
    con.execute(f"create view observations as select * from read_parquet('{path.as_posix()}')")
    con.execute("""
        create view obs_latest as
        select series, period, value, known_from, source,
               cast(substr(period, 1, 4) as integer) * 12 + cast(substr(period, 6, 2) as integer) as m,
               cast(substr(period, 6, 2) as integer) as month_no
        from observations
        qualify row_number() over (partition by series, period order by known_from desc) = 1""")
    cat = catalog_frame()  # noqa: F841 - referenced by name in the SQL below
    con.execute("create table catalog as select * from cat")
    return con


def run_checks(con: duckdb.DuckDBPyConnection | None = None) -> dict[str, pd.DataFrame]:
    con = con or connect()
    out = {}
    for name, sql in CHECKS.items():
        df = con.execute(sql).df()
        if name == "no_gaps" and len(df):
            df = df[~df["series"].isin(KNOWN_GAPS)]
        out[name] = df
    return out


if __name__ == "__main__":
    for name, df in run_checks().items():
        print(f"{name:40s} {'ok' if df.empty else f'{len(df)} violations'}")
        if len(df):
            print(df.head(10).to_string())
