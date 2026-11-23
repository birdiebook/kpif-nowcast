# Status: autonom körning 3 (svensk data där överraskningarna sitter)

## STOP

Körning 3 är avslutad 2026-11-23T18:05Z. Inga spår körs.

## Slutrapport (2026-11-23)

**Kort:** 12 spår och V2 klara, alla mergade till main (**347ec45**; därefter pages-rättning 0bf6cd0 och dokumenträttning **f999a36**). Pytest på
sammanslaget resultat var grönt (274 passed, 3 skipped). **35 nya serier** i sex katalogmoduler. Kalender för
administrerade priser med primärkällor är nu ett steg i månadsrutinen. **V2: ingen variant klarade urvalsskärmen
(urvalsevidens).** Körningen förbrukade 2 av 6 varianter, och projektet har nu 53 totalt. De 4 återstående
användes inte (Johannes beslut). Sverigeläget har tio nya dataset och sektioner och är uppladdat. Pages-workflowen
var trasig sedan K10 och är rättad. Veckohämtningen kördes sist: lokalt 372 serier ok, 0 fel, datatester 12/12
(inga nya värden samma dag). I Actions är den startad på main (körning 45232958155, första körningen från tom cache,
ca 1 h på grund av Energinet). Pages publiceras automatiskt efter den om Pages är påslaget, men det är inte verifierat här.

### Att besluta (Johannes)
1. **December 2026: `--adjust 0.52`** (förslag, inte beslutat). Innehåll: CO2-skattesänkningen upphör 1 dec
   (+0,398 pe, verifierad mot Skatteverket och prop. 2026/27:1–2) och månadskorten går tillbaka till fullpris
   (+0,115 pe, **bara delvis verifierad**: sista halvprisdagen 2 dec står i SFS 2026:1391, men regionernas egna
   datum är inte bekräftade). Kommando: `python -m kpif_nowcast.admin_calendar 2026-12`. Rör inte novemberprognosen
   eller `kpif-final-forecast-2026-11`.
2. **Tillväxtverkets gästnätter (L2b):** be Tillväxtverket om en öppen fil eller ett API, eller godkänn uttryckligen
   portalens interna RPC. Tills dess används Eurostat (t−3 vid deadline mot t−1).
3. **Pages:** om Pages inte redan är på: Settings → Pages → Source: GitHub Actions. Workflowen kan inte göra det själv.
4. Små driftval till nästa körning: `OMP_NUM_THREADS=1` även i `monthly-shadow.yml` (L8). K13:s två varianter in i
   `k12_global`:s universum före nästa globala test (V2-granskningen). Elskatt 2027: kontrollera Skatteverkets sats
   före januarirutinen (L1b).

