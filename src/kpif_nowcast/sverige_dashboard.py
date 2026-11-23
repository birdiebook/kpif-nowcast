"""Export the datasets behind the "Sverigeläget" dashboard (Claude Data).

Run: python -m kpif_nowcast.sverige_dashboard

Reads the versioned observation table (latest vintage of every catalog series) and writes
outputs/sverige/<name>.json as {"rows": [...], "meta": [...]}; meta carries this script's code.

How each series is shown ("display value"):
- levels that trend (prices, indices, wages, counts) -> change vs 12 months earlier, %
- rates, balances, shares and survey indicators -> as published
- AI job ads -> per 10 000 published ads

Inflation pressure: each series gets a sign (+1 = higher value means more inflation pressure,
-1 = less, 0 = not part of the pressure picture). Its z-score over 2005..now times the sign is
its "pressure". An area's pressure is the mean over its series. These are descriptive, not a model.

Link to inflation: correlation between the display value lagged L = 0..12 months and KPIF y/y,
2005..now, monthly (quarterly series on their quarter months). Correlation is not prediction;
the forecast test is a separate step.

v2 (K5) adds: county map data (K4, `region`), Arbetsförmedlingen national (J6, `af`), the AI indicator
(J7 method on the observation table, `ai_indicator`), the price chain (K0, `prisled`), the forecasts for the
target month (committed live forecast, shadows, benchmarks: `forecast`), champion/challenger (`champion`) and
K3's explanation (`explain_summary`, `explain_text`, `explain_components`). The page is
templates/sverige_index.html, copied to outputs/sverige/index.html; outputs/sverige/MANIFEST.json lists
every file to upload (asset + datasets/<id>). A failing v2 section is skipped with a warning.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from kpif_nowcast import observations as obs
from kpif_nowcast.catalog import AREAS, CATALOG

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "sverige"
START = pd.Period("2005-01", "M")
SERIES_START = pd.Period("2010-01", "M")
MAX_LAG = 12

YOY = {
    "brent_sek", "kix", "wage_private_nonmanual", "wage_private_manual_hourly", "vacancies", "aku_employed",
    "house_price_idx", "housing_starts", "bankruptcies", "service_prod_idx", "fao_food_idx", "fao_cereals",
    "fao_dairy", "gas_eu_usd", "wheat_usd", "freight_ppi_deepsea", "gdp_real_q", "hours_worked_q",
    "software_investment_q", "jobads_total", "af_varsel", "af_inskrivna_arbetslosa", "af_oppet_arbetslosa",
    # K0 price chain: indices and world market prices are shown as y/y
    "ppi_hmpi_consumer", "ppi_impi_consumer", "ppi_itpi_consumer", "ppi_itpi_consumer_xfood", "ppi_hmpi_food",
    "ppi_impi_food", "kpif_xe_index", "kpif_goods_index", "kpif_services_index", "coffee_usd", "cocoa_usd",
    "sugar_usd", "beef_usd", "pork_usd", "poultry_usd", "palm_oil_usd", "soy_oil_usd", "rapeseed_oil_usd",
    "sunflower_oil_usd",
}
PER_10K_ADS = {"jobads_ml", "jobads_ai"}
SKIP = {"kpif_index", "kpif_yy", "aku_unemp_sa", "nier_firm_infl_exp_new"}  # target / duplicates / 1 obs

SIGN = {
    "aku_unemp_nsa": -1, "bankruptcies": -1, "hh_saving_rate": -1, "mortgage_rate_new": -1, "policy_rate": -1,
    "lp_hour_yy_se": -1, "lp_hour_yy_ea": 0, "ai_use_firms_se": 0, "ai_use_firms_eu": 0, "jobads_ml": 0,
    "jobads_ai": 0, "software_investment_q": 0, "gdp_real_q": 0, "hours_worked_q": 0,
    "af_varsel": -1, "af_inskrivna_arbetslosa": -1, "af_oppet_arbetslosa": -1,
    "gvb_2y": -1, "gvb_5y": -1, "gvb_10y": -1, "swestr": -1,
}  # every other series: +1


def display_value(key: str, s: pd.Series, table: pd.DataFrame) -> pd.Series:
    if key in YOY:
        return (s / s.shift(12) - 1) * 100 if s.index.freqstr == "M" else _yoy_sparse(s)
    if key in PER_10K_ADS:
        total = obs.as_of("jobads_total", "2100-01-01", table)
        return (s / total * 10_000).dropna()
    return s


def _yoy_sparse(s: pd.Series) -> pd.Series:
    """y/y for series stored on quarter/year months: compare with the same month a year earlier."""
    prev = s.reindex(s.index - 12)
    prev.index = s.index
    return ((s / prev - 1) * 100).dropna()


def _clean(v):
    if v is None:
        return None
    if isinstance(v, pd.Period):
        return str(v)
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float):
        return None if not math.isfinite(v) else round(v, 4)
    return v


WRITTEN: dict[str, tuple[str, str]] = {}  # name -> (title, description) of every file written this run


def _write(name: str, df: pd.DataFrame, note: str, title: str = "", source: str | None = None,
           out_dir: Path | None = None) -> None:
    out_dir = OUT_DIR if out_dir is None else out_dir
    code = Path(__file__).read_text(encoding="utf-8")
    src = "data/observations.parquet (latest vintage per series), " if source is None else source + ", "
    payload = {
        "rows": [{k: _clean(v) for k, v in r.items()} for r in df.to_dict(orient="records")],
        "meta": [
            {"label": "sverige_dashboard.py", "value": code, "type": "code", "lang": "python"},
            {"label": "Input", "value": src + note},
            {"label": "Exported", "value": datetime.now().isoformat(timespec="seconds")},
            {"label": "Repository", "value": "https://github.com/birdiebook/kpif-nowcast"},
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    WRITTEN[name] = (title or name, note)
    try:
        shown = path.relative_to(ROOT)
    except ValueError:
        shown = path
    print(f"  {shown}: {len(df)} rows, {path.stat().st_size // 1024} KB")


def best_lead(x: pd.Series, kpif: pd.Series) -> tuple[float, int, int]:
    """Correlation with KPIF y/y at the lag (0..12 months) with the largest |r|; returns (r, lag, n)."""
    best = (np.nan, 0, 0)
    for lag in range(MAX_LAG + 1):
        shifted = x.copy()
        shifted.index = shifted.index + lag
        pair = pd.concat([shifted, kpif], axis=1, join="inner").dropna()
        pair = pair[pair.index >= START]
        if len(pair) < 24:
            continue
        r = float(pair.iloc[:, 0].corr(pair.iloc[:, 1]))
        if np.isnan(best[0]) or abs(r) > abs(best[0]):
            best = (r, lag, len(pair))
    return best


def v1_datasets(table: pd.DataFrame, out_dir: Path | None = None) -> pd.DataFrame:
    """v1 datasets (overview, series, pressure, ai), method unchanged. Returns the overview frame."""
    kpif = obs.as_of("kpif_yy", LATEST, table)
    overview, long_rows, pressure_cols = [], [], {}

    for spec in CATALOG:
        if spec.key in SKIP:
            continue
        raw = obs.as_of(spec.key, LATEST, table)
        if raw.empty:
            continue
        dv = display_value(spec.key, raw, table).dropna()
        if dv.empty:
            continue
        hist = dv[dv.index >= START]
        mu, sd = hist.mean(), hist.std()
        z = (dv - mu) / sd if sd and sd > 0 else dv * np.nan
        sign = SIGN.get(spec.key, 1)
        r, lag, n = best_lead(dv, kpif) if spec.freq != "A" else (np.nan, 0, 0)
        last_p = dv.index.max()
        prev = dv[dv.index <= last_p - 12]
        overview.append({
            "key": spec.key, "area": spec.area, "area_label": AREAS[spec.area], "label": spec.label,
            "display": "årsförändring %" if spec.key in YOY else ("per 10 000 annonser" if spec.key in PER_10K_ADS else spec.unit),
            "freq": spec.freq, "source": spec.source, "link": spec.link,
            "period": str(last_p), "value": float(dv.iloc[-1]),
            "value_12m_ago": float(prev.iloc[-1]) if len(prev) else None,
            "z": float(z.iloc[-1]), "pressure": float(z.iloc[-1] * sign) if sign else None, "sign": sign,
            "corr_kpif": r, "corr_lead_months": lag, "corr_n": n,
            "revised": spec.revised,
        })
        for p, v in dv[dv.index >= SERIES_START].items():
            long_rows.append({"key": spec.key, "period": str(p), "value": float(v),
                              "z": float(z.get(p)) if pd.notna(z.get(p)) else None})
        if sign and spec.freq in ("M", "Q"):
            zz = (z * sign)
            if spec.freq == "Q":  # spread a quarter over its three months for the area average
                zz = zz.reindex(pd.period_range(zz.index.min() - 2, zz.index.max(), freq="M")).bfill(limit=2)
            pressure_cols.setdefault(spec.area, []).append(zz.rename(spec.key))

    ov = pd.DataFrame(overview)
    _write("overview", ov, "one row per series: latest value, z-score, pressure sign, correlation with KPIF",
           out_dir=out_dir)
    _write("series", pd.DataFrame(long_rows), f"display values from {SERIES_START}, long format", out_dir=out_dir)

    area_rows = []
    for area, cols in pressure_cols.items():
        m = pd.concat(cols, axis=1)
        avg = m.mean(axis=1).where(m.notna().sum(axis=1) >= max(1, len(cols) // 3))
        for p, v in avg[avg.index >= SERIES_START].items():
            if pd.notna(v):
                area_rows.append({"area": area, "area_label": AREAS[area], "period": str(p), "pressure": float(v),
                                  "n_series": int(m.loc[p].notna().sum())})
    for p, v in kpif[kpif.index >= SERIES_START].items():
        area_rows.append({"area": "kpif", "area_label": "KPIF, årstakt", "period": str(p), "pressure": float(v),
                          "n_series": 1})
    _write("pressure", pd.DataFrame(area_rows), "area pressure = mean of signed z-scores; plus KPIF y/y",
           out_dir=out_dir)

    # AI and productivity story, one tidy table
    ai_keys = ["lp_hour_yy_se", "lp_hour_yy_ea", "ai_use_firms_se", "ai_use_firms_eu", "jobads_ml", "jobads_ai",
               "software_investment_q"]
    ai = [r for r in long_rows if r["key"] in ai_keys]
    for k in ["ai_use_firms_se", "ai_use_firms_eu"]:  # annual: whole history
        s = obs.as_of(k, LATEST, table)
        ai = [r for r in ai if r["key"] != k] + [{"key": k, "period": str(p), "value": float(v), "z": None}
                                                 for p, v in s.items()]
    _write("ai", pd.DataFrame(ai), "AI and productivity series", out_dir=out_dir)
    return ov


# ------------------------------------------------------------------ v2 (K5): new sections
#
# Every builder takes the observation table as an argument. The monthly letter (manadsbrev.py) passes a table
# cut at its information date (rows with known_from <= cutoff), so the same code gives the picture as it was
# known then; the dashboard passes the whole table.

LATEST = "2100-01-01"

DATASETS = {  # file name -> (title, description) for MANIFEST.json and the dashboard's datasets/<id>
    "overview": ("Alla serier: läge och samband",
                 "En rad per serie i datakatalogen: senaste värde, tryck mot inflationen och korrelation med KPIF."),
    "series": ("Serier över tid",
               "Varje series visade värde per månad sedan 2010 (årsförändring eller nivå), med z-värde."),
    "pressure": ("Inflationstryck per område",
                 "Områdets snitt av seriernas tecknade z-värden per månad sedan 2010, plus KPIF:s årstakt (area = kpif)."),
    "ai": ("AI och produktivitet",
           "Produktivitet Sverige och euroområdet, AI-användning i företag, AI i platsannonser och programvaruinvesteringar."),
    "region": ("Län: senaste läget",
               "Senaste värde och förändring på ett år per län för arbetslöshet (AF och AKU), småhuspriser, "
               "konkurser per 10 000 invånare och varsel. AKU-län som ligger efter riket är borttagna. "
               "Varsel per län finns bara till och med 2026-03."),
    "af": ("Arbetsförmedlingen, riket",
           "Inskrivna arbetslösa, öppet arbetslösa och varsel per månad sedan 2010, med tremånadersmedel och årsförändring."),
    "ai_indicator": ("AI-indikatorn (J7)",
                     "Årsvis: maskininlärning och AI i platsannonser per 10 000 annonser, företagens AI-användning, "
                     "och indikatorn (snitt av z-värden), med J7:s metod på observationstabellens data."),
    "prisled": ("Prisleden",
                "KPIF och delar, producent- och importpriser, KI:s prisplaner, råvarupriser och räntor per månad sedan 2015."),
    "forecast": ("Prognoser för månaden",
                 "Skarp prognos (committad), skuggprognoser (urvalsevidens) och jämförelser för samma målmånad."),
    "champion": ("Champion/challenger",
                 "Medelabsolutfel per modell: 2015–26 (urvalsevidens), 2024–26 (använd period) och live."),
    "explain_summary": ("Förklaringen: nyckeltal",
                        "K3:s förklaring av prognosen för målmånaden: prognos, senaste utfall, osäkerhetsband (J5) "
                        "och informationsmängd. En rad."),
    "explain_text": ("Förklaringen: text", "K3:s förklaring i meningar, huvudbudskapet först."),
    "explain_components": ("Förklaringen: bidrag per komponent",
                           "Prognosens månadsförändring per KPIF-komponent (trend, säsong, el, drivmedel) och bidraget "
                           "till förändringen i årstakt mot förra utfallet, i procentenheter."),
}

PRISLED_GROUPS = {
    "kpi": "KPIF och delar, årstakt %",
    "ppi": "Producent- och importpriser, konsumtionsvaror, årsförändring %",
    "ppi_food": "Producent- och importpriser, livsmedel, årsförändring %",
    "ki": "Företagens prisplaner kommande 3 mån (KI, nettotal)",
    "raw": "Råvarupriser i USD, årsförändring %",
    "rates": "Räntor, %",
}
PRISLED = [  # key, group, short label, "yoy" (change vs 12 months earlier, %) or "level"
    ("kpif_yy", "kpi", "KPIF", "level"),
    ("kpif_xe_index", "kpi", "KPIF-XE (exkl. energi)", "yoy"),
    ("kpif_goods_index", "kpi", "Varor", "yoy"),
    ("kpif_services_index", "kpi", "Tjänster", "yoy"),
    ("ppi_itpi_consumer", "ppi", "Inhemsk tillgång", "yoy"),
    ("ppi_hmpi_consumer", "ppi", "Hemmamarknad", "yoy"),
    ("ppi_impi_consumer", "ppi", "Import", "yoy"),
    ("ppi_hmpi_food", "ppi_food", "Hemmamarknad", "yoy"),
    ("ppi_impi_food", "ppi_food", "Import", "yoy"),
    ("ki_prices_grocery", "ki", "Dagligvaruhandeln", "level"),
    ("ki_purchase_prices_grocery", "ki", "Inköpspriser dagligvaror", "level"),
    ("ki_prices_food_industry", "ki", "Livsmedelsindustrin", "level"),
    ("ki_prices_durables", "ki", "Sällanköpshandeln", "level"),
    ("ki_services", "ki", "Tjänstesektorn", "level"),
    ("fao_food_idx", "raw", "FAO livsmedel", "yoy"),
    ("coffee_usd", "raw", "Kaffe", "yoy"),
    ("cocoa_usd", "raw", "Kakao", "yoy"),
    ("beef_usd", "raw", "Nötkött", "yoy"),
    ("sugar_usd", "raw", "Socker", "yoy"),
    ("policy_rate", "rates", "Styrränta", "level"),
    ("swestr", "rates", "SWESTR", "level"),
    ("gvb_2y", "rates", "Statsobligation 2 år", "level"),
    ("gvb_10y", "rates", "Statsobligation 10 år", "level"),
    ("mortgage_rate_new", "rates", "Bolåneränta, nya avtal", "level"),
]

AF_KEYS = [("af_inskrivna_arbetslosa", "Inskrivna arbetslösa"), ("af_oppet_arbetslosa", "Öppet arbetslösa"),
           ("af_varsel", "Varsel, personer")]

REGION_MEASURES = {  # measure -> short label for the map's selector
    "af_andel": "Arbetslöshet, inskrivna på AF (% av arbetskraften)",
    "aku_arbetsloshet": "Arbetslöshet enligt AKU (%, kvartal)",
    "smahus_pris": "Småhuspriser, medelpris (tkr, kvartal)",
    "konkurser_per_10k": "Konkurser senaste 12 mån per 10 000 invånare",
    "af_varsel": "Varsel, personer (bara t.o.m. 2026-03)",
}

SHADOW_LABELS = {
    "comp_fuel_el": "Skarpa modellen körd med dagens data",
    "j2_el_dev": "J2 V2: el som avvikelse från säsongen",
    "j1_comb_equal": "J1 C1: 50/50 Riksbanken uppdaterad och J2",
}


def cut_table(table: pd.DataFrame, cutoff: pd.Timestamp | str | None) -> pd.DataFrame:
    """Rows known on `cutoff` (known_from <= cutoff); None = the whole table."""
    if cutoff is None:
        return table
    return table[table["known_from"] <= pd.Timestamp(cutoff)]


def prisled_rows(table: pd.DataFrame, start: str = "2015-01") -> pd.DataFrame:
    from kpif_nowcast.catalog import by_key

    specs = by_key()
    rows = []
    for key, group, label, how in PRISLED:
        s = obs.as_of(key, LATEST, table)
        if s.empty:
            continue
        v = (_yoy_sparse(s) if how == "yoy" else s).dropna()
        unit = "årsförändring %" if how == "yoy" else specs[key].unit
        for p, x in v[v.index >= pd.Period(start, "M")].items():
            rows.append({"key": key, "group": group, "group_label": PRISLED_GROUPS[group], "label": label,
                         "display": unit, "period": str(p), "value": float(x)})
    return pd.DataFrame(rows)


def af_rows(table: pd.DataFrame, start: str = "2010-01") -> pd.DataFrame:
    rows = []
    for key, label in AF_KEYS:
        s = obs.as_of(key, LATEST, table)
        if s.empty:
            continue
        s = s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="M"))
        m3 = s.rolling(3, min_periods=3).mean()
        yoy = (s / s.shift(12) - 1) * 100
        for p in s.index[s.index >= pd.Period(start, "M")]:
            if pd.isna(s[p]):
                continue
            rows.append({"key": key, "label": label, "period": str(p), "value": float(s[p]),
                         "value_3m": None if pd.isna(m3[p]) else float(m3[p]),
                         "yoy_pct": None if pd.isna(yoy[p]) else float(yoy[p])})
    return pd.DataFrame(rows)


def region_rows(table: pd.DataFrame) -> pd.DataFrame:
    """K4's latest_by_county for the map's measures; county rows older than the national period are dropped
    (in practice LFS cells SCB suppressed in the latest quarter)."""
    from kpif_nowcast import catalog_region as cr

    out = []
    for r in cr.latest_by_county(table):
        if r["measure"] not in REGION_MEASURES or r.get("behind_national"):
            continue
        r = dict(r)
        tile = r.pop("tile") or [None, None]
        r["tile_col"], r["tile_row"] = tile
        r["map_label"] = REGION_MEASURES[r["measure"]]
        out.append(r)
    return pd.DataFrame(out)


def ai_indicator_rows(table: pd.DataFrame, first_year: int = 2016) -> pd.DataFrame:
    """J7's indicator (docs/ai-indikator.md) recomputed from the observation table: yearly ads mentioning
    "maskininlärning" per 10 000 ads (main series) and firms' AI use in Sweden, z-scores from 2017, mean.
    Only complete years enter the indicator; the current year's ad share is shown with partial = True."""
    ads = {k: obs.as_of(k, LATEST, table) for k in ["jobads_ml", "jobads_ai", "jobads_total"]}
    if any(s.empty for s in ads.values()):
        return pd.DataFrame()
    df = pd.DataFrame(ads).dropna()
    df["year"] = df.index.year
    g = df.groupby("year")
    yearly = g[["jobads_ml", "jobads_ai", "jobads_total"]].sum()
    months = g.size()
    share = yearly[["jobads_ml", "jobads_ai"]].div(yearly["jobads_total"], axis=0) * 1e4
    full = months[months == 12].index
    use = {grp: obs.as_of(k, LATEST, table) for grp, k in [("SE", "ai_use_firms_se"), ("EU27", "ai_use_firms_eu")]}
    use = {grp: pd.Series(s.to_numpy(), index=s.index.year) for grp, s in use.items()}
    ind = pd.DataFrame({"ad_share": share.loc[full, "jobads_ml"]})
    ind["firm_use_se"] = use["SE"].reindex(ind.index)
    zs = ind.loc[2017:].apply(lambda s: (s - s.mean()) / s.std())
    indicator = zs.mean(axis=1, skipna=True)
    rows = []
    for y in share.index[share.index >= first_year]:
        for col, grp in [("jobads_ml", "maskininlärning"), ("jobads_ai", "AI")]:
            rows.append({"series": "ad_share_per_10k", "group": grp, "year": int(y), "value": float(share.loc[y, col]),
                         "partial": bool(y not in full), "months": int(months[y])})
    for grp, s in use.items():
        for y, v in s.dropna().items():
            rows.append({"series": "firm_ai_use_pct", "group": grp, "year": int(y), "value": float(v),
                         "partial": False, "months": 12})
    for y, v in indicator.dropna().items():
        rows.append({"series": "ai_diffusion_indicator_z", "group": "SE", "year": int(y), "value": float(v),
                     "partial": False, "months": 12})
    return pd.DataFrame(rows)


