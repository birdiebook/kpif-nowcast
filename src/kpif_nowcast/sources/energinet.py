"""Historical day-ahead (Elspot) prices for SE3/SE4 from Energinet's Energi Data Service.

Used to extend the electricity history back before elprisetjustnu.se (which starts 2021-11-01).

- Dataset: Elspotprices (hourly, EUR and DKK per MWh). SE3/SE4 exist from 2011-11-01, when
  Sweden was split into four bidding zones. The dataset was discontinued after 2025-09-30
  (successor: DayAheadPrices), which does not matter for a static backfill.
- Licence: CC BY 4.0. Credit: "Source: Energinet (www.energidataservice.dk)".
- No API key. Rate limit is dataset specific and unpublished; in practice ~1 data call per
  ~5 minutes (HTTP 429 with Retry-After). So we fetch a few large chunks, cache each raw
  response under data/raw/energinet/ with the fetch date, and never refetch a cached chunk.
  The full backfill takes ~30-40 minutes: run it in the background.

Chunk boundaries are passed as-is to the API; adjacent chunks share the same convention,
so there are no gaps.

Prices are converted to SEK/kWh with the Riksbank's daily SEK/EUR fixing (SEKEURPMI),
carried forward over weekends and holidays. Days are local (Swedish = Danish) time.

Run: python -m kpif_nowcast.sources.energinet
"""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from kpif_nowcast.sources import riksbank

URL = "https://api.energidataservice.dk/dataset/Elspotprices"
CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "raw" / "energinet"
ZONES = ("SE3", "SE4")
FIRST_DAY = "2011-11-01"  # SE1-SE4 introduced
# Two-year chunks (~35k rows, ~5 MB each). The last chunks overlap elprisetjustnu.se
# (2021-11 onwards) so the splice can be checked.
CHUNKS = [
    ("2011-11-01", "2013-01-01"),
    ("2013-01-01", "2015-01-01"),
    ("2015-01-01", "2017-01-01"),
    ("2017-01-01", "2019-01-01"),
    ("2019-01-01", "2021-01-01"),
    ("2021-01-01", "2023-01-01"),
    ("2023-01-01", "2025-01-01"),
]
MAX_RETRIES = 6


def _cached(start: str, end: str) -> Path | None:
    hits = sorted(CACHE_DIR.glob(f"elspot_{'-'.join(ZONES)}_{start}_{end}_*.json"))
    return hits[-1] if hits else None


def _fetch_chunk(start: str, end: str, session: requests.Session) -> list[dict]:
    path = _cached(start, end)
    if path:
        return json.loads(path.read_text(encoding="utf-8"))["records"]
    params = {
        "start": f"{start}T00:00",
        "end": f"{end}T00:00",
        "filter": json.dumps({"PriceArea": list(ZONES)}),
        "columns": "HourUTC,HourDK,PriceArea,SpotPriceEUR,SpotPriceDKK",
        "sort": "HourUTC asc",
        "limit": 0,  # all rows
    }
    for attempt in range(MAX_RETRIES):
        resp = session.get(URL, params=params, timeout=300)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 300)) + 10
            print(f"  rate limited, waiting {wait}s (attempt {attempt + 1})", flush=True)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        payload = resp.json()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        out = CACHE_DIR / f"elspot_{'-'.join(ZONES)}_{start}_{end}_{date.today():%Y%m%d}.json"
        out.write_text(json.dumps(payload), encoding="utf-8")
        print(f"  {start}..{end}: {len(payload['records'])} rows -> {out.name}", flush=True)
        return payload["records"]
    raise RuntimeError(f"Energinet still rate limiting after {MAX_RETRIES} attempts ({start}..{end})")


def fetch_all(fetch_missing: bool = True) -> pd.DataFrame:
    """All cached (and, if allowed, missing) chunks as hourly rows: HourDK, PriceArea, SpotPriceEUR."""
    frames = []
    with requests.Session() as session:
        for start, end in CHUNKS:
            if not fetch_missing and _cached(start, end) is None:
                continue
            frames.append(pd.DataFrame(_fetch_chunk(start, end, session)))
    if not frames:
        return pd.DataFrame(columns=["HourDK", "PriceArea", "SpotPriceEUR"])
    df = pd.concat(frames, ignore_index=True).drop_duplicates(["HourUTC", "PriceArea"])
    df["HourDK"] = pd.to_datetime(df["HourDK"])
    return df


def sek_per_eur() -> pd.Series:
    """Riksbank daily SEK/EUR fixing, on a calendar-day index (forward filled)."""
    s = riksbank.fetch_swea("SEKEURPMI", start="2011-01-01")
    return s.asfreq("D").ffill()


def daily_prices(zone: str, hourly: pd.DataFrame | None = None, fx: pd.Series | None = None) -> pd.Series:
    """Daily mean spot price (SEK/kWh, excl. VAT) for one zone. Simple mean over hours.

    Uses only cached chunks unless `hourly` is given; run this module to fill the cache.
    """
    hourly = fetch_all(fetch_missing=False) if hourly is None else hourly
    h = hourly[hourly["PriceArea"] == zone].dropna(subset=["SpotPriceEUR"])
    if h.empty:
        return pd.Series(dtype=float, name=zone)
    eur_mwh = h.groupby(h["HourDK"].dt.normalize())["SpotPriceEUR"].mean()
    fx = sek_per_eur() if fx is None else fx
    sek_kwh = eur_mwh * fx.reindex(eur_mwh.index).to_numpy() / 1000
    return sek_kwh.rename(zone)


def splice_report(hourly: pd.DataFrame | None = None) -> pd.DataFrame:
    """Daily Energinet vs elprisetjustnu.se on overlapping days (SEK/kWh)."""
    from kpif_nowcast.sources import elpris

    hourly = fetch_all(fetch_missing=False) if hourly is None else hourly
    fx = sek_per_eur()
    rows = []
    for z in ZONES:
        a = daily_prices(z, hourly, fx)
        a = a[a.index >= pd.Timestamp(elpris.FIRST_DAY)]
        if a.empty:
            continue
        b = elpris.daily_prices(z, end=a.index.max().date())
        both = pd.concat([a.rename("energinet"), b.rename("elpris")], axis=1).dropna()
        both["zone"] = z
        rows.append(both)
    return pd.concat(rows)


if __name__ == "__main__":
    print(f"Fetching {len(CHUNKS)} chunks from Energi Data Service (cached chunks are skipped)", flush=True)
    hourly = fetch_all(fetch_missing=True)
    for z in ZONES:
        h = hourly[(hourly["PriceArea"] == z)].dropna(subset=["SpotPriceEUR"])
        print(f"{z}: {h['HourDK'].min()} .. {h['HourDK'].max()}, {len(h)} hours", flush=True)
    rep = splice_report(hourly)
    diff = rep["energinet"] - rep["elpris"]
    print("Splice (Energinet - elprisetjustnu, SEK/kWh, daily):")
    print(diff.groupby(rep["zone"]).describe().round(4))
