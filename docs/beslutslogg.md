# Beslutslogg

Varje viktigt val, med mina egna ord. Kan jag inte förklara det här har jag
hittat min nästa lärfråga.

Mall:

```
## ÅÅÅÅ-MM-DD – Beslut
**Vad:** …
**Varför:** …
**Alternativ jag valde bort:** …
**Min gissning innan / vad som faktiskt hände:** …
**Öppna frågor:** …
```

---

## 2026-11-22 – Projektets ramar
**Vad:** Nowcasta KPIF, alltså nästa månads siffra innan SCB publicerar den.
**Varför:** Avgränsat, öppen data, och ett facit varje månad att lära mig av.
Makro på lång sikt har för få observationer och för många regimskiften för en start.
**Alternativ jag valde bort:** Valanalys (möjligt projekt 2), AI-produktivitet (inget facit än),
Polymarket (blir en sidovana för att träna kalibrering).
**Öppna frågor:** Hur nära Riksbanken kan en enkel modell komma?

## 2026-11-22 – Prognosen låses före snabb-KPI
**Vad:** Prognosen för månad t låses senast den 4:e i månad t+1, före SCB:s snabb-KPI.
**Varför:** Snabb-KPI (sedan okt 2024) ligger ~0,01 procentenheter från slutlig siffra.
Efter den finns inget kvar att förutse.
**Konsekvens:** Vid prognostillfället är senaste kända KPIF månad t-1.

## 2026-11-22 – Fas 2: baslinjer och mått
**Vad:** Alla modeller förutser månadsförändringen för t och räknas om till årstakt
via kända index för t-1 och t-12. Utvärdering mot SCB:s officiella årstakt (en decimal).
Mått: MAE i procentenheter (huvudmått), RMSE, och andel exakta träffar efter avrundning.
Riksbanken: senaste prognosomgång publicerad före deadline, där t fortfarande är prognos.
**Resultat 2015–2026 (141 mån), MAE:** Riksbanken 0,32 · säsong+trend 0,34 · naiv 0,38.
**Lärdomar:**
- "Samma månadsförändring som i fjol" är matematiskt identisk med "samma årstakt som förra månaden".
- Säsongsmodellerna är bäst över lång tid men sämst 2024–2026 (MAE 0,45 mot Riksbankens 0,33).
- Skillnaden mot Riksbanken (0,015) är för liten för att skilja från slump på 141 månader.
- Riksbankens prognos är oftast 1–3 månader gammal vid vår deadline.
**Öppna frågor:** Varför tappar säsongsmodellerna 2024–2026? Kandidater: elprisets
svängningar, COICOP 2018-bytet, ändrade säsongsmönster.

## 2026-11-22 – Fas 3: energipriser
**Vad:** Säsong+trend-baslinjen plus en korrigering för månadens energiprisrörelser:
drivmedel (Brent i SEK, dag 1–25, log-förändring) och el (spotpris SE3/SE4 viktat 70/30,
förändring i kr/kWh). Linjär regression utan intercept, expanderande fönster.
Elpriser bara från 2021-11 (elprisetjustnu.se) i väntan på ENTSO-E-nyckel.
**Resultat, MAE:**
- 2015–2026: drivmedelsmodell 0,316 · Riksbanken 0,320 · baslinje 0,335 (skillnaden mot Riksbanken är brus).
- 2024–2026 (34 mån): Riksbanken 0,33 · drivmedel+el 0,40 · naiv 0,40 · baslinje 0,45.
**Koefficienter (rimliga):** +10 % oljepris i kronor → ca +0,1 pe på KPIF samma månad.
+1 kr/kWh i spotpris → ca +0,8 pe.
**Lärdomar:**
- Energipriser förbättrar baslinjen tydligt 2024–2026 (0,45 → 0,40) men räcker inte för att nå Riksbanken.
- De största missarna är januari och mars–april (2026-03: +1,4 pe, 2025-01: −1,2 pe).
  Hypotes: engångshändelser som skatte- och momsändringar och årliga vikt-/avgiftsbyten.
  Sådant vet Riksbanken i förväg men syns inte i prisdata. Ej verifierat.
- Viktningen 70/30 mellan SE3 och SE4 är ett antagande.
**Nästa:** dela upp KPIF i komponenter (fas 4) för att se exakt vad som missas de månaderna.

## 2026-11-22 – Fas 4: komponentmodell
**Vad:** Prognos per analysgrupp i SCB:s TAB6628 (tjänster, varor, livsmedel, energi,
kapitalstock), på varje grupps *bidrag* till KPIF:s månadsförändring. Bidragen summerar
till KPIF m/m (avvikelse ~0,03 pe från avrundning). Energi får regressionskorrigering
(drivmedel + el), övriga grupper säsong+trend.
**Varför bidrag och inte index + vikter:** att kedja ihop gruppindex med SCB:s vikter
reproducerade inte KPIF tillräckligt exakt (indexfel 0,13 i snitt). Bidragen gör det.
**Resultat, MAE 2024–2026:** Riksbanken 0,33 · komponentmodell 0,375 · fas 3 0,395 · baslinje 0,45.
2015–2026 (bara drivmedel): komponentmodell 0,316 ≈ fas 3 0,316 ≈ Riksbanken 0,320.
**Var felet sitter 2024–2026 (MAE i pe av KPIF m/m):** energi 0,24 (från 0,35),
tjänster 0,19, varor 0,10, livsmedel 0,09, kapitalstock 0,01.
**Lärdomar:**
- Energi var största felkällan, och elpriset tar bort en tredjedel av energifelet.
- Januari är svårast: energin stiger mer än modellen tror (nätavgifter, skatter, vinterpris).
- April 2026: livsmedel föll kraftigt, troligen sänkt matmoms. Ej verifierat i källa.
- Tjänster är nu näst största felkällan, och där har vi ingen förklarande variabel än.
**Nästa kandidater:** (1) kalender över kända skatte-/avgiftsändringar, (2) Konjunkturinstitutets
prisplaner för tjänster och livsmedel, (3) längre elhistorik via ENTSO-E, (4) andel rörliga elavtal.

