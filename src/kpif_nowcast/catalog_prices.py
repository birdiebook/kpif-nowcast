"""K0 "price chain": series close to KPIF, from producer and import prices to the shop shelf.

Sources (all open, no key): SCB PxWebApi v2 (PPI TAB3184, KPIF-XE TAB6593, KPIF goods/services
TAB6627), NIER business survey price plans (PxWeb v1), IMF primary commodity prices via FRED
(fredgraph.csv), Riksbank SWEA (government bond yields) and SWESTR API.

Raw responses are cached under data/raw/k0/<name>_<fetch date>.<ext>. A cached file at most
MAX_AGE_DAYS old is reused instead of downloading again; files that earlier jobs already cached in
data/raw/ (KPIF-XE, two NIER retail series) are reused the same way.

Publication lags (days after period end, rounded towards later publication):
- PPI (TAB3184): September 2026 was published 2026-10-26 (table 'updated' stamp) -> 30 days.
  Preliminary for the latest months and revised afterwards -> revised=True.
- KPIF tables: published ~day 13 of t+1 -> 15 days (same as kpif_index in catalog.py).
- NIER barometer: month m published in the last days of m -> 3 days (same as ki_services).
  Net balances not seasonally adjusted ('O'), so no re-estimated seasonal factors -> revised=False.
- IMF commodity prices via FRED: 60 days (same convention as wheat_usd in catalog.py), revised=True.
- Riksbank yields and SWESTR: monthly mean of daily fixings, complete month only -> 1 day.

Not added (BLOCKED, see docs/auto2/k0/serier.md): Medlingsinstitutet (negotiated wage increases only
in PDF; the PxWeb database sits behind a session proxy), Swedavia (HTTP 403 to scripts), SCB hotel
nights (table ends 2021-12; statistics moved to Tillväxtanalys, outside this track's sources),
Riksbank Prospera (Excel file, not attempted).
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import time
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "k0"
MAIN_RAW = ROOT / "data" / "raw"
MAX_AGE_DAYS = 7
HEADERS = {"User-Agent": "kpif-nowcast research script"}

SCB_URL = "https://statistikdatabasen.scb.se/api/v2/tables/{table}/data"
KONJ_ROOT = "https://statistik.konj.se/PxWeb/api/v1/sv"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
SWEA_URL = "https://api.riksbank.se/swea/v1/Observations/{series}/{start}"
SWESTR_URL = "https://api.riksbank.se/swestr/v1/all/SWESTR"

LAG_PPI, LAG_KPIF, LAG_KI, LAG_IMF, LAG_RB = 30, 15, 3, 60, 1


# ------------------------------------------------------------------ cache and HTTP


def _fresh(*patterns: str, today: date | None = None) -> Path | None:
    """Newest cached file matching any glob pattern (in data/raw/k0 or data/raw) no older than MAX_AGE_DAYS."""
    today = today or date.today()
    best = None
    for d in (RAW_DIR, MAIN_RAW):
        for pat in patterns:
            for p in d.glob(pat):
                m = re.search(r"_(\d{8})\.\w+$", p.name)
                if not m:
                    continue
                got = datetime.strptime(m.group(1), "%Y%m%d").date()
                if (today - got).days <= MAX_AGE_DAYS and (best is None or got > best[0]):
                    best = (got, p)
    return best[1] if best else None


def _request(method: str, url: str, tries: int = 3, pause: float = 0.0, headers: dict | None = None, **kw):
    import requests

    for k in range(tries):
        try:
            r = requests.request(method, url, timeout=60, headers=HEADERS if headers is None else headers, **kw)
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


def _save(name: str, text: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    p = RAW_DIR / f"{name}_{date.today():%Y%m%d}{'.csv' if name.startswith('fred_') else '.json'}"
    p.write_text(text, encoding="utf-8")
    return p


def _tag(obj) -> str:
    return hashlib.md5(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:6]


def _current_month() -> pd.Period:
    return pd.Period(date.today(), "M")


# ------------------------------------------------------------------ SCB


def _scb_payload(table: str, codes: dict[str, str], cache: tuple[str, ...] = ()) -> dict:
    name = f"scb_{table}_{_tag(codes)}"
    hit = _fresh(f"{name}_*.json", *cache)
    if hit is not None:
        return json.loads(hit.read_text(encoding="utf-8"))
    params = {"lang": "en", "outputFormat": "json-stat2", **{f"valueCodes[{k}]": v for k, v in codes.items()}}
    r = _request("GET", SCB_URL.format(table=table), params=params, pause=0.5)
    _save(name, r.text)
    return r.json()


def scb_series(table: str, cache: tuple[str, ...] = (), **codes: str):
    """One SCB series; all non-time dimensions fixed except ContentsCode when the cached file holds several."""

    def f() -> pd.Series:
        from kpif_nowcast.sources.scb import _jsonstat_to_frame, to_month_period

        req = {**codes, "Tid": "*"}
        payload = _scb_payload(table, req if not cache else {"ContentsCode": "*", "Tid": "*"}, cache)
        df = _jsonstat_to_frame(payload)
        for k, v in codes.items():
            df = df[df[k] == v]
        other = [c for c in df.columns if c not in ("Tid", "value")]
        if len(df[other].drop_duplicates()) != 1:
            raise ValueError(f"{table}: {codes} is not exactly one series")
        s = pd.Series(pd.to_numeric(df["value"], errors="coerce").to_numpy(), index=to_month_period(df["Tid"]))
        return s.dropna().sort_index()

    return f


# ------------------------------------------------------------------ NIER (Konjunkturinstitutet)


def _px_series(payload: dict) -> pd.Series:
    from kpif_nowcast.sources.scb import to_month_period

    t = [c["code"] for c in payload["columns"] if c.get("type") == "t"][0]
    cols = [c["code"] for c in payload["columns"] if c.get("type") != "c"]
    ti = cols.index(t)
    vals = {}
    for row in payload["data"]:
        v = row["values"][0]
        vals[row["key"][ti]] = None if v in ("..", ".", "", "-") else float(v)
    s = pd.Series(vals, dtype=float)
    s.index = to_month_period(s.index.to_series())
    return s.dropna().sort_index()


def ki(table: str, branch: str, question: str = "202", serie: str = "O"):
    """NIER firm survey net balance (not seasonally adjusted)."""

    def f() -> pd.Series:
        name = f"konj_{table.replace('.px', '')}_{branch}_{question}_{serie}"
        old = f"konj_{table}_{branch}_{question}_{serie}_*.json"  # name used by features.ki_price_plans
        hit = _fresh(f"{name}_*.json", old)
        if hit is not None:
            payload = json.loads(hit.read_text(encoding="utf-8"))
        else:
            sel = {"Bransch (SNI 2007)": branch, "Fråga": question, "Serie": serie}
            q = {"query": [{"code": k, "selection": {"filter": "item", "values": [v]}} for k, v in sel.items()],
                 "response": {"format": "json"}}
            r = _request("POST", f"{KONJ_ROOT}/KonjBar/ftgmanad/{table}", json=q, pause=0.5)
            _save(name, r.text)
            payload = r.json()
        s = _px_series(payload)
        return s[s.index < _current_month()]

    return f


# ------------------------------------------------------------------ FRED (IMF primary commodity prices)


def fred(series_id: str):
    def f() -> pd.Series:
        name = f"fred_{series_id}"
        hit = _fresh(f"{name}_*.csv")
        text = hit.read_text(encoding="utf-8") if hit is not None else None
        if text is None:
            # FRED stalls requests that carry a custom User-Agent; send the library default
            text = _request("GET", FRED_URL.format(series=series_id), pause=1.0, headers={}).text
            _save(name, text)
        df = pd.read_csv(io.StringIO(text), na_values=".")
        df.columns = ["date", "value"]
        s = pd.Series(df["value"].to_numpy(dtype=float), index=pd.to_datetime(df["date"]).dt.to_period("M"))
        s = s.dropna()
        return s[s.index < _current_month()]

    return f


# ------------------------------------------------------------------ Riksbank


def _monthly_mean(daily: pd.Series) -> pd.Series:
    m = daily.groupby(daily.index.to_period("M")).mean()
    return m[m.index < _current_month()]


def swea(series_id: str, start: str = "1987-01-01"):
    def f() -> pd.Series:
        name = f"riksbank_{series_id}"
        hit = _fresh(f"{name}_*.json")
        if hit is not None:
            payload = json.loads(hit.read_text(encoding="utf-8"))
        else:  # no key: 5 calls/min
            r = _request("GET", SWEA_URL.format(series=series_id, start=start), pause=13.0)
            _save(name, r.text)
            payload = r.json()
        d = pd.Series({pd.Timestamp(o["date"]): float(o["value"]) for o in payload}).sort_index()
        return _monthly_mean(d)

    return f


def swestr() -> pd.Series:
    hit = _fresh("riksbank_SWESTR_*.json")
    if hit is not None:
        payload = json.loads(hit.read_text(encoding="utf-8"))
    else:
        r = _request("GET", SWESTR_URL, params={"fromDate": "2021-09-01"}, pause=13.0)
        _save("riksbank_SWESTR", r.text)
        payload = r.json()
    d = pd.Series({pd.Timestamp(o["date"]): float(o["rate"]) for o in payload}).sort_index()
    return _monthly_mean(d)


# ------------------------------------------------------------------ catalog entries

PPI_TABLE = "TAB3184"
HMPI, IMPI, ITPI = "000001I3", "000001I0", "000004XU"

PPI = [  # key, market code, product group, label
    ("ppi_hmpi_consumer", HMPI, "MIG_COG", "Hemmamarknadspriser, konsumtionsvaror"),
    ("ppi_impi_consumer", IMPI, "MIG_COG", "Importpriser, konsumtionsvaror"),
    ("ppi_itpi_consumer", ITPI, "MIG_COG", "Priser inhemsk tillgång, konsumtionsvaror"),
    ("ppi_itpi_consumer_xfood", ITPI, "MIG_COG_X_FOOD", "Priser inhemsk tillgång, konsumtionsvaror exkl. livsmedel"),
    ("ppi_hmpi_food", HMPI, "10", "Hemmamarknadspriser, livsmedel (SPIN 10)"),
    ("ppi_impi_food", IMPI, "10", "Importpriser, livsmedel (SPIN 10)"),
]

KI = [  # key, table, branch, question, label
    ("ki_prices_grocery", "Barhanm.px", "B4711X", "202", "Prisplaner dagligvaruhandeln (nettotal)"),
    ("ki_prices_durables", "Barhanm.px", "B47XXX", "202", "Prisplaner sällanköpshandeln (nettotal)"),
    ("ki_prices_retail", "Barhanm.px", "BDHAN", "202", "Prisplaner detaljhandeln (nettotal)"),
    ("ki_purchase_prices_grocery", "Barhanm.px", "B4711X", "250", "Inköpspriser dagligvaruhandeln, kommande 3 mån (nettotal)"),
    ("ki_prices_food_industry", "Barindm.px", "BLIVS", "202", "Prisplaner livsmedelsindustrin, hemma (nettotal)"),
    ("ki_prices_consumer_industry", "Barindm.px", "BCONS", "202", "Prisplaner konsumtionsvaruindustrin, hemma (nettotal)"),
]

IMF = [  # key, FRED id, label, unit
    ("coffee_usd", "PCOFFOTMUSDM", "Kaffe (arabica, other mild)", "US-cent/pund"),
    ("cocoa_usd", "PCOCOUSDM", "Kakao", "USD/ton"),
    ("sugar_usd", "PSUGAISAUSDM", "Socker, världsmarknad", "US-cent/pund"),
    ("beef_usd", "PBEEFUSDM", "Nötkött", "US-cent/pund"),
    ("pork_usd", "PPORKUSDM", "Griskött", "US-cent/pund"),
    ("poultry_usd", "PPOULTUSDM", "Fågel", "US-cent/pund"),
    ("palm_oil_usd", "PPOILUSDM", "Palmolja", "USD/ton"),
    ("soy_oil_usd", "PSOILUSDM", "Sojaolja", "USD/ton"),
    ("rapeseed_oil_usd", "PROILUSDM", "Rapsolja", "USD/ton"),
    ("sunflower_oil_usd", "PSUNOUSDM", "Solrosolja", "USD/ton"),
]

RATES = [  # key, SWEA id, label
    ("gvb_2y", "SEGVB2YC", "Statsobligationsränta 2 år"),
    ("gvb_5y", "SEGVB5YC", "Statsobligationsränta 5 år"),
    ("gvb_10y", "SEGVB10YC", "Statsobligationsränta 10 år"),
]


def specs() -> list:
    """Catalog entries (lazy import of Spec: catalog.py imports this module)."""
    from kpif_nowcast.catalog import Spec

    out = []
    for key, market, group, label in PPI:
        out.append(Spec(key, "prisled", label, "2020=100", "M", f"SCB {PPI_TABLE}",
                        scb_series(PPI_TABLE, ContentsCode=market, SPIN2015=group), LAG_PPI, revised=True,
                        link="Producent- och importpriser föregår konsumentpriserna på varor med några månader.",
                        note="Preliminär för senaste månaderna, revideras."))
    xe_cache = ("scb_TAB6593_2*.json",)  # cached by data.build_tax_effects with ContentsCode=*
    out += [
        Spec("kpif_xe_index", "inflation", "KPIF exkl. energi (KPIF-XE), index", "2020=100", "M", "SCB TAB6593",
             scb_series("TAB6593", cache=xe_cache, ContentsCode="000007ZW"), LAG_KPIF,
             link="Underliggande inflation utan energipriser."),
        Spec("kpif_goods_index", "inflation", "KPIF varor, index", "2020=100", "M", "SCB TAB6627",
             scb_series("TAB6627", VaruTjanstegrupp="V", ContentsCode="0000084J"), LAG_KPIF, revised=True,
             link="Varudelen av KPIF, påverkas av import- och producentpriser.",
             note="Indelningen före 2026 är troligen SCB:s omräkning till COICOP 2018, därför revised."),
        Spec("kpif_services_index", "inflation", "KPIF tjänster, index", "2020=100", "M", "SCB TAB6627",
             scb_series("TAB6627", VaruTjanstegrupp="T", ContentsCode="0000084J"), LAG_KPIF, revised=True,
             link="Tjänstedelen av KPIF, driven av löner och hyror.",
             note="Som KPIF varor."),
    ]
    for key, table, branch, q, label in KI:
        out.append(Spec(key, "prisled", label, "nettotal", "M", f"KI Konjunkturbarometern {table}",
                        ki(table, branch, q), LAG_KI,
                        link="Företagens planerade prisändringar kommande 3 månader.",
                        note="Ej säsongsrensad (serie O)."))
    for key, sid, label, unit in IMF:
        out.append(Spec(key, "omvarld", f"{label}, världsmarknadspris", unit, "M", f"IMF via FRED {sid}",
                        fred(sid), LAG_IMF, revised=True,
                        link="Råvarupriser → svenska livsmedelspriser med fördröjning."))
    for key, sid, label in RATES:
        out.append(Spec(key, "penningpolitik", label, "%", "M", f"Riksbanken SWEA {sid}", swea(sid), LAG_RB,
                        link="Marknadens ränteförväntningar och finansiella villkor.",
                        note="Månadsmedel av dagliga noteringar."))
    out.append(Spec("swestr", "penningpolitik", "SWESTR (dagslåneränta)", "%", "M", "Riksbanken SWESTR API", swestr,
                    LAG_RB, link="Kortränta som styrräntan styr; från 2021-09.", note="Månadsmedel."))
    return out


def keys() -> list[str]:
    return [s.key for s in specs()]


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
        end = (per + 1).to_timestamp() - pd.Timedelta(days=1)
        rows[k] = {
            "rows": len(t),
            "from": str(per.min()), "to": str(per.max()),
            "holes": len(span) - latest["period"].nunique(),
            "dup_keys": int(t.duplicated(["series", "period", "known_from"]).sum()),
            "kf_before_end": int((t["known_from"].to_numpy() < end.to_numpy()).sum()),
        }
    return pd.DataFrame(rows).T


if __name__ == "__main__":
    q = quality()
    print(q.to_string())