def _made_at(rec: dict) -> pd.Timestamp | None:
    t = rec.get("made_at") or (rec.get("run") or {}).get("made_at")
    return pd.Timestamp(t) if t else None


def forecast_files(target: pd.Period, cutoff: pd.Timestamp | None = None) -> tuple[dict | None, dict[str, dict]]:
    """The committed live forecast and the shadow forecasts for `target`, only those made by `cutoff`."""
    from kpif_nowcast.forecast import FORECAST_DIR
    from kpif_nowcast.shadow import SHADOW_DIR

    def ok(rec: dict) -> bool:
        t = _made_at(rec)
        return cutoff is None or (t is not None and t <= pd.Timestamp(cutoff))

    live = None
    p = FORECAST_DIR / f"{target}.json"
    if p.exists():
        rec = json.loads(p.read_text(encoding="utf-8"))
        live = rec if ok(rec) else None
    shadows = {}
    if SHADOW_DIR.exists():
        for d in sorted(SHADOW_DIR.iterdir()):
            f = d / f"{target}.json"
            if f.exists():
                rec = json.loads(f.read_text(encoding="utf-8"))
                if ok(rec):
                    shadows[d.name] = rec
    return live, shadows


def forecast_rows(target: pd.Period, expl: dict | None = None, cutoff: pd.Timestamp | None = None) -> pd.DataFrame:
    """One row per forecast of `target`. kind: skarp | skugga | kandidat | jämförelse. Shadows and the K2
    candidate are selection evidence only (models chosen on 2015-26); 'skarp' is the committed forecast file."""
    from kpif_nowcast.shadow import CHAMPION

    live, shadows = forecast_files(target, cutoff)
    rows = []
    if live:
        r50, r80 = live.get("range_50") or [None, None], live.get("range_80") or [None, None]
        rows.append({"model": "skarp", "label": f"Skarp prognos ({live.get('model')})", "kind": "skarp",
                     "evidence": "skarp, committad före utfallet", "forecast_yy": live["forecast_yy"],
                     "lo50": r50[0], "hi50": r50[1], "lo80": r80[0], "hi80": r80[1],
                     "status": live.get("status"), "made_at": live.get("made_at"),
                     "adjustment_pp": live.get("manual_adjustment_pp")})
    for name, rec in shadows.items():
        rows.append({"model": name, "label": SHADOW_LABELS.get(name, rec.get("description", name)),
                     "kind": "skugga", "evidence": "skugga, urvalsevidens" + (" (champion)" if name == CHAMPION else ""),
                     "forecast_yy": rec["forecast_yy"], "status": rec.get("status"),
                     "made_at": (rec.get("run") or {}).get("made_at")})
    sh = (expl or {}).get("shadows") or {}
    if "k2_avg_ens_s" in sh:
        rows.append({"model": "k2_avg_ens_s", "label": "K2-kandidat: 50/50 + ridge/boosting", "kind": "kandidat",
                     "evidence": "skugga, urvalsevidens (inte registrerad i forecasts/shadow)",
                     "forecast_yy": round(sh["k2_avg_ens_s"]["forecast_yy"], 2)})
    if "rb_updated" in sh:
        rb = sh["rb_updated"]
        rows.append({"model": "rb_updated", "label": "Riksbanken uppdaterad med senaste miss", "kind": "jämförelse",
                     "evidence": "jämförelse", "forecast_yy": rb["forecast_yy"]})
        rows.append({"model": "riksbank", "label": f"Riksbankens prognos ({rb.get('policy_round')})",
                     "kind": "jämförelse", "evidence": "jämförelse", "forecast_yy": rb["riksbank_yy"]})
    df = pd.DataFrame(rows)
    if len(df):
        df.insert(0, "target_month", str(target))
    return df


