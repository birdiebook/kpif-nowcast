# K11 Oberoende granskning av publiceringsfördröjningar och datakvalitet

**Dom: fel som påverkar.** <!--DOM-->

Granskat 2026-11-23 av en agent som inte skrev katalogen. 0 modellvarianter (omkörningen av K2 är en rättning).
Låsning: [docs/publiceringskalender.md](../../publiceringskalender.md) + `tests/test_publication_calendar.py`.

## Metod

Deadline för målmånad t är dag 4 i t+1 (`riksbank_benchmark.deadline`). `known_from = periodens slut + lag_days`
och `as_of` tar med värden med `known_from <= deadline`. Därför spelar en fördröjning bara roll vid vissa gränser:

| lag_days | Period modellen ser vid deadline | Läckage om verklig publicering sker senare än |
|---|---|---|
| ≤ 4 | t | dag 4 i t+1 |
| 5–32 | t−1 | dag 4 i t+1 (32–35 d efter t−1, beror på månadens längd) |
| 35 | t−1 i månader med 31 dagar, annars t−2 | dag 4 i t+1 (35 d) |
| 36–63 | t−2 | dag 4 i t+1 (≥ 63 d) |

För varje serie jämfördes antagen fördröjning med belagd fördröjning från officiella källor: SCB PxWeb v2
`updated`/`lastPeriod` (senaste publiceringen, en per tabell), SCB:s statistiknyheter (historiska datum),
KI:s publikationslista (34 barometrar 2024–2026), Eurostats euro-indikatorer (releasekoden `2-DDMMYYYY-ap`
innehåller datumet; alla flashmånader 2017-08..2026-10 provades för dag 4–7), FAO:s releasekalender 2026, BLS
historiska releasedatum för PPI, FRED-sidor och Riksbankens beslutsdatum. Inga stora hämtningar (råfiler i
`data/raw/k11/`, inte i git).

## Fel som påverkar (läckage)

<!--FEL-->

## Fel som inte påverkar

<!--OFARLIGA-->

## revised-flaggor

<!--REV-->

## Omkörning av K2:s frysta varianter

<!--K2-->

## Rättningar i grenen

<!--RATT-->

## BLOCKED / inte belagt

<!--BLOCKED-->

## Vad lärde vi oss

<!--LARDOM-->
