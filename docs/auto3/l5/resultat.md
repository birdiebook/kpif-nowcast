# L5 El: rörliga avtal och elnätsavgifter

Spår L5 i körning 3 (våg 1, datainsamling). Ingen modell och inget prognostest här. Det görs i våg 2.

## Vad som byggdes

- `src/kpif_nowcast/catalog_el.py`: 12 nya katalogserier i området *Energi och råvaror*, registrerade i
  `catalog.py` direkt efter `catalog_prices`. Rådata cachas i `data/raw/l5/` med hämtdatum.
- Källor, alla öppna och utan nyckel:
  - **SCB TAB3571** (EN0301): fördelning av hushållens elavtal per avtalstyp, riket, månad från 2013-04.
    Det är rätt tabell för briefens "andel rörliga avtal". Den används redan i `data.build_el_contracts` och J2.
  - **SCB TAB3950** (EN0301, helår): elnätspriser per 1 januari, öre/kWh exkl. skatter, per kundkategori.
    Viktat från 2015, oviktat från 1996.
  - **Energimarknadsinspektionen (Ei)**, sidan *Nätavgifter – elnät*: alla nätbolags inrapporterade tariffer
    per 1 januari för typkunder, arkivfil 1999–2026 (xlsx). Länken läses från sidan, eftersom fil-URL:en byts
    vid varje uppdatering, med senast kända länk som reserv. Filen läses med `sources/xlsx_lite`, så inget nytt
    beroende behövs. Vi beräknar median över nätområden av total årsavgift (kr/år exkl. moms) och andelen
    nätområden som höjt avgiften jämfört med året före.
- `tests/test_l5_el.py`: 9 tester utan nät. De täcker Ei-arkets layout, att nollor tas bort, parningen över
  radbrottet 2003/2004, länkhittaren, summeringen av avtalstyper, att årsvärden hamnar på december,
  informationsmängden vid januari-deadline, samt observationstabellen när den finns.
- Publiceringskalendern har fått sektionen `## Körning 3: L5` med belägg, och datakatalogen har 12 nya rader.

## Serier

| Nyckel | Frekv. | Från | Fördröjning | Rev. |
|---|---|---|---|---|
| `el_contract_spot_share` (rörligt månadspris + tim-/kvartspris) | M | 2013-04 | 28 d | ja |
| `el_contract_hourly_share` (tim-/kvartspris) | M | 2023-02 | 28 d | ja |
| `el_contract_fixed_share` (fast 1–3 år) | M | 2013-04 | 28 d | ja |
| `el_contract_default_share` (anvisat) | M | 2013-04 | 28 d | ja |
| `el_grid_price_flat`, `_house`, `_house_heat` (SCB, viktat) | A | 2015 | 0 d | nej |
| `el_grid_price_house_heat_unw` (SCB, oviktat) | A | 1996 | 0 d | nej |
| `ei_grid_fee_flat`, `_house`, `_house_heat` (Ei, median) | A | 1999 | 0 d | ja |
| `ei_grid_fee_raise_share` (Ei, andel som höjt) | A | 2000 | 0 d | ja |

**Fördröjning och belägg:**
- **TAB3571:** september 2026 publicerades 2026-10-23. Oktober 2026 är planerad till 2026-11-24
  (scb.se/en0301), och Ei skriver "runt den 22:a … med en månads fördröjning". Vi sätter 28 d. Vid deadline
  för månad t är t−1 känd. Revised=ja, eftersom tabellnoten dokumenterar revideringar för 2022 och 2023–24.
  Rättelserna ligger som sena releaser: maj 2023–juni 2024 är känd först 2024-09-27 (rättelsedatum) och
  jan–mar 2022 först 2022-04-30 ("April 2022", dag okänd). De felaktiga förstautgåvorna finns inte kvar.
  Sommarmånaderna (juni → juli/augusti) är inte verifierade mot 28 d.
- **TAB3950 och Ei:** år Y avser tariffen per 1 januari Y. 2026 publicerades i maj–juni (SCB 2026-05-22,
  Ei 2026-05-12 och arkivfilen 2026-06-11), men tidigare år är inte belagda och kan ha kommit senare
  (kvalitetsdeklarationen för 2023 är daterad 2024-09-25). Därför fördröjning 0 d mot december: känt från
  31 december år Y. Informationen vid januari-deadline Y+1 blir densamma som med maj-datumet.
  Ei har revised=ja, eftersom sena eller rättade inrapporteringar kan flytta medianen. 2024–2026-värdena i
  maj- och junifilerna var identiska (442 par), så någon revidering är inte påvisad, bara möjlig.