## 2026-11-22 – Fas 4b: Konjunkturinstitutets prisplaner – ingen effekt
**Vad:** Företagens förväntade försäljningspriser kommande 3 månader (nettotal, ej
säsongsrensat) för tjänstesektorn, dagligvaruhandeln och sällanköpshandeln, som
korrigering för tjänster, livsmedel respektive varor. Två varianter: nivå och avvikelse
från eget 12-månaderssnitt. Enkätmånad t-1 används för prognos av t.
**Varför ej säsongsrensat:** säsongsrensningen skattas om på hela serien, så gamla värden
ändras i efterhand. Det vore läckage.
**Resultat, MAE:** 2024–2026: 0,375 → 0,369 (avvikelse) / 0,375 (nivå).
2015–2026: 0,316 → 0,311 / 0,319. På komponentnivå är förbättringen ≤ 0,002 pe.
**Slutsats:** Prisplanerna tillför i praktiken inget en månad framåt. Trenden fångar redan
samma information. Skillnaden mellan varianterna är brus, och att välja den som råkade vinna
på testperioden vore överanpassning. Huvudmodellen förblir komponentmodell med drivmedel + el.
Prisplanerna kan vara mer värda för längre horisonter (fas 5).

## 2026-11-22 – Fas 4b: skattekalender – hjälper vid stora händelser, inte i snitt
**Vad:** Skatteeffekt per månad = KPIF m/m − KPIF med konstant skatt (KPIF-KS, SCB TAB6592).
Skatteändringar beslutas i förväg, så effekten för månad t räknas som känd vid deadline
(antagande: full genomslag, som i SCB:s KS-metod). Historiken rensas från skatteeffekter,
modellen körs på rensade data och månadens kända skatteeffekt läggs tillbaka.
Fördelning mellan energi och övrigt via KPIF-XE-KS (finns från ~2020), annars efter vikt.
**Verifierat mot källor:** matmomsen halverades 12 → 6 % från 1 april 2026 (regeringen, SCB:
livsmedel −5,5 % i april). Sänkt skatt på bensin/diesel juli 2026 (SCB, TV4/TT). Samma
månad sänktes också kollektivtrafik- och förskoleavgifter, men det är avgifter och syns inte i KS.
**Resultat, MAE:** 2024–2026: 0,375 → 0,388. 2015–2026: 0,316 → 0,327.
April 2026 går från 0,75 till 0,03 i fel, men övriga månader blir något sämre.
**Varför sämre i snitt (hypoteser):** de återkommande små skatteändringarna (januari +0,1–0,3,
juli −0,2) fångas redan av säsongsmönstret, så rensningen tillför brus. Genomslaget är inte
alltid fullt eller omedelbart. Och de största kvarvarande missarna (jan 2025, mars 2026)
har ingen skatteeffekt alls. De är el, nätavgifter och annat.
**Beslut:** Skattekalendern ingår inte i huvudmodellen. Vid skarpa prognoser görs en
**manuell justering för stora, beslutade engångshändelser** (t.ex. momsändringar), vilket
också är så professionella prognosmakare arbetar.

## 2026-11-22 – Skarpa prognoser och första preliminära prognos (november 2026)
**Vad:** `forecast.py` gör prognos för månaden efter senast publicerade KPIF med
huvudmodellen (komponentmodell, drivmedel + el), sparar den som JSON i `forecasts/` och
committas före snabb-KPI. Status FINAL bara om data för hela månaden finns och körningen
sker senast den 4:e. Osäkerhetsintervall = empiriska felkvantiler från backtesten 2024–2026
(50 %: ±0,34, 80 %: ±0,54). Manuell justering möjlig med motivering.
**Preliminär prognos 2026-11 (gjord 22 nov):** 2,1 % (80 %: 1,5–2,6). Riksbanken (sept): 1,73.
Senaste utfall (okt): 1,1.
**Varför så högt:** elpriset i november är extremt hittills (SE3 ~1,8 kr/kWh mot 0,8 i okt,
SE4 ~2,7 mot 1,6), vilket ger energi ett bidrag på +1,2 pe. Oljepriset i kronor föll ~25 %
och drar ner. Övriga komponenter är svagt negativa (säsong).
**Risker:** elpriset kan falla resten av månaden (21 av 30 dagar kända). Elbidraget är en
extrapolation nära kanten av vad modellen sett sedan 2021. Kontrollera före slutlig prognos
om några skatter eller avgifter ändras i november.

## 2026-11-22 – Visualisering i Claude Data
**Vad:** en dashboard i Claude Data (privat artefakt på claude.ai) med aktuell prognos,
KPIF-historik med Riksbankens bana, bidrag per komponent, el- och drivmedelsdata,
backtestens träffsäkerhet och logg över skarpa prognoser.
**Hur:** `python -m kpif_nowcast.export_dashboard` skriver sex JSON-filer till
`outputs/dashboard/` (gitignorerat). Agenten laddar upp dem efter varje körning. Varje fil
bär exportskriptets egen kod, så att varje siffra kan spåras till koden som räknade fram den.
**Varför filer och inte live-frågor:** det finns ingen koppling (connector) till SCB eller
Riksbanken, och modellen körs ändå lokalt i Python.
**Backtesten per månad** räknas om i exporten med samma funktioner som `forecast.py`
(MAE 0,375 på 34 månader, samma som felbanden). Riksbanken ligger något lägre (0,33) på
samma månader. Skillnaden är liten och kan vara slump.

