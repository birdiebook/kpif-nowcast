"""L3 rents: outcomes of the annual rent negotiations, and the CPI rent index they feed into.

Two series:
- rent_negotiated: weighted national average rent increase agreed in the annual negotiations for
  rental flats (public housing + private landlords), as reported by Hyresgaestfoereningen (the tenants'
  union, party to ~90 % of all rental flats). A small hand-curated table in this module (NEGOTIATIONS),
  one row per year with its source link. Annual, stored on December of the rent year (catalog convention).
- kpi_rent_index: CPI/CPIF COICOP 04.1.1 "actual rentals paid by tenants for main residence",
  SCB TAB6598, monthly index 2020=100. CPI and CPIF are identical here (CPIF only differs in interest).

The table is read from this module, not from the web: the national figures sit in Hyresgaestfoereningen's
annual reports (PDF, one sentence per year) and on its negotiation page, so a scraper would be fragile
for 11 numbers. `fetch` writes a dated copy of the table to data/raw/l3/ so the raw-data convention holds.

Publication lag (docs/publiceringskalender.md, section "Koerning 3: L3 Hyror"):
- rent_negotiated: -184 days -> known_from = 30 June of the rent year. Negotiations start in the autumn
  and finish in the spring; the preliminary national average is public by March-April (documented for
  2020, 2022, 2025, 2026). 30 June leaves at least two months of margin. The stored value is the final
  weighted average from the annual report (published the year after), which differs slightly from the
  spring figure (2020: 1.93 in March vs 1.92 final) -> revised=True.
- kpi_rent_index: 15 days (same as kpif_index). Values before 2026 are SCB's back-calculation to
  COICOP 2018 ("to some extent model estimated") -> revised=True.

Missing years: 2010-2015 (no national figure on the reachable sources) and 2027 (negotiations under way,
only local outcomes; see NEGOTIATIONS_2027_PARTIAL).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "l3"
MAX_AGE_DAYS = 7
HEADERS = {"User-Agent": "kpif-nowcast research script"}
SCB_URL = "https://statistikdatabasen.scb.se/api/v2/tables/{table}/data"

LAG_NEGOTIATED = -184  # 30 June of the rent year
LAG_KPI = 15

HGF = "https://www.hyresgastforeningen.se/globalassets"


@dataclass(frozen=True)
class Outcome:
    year: int
    pct: float  # weighted average rent increase, %
    scope: str  # which parties / coverage
    public_by: str  # earliest documented date the national figure was public ("" = only the annual report)
    source: str  # link
    note: str = ""


NEGOTIATIONS: list[Outcome] = [
    Outcome(2016, 0.64, "Alla förhandlade hyresrätter (allmännyttan + privata), vägt", "",
            f"{HGF}/dokument/verksamhetsberattelser/verksamhetsberattelse-2017-med-arsredovisning.pdf",
            "Anges som jämförelse i verksamhetsberättelsen 2017."),
    Outcome(2017, 0.71, "Alla förhandlade hyresrätter (allmännyttan + privata), vägt", "",
            f"{HGF}/dokument/verksamhetsberattelser/verksamhetsberattelse-2017-med-arsredovisning.pdf",
            "7,04 kr/kvm."),
    Outcome(2018, 0.98, "Alla förhandlade hyresrätter (allmännyttan + privata), vägt", "",
            f"{HGF}/bostadsfakta/rapporter/2019/verksamhetsberattelse_2018_2019-_16_dec_2020.pdf"),
    Outcome(2019, 1.91, "Alla förhandlade hyresrätter (allmännyttan + privata), vägt", "",
            f"{HGF}/bostadsfakta/rapporter/2019/verksamhetsberattelse_2018_2019-_16_dec_2020.pdf"),
    Outcome(2020, 1.92, "Alla förhandlade hyresrätter (allmännyttan + privata), vägt", "2020-03-15",
            f"{HGF}/bostadsfakta/rapporter/2021/verksamhetsberattelse-med-arsredovisning-2020.pdf",
            "Preliminärt 1,93 % i mitten av mars 2020 när 60 % av förhandlingarna var klara "
            "(verksamhetsberättelse 2018–2019)."),
    Outcome(2021, 1.32, "Alla förhandlade hyresrätter (allmännyttan + privata), vägt", "",
            f"{HGF}/om-oss/var-organisation/verksamhetsberattelse-2021.pdf"),
    Outcome(2022, 1.71, "Alla förhandlade hyresrätter; privata fick samma höjning som allmännyttan", "2022-04-20",
            f"{HGF}/policy-och-styrdokument/verksamhetsberattelse-2022.pdf",
            "Läge per 2022-04-20 när 83 % av förhandlingarna var klara; slutligt värde inte angivet."),
    Outcome(2023, 4.0, "Alla förhandlade hyresrätter (allmännyttan + privata)", "",
            f"{HGF}/dokument/verksamhetsberattelser/verksamhetsberattelse_2023.pdf",
            "Avrundat: \"landade hyreshöjningarna i genomsnitt på fyra procent\"."),
    Outcome(2024, 5.15, "Alla förhandlade; allmännyttan 5,16 %, privata 5,13 %", "",
            f"{HGF}/policy-och-styrdokument/verksamhetsberattelse-hyresgastforeningen-2024.pdf",
            "Webbsidan säger \"cirka 5 procent\"; yrkande 9,59 %."),
    Outcome(2025, 4.8, "Alla förhandlade hyresrätter (allmännyttan + privata)", "2025-03-21",
            f"{HGF}/om-oss/var-organisation/verksamhetsberattelse-hyresgastforeningen-2025-.pdf",
            "Yrkanden: privata 11,2 %, allmännyttan 7,7 %. Tidig siffra: TT 2025-03-21 (ej nåbar härifrån)."),
    Outcome(2026, 3.4, "Allmännyttan och privata hyresvärdar", "2026-03-02",
            "https://www.hyresgastforeningen.se/om-oss/vad-vi-gor/hyresforhandling/hyresforhandling_2027/",
            "213 ärenden avgjordes av skiljeman. Tidig siffra: TT 2026-03-02 (ej nåbar härifrån)."),
]

MISSING_YEARS = list(range(2010, 2016)) + [2027]

# 2027: no national average yet (2026-11-23). Local outcomes for 1 January 2027 known so far.
NEGOTIATIONS_2027_PARTIAL = [
    ("Stockholms stad, privata (skiljeman)", 2.85, "2026-10-21",
     "https://www.fastighetsagarna.se/aktuellt/nyheter/2026/stockholm/"
     "hyreshojning-pa-285-procent-i-stockholms-stad--fastighetsagarna-kraver-skarpt-lagstiftning/"),
    ("Stockholmsregionen, privata (skiljeman, 2,7–3,2 % per kommun)", 3.0, "2026-10-02",
     "https://www.hyresgastforeningen.se/regioner/stockholm/hyresforhandlingar/forhandlingslaget-i-stockholm/"),
]


# ------------------------------------------------------------------ cache and HTTP


def _fresh(pattern: str, today: date | None = None) -> Path | None:
    """Newest file in data/raw/l3 matching the glob, at most MAX_AGE_DAYS old."""
    today = today or date.today()
    best = None
    for p in RAW_DIR.glob(pattern):
        m = re.search(r"_(\d{8})\.\w+$", p.name)
        if not m:
            continue
        got = datetime.strptime(m.group(1), "%Y%m%d").date()
        if (today - got).days <= MAX_AGE_DAYS and (best is None or got > best[0]):
            best = (got, p)
    return best[1] if best else None


def _save(name: str, text: str, ext: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    p = RAW_DIR / f"{name}_{date.today():%Y%m%d}.{ext}"
    p.write_text(text, encoding="utf-8")
    return p


def _get(url: str, params: dict, tries: int = 3):
    import requests

    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=60, headers=HEADERS)
            if r.status_code == 429 and k < tries - 1:
                time.sleep(20 * (k + 1))
                continue
            r.raise_for_status()
            return r
        except Exception:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(2 ** (k + 1))


# ------------------------------------------------------------------ series


def negotiations_frame() -> pd.DataFrame:
    return pd.DataFrame([o.__dict__ for o in NEGOTIATIONS])


def negotiated() -> pd.Series:
    """National negotiated rent increase per year, on December of the rent year."""
    df = negotiations_frame()
    if _fresh("rent_negotiations_*.csv") is None:
        _save("rent_negotiations", df.to_csv(index=False), "csv")
    s = pd.Series(df["pct"].to_numpy(dtype=float),
                  index=pd.PeriodIndex([f"{y}-12" for y in df["year"]], freq="M"))
    return s.sort_index()


def _scb_series(table: str, codes: dict[str, str]) -> pd.Series:
    from kpif_nowcast.sources.scb import _jsonstat_to_frame, to_month_period

    req = {**codes, "Tid": "*"}
    tag = hashlib.md5(json.dumps(req, sort_keys=True).encode()).hexdigest()[:6]
    name = f"scb_{table}_{tag}"
    hit = _fresh(f"{name}_*.json")
    if hit is not None:
        payload = json.loads(hit.read_text(encoding="utf-8"))
    else:
        params = {"lang": "en", "outputFormat": "json-stat2", **{f"valueCodes[{k}]": v for k, v in req.items()}}
        r = _get(SCB_URL.format(table=table), params)
        _save(name, r.text, "json")
        payload = r.json()
    df = _jsonstat_to_frame(payload)
    for k, v in codes.items():
        df = df[df[k] == v]
    s = pd.Series(pd.to_numeric(df["value"], errors="coerce").to_numpy(), index=to_month_period(df["Tid"]))
    return s.dropna().sort_index()


def kpi_rent_index() -> pd.Series:
    return _scb_series("TAB6598", {"VaruTjanstegrupp": "04.1.1", "ContentsCode": "0000080H"})


def specs() -> list:
    """Catalog entries (lazy import of Spec: catalog.py imports this module)."""
    from kpif_nowcast.catalog import Spec

    return [
        Spec("rent_negotiated", "bostad_kredit", "Hyresförhandlingarnas utfall, vägt riksgenomsnitt", "% per år", "A",
             "Hyresgästföreningen (handkurerad tabell)", negotiated, LAG_NEGOTIATED, revised=True,
             link="Förhandlad hyreshöjning slår igenom i KPIF:s hyrespost, mest jan–apr samma år.",
             note="2016–2026; saknas 2010–2015 och 2027 (pågår). Vårens preliminära siffra revideras."),
        Spec("kpi_rent_index", "inflation", "KPIF-post hyror för hyresgäster (COICOP 04.1.1), index", "2020=100",
             "M", "SCB TAB6598", kpi_rent_index, LAG_KPI, revised=True,
             link="Hyresposten i KPIF; tar upp förhandlingsutfallet med fördröjning.",
             note="Före 2026 SCB:s omräkning till COICOP 2018, därför revised."),
    ]


def keys() -> list[str]:
    return [s.key for s in specs()]


# ------------------------------------------------------------------ comparison (descriptive, no tests)


def compare(rent_index: pd.Series | None = None, rent_change: pd.Series | None = None) -> pd.DataFrame:
    """Per rent year: negotiated outcome vs. the CPI rent post (and SCB's rent survey when given).

    kpi_dec_apr  : % change of the CPI rent index Dec(Y-1) -> Apr(Y) (where most agreements take effect)
    kpi_dec_dec  : % change Dec(Y-1) -> Dec(Y)
    kpi_annual   : % change of the annual average index Y vs Y-1
    share_jan_apr: share of the Dec->Dec change that came in Jan-Apr
    gap_dec_dec  : kpi_dec_dec - negotiated
    """
    idx = kpi_rent_index() if rent_index is None else rent_index
    idx = idx.copy()
    idx.index = pd.PeriodIndex(idx.index, freq="M")
    neg = negotiated()
    rows = []
    for p, v in neg.items():
        y = p.year
        get = lambda m: idx.get(pd.Period(m, "M"))  # noqa: E731
        d0, apr, dec = get(f"{y - 1}-12"), get(f"{y}-04"), get(f"{y}-12")
        yr = idx[idx.index.year == y]
        yr0 = idx[idx.index.year == y - 1]
        row = {"year": y, "negotiated": v,
               "kpi_dec_apr": 100 * (apr / d0 - 1) if d0 and apr else None,
               "kpi_dec_dec": 100 * (dec / d0 - 1) if d0 and dec else None,
               "kpi_annual": 100 * (yr.mean() / yr0.mean() - 1) if len(yr) == 12 and len(yr0) == 12 else None}
        if row["kpi_dec_apr"] is not None and row["kpi_dec_dec"]:
            row["share_jan_apr"] = row["kpi_dec_apr"] / row["kpi_dec_dec"]
        if row["kpi_dec_dec"] is not None:
            row["gap_dec_dec"] = row["kpi_dec_dec"] - v
        if rent_change is not None:
            row["scb_rent_change"] = rent_change.get(pd.Period(f"{y}-12", "M"))
        rows.append(row)
    return pd.DataFrame(rows).set_index("year")


def monthly_profile(rent_index: pd.Series | None = None, years: range = range(2016, 2027)) -> pd.DataFrame:
    """m/m % change of the CPI rent index by calendar month (rows: year, columns: month)."""
    idx = kpi_rent_index() if rent_index is None else rent_index
    mm = 100 * idx.pct_change()
    mm = mm[mm.index.year.isin(list(years))]
    return mm.groupby([mm.index.year, mm.index.month]).first().unstack()


if __name__ == "__main__":
    from kpif_nowcast.catalog import scb

    rc = scb("TAB6051", Region="00", ContentsCode="000005VT")()
    pd.set_option("display.width", 160)
    print(compare(rent_change=rc).round(2).to_string())
    print()
    print(monthly_profile().round(2).to_string())
