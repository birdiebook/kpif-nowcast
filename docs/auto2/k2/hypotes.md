# K2 ML-spåret: förregistrering

Skriven 2026-11-23 innan något fel för 2015–2026 har beräknats för varianterna nedan.
Bas: main @ 42b717b (J1–J7 mergade). Globalt varianttotal före K2: 23. K2:s tak: 10 av körning 2:s 30.

## Fråga och hypotes
Syfte (ändrat av Johannes 2026-11-23, före förregistreringen): bästa möjliga KPIF-prognos. Frågan är bara
"ger ML en bättre prognos än 50/50-snittet av `rb_updated` och J2:s V2 (`j2_el_dev`, här "j2")?".
Varianterna är därför valda för att maximera chansen till en verklig förbättring, och listan hålls kort (8)
för att Holm-familjen inte ska äta upp styrkan.

**Hypotes:** den enda starka signalen är skillnaden mellan prognoserna (`gap = j2 − rb_updated`) och hur
mycket den ska vägas beroende på prognosomgångens ålder (J1: j2 bättre vid 3+ mån, rb_updated vid 1 mån)
och energinyheten. En regulariserad modell med residualen mot 50/50 som mål krymper mot 50/50 när signalen
är svag och kan bara vinna om interaktionerna (gap × ålder) eller energinyheten bär något. Med 36–140
träningsobservationer dominerar varians, så vinsten blir liten om den finns. Boosting och den breda
feature-mängden med katalogserierna bör vara sämre (J3: ingen katalogserie tillförde något).

**Min gissning innan (MAE 2015-02..2026-10; 50/50 ≈ 0,217, rb_updated 0,256, j2 0,243):**
- Ingen variant klarar urvalsskärmen mot 50/50.
- Ridge/lasso på S med bas 50/50: 0,210–0,222 (diff mot 50/50 −0,007 till +0,005), rå ensidig p 0,2–0,6.
- Ridge på S med bas rb_updated eller j2: 0,213–0,228.
- Boosting: +0,005 till +0,025 mot 50/50. Ensemblen ridge+boosting mellan dem, nära ridge.
- Ridge på L: +0,0 till +0,012 mot 50/50.
- Mot rb_updated har alla varianter lägre MAE, rå ensidig p 0,005–0,06 (mest 50/50:s förtjänst).

## Uppställning
- **Panel:** en rad per målmånad t, 2015-02..2026-10 (Riksbankens prognosarkiv börjar 2015-02, så
  rb_updated finns inte tidigare; n = 141). Samma panel som J1 (`j1_hybrid.build_panel`).
- **Mål:** residualen `actual_t − bas_t` (KPIF årstakt, pe), där bas = `rb_updated`, `j2` eller
  `avg` = 0,5·rb_updated + 0,5·j2. Prognos = bas + predikterad residual. Inte KPIF direkt. Bas `avg` gör att
  regulariseringen krymper mot den bästa kända prognosen i stället för mot en sämre.
- **Träningsrader för t:** rader s < t med publicerat utfall (KPIF för t−1 publiceras mitten av t, före
  deadline = dag 4 i t+1). Varje rads features är beräknade med det som var känt vid radens egen deadline.
- **Start:** färre än 36 träningsrader (målmånader före 2018-02) → förregistrerat startvärde: prognosen =
  50/50-snittet (bas rb_updated: residual = 0,5·gap; bas j2: residual = −0,5·gap; bas avg: 0). Alla varianter är
  alltså identiska med 50/50 2015-02..2018-01, och jämförelsen mot 50/50 handlar bara om vad ML tillför när den
  är aktiv. Delurvalet 2018-02..2026-10 (n ≈ 105) rapporteras också.
- **Nästlad validering:** inom varje expanderande fönster väljs hyperparametrar med inre tidsserie-CV
  (`TimeSeriesSplit(n_splits=4)` på fönstrets träningsrader, i tidsordning), kriterium = lägst MAE över
  valideringsdelarna. Modellen tränas sedan om på hela fönstret med valda parametrar och predikterar t.
  2015–2026 används bara som yttre utvärdering, en gång.
- **Förbehandling inom fönstret:** saknade värden ersätts med fönstrets median (`SimpleImputer`), sedan
  standardisering (`StandardScaler`) för ridge/lasso, i en `Pipeline` som anpassas bara på träningsraderna
  (också i inre CV). Boosting får NaN direkt (hanteras inbyggt), ingen standardisering.
- **Hyperparametergrid (fast):**
  - Ridge: alpha ∈ {0,1, 0,3, 1, 3, 10, 30, 100, 300, 1000, 3000}.
  - Lasso: alpha ∈ {0,001, 0,002, 0,005, 0,01, 0,02, 0,05, 0,1, 0,2}, max_iter 20 000.
  - Boosting (`HistGradientBoostingRegressor`, loss squared_error, min_samples_leaf 8, early_stopping av,
    random_state 0): learning_rate ∈ {0,03, 0,1} × max_depth ∈ {2, 3} × max_iter ∈ {50, 150}.