## 2026-11-22 – Datalager och drift (plan, inte byggt)
**Vad:** ingen databas eller backend nu. Två steg längre fram:
1. **Fas 5:** en tabell med versionerade observationer `(serie, period, värde, known_from)`
   och `as_of(serie, datum)`, plus en tabell med modellens prognoser
   `(modell, version, målmånad, prognosdatum, prognos)`.
2. **Fas 6 (upplägg A):** GitHub Actions för schemalagd hämtning och prognos, Parquet i
   objektlagring (R2/B2), DuckDB, dbt för transformationer och datatester, MLflow,
   champion/challenger och dashboard på GitHub Pages. Manuell justering via `workflow_dispatch`.
**Varför:** volymen (~30 MB) motiverar ingen server. Det verkliga problemet är läckage från
reviderade siffror och från publiceringsfördröjningar (ragged edge) när BNP/löner/AKU kommer
in, och det löses med `known_from`, inte med en databas.
**Alternativ jag valde bort:** Supabase gratis (pausas vid inaktivitet), Databricks Free Edition
(låsning, oklara begränsningar), Airflow/Dagster (överdimensionerat), data i git.
**Öppna frågor:** dbt v2 (sept 2026) har inbyggd DuckDB-adapter men kan enligt uppgift inte
ladda tillägg som httpfs, alltså inte läsa Parquet direkt från S3. Testa, eller använd
Python-adaptern dbt-duckdb. Kolla om dlt passar för hämtningen. Kolla villkoren i
gratisnivåerna (R2 kräver ev. kort).

## 2026-11-22 – Fas 5: versionerade observationer
**Vad:** `observations.py` med tabellen `(series, period, value, known_from, source, fetched_at)`
i `data/observations.parquet` och `as_of(serie, datum)`. Nio serier: KPIF, AKU-arbetslöshet
(ej säsongsrensad + säsongsrensad), BNP-indikatorn (årstakt, kalenderjusterad), KIX, styrränta,
Brent i SEK, KI-prisplaner tjänster.
**known_from:** periodens slut + typisk publiceringsfördröjning (KPIF 15 d, AKU 25 d,
BNP-indikator 35 d, dagliga serier 1 d, KI 3 d), valt i överkant. Nya perioder vid senare
hämtningar får min(standard, hämtdatum). Ändrade värden (revideringar) får hämtdatum.
**Begränsning:** SCB:s API saknar historiska vintages, så återfyllnaden använder dagens värden.
Revideringar av BNP-indikatorn läcker alltså in i backtesten. Från och med nu sparas riktiga
vintages vid varje hämtning. Ofullständig innevarande månad för dagliga serier tas inte med.

## 2026-11-22 – Fas 5: prognoser 3, 6 och 12 månader framåt
**Vad:** direkta prognoser av KPIF-årstakten h månader efter senast publicerade månad, gjorda
samma dag som nowcasten. Variabler vid prognosdagen (via `as_of`): avstånd till 2 %, momentum
(3 mån), arbetslöshet (nivå och förändring), BNP-indikator, KIX-förändring, styrränta, Brent i SEK,
KI-prisplaner. Modeller: naiv, "2 % målet", återgång mot målet, ridge-regression,
gradient boosting (grunda träd). Expanderande fönster, minst 60 träningsmånader.
**Resultat, MAE 2015–2026 (pe årstakt):**

| | 3 mån | 6 mån | 12 mån |
|---|---|---|---|
| Riksbanken | **0,49** | **0,81** | **1,39** |
| Gradient boosting | 0,63 | 1,04 | 1,82 |
| Återgång mot målet | 0,68 | 1,15 | 1,60 |
| Naiv | 0,67 | 1,10 | 1,89 |
| Ridge | 0,69 | 1,23 | 2,19 |
| "Det blir 2 %" | 1,37 | 1,37 | **1,39** |

**Lärdomar:**
- Riksbanken vinner tydligt på alla längre horisonter, till skillnad från nowcasten där vi var i nivå.
  De vet sin egen räntebana och har mycket mer information och bedömning.
- På 12 månader är "det blir 2 %" lika bra som Riksbanken över hela perioden och bäst av
  alla 2024–2026. Lång sikt handlar om att inflationen är förankrad vid målet.
- Gradient boosting är bäst av våra modeller men slår inte enkla baslinjer med mycket.
  Ridge blir sämst på 12 månader: med ~150 effektivt oberoende observationer och en stor chock
  (2022) lär den sig samband som inte håller (t.ex. att stigande arbetslöshet ger *högre* inflation).
- Makro har för få oberoende observationer för avancerad ML. Precis den begränsning vi
  diskuterade i början, nu bekräftad med siffror.
**Beslut:** projektets styrka är nowcasten. Längre horisonter behålls som jämförelse, och den
bästa enkla regeln för 12 månader är målet. Ingen skarp publicering av långa prognoser än.

