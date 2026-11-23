# K1 Drift: skuggprognoserna går själva (fas 6, del 1) – resultat

Gren `auto2/k1`, bas main@42b717b. Inga nya modellvarianter (0 förbrukade). Skuggmodellerna är
befintliga serier: den skarpa modellen, J2 V2 och J1 C1 (50/50).

## Vad som byggdes

| Del | Fil | Kommentar |
|---|---|---|
| Pipeline | `src/kpif_nowcast/pipeline.py` | `weekly`, `monthly`, `fetch`, `shadow`, `check`, `scorecard`, `prune`. Ett kommando per workflow-jobb, så att samma steg körs lokalt och i Actions. |
| Offlineläge | `src/kpif_nowcast/sources/rawcache.py` + små ändringar i `scb`, `fred`, `riksbank`, `konj`, `eurostat`, `elpris` | `KPIF_OFFLINE=1` / `--offline`: källorna läser senaste sparade råsvar i `data/raw/` och alla andra nätanrop stoppas med fel. Det gör att hela kedjan kan byggas om från en råcache, utan att röra API:erna. |
| Skuggprognoser | `src/kpif_nowcast/shadow.py` | Register `SHADOW_MODELS` (en rad per modell). Skriver `forecasts/shadow/<modell>/<månad>.json`. Samma statusregel som `forecast.py` (FINAL/PRELIMINARY/LATE). En FINAL-fil skrivs aldrig över. `forecast.py` och `forecasts/<månad>.json` är orörda. |
| Datatester | `src/kpif_nowcast/warehouse.py`, `tests/test_data_quality.py` | DuckDB-vyer `observations`, `obs_latest`, `catalog`. Kontroller: unik nyckel (series, period, known_from), inga null, periodformat, known_from ≥ periodens slut (utom serier med negativ fördröjning i katalogen, dvs. hyror), hämtade rader inte daterade efter hämtningen, inga hål i frekvensen, rätt kvartals-/årsrutnät, alla serier i katalogen. Dessutom kontroller av KPIF, komponenter (5 per månad, summerar till KPIF m/m) och features (el från 2012). Ett syntetiskt test visar att kontrollerna fångar fel. dbt behövdes inte. |
| Champion/challenger | `src/kpif_nowcast/champion.py`, anrop i `scorecard.py` | Nytt avsnitt sist i `forecasts/SCORECARD.md`. Den skarpa tabellen är oförändrad. Om avsnittet fallerar skrivs den skarpa delen ändå, med en varning. |
| Workflows | `.github/workflows/weekly-fetch.yml`, `monthly-shadow.yml` | Bara `schedule` + `workflow_dispatch`. Pushen gick igenom (token hade workflow-scope), så inget behövde läggas i `ci/workflows/`. |
| Låsta versioner | `ci/requirements.txt` | Samma versioner som lokala venv, så att CI ger samma siffror. |
| Lokal körning | `scripts/run_workflow_locally.py` | Läser workflow-filerna och kör deras `python -m kpif_nowcast...`-steg i ordning. Hoppar över `uses:`, pip och "(CI only)". Offline som standard, `--online` för riktig hämtning. |
| Tester | `tests/test_shadow.py` | Informationsmängdstest för varje registrerad modell (prognosen för t är identisk med data kapad vid t:s deadline; plockar automatiskt upp K2:s kandidat). Skuggan för J2 V2 är identisk med J2:s egen körning, 50/50 identisk med J1:s `j1_comb_equal`. Status- och skrivregler, råcache och nätspärr, samt att workflows bara har tillåtna triggers och inga hemligheter. |

`duckdb` 2.0.1 installerat i venv och lagt i `pyproject.toml`.

## Workflows

- **Veckohämtning** (söndag 04:17 UTC): återställer `data/` från Actions-cachen, kör
  `pipeline weekly` (all data inkl. observationstabellen, sedan datatesterna), rensar råsvar till de
  4 senaste per anrop, sparar cachen och laddar upp `data/` som artifact (14 dagar). Behörighet:
  `contents: read`. Inget committas.
- **Skuggprognoser** (05:23 UTC dag 1–4): `pipeline monthly` (prognosdata, skuggor, scorecard),
  sparar cachen, committar `forecasts/shadow/` och `forecasts/SCORECARD.md`. Behörighet:
  `contents: write`, som bara låter jobbets egen `GITHUB_TOKEN` pusha till det här repot. Den
  första körningen med fullständig data före deadline blir FINAL. Senare dagar ändrar inte filen.
- `TZ: Europe/Stockholm`, så att statusregeln använder svenskt datum. `concurrency: kpif-data`, så att
  två jobb aldrig skriver cachen samtidigt.
- **Aktivering:** schemalagda workflows körs bara på standardgrenen, så inget körs förrän Johannes
  mergar. Efter merge kan man köra "Run workflow" (workflow_dispatch) en gång för att värma cachen.
- **Cache:** GitHub raderar en cache som inte använts på 7 dagar. Söndagsjobbet använder den varje
  vecka, men om den ändå försvinner hämtas allt från noll. Det tar längre tid men fungerar: Energinet
  (begränsad takt) och alla elpris-dagar sedan 2021-11, därför `timeout-minutes: 90`.

## Resultat

**Skuggprognoser 2026-11** (PRELIMINARY, gjorda 2026-11-23, el 22/30 dagar, drivmedel till 11-17):

