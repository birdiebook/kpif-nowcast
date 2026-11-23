"""Data catalog: every series in the observation table, with metadata.

One `Spec` per series: area, Swedish label, unit, frequency, source, how to fetch it,
publication lag (-> known_from), whether it gets revised, and why it matters for inflation.

All series are stored on a monthly period axis: a quarter sits on its last month, a year on December.

Run `python -m kpif_nowcast.observations` to fetch everything into data/observations.parquet,
and `python -m kpif_nowcast.catalog` to print the catalog as Markdown (docs/datakatalog.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

import pandas as pd

AREAS = {
    "inflation": "Inflation",
    "prisled": "Prisleden: producent-, import- och planerade priser",
    "energi": "Energi och råvaror",
    "arbetsmarknad": "Arbetsmarknad och löner",
    "hushall": "Hushållen",
    "bostad_kredit": "Bostäder och krediter",
    "foretag": "Företagen",
    "omvarld": "Omvärlden",
    "ai_produktivitet": "AI och produktivitet",
    "penningpolitik": "Penningpolitik och krona",
    "region": "Regionalt: län",
}


@dataclass
class Spec:
    key: str
    area: str
    label: str  # Swedish, for the dashboard
    unit: str
    freq: str  # "M", "Q", "A"
    source: str
    fetch: Callable[[], pd.Series] = field(repr=False)
    lag_days: int  # days after period end until typically published (conservative)
    revised: bool = False
    link: str = ""  # one line: connection to inflation (or to the AI/productivity story)
    note: str = ""


# ------------------------------------------------------------------ fetch helpers


def _current_month() -> pd.Period:
    return pd.Period(date.today(), "M")


def scb(table: str, **codes: str) -> Callable[[], pd.Series]:
    def f() -> pd.Series:
        from kpif_nowcast.sources import scb as _scb

        return _scb.series(table, codes)

    return f


def konj(path: str, **selection: str) -> Callable[[], pd.Series]:
    def f() -> pd.Series:
        from kpif_nowcast.sources import konj as _konj

        return _konj.fetch_series(path, selection)

    return f


def swea_monthly(series_id: str) -> Callable[[], pd.Series]:
    """Monthly mean of a daily Riksbank series, current (incomplete) month dropped."""

    def f() -> pd.Series:
        from kpif_nowcast.sources import riksbank

        d = riksbank.fetch_swea(series_id, "1990-01-01")
        m = d.groupby(d.index.to_period("M")).mean()
        return m[m.index < _current_month()]

    return f


def fred_monthly(series_id: str, how: str = "mean") -> Callable[[], pd.Series]:
    def f() -> pd.Series:
        from kpif_nowcast.sources import fred

        d = fred.fetch_series(series_id)
        if d.index.inferred_freq in ("MS", "M", "ME") or how == "as_is":
            m = d.copy()
            m.index = d.index.to_period("M")
        else:
            m = d.groupby(d.index.to_period("M")).agg(how)
        return m[m.index < _current_month()]

    return f


def scb_sum(table: str, sum_dim: str, **codes: str) -> Callable[[], pd.Series]:
    """Sum an SCB table over one dimension (e.g. dwelling starts over house types)."""

    def f() -> pd.Series:
        from kpif_nowcast.sources import scb as _scb

        df = _scb.fetch_table(table, {**codes, sum_dim: "*", "Tid": "*"})
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        s = df.groupby("Tid")["value"].sum(min_count=1)
        s.index = _scb.to_month_period(s.index.to_series())
        return s.dropna().sort_index()

    return f


def _bankruptcies() -> pd.Series:
    """Tillväxtanalys: bankruptcies per month, summed over all industries (no national total exists)."""
    from kpif_nowcast.sources import konj as _konj

    url = ("https://statistik.tillvaxtanalys.se/PxWeb/api/v1/sv/Tillv%C3%A4xtanalys%20statistikdatabas/"
           "Konkurser%20och%20offentliga%20ackord/12_konkurser_manad_tot_bransch.px")
    df = _konj.fetch_px(url, {"variabel": "0"}, prefix="tillvaxtanalys_konkurser")
    s = df.groupby("period")["value"].sum(min_count=1)
    return s[s.index < _current_month()].dropna()


def eurostat(dataset: str, **filters: str) -> Callable[[], pd.Series]:
    def f() -> pd.Series:
        from kpif_nowcast.sources import eurostat as _es

        return _es.series(dataset, **filters)

    return f


def ea_flash(code: str) -> Callable[[], pd.Series]:
    """Euro area HICP flash (first release, y/y): old dataset 2017-08..2025-12 + new from 2026."""

    def f() -> pd.Series:
        from kpif_nowcast.sources import eurostat as _es

        old_code = {"TOTAL": "CP00"}.get(code, code)
        old = _es.series("prc_hicp_fp", geo="EA", unit="RCH_A", release="FLS", coicop=old_code)
        new = _es.series("prc_hicp_fpd", geo="EA", unit="RCH_A", release="FLS", coicop18=code)
        s = pd.concat([old[old.index < new.index.min()], new])
        return s[~s.index.duplicated(keep="last")]

    return f


def fao(column: str) -> Callable[[], pd.Series]:
    def f() -> pd.Series:
        from kpif_nowcast.sources import misc

        return misc.fao_food_price_index()[column].dropna()

    return f


def gscpi() -> pd.Series:
    from kpif_nowcast.sources import misc

    return misc.gscpi()


def jobads(query: str | None) -> Callable[[], pd.Series]:
    def f() -> pd.Series:
        from kpif_nowcast.sources import misc

        return misc.jobtech_monthly_count(query)

    return f


def _kpif() -> pd.DataFrame:
    from kpif_nowcast.data import load_kpif

    return load_kpif()


def _brent_sek() -> pd.Series:
    from kpif_nowcast.features import fuel_proxy_monthly

    s = fuel_proxy_monthly()
    return s[s.index < _current_month()]


# ------------------------------------------------------------------ the catalog

AKU = dict(Arbetskraftstillh="ALÖSP", Kon="1+2", Alder="tot15-74", ContentsCode="000007L9")

CATALOG: list[Spec] = [
    # Inflation
    Spec("kpif_index", "inflation", "KPIF, index", "2020=100", "M", "SCB TAB6590",
         lambda: _kpif()["index"], 15, link="Målvariabeln."),
    Spec("kpif_yy", "inflation", "KPIF, årstakt", "%", "M", "SCB TAB6590",
         lambda: _kpif()["yy_official"], 15, link="Målvariabeln."),
    # Energy
    Spec("brent_sek", "energi", "Brent i kronor (dag 1–25)", "SEK/fat", "M", "FRED + Riksbanken",
         _brent_sek, 1, link="Drivmedelspriser samma månad."),
    # Labour market
    Spec("aku_unemp_nsa", "arbetsmarknad", "Arbetslöshet (AKU), ej säsongsrensad", "%", "M", "SCB TAB6387",
         scb("TAB6387", TypData="O_DATA", **AKU), 25, revised=True, link="Resursutnyttjande → löner → tjänstepriser.",
         note="2001–2020 är länkade data (SCB:s omläggning 2021), inte det som publicerades då."),
    Spec("aku_unemp_sa", "arbetsmarknad", "Arbetslöshet (AKU), säsongsrensad", "%", "M", "SCB TAB6387",
         scb("TAB6387", TypData="SR_DATA", **AKU), 25, revised=True,
         link="Som ovan, lättare att läsa men revideras."),
    # Activity
    Spec("gdp_ind_yy", "foretag", "BNP-indikatorn, årstakt (kalenderjusterad)", "%", "M", "SCB TAB443",
         scb("TAB443", BNPMarknadspris="BNPM", ContentsCode="0000027O"), 45, revised=True,
         link="Efterfrågetryck i ekonomin.",
         note="Publiceras ca dag 8–10 andra månaden efter (38–41 d), kvartalets sista månad ca 29 d (K11)."),
    # Monetary policy and krona
    Spec("kix", "penningpolitik", "Kronindex KIX (högre = svagare krona)", "index", "M", "Riksbanken SWEA",
         swea_monthly("SEKKIX92"), 1, link="Svagare krona → dyrare import med fördröjning."),
    Spec("policy_rate", "penningpolitik", "Styrränta", "%", "M", "Riksbanken SWEA",
         swea_monthly("SECBREPOEFF"), 1, link="Stramare penningpolitik dämpar efterfrågan."),
    # Firms' price plans
    Spec("ki_services", "foretag", "Prisplaner tjänstesektorn (nettotal)", "nettotal", "M", "KI Konjunkturbarometern",
         konj("KonjBar/ftgmanad/Bartjam.px", **{"Bransch (SNI 2007)": "BTJA", "Fråga": "202", "Serie": "O"}), 3,
         link="Företagens planerade prishöjningar kommande 3 mån."),

    # ---------------- Labour market and wages
    Spec("wage_private_nonmanual", "arbetsmarknad", "Månadslön tjänstemän, privat sektor", "kr", "M", "SCB TAB2564",
         scb("TAB2564", SNI2007="B-S exkl.O", Tillagg="30", ContentsCode="AM0101D2"), 60, revised=True,
         link="Löner är den största kostnaden i tjänstesektorn.", note="Preliminär, revideras för retroaktiva lönehöjningar."),
    Spec("wage_private_manual_hourly", "arbetsmarknad", "Timlön arbetare, privat sektor (exkl. övertid)", "kr/tim",
         "M", "SCB TAB2550", scb("TAB2550", SNI2007="B-S exkl.O", Overtidstillagg="10", ContentsCode="AM0101D4"),
         60, revised=True, link="Som ovan. Stark säsong, använd årsförändring."),
    Spec("wage_municipal_yy", "arbetsmarknad", "Månadslön kommuner, årstakt (preliminär)", "%", "M", "SCB TAB1972",
         scb("TAB1972", ContentsCode="AM0108A4"), 60, revised=True, link="Offentliga löner och avgifter."),
    Spec("labour_cost_salaried_yy", "arbetsmarknad", "Arbetskostnadsindex tjänstemän, årstakt", "%", "M",
         "SCB TAB3657", scb("TAB3657", EkoIndikator="AKI20", ContentsCode="AM0301AI"), 60, revised=True,
         link="Total arbetskostnad inkl. avgifter."),
    Spec("labour_cost_workers_yy", "arbetsmarknad", "Arbetskostnadsindex arbetare, årstakt", "%", "M",
         "SCB TAB3657", scb("TAB3657", EkoIndikator="AKI10", ContentsCode="AM0301AI"), 60, revised=True,
         link="Som ovan."),
    Spec("vacancies", "arbetsmarknad", "Lediga jobb, hela ekonomin (ej säsongsrensat)", "antal", "Q", "SCB TAB6406",
         scb("TAB6406", LedJobbTyp="LJtot", SNI2007Naring="A-S", ContentsCode="000007N4"), 60,
         link="Stramhet på arbetsmarknaden → lönetryck."),
    Spec("aku_employed", "arbetsmarknad", "Sysselsatta 15–74 år (AKU, ej säsongsrensat)", "tusental", "M",
         "SCB TAB6389", scb("TAB6389", Arbetskraftstillh="SYS", TypData="O_DATA", Kon="1+2", Alder="tot15-74",
                            ContentsCode="000007L2"), 25, revised=True, link="Sysselsättning och efterfrågan.",
         note="2001–2020 är länkade data (SCB:s omläggning 2021)."),
    Spec("hours_worked_yy", "ai_produktivitet", "Arbetade timmar (nationalräkenskaper), årstakt", "%", "Q",
         "SCB TAB4643", scb("TAB4643", SNI2007="0002", ContentsCode="0000025N"), 60, revised=True,
         link="Nämnare i produktiviteten (BNP per timme)."),

    # ---------------- Households
    Spec("hh_consumption_yy", "hushall", "Hushållens konsumtion (indikator), volym årstakt", "%", "M", "SCB TAB6932",
         scb("TAB6932", AndamalCOICOP="TOTex1012", ContentsCode="000008RA"), 45, revised=True,
         link="Efterfrågetryck. Hur mycket företagen kan föra vidare kostnader.",
         note="Ny metod från 2026 (moms- och kortdata, bakåtskattad till 2019), ca 10–13 d. "
              "Den gamla månadsindikatorn kom ca 40 d efter månaden, därför 45 d (K11)."),
    Spec("retail_volume_yy", "hushall", "Detaljhandelns försäljningsvolym exkl. drivmedel, årstakt", "%", "M",
         "SCB TAB3948", scb("TAB3948", SNI2007="47exkl47.3", ContentsCode="000006VZ"), 30, revised=True,
         link="Varuefterfrågan."),
    Spec("hh_infl_exp_median", "hushall", "Hushållens förväntade inflation 12 mån, median", "%", "M", "KI",
         konj("KonjBar/hushall/hushallinfrant.px", **{"Fråga": "Q661", "Serie": "S", "Grupp": "100"}), 3,
         link="Förväntningar påverkar lönekrav och acceptans för prishöjningar."),
    Spec("hh_infl_perceived_median", "hushall", "Hushållens upplevda inflation, median", "%", "M", "KI",
         konj("KonjBar/hushall/hushallinfrant.px", **{"Fråga": "Q551", "Serie": "S", "Grupp": "100"}), 3,
         link="Hur hushållen upplever prisutvecklingen nu."),
    Spec("hh_price_exp_net", "hushall", "Hushållens prisförväntningar 12 mån (nettotal)", "nettotal", "M", "KI",
         konj("KonjBar/hushall/hushall.px", **{"Fråga": "Q060", "Serie": "O", "Grupp": "100"}), 3,
         link="Lång serie (1996) för förväntningar."),
    Spec("hh_saving_rate", "hushall", "Hushållens sparkvot (säsongsrensad)", "%", "Q", "SCB TAB4591",
         scb("TAB4591", Sektor="S14", NRindikator="B8nRatioSAB6nD8n", ContentsCode="000000ZF"), 60, revised=True,
         link="Högt sparande = svagare konsumtion framåt."),

    # ---------------- External
    *[Spec(f"ea_flash_{k}", "omvarld", f"Euroområdet, inflation snabbestimat: {lbl}", "% årstakt", "M",
           "Eurostat prc_hicp_fp/fpd (FLS)", ea_flash(code), 2,
           link="Publiceras före vår deadline. Gemensamma rörelser i energi, mat, varor.",
           note="Första publicering (fryst), från 2017-08.")
      for k, code, lbl in [("total", "TOTAL", "totalt"), ("energy", "NRG", "energi"), ("food", "FOOD", "livsmedel"),
                           ("goods", "IGD_NNRG", "industrivaror"), ("services", "SERV", "tjänster")]],
    Spec("ea_hicp_total", "omvarld", "Euroområdet, inflation (HIKP), slutlig", "% årstakt", "M",
         "Eurostat prc_hicp_minr", eurostat("prc_hicp_minr", geo="EA", unit="RCH_A", coicop18="TOTAL"), 26,
         revised=True, link="Lång historik (1997) för omvärldens inflation."),
    Spec("fao_food_idx", "omvarld", "FAO:s livsmedelsprisindex", "2014–16=100", "M", "FAO",
         fao("food price index"), 10, revised=True, link="Världsmarknadspriser på mat → svenska matpriser med 3–9 mån."),
    Spec("fao_cereals", "omvarld", "FAO spannmålsprisindex", "2014–16=100", "M", "FAO", fao("cereals"), 10,
         revised=True, link="Spannmål → bröd, foder, kött."),
    Spec("fao_dairy", "omvarld", "FAO mejeriprisindex", "2014–16=100", "M", "FAO", fao("dairy"), 10, revised=True,
         link="Mejeripriser."),
    Spec("gas_eu_usd", "energi", "Naturgas Europa (TTF)", "USD/MMBtu", "M", "IMF via FRED",
         fred_monthly("PNGASEUUSDM", "as_is"), 60, revised=True, link="Gas → elpris och industrins kostnader."),
    Spec("wheat_usd", "omvarld", "Vete, världsmarknadspris", "USD/ton", "M", "IMF via FRED",
         fred_monthly("PWHEAMTUSDM", "as_is"), 60, revised=True, link="Livsmedelskedjan."),
    Spec("gscpi", "omvarld", "Global Supply Chain Pressure Index", "std.avvikelser", "M", "NY Fed", gscpi, 22,
         revised=True, link="Flaskhalsar i globala leveranskedjor → varupriser (2021–22)."),
    Spec("freight_ppi_deepsea", "omvarld", "Fraktpriser sjöfart (US PPI)", "index", "M", "BLS via FRED",
         fred_monthly("PCU483111483111", "as_is"), 21, revised=True, link="Fraktkostnader → importpriser.",
         note="BLS PPI kommer dag 8–20 i månaden efter. Försenade releaser 2025–26 i publication.py (K11)."),

    # ---------------- AI and productivity
    Spec("gdp_real_q", "ai_produktivitet", "BNP, fasta priser (produktionssidan)", "mnkr", "Q", "SCB TAB3112",
         scb("TAB3112", SNI2007="0010", ContentsCode="NR0103DB"), 60, revised=True,
         link="Täljare i produktiviteten."),
    Spec("hours_worked_q", "ai_produktivitet", "Arbetade timmar, hela ekonomin", "10 000 tim", "Q", "SCB TAB4643",
         scb("TAB4643", SNI2007="0002", ContentsCode="0000024N"), 60, revised=True,
         link="Nämnare i produktiviteten."),
    Spec("lp_hour_yy_se", "ai_produktivitet", "Arbetsproduktivitet per timme, Sverige, årstakt", "%", "Q",
         "Eurostat namq_10_lp_ulc",
         eurostat("namq_10_lp_ulc", geo="SE", na_item="RLPR_HW", unit="PCH_SM", s_adj="SCA"), 60, revised=True,
         link="Högre produktivitet sänker enhetsarbetskostnaden → lägre inflationstryck. AI:s väg in i makro."),
    Spec("lp_hour_yy_ea", "ai_produktivitet", "Arbetsproduktivitet per timme, euroområdet, årstakt", "%", "Q",
         "Eurostat namq_10_lp_ulc",
         eurostat("namq_10_lp_ulc", geo="EA20", na_item="RLPR_HW", unit="PCH_SM", s_adj="SCA"), 60, revised=True,
         link="Jämförelse för Sverige."),
    Spec("software_investment_q", "ai_produktivitet", "Investeringar i programvara och databaser, fasta priser",
         "mnkr", "Q", "SCB TAB3108", scb("TAB3108", Typ="142", ContentsCode="NR0103U5"), 60, revised=True,
         link="Digitala/AI-investeringar som ledande signal för produktivitet."),
    Spec("ai_use_firms_se", "ai_produktivitet", "Företag som använder AI, Sverige (10+ anställda)", "% av företag",
         "A", "Eurostat isoc_eb_ai",
         eurostat("isoc_eb_ai", geo="SE", unit="PC_ENT", indic_is="E_AI_TANY", size_emp="GE10"), 345,
         link="AI-spridningen i näringslivet."),
    Spec("ai_use_firms_eu", "ai_produktivitet", "Företag som använder AI, EU27 (10+ anställda)", "% av företag",
         "A", "Eurostat isoc_eb_ai",
         eurostat("isoc_eb_ai", geo="EU27_2020", unit="PC_ENT", indic_is="E_AI_TANY", size_emp="GE10"), 345,
         link="Jämförelse för Sverige."),
    Spec("jobads_total", "ai_produktivitet", "Publicerade platsannonser (Platsbanken)", "antal", "M",
         "JobTech historical ads", jobads(None), 3, link="Nämnare för AI-andelen. Även en signal för efterfrågan på arbetskraft."),
    Spec("jobads_ml", "ai_produktivitet", "Platsannonser som nämner \"maskininlärning\"", "antal", "M",
         "JobTech historical ads", jobads("maskininlärning"), 3,
         link="Efterfrågan på AI-kompetens.", note="Fritextsökning – brusig."),
    Spec("jobads_ai", "ai_produktivitet", "Platsannonser som nämner \"AI\"", "antal", "M", "JobTech historical ads",
         jobads("AI"), 3, link="Efterfrågan på AI-kompetens.", note="Fritextsökning – mycket brusig."),

    # ---------------- Housing and credit
    Spec("house_price_idx", "bostad_kredit", "Fastighetsprisindex, småhus", "index", "Q", "SCB TAB1150",
         scb("TAB1150", Region="00", ContentsCode="BO0501K2"), 30, revised=True,
         link="Förmögenhetseffekt på konsumtionen."),
    Spec("mortgage_rate_new", "bostad_kredit", "Bolåneränta, nya avtal (alla bindningstider)", "%", "M", "SCB TAB5783",
         scb("TAB5783", Referenssektor="1", Motpartssektor="2c", Avtal="0100", Rantebindningstid="1",
             ContentsCode="000004ZW"), 30, link="Penningpolitikens genomslag på hushållen."),
    Spec("hh_lending_growth", "bostad_kredit", "Utlåning till hushåll, årstakt", "%", "M", "SCB TAB4514",
         scb("TAB4514", NyckeltalSCB="FMS01", ContentsCode="000000UW"), 30, link="Kreditcykel → efterfrågan."),
    Spec("nfc_lending_growth", "bostad_kredit", "Utlåning till icke-finansiella företag, årstakt", "%", "M",
         "SCB TAB4514", scb("TAB4514", NyckeltalSCB="FMS02", ContentsCode="000000UW"), 30,
         link="Investeringar och kreditvillkor."),
    Spec("housing_starts", "bostad_kredit", "Påbörjade bostäder (fler- och småhus)", "antal", "Q", "SCB TAB4572",
         scb_sum("TAB4572", "Hustyp", Region="00", ContentsCode="BO0101A4"), 60, revised=True,
         link="Byggcykeln och byggkostnadstryck."),
    Spec("rent_change", "bostad_kredit", "Hyresförändring, hyresrätter", "% per år", "A", "SCB TAB6051",
         scb("TAB6051", Region="00", ContentsCode="000005VT"), -60,
         link="Hyror är en stor och trög del av KPIF. Förhandlas i förväg.",
         note="Publiceras under året (t.ex. okt) – därför negativ fördröjning mot årets slut."),

    # ---------------- Businesses
    Spec("nier_barometer", "foretag", "Barometerindikatorn (KI)", "index, 100 = normalt", "M", "KI",
         konj("KonjBar/indikatorer/Indikatorm.px", Indikator="KIFI"), 3, revised=True,
         link="Samlad bild av efterfrågeläget."),
    Spec("nier_conf_services", "foretag", "Konfidensindikator tjänstesektorn", "index, 100 = normalt", "M", "KI",
         konj("KonjBar/indikatorer/Indikatorm.px", Indikator="BTJA"), 3, revised=True,
         link="Tjänsteefterfrågan → tjänstepriser."),
    Spec("nier_conf_trade", "foretag", "Konfidensindikator handeln", "index, 100 = normalt", "M", "KI",
         konj("KonjBar/indikatorer/Indikatorm.px", Indikator="BHAN"), 3, revised=True,
         link="Handelns läge → varupriser."),
    Spec("nier_conf_households", "hushall", "Hushållens konfidensindikator", "index, 100 = normalt", "M", "KI",
         konj("KonjBar/indikatorer/Indikatorm.px", Indikator="bhus"), 3, revised=True,
         link="Hushållens framtidstro → konsumtion."),
    Spec("nier_capacity_util_mfg", "foretag", "Kapacitetsutnyttjande industrin", "%", "Q", "KI",
         konj("KonjBar/ftgkvartal/Barindq.px", **{"Bransch (SNI 2007)": "BTVI", "Fråga": "104", "Serie": "O"}), 3,
         link="Resursutnyttjande (outputgap)."),
    Spec("nier_labour_shortage", "arbetsmarknad", "Brist på arbetskraft, näringslivet", "andel %", "Q", "KI",
         konj("KonjBar/ftgkvartal/Bartotq.px", **{"Bransch": "BTOT", "Fråga": "brip", "Serie": "O"}), 3,
         link="Lönetryck."),
    Spec("nier_firm_infl_exp_old", "foretag", "Företagens förväntade inflation 12 mån (gammal metod)", "%", "Q", "KI",
         konj("KonjBar/ftgkvartal/Bartotq.px", **{"Bransch": "BTOT", "Fråga": "302", "Serie": "O"}), 3,
         link="Inflationsförväntningar styr prissättning.", note="Metodbyte 2026K4, skarvas inte ihop med ny metod."),
    Spec("nier_firm_infl_exp_new", "foretag", "Företagens förväntade inflation 12 mån (ny metod)", "%", "Q", "KI",
         konj("KonjBar/ftgkvartal/Bartotq.px", **{"Bransch": "BTOT", "Fråga": "303", "Serie": "O"}), 3,
         link="Som ovan, från 2026K4."),
    Spec("bankruptcies", "foretag", "Konkurser, antal (alla branscher)", "antal", "M", "Tillväxtanalys",
         _bankruptcies, 10, link="Finansiell stress och svag efterfrågan."),
    Spec("ipi_yy", "foretag", "Industriproduktion (B–D), årstakt", "%", "M", "SCB TAB1872",
         scb("TAB1872", SNI2007="B-D", ContentsCode="NV0402AZ"), 45, revised=True, link="Varusidans aktivitet."),
    Spec("service_prod_idx", "foretag", "Tjänsteproduktionsindex (ej kalenderjusterat)", "index", "M", "SCB TAB3854",
         scb("TAB3854", SNI2007="45-63+69-96", ContentsCode="HA0104A5"), 45, revised=True,
         link="Tjänsteefterfrågan."),
    Spec("industry_orders_yy", "foretag", "Orderingång industrin, årstakt", "%", "M", "SCB TAB1710",
         scb("TAB1710", Marknad="TOTALA", SNI2007="B+C", ContentsCode="NV0501BX"), 45, revised=True,
         link="Ledande indikator för varuefterfrågan."),
]


# Series added by separate modules (one per job), appended here so every tool sees them.
from kpif_nowcast import catalog_af  # noqa: E402

CATALOG += catalog_af.specs()

from kpif_nowcast import catalog_prices  # noqa: E402

CATALOG += catalog_prices.specs()

from kpif_nowcast import catalog_travel  # noqa: E402

CATALOG += catalog_travel.specs()
from kpif_nowcast import catalog_rents  # noqa: E402

CATALOG += catalog_rents.specs()
from kpif_nowcast import catalog_prospera  # noqa: E402

CATALOG += catalog_prospera.specs()
from kpif_nowcast import catalog_el  # noqa: E402

CATALOG += catalog_el.specs()
from kpif_nowcast import catalog_fx  # noqa: E402

CATALOG += catalog_fx.specs()

# County series (K4): in the observation table and the docs, but kept out of CATALOG so that the national
# candidate lists (j3_screen, k2_ml) and the national dashboard do not change.
from kpif_nowcast import catalog_region  # noqa: E402

REGIONAL = catalog_region.specs()
ALL = CATALOG + REGIONAL


def by_key() -> dict[str, Spec]:
    return {s.key: s for s in ALL}


def to_markdown(table: pd.DataFrame | None = None) -> str:
    """The catalog as Markdown, grouped by area, with coverage from the observation table."""
    from kpif_nowcast import observations as obs

    table = obs.load() if table is None else table
    lines = ["# Datakatalog", "",
             f"{len(ALL)} serier: {len(CATALOG)} nationella och {len(REGIONAL)} länsserier. "
             "Genererad av `python -m kpif_nowcast.catalog`.", ""]
    for area, title in AREAS.items():
        if area == "region":
            continue
        specs = [s for s in CATALOG if s.area == area]
        if not specs:
            continue
        lines += [f"## {title}", "", "| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |",
                  "|---|---|---|---|---|---|---|---|"]
        for s in specs:
            t = table[table["series"] == s.key]["period"]
            span = f"{t.min()}–{t.max()}" if len(t) else "–"
            lines.append(f"| `{s.key}` | {s.label} | {s.freq} | {span} | {s.lag_days} d | "
                         f"{'ja' if s.revised else 'nej'} | {s.source} | {s.link} |")
        lines.append("")
    return "\n".join(lines + _regional_markdown(table))


def _regional_markdown(table: pd.DataFrame) -> list[str]:
    """County series: one row per measure, then every county series and its span."""
    from kpif_nowcast.catalog_region import MEASURES, NAMES, NATIONAL, series_key

    lines = [f"## {AREAS['region']}", "",
             "En serie per mått och län: `region_<mått>_<länskod>` (01 Stockholm … 25 Norrbotten, 00 riket). "
             "Bara deskriptivt, ingår inte i de nationella kandidatlistorna. Kvalitet: `docs/auto2/k4/kvalitet.md`.", "",
             "| Mått | Serie | Frekv. | Från–till (riket) | Län | Fördröjning | Rev. | Källa | Anmärkning |",
             "|---|---|---|---|---|---|---|---|---|"]
    spans = {}
    for s in REGIONAL:
        t = table[table["series"] == s.key]["period"]
        spans[s.key] = f"{t.min()}–{t.max()}" if len(t) else "–"
    for m in MEASURES:
        n = sum(1 for c in m.codes if c != NATIONAL and spans[series_key(m.key, c)] != "–")
        lines.append(f"| `region_{m.key}_*` | {m.label} | {m.freq} | {spans[series_key(m.key, NATIONAL)]} | {n} | "
                     f"{m.lag_days} d | {'ja' if m.revised else 'nej'} | {m.source} | {m.note} |")
    lines += ["", "### Länsserier: täckning per län", "",
              "| Kod | Län | " + " | ".join(f"`{m.key}`" for m in MEASURES) + " |",
              "|---|---|" + "---|" * len(MEASURES)]
    for c in NAMES:
        cells = [spans[series_key(m.key, c)] if c in m.codes else "" for m in MEASURES]
        lines.append(f"| {c} | {NAMES[c]} | " + " | ".join(cells) + " |")
    lines.append("")
    return lines


if __name__ == "__main__":
    md = to_markdown()
    path = Path(__file__).resolve().parents[2] / "docs" / "datakatalog.md"
    path.write_text(md + "\n", encoding="utf-8")
    print(md)
