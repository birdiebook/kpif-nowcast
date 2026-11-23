# Status: autonom körning 3 (svensk data där överraskningarna sitter)

**Lås:** orkestrerare (molnsession) 2026-11-23T11:42Z · heartbeat 2026-11-23T13:20Z
**Start:** 2026-11-23 · **Bas:** main @ 129bbb0 · körning 2: STOP (bf11c0a)
**Varianter i körningen:** 0/6 (projektet totalt 51 + 0 = 51) · **Screening:** räknas inte mot taket
**Merge:** klara spår mergas till main av orkestreraren när pytest är grönt · **Brief:** [BRIEF.md](BRIEF.md) · regler: `docs/autonom-korning-2.md` på main, med ändringarna i briefen

**Miljö (avvikelse från briefen):** körningen går i en molncontainer (Linux), inte på `C:\dev`. Worktrees ligger under
`/home/user/kpif-auto3/<spår>`, grenar `auto3/<spår>`. Datan finns inte i containern från början, så allt hämtas från tomt
läge (`pipeline fetch`, samma väg som K2b:s onlinerepro). Nätet är en ny personlig miljö, `kpif-nowcast`, med en lista
över tillåtna källor (SCB, Riksbanken, Eurostat, KI, AF, Tillväxtanalys, Tillväxtverket, Kammarkollegiet, EI,
Hyresgästföreningen, Fastighetsägarna, FRED, NY Fed, FAO, Energinet, elprisetjustnu). Källås hålls med `flock` på
`/home/user/kpif-auto3/locks/<källa>.lock`.

## Spår

| Spår | Gren | Steg | Varianter | Senaste SHA | Resultat / BLOCKED | Tid / anrop / tokens |
|---|---|---|---|---|---|---|
| L1 Administrerade priser | auto3/l1 | **KLAR**, granskad (6 fynd, alla rättade), mergas | – | b46ab09 | `admin_calendar.py`: 26 egna händelser + K13:s 8 (moms, punktskatter, månadskort, tandvård, förskola, ROT …) med vikt × prisändring, beslutsdatum och källa. `python -m kpif_nowcast.admin_calendar <månad>` ger `--adjust`-rad. **Förslag 2026-12: +0,52 pe** (CO2-skatt +0,40, månadskort +0,12), 2027-01: −0,03. BLOCKED: regeringen/riksdagen/skatteverket inte i miljöns lista (länkar från webbsökning), elnät 2027 och SL 2027 utan besked. | 16 min bygg + granskn. + rättn. / 121 / 753k |
| L2 Resor | auto3/l2 | **DELVIS**, granskad (6 fynd, rättade), mergas | – | b437c8a | 9 serier: gästnätter (totalt, svenska, utländska, hotell; Eurostat tour_occ_nim, 80 d), påskserier (deterministiska, lag < 0), KPIF-index paketresor/flyg/logi. BLOCKED: Tillväxtverkets portal (tillvaxtdata.tillvaxtverket.se ej i listan), Kammarkollegiet (ingen tabell, bara register/PDF). | 9 min bygg / 132 / 647k |
| L3 Hyror | auto3/l3 | **KLAR**, granskad (5 fynd, rättade), mergas | – | 9ee2262 | `rent_negotiated` (Hyresgästföreningens vägda snitt 2016–2026, källa och releasedatum per år i LATE_RELEASES) och `kpi_rent_index`. BLOCKED: 2010–2015 (Sveriges Allmännytta, arkiv ej i listan), Fastighetsägarna publicerar inget riksgenomsnitt. | 9 min bygg / 106 / 635k |
| L4 Prospera | auto3/l4 | **DELVIS**, granskad (ok, 6 minor), mergas | – | d8926df | Penningmarknadens 5-åriga förväntningar (medel, P25, P75) 2019–2026 ur Riksbankens sifferunderlag (xlsx), lag 3 d. BLOCKED: 1/2 år och övriga grupper bara som Origo-PDF (origogroup.com ej i listan, PDF i skala), break-even finns inte i SWEA. | 9 min bygg / 78 / 417k |
| L5 El (rörliga avtal, nät) | auto3/l5 | **KLAR**, granskad (8 fynd varav 1 **läcka**, rättade), mergas | – | 4ac1580 | 12 serier: avtalsandelar (TAB3571; rättelse 2024-09-27 och 2022-04 i LATE_RELEASES = läckan), nätpris per typkund (SCB TAB3950), Ei nättariffer och andel nätområden som höjde. BLOCKED: nätbolagens aviserade januarihöjningar (ingen samlad källa), TAB4310 (halvår stöds inte). | 12 min bygg / 106 / 618k |
| L6 Kronan | auto3/l6 | **KLAR**, granskad (5 fynd, rättade), mergas | – | 8d7f970 | `sek_eur`, `sek_usd` (SWEA, månadsmedel 1993–, lag 1 d; ECU före 1999). | 6 min bygg / 54 / 421k |
| L7 Snabb-KPI mot utfall | auto3/l7 | **KLAR**, granskad (5 fynd, rättade), mergas | – | cd5a536 | 7 serier: snabb-KPIF/KPIF-XE årstakt och m/m från 2024-09, fel snabb − först publicerat utfall (1987=100-tabellerna före 2026-01). | 7 min bygg / 79 / 534k |
| L8 Snabbare testsvit | auto3/l8 | bygger (våg 1b) | – | – | – | – |
| L9 Månadsrutinen (kalender, snabb-KPI) | auto3/l9 | bygger (våg 1b) | – | – | – | – |
| L10 Dashboards (förberedelse) | auto3/l10 | bygger (våg 1b) | – | – | – | – |
| L2b Tillväxtverkets portal | auto3/l2b | bygger (våg 1b) | – | – | – | – |
| L1b Källkontroll av kalendern | auto3/l1b | bygger (våg 1b) | – | – | – | – |
| V2 Gemensam utvärdering | auto3/v2 | **pågår**: förregistrering → genomförande → 2 granskare → slutförande | 0/6 | – | – | – |
| V3 Avslut | – | väntar (våg 2) | – | – | – | – |

