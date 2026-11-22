"""Electricity spot prices per Swedish bidding zone from elprisetjustnu.se.

Free API, attribution requested ("Elpriser tillhandahålls av Elpriset just nu.se").
Underlying data: ENTSO-E. History from 2021-11-01. One call per day and zone,
so responses are cached per day under data/raw/elpris/ and only missing days are fetched.
"""

from __future__ import annotations

import json
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

URL = "https://www.elprisetjustnu.se/api/v1/prices/{y}/{md}_{zone}.json"
CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "raw" / "elpris"
FIRST_DAY = date(2021, 11, 1)


def _fetch_day(day: date, zone: str, session: requests.Session) -> list[dict] | None:
    path = CACHE_DIR / zone / f"{day:%Y-%m-%d}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    resp = session.get(URL.format(y=day.year, md=f"{day:%m-%d}", zone=zone), timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(resp.text, encoding="utf-8")
    time.sleep(0.2)  # be polite to a free service
    return resp.json()


def daily_prices(zone: str, start: date = FIRST_DAY, end: date | None = None) -> pd.Series:
    """Daily mean spot price (SEK/kWh, excl. VAT) for one zone. Simple mean over hours/quarters."""
    end = end or date.today() - timedelta(days=1)
    out = {}
    with requests.Session() as session:
        day = start
        while day <= end:
            rows = _fetch_day(day, zone, session)
            if rows:
                out[pd.Timestamp(day)] = sum(r["SEK_per_kWh"] for r in rows) / len(rows)
            day += timedelta(days=1)
    return pd.Series(out, name=zone)


if __name__ == "__main__":
    import sys

    for z in sys.argv[1:] or ["SE3", "SE4"]:
        s = daily_prices(z)
        print(z, s.index.min().date(), s.index.max().date(), len(s), "days")