**Brott i serierna:**
- Timpris redovisas separat först från 2023-02. Var avtalen låg innan anges inte; i skiftet jan–feb 2023 kom
  ca 2/3 ur "rörligt" (−6,5 pe mot timpris +10,4) och resten ur fast pris (−1,9), anvisat (−0,9) och övriga
  (−0,9). Brottet syns alltså i alla andelar, inte bara spot-andelen (där ett saknat timpris räknas som 0,
  hopp ca +4 pe).
- De viktade TAB3950-serierna finns från 2015, men vikterna infördes senare och räknades bakåt
  (metodändring enligt tabellnoten; införandeår anges inte). 2015 till införandeåret är som-om-historik.
  Använd `el_grid_price_house_heat_unw` eller Ei-medianen för test bakåt.
- Ei-medianen räknas över ett krympande antal nätområden (151 med värde 2019, 116 2026), så
  förändringen i medianen innehåller en sammansättningseffekt. Använd parvis förändring (samma nätområde)
  för ändringar i våg 2.
- Från 2025-02 ingår kvartsprisavtal i timpris.
- Ei 2026: myndighetsavgiften ändrades i efterhand (beslut 29 januari 2026), så inrapporteringen är blandad.

## Inte tillagt eller BLOCKED

- **Nätbolagens aviserade höjningar inför kommande 1 januari** (meddelas kunderna under hösten) är den enda
  informationen om januari år Y som finns vid deadline. Det finns ingen öppen samlad källa, varken hos Ei eller
  SCB. Att skrapa enskilda nätbolag är inte gjort. **BLOCKED:** källa saknas.
- **SCB TAB4310** (nätpris per halvår, öre/kWh) är inte tillagd. Katalogen och lagrets hålkontroll stöder bara
  M/Q/A, och halvår skulle kräva frekvensen "H" i `warehouse.py`. Informationen täcks i stort sett av TAB3950.
- **Ei:s viktade nätavgift** är inte byggd. Antal uttagspunkter finns bara i filen för 2022–2026, och SCB:s
  viktade TAB3950 täcker samma sak.
- **TAB4480** (omförhandlade avtal) och **TAB3819** (erbjudna priser per avtalstyp) är inte tillagda. De kan
  bli aktuella i våg 2 om januari-repricing av fastprisavtal visar sig spela roll.

## Läget i Sverige enligt serierna

- **Nästan alla hushåll har nu spotkopplat elpris.** Andelen rörliga avtal (månad + tim/kvart) var 74,7 % i
  september 2026, mot 36 % 2013 och 58 % i slutet av 2022. Fastprisavtalen har fallit från 26 % (slutet av
  2021) till 7,5 %, och anvisade avtal ligger stilla runt 8 %. KPIF-el följer alltså spotpriset mer direkt än
  någonsin. Månadssvängningarna blir större, och fastprisförnyelsen i januari betyder mindre än före 2022.
- **Nätavgifterna har stigit kraftigt och brett.** Elnätspriset för villa med elvärme (SCB, viktat) steg
  15,9 % 2023, 3,5 % 2024, 10,1 % 2025 och 7,1 % 2026. Ei:s median för villa 20A/20 000 kWh ligger på
  9 301 kr/år 2026, mot 6 840 kr/år 2021. Andelen nätområden som höjde var 96–99 % 2022, 2023 och 2025, 76 %
  2024 och 73 % 2026. 2026 är alltså ingen avvikelse: höjningarna varierar i bredd mellan år, men nivån
  fortsätter uppåt. Före 2022 var bilden en annan: 2020–2021 höjde bara 50–59 % och priset för villa med
  elvärme föll (−1,7 % och −3,3 %). Ei:s nya krav på
  prismodell (tidsdifferentierad effektavgift senast 1 januari 2027) kan ge ett strukturbrott i januari 2027.

## Hur serierna kan förklara januarimissen (vision: "januari är svårast")

