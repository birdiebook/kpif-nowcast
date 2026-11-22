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
| SCB EN0301 ✅ | Elhandelspriser per avtalstyp och elområde; andel avtalstyper | Månad | 2013M04 | ~1–2 mån | v1 (flytta till v2) | CC0 | 3 |
| SCB EN0301 ✅ | Elnätspriser 1 januari | År | 1996 | – | v1 | CC0 | 3 |
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
- **El före 2015:** ingen gratis källa med spridningsrätt (Nord Pool kostar ca 5 000 EUR/år).
  Vi klarar oss med 2015 och framåt.
- Ingen prognosmarknad för svensk inflation (kontrollerat på Kalshi och Polymarket).

## Tekniska noter

- SCB PxWebApi **v2**: `https://statistikdatabasen.scb.se/api/v2/`. v1 stängs runt årsskiftet 2026/27.
  Max 30 anrop per 10 s, 150 000 celler per anrop.
- Konjunkturinstitutets API är PxWeb v1. POST-frågan behöver rätt variabelkoder (ej löst än).
