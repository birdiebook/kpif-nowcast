"""Statistics Sweden (SCB) PxWebApi v2 client.

Licence: CC0. Rate limit: 30 calls per 10 s.
"""

from __future__ import annotations

import itertools
import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://statistikdatabasen.scb.se/api/v2"
RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def fetch_table(table_id: str, value_codes: dict[str, str] | None = None, lang: str = "en") -> pd.DataFrame:
    """Fetch an SCB table as a long DataFrame (one row per cell).

    `value_codes` maps dimension id -> selection, e.g. {"ContentsCode": "*", "Tid": "*"}.
    The raw json-stat2 response is saved to data/raw with today's date.
    """
    value_codes = value_codes or {"ContentsCode": "*", "Tid": "*"}
    params = {"lang": lang, "outputFormat": "json-stat2"}
    params.update({f"valueCodes[{k}]": v for k, v in value_codes.items()})

    resp = requests.get(f"{BASE_URL}/tables/{table_id}/data", params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"scb_{table_id}_{date.today():%Y%m%d}.json").write_text(json.dumps(payload), encoding="utf-8")

    return _jsonstat_to_frame(payload)


def _jsonstat_to_frame(payload: dict) -> pd.DataFrame:
    """Flatten a json-stat2 dataset. Values are stored in row-major order over `id`."""
    dim_ids = payload["id"]
    codes = []
    for dim in dim_ids:
        index = payload["dimension"][dim]["category"]["index"]
        codes.append(sorted(index, key=index.get))

    rows = list(itertools.product(*codes))
    df = pd.DataFrame(rows, columns=dim_ids)
    df["value"] = payload["value"]
    return df


def month_to_period(tid: pd.Series) -> pd.PeriodIndex:
    """'2026M10' -> Period('2026-10', 'M')."""
    return pd.PeriodIndex(tid.str.replace("M", "-"), freq="M")