KPIF-el ändras i januari av fyra saker: spotpriset (vägt med andelen rörliga avtal), fastprisavtal som
prissätts om, nätavgiften (ändras 1 januari) och energiskatten (K13:s skattekalender). Beskrivande tal,
utan test: KPIF-el m/m i januari 2010–2026 har ett medelabsolutvärde på 6,5 %, mot 4,0 % övriga månader.
Nätavgiften har ändrats −3 till +16 % per år 2016–2026 och varit positiv varje år sedan 2022. Den är ca 25–40 % av hushållens totala elpris (SCB TAB4310,
2024–2026, nätpris exkl. moms mot totalpris inkl. skatt och moms; lägre andel vid hög förbrukning).
Det motsvarar grovt 0–6 pe på januari-m/m i KPIF-el. Det är litet mot spotsvängningarna
(t.ex. −27 % 2023 och +21 % 2026), men det är systematiskt. Tecknet har varit positivt sedan 2022, inte
alltid (2020–2021 negativt), så en januarikorrektion får inte förutsätta positivt tecken.

**Läckagefälla:** årets nättariff publiceras i maj, alltså efter januari-KPI. Vid deadline för januari Y finns
bara:
1. andelen rörliga avtal t.o.m. december Y−1 (`el_contract_*`, ≤ 28 d; för maj 2023–juni 2024 först från
   2024-09-27)
2. fjolårets nätprishöjning (Y−1 mot Y−2) och andelen som höjde (kända från 31 december Y−1). Båda kan
   användas som persistensskattning; höjningarna har följt varandra sedan 2022, men inte före.

`as_of` ger detta automatiskt, och testet `test_january_deadline_sees_last_year_grid_and_previous_month_contracts`
låser det.

## Förslag till våg 2

1. **Spot × andel rörliga** som el-feature: J2:s `el_dev_var` gjorde det med lokal TAB3571-data, och
   `el_contract_spot_share` gör samma sak i observationstabellen med versioner. Andelen är revised, så
   resultatet ska märkas.
2. **Januari-dummy × fjolårets nätprisändring** (`el_grid_price_house_heat` årstakt, eller
   `ei_grid_fee_raise_share`) som korrektion av energikomponenten bara i januari. Det finns få observationer
   (11 med viktat, 26–30 med oviktat eller Ei), så det ska vara högst en parameter och förregistreras.
   Alternativet är att använda serierna som underlag för manuell `--adjust` i januari tillsammans med L1:s
   kalender, vilket Johannes beslutar.
3. **Efterhandsförklaring:** dela upp januarimissen i el i delarna spot, nät och skatt, för scorecard.

## Granskning

En oberoende granskare lämnade åtta fynd. Alla kontrollerades mot källan (cachad TAB3571-not, Ei-filen och
observationstabellen).

| Fynd | Dom | Åtgärd |
|---|---|---|
| Läcka: TAB3571 maj 2023–jun 2024 rättades 2024-09-27 men låg som känt ~28 d efter månaden | Stämmer (tabellnoten) | Rättat: sena releaser i `publication.LATE_RELEASES` för alla fyra `el_contract_*` (2023-05..2024-06 → 2024-09-27, 2022-01..03 → 2022-04-30, sista april eftersom dagen saknas), tabell i publiceringskalendern, test `test_contract_corrections_known_only_from_correction_date` |
| Fel: −180 d för årsserierna vilar på ett enda år (2026) | Stämmer | Rättat: `LAG_GRID` = 0 (känt 31 december Y). Januari-deadline Y+1 ser samma sak som förut, juli–december slipper risken. Release-datum för 2023–2025 är inte verifierade |
| Fel: "96–99 % 2022–2025" för andel som höjt | Stämmer (2024 = 76,4 %) | Rättat i texten; slutsatsen att 2026 avviker är struken |
| Fel: "0–16 % per år, samma tecken varje år" | Stämmer (2020 −1,7 %, 2021 −3,3 %) | Rättat: −3 till +16 % 2016–2026, positivt sedan 2022 |
| Mindre: brottet 2023-02 bara dokumenterat för spot-andelen | Stämmer (verifierat i TAB3571) | Rättat i katalognoten och här; "främst i rörligt" ersatt med "ca 2/3 ur rörligt" |
| Mindre: viktade TAB3950 från 2015 är bakåträknade | Rimligt (tabellnoten) | Dokumenterat i noten och här; införandeåret är okänt |
| Mindre: sammansättningseffekt i Ei-medianen | Stämmer | Dokumenterat i noten och här; parvis förändring rekommenderas för våg 2, inte byggt |
| Mindre: sommarmånaderna för TAB3571 inte verifierade | Stämmer | Ingen ändring, noterat ovan |

Inget fynd avvisades. Observationstabellen är omräknad för L5 (708 rader, inga dubbletter, known_from ≥
periodens slut).
