"""L1: calendar of administered prices (taxes, VAT, public fees) and the suggested manual adjustment.

Hand-curated metadata, not fetched data. Documentation and sources: docs/administrerade-priser.md.

The calendar extends K13's tax events (`k13_tax.EVENTS`, docs/skattekalender.md) without duplicating them:
K13 events are converted on the fly (`k13_events`), and `ADMIN_EVENTS` holds what K13 does not cover
(fees, subsidies, regulation, older taxes, 2027-2028). `k13_tax.EVENTS` is not modified, so K13's
registered variants stay reproducible.

Effect `pe`: estimated effect on KPIF m/m in percentage points, one of
- "scb_ks":     SCB's mechanical KS calculation (KPIF m/m - KPIF-KS m/m, energy/non-energy part as in K13);
- "weight_x_change": KPIF weight of the COICOP post (SCB KPIF2020COICOPM, per mille) x assumed price change;
- "observed":   weight x SCB's measured m/m change of the post in the event month (history only);
- "assumption": stated in `method_note`.

Kinds:
- "one_off": new level from `month` (also permanent changes: the model cannot see the step);
- "end":     a temporary change ends (reversal);
- "recurring": a yearly change (January fees, indexation). The component model's 5-year seasonal mean
  already carries a normal year, so only `pe - normal_pe` enters the suggestion, and only when both are known.

Leakage rule (as K13): an event is suggested for target month t only if `decided` < deadline(t) = day 4 of
t+1. Events without a decision (`decided=None`) are listed but never suggested.

The live main model's forecast (`forecast.py --adjust`) is in y/y; the m/m sum is converted with
index[t-1] / index[t-12] when KPIF data is available (else factor 1).

Run: python -m kpif_nowcast.admin_calendar 2026-12          (suggestion for the monthly routine)
     python -m kpif_nowcast.admin_calendar --table          (markdown table of all events, for the doc)
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date

import pandas as pd

from kpif_nowcast.k13_tax import EVENTS as K13_EVENTS
from kpif_nowcast.k13_tax import TaxEvent
from kpif_nowcast.riksbank_benchmark import deadline

CURATED = date(2026, 11, 23)  # last update of the calendar (no event can be decided after this)
VERIFIED_PREFIX = ("2026-11-23", "ej verifierad", "delvis")  # how the `verified` field must start (L1b)
KINDS = ("one_off", "end", "recurring")
METHODS = ("scb_ks", "weight_x_change", "observed", "assumption")
K13_COICOP = {"energy": "07.2.2", "food": "01"}  # K13 component -> COICOP 2018 post
K13_COICOP_BY_MONTH = {"2026-01": "04.5.1"}  # the 2026-01 K13 event is the electricity tax
POST = {"07.2.2": "Bränslen och smörjmedel", "04.5.1": "Elektricitet", "01": "Livsmedel och alkoholfria drycker"}
DOC = "docs/skattekalender.md"
K13_LABEL_SV = {  # Swedish labels for the doc and the --note (K13's own labels are English)
    "2022-05": "Tillfälligt sänkt energiskatt på bensin och diesel 1,05 kr/l, maj–sep 2022",
    "2022-10": "Sänkningen från maj 2022 upphör 30 sep",
    "2026-01": "Sänkt energiskatt på el (BP 2026)",
    "2026-04": "Matmomsen 12 → 6 % 1 apr 2026–31 dec 2027",
    "2026-05": "Tillfälligt sänkt energiskatt på bensin och diesel till EU:s miniminivå, maj–sep 2026",
    "2026-07": "Tillfälligt sänkt koldioxidskatt på bensin och diesel 2,40 kr/l (3,00 inkl. moms), jul–nov 2026",
    "2026-10": "Energiskattesänkningen från maj 2026 upphör 30 sep",
    "2026-12": "Koldioxidskattesänkningen upphör 30 nov 2026 (ingen förlängning i BP 2027)",
}
# L1b primary-source check of K13's events (2026-11-23). k13_tax.EVENTS is not modified; where K13's decision
# date is earlier than the actual decision, the calendar uses the verified date (K13_DECIDED_FIX).
RD = "https://data.riksdagen.se/dokument/"
RDS = "https://data.riksdagen.se/dokumentstatus/"
SKV_FUEL = "https://www.skatteverket.se/foretag/skatterochavdrag/punktskatter/energiskatter/skattpabransle.4.15532c7b1442f256bae5e56.html"
K13_DECIDED_FIX = {"2026-04": date(2026, 2, 25)}  # food VAT: prop. 2025/26:55, bet. 2025/26:SkU9, voted 2026-02-25
K13_SOURCE = {
    "2022-05": RD + "H903221 " + RDS + "H901FiU39",
    "2022-10": RD + "H903221 " + RDS + "H901FiU39",
    "2026-01": RD + "HD031d2 " + RDS + "HD01FiU1",
    "2026-04": RD + "HD0355 " + RDS + "HD01SkU9",
    "2026-05": RD + "HD03236 " + RDS + "HD01FiU48 " + SKV_FUEL,
    "2026-07": RD + "HD03275 " + RDS + "HD01FiU47 " + SKV_FUEL,
    "2026-10": RD + "HD03236 " + RDS + "HD01FiU48 " + SKV_FUEL,
    "2026-12": RD + "HD03275 " + RDS + "HD01FiU47 " + SKV_FUEL + " " + RD + "HE031d2",
}
K13_VERIFIED = {
    "2022-05": "2026-11-23: prop. 2021/22:221 läst; riksdagsbeslut bet. 2021/22:FiU39 27 apr 2022 (dokumentstatus)",
    "2022-10": "2026-11-23: solnedgång 30 sep 2022 i prop. 2021/22:221 (beslut 27 apr 2022); K13:s källa Företagarna "
               "(sekundär, inte nåbar) ersatt",
    "2026-01": "2026-11-23: prop. 2025/26:1 avsnitt 13.12.2 (36,0 öre/kWh 2026) läst; beslut bet. 2025/26:FiU1 "
               "26 nov 2025",
    "2026-04": "2026-11-23: K13:s beslutsdatum 2025-11-30 är fel. BP 2026 bara aviserade; prop. 2025/26:55 "
               "(25 nov 2025), riksdagsbeslut bet. 2025/26:SkU9 25 feb 2026, t.o.m. 31 dec 2027. Före deadline "
               "för 2026-04 (4 maj), så K13:s variant påverkas inte",
    "2026-05": "2026-11-23: beslut bet. 2025/26:FiU48 22 apr 2026; Skatteverket: bensin energiskatt 1,52 → 0,70 kr/l "
               "1 maj–30 sep 2026",
    "2026-07": "2026-11-23: beslut bet. 2025/26:FiU47 17 jun 2026; Skatteverket: koldioxidskatt bensin −2,40 kr/l "
               "1 jul–30 nov 2026",
    "2026-10": "2026-11-23: Skatteverket: bensin 1,57 → 2,39 kr/l skatt från 1 okt 2026",
    "2026-12": "2026-11-23: Skatteverket: bensin miljöklass 1 2,39 → 4,79 kr/l skatt, diesel 3 961 kr/m³ från "
               "1 dec 2026; inget förlängningsförslag i prop. 2026/27:1 (12 nov) eller höständringsbudgeten "
               "(prop. 2026/27:2), inga sådana propositioner eller betänkanden i riksdagens dokumentlista",
}

# Transit cards: SCB 07.3.5 Kombinerad persontransport, weight 5.91 per mille (2026), m/m -26.4 % in 2026-07
# (monthly cards 44 % of the post, halved). Reversal split by population share of the regions that return
# in each month (SCB BE0101N1, 2024): south (Skåne, Blekinge, Jönköping, Kalmar, Kronoberg) 22.7 %,
# Halland 3.3 %, other regions 74.0 %. Assumption: SCB's regional weights follow population.
TRANSIT_PE = round(-5.91 * 26.4 / 1000, 3)  # -0.156
SHARE_SOUTH, SHARE_HALLAND = 0.2271, 0.0326
SHARE_REST = 1 - SHARE_SOUTH - SHARE_HALLAND
SHARE_VG = 0.1674  # Västra Götaland, inside SHARE_REST
SCB_JULY_2026 = ("https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/"
                 "konsumentprisindex-kpi/produktrelaterat/aktuellt/"
                 "hantering-i-kpi-och-relaterade-matt-av-reformer-som-infors-i-juli-2026/")
SCB_KPI = ("https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/"
           "konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-{}/")
SCB_COICOP_TABLE = "https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__PR__PR0101__PR0101G/KPIF2020COICOPM/"
TT_TRANSIT = "https://www.tv4.se/artikel/35OZ9s7vhA6u63p2WPj0ph/da-blir-manadskortet-dubbelt-sa-dyrt-i-ditt-laen"
SL_DEC = ("https://www.dagensps.se/privatekonomi/"
          "manadskortet-dubbelt-sa-dyrt-2027-men-har-kan-du-behalla-rabatten-i-januari/")
GOV_TRANSIT = ("https://www.regeringen.se/pressmeddelanden/2026/06/"
               "halverade-priser-i-kollektivtrafiken--nu-har-regeringen-beslutat-om-reglerna/")


@dataclass(frozen=True)
class AdminEvent:
    month: str  # first month the new price is measured (YYYY-MM)
    coicop: str  # SCB COICOP 2018 post, as in KPIF2020COICOPM (e.g. "07.3.5")
    post: str  # post name (Swedish)
    kind: str  # one_off | end | recurring
    pe: float | None  # effect on KPIF m/m, pp (None: size unknown)
    method: str  # scb_ks | weight_x_change | observed | assumption
    decided: date | None  # decision, upper bound ("senast"); None = not decided
    label: str  # what happens (Swedish)
    source: str  # link(s), space separated
    weight: float | None = None  # KPIF weight of the post, per mille (SCB), when the method uses it
    change_pct: float | None = None  # price change of the post, %, when the method uses it
    normal_pe: float | None = None  # recurring: normal effect already in the model's season, pp
    in_ks: bool = False  # cleaned by SCB in KPIF-KS
    origin: str = "L1"  # "L1" or "K13" (converted from k13_tax.EVENTS)
    method_note: str = ""
    verified: str = ""  # L1b primary-source check: "2026-11-23: <how>", "delvis: ..." or "ej verifierad: <why>"

    @property
    def period(self) -> pd.Period:
        return pd.Period(self.month, "M")

    @property
    def suggest_pe(self) -> float:
        """The part of the effect the live model cannot see."""
        if self.pe is None:
            return 0.0
        if self.kind == "recurring":
            return self.pe - self.normal_pe if self.normal_pe is not None else 0.0
        return self.pe


def known(ev: AdminEvent, t: pd.Period) -> bool:
    """Leakage rule: decided before the deadline of target month t (same rule as k13_tax.known)."""
    return ev.decided is not None and pd.Timestamp(ev.decided) < deadline(t)


ADMIN_EVENTS: list[AdminEvent] = [
    # ---------------------------------------------------------------- history 2015-2025
    AdminEvent("2016-01", "07.2.2", "Bränslen och smörjmedel", "one_off", round(31.80 * 4.4 / 1000, 3),
               "weight_x_change", date(2015, 11, 25),
               "Höjd energiskatt på bensin (+48 öre/l) och diesel (+53 öre/l), BP 2016",
               RD + "H3031 " + RDS + "H301FiU1 "
               "https://www.regeringen.se/rattsliga-dokument/departementsserien-och-promemorior/2015/08/"
               "ytterligare-skattehojningar-pa-vissa-drivmedel/",
               weight=31.80, change_pct=4.4, in_ks=True,
               method_note="0,48 kr × 1,25 moms på ~13,5 kr/l ≈ +4,4 %; SCB KS 2016-01 totalt +0,30 inkl. januarihöjningar",
               verified="2026-11-23: prop. 2015/16:1 (+48/+53 öre/l från 1 jan 2016) läst; beslut bet. 2015/16:FiU1 "
                        "25 nov 2015. L1:s länk bet. 2015/16:SkU18 var fel (motionsbetänkande, beslut 9 mar 2016)"),
    AdminEvent("2016-01", "07.2.4", "Andra tjänster för personliga transportmedel", "one_off", 0.05,
               "assumption", date(2015, 12, 31),
               "Höjd trängselskatt i Stockholm (max 60 → 105 kr/dag) och ny avgift på Essingeleden",
               "https://www.transportstyrelsen.se/globalassets/global/vag/trangselskatt/"
               "infofolder-forandringar-trangselskatt-stockholm-.pdf",
               weight=8.98, change_pct=3.1,
               method_note="posten +3,1 % mot normalt −2 % i januari: (3,1+2,0) × 8,98 ‰ ≈ +0,05",
               verified="ej verifierad: transportstyrelsen.se inte nåbar från miljön och riksdagsbeslutet inte hittat; "
                        "L1:s länk bet. 2015/16:SkU18 var fel (beslut 9 mar 2016) och är borttagen"),
    AdminEvent("2017-07", "05.3.1", "Elektronik och vitvaror (flera poster)", "one_off", 0.116, "scb_ks",
               date(2016, 11, 24), "Ny kemikalieskatt på viss elektronik (lag 2016:1067), från 1 juli 2017",
               RD + "sfs-2016-1067 https://www.skatteverket.se/foretag/skatterochavdrag/punktskatter/kemikalieskatt/"
               "nyareglerforattdeklarerakemikalierivisselektronik.4.7361717f187e3364e41101b.html",
               in_ks=True, method_note="SCB KS 2017-07 (+0,116) tillskrivs hela skatten; inga andra kända skatteändringar",
               verified="2026-11-23: SFS 2016:1067 utfärdad 24 nov 2016 (riksdagens SFS-databas); storleken är SCB:s KS"),
    AdminEvent("2018-04", "07.3.3", "Persontransport med flyg", "one_off", 0.041, "scb_ks", date(2017, 11, 30),
               "Ny flygskatt (lag 2017:1200), från 1 april 2018",
               "https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/"
               "lag-20171200-om-skatt-pa-flygresor_sfs-2017-1200/", in_ks=True,
               method_note="SCB KS 2018-04",
               verified="2026-11-23: SFS 2017:1200 utfärdad 30 nov 2017 (riksdagens SFS-databas)"),
    AdminEvent("2019-01", "08.3.9", "Andra informations- och kommunikationstjänster", "one_off", 0.0,
               "assumption", date(2018, 11, 14),
               "Radio- och tv-avgiften ersätts av public service-avgift via skatten; SCB länkar ut avgiften utan "
               "priseffekt", SCB_KPI.format("januari-2019") + " https://www.scb.se/contentassets/"
               "d1f974c3e55d4ff39fa6314fc211980c/andringar_i_kpi_fran_2019_v002.pdf",
               method_note="SCB: utanför KPI:s målpopulation, utlänkad utan prispåverkan (vikten 11,2 → 6,0 ‰)",
               verified="2026-11-23: prop. 2017/18:261, riksdagsbeslut bet. 2018/19:KrU2 14 nov 2018 (dokumentstatus)"),
    AdminEvent("2019-07", "06.2.2", "Öppen tandvård", "one_off", round(9.30 * -20.1 / 1000, 3), "observed",
               date(2019, 8, 14),
               "Ny metod för allmänt tandvårdsbidrag (ATB) i KPI: tandvård faller varje juli (återkommande från 2020)",
               SCB_KPI.format("juli-2019"), weight=9.30, change_pct=-20.1, in_ks=True,
               method_note="metodbyte hos SCB, inte ett politiskt beslut; beslut = SCB:s publicering 14 aug 2019 (efter "
                           "deadline för 2019-07, så aldrig föreslagen). Juli −12 till −20 % varje år sedan dess",
               verified="2026-11-23: SCB:s KPI-nyhet juli 2019 (länken fungerar)"),
    AdminEvent("2024-01", "07.2.2", "Bränslen och smörjmedel", "one_off", round(25.96 * -10.8 / 1000, 3),
               "observed", date(2023, 11, 30),
               "Reduktionsplikten sänks till 6 % (prop. 2023/24:28) och sänkt drivmedelsskatt; ingen skatt för "
               "reduktionsplikten, så den rensas inte i KS",
               "https://data.riksdagen.se/dokument/HB01MJU5 https://www.konj.se/media/1dojjkax/"
               "specialstudie-104-sankning-av-reduktionsplikt.pdf",
               weight=25.96, change_pct=-10.8,
               method_note="hela drivmedelsposten −10,8 % i jan 2024 (övre gräns: inkluderar marknadspris); "
                           "huvudmodellen ser bara Brent i SEK",
               verified="2026-11-23: bet. 2023/24:MJU5 beslut 30 nov 2023 (dokumentstatus); Skatteverket: bensin "
                        "6,31 → 5,71 kr/l skatt 2023 → 2024. konj.se-länken inte nåbar"),
    AdminEvent("2025-05", "04.3", "Underhåll, reparation och säkerhet avseende bostaden (ROT)", "one_off", -0.176,
               "scb_ks", date(2025, 5, 7),
               "ROT-avdraget 30 → 50 % 12 maj–31 dec 2025 (finns i K13:s kalender, inte i EVENTS)",
               SCB_KPI.format("maj-2025") + " " + RD + "HC03156 " + RDS + "HC01FiU32", in_ks=True,
               verified="2026-11-23: L1:s datum 2025-04-30 var för tidigt. Prop. 2024/25:156 (10 apr 2025), "
                        "riksdagsbeslut bet. 2024/25:FiU32 7 maj 2025 (dokumentstatus); före deadline för 2025-05",
               method_note="SCB KS icke-energidel 2025-05 (k13_tax.ks_parts; −0,189 i tax_effects är tax_xe_own, "
                           "KPIF-XE-skala). Reparationstjänsterna (04.3.2) publiceras inte; publicerade 04.3 är bara "
                           "material (= 04.3.1, +0,8 % i maj)"),
    AdminEvent("2025-07", "06.1.1", "Läkemedel", "one_off", round(10.91 * 1.0 / 1000, 3), "observed",
               date(2025, 5, 22), "Höjt högkostnadsskydd för läkemedel (prop. 2024/25:144)",
               "https://data.riksdagen.se/dokument/HC03144 " + SCB_KPI.format("juli-2025"),
               weight=10.91, change_pct=1.0,
               verified="2026-11-23: riksdagsbeslut bet. 2024/25:SoU27 22 maj 2025 (dokumentstatus)"),
    AdminEvent("2025-07", "07.2.2", "Bränslen och smörjmedel", "one_off", 0.0, "assumption", date(2025, 5, 22),
               "Energiskatten på bensin och diesel −32 öre/l samtidigt som reduktionsplikten höjs (+32 öre/l), "
               "1 jul 2025; nettoeffekt på pumppriset ≈ 0",
               RD + "HC03131 " + RDS + "HC01MJU17 " + SKV_FUEL, in_ks=True,
               method_note="prop. 2024/25:131: skattesänkningen väger upp reduktionspliktens prishöjning. SCB:s KS "
                           "energidel 2025-07 −0,05 ser bara skatten, så KS-baserade justeringar överskattar effekten",
               verified="2026-11-23: L1b-tillägg. Skatteverket: bensin 5,11 → 4,79 kr/l skatt 1 jul 2025; prop. "
                        "2024/25:131 läst; beslut bet. 2024/25:MJU17 22 maj 2025"),
    # ---------------------------------------------------------------- 2026
    AdminEvent("2026-01", "06.2.2", "Öppen tandvård", "one_off", round(8.77 * -21.2 / 1000, 3), "observed",
               date(2025, 12, 8), "Tandvårdsstöd för 67+ (betalar 10 % av referenspriset), från 1 jan 2026",
               "https://www.regeringen.se/pressmeddelanden/2025/12/tandvarden-for-aldre-blir-billigare-den-1-januari-2026/ "
               + SCB_KPI.format("januari-2026"), weight=8.77, change_pct=-21.2,
               method_note="normal januari +2 till +4 %, så effekten är snarast −0,2 till −0,22",
               verified="2026-11-23: regeringen 8 dec 2025: riksdagen röstade 3 dec, förordningarna beslutade 8 dec"),
    AdminEvent("2026-01", "04.3", "Underhåll, reparation och säkerhet avseende bostaden (ROT)", "end", 0.037,
               "scb_ks", date(2025, 5, 7), "ROT 50 % upphör 31 dec 2025 (solnedgång i lagen)",
               SCB_KPI.format("januari-2026") + " " + RDS + "HC01FiU32", in_ks=True,
               verified="2026-11-23: solnedgång i prop. 2024/25:156, beslut bet. 2024/25:FiU32 7 maj 2025",
               method_note="hela icke-energidelen av SCB KS 2026-01 (alla januariändringar), så övre gräns för "
                           "ROT-slutet om övriga ändringar var ≥ 0. Återgången blev mycket mindre än startens −0,176; "
                           "orsaken är inte verifierad (osäker)"),
    AdminEvent("2026-07", "07.3.5", "Kombinerad persontransport", "one_off", TRANSIT_PE, "observed",
               date(2026, 6, 25), "Halverat pris på månadskort i kollektivtrafiken (statsbidrag) 1 jul–dec 2026",
               SCB_JULY_2026 + " " + GOV_TRANSIT + " " + RD + "sfs-2026-1391", weight=5.91, change_pct=-26.4,
               method_note="mekaniskt 44 % × −50 % = −22 % (−0,130); uppmätt −26,4 %. Indirekt subvention, rensas inte i KS",
               verified="2026-11-23: anslag bet. 2025/26:FiU47 17 jun 2026; SFS 2026:1391 utfärdad 25 jun 2026 "
                        "(bidrag för kort aktiverade senast 2 dec eller giltiga t.o.m. 31 dec 2026)"),
    AdminEvent("2026-07", "10.1.0", "Förskola", "one_off", round(2.82 * -19.9 / 1000, 3), "observed",
               date(2026, 6, 30), "Fribelopp i maxtaxan för förskola (permanent)", SCB_JULY_2026 + " " + RD + "HD031d18",
               weight=2.82, change_pct=-19.9, method_note="taxeändringar rensas inte i KS",
               verified="delvis: BP 2026 utgiftsområde 16 aviserar fribeloppet, anslaget beslutat 16 dec 2025 (bet. "
                        "2025/26:UbU1); förordningen inte hittad. Storleken är SCB:s uppmätta juli 2026"),
    AdminEvent("2026-07", "13.3.0", "Socialt skydd (fritidshem)", "one_off", round(10.07 * -3.6 / 1000, 3),
               "observed", date(2026, 6, 30), "Fribelopp i maxtaxan för fritidshem (permanent)",
               SCB_JULY_2026 + " " + RD + "HD031d18", weight=10.07, change_pct=-3.6,
               verified="delvis: som förskolan (BP 2026 UO16, bet. 2025/26:UbU1 16 dec 2025)"),
    AdminEvent("2026-07", "09.4.6", "Rekreations- och sporttjänster", "one_off", None, "assumption",
               date(2026, 5, 20), "Dansbandsmoms 25 → 6 % (rensas i KS, försumbar)",
               SCB_JULY_2026 + " " + RDS + "HD01SkU25", in_ks=True,
               verified="2026-11-23: prop. 2025/26:109, beslut bet. 2025/26:SkU25 20 maj 2026 (dokumentstatus)"),
    AdminEvent("2026-11", "07.3.5", "Kombinerad persontransport", "end", round(-TRANSIT_PE * SHARE_SOUTH, 3),
               "assumption", date(2026, 10, 28),
               "Månadskort åter fullpris från 3 nov i Skåne, Blekinge, Jönköping, Kalmar och Kronoberg",
               TT_TRANSIT, weight=5.91,
               method_note="+0,156 (juli omvänt) × befolkningsandel 22,7 %",
               verified="ej verifierad: TV4/TT och regionernas webbplatser inte nåbara från miljön; SFS 2026:1391 "
                        "tillåter halvpris till 2 dec, så regionerna får sluta tidigare"),
    AdminEvent("2026-12", "07.3.5", "Kombinerad persontransport", "end", round(-TRANSIT_PE * SHARE_REST, 3),
               "assumption", date(2026, 10, 28),
               "Månadskort åter fullpris från 3 dec i övriga regioner (SL och Västtrafik: sista köpdag 2 dec)",
               TT_TRANSIT + " " + SL_DEC, weight=5.91,
               method_note="+0,156 × 74,0 % (alla utom söder och Halland). Förlänger Västtrafik till 29 dec flyttas "
                           "+0,026 till 2027-01. Risk: SL-abonnemang dras med halvpris för december 26 nov och "
                           "30-dagarskort aktiverade 2 dec gäller till ~1 jan; prisar SCB efter giltighetstid hamnar "
                           "en del i januari",
               verified="delvis: sista dag 2 dec stämmer med SFS 2026:1391 4 § (kort aktiverade senast 2 dec 2026); "
                        "regionernas egna besked (SL, Västtrafik) inte nåbara från miljön"),
    # ---------------------------------------------------------------- 2027-2028
    AdminEvent("2027-01", "07.3.5", "Kombinerad persontransport", "end", round(-TRANSIT_PE * SHARE_HALLAND, 3),
               "assumption", date(2026, 10, 28),
               "Halland: rabatterat kort kan aktiveras till 1 jan, fullpris i januari", TT_TRANSIT, weight=5.91,
               method_note="+0,156 × 3,3 %",
               verified="ej verifierad: hallandstrafiken.se och TV4 inte nåbara. Obs: SFS 2026:1391 ger bara bidrag "
                        "för kort aktiverade senast 2 dec eller giltiga t.o.m. 31 dec, så aktivering till 1 jan är "
                        "regionens egen kostnad"),
    AdminEvent("2027-01", "07.3.5", "Kombinerad persontransport", "end", round(-TRANSIT_PE * SHARE_VG, 3),
               "assumption", None,
               "Västtrafik: förlängning av halva priset till 29 dec (återremitterad 6 okt 2026, ej beslutad)",
               "https://via.tt.se/pressmeddelande/4582212/regionfullmaktige-6-oktober-2026?lang=sv", weight=5.91,
               method_note="om beslutad: flytta +0,026 från 2026-12 hit",
               verified="ej verifierad: via.tt.se och vgregion.se inte nåbara från miljön"),
    AdminEvent("2027-01", "13.3.0", "Socialt skydd (äldreomsorg, maxtaxor)", "recurring",
               round(10.07 * 1.0 / 1000, 3), "weight_x_change", date(2026, 9, 24),
               "Prisbasbeloppet 2027 +0,7 % (59 600 kr); maxtaxor i omsorgen följer det",
               "https://www.regeringen.se/pressmeddelanden/2026/09/prisbasbeloppfor-2027-faststallt/ "
               + RD + "sfs-2026-1779",
               verified="2026-11-23: SFS 2026:1779 utfärdad 24 sep 2026 (59 600 kr, förhöjt 60 900 kr); regeringen: "
                        "+0,7 % mot 2026",
               weight=10.07, change_pct=1.0, normal_pe=0.041,
               method_note="posten följer prisbasbeloppet i januari (pbb +0,6/+8,7/+9,1/+0,7 % gav 2021 +0,6, 2023 +4,7, "
                           "2024 +11,2, 2026 +1,2 %), antag +1,0 %; "
                           "normal = snitt av januaribidragen 2022–2026 (ungefärlig: modellen avtrendar med "
                           "12-månaderssnittet, skillnad ≈ ±0,005 pe). Posten innehåller barnomsorg (13.3.0.1), vars "
                           "maxtaxa inte följer prisbasbeloppet, men hela vikten skalas med +1,0 %"),
    AdminEvent("2027-01", "04.5.1", "Elektricitet", "recurring", 0.004, "assumption", date(2026, 11, 12),
               "Energiskatt på el 36,0 → ~36,2 öre/kWh (ordinarie KPI-indexering; förslaget att låsa på 36,0 "
               "lades inte i BP 2027)",
               "https://www.regeringen.se/regeringens-politik/skatt-och-tull/"
               "skatteforslag-som-remitterats-infor-hostbudgeten-2027/ " + RD + "HE031d2 "
               "https://toreenergi.se/energiskatt-2027/", in_ks=True,
               method_note="0,25 öre inkl. moms på ~180 öre/kWh ≈ +0,14 % × 31,8 ‰; normal indexering, säsongen har den",
               verified="delvis: remissen (18 maj 2026) föreslog 36,0 öre/kWh 2027 men prop. 2026/27:1 (12 nov) "
                        "lägger bara inkomstskatteförslag, så indexeringen i 11 kap. 3 § LSE gäller (regeringen "
                        "fastställer före november månads utgång). Nivån 36,2 och SFS 2026:1859 kommer från "
                        "toreenergi.se (inte nåbar); Skatteverket visar ännu bara 2026"),
    AdminEvent("2027-01", "07.2.2", "Bränslen och smörjmedel", "recurring", 0.016, "assumption",
               date(2026, 11, 23), "Ordinarie indexering av skatt på bensin (+10 öre/l) och diesel (+8,5 öre/l)",
               SKV_FUEL, in_ks=True,
               method_note="12,5 öre inkl. moms på ~20 kr/l ≈ +0,6 % × 26,4 ‰; normal indexering",
               verified="2026-11-23: Skatteverket: bensin miljöklass 1 4,79 → 4,89 kr/l, diesel miljöklass 1 "
                        "3 961 → 4 046 kr/m³ från 1 jan 2027. Beslutsdatum = dag för kontrollen (övre gräns); "
                        "hurbra.se (sekundär) ersatt"),
    AdminEvent("2027-01", "02.3", "Tobak", "one_off", 0.0, "assumption", date(2026, 11, 12),
               "Aviserad tobaksskatt +3,5 % utöver indexering genomförs inte (prop. 2026/27:1 tabell 1.5); "
               "bara ordinarie indexering",
               "https://www.regeringen.se/rattsliga-dokument/departementsserien-och-promemorior/2025/11/"
               "hojd-skatt-pa-viss-tobak/ " + RD + "HE031d2", in_ks=True,
               method_note="indexeringen är normal och ligger i säsongen",
               verified="2026-11-23: prop. 2026/27:1 tabell 1.5 och avsnitt 12: 'Höjd skatt på vissa tobaksprodukter' "
                        "bland tidigare aviserade förslag som inte genomförs (−0,32 mdkr). PM 27 nov 2025 läst"),
    AdminEvent("2027-01", "04.5.1", "Elektricitet (elnät)", "recurring", None, "assumption", None,
               "Elnätsavgifter i januari (Ellevio, Vattenfall, E.ON): inga 2027-besked hittade 23 nov 2026; se L5",
               "https://www.svt.se/nyheter/inrikes/elnatsjattarna-hojer-avgiften-kraftigt",
               verified="ej verifierad: ingen samlad primärkälla (se L5); svt.se inte nåbar"),
    AdminEvent("2027-01", "04.4", "Vattenförsörjning (04.4.1), sophämtning (04.4.2) och avlopp (04.4.3)",
               "recurring", None, "assumption", None,
               "Kommunala VA- och avfallstaxor i januari (2024: VA +13,9 %, 2025 +9,8 %, 2026 +6,5 %)",
               SCB_COICOP_TABLE, verified="ej verifierad: 290 kommunala taxebeslut, ingen samlad källa"),
    AdminEvent("2028-01", "01", "Livsmedel och alkoholfria drycker", "end", 0.773, "assumption",
               date(2026, 2, 25), "Matmomsen 6 → 12 % igen (sänkningen gäller t.o.m. 31 dec 2027)",
               RD + "HD0355 " + RDS + "HD01SkU9", in_ks=True, method_note="minus K13:s KS-effekt 2026-04",
               verified="2026-11-23: prop. 2025/26:55 (t.o.m. 31 dec 2027), beslut bet. 2025/26:SkU9 25 feb 2026; "
                        "L1:s datum 2025-11-30 (från K13) var för tidigt"),
]


def k13_events(parts: pd.DataFrame | None = None) -> list[AdminEvent]:
    """K13's tax events in calendar form. End events: minus the realised KS part of the start month when
    `parts` (k13_tax.ks_parts) has it, else minus the start event's pe (same rule as k13_tax.addback)."""
    out = []
    for ev in K13_EVENTS:
        if ev.kind == "start":
            pe, method = ev.pe, "scb_ks"
        else:
            s = pd.Period(ev.start_of, "M")
            v = parts[ev.part].get(s) if parts is not None and ev.part in parts else None
            start: TaxEvent = next(e for e in K13_EVENTS if e.month == ev.start_of)
            pe, method = (-float(v), "scb_ks") if v is not None and pd.notna(v) else (-start.pe, "assumption")
        code = K13_COICOP_BY_MONTH.get(ev.month, K13_COICOP[ev.component])
        decided = K13_DECIDED_FIX.get(ev.month, ev.decided)
        out.append(AdminEvent(ev.month, code, POST[code], "one_off" if ev.kind == "start" else "end", round(pe, 3), method,
                              decided, K13_LABEL_SV.get(ev.month, ev.label), K13_SOURCE.get(ev.month, DOC), in_ks=True,
                              origin="K13", method_note="K13 (k13_tax.EVENTS)",
                              verified=K13_VERIFIED.get(ev.month, "")))
    return out


