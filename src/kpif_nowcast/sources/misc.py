"""Smaller sources: FAO Food Price Index, NY Fed GSCPI, JobTech historical job ads."""

from __future__ import annotations

import io
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"

FAO_URL = ("https://www.fao.org/media/docs/worldfoodsituationlibraries/wfs-library/"
           "food_price_indices_data.csv?download=true")
GSCPI_URL = "https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.xlsx"
JOBTECH_URL = "https://historical.api.jobtechdev.se/search"


def _save(name: str, content: bytes) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"{name}_{date.today():%Y%m%d}").write_bytes(content)


def fao_food_price_index() -> pd.DataFrame:
    """FAO Food Price Index and sub-indices (2014-16 = 100), monthly. Columns lower-cased."""
    resp = requests.get(FAO_URL, timeout=60)
    resp.raise_for_status()
    _save("fao_ffpi.csv", resp.content)
    text = resp.content.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    header = next(i for i, line in enumerate(lines) if line.lower().startswith("date"))
    df = pd.read_csv(io.StringIO("\n".join(lines[header:])))
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.dropna(subset=["date"])
    df["period"] = pd.PeriodIndex(pd.to_datetime(df["date"], errors="coerce"), freq="M")
    df = df.dropna(subset=["period"]).set_index("period").drop(columns="date")
    return df.apply(pd.to_numeric, errors="coerce")


def gscpi() -> pd.Series:
    """NY Fed Global Supply Chain Pressure Index (std. deviations from average)."""
    resp = requests.get(GSCPI_URL, timeout=60)
    resp.raise_for_status()
    _save("gscpi.xls", resp.content)
    xl = pd.read_excel(io.BytesIO(resp.content), sheet_name=None, header=None)
    for sheet in xl.values():
        df = sheet.dropna(how="all")
        dates = pd.to_datetime(df.iloc[:, 0], errors="coerce")
        vals = pd.to_numeric(df.iloc[:, 1], errors="coerce")
        ok = dates.notna() & vals.notna()
        if ok.sum() > 100:
            s = pd.Series(vals[ok].to_numpy(), index=pd.PeriodIndex(dates[ok], freq="M"))
            return s[~s.index.duplicated(keep="last")].sort_index()
    raise ValueError("GSCPI: no date/value sheet found")


def jobtech_monthly_count(query: str | None, start: str = "2016-01", end: str | None = None) -> pd.Series:
    """Number of job ads published per month in Platsbanken (JobTech historical ads, CC0).

    query=None counts all ads (the denominator). Free-text search, so terms are noisy.
    Assumes the historical-from/to window filters on publication date (UNVERIFIED by JobTech docs).
    """
    end_p = pd.Period(end, "M") if end else pd.Period(date.today(), "M") - 1
    out = {}
    with requests.Session() as s:
        for p in pd.period_range(start, end_p, freq="M"):
            params = {
                "limit": 0,
                "historical-from": f"{p.start_time:%Y-%m-%d}T00:00:00",
                "historical-to": f"{p.end_time:%Y-%m-%d}T23:59:59",
            }
            if query:
                params["q"] = query
            for attempt in range(4):
                r = s.get(JOBTECH_URL, params=params, timeout=60)
                if r.status_code < 500 and r.status_code != 429:
                    break
                time.sleep(5 * (attempt + 1))
            r.raise_for_status()
            out[p] = float(r.json()["total"]["value"])
            time.sleep(0.15)
    return pd.Series(out).sort_index()