| Modell | Prognos KPIF y/y |
|---|---|
| `comp_fuel_el` (skarpa modellen som skugga) | 2,05 |
| `j2_el_dev` (J2 V2) | 1,86 |
| `j1_comb_equal` (50/50 rb_updated + J2 V2) | 1,52 |

Den skarpa filen `forecasts/2026-11.json` säger 2,09, gjord 11-22 med 21 eldagar. Skillnaden mot
skuggans 2,05 kommer bara av en eldag till (el_chg 0,99 mot 0,96). Båda är PRELIMINARY och ersätts
av FINAL dag 1–4 i december.

**Champion/challenger** (genererad i `forecasts/SCORECARD.md`, MAE i procentenheter):

| Modell | Roll | 2015–26 (urval, n=141) | 2024–26 (använd, n=34) | Live |
|---|---|---|---|---|
| comp_fuel_el | champion | – (finns från 2023-12) | 0,375 | 0 mån |
| j2_el_dev | challenger | 0,243 | 0,252 | 0 mån |
| j1_comb_equal | challenger | 0,217 | 0,246 | 0 mån |
| rb_updated | benchmark | 0,256 | 0,267 | – |
| riksbank | benchmark | 0,320 | 0,326 | – |

MAE 2015–26 är **urvalsevidens**: modellerna valdes på den perioden. Siffrorna stämmer exakt med
J1:s och J2:s körningar (0,217 / 0,243 / 0,256), vilket bekräftar att skuggorna är samma modeller.
Inga DM-test görs här: det finns inga nya varianter och inga live-månader. Live-evidens finns ännu inte (0 månader).

**Datatester:** 12/12 gröna på worktreens `observations.parquet` (15 604 rader, 64 serier). Tre kända
hål är undantagna med orsak: hyror 1981 saknas hos SCB (kontrollerat i råsvaret), och AI-andelen hos
Eurostat saknar 2022. Hela pytest: 68 passerade, 4 överhoppade.

**Lokal workflow-körning:** `python scripts/run_workflow_locally.py` (offline) blev GRÖN för
både `weekly-fetch` och `monthly-shadow`.

**Reproducerbarhet:** jag klonade grenen till `C:\dev\kpif-auto2\k1-clean` (git clone, egen
PYTHONPATH, `kpif_nowcast.__file__` under klonen) och kopierade bara `data/raw/` dit. Därifrån
körde jag `pipeline fetch --offline` (processed, features och observationstabellen byggda från
råcachen) och sedan `pipeline shadow --offline --as-of 2026-11-23`:
- alla tre skuggprognoserna för 2026-11 är **identiska** med worktreens (alla fält utom `run`, som
  har tidsstämpel och commit),
- `kpif.csv`, `components.csv`, `tax_effects.csv`, `riksbank_kpif_forecasts.csv` och `features.csv`
  är **byte-identiska** med de online-hämtade filerna från 2026-11-22,
- datatesterna och skuggtesterna är gröna i klonen.
Klonen ligger kvar.

**Inte testat: en helt nätbaserad hämtning från noll** (tom `data/`, alla källor online, som
Actions första körning). SCB, KI, FRED och Riksbanken var låsta av K0, så den ska köras efter K0:
`python scripts/run_workflow_locally.py --online` i en ren klon utan `data/`, eller "Run workflow"
efter merge. Observationstabellen blir då ren backfill, och fyra källor (FAO, GSCPI, JobTech,
Arbetsförmedlingen) har inget offlineläge. Deras 10 av 67 serier gick inte att bygga om offline, men
de påverkar inte skuggprognoserna.

## BLOCKED

Inget. Pushen av workflow-filerna godtogs.

## Öppna frågor till Johannes

1. **Namn:** briefen säger `comp_fuel` om den skarpa modellen. I `backtest.py` betyder `comp_fuel`
   modellen med bara drivmedel, medan den skarpa (`component_fuel_el_v1`) heter `comp_fuel_el`.
   Skuggan heter därför `comp_fuel_el` och kör exakt den skarpa koden.
2. **Konflikt i SCORECARD.md:** både CI och den manuella månadsrutinen (steg 4) skriver filen. Om
   båda ändrar den samma dag kan CI:s `git pull --rebase` krocka. Då misslyckas jobbet synligt och
   ingenting går förlorat.
3. Rensning av råsvar (`prune --keep 4`) görs bara i CI. Den lokala regeln "spara rådata med
   hämtdatum" gäller fortfarande lokalt.
4. Sverigeläget-dashboarden laddas inte upp från Actions, eftersom Claude Data saknar API-nyckel i CI.
   Veckohämtningen håller bara datan färsk.

## Slutsatser

- Den enda ändringen som behövdes för att göra kedjan reproducerbar var offlineläget. Råcachen räcker
  för att bygga om allt som skuggprognoserna använder, byte för byte. Den gamla namngivningen av
  SCB:s råfiler, utan urvalstagg, var den enda fallgropen, och den löses med en reservregel som
  verifierats mot online-filerna.
- 2024–26 är den enda perioden där alla tre modellerna går att jämföra, och den är redan använd. Den
  skarpa modellens energikorrektion tränas från 2021-12 och har därför ingen 2015–26-historik. Riktig
  evidens för champion/challenger kommer först med live-månaderna, med start december 2026.