def all_events(parts: pd.DataFrame | None = None) -> list[AdminEvent]:
    return sorted(k13_events(parts) + ADMIN_EVENTS, key=lambda e: (e.month, e.coicop))


def echo(t: pd.Period, events: list[AdminEvent]) -> float:
    """What past one-off/end events (s < t, known at deadline(t)) add to the live model's forecast for t
    through its 12-month trend and 5-year seasonal mean (baselines.seasonal_trend_additive is linear).
    Information only: not in the suggestion (Johannes' decision on K13, beslutslogg 2026-11-23)."""
    from kpif_nowcast.baselines import seasonal_trend_additive

    past = [e for e in events if e.kind != "recurring" and e.pe and e.period < t and known(e, t)]
    if not past:
        return 0.0
    idx = pd.period_range(min(e.period for e in past) - 72, t, freq="M")
    pulses = pd.Series(0.0, index=idx)
    for e in past:
        pulses[e.period] += e.pe
    return float(seasonal_trend_additive(pulses).get(t, 0.0))


@dataclass
class Suggestion:
    target: pd.Period
    used: list[AdminEvent]
    listed: list[AdminEvent]  # same month, not used (undecided, after deadline, unknown size, recurring normal)
    mm_pe: float
    yy_factor: float
    echo_pe: float

    @property
    def adjust(self) -> float:
        return round(self.mm_pe * self.yy_factor, 2)

    def note(self) -> str:
        parts = [f"{_short(e.label)} {e.suggest_pe:+.3f} ({e.source.split()[0]})" for e in self.used]
        return f"admin_calendar {self.target}: " + "; ".join(parts)


