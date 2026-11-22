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

# Days after the end of the period until the figure is typically published.
# Chosen on the late side (conservative); see docs/datakallor.md.
PUBLICATION_LAG_DAYS = {
    "kpif_index": 15,  # ~12-15th of next month
    "kpif_yy": 15,
    "aku_unemp_nsa": 25,  # LFS ~20 days
    "aku_unemp_sa": 25,
    "gdp_ind_yy": 35,  # GDP indicator ~29 days
    "kix": 1,  # daily series, monthly mean
    "policy_rate": 1,
    "brent_sek": 1,
    "ki_services": 3,  # NIER survey, end of the survey month
    "ki_households_infl": 3,
}


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
    lag = pd.Timedelta(days=PUBLICATION_LAG_DAYS[series])
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


def fetch_all() -> pd.DataFrame:
    """Fetch every monthly series used by the longer-horizon models (one call per source)."""
    from kpif_nowcast.data import load_kpif
    from kpif_nowcast.features import fuel_proxy_monthly
    from kpif_nowcast.sources import konj, riksbank, scb

    out = {}
    kpif = load_kpif()
    out["kpif_index"] = kpif["index"]
    out["kpif_yy"] = kpif["yy_official"]

    aku = scb.fetch_table(
        "TAB6387",
        {"Arbetskraftstillh": "ALÖSP", "TypData": "O_DATA,SR_DATA", "Kon": "1+2", "Alder": "tot15-74",
         "ContentsCode": "*", "Tid": "*"},
    )
    for code, name in [("O_DATA", "aku_unemp_nsa"), ("SR_DATA", "aku_unemp_sa")]:
        a = aku[aku["TypData"] == code]
        out[name] = pd.Series(a["value"].to_numpy(dtype=float), index=scb.month_to_period(a["Tid"]))

    gdp = scb.fetch_table("TAB443", {"BNPMarknadspris": "BNPM", "ContentsCode": "0000027O", "Tid": "*"})
    out["gdp_ind_yy"] = pd.Series(gdp["value"].to_numpy(dtype=float), index=scb.month_to_period(gdp["Tid"]))

    for code, name in [("SEKKIX92", "kix"), ("SECBREPOEFF", "policy_rate")]:
        d = riksbank.fetch_swea(code, "2000-01-01")
        out[name] = d.groupby(d.index.to_period("M")).mean()

    out["brent_sek"] = fuel_proxy_monthly()
    # monthly means of daily series: drop the current, incomplete month
    current = pd.Period(date.today(), "M")
    for name in ["kix", "policy_rate", "brent_sek"]:
        out[name] = out[name][out[name].index < current]
    out["ki_services"] = konj.fetch_balance("Bartjam.px", "BTJA", "202")
    return pd.DataFrame(out)


def refresh() -> None:
    frame = fetch_all()
    for name in frame:
        n = upsert(name, frame[name])
        print(f"{name:20s} +{n} rows")
    t = load()
    print(f"\n{len(t)} rows, {t['series'].nunique()} series; sources: {t['source'].value_counts().to_dict()}")


if __name__ == "__main__":
    refresh()
