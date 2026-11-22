# Datakällor

Kartlagt 2026-11-22. ✅ = anropat/verifierat, ⚠️ = ej verifierat eller begränsning.

## Viktiga insikter

1. **SCB bytte system i januari 2026.** KPI går nu enligt COICOP 2018 med 2020=100.
   De gamla tabellerna (TAB5919 m.fl.) uppdateras inte längre. Använd bara de nya tabell-ID:na nedan.
2. **Snabb-KPI finns sedan oktober 2024.** SCB publicerar en preliminär KPIF ungefär den 5–8:e,
   en vecka före den slutliga siffran, och den träffar nästan exakt (medelavvikelse ≈ 0,01 procentenheter).
   → **Vår prognos måste vara klar före snabb-KPI:n**, annars är det inte en prognos.
3. **KPI revideras inte** (SCB:s revideringspolicy). Målvariabeln är alltså stabil och vi
   behöver inga historiska "vintages" av KPIF. Undantag: KPIF är inte formellt låst, men det revideras i praktiken sällan ⚠️.
4. **Vikterna byts varje januari** (baserat på år t-2). Januari är också månaden för
   nya elnätsavgifter och skatter. Januari blir därför en specialmånad i modellen.
5. **El mäts inte som spotpris.** SCB väger ihop rörliga avtal (spot samma månad), fastpris
   och tillsvidarepris, plus nätavgift och energiskatt. Spotpriset påverkar alltså bara via
   andelen rörliga avtal, och den publicerar SCB.
6. **Drivmedel mäts som snittpris den 1–25:e** i månaden från bolagens transaktionsdata.

## Målvariabel och riktmärken

| Källa | Vad | Frekvens | Från | Publiceras | Åtkomst | Villkor |
|---|---|---|---|---|---|---|
| SCB TAB6590 ✅ | KPIF index, m/m, å/å | Månad | 1987M01 | ~12–15:e månaden efter, 08:00 | PxWebApi v2 | CC0 |
| SCB TAB6593 ✅ | KPIF-XE (exkl. energi) | Månad | 1987M01 | Samma | v2 | CC0 |
| SCB TAB6601 ✅ | KPIF per COICOP-huvudgrupp + vikter | Månad | 1987M01 | Samma | v2 | CC0 |
| SCB TAB6628 ✅ | KPIF analysgrupper (tjänster, livsmedel, energi, varor) med vikter och bidrag | Månad | – | Samma | v2 | CC0 |
| SCB TAB6394 ✅ | Snabb-KPI (KPI, KPIF, KPIF-XE, 2 decimaler) | Månad | 2024M08 | ~5–8:e månaden efter | v2 | CC0, "statistik under utveckling" |
| Riksbanken ✅ | KPIF-prognoser, månadsvis, 60 prognosomgångar 2015–2026 | 4–6 omgångar/år | 2015 | Vid penningpolitiska beslut | `api.riksbank.se/monetary_policy_data/v1/forecasts` | Fri återanvändning |
| Infront/Bloomberg-konsensus ⚠️ | Bankekonomernas prognos inför varje utfall | Månad | – | Före utfall | Bara i nyhetstelegram | Ingen datamängd, skippas |

**Notera:** Riksbankens senaste prognos är oftast 2–4 månader gammal när ett utfall kommer.
Det är ett rättvist men lite generöst riktmärke för oss.

## Förklarande variabler

