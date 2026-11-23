"""L2 "travel": guest nights, the Easter calendar and the KPIF travel sub-indices.

Travel (package holidays, air fares, accommodation) is ~77 % of the services forecast error (K7).

Sources (all open, no key):
- Guest nights: Eurostat tour_occ_nim (nights spent at tourist accommodation, Sweden, monthly,
  1990-). SCB produced the Swedish accommodation statistics up to and including reference year
  2024; Tillväxtverket took over collection and production from reference year 2025 (possible
  producer break 2024/2025). SCB's own database tables (TAB5295, TAB3162) end 2021-12. Tillväxtverket's statistics portal
  (tillvaxtdata.tillvaxtverket.se) is not reachable from the run environment, so Eurostat is used.
  Total/domestic/foreign start in 2001 (camping included from 2001: a level break), hotels in 1990.
  Domestic nights are total minus foreign: Eurostat lacks the domestic split for 1991-2010
  (except 2001) and DOM + FOR = TOTAL exactly where all three exist.
- Easter: deterministic calendar (Gregorian Easter), the same 11-day travel window as K7
  (Friday before Palm Sunday .. Easter Monday).
- KPIF sub-indices: SCB TAB6613 (KPIF by COICOP 2018, all levels), index 2020=100.

Raw responses are cached under data/raw/l2/<name>_<fetch date>.json; a cached file at most
MAX_AGE_DAYS old is reused (6, so the weekly Sunday job refetches every week); only the newest
KEEP_VERSIONS files per response are kept. With KPIF_OFFLINE=1 the newest cached file is used whatever its age.

Publication lags (days after period end, rounded towards later publication; evidence in
docs/publiceringskalender.md, section "Körning 3: L2"):
- Eurostat guest nights: 80 days. Regulation 692/2011: monthly data transmitted within 6 weeks,
  Eurostat releases 1 day - 1 month after delivery (ESMS 14.1-14.2) -> at most ~73 days. On
  2026-11-23 (dataset updated 2026-11-16) Sweden ended 2026-08; 2026-09 was missing 54 days after
  period end although Tillväxtverket published it on 2026-10-29. The 6-week rule holds from 2020;
  the 1990-2019 backfill rests on SCB having published the same months itself (~t+35). Any lag of
  67-93 days gives exactly t-3 at the deadline. Preliminary until the final annual statistics ->
  revised=True.
- Easter: -366 days. The calendar is known long in advance; a value is stored as known one year
  before its month ends, so horizon forecasts up to 12 months can use it. The warehouse check
  "known_from_after_period_end" allows negative lags. Never revised. The series has a FIXED end
  (EASTER_END): a rolling end would add new periods through a later 'fetch' upsert, dated at the
  fetch date, which the warehouse check flags (known_from earlier than period end - 366).
- TAB6613: 15 days (as the other KPIF tables). History before 2026 is SCB's back-calculation to
  COICOP 2018 -> revised=True.
"""

from __future__ import annotations

import json
import re
import time
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "l2"
MAX_AGE_DAYS = 6
KEEP_VERSIONS = 4
HEADERS = {"User-Agent": "kpif-nowcast research script"}

EUROSTAT_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tour_occ_nim"
SCB_URL = "https://statistikdatabasen.scb.se/api/v2/tables/TAB6613/data"

LAG_NIGHTS, LAG_EASTER, LAG_KPIF = 80, -366, 15
EASTER_START = 2000
EASTER_END = 2050  # fixed: every period is in the first (backfill) load, none arrive later via 'fetch'

NIGHTS_NAME = "eurostat_tour_occ_nim_SE"
KPIF_NAME = "scb_TAB6613_travel"
KPIF_CODES = {  # key -> COICOP 2018 code in TAB6613
    "kpif_package_holidays_index": "09.8",
    "kpif_air_transport_index": "07.3.3",
    "kpif_accommodation_index": "11.2",
}
KPIF_INDEX = "0000083S"


# ------------------------------------------------------------------ cache and HTTP


def _offline() -> bool:
    from kpif_nowcast.sources import rawcache

    return rawcache.offline()


def _cached(name: str, today: date | None = None, max_age: int | None = MAX_AGE_DAYS) -> Path | None:
    """Newest data/raw/l2/<name>_<YYYYMMDD>.json, if at most max_age days old (None: any age)."""
    today = today or date.today()
    pat = re.compile(re.escape(name) + r"_(\d{8})\.json$")
    best = None
    for p in RAW_DIR.glob(f"{name}_*.json"):
        if m := pat.match(p.name):
            got = datetime.strptime(m.group(1), "%Y%m%d").date()
            if (max_age is None or (today - got).days <= max_age) and (best is None or got > best[0]):
                best = (got, p)
    return best[1] if best else None


