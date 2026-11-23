"""FRED (St. Louis Fed) daily series as CSV, no key needed. US public data."""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from kpif_nowcast.sources import rawcache

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def fetch_series(series: str = "DCOILBRENTEU") -> pd.Series:
    if rawcache.offline():
        text = rawcache.require(RAW_DIR, f"fred_{series}", ext=".csv").read_text(encoding="utf-8")
    else:
        resp = requests.get(URL.format(series=series), timeout=60)
        resp.raise_for_status()
        text = resp.text
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        (RAW_DIR / f"fred_{series}_{date.today():%Y%m%d}.csv").write_text(text, encoding="utf-8")
    df = pd.read_csv(io.StringIO(text), na_values=".")
    df.columns = ["date", series]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")[series].dropna()
