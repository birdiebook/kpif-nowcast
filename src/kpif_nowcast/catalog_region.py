"""K4 "regional Sweden": county (län) series for the 21 counties plus the national total.

Descriptive only: these series feed the dashboard's regional section, not the forecast models.
They live in `catalog.REGIONAL`, not in `catalog.CATALOG`, so the national candidate lists of the
screens and ML jobs (j3_screen, k2_ml) and the national dashboard are unchanged.

Keys: one observation-table series per measure and county, `region_<measure>_<code>`, where <code> is
the county code ("01" Stockholm ... "25" Norrbotten) and "00" the national total. This fits the
existing (series, period) model without a new column; `frame(measure)` puts a measure back together.

Sources and publication lags (days after period end, rounded towards later publication):
- Arbetsförmedlingen (AF), "tidigare statistik" Excel files. The county breakdown sits in the files'
  pivot caches (sources/xlsx_pivot.py). Same lag as J6: 15 days.
  * web-sok-lan-kom: registered unemployed and openly unemployed per municipality/county, 1996-01-.
  * web-Inskrivna-arbetslosa-andel-av-bas: registered unemployed as % of the labour force (BAS), 2023-01-.
  * web-inskrivna-arbetslosa-andel-av-reg-ak2008-2023-12: the same on the older register-based labour
    force, 2008-01..2023-12 (discontinued; a break against the BAS series, see docs/auto2/k4/kvalitet.md).
  * web-varsel-lan-1992-ÅÅÅÅ-MM: notices of redundancy per county; AF stopped updating the file after
    2026-03 (later data only in AF's interactive statistics tool -> BLOCKED after 2026-03).
- SCB PxWebApi v2:
  * TAB5663 BAS unemployment 20-65 years, %, monthly 2024M01-. August 2026 published 2026-10-27 -> 60 days.
    Preliminary statistics -> revised.
  * TAB2923 LFS (AKU) 15-74 by county, quarterly 2005K1-. Unemployment rate = unemployed / (unemployed +
    employed), from thousands. 2026K3 published 2026-10-16 -> 30 days. Not seasonally adjusted.
  * TAB1167 sold one- or two-dwelling houses, mean purchase price (tkr), quarterly 1998K1-.
    2026K3 published 2026-10-23 -> 30 days; latest quarter preliminary -> revised.
  * TAB1148 real estate price index for one- or two-dwelling houses (1990=100), annual 1990-2025.
    Kalmar and Gotland are published together (code "08+09" -> key suffix "0809"). 2025 published
    2026-06-05 -> 180 days.
  * TAB1625 (2000M01-2024M12) + TAB6473 (2025M01-) population at month end. September 2026 published
    2026-11-11 -> 45 days.
- Tillväxtanalys PxWeb v1 (open, no account), table 11_konkurser_manad_lan: bankruptcies per county
  and month, 1996M01-. Published ~day 5 -> 10 days (same as `bankruptcies` in catalog.py). The table has
  no national total; "00" is the sum of the counties.

Raw files are cached under data/raw/k4/. AF files are named after their data month, so a file whose name
is cached is not downloaded again; API responses are reused for MAX_AGE_DAYS. Offline mode
(KPIF_OFFLINE=1) uses the newest cached file. At most 3 tries with exponential backoff per request.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "k4"
MAX_AGE_DAYS = 7
HEADERS = {"User-Agent": "kpif-nowcast research script"}

COUNTIES = {
    "01": "Stockholm", "03": "Uppsala", "04": "Södermanland", "05": "Östergötland", "06": "Jönköping",
    "07": "Kronoberg", "08": "Kalmar", "09": "Gotland", "10": "Blekinge", "12": "Skåne", "13": "Halland",
    "14": "Västra Götaland", "17": "Värmland", "18": "Örebro", "19": "Västmanland", "20": "Dalarna",
    "21": "Gävleborg", "22": "Västernorrland", "23": "Jämtland", "24": "Västerbotten", "25": "Norrbotten",
}
NATIONAL = "00"
NAMES = {NATIONAL: "Riket", **COUNTIES, "0809": "Kalmar och Gotland"}

# Tile-grid map (column, row) for a county map without boundaries: north at the top, roughly geographic.
TILE_GRID = {
    "25": (3, 0), "24": (2, 1), "23": (1, 2), "22": (2, 2), "20": (1, 3), "21": (2, 3), "17": (0, 4),
    "19": (1, 4), "03": (2, 4), "01": (3, 4), "18": (1, 5), "04": (2, 5), "14": (0, 6), "05": (1, 6),
    "09": (3, 6), "13": (0, 7), "06": (1, 7), "08": (2, 7), "07": (1, 8), "10": (2, 8), "12": (1, 9),
}


def county_code(name: str) -> str | None:
    """County code from an AF / Tillväxtanalys label ('Stockholms', 'Västra Götalands län', '08 Kalmars län')."""
    s = re.sub(r"^\d{2}\s+", "", str(name).strip())
    s = re.sub(r"\s+län$", "", s).strip()
    if s in ("Riket", "Sverige", "Sweden"):
        return NATIONAL
    for code, base in COUNTIES.items():
        if s in (base, base + "s"):
            return code
    return None


# ------------------------------------------------------------------ cache and HTTP


def _offline() -> bool:
    from kpif_nowcast.sources import rawcache

    return rawcache.offline()


def _stamp(p: Path) -> date | None:
    m = re.search(r"_(\d{8})\.\w+$", p.name)
    return datetime.strptime(m.group(1), "%Y%m%d").date() if m else None


def _cached(prefix: str, ext: str, max_age: int | None = MAX_AGE_DAYS) -> Path | None:
    """Newest data/raw/k4/<prefix>_<YYYYMMDD><ext> (no older than max_age days unless offline)."""
    hits = [(d, p) for p in RAW_DIR.glob(f"{prefix}_*{ext}")
            if re.fullmatch(re.escape(prefix) + r"_\d{8}" + re.escape(ext), p.name) and (d := _stamp(p))]
    if not hits:
        return None
    d, p = max(hits)
    if _offline() or max_age is None or (date.today() - d).days <= max_age:
        return p
    return None


def _request(method: str, url: str, tries: int = 3, **kw):
    import requests

    for k in range(tries):
        try:
            r = requests.request(method, url, timeout=120, headers=HEADERS, **kw)
            if r.status_code == 429 and k < tries - 1:
                time.sleep(20 * (k + 1))
                continue
            r.raise_for_status()
            return r
        except Exception:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(2 ** (k + 1))


def _tag(obj) -> str:
    return hashlib.md5(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:6]


def _save(name: str, ext: str, content: bytes) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    p = RAW_DIR / f"{name}_{date.today():%Y%m%d}{ext}"
    p.write_bytes(content)
    return p


# ------------------------------------------------------------------ Arbetsförmedlingen

AF_FILES = {
    "sok_lan": r"web-sok-lan-kom-\d{4}-\d{2}",
    "andel_bas": r"web-Inskrivna-arbetslosa-andel-av-bas-\d{4}-\d{2}",
    "andel_ak08": r"web-inskrivna-arbetslosa-andel-av-reg-ak2008-2023-12",
    "varsel_lan": r"web-varsel-lan-1992-\d{4}-\d{2}",
}


@lru_cache(maxsize=1)
def _af_page() -> str:
    from kpif_nowcast.catalog_af import PAGE

    return _request("GET", PAGE).text


def af_file(kind: str, page_html: str | None = None) -> Path:
    """Cached path of the current AF file of `kind`; downloads it when this file name is not cached yet."""
    pat = AF_FILES[kind]
    if _offline():
        hits = sorted(p for p in RAW_DIR.glob("*.xlsx") if re.fullmatch(pat + r"_\d{8}\.xlsx", p.name))
        if not hits:
            raise RuntimeError(f"offline: no cached AF file for {kind}")
        return hits[-1]
    html = page_html if page_html is not None else _af_page()
    m = re.search(r'(/download/[^"\s]+/(' + pat + r')\.xlsx)', html)
    if not m:
        raise RuntimeError(f"no AF file link for {kind}")
    link, name = m.group(1), m.group(2)
    hit = _cached(name, ".xlsx", max_age=None)
    if hit is not None:
        return hit
    from kpif_nowcast.catalog_af import BASE

    return _save(name, ".xlsx", _request("GET", BASE + link).content)


def _pivot_with(path: Path, field: str, fields: list[str]) -> pd.DataFrame:
    """Records of the first pivot cache in `path` that has cache field `field`."""
    import zipfile

    from kpif_nowcast.sources.xlsx_pivot import cache_fields, read_pivot_cache

    with zipfile.ZipFile(path) as z:
        ns = sorted(int(m.group(1)) for n in z.namelist()
                    if (m := re.fullmatch(r"xl/pivotCache/pivotCacheDefinition(\d+)\.xml", n)))
    for n in ns:
        if field in [f for f, _ in cache_fields(path, n)]:
            return read_pivot_cache(path, n, fields)
    raise RuntimeError(f"{path.name}: no pivot cache with field {field}")


def _wide(df: pd.DataFrame, value: str, how: str = "sum") -> pd.DataFrame:
    """Long (period, code, value) -> wide Period[M] x code, plus national total '00' as the sum over all rows."""
    g = df.groupby(["period", "code"])[value].agg(how).unstack("code")
    g.index = pd.PeriodIndex(g.index, freq="M")
    return g.sort_index()


@lru_cache(maxsize=1)
def _af_counts() -> pd.DataFrame:
    """Registered unemployed (INSAL) and openly unemployed (ALTOT) per county and month."""
    df = _pivot_with(af_file("sok_lan"), "ALDGR", ["PERIOD", "LAN", "INSAL", "ALTOT"])
    df["code"] = df["LAN"].map(county_code)  # 'Uppgift saknas' -> None: only in the national total
    df["period"] = df["PERIOD"]
    return df


def _af_count_frame(col: str) -> pd.DataFrame:
    df = _af_counts()
    w = _wide(df.dropna(subset=["code"]), col)
    nat = df.groupby("period")[col].sum()
    nat.index = pd.PeriodIndex(nat.index, freq="M")
    w[NATIONAL] = nat
    return w


@lru_cache(maxsize=2)
def _af_share(kind: str) -> pd.DataFrame:
    """Registered unemployed as % of the labour force: sum(TOTSOK) / sum(TOTAK) * 100 per county.

    National total as AF publishes it: all registered unemployed, including the few without a known
    municipality (one record per month, no labour force), over the total labour force.
    """
    df = _pivot_with(af_file(kind), "TOTAK", ["PERIOD", "LAN", "TOTSOK", "TOTAK"]).dropna(subset=["PERIOD"])
    df["code"] = df["LAN"].map(county_code)
    df["period"] = df["PERIOD"]
    known = df.dropna(subset=["code", "TOTSOK", "TOTAK"])
    out = _wide(known, "TOTSOK") / _wide(known, "TOTAK") * 100
    tot = df.groupby("period")[["TOTSOK", "TOTAK"]].sum()
    nat = tot["TOTSOK"] / tot["TOTAK"] * 100
    nat.index = pd.PeriodIndex(nat.index, freq="M")
    out[NATIONAL] = nat
    return out


@lru_cache(maxsize=1)
def _af_varsel() -> pd.DataFrame:
    """Persons affected by notices per county and month (sheet 'Månad 1992-01--ÅÅÅÅ-MM')."""
    from kpif_nowcast.sources.xlsx_lite import read_sheets

    sheets = read_sheets(af_file("varsel_lan"))
    rows = next(v for k, v in sheets.items() if k.startswith("Månad"))
    hi = next(i for i, r in enumerate(rows) if r and len(r) > 2 and r[0] is None and r[1] and county_code(r[1]))
    codes = [county_code(c) if c else None for c in rows[hi]]
    data = {}
    for r in rows[hi + 1:]:
        if not r or not re.fullmatch(r"\d{4}-\d{2}", str(r[0])):
            continue
        data[pd.Period(r[0], "M")] = {c: (float(r[j]) if j < len(r) and isinstance(r[j], float) else np.nan)
                                      for j, c in enumerate(codes) if c}
    # A few county cells are empty (7 of ~8 600); the yearly sheets' row sums show they mean 0.
    return pd.DataFrame(data).T.sort_index().fillna(0.0)


# ------------------------------------------------------------------ SCB

SCB_URL = "https://statistikdatabasen.scb.se/api/v2/tables/{table}/data"
SCB_REGIONS = ",".join([NATIONAL, *COUNTIES])


def _scb(table: str, codes: dict[str, str]) -> pd.DataFrame:
    from kpif_nowcast.sources.scb import _jsonstat_to_frame

    req = {**codes, "Tid": "*"}
    name = f"scb_{table}_{_tag(req)}"
    hit = _cached(name, ".json")
    if hit is None:
        if _offline():
            raise RuntimeError(f"offline: no cached SCB file {name}")
        params = {"lang": "sv", "outputFormat": "json-stat2", **{f"valueCodes[{k}]": v for k, v in req.items()}}
        r = _request("GET", SCB_URL.format(table=table), params=params)
        time.sleep(0.5)  # well under SCB's 30 calls per 10 s
        hit = _save(name, ".json", r.content)
    df = _jsonstat_to_frame(json.loads(hit.read_text(encoding="utf-8")))
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def _scb_wide(df: pd.DataFrame, region_col: str = "Region") -> pd.DataFrame:
    from kpif_nowcast.sources.scb import to_month_period

    df = df.copy()
    df["period"] = to_month_period(df["Tid"])
    df["code"] = df[region_col].str.replace("+", "", regex=False)
    w = df.pivot_table(index="period", columns="code", values="value", aggfunc="first")
    w.index = pd.PeriodIndex(w.index, freq="M")
    return w.sort_index()


@lru_cache(maxsize=1)
def _bas_unemp() -> pd.DataFrame:
    return _scb_wide(_scb("TAB5663", {"Region": SCB_REGIONS, "NyckeltalSCB": "BAS03", "ContentsCode": "000007AN"}))


@lru_cache(maxsize=1)
def _aku_unemp() -> pd.DataFrame:
    df = _scb("TAB2923", {"Region": SCB_REGIONS, "Arbetskraftstillh": "ALÖS,SYS", "Kon": "1+2",
                          "ContentsCode": "AM0401UZ"})
    une = _scb_wide(df[df["Arbetskraftstillh"] == "ALÖS"])
    emp = _scb_wide(df[df["Arbetskraftstillh"] == "SYS"])
    return une / (une + emp) * 100


@lru_cache(maxsize=1)
def _house_price() -> pd.DataFrame:
    return _scb_wide(_scb("TAB1167", {"Region": SCB_REGIONS, "ContentsCode": "BO0501L3"}))


@lru_cache(maxsize=1)
def _fpi() -> pd.DataFrame:
    return _scb_wide(_scb("TAB1148", {"Lan": "*", "ContentsCode": "BO0501R5"}), region_col="Lan")


@lru_cache(maxsize=1)
def _population() -> pd.DataFrame:
    old = _scb_wide(_scb("TAB1625", {"Region": SCB_REGIONS, "Forandringar": "100", "Kon": "1+2",
                                     "ContentsCode": "000003KD"}))
    new = _scb_wide(_scb("TAB6473", {"Region": SCB_REGIONS, "Forandringar": "100", "Kon": "TotSa",
                                     "ContentsCode": "000007SR"}))
    return pd.concat([old[old.index < new.index.min()], new]).sort_index()


# ------------------------------------------------------------------ Tillväxtanalys

TVA_URL = ("https://statistik.tillvaxtanalys.se/PxWeb/api/v1/sv/Tillv%C3%A4xtanalys%20statistikdatabas/"
           "Konkurser%20och%20offentliga%20ackord/11_konkurser_manad_lan.px")


@lru_cache(maxsize=1)
def _bankruptcies() -> pd.DataFrame:
    from kpif_nowcast.sources.scb import to_month_period

    query = {"query": [{"code": "variabel", "selection": {"filter": "item", "values": ["0"]}}],
             "response": {"format": "json"}}
    name = f"tva_konkurser_lan_{_tag(query)}"
    hit = _cached(name, ".json")
    if hit is None:
        if _offline():
            raise RuntimeError(f"offline: no cached file {name}")
        hit = _save(name, ".json", _request("POST", TVA_URL, json=query).content)
    payload = json.loads(hit.read_text(encoding="utf-8"))
    cols = [c["code"] for c in payload["columns"] if c.get("type") != "c"]
    t = next(c["code"] for c in payload["columns"] if c.get("type") == "t")
    rows = []
    for r in payload["data"]:
        key = dict(zip(cols, r["key"]))
        v = r["values"][0]
        rows.append((key[t], key["Län"], None if v in ("..", ".", "", "-") else float(v)))
    df = pd.DataFrame(rows, columns=["Tid", "code", "value"])
    df["period"] = to_month_period(df["Tid"])
    w = df.pivot_table(index="period", columns="code", values="value", aggfunc="first")
    w.index = pd.PeriodIndex(w.index, freq="M")
    w = w[w.index < pd.Period(date.today(), "M")]
    w[NATIONAL] = w[list(COUNTIES)].sum(axis=1, min_count=len(COUNTIES))
    return w.sort_index()


# ------------------------------------------------------------------ measures


@dataclass(frozen=True)
class Measure:
    key: str
    label: str
    unit: str
    freq: str
    source: str
    lag_days: int
    revised: bool
    loader: Callable[[], pd.DataFrame]
    change: str  # how the dashboard shows change over a year: "pp" (difference) or "pct" (% change)
    codes: tuple[str, ...] = (NATIONAL, *COUNTIES)
    link: str = ""
    note: str = ""


AF_SRC = "Arbetsförmedlingen, tidigare statistik"
MEASURES = [
    Measure("af_andel", "Inskrivna arbetslösa, andel av arbetskraften (AF)", "%", "M",
            f"{AF_SRC} (web-Inskrivna-arbetslosa-andel-av-bas)", 15, True, lambda: _af_share("andel_bas"), "pp",
            link="Registerbaserad arbetslöshet per län, månadsvis.",
            note="Från 2023-01. Arbetskraft från SCB:s BAS (16–65 år 2023–2025, 16–66 år från 2026). "
                 "revised=True: nämnaren kan uppdateras när ny BAS-årgång kommer (inte verifierat)."),
    Measure("af_andel_ak08", "Inskrivna arbetslösa, andel av registerbaserad arbetskraft (AF, äldre bas)", "%", "M",
            f"{AF_SRC} (web-inskrivna-arbetslosa-andel-av-reg-ak2008-2023-12)", 15, False,
            lambda: _af_share("andel_ak08"), "pp",
            link="Lång historik för länsjämförelse.",
            note="2008-01–2023-12, avslutad. Annan nämnare än af_andel: brott 2023, se kvalitet.md."),
    Measure("af_inskrivna", "Inskrivna arbetslösa (AF)", "antal", "M", f"{AF_SRC} (web-sok-lan-kom)", 15, False,
            lambda: _af_count_frame("INSAL"), "pct",
            link="Öppet arbetslösa plus arbetslösa i program.",
            note="Från 1996-01. Åldersbrott 16–64 / 16–65 (2023–2025) / 16–66 (2026–). Riket inkl. okänt län."),
    Measure("af_oppet", "Öppet arbetslösa (AF)", "antal", "M", f"{AF_SRC} (web-sok-lan-kom)", 15, False,
            lambda: _af_count_frame("ALTOT"), "pct",
            link="Arbetslösa utanför program.", note="Som af_inskrivna."),
    Measure("af_varsel", "Varsel om uppsägning, personer (AF)", "antal", "M", f"{AF_SRC} (web-varsel-lan)", 15, True,
            _af_varsel, "pct",
            link="Ledande indikator för arbetslöshet per län.",
            note="1992-01–2026-03: AF uppdaterar inte filen efter 2026-03 (BLOCKED därefter). Län efter "
                 "företagets organisationsnummer. Riket inkl. 'Inga uppgifter'."),
    Measure("bas_arbetsloshet", "Arbetslöshet 20–65 år (SCB BAS)", "%", "M", "SCB TAB5663", 60, True,
            _bas_unemp, "pp",
            link="Registerbaserad arbetslöshet enligt SCB, månadsvis.", note="Från 2024-01, preliminär statistik."),
    Measure("aku_arbetsloshet", "Arbetslöshet 15–74 år (AKU)", "%", "Q", "SCB TAB2923", 30, True, _aku_unemp, "pp",
            link="Enkätbaserad arbetslöshet per län, kvartal.",
            note="Från 2005K1. Beräknad som arbetslösa/(arbetslösa+sysselsatta) ur tusental; ej säsongsrensad. "
                 "Stor osäkerhet i små län (SCB anger felmarginal)."),
    Measure("smahus_pris", "Försålda småhus, köpeskilling medelvärde", "tkr", "Q", "SCB TAB1167", 30, True,
            _house_price, "pct",
            link="Bostadspriser per län.",
            note="Från 1998K1. Medelpris, inte kvalitetsjusterat: påverkas av vilka hus som säljs. "
                 "Senaste kvartalet preliminärt."),
    Measure("fpi_smahus", "Fastighetsprisindex permanenta småhus (1990=100)", "index", "A", "SCB TAB1148", 180, True,
            _fpi, "pct", codes=(NATIONAL, *[c for c in COUNTIES if c not in ("08", "09")], "0809"),
            link="Kvalitetsjusterade småhuspriser per län, årsvis.",
            note="1990–2025. Kalmar och Gotland redovisas tillsammans (0809)."),
    Measure("konkurser", "Konkurser, antal", "antal", "M", "Tillväxtanalys 11_konkurser_manad_lan", 10, False,
            _bankruptcies, "pct",
            link="Finansiell stress per län.", note="Från 1996-01. Riket = summan av länen."),
    Measure("befolkning", "Folkmängd", "antal", "M", "SCB TAB1625 + TAB6473", 45, False, _population, "pct",
            link="Nämnare för per capita-mått.", note="Från 2000-01, vid månadens slut."),
]
BY_MEASURE = {m.key: m for m in MEASURES}


def series_key(measure: str, code: str) -> str:
    return f"region_{measure}_{code}"


def _fetcher(m: Measure, code: str) -> Callable[[], pd.Series]:
    def f() -> pd.Series:
        w = m.loader()
        if code not in w.columns:
            raise KeyError(f"{m.key}: no column {code}")
        return w[code].dropna().rename(series_key(m.key, code))

    return f


def specs() -> list:
    """Catalog entries, one per measure and county (lazy import of Spec: catalog.py imports this module)."""
    from kpif_nowcast.catalog import Spec

    return [Spec(series_key(m.key, c), "region", f"{m.label}, {NAMES[c]}", m.unit, m.freq, m.source,
                 _fetcher(m, c), m.lag_days, revised=m.revised, link=m.link, note=m.note)
            for m in MEASURES for c in m.codes]


def keys() -> list[str]:
    return [series_key(m.key, c) for m in MEASURES for c in m.codes]


def parse_key(key: str) -> tuple[str, str]:
    """'region_af_andel_01' -> ('af_andel', '01')."""
    m = re.fullmatch(r"region_(.+)_(\d{2,4})", key)
    if not m:
        raise ValueError(key)
    return m.group(1), m.group(2)


# ------------------------------------------------------------------ reading back from the table


def frame(measure: str, table: pd.DataFrame | None = None, when: str = "2100-01-01") -> pd.DataFrame:
    """One measure from the observation table as Period[M] x county code (latest vintage known at `when`)."""
    from kpif_nowcast import observations as obs

    table = obs.load() if table is None else table
    m = BY_MEASURE[measure]
    cols = {c: obs.as_of(series_key(measure, c), when, table) for c in m.codes}
    return pd.DataFrame({c: s for c, s in cols.items() if not s.empty}).sort_index()


def latest_by_county(table: pd.DataFrame | None = None) -> list[dict]:
    """Latest value and change over a year per measure and county (JSON-friendly rows, for the dashboard).

    change: 'pp' = difference in percentage points, 'pct' = % change vs the same period a year earlier.
    Derived measure 'konkurser_per_10k': bankruptcies over the last 12 months per 10 000 inhabitants.
    rank: 1 = highest value among the counties (the national total is not ranked).
    period is per county; behind_national = the county's latest period is older than the national one.
    tile: (column, row) in TILE_GRID for a tile-grid map (no open county boundaries, see kvalitet.md).
    """
    from kpif_nowcast import observations as obs

    table = obs.load() if table is None else table
    out = []
    frames = {m.key: frame(m.key, table) for m in MEASURES}
    for m in MEASURES:
        w = frames[m.key]
        if w.empty:
            continue
        out += _rows(m.key, m.label, m.unit, m.freq, m.change, w)
    k, pop = frames.get("konkurser"), frames.get("befolkning")
    if k is not None and pop is not None and not k.empty and not pop.empty:
        per = (k.rolling(12, min_periods=12).sum() / pop.reindex(k.index).ffill() * 10_000).dropna(how="all")
        out += _rows("konkurser_per_10k", "Konkurser senaste 12 mån per 10 000 invånare", "per 10 000", "M", "pp", per)
    return out


def _rows(key, label, unit, freq, change, w: pd.DataFrame) -> list[dict]:
    step = {"M": 12, "Q": 12, "A": 12}[freq]  # periods sit on months: a year back is always 12 months
    rows = []
    for code in w.columns:
        s = w[code].dropna()
        if s.empty:
            continue
        p = s.index.max()
        prev = s.get(p - step)
        v = float(s.iloc[-1])
        if prev is None or pd.isna(prev):
            ch = None
        elif change == "pp":
            ch = v - float(prev)
        else:
            ch = (v / float(prev) - 1) * 100 if prev else None
        rows.append({"measure": key, "label": label, "unit": unit, "freq": freq, "code": code,
                     "county": NAMES.get(code, code), "period": str(p), "value": round(v, 4),
                     "value_year_ago": None if ch is None else round(float(prev), 4),
                     "change": None if ch is None else round(ch, 4), "change_kind": change,
                     "tile": list(TILE_GRID[code]) if code in TILE_GRID else None})
    nat = next((r["period"] for r in rows if r["code"] == NATIONAL), None)
    for r in rows:  # e.g. LFS cells SCB suppressed in the latest quarter: the county shows an older period
        r["behind_national"] = nat is not None and r["period"] < nat
    counties = [r for r in rows if r["code"] != NATIONAL]
    for i, r in enumerate(sorted(counties, key=lambda r: -r["value"])):
        r["rank"] = i + 1
    return rows


# ------------------------------------------------------------------ quality check


def quality(table: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """Quality tables: per series (span, holes, duplicates, known_from) and per measure (coverage, sum check)."""
    from kpif_nowcast import observations as obs

    table = obs.load() if table is None else table
    t = table[table["series"].str.startswith("region_")]
    per_series = {}
    for k in keys():
        x = t[t["series"] == k]
        if x.empty:
            per_series[k] = {"rows": 0}
            continue
        per = pd.PeriodIndex(x["period"], freq="M")
        step = {"M": 1, "Q": 3, "A": 12}[BY_MEASURE[parse_key(k)[0]].freq]
        span = pd.period_range(per.min(), per.max(), freq="M")[::step]
        end = (per + 1).to_timestamp() - pd.Timedelta(days=1)
        per_series[k] = {
            "rows": len(x), "from": str(per.min()), "to": str(per.max()),
            "holes": len(span) - x["period"].nunique(),
            "dup_keys": int(x.duplicated(["series", "period", "known_from"]).sum()),
            "kf_before_end": int((x["known_from"].to_numpy() < end.to_numpy()).sum()),
            "negative": int((x["value"] < 0).sum()),
        }
    per_measure = {}
    for m in MEASURES:
        w = frame(m.key, table)
        missing = [c for c in m.codes if c not in w.columns]
        row = {"series": len(m.codes) - len(missing), "missing_codes": ",".join(missing),
               "from": str(w.index.min()) if len(w) else "", "to": str(w.index.max()) if len(w) else ""}
        counties = [c for c in m.codes if c != NATIONAL and c in w.columns]
        if NATIONAL in w.columns and counties:
            if m.unit != "antal":  # rates, mean prices, indices: national must lie inside the county range
                inside = ((w[NATIONAL] >= w[counties].min(axis=1)) & (w[NATIONAL] <= w[counties].max(axis=1)))
                row["national_inside_county_range_share"] = round(float(inside[w[NATIONAL].notna()].mean()), 4)
            else:  # counts: the counties add up to the national total
                both = w[[NATIONAL]].join(w[counties].sum(axis=1, min_count=len(counties)).rename("sum")).dropna()
                dev = (both["sum"] / both[NATIONAL] - 1) * 100
                row["sum_vs_national_max_abs_pct"] = round(float(dev.abs().max()), 4)
                row["sum_vs_national_mean_pct"] = round(float(dev.mean()), 4)
        per_measure[m.key] = row
    return {"series": pd.DataFrame(per_series).T, "measures": pd.DataFrame(per_measure).T}


if __name__ == "__main__":
    q = quality()
    print(q["measures"].to_string())
    s = q["series"]
    print(s[(s.get("holes", 0) != 0) | (s.get("rows", 0) == 0)].to_string())
