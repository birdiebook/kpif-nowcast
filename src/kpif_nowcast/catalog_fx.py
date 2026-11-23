"""L6 "the krona": EUR/SEK and USD/SEK as separate monthly series (Riksbank SWEA).

The effective krona (KIX, SEKKIX92) is already in catalog.py as `kix`; it is not duplicated here.
EUR/SEK and USD/SEK are added separately because the euro dominates Swedish imports of processed
goods (and food), while oil, gas and most commodities are priced in dollars.

Source: Riksbank SWEA, series SEKEURPMI and SEKUSDPMI (SEK per unit of foreign currency, daily
fixing). Open API, no key; without a key 5 calls/min.

Monthly value = mean of the daily fixings in the month, complete months only. "Complete" is judged
against the date the raw file was fetched, not today's date: a cached file fetched on 27 November
and reused on 2 December must not publish a November mean built on 19 of 21 fixings.

Raw responses are cached under data/raw/l6/riksbank_<series>_<fetch date>.json. A cached file at
most MAX_AGE_DAYS old is reused instead of downloading again (files in data/raw/ cached by
sources.riksbank are reused the same way).

Publication lag: SWEA group 130 ("Currencies against Swedish kronor") states "Observations are
published daily at 16.15"; the fixing for the last bank day of a month is out the same afternoon,
so the full month is known the day after the month ends -> lag_days=1 (the same as kix and the
Riksbank yields). A fixing is a one-off observation without vintages -> revised=False.
"""

from __future__ import annotations

import json
import re
import time
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "l6"
MAIN_RAW = ROOT / "data" / "raw"
MAX_AGE_DAYS = 7
HEADERS = {"User-Agent": "kpif-nowcast research script"}

SWEA_URL = "https://api.riksbank.se/swea/v1/Observations/{series}/{start}"
START = "1993-01-01"  # SEKEURPMI and SEKUSDPMI both start 1993-01-04 (SWEA /Series metadata)
LAG_FX = 1

FX = [  # key, SWEA id, label, unit, link
    ("sek_eur", "SEKEURPMI", "EUR/SEK (kronor per euro)", "SEK/EUR",
     "Euroområdet är största importkällan: svagare krona mot euron → dyrare importvaror och livsmedel."),
    ("sek_usd", "SEKUSDPMI", "USD/SEK (kronor per dollar)", "SEK/USD",
     "Olja, drivmedel och de flesta råvaror prissätts i dollar: snabbt genomslag på energi."),
]


# ------------------------------------------------------------------ cache and HTTP


def _file_date(p: Path) -> date | None:
    m = re.search(r"_(\d{8})\.json$", p.name)
    return datetime.strptime(m.group(1), "%Y%m%d").date() if m else None


def _fresh(series_id: str, today: date | None = None) -> Path | None:
    """Newest cached raw file for a series (data/raw/l6 or data/raw) no older than MAX_AGE_DAYS."""
    today = today or date.today()
    best = None
    for d in (RAW_DIR, MAIN_RAW):
        for p in d.glob(f"riksbank_{series_id}_*.json"):
            got = _file_date(p)
            if got is None or got > today:
                continue
            if (today - got).days <= MAX_AGE_DAYS and (best is None or (got, d == RAW_DIR) > best[:2]):
                best = (got, d == RAW_DIR, p)
    return best[2] if best else None


def _download(series_id: str, start: str = START, tries: int = 6) -> str:
    import requests

    url = SWEA_URL.format(series=series_id, start=start)
    for k in range(tries):
        try:
            r = requests.get(url, timeout=60, headers=HEADERS)
            if r.status_code == 429 and k < tries - 1:  # no key: 5 calls/min
                time.sleep(15 * (k + 1))
                continue
            r.raise_for_status()
            time.sleep(13.0)
            return r.text
        except Exception:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(2 ** (k + 1))
    raise RuntimeError("unreachable")


def raw_daily(series_id: str, today: date | None = None) -> tuple[pd.Series, date]:
    """Daily fixings and the date they were fetched (from the cache file name, or today)."""
    hit = _fresh(series_id, today)
    if hit is not None:
        text, fetched = hit.read_text(encoding="utf-8"), _file_date(hit)
    else:
        text, fetched = _download(series_id), date.today()
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        (RAW_DIR / f"riksbank_{series_id}_{fetched:%Y%m%d}.json").write_text(text, encoding="utf-8")
    return parse(json.loads(text)), fetched


def parse(payload: list[dict]) -> pd.Series:
    """SWEA observations [{"date": ..., "value": ...}] -> daily series; empty values dropped."""
    obs = [o for o in payload if o.get("value") not in (None, "")]
    s = pd.Series([float(o["value"]) for o in obs], index=pd.DatetimeIndex([o["date"] for o in obs]),
                  dtype=float).sort_index()
    if s.index.has_duplicates:
        raise ValueError("duplicate dates in SWEA payload")
    return s


# ------------------------------------------------------------------ monthly aggregation


def monthly_mean(daily: pd.Series, fetched: date) -> pd.Series:
    """Mean of daily fixings per calendar month, only months that had ended before `fetched`.

    The fixing for day D is published 16:15 on D, so a month is complete once the fetch date is in a
    later month. The month of the fetch date itself is always dropped, also when it is the last day.
    """
    daily = daily.dropna()
    m = daily.groupby(daily.index.to_period("M")).mean()
    m.index = pd.PeriodIndex(m.index, freq="M")
    return m[m.index < pd.Period(fetched, "M")]


def fx_monthly(series_id: str):
    def f() -> pd.Series:
        daily, fetched = raw_daily(series_id)
        return monthly_mean(daily, fetched)

    return f


# ------------------------------------------------------------------ catalog entries


def specs() -> list:
    """Catalog entries (lazy import of Spec: catalog.py imports this module)."""
    from kpif_nowcast.catalog import Spec

    return [
        Spec(key, "penningpolitik", label, unit, "M", f"Riksbanken SWEA {sid}", fx_monthly(sid), LAG_FX,
             link=link, note="Månadsmedel av dagliga fixingkurser (kl. 16.15), bara hela månader.")
        for key, sid, label, unit, link in FX
    ]


def keys() -> list[str]:
    return [s.key for s in specs()]


# ------------------------------------------------------------------ quality check


def quality(table: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per series: rows, span, holes, duplicate keys, known_from before period end + lag."""
    from kpif_nowcast import observations as obs

    table = obs.load() if table is None else table
    rows = {}
    for k in keys():
        t = table[table["series"] == k]
        if t.empty:
            rows[k] = {"rows": 0}
            continue
        per = pd.PeriodIndex(t["period"], freq="M")
        span = pd.period_range(per.min(), per.max(), freq="M")
        end = (per + 1).to_timestamp() - pd.Timedelta(days=1)
        rows[k] = {
            "rows": len(t), "from": str(per.min()), "to": str(per.max()),
            "holes": len(span) - per.nunique(),
            "dup_keys": int(t.duplicated(["series", "period", "known_from"]).sum()),
            "kf_before_end_plus_lag": int((t["known_from"].to_numpy() < (end + pd.Timedelta(days=LAG_FX)).to_numpy()).sum()),
        }
    return pd.DataFrame(rows).T


if __name__ == "__main__":
    print(quality().to_string())
