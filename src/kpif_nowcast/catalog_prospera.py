"""L4 "Prospera": money market agents' 5-year inflation expectations (Riksbank survey run by Origo Group).

Source. The survey (Kantar Sifo Prospera until 2024, Origo Group from January 2025) is published by
Origo as one PDF per month on www.origogroup.com, which this environment cannot reach and which has no
time-series file. The Riksbank republishes the money market agents' 5-year expectations as figure data
("Spridning i 5-åriga inflationsförväntningar, penningmarknadens aktörer": mean, P25, P75 and whiskers,
monthly from 2019) in the Excel "sifferunderlag" of some monetary policy reports (June and September
2026). This module reads that figure from the newest report that has it.

Discovery (robust to the figure moving between sheets, the typo'd 'siffferunderlag' path and reports that
leave the figure out): listing page of monetary policy decisions -> each decision page, newest first ->
its sifferunderlag .xlsx -> the sheet whose heading mentions inflation expectations and whose source is
Origo/Prospera, with P25, P75 and a mean column. The first (newest) hit wins.

Cache: data/raw/l4/<file stem>_<fetch date>.xlsx (a published report file is reused whatever its age) and
data/raw/l4/prospera_source_<fetch date>.json (which file holds the figure; rediscovered after
MAX_AGE_DAYS). With KPIF_OFFLINE=1 only cached files are used.

Publication lag. Origo publishes month m in the middle of month m (eight releases 2025-12..2026-11, all on
day 10-19, see docs/publiceringskalender.md) -> 3 days after period end, the same convention as the NIER
surveys. Leakage note: the numbers are the Riksbank's own aggregation of the month-m responses, first
printed in the next report with the figure, so they are a close proxy of what was public in month m, not
the identical figure; and live updates only arrive when a report carries the figure (stale between).
Means differ by up to ~0.005 between the June and September 2026 files -> revised=True.

BLOCKED (see docs/auto3/l4/resultat.md): 1- and 2-year expectations, KPI vs KPIF split and the other
groups (labour market parties, purchasing managers) are only in Origo's PDFs on www.origogroup.com
(host not allowed in this environment, and PDF-only).
"""

from __future__ import annotations

import json
import re
import time
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "l4"
MAX_AGE_DAYS = 7
HEADERS = {"User-Agent": "kpif-nowcast research script"}

BASE = "https://www.riksbank.se"
LISTING_URL = BASE + "/sv/penningpolitik/penningpolitisk-rapport/"
MONTHS_SV = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september",
             "oktober", "november", "december"]
DECISION = re.compile(r'href="(/sv/penningpolitik/penningpolitisk-rapport/(\d{4})/penningpolitiskt-beslut-'
                      r'(' + "|".join(MONTHS_SV) + r')-(\d{4})/)"')
XLSX = re.compile(r'href="([^"]*sifferunderlag[^"]*\.xlsx)"', re.I)

LAG = 3
COLUMNS = {"mean": r"genomsnitt|medel", "p25": r"\bp\s?25\b|25:e", "p75": r"\bp\s?75\b|75:e"}
EXCEL_EPOCH = pd.Timestamp("1899-12-30")


# ------------------------------------------------------------------ parsing (no network)


def _meta(rows: list[list]) -> dict[str, str]:
    """Label -> text for the heading block ('Diagram', 'Rubrik', 'Enhet', 'Källor:', 'Anm.')."""
    out = {}
    for r in rows[:12]:
        if len(r) >= 2 and isinstance(r[0], str) and r[1] is not None:
            out[r[0].strip().rstrip(":").lower()] = str(r[1])
    return out


def _header(rows: list[list]) -> tuple[int, dict[str, int]] | None:
    for i, r in enumerate(rows[:40]):
        if r and isinstance(r[0], str) and r[0].strip():
            continue  # heading block ('Anm.' mentions mean and percentiles in one cell)
        cols = {}
        for j, c in enumerate(r):
            if isinstance(c, str):
                for name, pat in COLUMNS.items():
                    if name not in cols and j not in cols.values() and re.search(pat, c, re.I):
                        cols[name] = j
        if len(cols) == len(COLUMNS):
            return i, cols
    return None


