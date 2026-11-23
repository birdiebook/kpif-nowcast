# L7: Snabb-KPI mot utfall

## Vad som byggdes

`src/kpif_nowcast/catalog_flash.py`, registrerad i `catalog.py` direkt efter `catalog_prices`. Sju serier i området Inflation, hämtade från SCB PxWebApi v2 (CC0, ingen nyckel). Rådata cachas i `data/raw/l7/scb_<tabell>_<hämtdatum>.json` och återanvänds i 7 dagar. Offline-läget (`KPIF_OFFLINE=1`) stöds. Tester finns i `tests/test_l7_flash.py`.

- **Källa:** TAB6445, "Snabb-KPI: preliminära förändringstal för KPI, KPIF och KPIF-XE (en decimal)". Utfallet kommer från TAB6590 (KPIF) och TAB6593 (KPIF-XE), officiell månads- och 12-månadsförändring med en decimal.
- **Historiken börjar 2024-09.** SCB publicerade första Snabb-KPI den 2024-10-08 (avser september 2024). TAB6394 (två decimaler) börjar 2024-08, alltså en månad före första realtidspubliceringen. Den månaden är bakåtberäknad och tas inte med. Vi använder entabellen med en decimal: alla 26 värden 2024-09..2026-10 är identiska med siffrorna i SCB:s pressmeddelanden "Snabb-KPI <månad> <år>" (kontrollerat mot varje sida).
- **Analysgrupper (TAB1030) och COICOP-avdelningar (TAB2652)** finns från 2026-01, bara 10 månader. Inte tillagda: för korta för våg 2.

| Nyckel | Innehåll | Fördröjning | Rev. |
|---|---|---|---|
| `kpif_flash_yy` | Snabb-KPI KPIF, årstakt (%) | 8 d | nej |
| `kpif_flash_mm` | Snabb-KPI KPIF, m/m (%) | 8 d | nej |
| `kpif_xe_flash_yy` | Snabb-KPI KPIF-XE, årstakt (%) | 8 d | nej |
| `kpif_xe_flash_mm` | Snabb-KPI KPIF-XE, m/m (%) | 8 d | nej |
| `kpif_flash_err_yy` | Snabb minus utfall, KPIF årstakt (pe) | 20 d | nej |
| `kpif_flash_err_mm` | Snabb minus utfall, KPIF m/m (pe) | 20 d | nej |
| `kpif_xe_flash_err_yy` | Snabb minus utfall, KPIF-XE årstakt (pe) | 20 d | nej |

## Publiceringsfördröjning

Hela listan finns i `catalog_flash.RELEASES`, och tester kontrollerar att varje release ligger inom fördröjningen. Belägg: SCB:s statistiknyheter för alla 26 månader.

- **Snabb-KPI** publiceras kl. 08.00 fem arbetsdagar före ordinarie KPI. Det har skett dag 4–8 i t+1:
  - dag 4: 2025-04-04, 2025-09-04, 2025-12-04 och 2026-06-04
  - dag 8: 2024-10-08, 2025-01-08, 2025-10-08, 2026-01-08 och 2026-07-08

  Fördröjningen är satt till **8 d**. Snabb-KPI för målmånad t ligger alltså aldrig i informationsmängden vid vår deadline dag 4 i t+1. Det stämmer med månadsrutinen, som körs före snabb-KPI. Även dag-4-releaserna kommer samma morgon som deadline, och de räknas inte som kända. Inga sena releaser behövdes i `publication.LATE_RELEASES`: alla observerade datum ligger inom 8 d. Kommer en framtida release dag 9 eller senare ska den läggas till där.
- **Snabb minus utfall** blir känt när det ordinarie KPI-utfallet publiceras, dag 11–20 i t+1. Januari kommer senast: 2025-02-18 och 2026-02-20. Fördröjningen är satt till **20 d**.
  - Observera: `kpif_yy`/`kpif_index` har fördröjningen 15 d, men januari publiceras dag 18–20. Det ger inget läckage vid deadline dag 4, där gränsen är ≥ 32 d. Det spelar däremot roll om någon gör utvärderingar mitt i månaden. Detta flaggas till orkestreraren och ändras inte här, eftersom det är en annan serie.
- **Revised = nej** för alla serier. Snabbestimatet revideras inte, det ersätts av utfallet, och tabellen behåller förstapubliceringen (26 av 26 värden stämmer med pressmeddelandena). KPIF revideras inte.

## BLOCKED

Inget. SCB:s publiceringskalender som söksida (`www.scb.se/hitta-statistik/publiceringskalender/`) gav 404 för skript. Releasedatumen togs i stället från statistiknyheterna, som är tillåtna.

## Vad serierna säger om läget i Sverige

- **Oktober 2026** enligt Snabb-KPI: KPIF 1,1 % i årstakt (september 1,5 %) och 0,0 % m/m. KPIF-XE 0,1 % i årstakt. Den underliggande inflationen utan energi ligger alltså nära noll. Det stämmer med en kvarstående effekt av den sänkta matmomsen från april 2026, men det är inte verifierat i detta spår (se L1:s kalender): KPIF-XE föll från 1,1 % i mars till 0,0 % i april och har sedan legat på 0,1–0,6 %.
- **Snabbestimatet är mycket träffsäkert.** På 26 månader skilde årstakten för KPIF bara en gång (2025-06, +0,1 pe), och för KPIF-XE en gång (2025-07, −0,1 pe). M/m för KPIF skilde ±0,1 pe tre gånger. Medelfelet är i praktiken noll.

## Användning i våg 2

1. **Utvärderingsreferens.** Eftersom snabb ≈ utfall är "hur nära kommer vi snabb-KPI" i praktiken samma fråga som "hur nära kommer vi utfallet". Snabb-KPI kan användas som facit 6–12 dagar tidigare, vilket ger snabbare återkoppling i månadsrutinen. Det ändrar inte poängsättningen.
2. **Som feature vid deadline dag 4 tillför serien ingen ny information.** För t−1 finns det slutliga utfallet redan, eftersom det publicerats dag 11–20 i t. Serien bär information bara för prognoser med ursprung mellan snabb-KPI och utfallet (dag 5–20). Exempel är en mellanprognos för längre horisonter efter snabb-KPI, eller en flyttad deadline. Sådana ändringar är Johannes beslut. I screeningen bör flashserierna därför inte testas som korrektion vid dag-4-deadline: med korrekt `known_from` är de redundanta mot `kpif_yy`.
3. **Felserierna** är nästan alltid 0. De är användbara som kvalitetskontroll i scorecard och dashboard, inte som prediktor.
