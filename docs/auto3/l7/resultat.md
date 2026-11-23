# L7: Snabb-KPI mot utfall

## Vad som byggdes

`src/kpif_nowcast/catalog_flash.py`, registrerad i `catalog.py` direkt efter `catalog_prices`. Sju serier i området Inflation, hämtade från SCB PxWebApi v2 (CC0, ingen nyckel). Rådata cachas i `data/raw/l7/scb_<tabell>_<hämtdatum>.json` och återanvänds i 7 dagar. Offline-läget (`KPIF_OFFLINE=1`) stöds. Tester finns i `tests/test_l7_flash.py`.

- **Källa:** TAB6445, "Snabb-KPI: preliminära förändringstal för KPI, KPIF och KPIF-XE (en decimal)". Utfallet är det **först publicerade**, med en decimal: t.o.m. 2025-12 från 1987=100-tabellerna TAB5919 (KPIF) och TAB5918 (KPIF-XE), som är frysta efter 2025-12; från 2026-01 från TAB6590 (KPIF) och TAB6593 (KPIF-XE), 2020=100. Se Granskning.
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

  Fördröjningen är satt till **8 d**. Med backfill ligger snabb-KPI för målmånad t alltså aldrig i informationsmängden vid vår deadline dag 4 i t+1 (testat via `observations.upsert`/`as_of`). Undantag: en skarp hämtning samma dag som en dag-4-release, efter kl. 08.00, lagras med `known_from` = hämtdagen 00.00 och syns vid deadline. Det är projektets generella regel för hämtrader, inte specifikt för L7. Det stämmer med månadsrutinen, som körs före snabb-KPI. Även dag-4-releaserna kommer samma morgon som deadline, och de räknas inte som kända. Inga sena releaser behövdes i `publication.LATE_RELEASES`: alla observerade datum ligger inom 8 d. Kommer en framtida release dag 9 eller senare ska den läggas till där.
- **Snabb minus utfall** blir känt när det ordinarie KPI-utfallet publiceras, dag 11–20 i t+1. Januari kommer senast: 2025-02-18 och 2026-02-20. Fördröjningen är satt till **20 d**.
  - Observera: `kpif_yy`/`kpif_index` har fördröjningen 15 d, men januari publiceras dag 18–20. Det ger inget läckage vid deadline dag 4, där gränsen är ≥ 32 d. Det spelar däremot roll om någon gör utvärderingar mitt i månaden. Detta flaggas till orkestreraren och ändras inte här, eftersom det är en annan serie.
- **Revised = nej** för alla serier. Snabbestimatet revideras inte, det ersätts av utfallet, och tabellen behåller förstapubliceringen (26 av 26 värden stämmer med pressmeddelandena). Felserierna jämför mot det först publicerade utfallet, så även de är fria från revisioner. KPIF revideras inte inom en basperiod, men basbytet till 2020=100 (januari 2026) räknade om avrundade förändringstal bakåt.

## BLOCKED

Inget. SCB:s publiceringskalender som söksida (`www.scb.se/hitta-statistik/publiceringskalender/`) gav 404 för skript. Releasedatumen togs i stället från statistiknyheterna, som är tillåtna.

## Vad serierna säger om läget i Sverige

- **Oktober 2026** enligt Snabb-KPI: KPIF 1,1 % i årstakt (september 1,5 %) och 0,0 % m/m. KPIF-XE 0,1 % i årstakt. Den underliggande inflationen utan energi ligger alltså nära noll. Det stämmer med en kvarstående effekt av den sänkta matmomsen från april 2026, men det är inte verifierat i detta spår (se L1:s kalender): KPIF-XE föll från 1,1 % i mars till 0,0 % i april och har sedan legat på 0,1–0,6 %.
- **Snabbestimatet är mycket träffsäkert** (mot först publicerat utfall, 26 månader 2024-09..2026-10). Årstakten för KPIF skilde tre gånger, alla +0,1 pe (2024-11, 2025-06, 2025-08). KPIF-XE skilde två gånger (2024-12 +0,1, 2025-07 −0,1). M/m för KPIF skilde två gånger, båda −0,1 (2026-01, 2026-08). Aldrig mer än ±0,1 pe och medelfelet är i praktiken noll (KPIF årstakt +0,01 pe). Tre positiva missar av tre i KPIF årstakt är för få för att tala om bias.

## Användning i våg 2