## Källås
- Riksbanken: L4, L6 (turas om)
- SCB: L5, L7 (turas om)

## Logg
- 2026-11-23T13:20Z: Johannes: drygt 50 % av 5-timmarsfönstret använt, en timme kvar → ambitionen höjd. Våg 1b startad parallellt med våg 2: L8 testsvit (sviten > 40 min seriellt, merge-flaskhals), L9 månadsrutinen, L10 dashboards, L2b Tillväxtverkets portal, L1b primärkällkontroll. Miljön fick 6 värdar till (tillvaxtdata.tillvaxtverket.se, regeringen, riksdagen ×2, skatteverket, sverigesallmannytta). Pytest på merge1 avbröts av 40-minutersgränsen (inget fel), körs om med -n 4.
- 2026-11-23T13:08Z: våg 2 startad från `auto3/merge1` (93f3d91), parallellt med pytest på merge1. Förregistrering pushas före resultat.
- 2026-11-23T13:05Z: våg 1 klar (arbetsflöde 66 min väggtid, 20 agenter, 676 verktygsanrop). Alla sju spår granskade oberoende; granskarna fann 1 läcka (L5 TAB3571-rättelsen) och 13 wrong-fynd, alla rättade. 35 nya serier. Merge av alla sju i en omgång (`auto3/merge1`, union-lösning i catalog.py, publication.py, publiceringskalendern; datakatalogen omgenererad), pytest på sammanslaget resultat pågår.
- 2026-11-23T12:35Z: hämtning från tomt läge klar: 337 serier, 0 fel (≈ 55 min, styrt av Energinets hastighetsgräns).
- 2026-11-23T11:50Z: våg 1 startad: L1–L7 parallellt i ett arbetsflöde (bygg → oberoende granskning av fördröjningar/läckage → rättning). Worktrees från main 129bbb0.
- 2026-11-23T11:42Z: körning 2 har STOP (bf11c0a). Körning 3 startad från main 129bbb0. Ny miljö `kpif-nowcast` med
  tillåtna källor (Default-miljön blockerade alla). Hämtning från tomt läge pågår (Energinet hastighetsbegränsar).
