"""Statistics Sweden (SCB) PxWebApi v2 client.

Licence: CC0. Rate limit: 30 calls per 10 s.
"""

from __future__ import annotations

import itertools
import json
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://statistikdatabasen.scb.se/api/v2"
RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def fetch_table(
    table_id: str, value_codes: dict[str, str] | None = None, lang: str = "en", raw_suffix: str = ""
) -> pd.DataFrame:
    """Fetch an SCB table as a long DataFrame (one row per cell).

    `value_codes` maps dimension id -> selection, e.g. {"ContentsCode": "*", "Tid": "*"}.
    The raw json-stat2 response is saved to data/raw with today's date (plus `raw_suffix`,
    so chunks of the same table don't overwrite each other).
    """
    value_codes = value_codes or {"ContentsCode": "*", "Tid": "*"}
    params = {"lang": lang, "outputFormat": "json-stat2"}
    params.update({f"valueCodes[{k}]": v for k, v in value_codes.items()})

    resp = requests.get(f"{BASE_URL}/tables/{table_id}/data", params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"scb_{table_id}{raw_suffix}_{date.today():%Y%m%d}.json").write_text(json.dumps(payload), encoding="utf-8")

    return _jsonstat_to_frame(payload)


def fetch_metadata(table_id: str, lang: str = "en") -> dict:
    resp = requests.get(f"{BASE_URL}/tables/{table_id}/metadata", params={"lang": lang}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def dimension_codes(table_id: str, dim: str, lang: str = "en") -> list[str]:
    """All value codes of one dimension, in SCB's order."""
    index = fetch_metadata(table_id, lang)["dimension"][dim]["category"]["index"]
    return sorted(index, key=index.get)


def fetch_table_chunked(
    table_id: str, chunk_dim: str, value_codes: dict[str, str], chunk_size: int = 15, lang: str = "en"
) -> pd.DataFrame:
    """Fetch a large table in chunks over one dimension (to stay under 150 000 cells per call).

    `value_codes` holds the selection for all other dimensions. Each chunk's raw response is
    saved separately (suffix _c00, _c01, ...).
    """
    codes = dimension_codes(table_id, chunk_dim, lang)
    frames = []
    for i in range(0, len(codes), chunk_size):
        chunk = codes[i : i + chunk_size]
        sel = {chunk_dim: ",".join(chunk), **value_codes}
        frames.append(fetch_table(table_id, sel, lang, raw_suffix=f"_c{i // chunk_size:02d}"))
        time.sleep(0.5)  # well under 30 calls per 10 s
    return pd.concat(frames, ignore_index=True)


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