def _short(text: str, n: int = 70) -> str:
    text = re.sub(r"\s+", " ", text)
    return text if len(text) <= n else text[: n - 1] + "…"


def suggest(target: str | pd.Period, events: list[AdminEvent] | None = None,
            index: pd.Series | None = None) -> Suggestion:
    t = pd.Period(target, "M")
    events = all_events() if events is None else events
    month = [e for e in events if e.period == t]
    used = [e for e in month if known(e, t) and e.suggest_pe != 0.0]
    listed = [e for e in month if e not in used]
    factor = 1.0
    if index is not None and len(index):
        last = min(t - 1, index.index.max())  # before t-1 is published: latest 11-month ratio as proxy
        if (last - 11) in index.index:
            factor = float(index[last] / index[last - 11])
    return Suggestion(t, used, listed, sum(e.suggest_pe for e in used), factor, echo(t, events))


def _load_parts_and_index():
    """Realised KS parts and KPIF index from local caches (no network); (None, None) if missing."""
    try:
        from kpif_nowcast.data import load_components, load_kpif, load_tax_effects
        from kpif_nowcast.k13_tax import ks_parts

        return ks_parts(load_tax_effects(), load_components()), load_kpif()["index"]
    except (FileNotFoundError, KeyError, OSError):
        return None, None


