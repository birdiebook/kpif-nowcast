# K2 resultat (urvalsevidens)

Förregistrering: [hypotes.md](hypotes.md). Kod: `src/kpif_nowcast/k2_ml.py`. Körning:
`experiments/runs/20261123T083753Z_k2_ml.csv` vid 415ba6f ("+dirty" gäller bara radslut i `data/README.md`,
inget innehåll). Hela tabeller, ridge-vikter, lasso-urval och permutationsvikter: [results_raw.md](results_raw.md).

**Varianter:** 8 förregistrerade + 1 tillagd efter resultat (diagnostik) = **9 av K2:s 10**.
Globalt projekttotal efter K2: 23 + 9 = 32 (körning 2:s andel från K2: 9 av 30).
Alla p-värden är urvalsevidens. DM-test på absolutfel, ensidigt (H1: varianten har lägre MAE än referensen,
alla jämförelser är nästlade), Holm över de 8 förregistrerade per referens.

## Vad som byggdes
Mål = residualen mot en bas (50/50-snittet "avg", `rb_updated` eller J2 V2 "j2"); prognos = bas + predikterad
residual. Ridge, lasso och `HistGradientBoostingRegressor` (scikit-learn 1.9.1, fanns redan i venv).
Nästlad validering: inom varje expanderande fönster väljs hyperparametrar med `TimeSeriesSplit(4)` på MAE,
sedan refit på hela fönstret. Imputering och standardisering anpassas bara på fönstrets träningsrader. Före 36
träningsrader (mål före 2018-02) är prognosen = 50/50. Features: S = 14 (gap, energinyhet, el, drivmedel,
senaste missar, KI-prisplaner, euroområdets snabbestimat, prognosomgångens ålder och två interaktioner med
åldern), L = S + 43 katalogserier as-of deadline (24 av dem `revised=True`).

## Resultat 2015-02..2026-10, n = 141 (förregistrerat kriterium)

| Variant | MAE | mot 50/50: diff | p rå | Holm p | mot rb_updated: p rå | Holm p | mot J2 V2: p rå | Holm p |
|---|---|---|---|---|---|---|---|---|
| `k2_avg_ridge_l` | **0,199** | −0,018 | 0,002 | **0,014** | 0,004 | 0,033 | 0,001 | 0,009 |
| `k2_avg_ens_s` | 0,201 | −0,016 | 0,008 | **0,055** | 0,005 | 0,035 | 0,004 | 0,026 |
| `k2_avg_hgb_s` | 0,201 | −0,015 | 0,028 | 0,142 | 0,006 | 0,039 | 0,006 | 0,035 |
| `k2_avg_ridge_s` | 0,206 | −0,010 | 0,014 | **0,083** | 0,008 | 0,040 | 0,007 | 0,036 |
| `k2_avg_lasso_s` | 0,212 | −0,004 | 0,164 | 0,654 | 0,011 | 0,040 | 0,019 | 0,077 |
| `k2_rb_ridge_s` | 0,213 | −0,004 | 0,323 | 0,968 | 0,010 | 0,040 | 0,025 | 0,077 |
| `k2_j2_ridge_s` | 0,227 | +0,010 | 0,793 | 1 | 0,068 | 0,136 | 0,039 | 0,078 |
| `k2_rb_hgb_s` | 0,241 | +0,024 | 0,952 | 1 | 0,170 | 0,170 | 0,444 | 0,444 |
| 50/50 (referens) | 0,217 | – | – | – | | | | |
| J2 V2 (referens) | 0,243 | | | | | | | |
| rb_updated (referens) | 0,256 | | | | | | | |

**Tre varianter klarade urvalsskärmen** (Holm p < 0,10 mot 50/50 och inte högre MAE än 50/50 2024–26):
`k2_avg_ridge_l`, `k2_avg_ens_s` och `k2_avg_ridge_s`.

### Bara rapport
- 2018-02..2026-10 (ML aktiv, n = 105): ridge_l 0,211, ens_s 0,214, ridge_s 0,222 mot 50/50 0,235
  (Holm 0,009 / 0,043 / 0,071).
- 2024-01..2026-10 (använd, n = 34): ridge_l 0,229, ens_s 0,217, ridge_s 0,226 mot 50/50 0,246. Inget signifikant
  (Holm ≥ 0,42), men alla tre lägre.
- Per år (diff mot 50/50): vinsten kommer 2020–2025 (störst 2022 och 2025). **2019 och 2026 (10 mån) är
  varianterna något sämre** (+0,003 till +0,03). Vinsten är alltså inte jämn; den sitter i oroliga år.
- Av de 105 aktiva månaderna är ridge_l och ens_s bättre än 50/50 i ca 60 %; vinsten kommer mest från färre stora förbättringar
  (största enskilda: 2023-05, 2021-01, 2020-06). Medeljusteringen mot 50/50 är bara ±0,07 pe.

