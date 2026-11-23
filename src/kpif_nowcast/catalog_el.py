"""L5 electricity: contract shares and grid fees, for the January effect.

Why: the CPIF electricity item mixes spot-linked contracts (pass the monthly spot price through at once),
fixed-price contracts (repriced when they roll over, often in January) and the grid fee (network tariff,
usually changed on 1 January). The January electricity miss comes from the last two. These series let
wave 2 measure them; no model or test here.

Sources (open, no key):
- SCB TAB3571 (EN0301): share of household electricity contracts per contract type, monthly, %, 2013-04-.
  The table note documents revisions (Jan-Mar 2022 revised in April 2022, May 2023-Jun 2024 corrected
  2024-09-27; from 2025-02 quarter-hour contracts are reported together with hourly contracts).
- SCB TAB3950 (EN0301, annual): grid prices per 1 January, ore/kWh excl. taxes, per customer category.
  'viktat' (weighted by connection points) from 2015, 'oviktat' from 1996.
- Energimarknadsinspektionen (Ei), "Natavgifter - elnat": every grid operator's reported tariff per
  1 January for type customers, xlsx 1999-. We take the median over tariff areas of the total yearly fee
  (kr/year excl. VAT) and the share of tariff areas that raised the fee from the year before.

Publication lags (evidence in docs/publiceringskalender.md, section "Korning 3: L5"):
- TAB3571: month m around the 22nd-24th of m+1 (Sep 2026 -> 2026-10-23, Oct 2026 scheduled 2026-11-24,
  Ei: "uppdateras runt den 22:a i varje manad med en manads fordrojning") -> 28 days, revised=True.
- TAB3950 and Ei: year Y (tariffs per 1 January Y) out in May of Y (SCB 2026-05-22, Ei file 2026-05-12)
  -> -180 days against the December the year is stored on (known from early July of Y). So the tariff
  for January Y is NOT known at the January Y deadline (4 February); at that point only Y-1 is known.

Annual values sit on December (catalog convention). Raw responses are cached under
data/raw/l5/<name>_<fetch date>.<ext> and reused for MAX_AGE_DAYS.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote, urljoin

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "l5"
MAX_AGE_DAYS = 7
HEADERS = {"User-Agent": "kpif-nowcast research script"}

SCB_URL = "https://statistikdatabasen.scb.se/api/v2/tables/{table}/data"
EI_PAGE = "https://ei.se/om-oss/statistik-och-oppna-data/natavgifter---elnat"
# Archive file (all years) as linked from EI_PAGE on 2026-11-23; used only if the page cannot be parsed.
EI_FALLBACK = "https://ei.se/download/18.6586000219eb48404e7ac7/1781185169892/Hush%C3%A5llskunder.xlsx"

LAG_CONTRACTS, LAG_GRID = 28, -180

# ------------------------------------------------------------------ cache and HTTP


def _fresh(pattern: str, today: date | None = None) -> Path | None:
    """Newest cached file in data/raw/l5 matching the glob, no older than MAX_AGE_DAYS."""
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


def _request(url: str, tries: int = 3, pause: float = 0.5, **kw):
    import requests

    for k in range(tries):
        try:
            r = requests.get(url, timeout=60, headers=HEADERS, **kw)
            if r.status_code == 429 and k < tries - 1:
                time.sleep(20 * (k + 1))
                continue
            r.raise_for_status()
            time.sleep(pause)
            return r
        except Exception:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(2 ** (k + 1))


def _save(name: str, ext: str, content: bytes) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    p = RAW_DIR / f"{name}_{date.today():%Y%m%d}.{ext}"
    p.write_bytes(content)
    return p


def _tag(obj) -> str:
    return hashlib.md5(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:6]


# ------------------------------------------------------------------ SCB


def scb_frame(table: str, codes: dict[str, str]) -> pd.DataFrame:
    """Long frame of one SCB table selection (json-stat2), cached."""
    from kpif_nowcast.sources.scb import _jsonstat_to_frame

    name = f"scb_{table}_{_tag(codes)}"
    hit = _fresh(f"{name}_*.json")
    if hit is not None:
        payload = json.loads(hit.read_text(encoding="utf-8"))
    else:
        params = {"lang": "en", "outputFormat": "json-stat2", **{f"valueCodes[{k}]": v for k, v in codes.items()}}
        r = _request(SCB_URL.format(table=table), params=params)
        _save(name, "json", r.content)
        payload = r.json()
    df = _jsonstat_to_frame(payload)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def _to_series(df: pd.DataFrame) -> pd.Series:
    from kpif_nowcast.sources.scb import to_month_period

    if df["Tid"].duplicated().any():
        raise ValueError("SCB selection is not exactly one series")
    s = df.set_index("Tid")["value"]
    s.index = to_month_period(s.index.to_series())
    return s.dropna().sort_index()


def contract_share(*types: str, zone: str = "00"):
    """Share (%) of household contracts of the given TAB3571 types, summed, for one bidding zone."""

    def f() -> pd.Series:
        df = scb_frame("TAB3571", {"Elomrade": zone, "Avtalstyp": "*", "ContentsCode": "*", "Tid": "*"})
        df = df[df["Avtalstyp"].isin(types)]
        missing = set(types) - set(df["Avtalstyp"])
        if missing:
            raise ValueError(f"TAB3571: contract types {sorted(missing)} not in table")
        wide = df.pivot_table(index="Tid", columns="Avtalstyp", values="value", aggfunc="first")
        # Hourly contracts are reported separately only from 2023-02 (before that they sat mainly in
        # 'rorligt'), so a later type that is missing counts as 0; the first type must be present.
        s = wide[types[0]] + wide[list(types[1:])].fillna(0).sum(axis=1)
        from kpif_nowcast.sources.scb import to_month_period

        s.index = to_month_period(s.index.to_series())
        return s.dropna().sort_index()

    return f


def grid_price(category: str, weighting: str = "viktat"):
    """Grid price per 1 January, ore/kWh excl. taxes (TAB3950), one customer category; year Y on Y-12."""

    def f() -> pd.Series:
        df = scb_frame("TAB3950", {"Kundkategori": "*", "Viktat": "*", "ContentsCode": "*", "Tid": "*"})
        df = df[(df["Kundkategori"] == category) & (df["Viktat"] == weighting)]
        if df.empty:
            raise ValueError(f"TAB3950: no data for category {category}, {weighting}")
        return _to_series(df[["Tid", "value"]])

    return f


# ------------------------------------------------------------------ Energimarknadsinspektionen


def ei_archive_url(page_html: str) -> str:
    """Link to the all-years household file ('Hushållskunder 1999-YYYY') on Ei's grid fee page."""
    best = None
    for m in re.finditer(r'href="(/download/[^"]+\.xlsx)"[^>]*>(.*?)</a>', page_html, re.S):
        href, text = html.unescape(m.group(1)), re.sub(r"<[^>]+>", " ", m.group(2))
        name = unquote(href.rsplit("/", 1)[-1])
        if re.search(r"Hushållskunder\s*1999", html.unescape(text)) or name == "Hushållskunder.xlsx":
            best = href
            break
    if best is None:
        raise ValueError("Ei page: no link to the household archive file")
    return urljoin(EI_PAGE, best)