### Per spår
| Spår | Byggt | BLOCKED och varför |
|---|---|---|
| L1 Administrerade priser | `admin_calendar.py`: 26 egna händelser + K13:s 8, med vikt × prisändring, beslutsdatum och källa. Ger en `--adjust`-rad per månad. | Elnät 2027, SL 2027: inget besked. |
| L1b Källkontroll | Alla 36 händelser (L1:s 26, två nya, K13:s 8) kontrollerade mot primärkälla: 26 verifierade, 4 delvis, 6 overifierade. Fyra beslutsdatum rättade. Tillagt: flygskattens avskaffande 2025-07 och drivmedelsskattesänkningen 2025-07 (nettoeffekt 0). Tobaksskatten 2027 genomförs inte. | Regionala månadskort och elskatt 2027-nivån (värdarna nås inte från miljön), trängselskatt 2016, VA/avfall 2027 (ingen samlad källa). |
| L2 Resor | 9 serier: gästnätter via Eurostat (fyra serier), påskens placering (deterministisk), KPIF-index för paketresor, flyg och logi. | Kammarkollegiet: ingen tabell, bara register/PDF. |
| L2b Tillväxtverket | Fördröjningen belagd (22–30 d; 31 d enligt granskningen, ej reproducerat; `lag_days=31` från 2025-08), revisionsregeln bekräftad, nivåjämförelse mot Eurostat. | **Portalen:** DivePort-BI med noindex, inget öppet API och ingen fil. Data finns bara via sessionsbunden intern RPC, som nekade som obehörig. Inte forcerat. |
| L3 Hyror | `rent_negotiated` (vägt snitt 2016–2026, källa och releasedatum per år), `kpi_rent_index`. | 2010–2015 (arkivet nås inte), Fastighetsägarna har inget riksgenomsnitt. |
| L4 Prospera | Penningmarknadens 5-åriga förväntningar (medel, P25, P75) 2019– ur Riksbankens xlsx. | 1- och 2-årshorisonterna och övriga grupper finns bara som Origo-PDF (PDF i skala). Break-even finns inte i SWEA. |
| L5 El | 12 serier: avtalsandelar (TAB3571), nätpris per typkund (TAB3950), Ei:s nättariffer, andel nätområden som höjde. Granskningen fann **1 läcka** (en sen rättelse 2024-09-27), som är rättad i `LATE_RELEASES`. | Nätbolagens aviserade januarihöjningar (ingen samlad källa), TAB4310 (halvår stöds inte). |
| L6 Kronan | `sek_eur`, `sek_usd` (SWEA, månadsmedel 1993–). | – |
| L7 Snabb-KPI | 7 serier: snabb-KPIF/KPIF-XE i årstakt och m/m från 2024-09, samt felet snabb − utfall. | – |
| L8 Testsvit | Från över 40 min till cirka 9–15 min. Orsaken var OpenMP-trådar i HGB som konkurrerade om 4 kärnor; `OMP_NUM_THREADS=1` i conftest löser det. Memoiserad champion-historik. | – |
| L9 Månadsrutinen | Kalendern är ett icke-fatalt steg i `pipeline monthly` och en sektion i månadsbrevet (förslag + förhandsvisning). Snabb-KPI är referens i SCORECARD. Brevet 2026-11 är omgenererat. | – |
| L10 Dashboards | `sverige_sections.py` med tio dataset och åtta nya sektioner, samma mall för Claude Data och Pages. | cdnjs i containern (bara testet berördes). |
| V2 Utvärdering | Förregistrerad (c3f7670) screening av 10 serier × 2 baser, ett gemensamt test, SPA. Två oberoende granskningar: ingen läcka. | – |
| V3 Avslut | Två merge-omgångar. Sverigeläget uppladdat (23 dataset och sidan, 24 filer). Sidan är kontrollerad lokalt med Playwright i 1280 och 390 px: 74 ritningar, ingen tom, inga konsolfel. Pages-workflowen rättad (ogiltig YAML sedan K10, aldrig körd) och har nu ett test. Slutrapporten granskad av en oberoende agent, sex rättelser. Veckohämtningen kördes sist. | Plattformens egen kontroll av sidan har inte körts, eftersom ingen hade sidan öppen. |

### Utvärderingen (V2): urvalsevidens
Allt nedan är **urvalsevidens** på 2015–2026, samma period som modellerna valdes på. Projektet har totalt **53 varianter**.
- Screening (räknas inte mot taket): **0 BH-överlevare** av 10 serier per bas (q = 0,10). Lägsta råa p-värdet var 0,143
  mot K2-ridge-skuggan och 0,032 mot 50/50 (projektet totalt 53 varianter). Båda gällde flygpriserna (`kpif_air_transport_index`).
- `v2_r_corr`: MAE 0,2072 mot 0,2113. Rå p 0,143, Holm p 0,143, globalt justerat p 0,790 (40 modeller i U1 + V2;
  projektet totalt 53 varianter). **Klarade inte urvalsskärmen.**
