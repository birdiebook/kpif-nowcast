"""Konjunkturinstitutet (NIER) statistical database via PxWeb v1 (no key)."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

ROOT = "https://statistik.konj.se/PxWeb/api/v1/sv"
BASE_URL = f"{ROOT}/KonjBar/ftgmanad"
RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def fetch_px(url: str, selection: dict[str, str | list[str]], prefix: str = "px") -> pd.DataFrame:
    """Generic PxWeb v1 POST. Returns long rows: one column per key + 'value'.

    Works for any PxWeb v1 database (NIER, Tillväxtanalys, ...). Time is the last key.
    """
    query = {
        "query": [
            {"code": k, "selection": {"filter": "item", "values": v if isinstance(v, list) else [v]}}
            for k, v in selection.items()
        ],
        "response": {"format": "json"},
    }
    resp = requests.post(url, json=query, timeout=60)
    resp.raise_for_status()
    payload = resp.json()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    tag = hashlib.md5(json.dumps([url, selection], sort_keys=True).encode()).hexdigest()[:8]
    (RAW_DIR / f"{prefix}_{tag}_{date.today():%Y%m%d}.json").write_text(json.dumps(payload), encoding="utf-8")

    cols = [c["code"] for c in payload["columns"] if c.get("type") != "c"]
    rows = []
    for row in payload["data"]:
        value = row["values"][0]
        rows.append([*row["key"], None if value in ("..", ".", "", "-") else float(value)])
    df = pd.DataFrame(rows, columns=[*cols, "value"])
    from kpif_nowcast.sources.scb import to_month_period

    time_cols = [c["code"] for c in payload["columns"] if c.get("type") == "t"]
    df["period"] = to_month_period(df[time_cols[0] if time_cols else cols[-1]])
    return df


def fetch_series(path: str, selection: dict[str, str]) -> pd.Series:
    """One series from an NIER table (monthly or quarterly; quarter -> last month).

    path: table path below .../api/v1/sv/, e.g. "KonjBar/ftgmanad/Bartjam.px".
    selection: {variable code: single value code}; the time variable is left open.
    """
    df = fetch_px(f"{ROOT}/{path}", selection, prefix="konj_" + path.replace("/", "_").replace(".px", ""))
    return df.set_index("period")["value"].dropna().sort_index()


def fetch_balance(table: str, branch: str, question: str, series: str = "O") -> pd.Series:
    """Firm survey net balance for one branch and question.

    series "O" = not seasonally adjusted. We avoid "S"/"T" because seasonal adjustment
    is re-estimated on the full sample, so historical values change afterwards (look-ahead).
    """
    return fetch_series(
        f"KonjBar/ftgmanad/{table}",
        {"Bransch (SNI 2007)": branch, "Fråga": question, "Serie": series},
    )