def _ei_file() -> Path:
    hit = _fresh("ei_hushallskunder_*.xlsx")
    if hit is not None:
        return hit
    try:
        url = ei_archive_url(_request(EI_PAGE).text)
    except Exception:  # noqa: BLE001 - page layout changed: fall back to the last known link
        url = EI_FALLBACK
    r = _request(url)
    if not r.content.startswith(b"PK"):
        raise ValueError(f"Ei: {url} is not an xlsx file")
    return _save("ei_hushallskunder", "xlsx", r.content)


def parse_ei(rows: list[list]) -> pd.DataFrame:
    """Ei household sheet -> long frame (row, operator, code, year, value).

    Layout: one row with item codes (NT2000 = 'Villa 16A, 5 000 kWh/år, totalt kr/år'), one with labels,
    one starting with 'ReNamn' with the years; then one row per operator and tariff area. A code cell is
    left blank when the code repeats over several year columns. Blank and text cells are skipped.
    """
    head = [i for i, r in enumerate(rows[:10]) if r and r[0] == "ReNamn"]
    if not head:
        raise ValueError("Ei: header row 'ReNamn' not found")
    yi = head[0]
    ci = [i for i in range(yi) if any(isinstance(c, str) and re.fullmatch(r"NT\d{4}", c) for c in rows[i])]
    if not ci:
        raise ValueError("Ei: item code row not found")
    codes, last = [], None
    for j, c in enumerate(rows[ci[0]]):
        if isinstance(c, str) and re.fullmatch(r"NT\d{4}", c):
            last = c
        codes.append(last if j >= 3 else None)
    years = rows[yi]
    recs = []
    for k, r in enumerate(rows[yi + 1:]):
        if not r or not r[0]:
            continue
        for j in range(3, min(len(r), len(years), len(codes))):
            v, y = r[j], years[j]
            if codes[j] is None or not isinstance(v, (int, float)):
                continue
            try:
                yr = int(float(y))
            except (TypeError, ValueError):
                continue
            recs.append((k, str(r[0]), codes[j], yr, float(v)))
    return pd.DataFrame(recs, columns=["row", "operator", "code", "year", "value"])


