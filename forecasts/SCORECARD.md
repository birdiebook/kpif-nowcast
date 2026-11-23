# Scorecard – skarpa prognoser

Varje prognos committas före SCB:s snabb-KPI. Årstakt KPIF, procent.

| Månad   | Status      |   Prognos | 80%-intervall   |   Riksbanken | Utfall   | Fel   | Fel Riksbanken   | Manuell just.   |
|:--------|:------------|----------:|:----------------|-------------:|:---------|:------|:-----------------|:----------------|
| 2026-11 | PRELIMINARY |       2.1 | 1.5–2.6         |         1.73 |          |       |                  |                 |


## Champion/challenger

Skuggprognoser loggas i `forecasts/shadow/<modell>/<månad>.json` (genereras av `python -m kpif_nowcast.pipeline monthly`). Årstakt KPIF, absolut fel i procentenheter.

| Modell         | Roll                  | MAE 2015–26 (urval)   |   MAE 2024–26 (använd) | MAE live   | Första backtestmånad   |
|:---------------|:----------------------|:----------------------|-----------------------:|:-----------|:-----------------------|
| comp_fuel_el   | champion (live model) | –                     |                  0.375 | –          | 2023-12                |
| j2_el_dev      | challenger            | 0.243                 |                  0.252 | –          | 2014-12                |
| j1_comb_equal  | challenger            | 0.217                 |                  0.246 | –          | 2015-02                |
| k2_avg_ens_s   | challenger            | 0.202                 |                  0.22  | –          | 2015-02                |
| k2_avg_ridge_l | challenger            | 0.199                 |                  0.229 | –          | 2015-02                |
| rb_updated     | benchmark             | 0.256                 |                  0.267 | –          | 2015-02                |
| riksbank       | benchmark             | 0.320                 |                  0.326 | –          | 2015-02                |

- **MAE 2015–26 är urvalsevidens**: modellerna valdes på den perioden. Gemensamt urval 2015-02..2026-10, n = 141, bara modeller som finns från 2015 (`comp_fuel_el` har energikorrektion först från 2023-12 och saknas där).
- **MAE 2024–26** är en redan använd period, samma månader för alla modeller (2024-01..2026-10, n = 34). Rapporteras, väljs inte på.
- **Live**: FINAL-skuggprognoser med publicerat utfall, samma månader för alla modeller: **0 månader**. Än så länge finns ingen riktig evidens.
