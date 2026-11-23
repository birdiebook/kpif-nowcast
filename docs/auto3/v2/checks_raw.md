# V2 rådata (genererad av `python -m kpif_nowcast.v2_screen`, kod @ c3f7670+dirty)

## Kontroll 7: baserna reproduceras (MAE 2015-02..2026-10)

- Bas R (`k2_avg_ridge_l_shadow`): MAE 0.1993, n = 141, förregistrerat 0.200 → AVVIKER
- Bas A (`avg_5050`): MAE 0.2165, n = 141, förregistrerat 0.217 → OK
- Bas R mot skuggan på main före körning 3 (129bbb0, samma data): största absoluta skillnad 0.00e+00 → identisk
  - Avvikelsen från det förregistrerade 0,200 kommer inte från körning 3: skuggan är identisk med main före körning 3. Den förklaras av K11:s publiceringskalender (mergad efter K2b:s 0,200).

## Kontroll 8: redan registrerade varianter oförändrade

- Mot K12:s per-modelltabell (docs/auto2/k12/resultat.md, 38 modeller): 27 identiska på 3 decimaler. Avvikelser (K12 → nu): `k2_avg_ridge_l` 0,199 → 0,200, `k2_avg_ridge_lnr` 0,199 → 0,200, `k2_avg_ens_s` 0,201 → 0,202, `k8_ens_ridge` 0,201 → 0,202, `k2_avg_hgb_s` 0,201 → 0,202, `k2_avg_ridge_s` 0,206 → 0,207, `k7_k2_cal_full` 0,210 → 0,211, `k2_avg_lasso_s` 0,212 → 0,213, `j1_hyb_energy_ea` 0,222 → 0,223, `k2_j2_ridge_s` 0,227 → 0,230, `j3_combo` 0,254 → 0,255. Saknas: inga. n = 141.
- Familjer: {'refs': 'cache', 'phase': 'cache', 'j1': 'cache', 'j2': 'cache', 'j3': 'cache', 'j4': 'cache', 'k0': 'cache', 'k2': 'cache', 'k7': 'cache', 'k8': 'cache'}.
- Mot main före körning 3 (129bbb0, samma data, alla 47 kolumner i k12_global.collect_all, hela tidsserien): största absoluta skillnad 4.44e-16; avvikande: inga; saknas: inga → identiska.
  - Avvikelserna mot K12:s tabell kommer alltså inte från körning 3. De förklaras av K11 (publiceringskalendern och nya laggar, mergad efter K12:s körning; K11 rapporterade +0,001 för K2).
- K12:s U1 utan körning 3 (block 3, B och seed som K12): SPA consistent rb_updated 0,035, avg_5050 0,021 (K12:s fil: rb_updated 0,035, avg_5050 0,025); 38 serier.

## Kontroll 1–2: period känd vid deadline

Avvikelser från tabellen i avsnitt 1: 16 (varav okända: 0).

| series                 | target   | p_star   | expected   | kind         | why                           |
|:-----------------------|:---------|:---------|:-----------|:-------------|:------------------------------|
| el_contract_spot_share | 2022-02  | 2021-12  | 2022-01    | late release | documented release 2022-04-30 |
| el_contract_spot_share | 2022-03  | 2021-12  | 2022-02    | late release | documented release 2022-04-30 |
| el_contract_spot_share | 2023-06  | 2023-04  | 2023-05    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2023-07  | 2023-04  | 2023-06    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2023-08  | 2023-04  | 2023-07    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2023-09  | 2023-04  | 2023-08    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2023-10  | 2023-04  | 2023-09    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2023-11  | 2023-04  | 2023-10    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2023-12  | 2023-04  | 2023-11    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2024-01  | 2023-04  | 2023-12    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2024-02  | 2023-04  | 2024-01    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2024-03  | 2023-04  | 2024-02    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2024-04  | 2023-04  | 2024-03    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2024-05  | 2023-04  | 2024-04    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2024-06  | 2023-04  | 2024-05    | late release | documented release 2024-09-27 |
| el_contract_spot_share | 2024-07  | 2023-04  | 2024-06    | late release | documented release 2024-09-27 |

- Kontroll 2: p* för `el_contract_spot_share` vid deadline 2024-01 = 2023-04 (väntat 2023-04).

## Kontroll 3: marginal till deadline (dagar)

|                             |   min_days_used_before_deadline |   min_days_next_after_deadline |
|:----------------------------|--------------------------------:|-------------------------------:|
| easter_window_days          |                             370 |                            nan |
| kpif_package_holidays_index |                              17 |                             11 |
| kpif_air_transport_index    |                              17 |                             11 |
| kpif_accommodation_index    |                              17 |                             11 |
| guest_nights_domestic       |                              13 |                             14 |
| guest_nights_foreign        |                              13 |                             14 |
| kpi_rent_index              |                              17 |                             11 |
| el_contract_spot_share      |                               4 |                             24 |
| sek_eur                     |                               3 |                            nan |
| sek_usd                     |                               3 |                            nan |

## Täckning (minsta antal observationer)

|                             | first   |   n_primary | ok   |
|:----------------------------|:--------|------------:|:-----|
| easter_window_days          | 2015-01 |         117 | True |
| kpif_package_holidays_index | 2015-01 |         117 | True |
| kpif_air_transport_index    | 2015-01 |         117 | True |
| kpif_accommodation_index    | 2015-01 |         117 | True |
| guest_nights_domestic       | 2015-01 |         117 | True |
| guest_nights_foreign        | 2015-01 |         117 | True |
| kpi_rent_index              | 2015-01 |         117 | True |
| el_contract_spot_share      | 2015-01 |         103 | True |
| sek_eur                     | 2015-01 |         117 | True |
| sek_usd                     | 2015-01 |         117 | True |

- Inaktuella-regeln: x saknas för elavtal i 12 av 12 målmånader 2023-08..2024-07; brottregeln: x(2023-03) = nan.

- Elavtal, målmånader utan x i primärperioden: 2023-03, 2023-08, 2023-09, 2023-10, 2023-11, 2023-12, 2024-01, 2024-02, 2024-03, 2024-04, 2024-05, 2024-06, 2024-07, 2024-08.