def _year_index(s: pd.Series) -> pd.Series:
    s.index = pd.PeriodIndex([pd.Period(f"{y}-12", "M") for y in s.index], freq="M")
    return s.sort_index()


def ei_median(long: pd.DataFrame, code: str) -> pd.Series:
    """Median over tariff areas of a reported fee; zeros (not reported) dropped. Year Y on Y-12."""
    t = long[(long["code"] == code) & (long["value"] > 0)]
    return _year_index(t.groupby("year")["value"].median())


def ei_raise_share(long: pd.DataFrame, code: str, min_pairs: int = 20) -> pd.Series:
    """Share (%) of tariff areas whose fee is higher than the year before (both years > 0).

    Pairs are sheet rows (one row per operator and tariff area). Where the sheet starts new rows (it does
    so for 2003 -> 2004), the pairs are operators with exactly one value in both years instead.
    """
    t = long[(long["code"] == code) & (long["value"] > 0)]
    by_row = t.pivot_table(index="row", columns="year", values="value", aggfunc="first")
    once = t.groupby(["operator", "year"])["value"].transform("size") == 1
    by_op = t[once].pivot_table(index="operator", columns="year", values="value", aggfunc="first")
    out = {}
    for y in sorted(t["year"].unique()):
        for tab in (by_row, by_op):
            if y - 1 in tab.columns and y in tab.columns:
                both = tab[[y - 1, y]].dropna()
                if len(both) >= min_pairs:
                    out[y] = 100.0 * float((both[y] > both[y - 1] + 1e-9).mean())
                    break
    return _year_index(pd.Series(out, dtype=float))


def ei(kind: str, code: str):
    def f() -> pd.Series:
        from kpif_nowcast.sources.xlsx_lite import read_sheets

        sheets = read_sheets(_ei_file())
        long = parse_ei(next(iter(sheets.values())))
        s = ei_median(long, code) if kind == "median" else ei_raise_share(long, code)
        return s[s.index.year < date.today().year + 1]

    return f


# ------------------------------------------------------------------ catalog entries

