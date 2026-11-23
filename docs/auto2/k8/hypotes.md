# K8 Livsmedelskomponenten: förregistrering

Skriven 2026-11-23 innan något fel för 2015–2026 har beräknats för varianterna nedan.
Bas: main @ 51fa62f (K0–K4, K6 mergade), gren `auto2/k8`. K8:s tak: **högst 4 varianter**.
Kod: `src/kpif_nowcast/k8_food.py`. Inga nya hämtningar.

## Varför
K3 ([fel_per_komponent.md](../k3/fel_per_komponent.md)): livsmedel står för 20 % av kvadratfelet 2015–2026 och
29 % 2024–2026. Livsmedelsbidraget prognostiseras i dag bara med säsong + 12-månaderstrend. K0 testade
prisledserierna som fria korrektioner på totalen (ingen överlevde). Här testas de där de hör hemma: på
livsmedelsbidraget, med laggar som speglar att producent- och råvarupriser når butik först efter månader.

## Hypotes och gissning
**Hypotes:** livsmedelsbidragets avvikelse från säsong + trend (residualen) går delvis att förutsäga med
producentpriser för livsmedel (hemmamarknad och import, 1–6 mån bakåt), världsmarknadspriser på mat i SEK
(2–7 mån bakåt), kronkursen och KI:s prisplaner i dagligvaruhandeln och livsmedelsindustrin. Signalen är
störst i oroliga år (2022–2023), liten annars. I totalen späds den ut: J2:s livsmedelsdel väger hälften i
50/50-snittet, och livsmedel är ~20 % av felet.

**Gissning innan (MAE totalt 2015-01..2026-10):**
- Livsmedelsbidragets eget fel (pe av m/m): från 0,070 (bas) till 0,064–0,069 (−1 till −8 %), störst för ridge;
  2022–2023 −10 till −20 %.
- Totalt mot 50/50 (0,217): diff −0,001 till −0,005 för V1–V3, rå ensidig p 0,05–0,4. **Ingen variant klarar
  urvalsskärmen** efter Holm (gissning ~70 %).
- V3 (utan reviderade serier) sämre än V2: det mesta av signalen sitter i PPI.
- V4 mot `k2_avg_ens_s` (0,201): diff 0 till −0,003, p > 0,2 (K2 har redan KI:s livsmedelsplaner med).

## Uppställning
- **Mål för livsmedelsmodellen:** residualen `r_t = food_t − base_t`, där `food_t` är SCB:s bidrag från
  livsmedel till KPIF:s månadsförändring (TAB6628, pe) och `base_t = seasonal_trend_additive` (samma bas som i
  J2 V2 och den skarpa modellen; data till t−1). Ingen skatterensning (som J2; momssänkningen 2026-04 ligger
  kvar i residualen och i trenden, se nedan).
- **Korrektion:** `ĉ_t` = predikterad residual. Livsmedelsbidraget blir `base_t + ĉ_t`. I årstakt:
  `Δyy_t = k_t · ĉ_t`, `k_t = index(t−1)/index(t−12)` (exakt, eftersom årstakten är linjär i m/m-prognosen).
- **Total prognos:** `j2_food = j2 + k·ĉ` (J2 V2 med livsmedelsdelen utbytt). 50/50-varianten blir
  `0,5·rb_updated + 0,5·j2_food = avg + 0,5·k·ĉ`. Med ĉ = 0 fås exakt 50/50, så jämförelsen är nästlad.
- **Träning:** expanderande fönster, rader s < t med publicerat bidrag (TAB6628 för t−1 finns före deadline(t)),
  från 2005-01. Minst 36 träningsrader, annars ĉ = 0 (gäller bara 2005–2007; alla mål 2015–2026 är aktiva).
- **Features, punkt-i-tid:** varje rad s byggs från `observations.as_of(serie, deadline(s))`
  (deadline = dag 4 i s+1), även träningsraderna. Senast tillgängliga period vid deadline(t):
  PPI t−1 (30 d), IMF/FRED t−2 (60 d), KI t (3 d), KIX t (1 d), SEK/USD t (dagliga fixningar, hel månad).

### Drivande serier (alla finns redan)
| Namn | Serie | Transform | Laggar (de 6 senast tillgängliga) | revised |
|---|---|---|---|---|
| `ppi_hm` | `ppi_hmpi_food` (TAB3184, hemmamarknad livsmedel) | 100·Δlog m/m | 1–6 | ja |
| `ppi_imp` | `ppi_impi_food` (TAB3184, import livsmedel) | 100·Δlog m/m | 1–6 | ja |
| `cmd_sek` | IMF-råvaror för mat via FRED (vete, nöt, gris, fågel, socker, kaffe, kakao, palm-, soja-, raps-, solrosolja): likaviktat medel av 100·Δlog över de serier som finns, plus 100·Δlog SEK/USD (Riksbanken, månadsmedel) | m/m | 2–7 | ja |
| `kix` | `kix` (kronindex, högre = svagare krona) | 100·Δlog m/m | 0–5 | nej |
| `ki_groc` | `ki_prices_grocery` (prisplaner dagligvaruhandeln) | nivå (nettotal) | 0–5 | nej |
| `ki_food` | `ki_prices_food_industry` (prisplaner livsmedelsindustrin) | nivå (nettotal) | 0–5 | nej |