## Feature-mängder (förregistrerade)
**S (liten, 14 features, inga reviderade serier), allt känt vid deadline(t):**
1. `gap` = j2_t − rb_updated_t
2. `energy_news` = j2:s energiprognos minus säsongsbaslinjen (pe av m/m), som i J1
3. `fuel_chg` (Brent i SEK, dag 1–25 i t, logförändring)
4. `el_dev` (elprisförändring i t minus samma kalendermånad senaste ≤5 år, J2)
5. `core_dev` (icke-energikomponenternas avvikelse från baslinjen i t−1, J1)
6. `last_resid_rb` = actual_{t−1} − rb_updated_{t−1}
7. `last_resid_j2` = actual_{t−1} − j2_{t−1}
8. `ki_services_dev`, 9. `ki_grocery_dev`, 10. `ki_durables_dev` (KI-prisplaner, enkät t−1, avvikelse från 12-mån snitt)
11. `ea_news` (euroområdets snabbestimat t minus t−1, första publicering, 0 före 2017-08)
12. `rb_months_ahead` (prognosomgångens ålder)
13. `gap_x_age` = gap · min(rb_months_ahead, 3)
14. `energy_x_age` = energy_news · min(rb_months_ahead, 3)

**L (stor, 14 + 43 = 57 features):** S plus alla katalogens månadsserier (`catalog.CATALOG`, freq "M")
utom `kpif_index`, `kpif_yy`, `jobads_ai`, `jobads_ml` (AI-termer med känt mätbrott, ingen prisanknytning)
och `af_*` (finns inte i observationstabellen i denna worktree). Transform exakt som J3 (`j3_screen.transform`):
värde känt vid deadline(t) via `observations.as_of`, senaste period ≤ t, säsongsdifferentierad månadsnyhet
(eller förändring för årstakter). Serier före sin första publicering: saknas → median i fönstret.
**Reviderade serier:** av de 43 har ca 25 `revised=True` (backfill med dagens årgång). Se nedan.

Antalet features (57) är stort mot 36–140 observationer; det är avsiktligt testet "hjälper bredd när
regulariseringen väljs ärligt?". Ingen feature väljs efter att ha sett 2015–26-resultat.

## Varianter (exakt lista, 8 st)
| # | Namn | Bas (mål = residual mot) | Modell | Features |
|---|---|---|---|---|
| 1 | `k2_avg_ridge_s` | avg (50/50) | ridge | S |
| 2 | `k2_avg_lasso_s` | avg | lasso | S |
| 3 | `k2_avg_hgb_s` | avg | boosting | S |
| 4 | `k2_avg_ens_s` | avg | medel av ridge- och boostingresidualen (1 och 3) | S |
| 5 | `k2_avg_ridge_l` | avg | ridge | L |
| 6 | `k2_rb_ridge_s` | rb_updated | ridge | S |
| 7 | `k2_j2_ridge_s` | j2 | ridge | S |
| 8 | `k2_rb_hgb_s` | rb_updated | boosting | S |

8 av K2:s 10 används; 2 sparas oanvända. Inga fler varianter läggs till; eventuella tillägg efter resultat
märks som sådana och räknas mot taket.

## Jämförelser och Holm-familjer
- Period: 2015-02..2026-10 (n = 141), alla månader där rb_updated, j2 och utfall finns. Modellval sker bara här.
  Rapporteras också: 2018-02..2026-10 (ML aktiv) och 2024-01..2026-10 (använd, bara rapport).
- Tre jämförelser per variant: mot **50/50** (huvudfrågan), mot **rb_updated** och mot **j2**. Alla är nästlade
  (referensen är ett specialfall av bas + f(features), eftersom `gap` ingår), så DM-testet (absolutfel,
  `evaluation.dm_test`) är **ensidigt** med H1: varianten har lägre MAE än referensen.
- Holm-justering över de 8 varianterna, separat per referens (tre familjer). Råa p bredvid.
- **Urvalsskärmen:** Holm-p < 0,10 mot 50/50 på 2015-02..2026-10, och inte högre MAE än 50/50 på 2024–2026
  (bara rapport). Skrivs aldrig "slår", bara "klarade urvalsskärmen".
- **Revisionsläckage:** en L-variant som klarar skärmen märks "obekräftad (revisionsläckage möjligt)" om inte
  samma bas och modell på S också klarar den (`k2_avg_ridge_l` mot `k2_avg_ridge_s`).

## Förklaring (inga extra varianter)
- Ridge: standardiserade koefficienter och vald alpha i sista fönstret varje år. Lasso: andel fönster
  där varje feature har vikt ≠ 0.
- Boosting: permutationsvikt utanför urvalet: för varje feature permuteras dess värden över de aktiva
  prognosmånaderna och prognoserna görs om med varje månads egen modell; ökning i MAE, 20 upprepningar.

## Test
`tests/test_k2_ml.py`: prognosen för t är identisk med och utan data efter t:s deadline (KPIF/komponenter
till t−1, energifeatures till t, Riksbanksårgångar publicerade före deadline, observationer med
known_from ≤ deadline) för `k2_avg_ridge_l` (ridge + katalog), `k2_rb_hgb_s` (boosting) och `k2_avg_ens_s`.