def is_prospera_sheet(rows: list[list]) -> bool:
    m = _meta(rows)
    title, src = m.get("rubrik", ""), m.get("källor", "") + " " + m.get("källa", "")
    return (bool(re.search(r"inflationsförväntning", title, re.I)) and bool(re.search(r"5", title))
            and bool(re.search(r"penningmarknad", title, re.I)) and bool(re.search(r"origo|prospera", src, re.I))
            and _header(rows) is not None)


def _to_period(v) -> pd.Period | None:
    if isinstance(v, (int, float)) and 20000 < v < 80000:  # Excel serial date
        return (EXCEL_EPOCH + pd.Timedelta(days=float(v))).to_period("M")
    if isinstance(v, (datetime, date, pd.Timestamp)):
        return pd.Timestamp(v).to_period("M")
    if isinstance(v, str) and re.match(r"^\d{4}-\d{2}", v.strip()):
        return pd.Period(v.strip()[:7], "M")
    return None


def parse_sheet(rows: list[list]) -> pd.DataFrame:
    """Monthly frame (index Period[M]) with columns mean, p25, p75 from one figure sheet."""
    found = _header(rows)
    if found is None:
        raise ValueError("no header row with mean, P25 and P75")
    hi, cols = found
    data = {}
    for r in rows[hi + 1:]:
        if not r:
            continue
        p = _to_period(r[0])
        if p is None:
            continue
        vals = {k: (float(r[j]) if j < len(r) and isinstance(r[j], (int, float)) else None) for k, j in cols.items()}
        if any(v is not None for v in vals.values()):
            data[p] = vals
    df = pd.DataFrame.from_dict(data, orient="index", columns=list(COLUMNS)).sort_index()
    df.index = pd.PeriodIndex(df.index, freq="M")
    if df.index.has_duplicates:
        raise ValueError("duplicate months in figure sheet")
    return df


def find_in_workbook(sheets: dict[str, list[list]]) -> pd.DataFrame | None:
    for rows in sheets.values():
        if is_prospera_sheet(rows):
            return parse_sheet(rows)
    return None


def decision_pages(listing_html: str) -> list[str]:
    """Decision page paths on the listing page, newest first."""
    seen = {}
    for path, y, mon, y2 in DECISION.findall(listing_html):
        if y == y2:
            seen[path] = (int(y), MONTHS_SV.index(mon) + 1)
    return sorted(seen, key=seen.get, reverse=True)


def xlsx_links(page_html: str) -> list[str]:
    return list(dict.fromkeys(XLSX.findall(page_html)))


# ------------------------------------------------------------------ cache and HTTP


def _stamp(p: Path) -> date | None:
    m = re.search(r"_(\d{8})\.\w+$", p.name)
    return datetime.strptime(m.group(1), "%Y%m%d").date() if m else None


def _latest(pattern: str, max_age: int | None = None, today: date | None = None) -> Path | None:
    today = today or date.today()
    best = None
    for p in RAW_DIR.glob(pattern):
        got = _stamp(p)
        if got is None or (max_age is not None and (today - got).days > max_age):
            continue
        if best is None or got > best[0]:
            best = (got, p)
    return best[1] if best else None


def _get(url: str, tries: int = 3):
    import requests

    for k in range(tries):
        try:
            r = requests.get(url, timeout=60, headers=HEADERS)
            if r.status_code == 429 and k < tries - 1:
                time.sleep(20 * (k + 1))
                continue
            r.raise_for_status()
            time.sleep(1.0)
            return r
        except Exception:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(2 ** (k + 1))