- `v2_a_corr`: MAE 0,2241 mot 0,2320. Rå p 0,032, Holm p 0,064, globalt justerat p 0,477 (40 modeller i U1 + V2;
  projektet totalt 53 varianter). **Klarade inte urvalsskärmen.** 48 % av vinsten ligger i 2021, och utan 2021 är p 0,134 (projektet totalt 53 varianter).
- SPA över K12:s universum plus V2 (40 modeller; K13:s två varianter och de screenade serierna ingår inte), mot skuggan:
  0,625 (projektet totalt 53 varianter). Mot 50/50: 0,023 (projektet totalt 53 varianter), vilket beror på K2-familjen
  som i K12. Med K13 i universumet blir de justerade p-värdena 0,486 och 0,793. Inget fryses som skugga.
- Avvikelser från protokollet (redovisade, ingen läcka): basens MAE blev 0,1993 mot förregistrerat 0,200, men den är
  identisk med main före körning 3. Tredje decimalen skiljer mot K12:s fil för 11 av 38 modeller.

### Kalibrering
Väggtid ca 6,2 h (11:42–17:55Z). Tre arbetsflöden med 38 agenter och cirka 1 620 verktygsanrop. Per spår se
tabellen nedan och `docs/agentkalibrering.md`. Lärdomar:
- CPU (4 kärnor) blev flaskhalsen när spåren körde hela sviten parallellt.
- Spår ska köra riktade tester, och orkestreraren kör hela sviten en gång per omgång.
- Bygg → granskning → rättning hittade 1 läcka och 15 wrong-fynd.

### Kända småfel (ej åtgärdade)
- Sverigeläget: V2-sektionen visar hela resultat.md och blir lång.
- Sju äldre diagram har avklippta etiketter, enligt plattformens kontroll från 13:10Z.
- Den äldre "tryck"-listan visar Ei:s nätavgift för 2026-12 före katalogens `known_from`. Felet fanns före körning 3 (L10-granskningen).
- `admin_yy` saknar known_from per rad. Filtreringen görs på beslutsdatum.

---

**Lås:** orkestrerare (molnsession) 2026-11-23T11:42Z · heartbeat 2026-11-23T18:05Z
**Start:** 2026-11-23 · **Bas:** main @ 129bbb0 · körning 2: STOP (bf11c0a)
**Varianter i körningen:** 2/6 (projektet totalt 51 + 2 = 53) · **Screening:** räknas inte mot taket
**main:** f999a36 · **Merge:** klara spår mergas till main av orkestreraren när pytest är grönt · **Brief:** [BRIEF.md](BRIEF.md) · regler: `docs/autonom-korning-2.md` på main, med ändringarna i briefen

**Miljö (avvikelse från briefen):** körningen går i en molncontainer (Linux), inte på `C:\dev`. Worktrees ligger under
`/home/user/kpif-auto3/<spår>`, grenar `auto3/<spår>`. Datan finns inte i containern från början, så allt hämtas från tomt
läge (`pipeline fetch`, samma väg som K2b:s onlinerepro). Nätet är en ny personlig miljö, `kpif-nowcast`, med en lista
över tillåtna källor (SCB, Riksbanken, Eurostat, KI, AF, Tillväxtanalys, Tillväxtverket, Kammarkollegiet, EI,
Hyresgästföreningen, Fastighetsägarna, FRED, NY Fed, FAO, Energinet, elprisetjustnu). Källås hålls med `flock` på
`/home/user/kpif-auto3/locks/<källa>.lock`.

## Spår

