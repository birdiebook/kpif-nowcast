# K8 Livsmedelskomponenten: resultat (urvalsevidens)

Förregistrering: [hypotes.md](hypotes.md) (commit 1bc8e84, före körning). Kod: `src/kpif_nowcast/k8_food.py`.
Körning: `experiments/runs/20261123T093910Z_k8_food.csv` vid 711f3bd (kodfix av en tabellnyckel efter en
första körning som kraschade i rapportdelen; siffrorna var identiska). Hela tabeller: [results_raw.md](results_raw.md).

**Varianter: 4 av K8:s 4** (`k8_fixed`, `k8_ridge`, `k8_ridge_nr`, `k8_ens_ridge`), inga tillägg efter resultat.
DM-test på absolutfel, ensidigt (H1: varianten har lägre MAE än referensen; alla jämförelser nästlade),
Holm över de fyra.

## Vad som byggdes
Livsmedelsbidraget till KPIF:s månadsförändring (TAB6628) = säsong + 12-månaderstrend (samma bas som J2 V2)
plus en predikterad residual ĉ från PPI livsmedel (hemmamarknad och import, lagg 1–6), IMF-råvaror för mat
i SEK (lagg 2–7), KIX och KI:s prisplaner i dagligvaruhandeln och livsmedelsindustrin (lagg 0–5). Allt
punkt-i-tid via `observations.as_of(deadline)`, också träningsraderna. Totalen: 50/50 + 0,5·k·ĉ (J2 V2 med
livsmedelsdelen utbytt). SEK/EUR ersattes av KIX före körning (SEK/EUR-cachen börjar 2011; ingen ny hämtning).

## Resultat totalt, 2015-02..2026-10, n = 141 (förregistrerat kriterium)

| Variant | Referens | MAE | Ref-MAE | Diff | p ensidigt (rå) | Holm p | 2024–26 diff |
|---|---|---|---|---|---|---|---|
| `k8_fixed` (fasta laggar, OLS) | 50/50 | 0,214 | 0,217 | −0,002 | 0,136 | 0,408 | +0,002 |
| `k8_ridge` (42 features, nästlad CV) | 50/50 | 0,216 | 0,217 | −0,001 | 0,194 | 0,408 | +0,001 |
| `k8_ridge_nr` (utan reviderade serier) | 50/50 | 0,215 | 0,217 | −0,002 | 0,074 | 0,297 | +0,000 |
| `k8_ens_ridge` (K2-ensemble + livsmedel) | `k2_avg_ens_s` | 0,201 | 0,201 | +0,000 | 0,552 | 0,552 | +0,002 |

**Ingen variant klarade urvalsskärmen** (Holm p ≥ 0,30; alla är något sämre än referensen 2024–26, n = 34,
använd period). Gissningen före körning stämde (diff −0,001 till −0,005, ingen klarar).

Per år (diff mot referens, se results_raw): vinsten sitter i **2022** (−0,012 till −0,016) och för `k8_fixed`
också 2023 (−0,019). 2019, 2020 och 2024 är varianterna sämre (upp till +0,008). Det är alltså en effekt i
inflationschocken, inte en jämn förbättring.

## Livsmedelsbidragets eget fel (pe av KPIF m/m; i årstakt = k·fel, jämförbart med K3:s tabell 2)

| Period | n | Bas | `k8_fixed` | `k8_ridge` | `k8_ridge_nr` | p ensidigt mot bas (fixed / ridge / nr) |
|---|---|---|---|---|---|---|
| 2015–2026 | 142 | 0,076 | **0,069** (−10 %) | 0,074 (−3 %) | 0,071 (−7 %) | 0,038 / 0,046 / 0,026 |
| 2015–2019 | 60 | 0,057 | 0,059 | 0,058 | 0,058 | 0,78 / 0,96 / 0,90 |
| 2020–2021 | 24 | 0,061 | 0,059 | 0,061 | 0,061 | 0,35 / 0,28 / 0,13 |
| 2022–2023 | 24 | 0,127 | **0,082** (−35 %) | 0,115 | 0,104 | 0,001 / 0,038 / 0,012 |
| 2024–2026 (använd) | 34 | 0,085 | 0,083 | 0,081 | 0,079 | 0,41 / 0,20 / 0,14 |
| 2015–2026 utan 2026-04 | 141 | 0,072 | 0,064 | 0,069 | 0,067 | 0,046 / 0,055 / 0,025 |