CONTRACTS = [  # key, TAB3571 types, label
    ("el_contract_spot_share", ("rorligt", "timpris"),
     "Andel elavtal med rörligt pris (månads-, tim- och kvartspris), riket"),
    ("el_contract_hourly_share", ("timpris",), "Andel elavtal med tim- eller kvartspris, riket"),
    ("el_contract_fixed_share", ("avtal1ar", "avtal2ar", "avtal3ar"), "Andel elavtal med fast pris (1–3 år), riket"),
    ("el_contract_default_share", ("anvisat",), "Andel anvisade elavtal (tillsvidarepris), riket"),
]

GRID = [  # key, TAB3950 category, weighting, label
    ("el_grid_price_flat", "1", "viktat", "Elnätspris 1 januari, lägenhet (viktat)"),
    ("el_grid_price_house", "2", "viktat", "Elnätspris 1 januari, villa utan elvärme (viktat)"),
    ("el_grid_price_house_heat", "3", "viktat", "Elnätspris 1 januari, villa med elvärme (viktat)"),
    ("el_grid_price_house_heat_unw", "3", "oviktat", "Elnätspris 1 januari, villa med elvärme (oviktat, lång serie)"),
]

EI = [  # key, kind, Ei item code, label, unit
    ("ei_grid_fee_flat", "median", "NT1600", "Elnätsavgift 1 januari, lägenhet 16A 2 000 kWh, median över nätområden",
     "kr/år exkl. moms"),
    ("ei_grid_fee_house", "median", "NT2000", "Elnätsavgift 1 januari, villa 16A 5 000 kWh, median över nätområden",
     "kr/år exkl. moms"),
    ("ei_grid_fee_house_heat", "median", "NT4000",
     "Elnätsavgift 1 januari, villa 20A 20 000 kWh (elvärme), median över nätområden", "kr/år exkl. moms"),
    ("ei_grid_fee_raise_share", "raise", "NT2000",
     "Andel nätområden som höjt elnätsavgiften 1 januari (villa 16A 5 000 kWh)", "%"),
]


def specs() -> list:
    """Catalog entries (lazy import of Spec: catalog.py imports this module)."""
    from kpif_nowcast.catalog import Spec

    out = []
    for key, types, label in CONTRACTS:
        out.append(Spec(key, "energi", label, "% av hushållens avtal", "M", "SCB TAB3571", contract_share(*types),
                        LAG_CONTRACTS, revised=True,
                        link="Rörliga avtal för över spotpriset direkt till KPIF-el; fasta avtal prissätts om "
                             "när de löper ut (ofta i januari).",
                        note="Reviderad 2022 och 2023–24. Timpris redovisas separat från 2023-02 (låg tidigare "
                             "främst i rörligt). Från 2025-02 ingår kvartsprisavtal i timpris."))
    for key, cat, weighting, label in GRID:
        out.append(Spec(key, "energi", label, "öre/kWh exkl. skatt", "A", "SCB TAB3950", grid_price(cat, weighting),
                        LAG_GRID,
                        link="Nätavgiften ändras oftast 1 januari och är en del av januarieffekten i KPIF-el.",
                        note="År Y = tariff 1 januari Y, publiceras i maj Y: vid januari-deadline är bara Y-1 känt."
                             + (" Viktat från 2015." if weighting == "viktat" else " Från 1996.")))
    for key, kind, code, label, unit in EI:
        out.append(Spec(key, "energi", label, unit, "A", f"Energimarknadsinspektionen nätavgifter {code}",
                        ei(kind, code), LAG_GRID, revised=True,
                        link="Nätbolagens egna tariffer: hur bred och hur stor januarihöjningen av nätavgiften är.",
                        note="År Y = tariff 1 januari Y, Ei publicerar i maj Y. Oviktat (varje nätområde lika). "
                             "Sena eller rättade inrapporteringar kan ändra värdet."))
    return out


def keys() -> list[str]:
    return [s.key for s in specs()]


if __name__ == "__main__":
    for s in specs():
        v = s.fetch()
        print(f"{s.key:30s} {v.index.min()}..{v.index.max()} n={len(v)} last={v.iloc[-1]:.2f}")
