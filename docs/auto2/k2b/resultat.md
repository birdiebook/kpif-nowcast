# K2b resultat: granskning av K2, K2-skuggor i driften, nätbaserad reproducerbarhet

Gren `auto2/k2b` från main @ 25a6a6e. **Inga nya modellvarianter (0 förbrukade).** Granskningskörningarna
återanvänder K2:s frysta varianter. Sabotagescenarierna är kontroller, inga kandidater.

## 1. Granskning: håller med förbehåll
Hela granskningen finns i [granskning.md](granskning.md). Kort:

| (2015-02..2026-10, n = 141) | MAE K2 | MAE rättad (flashdatum) | Holm p rättad (rå p) | Urvalsskärmen |
|---|---|---|---|---|
| `k2_avg_ridge_l` | 0,199 | **0,200** | **0,025** (0,003) | klarar |
| `k2_avg_ens_s` | 0,201 | **0,202** | **0,083** (0,012) | klarar |
| `k2_avg_ridge_s` | 0,206 | 0,207 | 0,191 (0,032) | **klarar inte längre** |
| 50/50 (referens) | 0,217 | 0,217 | | |

DM ensidigt (H1: lägre MAE än 50/50), Holm över K2:s 8 förregistrerade. 2024–26 (använd, bara rapport):
ens_s 0,220, ridge_l 0,230 mot 50/50 0,246.

Fynd:
1. **Informationsläckage (rättat):** Eurostats flash för december (alla år), mars 2018 och januari 2026 publiceras
   efter deadline. Backfillen sa periodslut + 2 dagar. `ea_news` (K2:s viktigaste feature) och fem L-features läckte
   därför i 10 månader per serie. Rättelse: `k2b_review.realistic_flash`.
2. **Frysningsfel (rättat):** L växte tyst från 43 till 72 katalogserier när K0 mergades. Nu fryst i
   `k2_ml.K2_CATALOG_KEYS`. Med den reproduceras K2:s tabell exakt.
3. Mekaniken (träningsrader, imputering, standardisering, inre CV, hyperparametrar, förregistrering) läcker inte.
   DM och Holm är rätt implementerade.
4. Små gränsfall i L: `gdp_ind_yy` har `known_from == deadline` (83 rader, `<=` tar med dem), och tidpunkterna för
   `hh_consumption_yy`/`jobads_total` är overifierade. Alla tre är reviderade eller osäkra, och L utan reviderade serier ger samma MAE.
5. Sabotage: att ge modellen nästa månads data gör den **sämre** (signalen ligger i rätt månad). Ett planterat
   perfekt läckage av utfallet ger bara −0,03 till −0,04 (hård krympning). Med en månads extra fördröjning på allt finns halva vinsten kvar.
6. Robusthet: vinsten ligger 2020–2025. 2019 och 2026 är sämre. Utan 2022–23 finns −0,008 till −0,012 kvar
   (bara ridge_l har rå p < 0,05 när modellerna tränas som vanligt).

## 2. K2-skuggor i driften
- Registrerade i `shadow.SHADOW_MODELS`: `k2_avg_ens_s` och `k2_avg_ridge_l` (`shadow._k2`). De använder K2:s frysta kod
  och flashrättelsen. Historiken är identisk med den rättade backtesten (max avvikelse 0,0 över 141 månader).
- `Inputs` har nu `obs` (observationstabellen) och `rows_from`. Den skarpa körningen räknar bara målmånaden (cirka 15 s).
  Hela historiken för champion-tabellen tar cirka 2 min.
- `pipeline monthly` hämtar nu flashen och K2:s 43 serier (`fetch_shadow_observations`). Veckojobbet hämtade
  dem redan (hela katalogen).
- Statusregel: en K2-skugga blir FINAL före dag 4 bara om flashen för målmånaden finns (`ShadowModel.ready`).
  Annars blir den PRELIMINARY och ersätts nästa dag.
- Tester: informationsmängdstestet i `tests/test_shadow.py` täcker K2 (3 månader, `rows_from`, kapad obs-tabell).
  Ett test täcker flashväntan. `tests/test_k2b_review.py` täcker frusen L, flashrättelsen och att informationsmängdstestet slår
  larm vid planterat kodläckage.