| Källa | Vad | Frekvens | Från | Fördröjning | Åtkomst | Villkor | Fas |
|---|---|---|---|---|---|---|---|
| ENTSO-E ⚠️ | Elspotpris SE1–SE4 | Timme | ~2015 | Dagen före | API, gratis token (registrering) | Återanvändning med källhänvisning | 3 |
| elprisetjustnu.se ✅ | Elspotpris SE1–SE4 | Timme/15 min | 2021-11-01 | Dagen före | Öppet JSON-API | Fritt, källhänvisning | 3 |
| Energinet Energi Data Service ✅ | Elspotpris SE3, SE4 (dataset `Elspotprices`, EUR/MWh) | Timme | 2011-11-01 | Dagen före | `api.energidataservice.dk`, ingen nyckel, ~1 dataanrop per 5 min | CC BY 4.0, "Source: Energinet (www.energidataservice.dk)" | 3 |
| SCB EN0301 ✅ | Elhandelspriser per avtalstyp och elområde | Månad | 2013M04 | ~1–2 mån | v1 (flytta till v2) | CC0 | 3 |
| SCB TAB3571 ✅ | Andel elavtal per avtalstyp och elområde (%) | Månad | 2013M04 | Månad m publiceras ~23:e i m+1 → vid deadline känd t.o.m. t-1 | v2 | CC0 | 4b |
| SCB TAB3950 ✅ | Elnätspriser 1 januari, öre/kWh exkl. skatt, 4 kundkategorier | År | 1996 | Publiceras ~maj samma år (2026 uppdaterad 2026-05-22), alltså *efter* januari-KPI | v2 | CC0 | 4b |
| SCB TAB6613 ✅ | KPIF per COICOP 2018, alla nivåer (~390 koder): index, m/m, å/å, vikt, bidrag | Månad | 1987M01 | Samma som KPIF | v2, 15 koder per anrop | CC0 | 4b |
| FRED ✅ | Brent råolja (DCOILBRENTEU) | Dag | 1987 | Några dagar | CSV, ingen nyckel | Public domain | 3 |
| Riksbanken SWEA ✅ | SEK/EUR, SEK/USD, KIX, styrränta | Dag | 1992–94 | Samma dag | `api.riksbank.se/swea/v1`, ingen nyckel (5 anrop/min) | Fri återanvändning | 3–5 |
| Drivkraft Sverige ⚠️ | Listpriser bensin/diesel | Dag? | ? | – | Inbäddade tabeller, inget API | Oklart | 3 |
| SCB TAB3184 ✅ | Producent- och importprisindex | Månad | 1990M01 | ~25 dagar | v2 | CC0 | 4 |
| Konjunkturinstitutet ✅ | Företagens förväntade försäljningspriser (totalt, industri, handel inkl. dagligvaror, tjänster) | Månad | 1996–2001 | Publiceras i slutet av samma månad | PxWeb v1 `statistik.konj.se` | ⚠️ ej kontrollerat | 4 |
| Konjunkturinstitutet ✅ | Hushållens inflationsförväntningar 12 mån | Månad | 2001M12 | Samma | PxWeb v1 | ⚠️ | 4 |
| Origo/Prospera ✅ | Inflationsförväntningar 1, 2, 5 år | Månad | ~2005 | – | XLSX | ⚠️ | 5 |
| SCB TAB6387 ✅ | AKU arbetslöshet (säsongsjusterad) | Månad | 2001M01 | ~20 dagar | v2 | CC0 | 5 |
| SCB TAB443 ✅ | BNP-indikatorn | Månad | 2000M01 | ~29 dagar | v2 | CC0 | 5 |

## Luckor

- **Drivmedel:** ingen ren daglig källa med API. Plan: Brent × USD/SEK som ersättare,
  plus SCB:s eget drivmedelsindex med en månads fördröjning.
- **El före 2021-11:** löst via Energinet (SE3/SE4 från 2011-11, CC BY 4.0). SE1/SE2 finns inte
  där, men de ingår inte i vår viktning. Före 2011-11 fanns inga elområden (ett svenskt pris).
- Ingen prognosmarknad för svensk inflation (kontrollerat på Kalshi och Polymarket).

## Tekniska noter

- SCB PxWebApi **v2**: `https://statistikdatabasen.scb.se/api/v2/`. v1 stängs runt årsskiftet 2026/27.
  Max 30 anrop per 10 s, 150 000 celler per anrop.
- Konjunkturinstitutets API är PxWeb v1. POST-frågan behöver rätt variabelkoder (ej löst än).

## Elhistorik: Energinet + elprisetjustnu.se (kontrollerat 2026-11-22)

- **Licens:** CC BY 4.0 enligt energidataservice.dk/terms-and-conditions. Kopiering, ändring och
  spridning är tillåten, även kommersiellt. Krav: källhänvisning ("Source: Energinet
  (www.energidataservice.dk)") och att man anger om datan ändrats (vi räknar om till SEK/kWh
  och dygnsmedel). Ingen garanti för fortsatt tillgänglighet → därför cachas rådatan.
- **Rate limit:** opublicerad och olika per dataset. I praktiken ett dataanrop per ~5 min
  (HTTP 429 med `Retry-After` ≈ 260 s). `limit=0` ger alla rader. Vi hämtar 7 tvåårschunkar
  (~35 000 rader var) och sparar varje svar i `data/raw/energinet/` med hämtdatum. En cachad
  chunk hämtas aldrig igen. Hela hämtningen tar ~35 min: `python -m kpif_nowcast.sources.energinet`.