### Revisionsläckage
Enligt förregistreringen är `k2_avg_ridge_l` inte "obekräftad", eftersom `k2_avg_ridge_s` (inga reviderade
serier) också klarar skärmen. **Tillägg efter resultat (diagnostik, räknas mot taket, inte i Holm-familjen):**
`k2_avg_ridge_lnr` = ridge_l utan de 24 reviderade serierna: MAE 0,199 (ensidigt p = 0,001 mot 50/50), två-
sidigt p = 0,82 mot ridge_l. Vinsten kommer alltså inte från reviderade serier.

## Gissningen innan
Fel i riktningen. Jag gissade att ingen variant skulle klara skärmen och att L och boosting skulle vara sämre
än S och ridge. Utfallet: ridge på L var bäst, boosting på S var lika bra som ridge på L, och tre klarade
skärmen. Residual mot rb_updated eller j2 som mål (gissat: liten skillnad) var tydligt sämre än mot 50/50.

## Modellen i korthet
- **Ridge (S, bas 50/50):** vald alpha 100–1000, alltså kraftig krympning. Vikterna är nära noll till 2021 och
  växer sedan: euroområdets snabbestimat (`ea_news`), energinyheten gånger prognosålder (`energy_x_age`),
  elprisavvikelsen och KI:s prisplaner för livsmedel och sällanköp. Interceptet ≈ +0,015–0,05 rättar 50/50:s
  svaga underskattning. `gap` får ingen vikt: 50/50-vikten är redan rätt.
- **Ridge (L):** samma S-features överst, plus euroområdets snabbestimat för varor och totalt, utlåningstillväxt,
  hushållens inflationsförväntningar och GSCPI med små vikter. Alpha 300–1000.
- **Lasso (S):** väljer oftast `ea_news` (55 % av fönstren), `energy_x_age` (36 %), drivmedel (30 %). Lasso krymper
  för hårt och blir nästan 50/50 (0,212).
- **Boosting (S, bas 50/50):** permutationsvikt utanför urvalet: `energy_x_age` och `ea_news` (+0,010 MAE var),
  `el_dev` (+0,006). Väljer nästan alltid learning_rate 0,03, 50 träd, djup 2–3, alltså en svag modell.
- **Boosting mot rb_updated** (0,241) lär sig `gap` och `gap_x_age` men sämre än 50/50 gör utan skattning.

## Vad lärde vi oss (för modellvalet)
1. **Basen avgör.** Samma modell med 50/50 som bas (krymper mot den bästa kända prognosen) gav 0,206; med
   rb_updated som bas 0,213 och med j2 som bas 0,227. Att lära om kombinationsvikten kostar mer än det ger.
2. **ML tillför något utöver 50/50 när det får krympa mot 50/50:** information som kommit efter Riksbankens
   cutoff och som inte redan ligger i j2 (euroområdets snabbestimat, energichockens storlek gånger hur gammal
   Riksbanksprognosen är, prisplaner). Effekten, −0,01 till −0,02 pe, är av samma storlek som J1:s vinst och
   ligger i oroliga år.
3. **Bredd hjälpte lite med hård regularisering**, men vinsten L mot S kommer främst 2020 (pandemin) och är
   osäker. Ensemblen ridge+boosting (S) ger nästan samma MAE utan katalogserier.
4. **Försiktighet:** urvalsevidens på 105 aktiva månader, gissningen innan var fel, 2026 går åt fel håll, och
   alla tre varianterna liknar varandra (inte tre oberoende bevis). Skuggprognoser är det som avgör.

## Frysning och kandidat för K1
Frysta vid **415ba6f** (kod i `k2_ml.py` från 2318fa7; senare commits lägger bara till diagnostiken).
Parametrar: `MIN_TRAIN = 36`, `TimeSeriesSplit(n_splits=4)`, ridge-alpha {0,1 … 3000}, boosting-grid
lr {0,03, 0,1} × djup {2, 3} × träd {50, 150}, min_samples_leaf 8, random_state 0; feature-listor `SMALL` och
`catalog_keys()`. Live-prognos för t: `K2Runner(build_design(...)).forecast(namn, i)` med data till deadline(t).

**Förslag (Johannes/K1 beslutar, registreras inte här):**
- Huvudkandidat: **`k2_avg_ens_s`** (Holm 0,055). Behöver bara data som J1/J2 redan använder plus euroområdets
  snabbestimat, inga katalogserier och inga reviderade serier, så live-driften är enkel och samma som backtesten.
- Alternativ: `k2_avg_ridge_l` (starkast evidens, Holm 0,014), men kräver 43 katalogserier as-of live.

## BLOCKED
Inget. Inga nya datahämtningar gjordes. Inga nya paket (scikit-learn fanns).