def champion_rows(inp) -> pd.DataFrame:
    from kpif_nowcast import champion

    df, meta = champion.table(inp)
    df = df.reset_index(names="model").rename(columns={
        "Roll": "role", "MAE 2015–26 (urval)": "mae_2015_26", "MAE 2024–26 (använd)": "mae_2024_26",
        "MAE live": "mae_live", "Första backtestmånad": "first_month"})
    for k in ["n_long", "n_used", "n_live", "first_long", "first_used", "last"]:
        df[k] = meta[k]
    return df


def explanation(inp, info: dict, target: pd.Period | None = None, with_k2: bool = True) -> dict:
    """K3's explanation of `target` (default: the next unpublished month) without the outcome part."""
    from kpif_nowcast import explain as ex

    h = ex.build_history(inp)
    target = info["target"] if target is None else target
    k2 = {}
    if with_k2:
        try:
            k2 = ex.k2_explain(inp, [target])
        except Exception as exc:  # noqa: BLE001 - optional, like in explain.run
            print(f"  K2 explanation skipped: {exc!r}")
    return ex.explain_month(h, target, k2.get(str(target)), info if target == info["target"] else None)


def explain_frames(e: dict) -> dict[str, pd.DataFrame]:
    from kpif_nowcast.explain import NAME_SV

    u = e.get("uncertainty") or {}
    b = {k: (u.get(k) or [None, None]) for k in ["band_50", "band_80", "band_90"]}
    f, i = e["forecast"], e["information_set"]
    summary = pd.DataFrame([{
        "target_month": e["target_month"], "deadline": e["deadline"], "model": e["model"],
        "forecast_yy": f["yy"], "forecast_mm_pp": f["mm_pp"], "last_known_month": f["last_known_month"],
        "last_known_yy": f["last_known_yy"], "change_yy": f["change_yy"],
        "lo50": b["band_50"][0], "hi50": b["band_50"][1], "lo80": b["band_80"][0], "hi80": b["band_80"][1],
        "lo90": b["band_90"][0], "hi90": b["band_90"][1], "band_method": u.get("method"), "band_n": u.get("n_past"),
        "kpif_through": i.get("kpif_through"), "energy_prices_for": i.get("energy_prices_for"),
        "riksbank_vintage": i.get("riksbank_vintage"),
        "el_days": (e.get("inputs") or {}).get("el_days"), "fuel_last_day": (e.get("inputs") or {}).get("fuel_last_day"),
    }])
    text = pd.DataFrame([{"i": n, "text": t} for n, t in enumerate(e["text"])])
    comps = []
    for c, p in e["components"].items():
        comps.append({"component": c, "name": NAME_SV.get(c, c), "mm_pp": p["mm_pp"], "trend_pp": p["trend_pp"],
                      "season_pp": p["season_pp"], "el_pp": p.get("el_pp", 0.0), "fuel_pp": p.get("fuel_pp", 0.0),
                      "same_month_last_year_pp": p["same_month_last_year_pp"], "change_yy": p["change_yy"]})
    comps.append({"component": "rest", "name": "avrundning", "mm_pp": None, "trend_pp": None, "season_pp": None,
                  "el_pp": None, "fuel_pp": None, "same_month_last_year_pp": None, "change_yy": e["change_rest_yy"]})
    return {"explain_summary": summary, "explain_text": text, "explain_components": pd.DataFrame(comps)}


