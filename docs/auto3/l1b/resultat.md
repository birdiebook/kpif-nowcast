# L1b Källkontroll av kalendern: resultat

Körning 3, våg 1b, 2026-11-23. Gren `auto3/l1b`. Kod: `src/kpif_nowcast/admin_calendar.py`, dokumentation:
[administrerade-priser.md](../../administrerade-priser.md) (avsnittet Primärkällkontroll),
not i [skattekalender.md](../../skattekalender.md). Inga modellvarianter och inga p-värden.

## Vad som gjordes
- Alla 35 händelser (L1:s 26, en ny och K13:s åtta) är kontrollerade mot primärkälla: riksdagens
  `dokumentstatus` (riksdagens beslutsdatum), propositionstexter, SFS i riksdagens databas, Skatteverkets
  skattesatser för bränsle och el och regeringens pressmeddelanden. Varje händelse har nu fältet `verified` och
  kolumnen Verifierad: 25 verifierade, 4 delvis, 6 ej verifierade (med orsak).
- Alla länkar är provade. Länkar till regeringen.se utan www fungerade inte i miljön och har bytts till www.
  Sekundärkällor är ersatta där en primärkälla fanns (hurbra.se → Skatteverket, Företagarna → prop. 2021/22:221).
- `k13_tax.EVENTS` är oförändrad. Rättelser av K13:s datum ligger i `admin_calendar.K13_DECIDED_FIX`, och ett
  test kräver att en rättelse bara får flytta ett beslut senare.

## Före/efter
| Månad | Före | Efter | Kommentar |
|---|---|---|---|
| 2026-12 | `--adjust 0.52` (+0,398 CO2, +0,115 månadskort) | `--adjust 0.52` | CO2-slutet bekräftat av Skatteverket (bensin 2,39 → 4,79 kr/l skatt 1 dec), ingen förlängning i prop. 2026/27:1 eller 2026/27:2 och inget förslag i riksdagens dokumentlista |
| 2027-01 | `--adjust -0.03` | `--adjust -0.03` | tobak: "ej beslutad" → genomförs inte (prop. 2026/27:1 tabell 1.5); prisbasbeloppet bekräftat (SFS 2026:1779); drivmedelsindexeringen bekräftad (+10/+8,5 öre/l) |

Ekot (information) är oförändrat: −0,131 (2026-12) och −0,196 (2027-01).

## Fel som hittades
1. **2016-01 drivmedel:** källan bet. 2015/16:SkU18 var ett motionsbetänkande med beslut 9 mars 2016, alltså efter
   händelsen. Rätt källa är prop. 2015/16:1, med beslut i bet. FiU1 25 nov 2015. Samma länk togs bort från
   trängselskatten 2016.
2. **2025-05 ROT och ROT-slutet:** beslutet var 7 maj 2025 (FiU32). Kalendern angav "senast 30 april", före det
   verkliga beslutet. Före deadline, så ingen effekt.
3. **K13 2026-04 matmomsen och L1 2028-01:** beslutet var 25 feb 2026 (prop. 2025/26:55, SkU9), inte "senast 30 nov
   2025". Före deadline för 2026-04, så K13:s varianter påverkas inte. Noterat i skattekalender.md.
4. **K13 2026-01:** källan om att låsa elskatten 2027 gäller en remiss som inte kom med i budgeten.
5. **Saknad händelse:** 1 jul 2025 sänktes energiskatten på drivmedel med 32 öre/l, och reduktionsplikten höjdes så
   att pumppriset blev oförändrat (prop. 2024/25:131). SCB:s KS-mått visar −0,05 (energi), men nettoeffekten är
   0. Den är tillagd med effekt 0.
6. Tobaksraden ändrades från "ej beslutad" till beslutad med effekt 0.

## BLOCKED / ej verifierat
- Regionala månadskort (Skånetrafiken, SL, Västtrafik, Hallandstrafiken, TV4/TT, via.tt.se): värdarna är inte
  nåbara från miljön. Sista halvprisdag 2 dec stämmer med SFS 2026:1391 4 §. Västtrafiks förlängning är okänd.
- Elskattens nivå 2027 (~36,2 öre/kWh, SFS 2026:1859): toreenergi.se går inte att nå, Skatteverket visar bara
  2026, och riksdagens SFS-databas har inte förordningen. Raden räknas som normal indexering och påverkar inte
  förslaget.
- Trängselskatten 2016 (Transportstyrelsen går inte att nå, riksdagsbeslutet hittades inte) och förordningen om
  fribeloppet i maxtaxan (anslaget är beslutat 16 dec 2025).
- Elnät och VA/avfall 2027: ingen samlad primärkälla.

## Osäkerhet
Det som är verifierat är beslutsdatum, ikraftträdande och skattesatser. Storleken i pe (vikt × ändring, fullt
genomslag) är oförändrad och fortfarande ett antagande. K13 visade att drivmedelsskatter inte slår igenom fullt
samma månad.