def _get_json(name: str, url: str, params: dict) -> dict:
    hit = _cached(name, max_age=None if _offline() else MAX_AGE_DAYS)
    if hit is not None:
        return json.loads(hit.read_text(encoding="utf-8"))
    if _offline():
        from kpif_nowcast.sources.rawcache import OfflineError

        raise OfflineError(f"offline: no cached raw file for {name} in {RAW_DIR}")
    import requests

    for k in range(3):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=90)
            if r.status_code == 429 and k < 2:
                time.sleep(20 * (k + 1))
                continue
            r.raise_for_status()
            break
        except Exception:  # noqa: BLE001
            if k == 2:
                raise
            time.sleep(2 ** (k + 1))
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"{name}_{date.today():%Y%m%d}.json").write_text(r.text, encoding="utf-8")
    from kpif_nowcast.sources.rawcache import prune

    prune(RAW_DIR, KEEP_VERSIONS)  # pipeline prune only reads the top level of data/raw
    time.sleep(0.5)
    return r.json()


def _jsonstat_frame(payload: dict) -> pd.DataFrame:
    """Long frame (one column per dimension + value) from a JSON-stat 2.0 dataset."""
    from kpif_nowcast.sources.eurostat import _frame

    return _frame(payload)


# ------------------------------------------------------------------ guest nights (Eurostat)


def nights_frame(payload: dict | None = None) -> pd.DataFrame:
    """Sweden's nights spent, thousands: columns (c_resid, nace_r2) on a monthly PeriodIndex."""
    payload = payload or _get_json(NIGHTS_NAME, EUROSTAT_URL, {"format": "JSON", "lang": "EN", "geo": "SE", "unit": "NR"})
    df = _jsonstat_frame(payload)
    df = df[(df["geo"] == "SE") & (df["unit"] == "NR") & (df["freq"] == "M")]
    wide = df.pivot_table(index="time", columns=["c_resid", "nace_r2"], values="value", aggfunc="first")
    wide.index = pd.PeriodIndex(wide.index, freq="M")
    return wide.sort_index() / 1000.0


def nights(resid: str, nace: str = "I551-I553", start: str | None = None):
    """One guest-night series from `start`; resid 'DOM' is computed as TOTAL - FOR (consistent over the span)."""

    def f() -> pd.Series:
        w = nights_frame()
        if resid == "DOM":
            s = w[("TOTAL", nace)] - w[("FOR", nace)]
        else:
            s = w[(resid, nace)]
        s = s.dropna()
        if start is not None:
            s = s[s.index >= pd.Period(start, "M")]
        return s[s.index < pd.Period(date.today(), "M")]

    return f


# ------------------------------------------------------------------ Easter calendar


def _months(end_year: int | None = None) -> pd.PeriodIndex:
    end_year = end_year or EASTER_END
    return pd.period_range(f"{EASTER_START}-01", f"{end_year}-12", freq="M")


def easter_window_days(end_year: int | None = None) -> pd.Series:
    """Days of the Easter travel window (Easter Sunday -9 .. +1, 11 days) in each month (K7's regressor input)."""
    from kpif_nowcast.k7_services import easter_days

    return easter_days(_months(end_year))


def easter_sunday_in_month(end_year: int | None = None) -> pd.Series:
    """1 in the month of Easter Sunday (March or April), else 0."""
    from kpif_nowcast.j4_detail import easter

    idx = _months(end_year)
    return pd.Series([1.0 if easter(p.year).month == p.month else 0.0 for p in idx], index=idx)


def easter_date(year: int) -> date:
    from kpif_nowcast.j4_detail import easter

    return easter(year)


# ------------------------------------------------------------------ KPIF travel sub-indices (SCB TAB6613)


def kpif_frame(payload: dict | None = None) -> pd.DataFrame:
    """Index per COICOP code (columns) on a monthly PeriodIndex."""
    from kpif_nowcast.sources.scb import to_month_period

    if payload is None:
        codes = {"VaruTjanstegrupp": ",".join(KPIF_CODES.values()), "ContentsCode": KPIF_INDEX, "Tid": "*"}
        params = {"lang": "en", "outputFormat": "json-stat2", **{f"valueCodes[{k}]": v for k, v in codes.items()}}
        payload = _get_json(KPIF_NAME, SCB_URL, params)
    df = _jsonstat_frame(payload)
    df = df[df["ContentsCode"] == KPIF_INDEX]
    wide = df.pivot_table(index="Tid", columns="VaruTjanstegrupp", values="value", aggfunc="first")
    wide.index = to_month_period(wide.index.to_series())
    return wide.sort_index()


