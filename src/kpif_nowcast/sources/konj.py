"""Konjunkturinstitutet (NIER) Business Tendency Survey via PxWeb v1 (no key)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://statistik.konj.se/PxWeb/api/v1/sv/KonjBar/ftgmanad"
RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def fetch_balance(table: str, branch: str, question: str, series: str = "O") -> pd.Series:
    """Monthly net balance for one branch and question.

    series "O" = not seasonally adjusted. We avoid "S"/"T" because seasonal adjustment
    is re-estimated on the full sample, so historical values change afterwards (look-ahead).
    """
    query = {
        "query": [
            {"code": "Bransch (SNI 2007)", "selection": {"filter": "item", "values": [branch]}},
            {"code": "Fråga", "selection": {"filter": "item", "values": [question]}},
            {"code": "Serie", "selection": {"filter": "item", "values": [series]}},
        ],
        "response": {"format": "json"},
    }
    resp = requests.post(f"{BASE_URL}/{table}", json=query, timeout=60)
    resp.raise_for_status()
    payload = resp.json()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"konj_{table}_{branch}_{question}_{series}_{date.today():%Y%m%d}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    out = {}
    for row in payload["data"]:
        period = row["key"][-1]
        value = row["values"][0]
        if value not in ("..", ".", ""):
            out[pd.Period(period.replace("M", "-"), freq="M")] = float(value)
    return pd.Series(out).sort_index()
