"""L7: SCB flash CPI ("Snabb-KPI") for KPIF and KPIF-XE, and the flash minus the final outcome.

Source: SCB PxWebApi v2 (CC0, no key).
- TAB6445 "Snabb-KPI: preliminära förändringstal för KPI, KPIF och KPIF-XE (en decimal)": the headline
  numbers as published in the flash release (one decimal). First real-time release: September 2024,
  published 2024-10-08.
- Final outcomes: TAB6590 (KPIF) and TAB6593 (KPIF-XE), official monthly and 12-month changes (one decimal).

TAB6394 (two decimals) also starts in 2024M08, a month before the first real-time release, so at least
that month was back-calculated; we use the one-decimal table, whose 26 values 2024-09..2026-10 equal the
numbers in SCB's flash news releases (checked, see docs/auto3/l7/resultat.md).

Publication lags (days after period end, rounded towards later publication):
- Flash: five working days before the ordinary KPI release, observed day 4-8 of t+1 (26 releases
  2024-10-08..2026-11-05) -> 8 days. Day 4 releases are at 08:00 on the deadline day; with 8 days the flash
  for t is never treated as known at the day-4 deadline for t, which matches the monthly routine (run before
  the flash). Not revised: the flash is replaced by the final figure, the table keeps the first release.
- Flash minus final: known when the final figure is out, observed day 11-20 of t+1 (January releases come
  latest: 2025-02-18, 2026-02-20) -> 20 days. KPIF is not revised, so revised=False.

Raw responses are cached under data/raw/l7/scb_<table>_<fetch date>.json; a file at most MAX_AGE_DAYS old is
reused instead of downloading again. In offline mode (KPIF_OFFLINE=1) the newest cached file is used.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "l7"
MAX_AGE_DAYS = 7
SCB_URL = "https://statistikdatabasen.scb.se/api/v2/tables/{table}/data"

FLASH_TABLE = "TAB6445"
FLASH_DIM = "PrelAggr"
FLASH_KPIF, FLASH_XE = "SKPI02", "SKPI03"
FLASH_MM, FLASH_YY = "000007PK", "000007PM"
FIRST_RELEASE = pd.Period("2024-09", "M")  # first real-time Snabb-KPI, published 2024-10-08

FINAL = {  # aggregate -> (table, m/m code, y/y code)
    FLASH_KPIF: ("TAB6590", "000007ZO", "000007ZM"),
    FLASH_XE: ("TAB6593", "000007ZX", "000007ZV"),
}

LAG_FLASH, LAG_ERR = 8, 20

# Evidence for the lags: release dates (08:00) from SCB's news releases "Snabb-KPI <month> <year>" and
# "Konsumentprisindex (KPI), <month> <year>", period -> (flash release, ordinary release). Locked by tests:
# every release must fall on or before period end + lag.
RELEASES = {
    "2024-09": ("2024-10-08", "2024-10-15"), "2024-10": ("2024-11-07", "2024-11-14"),
    "2024-11": ("2024-12-05", "2024-12-12"), "2024-12": ("2025-01-08", "2025-01-15"),
    "2025-01": ("2025-02-06", "2025-02-18"), "2025-02": ("2025-03-06", "2025-03-13"),
    "2025-03": ("2025-04-04", "2025-04-11"), "2025-04": ("2025-05-07", "2025-05-14"),
    "2025-05": ("2025-06-05", "2025-06-13"), "2025-06": ("2025-07-07", "2025-07-14"),
    "2025-07": ("2025-08-07", "2025-08-14"), "2025-08": ("2025-09-04", "2025-09-11"),
    "2025-09": ("2025-10-08", "2025-10-15"), "2025-10": ("2025-11-06", "2025-11-13"),
    "2025-11": ("2025-12-04", "2025-12-11"), "2025-12": ("2026-01-08", "2026-01-15"),
    "2026-01": ("2026-02-06", "2026-02-20"), "2026-02": ("2026-03-05", "2026-03-12"),
    "2026-03": ("2026-04-07", "2026-04-14"), "2026-04": ("2026-05-06", "2026-05-13"),
    "2026-05": ("2026-06-04", "2026-06-11"), "2026-06": ("2026-07-08", "2026-07-15"),
    "2026-07": ("2026-08-06", "2026-08-13"), "2026-08": ("2026-09-07", "2026-09-14"),
    "2026-09": ("2026-10-07", "2026-10-14"), "2026-10": ("2026-11-05", "2026-11-12"),
}


# ------------------------------------------------------------------ cache and HTTP


def _cached(table: str, today: date | None = None, max_age: int | None = MAX_AGE_DAYS) -> Path | None:
    """Newest data/raw/l7/scb_<table>_<YYYYMMDD>.json, at most max_age days old (None: any age)."""
    today = today or date.today()
    best = None
    for p in RAW_DIR.glob(f"scb_{table}_*.json"):
        m = re.fullmatch(rf"scb_{table}_(\d{{8}})\.json", p.name)
        if not m:
            continue
        got = datetime.strptime(m.group(1), "%Y%m%d").date()
        if (max_age is None or (today - got).days <= max_age) and (best is None or got > best[0]):
            best = (got, p)
    return best[1] if best else None


def _payload(table: str) -> dict:
    """Whole table (every code of every dimension) as json-stat2, from cache or SCB."""
    from kpif_nowcast.sources import rawcache

    if rawcache.offline():
        hit = _cached(table, max_age=None)
        if hit is None:
            raise rawcache.OfflineError(f"offline: no cached raw file for scb_{table} in {RAW_DIR}")
        return json.loads(hit.read_text(encoding="utf-8"))
    hit = _cached(table)
    if hit is not None:
        return json.loads(hit.read_text(encoding="utf-8"))
    from kpif_nowcast.catalog_prices import _request

    meta = _request("GET", SCB_URL.format(table=table).replace("/data", "/metadata"), params={"lang": "en"}).json()
    params = {"lang": "en", "outputFormat": "json-stat2", **{f"valueCodes[{d}]": "*" for d in meta["id"]}}
    r = _request("GET", SCB_URL.format(table=table), params=params, pause=0.5)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"scb_{table}_{date.today():%Y%m%d}.json").write_text(r.text, encoding="utf-8")
    return r.json()


def _series(payload: dict, **codes: str) -> pd.Series:
    """One monthly series from a json-stat2 payload, every non-time dimension fixed by `codes`."""
    from kpif_nowcast.sources.scb import _jsonstat_to_frame, to_month_period

    df = _jsonstat_to_frame(payload)
    for k, v in codes.items():
        df = df[df[k] == v]
    other = [c for c in df.columns if c not in ("Tid", "value")]
    if df.empty or len(df[other].drop_duplicates()) != 1:
        raise ValueError(f"{codes} is not exactly one series")
    s = pd.Series(pd.to_numeric(df["value"], errors="coerce").to_numpy(), index=to_month_period(df["Tid"]))
    return s.dropna().sort_index()


# ------------------------------------------------------------------ series


def flash_from(payload: dict, aggr: str, content: str) -> pd.Series:
    s = _series(payload, **{FLASH_DIM: aggr, "ContentsCode": content})
    return s[s.index >= FIRST_RELEASE]


def error_from(flash: pd.Series, final: pd.Series) -> pd.Series:
    """Flash minus final, only months with both; rounded to 1 decimal (both inputs have one)."""
    both = pd.concat([flash, final], axis=1, join="inner").dropna()
    return (both.iloc[:, 0] - both.iloc[:, 1]).round(1)


def flash(aggr: str, content: str):
    def f() -> pd.Series:
        return flash_from(_payload(FLASH_TABLE), aggr, content)

    return f


def final(aggr: str, which: str) -> pd.Series:
    table, mm, yy = FINAL[aggr]
    return _series(_payload(table), ContentsCode=mm if which == "mm" else yy)


def error(aggr: str, which: str):
    def f() -> pd.Series:
        content = FLASH_MM if which == "mm" else FLASH_YY
        return error_from(flash(aggr, content)(), final(aggr, which))

    return f


# ------------------------------------------------------------------ catalog entries

FLASH_SERIES = [  # key, aggregate, content, label
    ("kpif_flash_yy", FLASH_KPIF, FLASH_YY, "Snabb-KPI: KPIF, årstakt"),
    ("kpif_flash_mm", FLASH_KPIF, FLASH_MM, "Snabb-KPI: KPIF, månadsförändring"),
    ("kpif_xe_flash_yy", FLASH_XE, FLASH_YY, "Snabb-KPI: KPIF-XE, årstakt"),
    ("kpif_xe_flash_mm", FLASH_XE, FLASH_MM, "Snabb-KPI: KPIF-XE, månadsförändring"),
]

ERROR_SERIES = [  # key, aggregate, which, label
    ("kpif_flash_err_yy", FLASH_KPIF, "yy", "Snabb-KPI minus utfall: KPIF, årstakt"),
    ("kpif_flash_err_mm", FLASH_KPIF, "mm", "Snabb-KPI minus utfall: KPIF, månadsförändring"),
    ("kpif_xe_flash_err_yy", FLASH_XE, "yy", "Snabb-KPI minus utfall: KPIF-XE, årstakt"),
]


def specs() -> list:
    """Catalog entries (lazy import of Spec: catalog.py imports this module)."""
    from kpif_nowcast.catalog import Spec

    out = []
    for key, aggr, content, label in FLASH_SERIES:
        out.append(Spec(key, "inflation", label, "%", "M", f"SCB {FLASH_TABLE} (Snabb-KPI)",
                        flash(aggr, content), LAG_FLASH,
                        link="SCB:s snabbestimat, en vecka före utfallet: referens för nowcasten.",
                        note="Från 2024-09 (första publiceringen 2024-10-08). Publiceras dag 4–8 i t+1, "
                             "alltså efter vår deadline för t. Ersätts av utfallet, revideras inte."))
    for key, aggr, which, label in ERROR_SERIES:
        table = FINAL[aggr][0]
        out.append(Spec(key, "inflation", label, "procentenheter", "M", f"SCB {FLASH_TABLE} minus {table}",
                        error(aggr, which), LAG_ERR,
                        link="Hur mycket snabbestimatet missar det slutliga utfallet.",
                        note="Båda med en decimal, som publicerade. Känd när utfallet publiceras (dag 11–20)."))
    return out


def keys() -> list[str]:
    return [s.key for s in specs()]