def kpif_sub(code: str):
    def f() -> pd.Series:
        s = kpif_frame()[code].dropna()
        return s[s.index < pd.Period(date.today(), "M")]

    return f


# ------------------------------------------------------------------ catalog entries

# I551-I553 jumps from 25.9 to 41.2 million nights a year in 2001 (camping included from then on),
# so those series start in 2001-01. Hotels (I551) have no such break and start in 1990.
NIGHTS = [  # key, residence, NACE, first period, label
    ("guest_nights_total", "TOTAL", "I551-I553", "2001-01", "Gästnätter totalt (hotell, stugbyar, vandrarhem, camping)"),
    ("guest_nights_domestic", "DOM", "I551-I553", "2001-01", "Gästnätter, svenska gäster"),
    ("guest_nights_foreign", "FOR", "I551-I553", "2001-01", "Gästnätter, utländska gäster"),
    ("guest_nights_hotel", "TOTAL", "I551", None, "Gästnätter på hotell"),
]

KPIF_LABELS = {
    "kpif_package_holidays_index": "KPIF paketresor (COICOP 09.8), index",
    "kpif_air_transport_index": "KPIF persontransport med flyg (COICOP 07.3.3), index",
    "kpif_accommodation_index": "KPIF logitjänster (COICOP 11.2), index",
}


def specs() -> list:
    """Catalog entries (lazy import of Spec: catalog.py imports this module)."""
    from kpif_nowcast.catalog import Spec

    out = []
    for key, resid, nace, start, label in NIGHTS:
        note = ("Preliminär till slutlig årsstatistik. SCB t.o.m. 2024, Tillväxtverket från 2025 (möjligt brott). "
                "Tillväxtverket: utländska gästnätter underrapporterade 2024.")
        if resid == "DOM":
            note = "Beräknad som totalt minus utländska (Eurostat saknar svenska 1991–2010). " + note
        out.append(Spec(key, "hushall", label, "tusental", "M", f"Eurostat tour_occ_nim ({resid}, {nace})",
                        nights(resid, nace, start), LAG_NIGHTS, revised=True,
                        link="Efterfrågan på resor och logi; logi och paketresor är en stor del av tjänstefelet.",
                        note=note))
    out += [
        Spec("easter_window_days", "inflation", "Påskens resefönster: dagar i månaden", "dagar", "M",
             "Kalender (gregoriansk påsk)", easter_window_days, LAG_EASTER,
             link="Påskresor höjer priset på paketresor, flyg och logi; K7: ≈ 0,01 pe KPIF per dag.",
             note="Dagar av fönstret påskdagen −9 till +1 (11 dagar) som faller i månaden. Känd i förväg."),
        Spec("easter_sunday_in_month", "inflation", "Påskdagen infaller i månaden", "0/1", "M",
             "Kalender (gregoriansk påsk)", easter_sunday_in_month, LAG_EASTER,
             link="Skiljer tidig påsk (mars) från sen (april).",
             note="1 i påskdagens månad, annars 0. Känd i förväg."),
    ]
    for key, code in KPIF_CODES.items():
        out.append(Spec(key, "inflation", KPIF_LABELS[key], "2020=100", "M", f"SCB TAB6613 ({code})",
                        kpif_sub(code), LAG_KPIF, revised=True,
                        link="Resekomponenterna som står för största delen av tjänstefelet (K7).",
                        note="Historiken före 2026 är SCB:s omräkning till COICOP 2018, därför revised."))
    return out


def keys() -> list[str]:
    return [s.key for s in specs()]


# ------------------------------------------------------------------ quality check


def quality(table: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per series: rows, span, holes, duplicate keys, known_from earlier than period end + lag (lag < 0 allowed)."""
    from kpif_nowcast import observations as obs

    table = obs.load() if table is None else table
    lags = {s.key: s.lag_days for s in specs()}
    rows = {}
    for k in keys():
        t = table[table["series"] == k]
        if t.empty:
            rows[k] = {"rows": 0}
            continue
        per = pd.PeriodIndex(t["period"], freq="M")
        span = pd.period_range(per.min(), per.max(), freq="M")
        floor = (per + 1).to_timestamp() - pd.Timedelta(days=1) + pd.Timedelta(days=min(lags[k], 0))
        rows[k] = {
            "rows": len(t),
            "from": str(per.min()), "to": str(per.max()),
            "holes": len(span) - t["period"].nunique(),
            "dup_keys": int(t.duplicated(["series", "period", "known_from"]).sum()),
            "kf_too_early": int((pd.to_datetime(t["known_from"]).to_numpy() < floor.to_numpy()).sum()),
        }
    return pd.DataFrame(rows).T


if __name__ == "__main__":
    print(quality().to_string())