1. **Utvärderingsreferens.** Eftersom snabb ≈ utfall är "hur nära kommer vi snabb-KPI" i praktiken samma fråga som "hur nära kommer vi utfallet". Snabb-KPI kan användas som facit 6–12 dagar tidigare, vilket ger snabbare återkoppling i månadsrutinen. Det ändrar inte poängsättningen.
2. **Som feature vid deadline dag 4 tillför serien ingen ny information.** För t−1 finns det slutliga utfallet redan, eftersom det publicerats dag 11–20 i t. Serien bär information bara för prognoser med ursprung mellan snabb-KPI och utfallet (dag 5–20). Exempel är en mellanprognos för längre horisonter efter snabb-KPI, eller en flyttad deadline. Sådana ändringar är Johannes beslut. I screeningen bör flashserierna därför inte testas som korrektion vid dag-4-deadline: med korrekt `known_from` är de redundanta mot `kpif_yy`.
3. **Felserierna** är nästan alltid 0. De är användbara som kvalitetskontroll i scorecard och dashboard, inte som prediktor.

## Granskning

En oberoende granskare lämnade fem fynd. Alla prövades mot källan (SCB:s tabeller TAB5918/TAB5919 och de cachade svaren i `data/raw/l7/`).

1. **Felserierna jämförde mot omräknat utfall (wrong) – rättat.** Stämmer. SCB har 1987=100-tabellerna TAB5919 (KPIF) och TAB5918 (KPIF-XE) kvar, frysta efter 2025-12. De ger exakt granskarens pressmeddelandevärden: KPIF årstakt 2024-11 1,8 (TAB6590 1,9), KPIF m/m 2024-12 0,3 (0,2), KPIF-XE årstakt 2024-12 2,0 (2,1), KPIF årstakt 2025-08 3,2 (3,3). Övriga 44 celler 2024-09..2025-12 är lika. `final()` tar nu utfallet från 1987=100-tabellen före 2026-01 och från 2020=100-tabellen därefter (`catalog_flash.final_from`, `REBASE`). Därmed är revised=False korrekt för felserierna. Felraderna i den lokala observationstabellen byggdes om som backfill. De fyra cellerna låses av `test_errors_use_first_published_final`. Docstring, publiceringskalendern och datakatalogens källkolumn är uppdaterade.
2. **Träffsäkerhetssiffrorna var fel (wrong) – rättat.** Följer av fynd 1. Nya antal: KPIF årstakt 3 avvikelser, KPIF-XE årstakt 2, KPIF m/m 2, se ovan. Slutsatsen (högst ±0,1 pe, ingen påvisbar bias) står kvar.
3. **Skarp hämtning på dag-4-releasedag syns vid deadline (minor) – dokumenterat, kod inte ändrad.** Stämmer: `upsert` sätter `known_from` = min(periodslut + fördröjning, hämtdag 00.00) för hämtrader, och `enforce` behåller det. Det gäller alla serier i projektet, inte bara L7. En rättning hör hemma i `observations`/`publication` (delad infrastruktur) och flaggas till orkestreraren. Det finns ingen billig lokal fix, eftersom `LATE_RELEASES` också begränsas av hämtdagen för hämtrader. Påståendet i docstring, kalender och resultat gäller nu uttryckligen backfill, med undantaget beskrivet. Det spelar bara roll om snabbserierna används som features vid dag 4, vilket avråds från ovan.
4. **kpif_yy/kpif_index bär basbytesskillnader (minor, inte L7) – flaggas, inget ändrat.** Stämmer och är större än granskaren angav: TAB5919 och TAB6590 skiljer även 2023-10 (4,2 mot 4,1) och 2024-06 (1,3 mot 1,4). Backtestens mål före 2026 är alltså den omräknade serien, inte förstapubliceringen. Valet av utvärderingsmål är Johannes beslut. TAB5919 ger ett färdigt alternativ för förstapublicerade värden före 2026-01.
5. **Dag-4-testet testade bara `LAG_FLASH > 4` (minor) – rättat.** `test_flash_never_known_at_day4_deadline` kör nu `observations.upsert`/`as_of` mot en temporär tabell: backfill syns aldrig vid deadline (00.00 dag 4) för någon av de 26 månaderna, och `publication.known_from` ligger efter deadline. Testet låser också undantaget i fynd 3 (hämtning dag 4 syns).