**Skuggprognoser 2026-11** (PRELIMINARY, 2026-11-23, el 22/30 dagar, drivmedel till 11-17):

| Modell | KPIF y/y |
|---|---|
| `k2_avg_ens_s` | 1,66 |
| `k2_avg_ridge_l` | 1,63 |
| `j1_comb_equal` (50/50, K1) | 1,52 |
| `j2_el_dev` (K1) | 1,86 |
| `comp_fuel_el` (skarp modell som skugga, K1) | 2,05 |

**Champion/challenger** (`forecasts/SCORECARD.md`): k2_avg_ens_s 0,202 / 0,220, k2_avg_ridge_l 0,200 / 0,230
(MAE 2015–26 urval / 2024–26 använd), live 0 månader.

## 3. Nätbaserad reproducerbarhet (ren klon, ingen data/, riktig hämtning)
- `git clone` av `auto2/k2b` till `C:\dev\kpif-auto2\k2b-clean` (bara `data/README.md` från git), egen
  PYTHONPATH (`kpif_nowcast.__file__` under klonen), samma venv.
- `python scripts/run_workflow_locally.py weekly-fetch --online` (vid 555c758): **GRÖN**, 3 023 s. Det mesta av tiden
  är Energinets historik (7 delar med cirka 5 minuters spärr emellan) och 1 848 elprisdagar × 2 zoner. Data: KPIF och
  komponenter till 2026-10, 60 Riksbanksårgångar, el till 2026-11-22, observationstabellen 96 serier / 27 819 rader
  (alla backfill), 0 misslyckade. Datatesterna 12/12 gröna. Loggar: `k2b-clean/weekly-online.log`, `monthly-online.log`.
- Klonen uppdaterad till 1673a83, sedan `run_workflow_locally.py monthly-shadow --online --as-of 2026-11-23`: **GRÖN**,
  456 s (prognosdata, K2:s 43 observationsserier, alla 5 skuggor, scorecard).
- **Jämförelse med worktreens skuggprognoser 2026-11 (alla fält utom `run`): identiska för alla fem modeller**
  (2,05 / 1,86 / 1,52 / 1,66 / 1,63). `forecasts/SCORECARD.md` är identisk byte för byte, inklusive champion/challenger-
  tabellen med K2:s historik 2015–26.
- Skillnader i data: av K2:s 43 serier skiljer sig bara `jobads_total`, i 5 värden 2026-05..2026-10 (t.ex. 2026-10:
  38 758 i går, 39 074 i dag). JobTech räknar alltså om de senaste månaderna, så serien är i praktiken reviderad trots
  `revised=False`. Det ändrar inte ridge_l:s prognos på andra decimalen. Worktreens tabell har 93 serier, klonens 96
  (tre serier som lagts till i katalogen efter worktreens hämtning, inga K2-serier).
- Begränsning: körningen visar att allt går att bygga från nätet och ger samma tal i dag. Den visar inte att
  källorna ger samma historik om ett år. Därför finns råsvaren och observationstabellens årgångar.

## BLOCKED
Inget.

## Vad lärde vi oss
- K2:s vinst är inte en kodbugg, men en del av den var ett datumfel i en datakälla. Efter rättelsen är vinsten
  ungefär −0,015 pe mot 50/50, för två av tre varianter. Den sitter i oroliga år.
- Det som kan lura oss i projektet är inte koden utan `known_from`. Informationsmängdstesten bevisar bara att koden
  följer tabellens datum, inte att datumen är rätt. Backfill med "periodslut + typisk fördröjning" måste
  kontrolleras mot verkliga releasedatum för de serier som får vikt.
- Ett läckage behöver inte ge en dramatisk MAE. Med hård krympning ger ett perfekt läckage bara −0,04, så
  "för bra för att vara sant" är ingen användbar larmklocka här.
- Backtest och skarp drift måste ha samma information. För K2 betyder det att vänta på flashen, så statusregeln har ändrats.
