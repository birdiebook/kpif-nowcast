"""Sveriges Riksbank APIs (no key needed; free re-use).

Without a key: 5 calls/min, 1000/day.
"""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from kpif_nowcast.sources import rawcache

FORECAST_URL = "https://api.riksbank.se/monetary_policy_data/v1/forecasts"
SWEA_URL = "https://api.riksbank.se/swea/v1/Observations/{series}/{start}"


def fetch_swea(series: str = "SEKUSDPMI", start: str = "2000-01-01") -> pd.Series:
    """Daily SWEA series, e.g. SEKUSDPMI (SEK per USD), SEKEURPMI, SEKKIX92."""
    if rawcache.offline():
        payload = json.loads(rawcache.require(RAW_DIR, f"riksbank_{series}").read_text(encoding="utf-8"))
        s = pd.Series({pd.Timestamp(o["date"]): float(o["value"]) for o in payload}, name=series)
        return s.sort_index()
    for attempt in range(6):  # without a key: 5 calls/min -> back off on 429
        resp = requests.get(SWEA_URL.format(series=series, start=start), timeout=60)
        if resp.status_code != 429:
            break
        time.sleep(15 * (attempt + 1))
    resp.raise_for_status()
    payload = resp.json()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"riksbank_{series}_{date.today():%Y%m%d}.json").write_text(json.dumps(payload), encoding="utf-8")
    s = pd.Series({pd.Timestamp(o["date"]): float(o["value"]) for o in payload}, name=series)
    return s.sort_index()
RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def fetch_forecasts(series: str = "SEMCPIFNAYNA") -> pd.DataFrame:
    """All forecast vintages for one series, long format.

    Columns: policy_round, cutoff (last outcome month), published (date), month, value.
    Each vintage contains outcomes up to `cutoff` followed by the forecast path.
    """
    if rawcache.offline():
        payload = json.loads(rawcache.require(RAW_DIR, f"riksbank_{series}").read_text(encoding="utf-8"))
    else:
        resp = requests.get(FORECAST_URL, params={"series": series}, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        (RAW_DIR / f"riksbank_{series}_{date.today():%Y%m%d}.json").write_text(json.dumps(payload), encoding="utf-8")

    rows = []
    for vintage in payload["data"][0]["vintages"]:
        meta = vintage["metadata"]
        for obs in vintage["observations"]:
            rows.append(
                {
                    "policy_round": meta["policy_round"],
                    "cutoff": pd.Period(meta["forecast_cutoff_date"][:7], freq="M"),
                    "published": pd.Timestamp(meta["policy_round_end_dtm"][:10]),
                    "month": pd.Period(obs["dt"][:7], freq="M"),
                    "value": obs["value"],
                }
            )
    return pd.DataFrame(rows)