## 2026-11-22 – Vision och datakatalog
**Vision:** se [`vision.md`](vision.md). Förstå svensk ekonomi genom inflationen. Tre delar:
en ärlig månadsprognos, en bred bild av läget i Sverige och en AI-lins (AI → produktivitet → inflation).
**Vad:** `catalog.py` med en `Spec` per serie (område, etikett, enhet, frekvens, källa, hämtning,
publiceringsfördröjning, revideras ja/nej, koppling till inflationen). 64 serier i åtta områden från
SCB, Riksbanken, Konjunkturinstitutet, Tillväxtanalys, Eurostat, FAO, FRED, NY Fed och JobTech.
Kvartal lagras på kvartalets sista månad och år på december, så att `known_from` fungerar lika för alla.
**Val:**
- Ej säsongsrensade serier där säsongsrensning revideras. Undantag (sparkvot, KI-indikatorer)
  är markerade som reviderade.
- Euroområdets inflation lagras som *första publicering* (snabbestimat, fryst), eftersom det är
  den som fanns före vår deadline.
- KI:s nya mätmetod för företagens inflationsförväntningar (2026K4) skarvas inte ihop med den gamla.
- AI-annonser: fritextsökning i JobTech, alltså brusig. Ska normeras med totalt antal annonser.
**Kvalitetskontroll:** inga luckor utom AI-användning (undersökningen görs inte varje år) och hyror.
Inga orimliga värden. KI:s kvartalsenkäter får `known_from` vid kvartalets slut, trots att de
publiceras tidigare, vilket är försiktigt men inte fel.
**Ej med än:** Arbetsförmedlingens varsel och inskrivna arbetslösa (Excel-filer med ändrade URL:er,
kräver skrapning), bostadsrättspriser per månad (ingen öppen källa), ENTSO-E.

## 2026-11-22 – Elhistorik från 2011 via Energinet (bara data, ingen modelländring)
**Vad:** Spotpris SE3/SE4 före 2021-11 hämtas från Energinets Energi Data Service (CC BY 4.0,
ingen nyckel). Det skarvas mot elprisetjustnu.se, som används oförändrat från 2021-11-01.
`el_spot` och `el_chg` finns nu från 2011-11 respektive 2011-12, med samma 70/30-viktning.
**Varför:** Fixen för dubbelräkning av el (femårig säsongsfaktor + el_chg) måste valideras
på 2015–2023, och då behövs elpriser före elkrisen.
**Skarv:** På överlappet 2021-11 till 2024-12 skiljer månadspriset i snitt 0,001 SEK/kWh
(max 0,005, ≈0,1 %) och `el_chg` högst 0,006. Det är försumbart, troligen växelkursskillnad.
Värdena från 2021-12 är exakt oförändrade.
**Modellen:** oförändrad. `ENERGY` tränar fortfarande från 2021-12, så backtesten 2024–2026
ger samma siffror (comp_fuel_el MAE 0,375).
**Även tillagt (används inte än):** SCB TAB6613 (KPIF per COICOP, alla nivåer), TAB3571
(andel elavtal) och TAB3950 (elnätspriser). Publiceringsfördröjning och revideringar står i
`docs/datakallor.md`. Två fällor: TAB3571 har reviderats i efterhand (2022, 2023–24) och
TAB3950 publiceras först i maj, alltså efter januari-KPI.

## 2026-11-22 – Ny ribba: "Riksbanken + senaste miss" (rb_updated), och regler för utvärdering
**Vad:** Ny huvudjämförelse `rb_updated` = Riksbankens prognos för t + dess kända miss för t-1
(KPIF utfall t-1 − Riksbankens prognos för t-1, samma prognosomgång). Gäller när prognosomgångens
cutoff ligger före t-1. Annars är den lika med Riksbankens prognos. Ingen parameter skattas.
Alla modeller jämförs mot den med ett enda Diebold-Mariano-test (absolutfel, Newey-West med
lag = ⌊4·(n/100)^(2/9)⌋, HLN-korrigering, t-fördelning). Varje körning loggas i
`experiments/runs/`.
**Varför:** Riksbankens prognos är oftast 2–3 månader gammal vid vår deadline. Inflationen är
trög, så förra månadens miss säger mycket om denna månads. Det är en ärligare ribba än den rena
prognosen. Felet växer med prognosens ålder: MAE 0,19 vid 1 månad, 0,30 vid 2 och 0,46 vid 3.
Med rb_updated blir det 0,19, 0,25 respektive 0,33.
**Resultat (körning `rb_updated_baseline`):**

| Modell | MAE 2015–26 (n=141) | DM p | MAE 2024–26 (n=34) | DM p |
|---|---|---|---|---|
| rb_updated | 0,256 | – | 0,267 | – |
| Riksbanken | 0,320 | 0,005 | 0,326 | 0,06 |
| Komponentmodell (drivmedel / drivmedel+el) | 0,316 | 0,03 | 0,375 | 0,008 |
| Naiv (samma årstakt) | 0,376 | <0,001 | 0,400 | 0,02 |

Minsta skillnad som går att upptäcka (5 %, 80 % styrka): ca 0,06–0,08 pe på 2015–26 och
0,08–0,15 pe på 2024–26.
**Regler från och med nu:**
- Modellval görs på **längsta möjliga sample** (i dag 2015–2026).
- 2024–2026 är **använd**. Där har ~50 varianter redan testats, så perioden rapporteras men får
  inte avgöra modellval.
- Hypotes och förväntat tecken skrivs här, i fältet "Min gissning innan", **före** varje körning.
- `tests/test_information_set.py` är ett *indexeringstest*: det klipper data vid deadline och kräver
  samma prognos som backtesten. Det är inget läckagetest. Reviderade siffror (vintage-läckage)
  fångas inte.
