# L4 Prospera: resultat (körning 3, våg 1)

## Vad som byggdes

`src/kpif_nowcast/catalog_prospera.py` läser **penningmarknadens 5-åriga inflationsförväntningar** från
Riksbankens enkät (Kantar Sifo Prospera t.o.m. 2024, Origo Group från januari 2025). Datat kommer från
**Riksbankens sifferunderlag (xlsx) till de penningpolitiska rapporterna** på www.riksbank.se, diagrammet
"Spridning i 5-åriga inflationsförväntningar, penningmarknadens aktörer" (källa Origo Group och Riksbanken,
månadsdata från 2019-01).

Läsaren är byggd för att tåla att filen ändras:
listningssidan med penningpolitiska beslut → beslutssidorna, nyast först → deras sifferunderlag-xlsx →
det blad vars rubrik nämner inflationsförväntningar, 5 år och penningmarknaden, med källa Origo/Prospera
och kolumner för P25, P75 och medel ("Genomsnitt" eller "Medelvärde"). Den nyaste träffen vinner.
Diagramnumret flyttar mellan rapporter (29 i juni, 36 i september 2026) och sökvägen har ett stavfel
(`siffferunderlag`), så URL:en gissas inte. Rådata cachas i `data/raw/l4/` med hämtdatum. En rapportfil
återanvänds oavsett ålder, och vilken fil som har diagrammet upptäcks på nytt efter 7 dagar. Offline-läget
(`KPIF_OFFLINE=1`) fungerar. Läsaren använder `xlsx_lite`, så den kräver inget nytt beroende.

| Nyckel | Serie | Fördröjning | Rev. | Period |
|---|---|---|---|---|
| `prospera_mm_5y_mean` | 5 år, medel | 3 d | ja | 2019-01–2026-09 |
| `prospera_mm_5y_p25` | 5 år, 25:e percentil | 3 d | ja | 2019-01–2026-09 |
| `prospera_mm_5y_p75` | 5 år, 75:e percentil | 3 d | ja | 2019-01–2026-09 |

**Fördröjning.** Origo publicerar mätmånad m mitt i m. Åtta releaser är belagda: dec 2025 → 12-17,
mar 2026 → 03-19, apr → 04-15, maj → 05-18, jul → 07-10, aug → 08-17, okt → 10-15 och nov → 11-16
(dag 10–19 i mätmånaden). Fördröjningen är satt till 3 d efter periodens slut, samma konvention som för
KI-enkäterna, och ligger inom deadline dag 4 i t+1.

**Revised = ja.** Medelvärdet skiljer sig upp till 0,005 mellan juni- och septemberfilen 2026.

**Läckagerisk (flaggas).** Värdena är Riksbankens egen aggregering av svaren för månad m. Informationen
fanns offentligt i m, i Origos release. De exakta talen trycks däremot först i nästa rapport som har
diagrammet. Riksbankens medel avviker i snitt 0,04 (max 0,27) från den "Prospera 5 år"-serie som
Riksbanken visade 2024. Det är en nära proxy, inte samma tal. Serien kan alltså ses vid deadline i en
backtest, men i drift uppdateras den bara när en rapport har diagrammet. Så var det i juni och september
2026, men inte i någon rapport 2025. Mellan sådana rapporter blir serien inaktuell i flera månader.

**KI duplicerades inte.** Hushållens (`hh_infl_exp_median`, `hh_price_exp_net`) och företagens
(`nier_firm_infl_exp_*`) förväntningar finns redan från KI och rördes inte.

## BLOCKED

- **Origo Groups egna releaser (1, 2 och 5 år, KPI och KPIF, alla grupper: penningmarknaden,
  arbetsmarknadens parter, inköpschefer).** Värden `www.origogroup.com` finns inte i miljöns lista
  (proxyn ger 403). Dessutom publiceras resultaten bara som en PDF per månad
  (`/wp-content/uploads/<år>/<mån>/Inflation-Expectations-<Månad>-<år>.pdf`), utan Excel eller
  tidsseriefil. Historiken skulle kräva PDF-tolkning i stor skala. Om Johannes lägger till värden går det
  att läsa den senaste månadens tabell ur PDF:en framåt. Det skulle göra serien aktuell varje månad.
- **1- och 2-årsförväntningar från Riksbankens filer.** De finns bara i sifferunderlaget från
  februari–maj 2024 ("Prospera, 1/2/5 år") och slutar 2024-04. Serien är död och har en annan definition
  än medlet ovan, så den lades inte in.
- **Marknadsbaserade förväntningar (break-even, realobligationer).** De finns inte i Riksbankens
  SWEA-API (117 serier är kontrollerade) och inte i API:et för prognoser och utfall.

## Läget i Sverige enligt serien

De långsiktiga förväntningarna sitter **fast vid 2 %**. I september 2026 var medlet 2,08 med P25–P75 på
2,0–2,15. Under 2026 har medlet legat på 2,02–2,16, och P25 har legat på exakt 2,0 sedan 2025. Spridningen
är den minsta i serien: interkvartilavståndet var 0,11 i snitt 2026, mot 0,36–0,48 2019–2022. Toppen kom
2022-07 med medel 2,40 och P75 2,45. Under inflationschocken låg 5-årsförväntningarna alltså bara
0,2–0,4 enheter över målet och föll tillbaka till 2,0–2,1 från 2024. Penningmarknaden ser ingen risk för att inflationen ska bita sig fast på lång sikt. Serien slutar
2026-09, alltså före Riksbankens höjning av styrräntan till 2 % den 4 november 2026. Hur förväntningarna
har rört sig efter höjningen syns inte här (Origos release för november är BLOCKED).

## Användning i våg 2

- För KPIF m/m på 1 månads sikt väntas litet prognosvärde, eftersom 5-årsförväntningar nästan inte
  varierar alls. Serien passar som **nivå- och ankarvariabel på 6–12 månaders horisont**: medlet minus
  2 %, och IQR som osäkerhetsmått. Den kan också användas som regimindikator, där en hög IQR betyder
  sämre förankring.
- I screeningen bör bara **en** av de tre nycklarna tas med, helst `prospera_mm_5y_mean` eller
  IQR = p75 − p25, eftersom de är nästan kollinjära. Det sparar statistisk budget.
- Varning för drift: serien kan vara flera månader gammal vid prognostillfället. Använd `as_of()` och
  senast kända värde, och fyll inte i värden.