def report(s: Suggestion) -> str:
    dl = deadline(s.target).date()
    lines = [f"Administrerade priser för {s.target} (deadline {dl}, händelser beslutade före den)", ""]
    for e in s.used:
        extra = f" (normal {e.normal_pe:+.3f})" if e.kind == "recurring" else ""
        lines.append(f"  {e.suggest_pe:+.3f} pe  {e.coicop:7s} {_short(e.label, 90)}{extra}  [{e.origin}, {e.method}]")
    if not s.used:
        lines.append("  inga beslutade engångshändelser")
    lines.append("")
    lines.append(f"  Summa m/m: {s.mm_pe:+.3f} pe; i årstakt × {s.yy_factor:.3f} = {s.mm_pe * s.yy_factor:+.3f} pe")
    for e in s.listed:
        why = ("ej beslutad" if e.decided is None else "beslut efter deadline" if not known(e, s.target)
               else "storlek okänd" if e.pe is None else "ingen effekt" if e.pe == 0
               else "normal, finns i säsongen")
        size = "?" if e.pe is None else f"{e.pe:+.3f}"
        lines.append(f"  ej med ({why}): {size} pe  {e.coicop} {_short(e.label, 90)}")
    lines.append(f"  Info: eko av tidigare engångshändelser i huvudmodellens trend och säsong: {s.echo_pe:+.3f} pe m/m "
                 f"(ingår inte i förslaget)")
    lines.append("")
    if s.used and s.adjust != 0:
        note = s.note().replace('"', "'")
        lines.append(f'Förslag: python -m kpif_nowcast.forecast --adjust {s.adjust:.2f} --note "{note}"')
    else:
        lines.append("Förslag: ingen justering")
    lines.append("Källor och metod: docs/administrerade-priser.md. Användningen beslutar Johannes.")
    return "\n".join(lines)