def _xlsx(url: str) -> Path:
    """Cached copy of a report file (published files do not change, so any cached copy is reused)."""
    from kpif_nowcast.sources import rawcache

    stem = Path(url.split("?")[0]).stem
    hit = _latest(f"{stem}_*.xlsx")
    if hit is not None:
        return hit
    if rawcache.offline():
        raise rawcache.OfflineError(f"offline: {stem}.xlsx not cached in {RAW_DIR}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    p = RAW_DIR / f"{stem}_{date.today():%Y%m%d}.xlsx"
    p.write_bytes(_get(url).content)
    return p


def _discover(max_pages: int = 12) -> dict:
    """Walk decision pages newest first until a report file holds the figure."""
    pages = decision_pages(_get(LISTING_URL).text)[:max_pages]
    scanned = []
    for path in pages:
        for link in xlsx_links(_get(BASE + path).text):
            url = link if link.startswith("http") else BASE + link
            scanned.append(url)
            from kpif_nowcast.sources.xlsx_lite import read_sheets

            if find_in_workbook(read_sheets(_xlsx(url))) is not None:
                return {"hit": url, "page": BASE + path, "scanned": scanned}
    raise LookupError(f"no Prospera figure in the sifferunderlag of {len(pages)} decision pages")


def source_file() -> Path:
    from kpif_nowcast.sources import rawcache

    hit = _latest("prospera_source_*.json", None if rawcache.offline() else MAX_AGE_DAYS)
    if hit is None:
        if rawcache.offline():
            raise rawcache.OfflineError(f"offline: no prospera_source_*.json in {RAW_DIR}")
        info = _discover()
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        hit = RAW_DIR / f"prospera_source_{date.today():%Y%m%d}.json"
        hit.write_text(json.dumps(info, indent=1), encoding="utf-8")
    return _xlsx(json.loads(hit.read_text(encoding="utf-8"))["hit"])


def frame() -> pd.DataFrame:
    from kpif_nowcast.sources.xlsx_lite import read_sheets

    df = find_in_workbook(read_sheets(source_file()))
    if df is None:
        raise LookupError("cached Prospera file no longer holds the figure")
    return df[df.index < pd.Period(date.today(), "M")]


def column(name: str):
    def f() -> pd.Series:
        return frame()[name].dropna()

    return f


# ------------------------------------------------------------------ catalog entries

SERIES = [  # key, column, label
    ("prospera_mm_5y_mean", "mean", "Penningmarknadens inflationsförväntningar 5 år, medel (Prospera/Origo)"),
    ("prospera_mm_5y_p25", "p25", "Penningmarknadens inflationsförväntningar 5 år, 25:e percentil"),
    ("prospera_mm_5y_p75", "p75", "Penningmarknadens inflationsförväntningar 5 år, 75:e percentil"),
]


def specs() -> list:
    """Catalog entries (lazy import of Spec: catalog.py imports this module)."""
    from kpif_nowcast.catalog import Spec

    note = ("Riksbankens sifferunderlag till penningpolitiska rapporter (Origo Group och Riksbanken), från 2019. "
            "Uppdateras bara när en rapport har diagrammet. Mått (KPI/KPIF) anges inte i filen.")
    return [Spec(key, "penningpolitik", label, "%", "M", "Riksbanken sifferunderlag PPR (Origo/Prospera)",
                 column(col), LAG, revised=True,
                 link="Förankring av inflationsförväntningarna på lång sikt; spridningen visar hur fast ankaret sitter.",
                 note=note)
            for key, col, label in SERIES]


def keys() -> list[str]:
    return [k for k, _, _ in SERIES]


# ------------------------------------------------------------------ quality check


def quality(table: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per series: rows, span, missing months inside the span, duplicate keys, known_from before period end."""
    from kpif_nowcast import observations as obs

    table = obs.load() if table is None else table
    rows = {}
    for k in keys():
        t = table[table["series"] == k]
        if t.empty:
            rows[k] = {"rows": 0}
            continue
        per = pd.PeriodIndex(t["period"], freq="M")
        latest = t.sort_values("known_from").drop_duplicates("period", keep="last")
        span = pd.period_range(per.min(), per.max(), freq="M")
        ends = per.to_timestamp(how="end").normalize()
        rows[k] = {"rows": len(t), "first": str(per.min()), "last": str(per.max()),
                   "holes": len(span) - latest["period"].nunique(),
                   "dup_keys": int(t.duplicated(["series", "period", "known_from"]).sum()),
                   "kf_before_end": int((pd.to_datetime(t["known_from"]).to_numpy() < ends.to_numpy()).sum())}
    return pd.DataFrame(rows).T


if __name__ == "__main__":
    df = frame()
    print(df.tail(12).round(3).to_string())
    print(quality().to_string())
