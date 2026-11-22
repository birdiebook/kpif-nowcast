# J2 resultat (urvalsevidens)

Körning: `experiments/runs/20261122T220640Z_j2_el.csv` (kod @ 63fe150). Full tabell: [results_raw.md](results_raw.md).
Globalt varianttotal vid körningen: **5/50**. Alla p-värden nedan är urvalsevidens från samma urval 2015–2026.

## 2015-01..2026-10, n = 141 (modellval)

| Modell | MAE | Diff mot comp_fuel | DM p mot comp_fuel (rå) | Holm p (5 varianter) | DM p mot rb_updated |
|---|---|---|---|---|---|
| V2 j2_el_dev | 0,243 | −0,073 | 0,003 | 0,014 | 0,57 |
| V4 j2_el_dev_var (revised) | 0,243 | −0,073 | 0,005 | 0,015 | 0,56 |
| V5 j2_el_dev_se3 | 0,245 | −0,070 | 0,004 | 0,015 | 0,63 |
| V3 j2_el_trendbase | 0,248 | −0,068 | 0,009 | 0,018 | 0,74 |
| V1 j2_el_raw | 0,279 | −0,037 | 0,039 | 0,039 | 0,32 |
| rb_updated | 0,256 | | | | – |
| comp_fuel | 0,316 | – | – | – | 0,03 |

## 2024-01..2026-10, n = 34 (använd period, bara rapport)
V2 0,252, V4 0,238, V1 0,372, comp_fuel 0,443, rb_updated 0,267. Ingen variant blir sämre än comp_fuel.

## Tolkning
- Alla fem varianter klarade urvalsskärmen mot comp_fuel (Holm p < 0,10, inte sämre 2024–26).
- **Dubbelräkningen var verklig:** rå el (V1) ger −0,037, el som avvikelse från säsongen (V2) −0,073.
  Båda sätten att fixa den (V2, V3) ger nästan samma sak.
- Rörlig avtalsandel (V4) och zonvikt (V5) tillför inget på 2015–26 utöver V2.
- Mot rb_updated: MAE 0,243 mot 0,256, p = 0,57. Skillnaden går **inte** att skilja från slump
  (minsta upptäckbara ≈ 0,06–0,08). Ingen slutsats om att modellen är bättre än ribban.
- Störst vinst när Riksbankens prognos är 3 månader gammal (0,270 mot rb_updated 0,327) och i
  januari (0,410 mot 0,517, n = 11). Vid 1 månad är rb_updated bättre (0,188 mot 0,213).
  Det pekar på att en kombination (J1) kan ge mer.

## Frysning: skuggprognos från 2026-12
**V2 `j2_el_dev`** på grenen auto/j2-el @ SHA i taggen `auto/j2-done`.
Parametrar: komponentmodell (5-årig säsong + 12-mån trend), energikorrektion OLS utan intercept
på [fuel_chg, el_dev], expanderande fönster från 2012-01, min 24 månader; el_dev = el_chg − medel
av el_chg samma kalendermånad senaste ≤5 år; el SE3/SE4 70/30.
Valet mellan V2 och V4 (lika MAE) gjordes efter resultat: V2 valdes för att den saknar reviderade
features och är enklare. Johannes utvärderar den live.

## Januari
TAB3950 (nätpris 1 januari) publiceras i maj, alltså efter januari-KPI. Bara ändringen till 1
januari året innan kan användas. Inte testad. V2 är redan bäst i januari (0,410).