| Spår | Gren | Steg | Varianter | Senaste SHA | Resultat / BLOCKED | Tid / anrop / tokens |
|---|---|---|---|---|---|---|
| L1 Administrerade priser | auto3/l1 | **KLAR**, granskad (6 fynd, alla rättade), **mergad** (856ced2) | – | b46ab09 | `admin_calendar.py`: 26 egna händelser + K13:s 8 (moms, punktskatter, månadskort, tandvård, förskola, ROT …) med vikt × prisändring, beslutsdatum och källa. `python -m kpif_nowcast.admin_calendar <månad>` ger `--adjust`-rad. **Förslag 2026-12: +0,52 pe** (CO2-skatt +0,40, månadskort +0,12), 2027-01: −0,03. BLOCKED: regeringen/riksdagen/skatteverket inte i miljöns lista (länkar från webbsökning), elnät 2027 och SL 2027 utan besked. | 16 min bygg + granskn. + rättn. / 121 / 753k |
| L2 Resor | auto3/l2 | **DELVIS**, granskad (6 fynd, rättade), **mergad** (856ced2) | – | b437c8a | 9 serier: gästnätter (totalt, svenska, utländska, hotell; Eurostat tour_occ_nim, 80 d), påskserier (deterministiska, lag < 0), KPIF-index paketresor/flyg/logi. BLOCKED: Tillväxtverkets portal (tillvaxtdata.tillvaxtverket.se ej i listan), Kammarkollegiet (ingen tabell, bara register/PDF). | 9 min bygg / 132 / 647k |
| L3 Hyror | auto3/l3 | **KLAR**, granskad (5 fynd, rättade), **mergad** (856ced2) | – | 9ee2262 | `rent_negotiated` (Hyresgästföreningens vägda snitt 2016–2026, källa och releasedatum per år i LATE_RELEASES) och `kpi_rent_index`. BLOCKED: 2010–2015 (Sveriges Allmännytta, arkiv ej i listan), Fastighetsägarna publicerar inget riksgenomsnitt. | 9 min bygg / 106 / 635k |
| L4 Prospera | auto3/l4 | **DELVIS**, granskad (ok, 6 minor), **mergad** (856ced2) | – | d8926df | Penningmarknadens 5-åriga förväntningar (medel, P25, P75) 2019–2026 ur Riksbankens sifferunderlag (xlsx), lag 3 d. BLOCKED: 1/2 år och övriga grupper bara som Origo-PDF (origogroup.com ej i listan, PDF i skala), break-even finns inte i SWEA. | 9 min bygg / 78 / 417k |
| L5 El (rörliga avtal, nät) | auto3/l5 | **KLAR**, granskad (8 fynd varav 1 **läcka**, rättade), **mergad** (856ced2) | – | 4ac1580 | 12 serier: avtalsandelar (TAB3571; rättelse 2024-09-27 och 2022-04 i LATE_RELEASES = läckan), nätpris per typkund (SCB TAB3950), Ei nättariffer och andel nätområden som höjde. BLOCKED: nätbolagens aviserade januarihöjningar (ingen samlad källa), TAB4310 (halvår stöds inte). | 12 min bygg / 106 / 618k |
| L6 Kronan | auto3/l6 | **KLAR**, granskad (5 fynd, rättade), **mergad** (856ced2) | – | 8d7f970 | `sek_eur`, `sek_usd` (SWEA, månadsmedel 1993–, lag 1 d; ECU före 1999). | 6 min bygg / 54 / 421k |
| L7 Snabb-KPI mot utfall | auto3/l7 | **KLAR**, granskad (5 fynd, rättade), **mergad** (856ced2) | – | cd5a536 | 7 serier: snabb-KPIF/KPIF-XE årstakt och m/m från 2024-09, fel snabb − först publicerat utfall (1987=100-tabellerna före 2026-01). | 7 min bygg / 79 / 534k |
| L8 Snabbare testsvit | auto3/l8 | **KLAR**, granskad (ok, 2 minor), **mergad** (856ced2) | – | a11ab45 | Orsaken till > 40 min: OpenMP-trådar i HGB som slogs om 4 kärnor (en nästlad anpassning > 12 min → 2,1 s med OMP_NUM_THREADS=1 i conftest). Memoiserad champion-historik. Samma 205 tester. Öppet: samma trådgräns i `monthly-shadow.yml` (Johannes/nästa körning). | 74 min (under last) / 120 / 447k |
| L9 Månadsrutinen (kalender, snabb-KPI) | auto3/l9 | **KLAR**, granskad (5 fynd, rättade), **mergad** (347ec45) | – | 2a6b0c0 | Kalendern som icke-fatalt steg i `pipeline monthly` (`outputs/admin_calendar/<månad>.json/.md`, artefakt i monthly-shadow.yml), läckageregel även på informationsdatum, två nya sektioner i månadsbrevet (förslag + förhandsvisning), brevet 2026-11 omgenererat. Snabb-KPI som referens i SCORECARD (`flash_live_lines`) och champion (`flash_reference`): snabb-KPI:s fel mot samma utfall MAE 0,004 pe. | 44 + 21 + 38 min / 150 / 632k |
| L10 Dashboards | auto3/l10 | **KLAR**, granskad (ok, 5 minor), **mergad** (347ec45) | – | 927435a | `sverige_sections.py`: tio dataset (admin_yy, admin_upcoming, admin_events, snabbkpi, resor, hyror, elmarknad, kronan, prospera, v2_eval), åtta nya sektioner i mallen (samma mall för Pages). Playwright 1280/390 px utan fel. BLOCKED: cdnjs i containern (403, löst i testet med samma d3 från npm). | 58 + 12 min / 164 / 570k |
| L2b Tillväxtverkets portal | auto3/l2b | **BLOCKED** för data, granskad (1 wrong, rättat), **mergad** (347ec45, bara dokumentation) | – | 8118502 | BLOCKED: portalen är ett DivePort-BI-gränssnitt (noindex) utan öppet API eller fil; data bara via sessionsbunden intern RPC som nekade som obehörig. Inte forcerat. Väg: Johannes ber Tillväxtverket om fil/API eller godkänner RPC-vägen. Levererat: fördröjning belagd (22–31 d → t−1 vid deadline mot t−3 via Eurostat, `lag_days=31` från 2025-08), revisionsregel, nivåjämförelse mot Eurostat (hotell lika, total skiljer pga SoL). | 7 + 7 + 63 min / 132 / 496k |
| L1b Källkontroll av kalendern | auto3/l1b | **KLAR**, granskad (1 wrong + 5 minor, rättade), **mergad** (347ec45) | – | 2021134 | 36 händelser kontrollerade mot riksdagen/SFS/Skatteverket/regeringen: 26 verifierade, 4 delvis, 6 overifierade (fält `verified`). Förslagen oförändrade: **2026-12 +0,52**, 2027-01 −0,03. Rättat: fyra beslutsdatum (2016-01, ROT 2025, matmomsen 2026), tobaksskatten 2027 genomförs inte, flygskattens avskaffande och drivmedelsskattesänkningen 2025-07 tillagda. BLOCKED: regionala månadskort, elskatt 2027-nivån, trängselskatt 2016, elnät/VA 2027 (värdar ej nåbara eller ingen samlad källa). | 66 + 8 + 13 min / 149 / 740k |
| V2 Gemensam utvärdering | auto3/v2 | **KLAR**, två oberoende granskningar (håller med förbehåll, 9 minor, ingen läcka), **mergad** (347ec45) | **2/6** | 9430209 | **Urvalsevidens: ingen variant klarade urvalsskärmen; inget fryst som skugga.** 0 BH-överlevare av 10 serier per bas. `v2_r_corr` (flyg på K2-ridge-skuggan): MAE 0,2072 mot 0,2113, rå p 0,143, Holm p 0,143, globalt p 0,790 (projektet totalt 53 varianter). `v2_a_corr` (flyg på 50/50): MAE 0,2241 mot 0,2320, rå p 0,032, Holm p 0,064, globalt p 0,477 (projektet totalt 53 varianter); 48 % av vinsten i 2021. SPA mot skuggan 0,625. | 7 + 106 + 149 min / 229 / 1298k |
| V3 Avslut | main | **KLAR** | – | f999a36 | Se slutrapporten. | ca 30 min orkestrering + 1 granskningsagent (27 anrop, 141k) |

