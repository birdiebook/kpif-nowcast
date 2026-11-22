"""Eurostat dissemination API (JSON-stat 2.0), no key. Licence CC BY 4.0 (attribution)."""

from __future__ import annotations

import hashlib
import itertools
import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def fetch(dataset: str, **filters: str) -> pd.DataFrame:
    """Long DataFrame (one column per dimension + 'value') for a filtered dataset."""
    resp = requests.get(f"{BASE_URL}/{dataset}", params={"format": "JSON", "lang": "EN", **filters}, timeout=90)
    resp.raise_for_status()
    payload = resp.json()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    tag = hashlib.md5(json.dumps([dataset, filters], sort_keys=True).encode()).hexdigest()[:6]
    (RAW_DIR / f"eurostat_{dataset}_{tag}_{date.today():%Y%m%d}.json").write_text(json.dumps(payload), encoding="utf-8")

    dims = payload["id"]
    codes = []
    for d in dims:
        idx = payload["dimension"][d]["category"]["index"]
        codes.append(sorted(idx, key=idx.get))
    values = payload["value"]  # dict: flat index (str) -> value; missing cells are absent
    rows = []
    for flat, combo in enumerate(itertools.product(*codes)):
        v = values.get(str(flat)) if isinstance(values, dict) else values[flat]
        if v is not None:
            rows.append([*combo, float(v)])
    return pd.DataFrame(rows, columns=[*dims, "value"])


def to_month_period(time: pd.Series) -> pd.PeriodIndex:
    """'2026-10' -> 2026-10, '2026-Q2' -> 2026-06, '2025' -> 2025-12."""
    out = []
    for t in time.astype(str):
        if "-Q" in t:
            y, q = t.split("-Q")
            out.append(pd.Period(f"{y}-{int(q) * 3:02d}", "M"))
        elif len(t) == 4:
            out.append(pd.Period(f"{t}-12", "M"))
        else:
            out.append(pd.Period(t[:7], "M"))
    return pd.PeriodIndex(out, freq="M")


def series(dataset: str, **filters: str) -> pd.Series:
    df = fetch(dataset, **filters)
    other = [c for c in df.columns if c not in ("time", "value")]
    if len(df[other].drop_duplicates()) != 1:
        raise ValueError(f"{dataset} {filters}: more than one series")
    return pd.Series(df["value"].to_numpy(), index=to_month_period(df["time"])).sort_index()