**Min gissning innan / vad som faktiskt hände:** Gissning: rb_updated slår Riksbanken med ~0,06 pe.
Utfall: 0,064 (2015–26) och 0,059 (2024–26). Ingen egen modell är i närheten av rb_updated.
**Öppna frågor:** Komponentmodellen med el kan bara utvärderas från 2024. Längre elhistorik behövs
för att modellvalet ska kunna göras på 2015–2026.

## 2026-11-22 – J2 Elmodellen på lång historik (förregistrering)
Hypotes, gissning och exakt variantlista (V1–V5): [docs/auto/j2/hypotes.md](auto/j2/hypotes.md). Resultat läggs till när jobbet är klart.
**Resultat (urvalsevidens, 5/50 varianter):** V2 `j2_el_dev` (el som avvikelse från samma kalendermånad
senaste ≤5 år) MAE 0,243 mot comp_fuel 0,316 på 2015–26, Holm p = 0,014: klarade urvalsskärmen. Mot
rb_updated 0,256 är p = 0,57, alltså ingen skillnad. Rå el ger −0,037, så dubbelräkningen var verklig.
Gissningen innan underskattade effekten (−0,02 till −0,04). V2 fryses som skuggprognos från 2026-12.
Detaljer: [docs/auto/j2/resultat.md](auto/j2/resultat.md).

## 2026-11-22 – J1 Hybridmodell (förregistrering)
Hypotes, gissning och exakt variantlista (C1–C4, H1–H4): [docs/auto/j1/hypotes.md](auto/j1/hypotes.md). Bas: auto/j2-done.
**Resultat (urvalsevidens, 13/50 varianter):** ingen variant klarade urvalsskärmen. Bäst var 50/50-snittet
av rb_updated och J2:s V2: MAE 0,217 mot 0,256 på 2015–26, ensidigt p = 0,015, Holm p = 0,117 över 8
varianter. Skattade vikter gav inget utöver 50/50. Gissningen innan stämde. Ingen frysning; förslag att
följa 50/50-snittet live. Detaljer: [docs/auto/j1/resultat.md](auto/j1/resultat.md).

