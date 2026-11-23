"""Run 3 (L10): Sverigeläget sections for the series added in run 3 and the administered-price calendar.

Every builder takes the observation table and a cutoff date and only uses rows with known_from <= cutoff
(`sverige_dashboard.cut_table`), so the page shows what was known on the cutoff day (default: today). Each row
carries the `known_from` of the value it shows. Descriptive only: no model, no forecast test (that is V2's job).

Datasets (file name = dataset id):
- resor:          guest nights (Swedish / foreign guests, y/y of the 3-month sum), KPIF travel indices (y/y),
                  and the Easter window per year (days in March and April)
- hyror:          negotiated rent increase per year (Hyresgästföreningen) vs KPI rents y/y in December
- prospera:       money-market participants' 5-year inflation expectations, mean and P25-P75
- elmarknad:      contract shares (monthly), grid fees and the share of grid areas that raised them (yearly)
- kronan:         EUR/SEK and USD/SEK, monthly mean and y/y
- snabbkpi:       flash KPIF / KPIF-XE vs the first published outcome
- admin_events:   every event in admin_calendar (L1) with its status today
- admin_yy:       the events' contribution to KPIF y/y per month 2016-2028, by group (one-off level changes
                  count for 12 months; m/m effect taken as y/y effect, factor ~1)
- admin_upcoming: the monthly routine's suggested --adjust for each coming month with an event
- v2_eval:        V2's joint evaluation (docs/auto3/v2/resultat.md) as text blocks, or one row "kommer"
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from kpif_nowcast import observations as obs

ROOT = Path(__file__).resolve().parents[2]
V2_RESULT = ROOT / "docs" / "auto3" / "v2" / "resultat.md"
LATEST = "2100-01-01"

DATASETS = {
    "resor": ("Resor: gästnätter, resepriser och påsken",
              "Gästnätter för svenska och utländska gäster (årsförändring av tremånaderssumman), KPIF-index för "
              "paketresor, flyg och logi (årstakt) och påskens resefönster per år. Värden kända per byggdagen."),
    "hyror": ("Hyror: förhandlat mot KPI",
              "Hyresförhandlingarnas vägda utfall per år (Hyresgästföreningen) mot KPI-hyrornas årsförändring i "
              "december. Värden kända per byggdagen."),
    "prospera": ("Inflationsförväntningar 5 år (Prospera)",
                 "Penningmarknadens förväntade inflation om 5 år: medel och 25:e–75:e percentil, mot målet 2 %."),
    "elmarknad": ("Elmarknaden: avtal och nät",
                  "Andel elavtal per avtalstyp (SCB, månad) och elnätsavgifter 1 januari med andel nätområden som "
                  "höjde (Ei, år). Värden kända per byggdagen."),
    "kronan": ("Kronan", "EUR/SEK och USD/SEK, månadsmedel och årsförändring (Riksbanken)."),
    "snabbkpi": ("Snabb-KPI mot utfall",
                 "SCB:s snabbskattning av KPIF och KPIF-XE mot första publicerade utfall, årstakt och "
                 "månadsförändring, med felet snabb minus utfall."),
    "admin_events": ("Administrerade priser: händelser",
                     "Alla händelser i kalendern för administrerade priser (moms, skatter, avgifter) med effekt på "
                     "KPIF:s månadsförändring, beslutsdatum, källa och status per byggdagen."),
    "admin_yy": ("Administrerade priser: bidrag till årstakten",
                 "Engångshändelsernas bidrag till KPIF:s årstakt per månad 2016–2028, per grupp, i procentenheter. "
                 "Bara händelser beslutade per byggdagen."),
    "admin_upcoming": ("Administrerade priser: kommande justeringar",
                       "Förslag till manuell justering (--adjust) i månadsrutinen för kommande månader med händelser."),
    "v2_eval": ("Gemensam utvärdering (V2)",
                "Körning 3:s förregistrerade screening av de nya serierna (docs/auto3/v2/resultat.md) när den är "
                "klar, annars en rad med status kommer."),
}


def cutoff_today() -> pd.Timestamp:
    return pd.Timestamp.now().normalize()


def _known(table: pd.DataFrame, cutoff) -> pd.DataFrame:
    return table[table["known_from"] <= pd.Timestamp(cutoff)]


def _series(table: pd.DataFrame, key: str) -> tuple[pd.Series, pd.Series]:
    """(values, known_from) of the latest known vintage per period."""
    s = obs.as_of(key, LATEST, table)
    rows = table[table["series"] == key].sort_values("known_from")
    kf = rows.groupby("period")["known_from"].last()
    kf.index = pd.PeriodIndex(kf.index, freq="M") if not isinstance(kf.index, pd.PeriodIndex) else kf.index
    return s, kf.reindex(s.index)


def _kf(kf: pd.Series, p) -> str | None:
    v = kf.get(p) if kf is not None else None
    return None if v is None or pd.isna(v) else str(pd.Timestamp(v).date())


def _yoy(s: pd.Series) -> pd.Series:
    prev = s.reindex(s.index - 12)
    prev.index = s.index
    return (s / prev - 1) * 100


def _monthly(s: pd.Series) -> pd.Series:
    return s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="M")) if len(s) else s


# ------------------------------------------------------------------ resor
TRAVEL_GUESTS = [("guest_nights_domestic", "Svenska gäster"), ("guest_nights_foreign", "Utländska gäster")]
TRAVEL_PRICES = [("kpif_package_holidays_index", "Paketresor"), ("kpif_air_transport_index", "Flyg"),
                 ("kpif_accommodation_index", "Logi")]


def travel_rows(table: pd.DataFrame, cutoff=None, start: str = "2015-01") -> pd.DataFrame:
    t = _known(table, cutoff or cutoff_today())
    rows, p0 = [], pd.Period(start, "M")
    for key, label in TRAVEL_GUESTS:
        s, kf = _series(t, key)
        if s.empty:
            continue
        s3 = _monthly(s).rolling(3, min_periods=3).sum()
        for p, v in _yoy(s3).dropna().items():
            if p >= p0:
                rows.append({"group": "guests", "key": key, "label": label, "period": str(p), "year": p.year,
                             "value": float(v), "display": "årsförändring %, tremånaderssumma",
                             "level": float(s[p]), "known_from": _kf(kf, p)})
    for key, label in TRAVEL_PRICES:
        s, kf = _series(t, key)
        for p, v in _yoy(s).dropna().items():
            if p >= p0:
                rows.append({"group": "prices", "key": key, "label": label, "period": str(p), "year": p.year,
                             "value": float(v), "display": "årstakt %", "level": float(s[p]),
                             "known_from": _kf(kf, p)})
    s, kf = _series(t, "easter_window_days")
    sunday, _ = _series(t, "easter_sunday_in_month")
    for y in sorted({p.year for p in s.index if p.year >= p0.year}):
        mar, apr = pd.Period(f"{y}-03", "M"), pd.Period(f"{y}-04", "M")
        if mar not in s.index or apr not in s.index:
            continue
        month = "mars" if sunday.get(mar, 0) == 1 else "april"
        rows.append({"group": "easter", "key": "easter_window_days", "label": f"Påsk {y}: {month}",
                     "period": str(apr), "year": y, "value": float(s[apr]), "display": "resefönstrets dagar i april",
                     "level": None, "march_days": float(s[mar]), "april_days": float(s[apr]),
                     "known_from": _kf(kf, apr), "easter_month": month})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ hyror
def rent_rows(table: pd.DataFrame, cutoff=None, first_year: int = 2010) -> pd.DataFrame:
    t = _known(table, cutoff or cutoff_today())
    neg, kf_neg = _series(t, "rent_negotiated")
    kpi, kf_kpi = _series(t, "kpi_rent_index")
    yy = _yoy(kpi)
    years = sorted({p.year for p in neg.index} | {p.year for p in yy.dropna().index})
    rows = []
    for y in years:
        if y < first_year:
            continue
        dec = pd.Period(f"{y}-12", "M")
        last = yy.dropna()
        last = last[last.index.year == y]
        kpi_p = dec if dec in last.index else (last.index.max() if len(last) else None)
        rows.append({
            "year": y, "negotiated_pct": float(neg[dec]) if dec in neg.index else None,
            "negotiated_known_from": _kf(kf_neg, dec) if dec in neg.index else None,
            "kpi_rent_yy": float(last[kpi_p]) if kpi_p is not None else None,
            "kpi_period": str(kpi_p) if kpi_p is not None else None,
            "kpi_partial": bool(kpi_p is not None and kpi_p != dec),
            "kpi_known_from": _kf(kf_kpi, kpi_p) if kpi_p is not None else None,
        })
    return pd.DataFrame([r for r in rows if r["negotiated_pct"] is not None or r["kpi_rent_yy"] is not None])


# ------------------------------------------------------------------ prospera
def prospera_rows(table: pd.DataFrame, cutoff=None) -> pd.DataFrame:
    t = _known(table, cutoff or cutoff_today())
    m, kf = _series(t, "prospera_mm_5y_mean")
    lo, _ = _series(t, "prospera_mm_5y_p25")
    hi, _ = _series(t, "prospera_mm_5y_p75")
    rows = [{"period": str(p), "mean": float(v),
             "p25": float(lo[p]) if p in lo.index else None, "p75": float(hi[p]) if p in hi.index else None,
             "target": 2.0, "gap_pp": float(v) - 2.0, "known_from": _kf(kf, p)} for p, v in m.dropna().items()]
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ elmarknad
EL_CONTRACTS = [("el_contract_spot_share", "Rörligt (månad, tim, kvart)"), ("el_contract_hourly_share", "varav tim/kvart"),
                ("el_contract_fixed_share", "Fast pris 1–3 år"), ("el_contract_default_share", "Anvisat (tillsvidare)")]
EL_GRID = [("ei_grid_fee_flat", "Lägenhet 16A, 2 000 kWh", "fee"), ("ei_grid_fee_house", "Villa 16A, 5 000 kWh", "fee"),
           ("ei_grid_fee_house_heat", "Villa elvärme 20A, 20 000 kWh", "fee"),
           ("ei_grid_fee_raise_share", "Andel nätområden som höjde (villa 5 000 kWh)", "raise")]


def el_rows(table: pd.DataFrame, cutoff=None, start: str = "2013-01") -> pd.DataFrame:
    t = _known(table, cutoff or cutoff_today())
    rows = []
    for key, label in EL_CONTRACTS:
        s, kf = _series(t, key)
        for p, v in s.dropna().items():
            if p >= pd.Period(start, "M"):
                rows.append({"group": "contracts", "key": key, "label": label, "period": str(p), "year": p.year,
                             "value": float(v), "unit": "% av avtalen", "yoy_pct": None, "known_from": _kf(kf, p)})
    for key, label, kind in EL_GRID:
        s, kf = _series(t, key)
        yy = _yoy(s)
        for p, v in s.dropna().items():
            if p.year >= 2010:
                rows.append({"group": "grid_" + kind, "key": key, "label": label, "period": str(p), "year": p.year,
                             "value": float(v), "unit": "kr/år exkl. moms" if kind == "fee" else "%",
                             "yoy_pct": None if kind != "fee" or pd.isna(yy.get(p)) else float(yy[p]),
                             "known_from": _kf(kf, p)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ kronan
FX = [("sek_eur", "EUR/SEK"), ("sek_usd", "USD/SEK")]


def fx_rows(table: pd.DataFrame, cutoff=None, start: str = "2010-01") -> pd.DataFrame:
    t = _known(table, cutoff or cutoff_today())
    rows = []
    for key, label in FX:
        s, kf = _series(t, key)
        yy = _yoy(s)
        for p, v in s.dropna().items():
            if p >= pd.Period(start, "M"):
                rows.append({"key": key, "label": label, "period": str(p), "value": float(v),
                             "yoy_pct": None if pd.isna(yy.get(p)) else float(yy[p]), "known_from": _kf(kf, p)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ snabb-KPI
FLASH = {"flash_yy": "kpif_flash_yy", "err_yy": "kpif_flash_err_yy", "flash_mm": "kpif_flash_mm",
         "err_mm": "kpif_flash_err_mm", "xe_flash_yy": "kpif_xe_flash_yy", "xe_err_yy": "kpif_xe_flash_err_yy"}


def flash_rows(table: pd.DataFrame, cutoff=None) -> pd.DataFrame:
    """One row per month. outcome = flash - error (error = flash minus first published outcome, L7)."""
    t = _known(table, cutoff or cutoff_today())
    got = {name: _series(t, key) for name, key in FLASH.items()}
    periods = sorted(set().union(*[set(s.dropna().index) for s, _ in got.values()]))
    rows = []
    for p in periods:
        r = {"period": str(p)}
        for name, (s, _) in got.items():
            r[name] = None if pd.isna(s.get(p)) else float(s[p])
        r["outcome_yy"] = None if r["flash_yy"] is None or r["err_yy"] is None else round(r["flash_yy"] - r["err_yy"], 4)
        r["outcome_mm"] = None if r["flash_mm"] is None or r["err_mm"] is None else round(r["flash_mm"] - r["err_mm"], 4)
        r["xe_outcome_yy"] = (None if r["xe_flash_yy"] is None or r["xe_err_yy"] is None
                              else round(r["xe_flash_yy"] - r["xe_err_yy"], 4))
        r["flash_known_from"] = _kf(got["flash_yy"][1], p)
        r["outcome_known_from"] = _kf(got["err_yy"][1], p)
        rows.append(r)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ administered prices (L1)
ADMIN_GROUPS = {  # COICOP prefix -> (group, label); first match wins
    "07.2.2": ("drivmedel", "Drivmedelsskatter"),
    "04.5.1": ("el", "Energiskatt på el"),
    "01": ("mat", "Matmomsen"),
    "07.3": ("resor", "Kollektivtrafik och flyg"),
}
ADMIN_OTHER = ("ovrigt", "Övrigt (tandvård, avgifter, ROT …)")


def admin_group(coicop: str) -> tuple[str, str]:
    for prefix, g in ADMIN_GROUPS.items():
        if coicop == prefix or coicop.startswith(prefix + "."):
            return g
    return ADMIN_OTHER


def _admin_events(events=None):
    from kpif_nowcast import admin_calendar as ac

    if events is not None:
        return events, None
    parts, index = ac._load_parts_and_index()
    return ac.all_events(parts), index


def decided_by(ev, cutoff) -> bool:
    return ev.decided is not None and pd.Timestamp(ev.decided) <= pd.Timestamp(cutoff)


def admin_event_rows(events=None, cutoff=None) -> pd.DataFrame:
    events, _ = _admin_events(events)
    cutoff = pd.Timestamp(cutoff or cutoff_today())
    now = cutoff.to_period("M")
    rows = []
    for e in events:
        g, gl = admin_group(e.coicop)
        decided = decided_by(e, cutoff)
        rows.append({
            "month": e.month, "coicop": e.coicop, "post": e.post, "group": g, "group_label": gl, "kind": e.kind,
            "pe": e.pe, "suggest_pe": round(e.suggest_pe, 4) if decided else None, "normal_pe": e.normal_pe,
            "method": e.method, "decided": str(e.decided) if e.decided else None,
            "status": "beslutad" if decided else ("ej beslutad" if e.decided is None else "beslutas senare"),
            "upcoming": bool(e.period >= now), "in_ks": e.in_ks, "origin": e.origin, "label": e.label,
            "source": e.source.split()[0] if e.source else None,
        })
    return pd.DataFrame(rows)


def admin_effect(e) -> float:
    """Effect on the level of KPIF from the event month on: pe for one-off/end, the excess over normal for
    recurring events (suggest_pe), 0 when the size is unknown."""
    if e.pe is None:
        return 0.0
    return e.suggest_pe if e.kind == "recurring" else e.pe


def admin_yy_rows(events=None, cutoff=None, start: str = "2016-01", end: str = "2028-12") -> pd.DataFrame:
    """Contribution to KPIF y/y per month and group: sum of effects of events decided by `cutoff` with event
    month in (t-11 .. t). A level change raises the y/y rate for 12 months and drops out in month 13."""
    events, _ = _admin_events(events)
    cutoff = pd.Timestamp(cutoff or cutoff_today())
    now = cutoff.to_period("M")
    used = [e for e in events if decided_by(e, cutoff) and admin_effect(e) != 0.0]
    months = pd.period_range(start, end, freq="M")
    groups = list(dict.fromkeys([g for g, _ in ADMIN_GROUPS.values()] + [ADMIN_OTHER[0]]))
    labels = dict(list(ADMIN_GROUPS.values()) + [ADMIN_OTHER])
    rows = []
    for t in months:
        live = [e for e in used if t - 11 <= e.period <= t]
        total = sum(admin_effect(e) for e in live)
        for g in groups:
            v = sum(admin_effect(e) for e in live if admin_group(e.coicop)[0] == g)
            rows.append({"period": str(t), "group": g, "group_label": labels[g], "pe": round(v, 4),
                         "total_pe": round(total, 4), "future": bool(t > now)})
    return pd.DataFrame(rows)


def admin_upcoming_rows(events=None, index=None, cutoff=None) -> pd.DataFrame:
    """admin_calendar.suggest for every month from the cutoff month with an event, using only events decided by
    the cutoff. adjust_yy is what the monthly routine would pass to forecast.py --adjust."""
    from kpif_nowcast import admin_calendar as ac

    if events is None:
        events, index = _admin_events(None)
    cutoff = pd.Timestamp(cutoff or cutoff_today())
    now = cutoff.to_period("M")
    known_events = [e for e in events if decided_by(e, cutoff)]
    rows = []
    for t in sorted({e.period for e in events if e.period >= now}):
        s = ac.suggest(t, known_events, index)
        undecided = [e for e in events if e.period == t and not decided_by(e, cutoff)]
        rows.append({"month": str(t), "adjust_yy": s.adjust, "mm_pe": round(s.mm_pe, 4),
                     "yy_factor": round(s.yy_factor, 4), "n_used": len(s.used),
                     "n_not_used": len(s.listed) + len(undecided),
                     "events": "; ".join(f"{ac._short(e.label, 60)} {e.suggest_pe:+.3f}" for e in s.used) or None,
                     "deadline": str(ac.deadline(t).date())})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ V2 evaluation
def v2_rows(path: Path | None = None) -> pd.DataFrame:
    """docs/auto3/v2/resultat.md as blocks (heading / paragraph / bullet / table row), or one 'kommer' row.
    Read-only: the file belongs to V2."""
    path = V2_RESULT if path is None else path
    if not path.exists():
        return pd.DataFrame([{"i": 0, "kind": "status", "status": "kommer", "text":
                              "Den gemensamma utvärderingen (V2) pågår. Resultatet visas här när det är klart.",
                              "cells": None, "source": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)}])
    rows, para = [], []
    src = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)

    def add(kind, text, cells=None):
        rows.append({"i": len(rows), "kind": kind, "status": "klar", "text": text, "cells": cells, "source": src})

    def flush():
        if para:
            add("paragraph", " ".join(para))
            para.clear()

    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            flush()
            continue
        if s.startswith("#"):
            flush()
            add("heading", s.lstrip("#").strip())
        elif s.startswith("|"):
            flush()
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            add("table_row", " | ".join(cells), cells)
        elif re.match(r"^([-*]|\d+\.)\s+", s):
            flush()
            add("bullet", re.sub(r"^([-*]|\d+\.)\s+", "", s))
        else:
            para.append(s)
    flush()
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ all
def build_all(table: pd.DataFrame, cutoff=None) -> dict[str, pd.DataFrame]:
    """Every run-3 dataset from the table, as known on `cutoff` (default today)."""
    cutoff = pd.Timestamp(cutoff or cutoff_today())
    events, index = _admin_events(None)
    return {
        "resor": travel_rows(table, cutoff), "hyror": rent_rows(table, cutoff), "prospera": prospera_rows(table, cutoff),
        "elmarknad": el_rows(table, cutoff), "kronan": fx_rows(table, cutoff), "snabbkpi": flash_rows(table, cutoff),
        "admin_events": admin_event_rows(events, cutoff), "admin_yy": admin_yy_rows(events, cutoff),
        "admin_upcoming": admin_upcoming_rows(events, index, cutoff), "v2_eval": v2_rows(),
    }
