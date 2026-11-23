# K6 resultat: Bara om det är lätt

Förregistrering: [hypotes.md](hypotes.md). Kod: `src/kpif_nowcast/k6_nordic.py`, test `tests/test_k6_nordic.py`.
Körning: `experiments/runs/20261123T091208Z_k6_nordic.csv`. Rådata och fler tabeller: [results_raw.md](results_raw.md).
**Varianter: 2 förbrukade (N1, N2).** Körning 2: 13 av 30, projektet: 36. Ny data: sex Eurostat-svar i `data/raw/k6/`.

## Del 1: vintages för TAB6613 → BLOCKED, men datakontrollen gick att göra
**BLOCKED:** riktiga vintages av COICOP 2018-grupperna finns inte, eftersom de publicerades första gången 2026.
Riksbanken och KI arkiverar inga KPI-detaljindex, och ALFRED har inga KPIF-detaljserier. "D2 med vintage-data"
gick därför inte att köra. 0 varianter.

**Ersättningskontroll:** Eurostat har kvar den gamla svenska HIKP:n (ECOICOP 1, fryst 2025-12) bredvid den nya
omräknade (COICOP 2018). Månadsförändring 2001–2025, n = 300:

| Jämförelse | Korrelation | Medelabs. skillnad, pe | Max, pe |
|---|---|---|---|
| HIKP ny mot gammal, 04.5 el, gas m.m. | 1,0000 | 0,010 | 0,18 |
| HIKP ny mot gammal, 07.2 drift av fordon | 1,0000 | 0,010 | 0,13 |
| TAB6613 04.5 mot HIKP gammal 04.5 | 0,9987 | 0,41 | 3,3 |
| TAB6613 07.2 mot HIKP gammal 07.2 | 0,9963 | 0,04 | 1,6 |

- Det förregistrerade kriteriet (korrelation ≥ 0,98 och medelabsolut skillnad ≤ 0,10 pe, gammal mot ny HIKP) är
  uppfyllt för båda energigrupperna. **Omräkningen har praktiskt taget inte ändrat el- och drivmedelsgrupperna.**
  D2:s vinst mot comp_fuel kommer från dem, så den vinsten beror inte på revision.
- TAB6613 04.5 har samma rörelser som HIKP (korrelation 0,999) men en annan nivå på utslagen: medelskillnaden är
  0,41 pe. Det beror troligen på att KPIF och HIKP väger el, gas och fjärrvärme olika. Det säger inget om revision.
- Summan av TAB6613:s 43 bidrag stämmer med den publicerade KPIF-månadsförändringen, som inte revideras:
  medelavvikelse 0,004 pe, max 0,015 pe (avrundning), n = 466.
- **Andra grupper har ändrats kraftigt:** i division 09 (fritid) och delar av 08 och 12 är korrelationen mellan
  gammal och ny kod nära noll (09.2, 09.6, 08.1, 12.1). Där har samma kod fått nytt innehåll i COICOP 2018
  (09.6 var paketresor i ECOICOP 1; i COICOP 2018 ligger de under 09.8). D1-baslinjerna
  för de grupperna bygger alltså på serier som inte fanns i realtid.
- **Slutsats:** D2 förblir märkt "obekräftad (revisionsläckage möjligt)", eftersom 41 grupper är omräknade. Men
  energidelen, där vinsten finns, är i praktiken oreviderad. Det stärker J4:s slutsats att J2 V2 ger samma sak utan
  detaljdata. Gissningen innan stämde.

## Del 2: J2:s elmetod på finsk och dansk HIKP – klarade inte skärmen
Baslinje: säsong + trend på HIKP m/m (referens `seasonal_trend_5y`). Variant: samma plus J2 V2:s korrigering
[drivmedel, el som avvikelse från samma kalendermånad]. Elpriset är ett ombud: SE3 för Finland och SE4 för
Danmark, i EUR. MAE i årstakt, procentenheter.