## Källås
- Riksbanken: L4, L6 (turas om)
- SCB: L5, L7 (turas om)

## Logg
- 2026-11-23T18:05Z: **STOP.** Våg 3 klar: Sverigeläget (23 dataset + sida) uppladdat till Claude Data, Pages-workflowen rättad (0bf6cd0), slutrapporten granskad oberoende och rättad (f999a36). Veckohämtningen kördes sist (lokalt 372 ok, 0 fel, datatester 12/12; i Actions startad).
- 2026-11-23T17:50Z: **main → 347ec45** (V2, L9, L10, L2b, L1b i en omgång, `auto3/merge2`). Konflikter: `admin_calendar.py` (L9 × L1b, löst med L9:s `why_not_used` + L1b:s "ingen effekt") och L6-testet. Två V2-tester föll för att `el_contracts.csv` saknades i datan; filerna kopierades in från V2:s körning och testerna hoppar nu över rent utan filen. Pytest med full data: 274 passed, 3 skipped, 8,6 min (-n 4). Våg 3 startad.
- 2026-11-23T15:28Z: **main → 856ced2** (L1–L7, L8, L6-testrättning). Pytest på det sammanslagna: 201 passed, 11 skipped, 15,6 min med -n 3 (L8:s OMP-fix). Johannes godkände planen: de 4 återstående varianterna används inte (inget januaritest).
- 2026-11-23T15:15Z: V2 genomförd: 0 BH-överlevare, ingen variant klarade urvalsskärmen (v2_a_corr Holm 0,064, globalt 0,48; v2_r_corr Holm 0,143; projektet totalt 53 varianter); granskning pågår. L8 mergad i merge1 + rättat L6-ordningstest (mergen satte andra moduler mellan K0 och FX). Full pytest på merge1 körs.
- 2026-11-23T13:20Z: Johannes: drygt 50 % av 5-timmarsfönstret använt, en timme kvar → ambitionen höjd. Våg 1b startad parallellt med våg 2: L8 testsvit (sviten > 40 min seriellt, merge-flaskhals), L9 månadsrutinen, L10 dashboards, L2b Tillväxtverkets portal, L1b primärkällkontroll. Miljön fick 6 värdar till (tillvaxtdata.tillvaxtverket.se, regeringen, riksdagen ×2, skatteverket, sverigesallmannytta). Pytest på merge1 avbröts av 40-minutersgränsen (inget fel), körs om med -n 4.
- 2026-11-23T13:08Z: våg 2 startad från `auto3/merge1` (93f3d91), parallellt med pytest på merge1. Förregistrering pushas före resultat.
- 2026-11-23T13:05Z: våg 1 klar (arbetsflöde 66 min väggtid, 20 agenter, 676 verktygsanrop). Alla sju spår granskade oberoende; granskarna fann 1 läcka (L5 TAB3571-rättelsen) och 13 wrong-fynd, alla rättade. 35 nya serier. Merge av alla sju i en omgång (`auto3/merge1`, union-lösning i catalog.py, publication.py, publiceringskalendern; datakatalogen omgenererad), pytest på sammanslaget resultat pågår.
- 2026-11-23T12:35Z: hämtning från tomt läge klar: 337 serier, 0 fel (≈ 55 min, styrt av Energinets hastighetsgräns).
- 2026-11-23T11:50Z: våg 1 startad: L1–L7 parallellt i ett arbetsflöde (bygg → oberoende granskning av fördröjningar/läckage → rättning). Worktrees från main 129bbb0.
- 2026-11-23T11:42Z: körning 2 har STOP (bf11c0a). Körning 3 startad från main 129bbb0. Ny miljö `kpif-nowcast` med
  tillåtna källor (Default-miljön blockerade alla). Hämtning från tomt läge pågår (Energinet hastighetsbegränsar).
