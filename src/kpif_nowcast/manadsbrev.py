"""K5: the monthly letter (månadsbrev) - the situation in Sweden seen through KPIF, and the forecast.

Run: python -m kpif_nowcast.manadsbrev 2026-11 [--today YYYY-MM-DD] [--no-k2] [--stdout]
Writes docs/manadsbrev/<month>.md (committed).

<month> is the forecast's target month. Information date (cutoff) = the earlier of today (end of day) and
the target month's deadline (end of day 4 of the next month, riksbank_benchmark.deadline). Everything in the
letter is restricted to what was known then:
- observation table: rows with known_from <= cutoff (sverige_dashboard.cut_table), so the latest values
  and every comparison are the vintages known on that date;
- forecast files (forecasts/<month>.json, forecasts/shadow/*/<month>.json): only if made_at <= cutoff;
- processed data behind the K3 explanation and champion/challenger: KPIF and components to month-1,
  energy prices for the month, Riksbank forecasts published before the cutoff and the deadline (the same cut
  as tests/test_explain.py). The outcome part of the explanation is never used.
"What changed" compares the picture at the cutoff with the picture at the previous month's cutoff.

L9: "Beslutade engångshändelser" shows the administered-price calendar's suggestion (admin_calendar) for the
target month, and "Förhandsvisning" the suggestion for the next month. Both use only events decided before the
target's deadline and on or before the cutoff (admin_calendar.known_at); realised KS parts behind K13's end
events and the KPIF index behind the y/y factor are cut to month-1, like the explanation. Both are proposals:
Johannes decides on any --adjust, and a recorded decision is shown when it was made by the cutoff.

Descriptive text only: levels, changes and rankings, no causal claims. Shadows and the K2 candidate are
labelled as selection evidence. No personal data.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from kpif_nowcast import observations as obs
from kpif_nowcast import sverige_dashboard as sd
from kpif_nowcast.explain import month_sv, num
from kpif_nowcast.riksbank_benchmark import deadline

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "docs" / "manadsbrev"


def cutoff_for(month: pd.Period, today: pd.Timestamp | str | None = None) -> pd.Timestamp:
    end_of_deadline = deadline(month) + pd.Timedelta(hours=23, minutes=59, seconds=59)
    today = pd.Timestamp.now().normalize() if today is None else pd.Timestamp(today).normalize()
    return min(end_of_deadline, today + pd.Timedelta(hours=23, minutes=59, seconds=59))


def cut_inputs(inp, month: pd.Period, cutoff: pd.Timestamp):
    """What the forecast for `month` could use at `cutoff` (outcomes to month-1, energy prices for month)."""
    from kpif_nowcast.shadow import Inputs

    rb = inp.rb_fc[(inp.rb_fc["published"] < deadline(month)) & (inp.rb_fc["published"] <= cutoff)]
    return Inputs(inp.kpif.loc[: month - 1], inp.comps[inp.comps["month"] <= month - 1], inp.feats.loc[:month], rb)


# ------------------------------------------------------------------ small helpers


def _latest(table: pd.DataFrame, key: str, how: str = "level") -> pd.Series:
    s = obs.as_of(key, sd.LATEST, table)
    if s.empty:
        return s
    return (sd._yoy_sparse(s) if how == "yoy" else s).dropna()


def _at(s: pd.Series, p: pd.Period) -> float | None:
    v = s.get(p)
    return None if v is None or pd.isna(v) else float(v)


def _n(x: float | None, d: int = 1, sign: bool = False) -> str:
    if x is None or pd.isna(x):
        return "–"
    if d == 0 and not sign and abs(x) >= 1000:
        return _int(x)
    return num(float(x), d, sign)


def _int(x: float | None) -> str:
    return "–" if x is None or pd.isna(x) else f"{x:,.0f}".replace(",", " ")


def _md_table(header: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out


def _direction(now: float | None, before: float | None, tol: float = 0.05) -> str:
    if now is None or before is None:
        return "–"
    if now > before + tol:
        return "upp"
    if now < before - tol:
        return "ned"
    return "oförändrat"


# Indicators shown in "Läget" and compared in "Vad har ändrats": key, label, how, decimals
INDICATORS = [
    ("kpif_yy", "KPIF, årstakt %", "level", 1),
    ("kpif_xe_index", "KPIF-XE, årstakt %", "yoy", 1),
    ("kpif_services_index", "KPIF tjänster, årstakt %", "yoy", 1),
    ("kpif_goods_index", "KPIF varor, årstakt %", "yoy", 1),
    ("ppi_itpi_consumer", "Producentpriser konsumtionsvaror (inhemsk tillgång), årsförändring %", "yoy", 1),
    ("ppi_impi_food", "Importpriser livsmedel, årsförändring %", "yoy", 1),
    ("ki_prices_grocery", "Prisplaner dagligvaruhandeln, nettotal", "level", 0),
    ("ki_services", "Prisplaner tjänstesektorn, nettotal", "level", 0),
    ("fao_food_idx", "FAO livsmedelspriser (USD), årsförändring %", "yoy", 1),
    ("policy_rate", "Styrränta %", "level", 2),
    ("gvb_2y", "Statsobligation 2 år %", "level", 2),
    ("mortgage_rate_new", "Bolåneränta nya avtal %", "level", 2),
    ("aku_unemp_sa", "Arbetslöshet AKU, säsongsrensad %", "level", 1),
    ("af_inskrivna_arbetslosa", "Inskrivna arbetslösa (AF), årsförändring %", "yoy", 1),
    ("af_varsel", "Varsel (AF), personer", "level", 0),
    ("house_price_idx", "Fastighetsprisindex småhus, årsförändring %", "yoy", 1),
    ("hh_lending_growth", "Utlåning till hushåll, årstakt %", "level", 1),
]


def snapshot(table: pd.DataFrame) -> dict[str, tuple[pd.Period, float]]:
    out = {}
    for key, _, how, _ in INDICATORS:
        s = _latest(table, key, how)
        if len(s):
            out[key] = (s.index.max(), float(s.iloc[-1]))
    return out


# ------------------------------------------------------------------ sections


def section_forecast(month: pd.Period, cutoff: pd.Timestamp, e: dict | None, champ: pd.DataFrame | None) -> tuple[list[str], dict]:
    fc = sd.forecast_rows(month, e, cutoff)
    facts = {}
    lines = [f"## Prognosen för {month_sv(str(month))}", ""]
    live = fc[fc["model"] == "skarp"].iloc[0] if len(fc) and (fc["model"] == "skarp").any() else None
    if live is not None:
        facts["live"] = float(live["forecast_yy"])
        lines.append(f"**Skarp prognos: {_n(live['forecast_yy'], 2)} %** i årstakt (50 %: {_n(live['lo50'])}–{_n(live['hi50'])}, "
                     f"80 %: {_n(live['lo80'])}–{_n(live['hi80'])} %; status {live['status']}, gjord {str(live['made_at'])[:16].replace('T', ' ')}).")
    else:
        lines.append("Ingen skarp prognosfil fanns vid informationsdatumet.")
    if e is not None:
        u = e.get("uncertainty") or {}
        facts["model"] = float(e["forecast"]["yy"])
        b50, b80 = u.get("band_50"), u.get("band_80")
        if b50 and b80:
            lines.append(f"Osäkerhet enligt J5:s EWMA-band (förslag, {u.get('n_past')} tidigare fel): 50 % {_n(b50[0])}–{_n(b50[1])}, "
                         f"80 % {_n(b80[0])}–{_n(b80[1])} %.")
    lines.append("")
    if len(fc):
        rows = [[r["label"], r["evidence"], _n(r["forecast_yy"], 2)] for _, r in fc.iterrows()]
        lines += _md_table(["Prognos", "Typ", "KPIF årstakt %"], rows)
        lines += ["", "Skuggor och K2-kandidaten är valda på 2015–2026: deras fel bakåt är urvalsevidens, och de styr inte "
                      "den skarpa prognosen.", ""]
    if e is not None:
        lines += ["### Förklaring (K3)", ""]
        lines += [f"- {t}" for t in e["text"]]
        lines += ["", "Bidrag per komponent, procentenheter (prognos för månadsförändringen och bidrag till förändringen i årstakt):", ""]
        from kpif_nowcast.explain import NAME_SV

        rows = [[NAME_SV.get(c, c), _n(p["mm_pp"], 2, True), _n(p["change_yy"], 2, True)] for c, p in e["components"].items()]
        rows.append(["avrundning", "", _n(e["change_rest_yy"], 2, True)])
        lines += _md_table(["Komponent", "Prognos m/m", "Bidrag till ändrad årstakt"], rows)
        i = e["information_set"]
        lines += ["", f"Förklaringen är den skarpa modellen körd med data kända vid informationsdatumet "
                      f"({_n(e['forecast']['yy'], 2)} %); informationsmängd: KPIF t.o.m. {i['kpif_through']}, energipriser för "
                      f"{i['energy_prices_for']}, Riksbankens bana {i['riksbank_vintage']}.", ""]
    if champ is not None and len(champ):
        c = champ.set_index("model")
        r0 = champ.iloc[0]
        parts = [f"{m} {_n(c.loc[m, 'mae_2015_26'], 3)}" for m in c.index if pd.notna(c.loc[m, "mae_2015_26"])]
        lines += [f"Champion/challenger (MAE i årstakt, 2015–26, urvalsevidens, n = {int(r0['n_long'])}): " + ", ".join(parts)
                  + f". Live-utvärdering: {int(r0['n_live'])} månader med FINAL-skuggprognos och publicerat utfall.", ""]
    return lines, facts


def section_situation(table: pd.DataFrame) -> tuple[list[str], dict]:
    facts = {}
    lines = ["## Läget", ""]
    # inflation and the price chain: latest, 3 and 12 months earlier
    rows = []
    for key, label, how, d in INDICATORS[:9]:
        s = _latest(table, key, how)
        if s.empty:
            continue
        p = s.index.max()
        rows.append([label, str(p), _n(s.iloc[-1], d), _n(_at(s, p - 3), d), _n(_at(s, p - 12), d)])
        facts[key] = (p, float(s.iloc[-1]), _at(s, p - 3), _at(s, p - 12))
    lines += ["### Inflation och prisleden", ""]
    lines += _md_table(["Serie", "Senaste", "Värde", "3 mån tidigare", "12 mån tidigare"], rows)
    lines.append("")
    if "kpif_yy" in facts:
        p, v, v3, v12 = facts["kpif_yy"]
        lines.append(f"KPIF låg på {num(v, 1)} % i årstakt i {month_sv(str(p))}, {_direction(v, v3)} från {_n(v3)} % tre månader tidigare.")
    if "ppi_itpi_consumer" in facts:
        p, v, v3, _ = facts["ppi_itpi_consumer"]
        lines.append(f"Producentpriserna på konsumtionsvaror ökade {num(v, 1)} % på ett år ({month_sv(str(p))}), "
                     f"{_direction(v, v3)} mot tre månader tidigare.")
    if "ki_prices_grocery" in facts:
        p, v, _, v12 = facts["ki_prices_grocery"]
        lines.append(f"Dagligvaruhandelns prisplaner låg på nettotal {num(v, 0)} ({month_sv(str(p))}) mot {_n(v12, 0)} ett år tidigare.")
    lines.append("")

    # labour market
    lines += ["### Arbetsmarknad", ""]
    ins = _latest(table, "af_inskrivna_arbetslosa")
    vs = _latest(table, "af_varsel")
    aku = _latest(table, "aku_unemp_sa")
    if len(ins):
        p = ins.index.max()
        prev = _at(ins, p - 12)
        facts["af_inskrivna"] = (p, float(ins.iloc[-1]), prev)
        lines.append(f"- Inskrivna arbetslösa hos Arbetsförmedlingen: {_int(ins.iloc[-1])} i {month_sv(str(p))}"
                     + (f", {num((ins.iloc[-1] / prev - 1) * 100, 1, True)} % mot ett år tidigare." if prev else "."))
    if len(vs):
        vs3 = vs.rolling(3).mean().dropna()
        if len(vs3):
            p = vs3.index.max()
            prev = _at(vs3, p - 12)
            lines.append(f"- Varsel, tremånadersmedel t.o.m. {month_sv(str(p))}: {_int(vs3.iloc[-1])} personer per månad"
                         + (f" ({num((vs3.iloc[-1] / prev - 1) * 100, 1, True)} % mot ett år tidigare)." if prev else "."))
    if len(aku):
        p = aku.index.max()
        lines.append(f"- Arbetslöshet enligt AKU, säsongsrensad: {num(aku.iloc[-1], 1)} % i {month_sv(str(p))} "
                     f"({_n(_at(aku, p - 12))} % ett år tidigare).")
    lines.append("")

    # housing and credit
    lines += ["### Bostäder och krediter", ""]
    hp = _latest(table, "house_price_idx", "yoy")
    mr = _latest(table, "mortgage_rate_new")
    hl = _latest(table, "hh_lending_growth")
    if len(hp):
        lines.append(f"- Småhuspriser (fastighetsprisindex): {num(hp.iloc[-1], 1, True)} % på ett år ({hp.index.max()}).")
    if len(mr):
        p = mr.index.max()
        lines.append(f"- Bolåneränta, nya avtal: {num(mr.iloc[-1], 2)} % i {month_sv(str(p))} ({_n(_at(mr, p - 12), 2)} % ett år tidigare).")
    if len(hl):
        lines.append(f"- Utlåning till hushåll: {num(hl.iloc[-1], 1)} % i årstakt ({month_sv(str(hl.index.max()))}).")
    lines.append("")

    # counties
    lines += ["### Regionala skillnader", ""]
    try:
        reg = sd.region_rows(table)
    except Exception as exc:  # noqa: BLE001
        reg = pd.DataFrame()
        lines.append(f"Länsdata saknas ({type(exc).__name__}).")
    if len(reg):
        def county_line(measure: str, label: str, fmt) -> str | None:
            r = reg[reg["measure"] == measure]
            if r.empty:
                return None
            nat = r[r["code"] == "00"]
            cs = r[r["code"] != "00"].sort_values("value", ascending=False)
            hi = ", ".join(f"{x.county} {fmt(x.value)}" for x in cs.head(3).itertuples())
            lo = ", ".join(f"{x.county} {fmt(x.value)}" for x in cs.tail(3).iloc[::-1].itertuples())
            p = r["period"].max()
            n = f"riket {fmt(nat['value'].iloc[0])}" if len(nat) else ""
            return f"- {label} ({p}; {n}): högst {hi}; lägst {lo}."

        for measure, label, fmt in [
            ("af_andel", "Inskrivna arbetslösa, % av arbetskraften", lambda v: num(v, 1)),
            ("konkurser_per_10k", "Konkurser senaste 12 mån per 10 000 invånare", lambda v: num(v, 1)),
            ("smahus_pris", "Småhuspriser, medelpris tkr", _int),
        ]:
            ln = county_line(measure, label, fmt)
            if ln:
                lines.append(ln)
        sm = reg[(reg["measure"] == "smahus_pris") & (reg["code"] != "00")].dropna(subset=["change"])
        if len(sm):
            lines.append(f"- Småhuspriserna (medelpris, inte kvalitetsjusterat) ändrades mellan {num(sm['change'].min(), 1, True)} och "
                         f"{num(sm['change'].max(), 1, True)} % på ett år mellan länen.")
        aku_missing = 21 - int(((reg["measure"] == "aku_arbetsloshet") & (reg["code"] != "00")).sum())
        if aku_missing > 0:
            lines.append(f"- AKU per län: {aku_missing} län saknar senaste kvartalet och redovisas inte.")
        facts["region"] = True
    lines.append("")

    # AI
    lines += ["### AI", ""]
    try:
        ai = sd.ai_indicator_rows(table)
    except Exception:  # noqa: BLE001
        ai = pd.DataFrame()
    if len(ai):
        ind = ai[ai["series"] == "ai_diffusion_indicator_z"].sort_values("year")
        ml = ai[(ai["series"] == "ad_share_per_10k") & (ai["group"] == "maskininlärning")].sort_values("year")
        use = ai[ai["series"] == "firm_ai_use_pct"].sort_values("year")
        if len(ind):
            r = ind.iloc[-1]
            lines.append(f"- AI-indikatorn (J7:s metod, z-värde mot 2017–): {num(r['value'], 2, True)} för {int(r['year'])}.")
        if len(ml):
            full = ml[~ml["partial"]]
            r = ml.iloc[-1]
            txt = f"- Platsannonser som nämner maskininlärning: {num(r['value'], 1)} per 10 000 annonser {int(r['year'])}"
            txt += f" ({int(r['months'])} månader)" if r["partial"] else ""
            if len(full) and r["partial"]:
                txt += f", mot {num(full.iloc[-1]['value'], 1)} helåret {int(full.iloc[-1]['year'])}"
            lines.append(txt + ".")
        se, eu = use[use["group"] == "SE"], use[use["group"] == "EU27"]
        if len(se) and len(eu):
            lines.append(f"- Företag som använder AI {int(se.iloc[-1]['year'])}: Sverige {num(se.iloc[-1]['value'], 0)} %, "
                         f"EU27 {num(eu.iloc[-1]['value'], 0)} %.")
    else:
        lines.append("AI-data saknas.")
    lines.append("")
    return lines, facts


def section_changes(table_now: pd.DataFrame, table_prev: pd.DataFrame, prev_cutoff: pd.Timestamp,
                    e: dict | None) -> list[str]:
    now, before = snapshot(table_now), snapshot(table_prev)
    rows = []
    for key, label, _, d in INDICATORS:
        if key not in now:
            continue
        p, v = now[key]
        if key in before and before[key][0] == p and abs(before[key][1] - v) < 1e-9:
            continue  # nothing new
        bp, bv = before.get(key, (None, None))
        rows.append([label, f"{bp or '–'}: {_n(bv, d)}", f"{p}: {_n(v, d)}"])
    lines = ["## Vad har ändrats sedan förra månaden", "",
             f"Jämfört med bilden vid förra månadens informationsdatum ({prev_cutoff.date()}): serier med ny eller reviderad "
             "siffra.", ""]
    lines += _md_table(["Serie", "Då (period: värde)", "Nu (period: värde)"], rows) if rows else ["Inga nya siffror."]
    lines.append("")
    if e is not None and e.get("last_miss"):
        lm = e["last_miss"]
        lines.append(f"Förra månadens prognos ({month_sv(lm['month'])}), modellen körd med data kända vid dess deadline: "
                     f"{_n(lm['forecast_yy'], 2)} %, utfall {_n(lm['actual_yy'], 1)} %, fel {_n(lm['error_yy'], 2, True)} pe.")
        lines.append("")
    return lines


def headline(month: pd.Period, fc_facts: dict, sit: dict, e: dict | None) -> list[str]:
    out = ["## Huvudbudskap", ""]
    if "live" in fc_facts:
        s = f"- Skarp prognos för KPIF i {month_sv(str(month))}: **{num(fc_facts['live'], 1)} %** i årstakt"
    elif "model" in fc_facts:
        s = f"- Ingen skarp prognosfil vid informationsdatumet; modellens prognos för {month_sv(str(month))}: **{num(fc_facts['model'], 1)} %**"
    else:
        s = f"- Ingen prognos för {month_sv(str(month))} kunde tas fram."
    if e is not None:
        f = e["forecast"]
        s += f", mot {num(f['last_known_yy'], 1)} % i {month_sv(f['last_known_month'])}"
    out.append(s + ".")
    if e is not None:
        comps = {c: p["change_yy"] for c, p in e["components"].items()}
        from kpif_nowcast.explain import NAME_SV

        top = max(comps, key=lambda c: abs(comps[c]))
        out.append(f"- Största bidraget till förändringen i årstakt kommer från {NAME_SV.get(top, top)} "
                   f"({num(comps[top], 2, True)} pe) enligt modellens bokföring.")
    if "kpif_xe_index" in sit and "kpif_services_index" in sit:
        p, xe, _, _ = sit["kpif_xe_index"]
        out.append(f"- Underliggande: KPIF-XE {num(xe, 1)} % och tjänster {num(sit['kpif_services_index'][1], 1)} % i årstakt ({month_sv(str(p))}).")
    if "ppi_itpi_consumer" in sit and "ki_prices_grocery" in sit:
        out.append(f"- Prisleden: producentpriser konsumtionsvaror {num(sit['ppi_itpi_consumer'][1], 1, True)} % på ett år, "
                   f"dagligvaruhandelns prisplaner nettotal {num(sit['ki_prices_grocery'][1], 0)}.")
    if "admin" in fc_facts:
        a = fc_facts["admin"]
        adj = f"{num(a.adjust, 2, True)} pe i årstakt" if a.used and a.adjust else "ingen justering"
        txt = f"- Beslutade engångshändelser (kalendern för administrerade priser, förslag): {adj} för {month_sv(str(month))}"
        pv = fc_facts.get("preview")
        if pv is not None and pv.used and pv.adjust:
            txt += f", {num(pv.adjust, 2, True)} pe för {month_sv(str(month + 1))}"
        out.append(txt + ". Johannes beslutar om användningen.")
    if "af_inskrivna" in sit:
        p, v, prev = sit["af_inskrivna"]
        if prev:
            out.append(f"- Arbetsmarknad: inskrivna arbetslösa {num((v / prev - 1) * 100, 1, True)} % mot ett år tidigare ({month_sv(str(p))}).")
    out.append("")
    return out


# ------------------------------------------------------------------ administered prices (L9)

# Decisions on the calendar's suggestion (beslutslogg), shown when made by the cutoff: month -> (date, text)
ADMIN_DECISIONS = {
    "2026-11": ("2026-11-23", "Johannes beslutade 2026-11-23 att inte justera novemberprognosen; den schemalagda "
                              "slutprognosen körs oförändrad (beslutsloggen)."),
}


def admin_inputs(month: pd.Period, inp=None) -> tuple[list, pd.Series | None]:
    """Calendar events and KPIF index as known for `month`: KS parts and index cut to month-1."""
    from kpif_nowcast import admin_calendar as ac

    parts, index = ac._load_parts_and_index()
    if inp is not None:
        index = inp.kpif["index"]
    if parts is not None:
        parts = parts.loc[: month - 1]
    if index is not None:
        index = index.loc[: month - 1]
    return ac.all_events(parts), index


def section_admin(month: pd.Period, cutoff: pd.Timestamp, events: list, index: pd.Series | None) -> tuple[list[str], dict]:
    from kpif_nowcast import admin_calendar as ac

    s = ac.suggest(month, events, index, cutoff)
    lines = ac.markdown_section(s, "##")
    dec = ADMIN_DECISIONS.get(str(month))
    if dec and pd.Timestamp(dec[0]) <= cutoff:
        lines += [f"**Beslut:** {dec[1]}", ""]
    return lines, {"admin": s}


def section_preview(month: pd.Period, cutoff: pd.Timestamp, events: list, index: pd.Series | None,
                    rb_fc: pd.DataFrame | None, fc_facts: dict) -> tuple[list[str], dict]:
    """The next month: the calendar's suggestion at this letter's cutoff and what it means for that forecast."""
    from kpif_nowcast import admin_calendar as ac

    nxt = month + 1
    s = ac.suggest(nxt, events, index, cutoff)
    lines = [f"## Förhandsvisning: {month_sv(str(nxt))}", "",
             f"*Kalenderns förslag för {nxt} med beslut kända vid informationsdatumet {cutoff.date()}. Prognosen för "
             f"{month_sv(str(nxt))} görs i månadsrutinen dag 1–4 i {month_sv(str(nxt + 1))}; förslaget räknas om då "
             "med beslut fram till dess. Johannes beslutar om justeringen används.*", ""]
    if s.used:
        lines += [f"- {ac._short(e.label, 90)}: {ac._num(e.suggest_pe)} pe m/m ({e.method}, beslut senast {e.decided})."
                  for e in s.used]
        lines += [f"- Summa {ac._num(s.mm_pe)} pe m/m, i årstakt **{ac._num(s.adjust, 2)} pe**: används förslaget blir den "
                  f"skarpa prognosen för {month_sv(str(nxt))} modellens siffra plus {num(s.adjust, 2)} procentenheter. "
                  "Huvudmodellen ser drivmedel bara via Brent i SEK, så skatteändringar på drivmedel finns inte i modellens "
                  "siffra, och inte regionala biljettpriser heller."]
    else:
        lines.append(f"- Inga beslutade engångshändelser med känd storlek för {month_sv(str(nxt))}.")
    for e in s.listed:
        size = "?" if e.pe is None else ac._num(e.pe)
        lines.append(f"- Ej med ({ac.why_not_used(e, nxt, cutoff)}): {size} pe, {ac._short(e.label, 90)}.")
    lines.append(f"- Eko av tidigare engångshändelser i modellens trend och säsong: {ac._num(s.echo_pe)} pe m/m "
                 "(information, ingår inte i förslaget).")
    facts = {"preview": s}
    if rb_fc is not None and len(rb_fc):
        from kpif_nowcast.riksbank_benchmark import riksbank_at_deadline

        rb = riksbank_at_deadline(rb_fc[rb_fc["published"] <= cutoff], pd.PeriodIndex([month, nxt]))
        if nxt in rb.index:
            r = rb.loc[nxt]
            prev = rb["riksbank"].get(month)
            txt = (f"- Riksbankens senaste bana vid informationsdatumet ({r['rb_round']}): {num(float(r['riksbank']), 1)} % "
                   f"för {month_sv(str(nxt))}")
            if prev is not None and pd.notna(prev):
                txt += f" mot {num(float(prev), 1)} % för {month_sv(str(month))}"
            lines.append(txt + ". Om banan räknar med de beslutade ändringarna är inte verifierat här.")
            facts["rb_next"] = float(r["riksbank"])
    if "live" in fc_facts:
        lines.append(f"- Som jämförelse: skarp prognos för {month_sv(str(month))} {num(fc_facts['live'], 2)} %. "
                     "Ingen prognos för nästa månad görs här (energipriserna för månaden saknas).")
    lines.append("")
    return lines, facts


# ------------------------------------------------------------------ assembly


def build(month: str | pd.Period, table: pd.DataFrame | None = None, inp=None, info: dict | None = None,
          today: pd.Timestamp | str | None = None, with_k2: bool = True) -> str:
    month = pd.Period(month, "M")
    cutoff = cutoff_for(month, today)
    prev_cutoff = cutoff_for(month - 1, today)
    full = obs.load() if table is None else table
    t_now, t_prev = sd.cut_table(full, cutoff), sd.cut_table(full, prev_cutoff)

    e, champ = None, None
    try:
        if inp is None:
            from kpif_nowcast.shadow import load_inputs

            inp, info = load_inputs()
        ci = cut_inputs(inp, month, cutoff)
        if month not in ci.feats.index:
            raise ValueError(f"no energy features for {month}")
        live_info = info if info and info.get("target") == month else {"target": None}  # el days etc. only for today's target
        e = sd.explanation(ci, live_info, target=month, with_k2=with_k2)
        try:
            champ = sd.champion_rows(ci)
        except Exception as exc:  # noqa: BLE001
            print(f"champion table skipped: {exc!r}")
    except Exception as exc:  # noqa: BLE001 - the letter is still useful without the explanation
        print(f"explanation skipped: {exc!r}")

    fc_lines, fc_facts = section_forecast(month, cutoff, e, champ)
    admin_lines, preview_lines = [], []
    try:
        events, index = admin_inputs(month, inp)
        admin_lines, a_facts = section_admin(month, cutoff, events, index)
        fc_facts.update(a_facts)
        rb_fc = getattr(inp, "rb_fc", None)
        preview_lines, p_facts = section_preview(month, cutoff, events, index, rb_fc, fc_facts)
        fc_facts.update(p_facts)
    except Exception as exc:  # noqa: BLE001 - the letter is still useful without the calendar
        print(f"admin calendar skipped: {exc!r}")
    sit_lines, sit = section_situation(t_now)
    lines = [f"# Månadsbrev: KPIF och läget i Sverige, {month_sv(str(month))}", "",
             f"*Informationsdatum {cutoff.date()} (data kända då). Genererat av `python -m kpif_nowcast.manadsbrev {month}`; "
             "beskrivande, inga orsaksslutsatser. Dashboard: Sverigeläget.*", ""]
    lines += headline(month, fc_facts, sit, e)
    lines += fc_lines
    lines += admin_lines
    lines += preview_lines
    lines += sit_lines
    lines += section_changes(t_now, t_prev, prev_cutoff, e)
    lines += ["## Om brevet", "",
              "Källor: SCB, Riksbanken, Konjunkturinstitutet, Arbetsförmedlingen, Tillväxtanalys, Eurostat, FAO, FRED, JobTech "
              "(via projektets observationstabell, senaste version känd vid informationsdatumet). Den skarpa prognosen är "
              "den committade filen `forecasts/<månad>.json`; skuggprognoser i `forecasts/shadow/`. Metod för förklaringen: "
              "`src/kpif_nowcast/explain.py` (K3), för osäkerhetsbandet J5, för AI-indikatorn `docs/ai-indikator.md`.", ""]
    return "\n".join(lines)


def write(month: str, **kw) -> Path:
    text = build(month, **kw)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{pd.Period(month, 'M')}.md"
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path}")
    return path


def default_month() -> pd.Period:
    """The next KPIF month not yet published (the live forecast's target)."""
    from kpif_nowcast.data import load_kpif

    return load_kpif().index.max() + 1


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("month", nargs="?", help="target month YYYY-MM (default: next unpublished month)")
    parser.add_argument("--today", help="information date override (YYYY-MM-DD)")
    parser.add_argument("--no-k2", action="store_true")
    parser.add_argument("--stdout", action="store_true", help="print instead of writing docs/manadsbrev/")
    args = parser.parse_args(argv)
    month = args.month or str(default_month())
    if args.stdout:
        import sys

        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(build(month, today=args.today, with_k2=not args.no_k2))
    else:
        write(month, today=args.today, with_k2=not args.no_k2)


if __name__ == "__main__":
    main()