SEK/EUR: Riksbankens dagliga SEK/EUR-cache börjar först 2011, så **KIX** (handelsvägd, euron väger mest) används
i stället för SEK/EUR, för att få träning från 2005 utan ny hämtning. `ki_purchase_prices_grocery` börjar
2015-10 och tas inte med.

## Varianter (exakt fyra, alla räknas mot taket)
1. **`k8_fixed`** – fasta förregistrerade laggar, OLS med intercept, 6 regressorer ("acceleration": kort medel
   minus 12-månadersmedel, så att bara nyhet utöver basens trend räknas):
   - `ppi_hm`: medel lagg 1–3 minus medel lagg 1–12
   - `ppi_imp`: medel lagg 1–3 minus medel lagg 1–12
   - `cmd_sek`: medel lagg 2–7 minus medel lagg 2–13
   - `kix`: medel lagg 0–5 minus medel lagg 0–11
   - `ki_groc`: medel lagg 0–2 minus medel lagg 0–11
   - `ki_food`: medel lagg 0–2 minus medel lagg 0–11
   
   Total: `avg + 0,5·k·ĉ`. Referens 50/50.
2. **`k8_ridge`** – ridge med nästlad CV (som K2): alla 6 serier × 6 laggar (36) plus 12-månadersmedel per serie
   (6) = 42 features. Median-imputering och standardisering anpassas bara på fönstrets träningsrader;
   alpha ∈ {0,1, 0,3, 1, 3, 10, 30, 100, 300, 1000, 3000} väljs med `TimeSeriesSplit(4)` på MAE inom fönstret,
   sedan refit på hela fönstret (`k2_ml.fit_nested`). Laggvalet sker alltså genom krympningen inom varje
   fönster. Total: `avg + 0,5·k·ĉ`. Referens 50/50.
3. **`k8_ridge_nr`** – som 2 men utan reviderade serier (bara `kix`, `ki_groc`, `ki_food`: 21 features).
   Diagnostik för revisionsläckage, men förregistrerad och i Holm-familjen. Referens 50/50.
4. **`k8_ens_ridge`** – `k2_avg_ens_s` + 0,5·k·ĉ från `k8_ridge`. Referens `k2_avg_ens_s` (K2:s kandidat,
   omräknad med `K2Runner`, oförändrad kod).

## Utvärdering
- Mål 2015-01..2026-10 (n = 142) för totalen där alla serier finns; `k2_avg_ens_s` finns från 2015-02, så
  V4 och alla Holm-jämförelser körs på det gemensamma urvalet 2015-02..2026-10 (n = 141). 2015–2026 är
  modellvalsperioden; 2024–2026 är använd och rapporteras bara.
- DM-test på absolutfel (`evaluation.dm_test`), **ensidigt** (H1: varianten har lägre MAE än sin referens;
  alla jämförelser är nästlade), **Holm över de fyra varianterna**.
- **Urvalsskärm:** Holm-p < 0,10 mot referensen och inte högre MAE än referensen 2024–2026.
- Revisionsflagga: V1, V2 och V4 bygger på reviderade serier (PPI, IMF). Klarar någon av dem skärmen men inte V3,
  märks den "obekräftad (revisionsläckage möjligt)". Observationstabellen har bara en vintage (backfill), så
  PPI- och råvaruvärden är dagens reviderade siffror förskjutna med publiceringsfördröjningen.
- Rapporteras också: livsmedelsbidragets eget fel (MAE, pe av m/m, och k·fel i årstakt som K3:s tabell 2),
  per år, ensidig DM på livsmedelsfelet (bara rapport), och koefficienter i sista fönstret.
- Körning loggas med `evaluation.log_run("k8_food", ...)`.
- `tests/test_k8_food.py`: korrektionen och totalprognosen för t är identiska med och utan data efter
  deadline(t) (components till t−1, observations med known_from ≤ deadline, SEK/USD till t).

## Kända begränsningar (före körning)
- Momssänkningen på livsmedel 2026-04 (−0,76 pe) ligger i residualen och i 12-månaderstrenden till 2027-03.
  Ingen av varianterna kan förutsäga den; den påverkar bara 2026 (använd period). Ingen skatterensning här,
  för att inte blanda två ändringar i samma test.
- Om en variant klarar skärmen fryses den vid committen (registreras inte här; K1/Johannes beslutar).