TEMPLATE = Path(__file__).with_name("templates") / "sverige_index.html"


def write_page_and_manifest(out_dir: Path | None = None) -> Path:
    import shutil

    out_dir = OUT_DIR if out_dir is None else out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, out_dir / "index.html")
    files = [{"file": "index.html", "kind": "page",
              "description": "Sidan (dashboardens files/index.html). Läser dataseten med dash.data(<dataset_id>)."}]
    for name in WRITTEN:
        title, desc = DATASETS.get(name, (name, WRITTEN[name][1]))
        files.append({"file": f"{name}.json", "kind": "dataset", "dataset_id": name, "title": title,
                      "description": desc, "format": "json"})
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "generator": "python -m kpif_nowcast.sverige_dashboard",
        "how_the_page_reads_data": "index.html has no fetch or relative paths: every dataset is read with "
                                   "dash.data('<dataset_id>'), so each JSON file is uploaded as an asset and "
                                   "registered as datasets/<dataset_id> with source {kind: 'file', format: 'json', "
                                   "name: '<file>', url: '/_blob/<asset id>'}.",
        "files": files,
    }
    path = out_dir / "MANIFEST.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  {path}: {len(files)} files")
    return path


def main(out_dir: Path | None = None, with_k2: bool = True) -> list[str]:
    """Write every dataset, index.html and MANIFEST.json. Returns the v2 sections that failed (non-fatal)."""
    WRITTEN.clear()
    table = obs.load()
    ov = v1_datasets(table, out_dir)
    failed = []

    def step(name: str, fn) -> None:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - one section must not stop the rest
            failed.append(name)
            print(f"  {name} skipped: {type(exc).__name__}: {exc}")

    step("prisled", lambda: _write("prisled", prisled_rows(table), "price chain (K0), from 2015", out_dir=out_dir))
    step("af", lambda: _write("af", af_rows(table), "Arbetsförmedlingen (J6), national, from 2010", out_dir=out_dir))
    step("region", lambda: _write("region", region_rows(table), "catalog_region.latest_by_county (K4)", out_dir=out_dir))
    step("ai_indicator", lambda: _write("ai_indicator", ai_indicator_rows(table),
                                        "J7 method on the observation table (docs/ai-indikator.md)", out_dir=out_dir))

    def forecast_part() -> None:
        from kpif_nowcast.shadow import load_inputs

        inp, info = load_inputs()
        e = explanation(inp, info, with_k2=with_k2)
        src = "forecasts/<month>.json, forecasts/shadow/, data/processed (shadow.load_inputs)"
        _write("forecast", forecast_rows(info["target"], e), "live, shadow and benchmark forecasts", source=src,
               out_dir=out_dir)
        for name, df in explain_frames(e).items():
            _write(name, df, "K3 explanation (explain.explain_month), forecast part only", source=src, out_dir=out_dir)
        step("champion", lambda: _write("champion", champion_rows(inp), "champion.table (as in SCORECARD.md)",
                                        source=src, out_dir=out_dir))

    step("forecast", forecast_part)
    write_page_and_manifest(out_dir)

    print("\nTop pressure now:")
    print(ov.dropna(subset=["pressure"]).sort_values("pressure", ascending=False)[["key", "period", "value", "pressure"]]
          .head(8).round(2).to_string(index=False))
    if failed:
        print(f"\nWARNING: sections skipped: {failed}")
    return failed


if __name__ == "__main__":
    main()