| Variant | Period | n | MAE variant | MAE referens | Diff | DM p rå | Holm p | naive_yy |
|---|---|---|---|---|---|---|---|---|
| N1 `k6_fi_el_dev` | 2015–2026 | 142 | 0,268 | 0,279 | −0,011 | 0,29 | 0,58 | 0,311 |
| N1 | 2024–2026 | 34 | 0,235 | 0,253 | −0,018 | 0,21 | | 0,265 |
| N2 `k6_dk_el_dev` | 2015–2026 | 142 | 0,321 | 0,320 | +0,002 | 0,86 | 0,86 | 0,366 |
| N2 | 2024–2026 | 34 | 0,295 | 0,282 | +0,014 | 0,32 | | 0,350 |

Delperioder: Finland 2021–23 −0,002, Danmark 2021–23 +0,026 (p = 0,13). Danmark 2015–20 −0,017.

- Ingen variant klarade urvalsskärmen. Gissningen innan var fel: Danmark var tänkt att ge störst vinst (−0,06)
  men gav ingenting, och Finland gav −0,01 i stället för −0,03.
- **Orsaken syns i data (diagnostik efter resultat, ingen variant):** korrelationen mellan ombudsspotens
  förändring och landets el-HIKP (CP0451, m/m):

  Varje cell: 2012–2020 / 2021–2026.

  | Land (ombud) | Samma månad | En månad senare |
  |---|---|---|
  | Sverige (SE3) | 0,91 / 0,90 | −0,10 / −0,13 |
  | Finland (SE3) | −0,01 / −0,11 | 0,05 / 0,28 |
  | Danmark (SE4) | 0,02 / −0,17 | 0,31 / 0,32 |

  I Sverige slår spotpriset igenom i el-KPI samma månad, och det är därför metoden fungerar här. I Danmark och
  Finland syns spotpriset i el-HIKP först månaden efter, och svagt. Det beror troligen på hur länderna mäter elpriset
  (avtal och faktureringstidpunkt), och på att ombudet bara delvis följer ländernas egna priser. Därför blev
  elkoefficienten negativ på senare år: −1,3 för FI och −2,2 för DK, mot +2,2 och +4,6 i december 2020.
- **Robustheten:** metoden är inte en generell sanning om Nord Pool-länder. Den bygger på att svensk el-KPI följer
  spotpriset samma månad. Det är en egenskap hos SCB:s mätning som håller i svensk data (korrelation 0,9 i båda
  perioderna), men den förs inte över till grannländerna. För den svenska prognosen ändras inget.
- En variant med spotpriset för t−1 vore nästa naturliga test. Den är **inte körd**, eftersom den inte var
  förregistrerad och K6:s tak för del 2 är två varianter.

## Dataobservationer
- Finlands HIKP total är identisk i gammal och ny datamängd. **Danmarks HIKP total skiljer sig:** korrelation
  0,994 och medelskillnad 0,04 pe i m/m. Den danska totalen har alltså räknats om vid bytet till COICOP 2018. N2
  använder den nya serien; det påverkar inte slutsatsen.
- HIKP för Sverige: undergrupper på femsiffrig nivå skiljer sig mycket mellan klassificeringarna (median-korrelation
  0,81). Det spelar ingen roll för J4, som använder tvåsiffrig nivå.

## BLOCKED
- Vintages av TAB6613/COICOP 2018-grupper: finns inte, eftersom grupperna publicerades första gången 2026.
  Riksbanken, KI och ALFRED har inga KPIF-detaljserier.
- Grannländernas egna spotpriser (FI, DK1/DK2, NO): finns inte i K6:s källor. Energinet hör inte till källåset och
  elprisetjustnu.se har bara svenska områden. Svenska kopplade områden användes som ombud. Norge är inte testat.

## Vad lärde vi oss
Energigrupperna i den omräknade KPIF-detaljen är i praktiken desamma som de som publicerades i realtid, så J4 D2:s
vinst är inte en revisionseffekt. Den är samma sak som J2 V2. Elmetoden fungerar i Sverige för att svensk el-KPI
följer samma månads spotpris. I Danmark och Finland gör den inte det, och där ger metoden ingenting.