- **Dataset:** `Elspotprices` slutade uppdateras efter 2025-09-30 (efterträdare `DayAheadPrices`).
  Det spelar ingen roll, eftersom vi bara använder det före 2021-11.
- **Valuta:** priset i EUR/MWh räknas om med Riksbankens dagliga SEK/EUR-fixing (SEKEURPMI),
  framåtfylld över helger. Dygn = svensk (= dansk) lokal tid.
- **Skarv:** Energinet används för dagar före 2021-11-01, elprisetjustnu.se från och med den
  dagen. elprisetjustnu-värdena är oförändrade, så `el_spot` och `el_chg` från 2021-12 är
  identiska med tidigare. Skarvkvaliteten mäts på överlappet 2021-11 till 2024-12 (se nedan).
- **Läckage:** day-ahead-priser fastställs dagen före leverans och revideras inte.

**Täckning och skarvkvalitet (hämtat 2026-11-22):**

- Energinet SE3 och SE4: 2011-11-01 till 2024-12-31, 115 440 timmar per zon, inga luckor och
  inga saknade priser (23 resp. 25 timmar bara vid sommartidsbyten).
- `el_spot` finns nu från 2011-11 och `el_chg` från 2011-12 (179 månader, tidigare 59), utan luckor.
- Överlapp 2021-11 till 2024-12 (1 157 dagar), Energinet minus elprisetjustnu.se, SEK/kWh:
  - Per dag: medel −0,0006 (SE3) / −0,0008 (SE4), std ~0,005, max ±0,05. 29 dagar avviker mer än 0,02.
  - Viktad månad (70/30): medelavvikelse −0,0007, MAE 0,0010, max 0,0050 (≈0,1 %).
  - `el_chg` per månad: MAE 0,0011, max 0,0063. Korrelation 0,999996.
- Avvikelsen kommer sannolikt från växelkursen. Vi använder Riksbankens fixing,
  elprisetjustnu.se använder en annan kurs (troligen ENTSO-E:s/ECB:s). Ej verifierat.
  Med dagens elkoefficient (~0,9) ger skarvfelet högst ~0,006 pe på KPIF, vilket är försumbart.
- Månaden 2021-11 är den enda där `el_chg` blandar källor (oktober från Energinet, november från
  elprisetjustnu). Den ligger före träningsstarten 2021-12 för dagens modell.

## Publiceringsfördröjning och revideringar (vintage-risk) för nya SCB-tabeller

| Tabell | Fördröjning | Revideras? | Konsekvens |
|---|---|---|---|
| TAB6613 KPIF per COICOP | Som KPIF (~12–15:e i t+1) | KPI revideras inte, **men** allt före 2026 är SCB:s bakåtberäkning till COICOP 2018, "delvis modellskattad" (SCB:s fotnot). | Historiken är inte exakt vad som publicerades då. Ingen läckage av framtida *priser*, men indelningen är efterhandskonstruerad. Bidrag (`effect_month`) saknas för totalen (00). Några av de 398 koderna saknar helt värden. |
| TAB3571 andel avtalstyper | Månad m ~23:e i m+1. Vid deadline för t är t-1 senast kända. | **Ja.** Jan–mar 2022 reviderades i april 2022. Maj 2023–jun 2024 korrigerades 2024-09-27. Från 2025-02 slås kvarts- och timprisavtal ihop. | Hämtad historik är senaste vintage, inte vad som var känt då. Revideringarna är kända och avgränsade, men backtester som använder 2022–2024 bör vara medvetna om det. |
| TAB3950 elnätspriser 1 jan | Årets värde publiceras ~maj (2026-utgåvan 2026-05-22), alltså *efter* januari-KPI. | Inget dokumenterat. Metodbyte 2015: viktade priser från 2015, oviktade hela serien. | För prognos av januari år Y är årets nätpris **inte** publicerat vid deadline. Använd bara år Y-1, eller nätbolagens egna aviseringar. Använd oviktad serie för lång historik. |

Processade filer: `data/processed/cpif_detail.csv`, `el_contracts.csv`, `el_grid_prices.csv`
(`python -m kpif_nowcast.data`). De hämtas inte av `forecast.py` (bara `refresh()`), för att hålla
den skarpa körningen snabb.