def markdown_table(events: list[AdminEvent]) -> str:
    def fmt(x):
        return "?" if x is None else f"{x:+.3f}".replace(".", ",").replace("-", "−")

    rows = ["| Månad | COICOP | Post | Typ | Effekt (pe m/m) | Metod | I KS | Beslut senast | Händelse | Källa | Verifierad |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in events:
        eff = fmt(e.pe) + (f" (normal {fmt(e.normal_pe)})" if e.normal_pe is not None else "")
        links = " ".join(f"[{i + 1}]({u})" for i, u in enumerate(e.source.split())) if e.source != DOC \
            else "[skattekalender](skattekalender.md)"
        if e.origin == "K13":
            links = "[skattekalender](skattekalender.md) " + (links if e.source != DOC else "")
        note = f" {e.method_note}." if e.method_note and e.origin != "K13" else (" (K13)" if e.origin == "K13" else "")
        rows.append(f"| {e.month} | {e.coicop} | {e.post} | {e.kind} | {eff} | {e.method} | "
                    f"{'ja' if e.in_ks else 'nej'} | {e.decided or 'ej beslutad'} | {e.label}.{note} | {links.strip()} | "
                    f"{e.verified or '–'} |")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Suggested manual adjustment from the administered-price calendar")
    p.add_argument("month", nargs="?", help="target month YYYY-MM")
    p.add_argument("--table", action="store_true", help="print the markdown table of all events")
    a = p.parse_args(argv)
    parts, index = _load_parts_and_index()
    events = all_events(parts)
    if a.table:
        print(markdown_table(events))
        return
    if not a.month:
        p.error("give a target month YYYY-MM or --table")
    print(report(suggest(a.month, events, index)))


if __name__ == "__main__":
    main()