## 2026-11-23 – J2 och J1 mergade till main
**Beslut (Johannes):** J2 (elmodellen) och J1 (hybriden) mergas. Huvudmodellen i `forecast.py` byts inte.
J2:s V2 och 50/50-snittet av rb_updated och V2 följs som skuggprognoser från 2026-12; byte av
huvudmodell avgörs av live-utfallet. Övriga auto/*-grenar (J3–J7) ligger kvar omergade.
**Inriktning framåt:** fokus på Sverige. Andra länder bara om datan går lätt att få fram.

## 2026-11-22 – J3 Prognostest av datakatalogen (förregistrering)
Protokoll, gissning och kombinationsregel: [docs/auto/j3/hypotes.md](auto/j3/hypotes.md). Bas rb_updated (h=1), Riksbanken (h=3, 12).
**Resultat (urvalsevidens, 14/50 varianter):** ingen av 45 serier överlever Benjamini-Hochberg på h=1, 3
eller 12. Kombinationen av de tre bästa h=1-serierna gav MAE 0,279 mot rb_updated 0,281 (p = 0,43).
Inget håller; behåll ingen serie. Detaljer: [docs/auto/j3/resultat.md](auto/j3/resultat.md).

## 2026-11-22 – J4 KPIF underifrån på detaljnivå (förregistrering)
Hypotes, gissning och varianter D1–D3: [docs/auto/j4/hypotes.md](auto/j4/hypotes.md). TAB6613 är omräknad → revised.
**Resultat (urvalsevidens, 17/50 varianter, obekräftat p.g.a. omräknad TAB6613):** D2 (el och drivmedel
på rätt delindex) MAE 0,243 mot comp_fuel 0,316, Holm p = 0,010. Bara grupper utan korrektion (D1) är sämre
(0,335). Påsken gav inget. Vinsten är densamma som J2 V2 utan detaljdata, så J2 V2 föredras. Kvarvarande fel:
paketresor, livsmedel, persontransporter. Detaljer: [docs/auto/j4/resultat.md](auto/j4/resultat.md).

## 2026-11-22 – J5 Prognosintervall (förregistrering)
Hypotes, gissning och metoder U1–U6: [docs/auto/j5/hypotes.md](auto/j5/hypotes.md).
**Resultat (urvalsevidens, 23/50 varianter):** EWMA-normaliserade band (U4) gav träffgrad 52/80/89 % och lägst
pinball; rullande 36 mån (U2) klarade också ±5 pe. Expanderande metoder, som dagens, undertäcker (40/62/77 %).
Att skala med elprisets svängning hjälpte inte; det är felnivåns skift över tid som spelar roll. I oroliga
månader är banden fortfarande för smala. Förslag till forecast.py finns men är inte aktiverat.
Detaljer: [docs/auto/j5/resultat.md](auto/j5/resultat.md).

## 2026-11-22 – J6 Arbetsförmedlingens varsel och inskrivna arbetslösa
**Vad:** Tre nya katalogserier i egen modul (`catalog_af.py`): varsel (1992–), inskrivna och öppet arbetslösa
(1996–), riket, månad, fördröjning 15 dagar. **Brott:** åldersgränsen höjs 2023 och 2026, men brottet syns inte
i januariförändringarna; varsel tas bara som riket totalt, så SNI-byten spelar ingen roll. Varsel är reviderad
(2025-06-30 från 2019-11). Ingen modellvariant. Detaljer: [docs/auto/j6/kvalitet.md](auto/j6/kvalitet.md).

## 2026-11-22 – J7 Svensk AI-indikator
**Vad:** AI-spridning = z-snitt av maskininlärningsandelen i platsannonser (JobTech) och andelen företag som
använder AI (Eurostat). Produktivitet per bransch (Eurostat nama_10_lp_a21) visas bredvid som utfall.
**Val efter resultat:** huvudserien skulle enligt planen vara "AI" (bredaste godkända termen), men den har ett
mätbrott 2025 i JobTech:s matchning (×10 på ett år). Därför används "maskininlärning". **Resultat:** spridningen
är 2025 den högsta i perioden; Sverige före EU i företagens AI-användning (35 mot 20 %); produktiviteten i
svensk IT och kommunikation +28 % 2023→2025 (EU +5 %), utan orsaksslutsats. Detaljer: [docs/ai-indikator.md](ai-indikator.md).

## 2026-11-23 – J3–J7 mergade till main
**Beslut (Johannes):** även J3 (katalogtest, negativt), J4 (detaljnivå, obekräftad), J5 (EWMA-band,
förslag, ej aktiverat i `forecast.py`), J6 (Arbetsförmedlingen) och J7 (AI-indikator) mergas, så att
körning 2 ([autonom-korning-2.md](autonom-korning-2.md)) kan bygga på dem. Huvudmodellen är oförändrad.

## 2026-11-23 – Nytt syfte: bästa möjliga lösning
**Beslut (Johannes):** projektet är inte längre ett lärprojekt. Det står på egna meriter, och målet är
bästa möjliga lösning: en så träffsäker KPIF-prognos som möjligt och den bästa bilden av läget i Sverige
sedd genom KPIF. Alla val ska ge snabb och effektiv progress med kvalitet. Kvalitetsreglerna gäller oförändrat:
inget läckage, jämförelse mot baslinje och Riksbanken, förregistrering och ärlighet om osäkerhet.
Pedagogiska hänsyn är inget mål i sig. `CLAUDE.md` och `docs/vision.md` är uppdaterade. Körning 2 pågår och fortsätter
med det nya syftet.

## 2026-11-23 – Agentic first: agenten mergar till main
**Beslut (Johannes):** projektet ska tänja gränserna för AI-agentiskt arbete. Agenten får committa, merga och
pusha till main när pytest är grönt och reglerna är uppfyllda. Parallella spår mergas av orkestreraren när de
är klara. GitHub Actions får aktiveras efter grön lokal körning. Johannes beslutar fortfarande om byte av
huvudmodell, och skarpa prognoser skrivs aldrig om (tidsstämpeln är beviset). Force-push och omskrivning av
historik är förbjudna. Skälet: förregistrering och läckagetester gör resultaten granskningsbara i efterhand, så
manuell merge är en flaskhals utan kvalitetsvinst.

## 2026-11-23 – Bedömning i agentlinsen
**Beslut (Johannes):** arbete bedöms i agentlinsen, inte människolinsen. Omfattning, tid och ambition dimensioneras
efter vad agenter klarar (parallellt, dygnet runt). Flaskhalsen är kvalitetskontroll och datatillgång. Står i CLAUDE.md.

## 2026-11-23 – K2 ML-spåret (förregistrering)
Hypotes, gissning och exakt variantlista (8 av K2:s 10): [docs/auto2/k2/hypotes.md](auto2/k2/hypotes.md).
Ridge/lasso/boosting på residualen mot 50/50, rb_updated och J2 V2, nästlad tidsserie-CV inom varje fönster.
**Resultat (urvalsevidens, 9 av K2:s 10 varianter, varav 1 diagnostik efter resultat):** tre varianter med
50/50 som bas klarade urvalsskärmen mot 50/50 (MAE 0,217): ridge på S + katalog 0,199 (Holm p = 0,014),
ensemble ridge+boosting på S 0,201 (Holm 0,055), ridge på S 0,206 (Holm 0,083). Vinsten kommer 2020–2025,
inte från reviderade serier; 2026 är något sämre. Gissningen innan (ingen klarar) var fel. Frysta vid 415ba6f;
föreslagen K1-kandidat `k2_avg_ens_s`. Detaljer: [docs/auto2/k2/resultat.md](auto2/k2/resultat.md).

## 2026-11-23 – K1 Drift: skuggprognoser i GitHub Actions (förslag, aktiveras vid merge)
**Vad:** `pipeline.py` (veckohämtning och prognoskörning som kommandon), skuggprognoser i
`forecasts/shadow/<modell>/<månad>.json` för den skarpa modellen (`comp_fuel_el`), J2 V2 och 50/50, offlineläge
som bygger om allt från `data/raw/`, DuckDB-datatester och en champion/challenger-tabell i SCORECARD.md.
**Val:** data i Actions-cachen (inget konto), låsta paketversioner, FINAL-skuggor skrivs aldrig över.
Inga nya varianter. Reproducerbarhet från ren klon + råcache är verifierad, men en helt nätbaserad hämtning
från noll är inte testad. Detaljer: [docs/auto2/k1/resultat.md](auto2/k1/resultat.md).

## 2026-11-23 – K0 Prisleden (förregistrering)
Nya serier i `catalog_prices.py`, screening enligt J3:s protokoll och varianterna K0-C1, K0-C2: [docs/auto2/k0/hypotes.md](auto2/k0/hypotes.md).
**Resultat (urvalsevidens, K0 förbrukar 2 varianter):** ingen av 29 prisledsserier överlever BH på h=1, 3 eller 12
(bäst h=1: PPI livsmedel −0,004, p = 0,32). K0-C1 (ppi_hmpi_food, rapsolja, SWESTR på rb_updated) ger +0,000.
K0-C2 (samma på 50/50-snittet) MAE 0,226 mot 0,232, Holm p = 0,097: klarade urvalsskärmen formellt men
obekräftad (revisionsläckage möjligt), bara aktiv 25 månader, alla i använda 2024–26. Inget håller; ingen
frysning. Serierna behålls i katalogen. Detaljer: [docs/auto2/k0/resultat.md](auto2/k0/resultat.md).

## 2026-11-23 – K3 Förklarade prognoser
**Vad:** `explain.py` förklarar varje prognos exakt. Den ger bidrag per komponent (trend, säsong, el, drivmedel),
förändringen i årstakt sedan förra utfallet, senaste miss och skuggornas skillnad mot den skarpa, med J5:s
EWMA-band som osäkerhet (förslag). Efter utfall delas felet per komponent. Steget körs i `pipeline monthly`
(inte fatalt) och skriver bara till `outputs/explain/`. 0 varianter.
**Resultat:** tjänster står för 37 % av kvadratfelet 2015–2026 och energi för 21 % (energi dominerade bara
2022–2023). Den skarpa modellens energifel 2024–2026 är 0,242 pe mot J2 V2:s 0,128 (använd period).
Detaljer: [docs/auto2/k3/resultat.md](auto2/k3/resultat.md).

## 2026-11-23 – K6 Bara om det är lätt (förregistrering)
Vintagekontroll för TAB6613 (0 varianter) och J2:s elmetod på dansk och finsk HIKP (N1, N2): [docs/auto2/k6/hypotes.md](auto2/k6/hypotes.md).
**Resultat (2 varianter, N1 och N2, ingen klarade urvalsskärmen):** vintages av TAB6613 finns inte (BLOCKED). Gammal och
omräknad svensk HIKP är praktiskt taget identiska för 04.5 och 07.2 (korrelation 1,000, medelskillnad 0,01 pe), så J4 D2:s
energivinst är ingen revisionseffekt. Elmetoden på Finland (SE3 som ombud) ger −0,011 (Holm p = 0,58), på Danmark (SE4)
+0,002 (0,86). Där slår spotpriset igenom i el-HIKP först månaden efter, medan svensk el-KPI följer samma månad (korrelation 0,9).
Detaljer: [docs/auto2/k6/resultat.md](auto2/k6/resultat.md).

## 2026-11-23 – K4 Regionala Sverige: en serie per mått och län
**Val:** länsdata lagras i den befintliga observationstabellen som en serie per mått och län,
`region_<mått>_<länskod>` (`00` = riket). Ingen ny kolumn behövs, och `as_of`, known_from och K1:s datatester
fungerar som för andra serier. Serierna ligger i `catalog.REGIONAL`, inte i `CATALOG`. Därför ändras inte
kandidatlistorna i J3/K2 och den nationella dashboarden. `by_key`, `refresh` och `warehouse` använder `catalog.ALL`.
241 serier, 11 mått (AF-andel och antal, varsel, BAS, AKU, småhuspris, FPI, konkurser, folkmängd), bara deskriptivt.
Inga modellvarianter. Länskarta BLOCKED (inget öppet länslager utan konto eller nytt GIS-paket), rutnätskarta i stället.
Detaljer: [docs/auto2/k4/resultat.md](auto2/k4/resultat.md), [kvalitet](auto2/k4/kvalitet.md), [läget](auto2/k4/lage.md).

## 2026-11-23 – K9 Längre horisont 3–12 mån (förregistrering)
Korrektion/krympning av Riksbankens prognos, 4 varianter (k9_ridge_h3, k9_ridge_h12, k9_shrink_h12, k9_miss_h6): [docs/auto2/k9/hypotes.md](auto2/k9/hypotes.md).
**Resultat (4 varianter, ingen klarade urvalsskärmen, alla Holm p = 1,00):** MAE 2015–2026 mot Riksbanken: h=3 ridge 0,471 mot 0,489 (rå p 0,33), h=6 miss 0,833 mot 0,814, h=12 krympning mot 2 % 1,485 och ridge 1,945 mot 1,388. Effektivt n ≈ 46/23/11. Riksbanken och "2 %" lika på h=12 (1,388/1,385). Ingen frysning; Riksbanken förblir referens på längre sikt. Detaljer: [docs/auto2/k9/resultat.md](auto2/k9/resultat.md).

## 2026-11-23 – K7 Tjänstekomponenten (förregistrering)
Robust säsong (median) och påsk-/januariregressorer för tjänstedelen, 5 varianter (T1–T5): [docs/auto2/k7/hypotes.md](auto2/k7/hypotes.md).
**Resultat (5 varianter, ingen klarade urvalsskärmen):** median-säsong och påsk-/januariregressorer gör tjänstedelen
sämre, inte bättre (m/m-MAE 0,157 → 0,160–0,162 2015–2026; 0,067 → 0,068–0,069 på den rena perioden 2000–2009).
Totalt T1–T4 −0,001 till +0,003 mot 50/50 (Holm 1), T5 +0,010 mot `k2_avg_ens_s`. Påskeffekten finns (≈ 0,01 pe per dag)
men är liten. Tjänstefelet är resor och går inte att förutse med data vi har vid deadline. Ingen frysning.
Detaljer: [docs/auto2/k7/resultat.md](auto2/k7/resultat.md).

## 2026-11-23 – K8 Livsmedelskomponenten (förregistrering)
Livsmedelsbidraget (TAB6628) prognostiseras från PPI livsmedel, IMF-råvaror i SEK, KIX och KI:s prisplaner med
laggar 1–6 mån; fyra varianter (fasta laggar, ridge med nästlad CV, ridge utan reviderade serier, K2-ensemblen +
livsmedel): [docs/auto2/k8/hypotes.md](auto2/k8/hypotes.md).
**Resultat (urvalsevidens, 4 av K8:s 4 varianter):** ingen klarade urvalsskärmen. Mot 50/50 (0,217): fasta laggar
0,214 (Holm p = 0,41), ridge 0,216 (0,41), ridge utan reviderade serier 0,215 (0,30); K2-ensemblen + livsmedel 0,201
mot 0,201 (0,55). Livsmedelsbidragets eget fel sjunker 10 % med fasta laggar (0,076 → 0,069 pe), 35 % 2022–23, men
i totalen blir det ≤ 0,002 pe. Ingen frysning. Nästa kandidat: skatterensad livsmedelsbas (momssänkningen 2026-04).
Detaljer: [docs/auto2/k8/resultat.md](auto2/k8/resultat.md).

## 2026-11-23 – K5 Sverigeläget v2 och månadsbrev
**Val:** dashboardens sida versioneras nu i repot (`src/kpif_nowcast/templates/sverige_index.html`) och kopieras till
`outputs/sverige/index.html`; `outputs/sverige/MANIFEST.json` listar alla filer som ska laddas upp. Nya dataset:
länen (K4, rutnätskarta), Arbetsförmedlingen (J6), AI-indikatorn (J7:s metod räknad på observationstabellen, eftersom
J7:s råcache inte finns och ingen ny hämtning gjordes), prisleden (K0), prognoserna med skuggor märkta "urvalsevidens",
champion/challenger och K3:s förklaring. Månadsbrevet (`python -m kpif_nowcast.manadsbrev <månad>`) har
informationsdatum = tidigast av i dag och månadens deadline och använder bara data kända då (observationstabellen
klipps på known_from, prognosfiler på made_at, processad data som i `tests/test_explain.py`). Steg i
`pipeline monthly` (inte fatalt), committas av månadsjobbet. Inga modellvarianter.
Detaljer: [docs/auto2/k5/resultat.md](auto2/k5/resultat.md).

## 2026-11-23 – K2b: oberoende granskning av K2, K2-skuggor i driften
**Dom: håller med förbehåll.** K2:s mekanik läcker inte, men Eurostats flash för december (och mars 2018,
januari 2026) publiceras efter deadline medan backfillen sa periodslut + 2 dagar. `ea_news` läckte därmed.
Efter rättelsen klarar `k2_avg_ridge_l` (MAE 0,200, Holm 0,025) och `k2_avg_ens_s` (0,202, Holm 0,083)
fortfarande urvalsskärmen mot 50/50 (0,217). `k2_avg_ridge_s` gör det inte (Holm 0,19). Vinsten sitter
2020–25, och 2026 är sämre. L:s katalogfeatures frystes (hade vuxit 43 → 72 när K0 mergades). **Beslut:** de två
registreras som skuggor med flashrättelsen, och de blir FINAL före dag 4 först när flashen finns. Inga nya varianter.
Detaljer: [docs/auto2/k2b/granskning.md](auto2/k2b/granskning.md), [resultat](auto2/k2b/resultat.md).

## 2026-11-23 – K12 Globalt test över alla varianter

Inga nya varianter (0 förbrukade). Alla 31 registrerade h=1-varianter med fel 2015–2026 (J1–J4, K0, K2, K7) plus
referenserna, gemensamt urval n = 141: Hansens SPA, Romano–Wolf StepM och Model Confidence Set med stationär bootstrap
(medelblock 3 mån; känslighet 1, 6, 12). **`k2_avg_ridge_l` håller även globalt**: SPA p 0,035 mot rb_updated och
0,018 mot 50/50 (högst 0,083 resp. 0,040 för block 3–6), StepM pekar ut den mot båda. Men marginalen mot 50/50
(0,018 pe) är mindre än den råa urvalsbiasen (förväntat bästa under H0 0,022 pe); den håller för att korrektionen är
liten och stabil (studentiserat). MCS (90 %) behåller 32 av 34 modeller: datan räcker inte för att rangordna de flesta.
Omkörbart: `python -m kpif_nowcast.k12_global` (K8 tas med automatiskt). Detaljer:
[docs/auto2/k12/resultat.md](auto2/k12/resultat.md).

## 2026-11-23 – K13 Skatterensad bas (förregistrering)
Säsong och trend skattas på bidrag där identifierade skatteengångshändelser (KS-delen, per komponent) är borttagna; effekten läggs tillbaka i prognosmånaden bara om beslutet är fattat före deadline. 2 varianter (`k13_j2_clean`, `k13_ens_clean`): [docs/auto2/k13/hypotes.md](auto2/k13/hypotes.md).
**Resultat (urvalsevidens, 2 varianter, ingen klarade urvalsskärmen):** `k13_j2_clean` 0,239 mot J2 V2 0,243 (rå p 0,27, Holm 0,54), `k13_ens_clean` 0,203 mot 0,201 (Holm 0,73). Utan händelsemånaderna är skillnaden noll; momsen 2026-04 fångas, men drivmedelssänkningarna slår inte igenom fullt samma månad. **Skarp prognos 2026-11:** rensad bas ger +0,13 pe (2,05 → 2,18) → förslag `--adjust` ~+0,15 inkl. månadskort (manuell justering, inte modelländring). December: +0,40 pe när koldioxidskattesänkningen upphör, +~0,15 månadskort. Kalender: [docs/skattekalender.md](skattekalender.md). Detaljer: [docs/auto2/k13/resultat.md](auto2/k13/resultat.md).
