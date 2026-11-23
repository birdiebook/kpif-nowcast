"""Arbetsförmedlingen (Swedish Public Employment Service): notices of redundancy and registered unemployed.

Source: Excel files under https://arbetsformedlingen.se/statistik/sok-statistik/tidigare-statistik.
The download links change every month, so the page is scraped for the current file name.
Files are cached under data/raw/j6/<name>_<fetch date>.xlsx; a file whose name (it carries the
data month) is already cached is not downloaded again.

Breaks, and how they are handled:
- Registered unemployed: the age band is 16-64 until 2022, 16-65 in 2023-2025 and 16-66 from 2026.
  No overlap is published, so the series is stored as published. The step is small (people aged
  65-66 are a few thousand of several hundred thousand); see docs/auto/j6/kvalitet.md.
- Notices: industry codes change (SNI 2002 -> 2007 -> 2025). We only use the national total,
  which does not depend on the industry classification.

Publication lag: the October 2026 files were uploaded 2026-11-10 (timestamp in the download URL),
i.e. ~10 days after the month. Rounded up to 15 days (later publication, never earlier).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd


PAGE = "https://arbetsformedlingen.se/statistik/sok-statistik/tidigare-statistik"
BASE = "https://arbetsformedlingen.se"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "j6"
HEADERS = {"User-Agent": "kpif-nowcast research script"}
PATTERNS = {
    "varsel": r'(/download/[^"\s]+/web-varsel-bransch-199201-\d{4}-\d{2}\.xlsx)',
    "sok": r'(/download/[^"\s]+/web-sok-riket-\d{4}-\d{2}\.xlsx)',
}
LAG_DAYS = 15


def _cached(name: str) -> Path | None:
    hits = sorted(RAW_DIR.glob(f"{name.removesuffix('.xlsx')}_*.xlsx"))
    return hits[-1] if hits else None


def _get(url: str, tries: int = 3):
    import time

    import requests

    for k in range(tries):
        try:
            r = requests.get(url, timeout=60, headers=HEADERS)
            r.raise_for_status()
            return r
        except Exception:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(2 ** (k + 1))


def current_file(kind: str, page_html: str | None = None) -> Path:
    """Path to the cached current file of `kind`; downloads it if this file name is not cached yet."""
    html = page_html if page_html is not None else _get(PAGE).text
    m = re.search(PATTERNS[kind], html)
    if not m:
        raise RuntimeError(f"no {kind} file link found on {PAGE}")
    link = m.group(1)
    name = link.rsplit("/", 1)[-1]
    hit = _cached(name)
    if hit is not None:
        return hit
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / f"{name.removesuffix('.xlsx')}_{date.today():%Y%m%d}.xlsx"
    out.write_bytes(_get(BASE + link).content)
    return out


def _period(label) -> pd.Period | None:
    s = str(label).strip()
    m = re.fullmatch(r"(\d{4})-?(\d{2})", s)
    return pd.Period(f"{m.group(1)}-{m.group(2)}", "M") if m else None


def parse_varsel(path: Path) -> pd.Series:
    """National total of persons affected by notices, per month.

    1992-2004 from the 'Summa' row of the industry sheet, 2005- from 'Totalsumma' of the section
    ('Avd') sheets; the two agree where both exist (checked in the quality report).
    """
    from kpif_nowcast.sources.xlsx_lite import read_sheets

    sheets = read_sheets(path)
    out = {}
    for name, rows in sheets.items():
        header = next((r for r in rows if r and str(r[0]).upper().startswith(("SNI",))), None)
        if header is None:
            continue
        label = "Totalsumma" if name.startswith("Avd") else "Summa"
        total = next((r for r in rows if r and str(r[0]).strip() == label), None)
        if total is None:
            continue
        for col, h in enumerate(header):
            p = _period(h)
            if p is None:
                continue
            v = total[col] if col < len(total) else None
            if name.startswith("Avd") or p.year < 2005:
                out[p] = 0.0 if v is None else float(v)
    return pd.Series(out, dtype=float).sort_index().rename("af_varsel")


def varsel_by_sheet(path: Path) -> dict[str, pd.Series]:
    """Totals per sheet (for the overlap check)."""
    from kpif_nowcast.sources.xlsx_lite import read_sheets

    res = {}
    for name, rows in read_sheets(path).items():
        header = next((r for r in rows if r and str(r[0]).upper().startswith("SNI")), None)
        label = "Totalsumma" if name.startswith("Avd") else "Summa"
        total = next((r for r in rows if r and str(r[0]).strip() == label), None)
        if header is None or total is None:
            continue
        res[name] = pd.Series({p: (0.0 if (c >= len(total) or total[c] is None) else float(total[c]))
                               for c, h in enumerate(header) if (p := _period(h)) is not None})
    return res


def parse_sok(path: Path) -> pd.DataFrame:
    """Monthly national counts from the 'Tabell' sheet: one column per measure."""
    from kpif_nowcast.sources.xlsx_lite import read_sheets

    rows = read_sheets(path)["Tabell"]
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "Period")
    cols = rows[hi]
    data = {}
    for r in rows[hi + 1:]:
        p = _period(r[0]) if r else None
        if p is None:
            continue
        data[p] = {c: (float(r[j]) if j < len(r) and isinstance(r[j], float) else None) for j, c in enumerate(cols) if j}
    return pd.DataFrame(data).T.sort_index()


def _varsel() -> pd.Series:
    return parse_varsel(current_file("varsel"))


def _sok(col: str):
    def f() -> pd.Series:
        return parse_sok(current_file("sok"))[col].dropna().rename(col)

    return f


def specs() -> list:
    """Catalog entries (built lazily: catalog.py imports this module, so no import of Spec at module level)."""
    from kpif_nowcast.catalog import Spec

    return [
        Spec("af_varsel", "arbetsmarknad", "Varsel om uppsägning (personer)", "antal", "M",
             "Arbetsförmedlingen, tidigare statistik (web-varsel-bransch)", _varsel, LAG_DAYS, revised=True,
             link="Ledande indikator för arbetslöshet: varsel föregår uppsägningar med 2–6 månader.",
             note="Riket totalt från 1992-01, oberoende av SNI-byten. Serien från 2019-11 uppdaterades 2025-06-30, "
                  "därför revised."),
        Spec("af_inskrivna_arbetslosa", "arbetsmarknad", "Inskrivna arbetslösa, Arbetsförmedlingen", "antal", "M",
             "Arbetsförmedlingen, tidigare statistik (web-sok-riket)", _sok("Inskrivna arbetslösa"), LAG_DAYS,
             link="Registerbaserad arbetslöshet, mindre brus än AKU. Svagare arbetsmarknad → lägre löne- och tjänsteinflation.",
             note="Från 1996-01. Åldersbrott: 16–64 år t.o.m. 2022, 16–65 år 2023–2025, 16–66 år från 2026."),
        Spec("af_oppet_arbetslosa", "arbetsmarknad", "Öppet arbetslösa, Arbetsförmedlingen", "antal", "M",
             "Arbetsförmedlingen, tidigare statistik (web-sok-riket)", _sok("Öppet arbetslösa"), LAG_DAYS,
             link="Arbetslösa utanför program; påverkas mindre av politiska programvolymer.",
             note="Från 1996-01. Samma åldersbrott som inskrivna arbetslösa."),
    ]