(Bara rapport, inte i Holm-familjen. I årstakt: bas 0,079, `k8_fixed` 0,071.)
Komponentmodellen fungerar alltså på sin egen komponent, främst 2022–2023, men i totalen syns bara en
bråkdel: korrektionen i 50/50 är i snitt 0,015 pe (`k8_fixed`) eller 0,006 pe (ridge), och livsmedelsfelet
är bara en del av totalfelet, så den drunknar i övriga komponenters fel.

## Modellen i korthet
- **`k8_fixed`:** stabila koefficienter över tid. Hemmamarknads-PPI (acceleration, +0,035–0,053 pe per
  procentenhet) och KIX (svagare krona → högre matpriser, +0,03–0,06) bär signalen; import-PPI får negativt
  tecken (samvarierar med hemma-PPI), råvarorna i SEK ≈ 0. KI:s prisplaner små positiva.
- **`k8_ridge`:** väljer alpha 3000 (gridens tak) i 88 av 142 fönster, alltså nästan ingen korrektion före
  2022. Först efter 2022 växer vikterna (PPI lagg 1, råvarornas 12-månadersmedel, KI-planer, KIX).
- **`k8_ridge_nr`:** bara KI-planer och KIX. Väljer lägre alpha (10–100) efter 2022 och lägger vikt på
  KI-planernas avvikelse från sitt 12-månadersmedel.

## Revisionsläckage
Ingen variant klarade skärmen, så ingen märks "obekräftad". Diagnostiken (V3, förregistrerad) visar att
reviderade serier inte är källan till den lilla vinsten: `k8_ridge_nr` är något bättre än `k8_ridge`
(tvåsidigt p = 0,13). För `k8_fixed`, där PPI bär mest, kan en del av livsmedelsvinsten 2022–23 komma från att
backfill-vintagen är dagens reviderade PPI.

## Informationsmängdstest
`tests/test_k8_food.py`: för 2016-03, 2022-07 och 2026-10 är korrektionerna och totalerna för V1–V3
identiska (tolerans 1e−10) när KPIF/komponenter klipps vid t−1, observationer vid known_from ≤ deadline,
Riksbanksvintagar före deadline och SEK/USD vid deadline. V4 = K2:s ensemble (testad i `test_k2_ml.py`) +
samma korrektion. Hela sviten: 107 passerade, 1 hoppad.

## Bedömning: skugga eller inte
**Frys inte, ingen skugga.** Ingen variant klarade skärmen, vinsten i totalen är ≤ 0,002 pe och sitter i 2022–23,
och 2024–26 är alla något sämre. Mot K2:s kandidat (`k2_avg_ens_s`) tillför livsmedelsmodellen ingenting
(K2 har redan KI:s livsmedelsplaner och fångar 2022 på annat sätt).

## BLOCKED
Inget. Inga nya hämtningar (SEK/USD och övriga serier fanns i cachen och observationstabellen), inga nya paket.

## Vad lärde vi oss
1. **Rätt form hjälper komponenten men inte totalen här.** Producentpriser och kronan förutsäger
   livsmedelsbidraget 2022–2023 (−35 % fel med fasta laggar), men i övriga år är residualen brus som säsong +
   trend redan hanterar. I 50/50-snittet väger livsmedelsdelen hälften, så effekten på totalen blir ~0,002 pe.
2. **Fasta, enkla laggar slog ridge med laggval** på komponenten (0,069 mot 0,074). Med ~120–250 träningsrader
   och en signal som bara finns i några få år krymper den nästlade CV:n nästan allt till noll.
3. **Livsmedelsfelet 2026 är momssänkningen** (2026-04, residual −0,74 pe), som ingen prisled kan förutse.
   Den ligger dessutom i 12-månaderstrenden till 2027-03 och i säsongsmönstret för april de kommande fem åren;
   en skatterensad bas för livsmedel är en tydlig kandidat för nästa steg (inte testad här, inget varianttak kvar).
4. **Öppen fråga (inte testad):** halv vikt (0,5·k·ĉ) var förregistrerat eftersom bara J2-halvan har en
   livsmedelsmodell. Riksbankens prognos saknar också prisnyheten, så full vikt eller en skattad vikt kunde
   ge mer. Det kräver en ny förregistrerad variant.
