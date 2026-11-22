"""Statistics Sweden (SCB) PxWebApi v2 client.

Licence: CC0. Rate limit: 30 calls per 10 s.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import time
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
    tag = hashlib.md5(json.dumps(value_codes, sort_keys=True).encode()).hexdigest()[:6]
    (RAW_DIR / f"scb_{table_id}_{tag}_{date.today():%Y%m%d}.json").write_text(json.dumps(payload), encoding="utf-8")
    time.sleep(0.4)  # stay well under 30 calls / 10 s

    return _jsonstat_to_frame(payload)


def series(table_id: str, value_codes: dict[str, str], time_dim: str = "Tid") -> pd.Series:
    """Fetch exactly one time series (all non-time dimensions fixed to one code each).

    Monthly, quarterly and annual periods are all mapped to a monthly Period: a quarter to
    its last month, a year to December, so that known_from = period end + lag works uniformly.
    """
    codes = {k: v for k, v in value_codes.items()}
    codes.setdefault(time_dim, "*")
    df = fetch_table(table_id, codes)
    other = [c for c in df.columns if c not in (time_dim, "value")]
    if len(df[other].drop_duplicates()) != 1:
        raise ValueError(f"{table_id}: selection {value_codes} returns more than one series")
    s = pd.Series(pd.to_numeric(df["value"], errors="coerce").to_numpy(), index=to_month_period(df[time_dim]))
    return s.dropna().sort_index()


def to_month_period(tid: pd.Series) -> pd.PeriodIndex:
    """'2026M10' -> 2026-10, '2026K3' -> 2026-09, '2026' -> 2026-12."""
    out = []
    for t in tid.astype(str):
        if "M" in t:
            out.append(pd.Period(t.replace("M", "-"), "M"))
        elif "K" in t or "Q" in t:
            y, q = t.replace("Q", "K").split("K")
            out.append(pd.Period(f"{y}-{int(q) * 3:02d}", "M"))
        else:
            out.append(pd.Period(f"{t[:4]}-12", "M"))
    return pd.PeriodIndex(out, freq="M")


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
