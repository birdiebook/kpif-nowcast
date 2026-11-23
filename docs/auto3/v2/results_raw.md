# V2 rådata (genererad av `python -m kpif_nowcast.v2_screen`, kod @ 8e0ad8e)

## Kontroll 7: baserna reproduceras (MAE 2015-02..2026-10)

- Bas R (`k2_avg_ridge_l_shadow`): MAE 0.1993, n = 141, förregistrerat 0.200 → AVVIKER
- Bas A (`avg_5050`): MAE 0.2165, n = 141, förregistrerat 0.217 → OK
- Bas R mot skuggan på main före körning 3 (129bbb0, samma data): största absoluta skillnad 0.00e+00 → identisk
  - Avvikelsen från det förregistrerade 0,200 kommer inte från körning 3: skuggan är identisk med main före körning 3. Den kommer från ändringar på main efter K2b:s 0,200 (K11:s publiceringskalender och laggar) och möjligen dagens dataårgång.

## Kontroll 8: redan registrerade varianter oförändrade

- Mot K12:s per-modelltabell (docs/auto2/k12/resultat.md, 38 modeller): 27 identiska på 3 decimaler. Avvikelser (K12 → nu): `k2_avg_ridge_l` 0,199 → 0,200, `k2_avg_ridge_lnr` 0,199 → 0,200, `k2_avg_ens_s` 0,201 → 0,202, `k8_ens_ridge` 0,201 → 0,202, `k2_avg_hgb_s` 0,201 → 0,202, `k2_avg_ridge_s` 0,206 → 0,207, `k7_k2_cal_full` 0,210 → 0,211, `k2_avg_lasso_s` 0,212 → 0,213, `j1_hyb_energy_ea` 0,222 → 0,223, `k2_j2_ridge_s` 0,227 → 0,230, `j3_combo` 0,254 → 0,255. Saknas: inga. n = 141.
- Familjer: {'refs': 'cache', 'phase': 'cache', 'j1': 'cache', 'j2': 'cache', 'j3': 'cache', 'j4': 'cache', 'k0': 'cache', 'k2': 'cache', 'k7': 'cache', 'k8': 'cache'}.
- Mot main före körning 3 (129bbb0, samma data, alla 47 kolumner i k12_global.collect_all, hela tidsserien): största absoluta skillnad 4.44e-16; avvikande: inga; saknas: inga → identiska.
  - Avvikelserna mot K12:s tabell kommer alltså inte från körning 3. De kommer från main efter K12:s körning (K11:s publiceringskalender och laggar, mergad efter K12; K11 rapporterade +0,001 för K2) och kan delvis vara dagens dataårgång. Vilket av de två som ger vad har inte separerats.
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

## Screening bas R (`k2_avg_ridge_l_shadow`), primary 2017-02..2026-10 (bas-MAE 0.2113, n = 117)

| Serie | Grupp | MAE | diff mot bas | rå p (ensidig) | BH-q | n | aktiva | revised | täckning ok |
|---|---|---|---|---|---|---|---|---|---|
| `kpif_air_transport_index` | resor | 0,207 | -0,0041 | 0,143 | 0,998 | 117 | 117 | ja | ja |
| `easter_window_days` | resor | 0,212 | 0,0008 | 0,557 | 0,998 | 117 | 27 | nej | ja |
| `guest_nights_domestic` | resor | 0,212 | 0,0008 | 0,650 | 0,998 | 117 | 117 | ja | ja |
| `kpi_rent_index` | hyror | 0,217 | 0,0062 | 0,778 | 0,998 | 117 | 117 | ja | ja |
| `sek_usd` | kronan | 0,214 | 0,0029 | 0,864 | 0,998 | 117 | 117 | nej | ja |
| `kpif_package_holidays_index` | resor | 0,216 | 0,0046 | 0,937 | 0,998 | 117 | 117 | ja | ja |
| `kpif_accommodation_index` | resor | 0,215 | 0,0040 | 0,943 | 0,998 | 117 | 117 | ja | ja |
| `guest_nights_foreign` | resor | 0,215 | 0,0041 | 0,971 | 0,998 | 117 | 117 | ja | ja |
| `el_contract_spot_share` | el | 0,216 | 0,0048 | 0,986 | 0,998 | 117 | 103 | ja | ja |
| `sek_eur` | kronan | 0,214 | 0,0028 | 0,998 | 0,998 | 117 | 117 | nej | ja |

## Screening bas R (`k2_avg_ridge_l_shadow`), 2015-01..2026-10 (bas-MAE 0.1993, n = 141)

| Serie | Grupp | MAE | diff mot bas | rå p (ensidig) | BH-q | n | aktiva | revised | täckning ok |
|---|---|---|---|---|---|---|---|---|---|
| `kpif_air_transport_index` | resor | 0,196 | -0,0034 | 0,143 | 0,998 | 141 | 117 | ja | ja |
| `easter_window_days` | resor | 0,200 | 0,0006 | 0,557 | 0,998 | 141 | 27 | nej | ja |
| `guest_nights_domestic` | resor | 0,200 | 0,0007 | 0,650 | 0,998 | 141 | 117 | ja | ja |
| `kpi_rent_index` | hyror | 0,204 | 0,0051 | 0,778 | 0,998 | 141 | 117 | ja | ja |
| `sek_usd` | kronan | 0,202 | 0,0024 | 0,864 | 0,998 | 141 | 117 | nej | ja |
| `kpif_package_holidays_index` | resor | 0,203 | 0,0039 | 0,935 | 0,998 | 141 | 117 | ja | ja |
| `kpif_accommodation_index` | resor | 0,203 | 0,0033 | 0,944 | 0,998 | 141 | 117 | ja | ja |
| `guest_nights_foreign` | resor | 0,203 | 0,0034 | 0,969 | 0,998 | 141 | 117 | ja | ja |
| `el_contract_spot_share` | el | 0,203 | 0,0040 | 0,986 | 0,998 | 141 | 103 | ja | ja |
| `sek_eur` | kronan | 0,202 | 0,0023 | 0,998 | 0,998 | 141 | 117 | nej | ja |

## Screening bas R (`k2_avg_ridge_l_shadow`), 2024-01..2026-10 (used, report only) (bas-MAE 0.2292, n = 34)

| Serie | Grupp | MAE | diff mot bas | rå p (ensidig) | BH-q | n | aktiva | revised | täckning ok |
|---|---|---|---|---|---|---|---|---|---|
| `kpif_air_transport_index` | resor | 0,224 | -0,0047 | 0,296 | 0,984 | 34 | 34 | ja | ja |
| `el_contract_spot_share` | el | 0,230 | 0,0007 | 0,569 | 0,984 | 34 | 26 | ja | ja |
| `easter_window_days` | resor | 0,230 | 0,0009 | 0,586 | 0,984 | 34 | 9 | nej | ja |
| `sek_usd` | kronan | 0,230 | 0,0009 | 0,622 | 0,984 | 34 | 34 | nej | ja |
| `kpi_rent_index` | hyror | 0,233 | 0,0042 | 0,733 | 0,984 | 34 | 34 | ja | ja |
| `guest_nights_domestic` | resor | 0,229 | 0,0001 | 0,776 | 0,984 | 34 | 34 | ja | ja |
| `sek_eur` | kronan | 0,231 | 0,0022 | 0,870 | 0,984 | 34 | 34 | nej | ja |
| `guest_nights_foreign` | resor | 0,230 | 0,0004 | 0,882 | 0,984 | 34 | 34 | ja | ja |
| `kpif_accommodation_index` | resor | 0,230 | 0,0011 | 0,960 | 0,984 | 34 | 34 | ja | ja |
| `kpif_package_holidays_index` | resor | 0,231 | 0,0016 | 0,984 | 0,984 | 34 | 34 | ja | ja |

**Valda för bas R (ingen överlevde BH):** kpif_air_transport_index

## Screening bas A (`avg_5050`), primary 2017-02..2026-10 (bas-MAE 0.2320, n = 117)

| Serie | Grupp | MAE | diff mot bas | rå p (ensidig) | BH-q | n | aktiva | revised | täckning ok |
|---|---|---|---|---|---|---|---|---|---|
| `kpif_air_transport_index` | resor | 0,224 | -0,0079 | 0,032 | 0,320 | 117 | 117 | ja | ja |
| `easter_window_days` | resor | 0,232 | -0,0003 | 0,479 | 0,988 | 117 | 27 | nej | ja |
| `kpi_rent_index` | hyror | 0,238 | 0,0056 | 0,765 | 0,988 | 117 | 117 | ja | ja |
| `kpif_accommodation_index` | resor | 0,235 | 0,0031 | 0,833 | 0,988 | 117 | 117 | ja | ja |
| `guest_nights_domestic` | resor | 0,235 | 0,0029 | 0,867 | 0,988 | 117 | 117 | ja | ja |
| `sek_usd` | kronan | 0,235 | 0,0033 | 0,870 | 0,988 | 117 | 117 | nej | ja |
| `kpif_package_holidays_index` | resor | 0,237 | 0,0050 | 0,923 | 0,988 | 117 | 117 | ja | ja |
| `el_contract_spot_share` | el | 0,235 | 0,0034 | 0,935 | 0,988 | 117 | 103 | ja | ja |
| `sek_eur` | kronan | 0,236 | 0,0036 | 0,979 | 0,988 | 117 | 117 | nej | ja |
| `guest_nights_foreign` | resor | 0,237 | 0,0048 | 0,988 | 0,988 | 117 | 117 | ja | ja |

## Screening bas A (`avg_5050`), 2015-01..2026-10 (bas-MAE 0.2165, n = 141)

| Serie | Grupp | MAE | diff mot bas | rå p (ensidig) | BH-q | n | aktiva | revised | täckning ok |
|---|---|---|---|---|---|---|---|---|---|
| `kpif_air_transport_index` | resor | 0,210 | -0,0066 | 0,033 | 0,330 | 141 | 117 | ja | ja |
| `easter_window_days` | resor | 0,216 | -0,0002 | 0,479 | 0,987 | 141 | 27 | nej | ja |
| `kpi_rent_index` | hyror | 0,221 | 0,0046 | 0,765 | 0,987 | 141 | 117 | ja | ja |
| `kpif_accommodation_index` | resor | 0,219 | 0,0025 | 0,835 | 0,987 | 141 | 117 | ja | ja |
| `guest_nights_domestic` | resor | 0,219 | 0,0024 | 0,866 | 0,987 | 141 | 117 | ja | ja |
| `sek_usd` | kronan | 0,219 | 0,0027 | 0,869 | 0,987 | 141 | 117 | nej | ja |
| `kpif_package_holidays_index` | resor | 0,221 | 0,0041 | 0,920 | 0,987 | 141 | 117 | ja | ja |
| `el_contract_spot_share` | el | 0,219 | 0,0028 | 0,934 | 0,987 | 141 | 103 | ja | ja |
| `sek_eur` | kronan | 0,219 | 0,0030 | 0,979 | 0,987 | 141 | 117 | nej | ja |
| `guest_nights_foreign` | resor | 0,221 | 0,0040 | 0,987 | 0,987 | 141 | 117 | ja | ja |

## Screening bas A (`avg_5050`), 2024-01..2026-10 (used, report only) (bas-MAE 0.2461, n = 34)

| Serie | Grupp | MAE | diff mot bas | rå p (ensidig) | BH-q | n | aktiva | revised | täckning ok |
|---|---|---|---|---|---|---|---|---|---|
| `easter_window_days` | resor | 0,243 | -0,0031 | 0,258 | 0,961 | 34 | 9 | nej | ja |
| `kpif_air_transport_index` | resor | 0,244 | -0,0021 | 0,396 | 0,961 | 34 | 34 | ja | ja |
| `sek_usd` | kronan | 0,246 | -0,0001 | 0,485 | 0,961 | 34 | 34 | nej | ja |
| `el_contract_spot_share` | el | 0,247 | 0,0008 | 0,569 | 0,961 | 34 | 26 | ja | ja |
| `guest_nights_domestic` | resor | 0,246 | 0,0002 | 0,680 | 0,961 | 34 | 34 | ja | ja |
| `guest_nights_foreign` | resor | 0,247 | 0,0006 | 0,871 | 0,961 | 34 | 34 | ja | ja |
| `kpif_accommodation_index` | resor | 0,248 | 0,0016 | 0,919 | 0,961 | 34 | 34 | ja | ja |
| `sek_eur` | kronan | 0,250 | 0,0041 | 0,944 | 0,961 | 34 | 34 | nej | ja |
| `kpi_rent_index` | hyror | 0,253 | 0,0070 | 0,957 | 0,961 | 34 | 34 | ja | ja |
| `kpif_package_holidays_index` | resor | 0,249 | 0,0027 | 0,961 | 0,961 | 34 | 34 | ja | ja |

**Valda för bas A (ingen överlevde BH):** kpif_air_transport_index

## Gemensamt test (projektet totalt 53 varianter)

| Variant | Bas | Serier | Period | MAE | bas-MAE | diff | rå p | Holm p | n | aktiva | MAE rb_updated | p mot rb_updated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `v2_r_corr` (nr 52) | k2_avg_ridge_l_shadow | kpif_air_transport_index | primary 2017-02..2026-10 | 0,2072 | 0,2113 | -0,0041 | 0,143 | 0,143 | 117 | 117 | 0,2806 | 0,002 |
| `v2_r_corr` (nr 52) | k2_avg_ridge_l_shadow | kpif_air_transport_index | 2015-01..2026-10 | 0,1959 | 0,1993 | -0,0034 | 0,143 | – | 141 | 117 | 0,2555 | 0,003 |
| `v2_r_corr` (nr 52) | k2_avg_ridge_l_shadow | kpif_air_transport_index | 2024-01..2026-10 (used, report only) | 0,2245 | 0,2292 | -0,0047 | 0,296 | – | 34 | 34 | 0,2668 | 0,087 |
| `v2_a_corr` (nr 53) | avg_5050 | kpif_air_transport_index | primary 2017-02..2026-10 | 0,2241 | 0,2320 | -0,0079 | 0,032 | 0,064 | 117 | 117 | 0,2806 | 0,005 |
| `v2_a_corr` (nr 53) | avg_5050 | kpif_air_transport_index | 2015-01..2026-10 | 0,2100 | 0,2165 | -0,0066 | 0,033 | – | 141 | 117 | 0,2555 | 0,007 |
| `v2_a_corr` (nr 53) | avg_5050 | kpif_air_transport_index | 2024-01..2026-10 (used, report only) | 0,2440 | 0,2461 | -0,0021 | 0,396 | – | 34 | 34 | 0,2668 | 0,155 |

## Globalt test: U1 + körning 3 (41 serier, n = 141)

| Ribba | block | n modeller | SPA lower | SPA consistent | SPA upper | White RC | E[max förb.] H0 | 90 % | observerat max | StepM 10 % väljer |
|---|---|---|---|---|---|---|---|---|---|---|
| rb_updated | 3 | 40 | 0,029 | 0,029 | 0,031 | 0,026 | 0,022 | 0,045 | 0,060 | `avg_5050`, `k0_c2`, `k2_avg_ridge_s`, `k2_avg_lasso_s`, `k2_avg_hgb_s`, `k2_avg_ens_s`, `k2_avg_ridge_l`, `k2_rb_ridge_s`, `k2_avg_ridge_lnr`, `k7_med_half`, `k7_cal_half`, `k8_fixed`, `k8_ridge`, `k8_ridge_nr`, `k8_ens_ridge`, `v2_r_corr`, `v2_a_corr`, `k2_avg_ridge_l_shadow` |
| avg_5050 | 3 | 40 | 0,019 | 0,023 | 0,024 | 0,530 | 0,023 | 0,038 | 0,021 | `k2_avg_ridge_l`, `k2_avg_ridge_lnr`, `v2_r_corr`, `k2_avg_ridge_l_shadow` |
| k2_avg_ridge_l_shadow | 3 | 40 | 0,344 | 0,625 | 0,790 | 0,945 | 0,023 | 0,041 | 0,003 | ingen |
| rb_updated | 1 | 40 | 0,005 | 0,005 | 0,005 | 0,017 | 0,021 | 0,043 | 0,060 | `avg_5050`, `j1_comb_invmse`, `k0_c2`, `k2_avg_ridge_s`, `k2_avg_lasso_s`, `k2_avg_hgb_s`, `k2_avg_ens_s`, `k2_avg_ridge_l`, `k2_rb_ridge_s`, `k2_avg_ridge_lnr`, `k7_med_half`, `k7_med_full`, `k7_cal_half`, `k7_cal_full`, `k7_k2_cal_full`, `k8_fixed`, `k8_ridge`, `k8_ridge_nr`, `k8_ens_ridge`, `v2_r_corr`, `v2_a_corr`, `k2_avg_ridge_l_shadow` |
| avg_5050 | 1 | 40 | 0,025 | 0,031 | 0,037 | 0,454 | 0,020 | 0,034 | 0,021 | `k2_avg_ridge_l`, `k2_avg_ridge_lnr`, `v2_r_corr`, `k2_avg_ridge_l_shadow` |
| k2_avg_ridge_l_shadow | 1 | 40 | 0,387 | 0,679 | 0,859 | 0,960 | 0,020 | 0,035 | 0,003 | ingen |
| rb_updated | 6 | 40 | 0,072 | 0,075 | 0,082 | 0,047 | 0,024 | 0,049 | 0,060 | `k2_avg_ridge_lnr`, `v2_r_corr` |
| avg_5050 | 6 | 40 | 0,038 | 0,046 | 0,049 | 0,553 | 0,024 | 0,041 | 0,021 | `k2_avg_ridge_l`, `k2_avg_ridge_lnr`, `v2_r_corr`, `k2_avg_ridge_l_shadow` |
| k2_avg_ridge_l_shadow | 6 | 40 | 0,259 | 0,514 | 0,677 | 0,919 | 0,024 | 0,045 | 0,003 | ingen |
| rb_updated | 12 | 40 | 0,106 | 0,111 | 0,117 | 0,057 | 0,024 | 0,052 | 0,060 | ingen |
| avg_5050 | 12 | 40 | 0,079 | 0,095 | 0,099 | 0,547 | 0,024 | 0,043 | 0,021 | `v2_r_corr` |
| k2_avg_ridge_l_shadow | 12 | 40 | 0,163 | 0,381 | 0,482 | 0,903 | 0,025 | 0,050 | 0,003 | ingen |

## Per variant: kriterierna (avsnitt 5)

| Variant | Holm p | justerat p mot egen bas (block 3) | block 1 | block 6 | block 12 | MAE 2024–26 | bas-MAE 2024–26 | MCS p T_max | MCS p T_R | klarade urvalsskärmen |
|---|---|---|---|---|---|---|---|---|---|---|
| `v2_r_corr` | 0,143 | 0,790 | 0,859 | 0,677 | 0,482 | 0,2245 | 0,2292 | 1,000 | 1,000 | nej |
| `v2_a_corr` | 0,064 | 0,477 | 0,620 | 0,359 | 0,315 | 0,2440 | 0,2461 | 0,684 | 0,366 | nej |

## Per modell (U1 + körning 3, block 3)

| Modell | MAE | justerat p mot rb_updated | mot 50/50 | mot skugga | MCS p (T_max) | MCS p (T_R) |
|---|---|---|---|---|---|---|
| `v2_r_corr` | 0,196 | 0,031 | 0,047 | 0,790 | 1,000 | 1,000 |
| `k2_avg_ridge_l_shadow` | 0,199 | 0,040 | 0,052 | – | 0,869 | 0,854 |
| `k2_avg_ridge_lnr` | 0,200 | 0,038 | 0,024 | 0,996 | 0,869 | 0,856 |
| `k2_avg_ridge_l` | 0,200 | 0,042 | 0,060 | 1,000 | 0,869 | 0,809 |
| `k2_avg_ens_s` | 0,202 | 0,049 | 0,200 | 0,999 | 0,837 | 0,856 |
| `k8_ens_ridge` | 0,202 | 0,050 | 0,230 | 0,999 | 0,849 | 0,856 |
| `k2_avg_hgb_s` | 0,202 | 0,062 | 0,492 | 0,999 | 0,869 | 0,856 |
| `k2_avg_ridge_s` | 0,207 | 0,065 | 0,330 | 1,000 | 0,684 | 0,499 |
| `v2_a_corr` | 0,210 | 0,055 | 0,477 | 1,000 | 0,684 | 0,366 |
| `k7_k2_cal_full` | 0,211 | 0,112 | 0,984 | 1,000 | 0,684 | 0,375 |
| `k0_c2` | 0,212 | 0,058 | 0,605 | 1,000 | 0,684 | 0,444 |
| `k2_avg_lasso_s` | 0,213 | 0,091 | 0,942 | 1,000 | 0,684 | 0,245 |
| `k2_rb_ridge_s` | 0,213 | 0,077 | 0,999 | 1,000 | 0,684 | 0,498 |
| `k8_fixed` | 0,214 | 0,085 | 0,882 | 1,000 | 0,684 | 0,245 |
| `k8_ridge_nr` | 0,215 | 0,089 | 0,716 | 1,000 | 0,684 | 0,233 |
| `k7_med_half` | 0,216 | 0,089 | 0,994 | 1,000 | 0,684 | 0,245 |
| `k7_cal_half` | 0,216 | 0,080 | 0,998 | 1,000 | 0,684 | 0,249 |
| `k8_ridge` | 0,216 | 0,101 | 0,958 | 1,000 | 0,684 | 0,183 |
| `j1_comb_invmse` | 0,216 | 0,135 | 1,000 | 1,000 | 0,684 | 0,233 |
| `avg_5050` | 0,217 | 0,101 | – | 1,000 | 0,668 | 0,157 |
| `j1_comb_ols` | 0,217 | 0,158 | 1,000 | 1,000 | 0,684 | 0,286 |
| `k7_med_full` | 0,218 | 0,121 | 1,000 | 1,000 | 0,668 | 0,192 |
| `k7_cal_full` | 0,219 | 0,120 | 1,000 | 1,000 | 0,624 | 0,233 |
| `j1_comb_ols_age` | 0,222 | 0,207 | 1,000 | 1,000 | 0,668 | 0,245 |
| `j1_hyb_energy_ea` | 0,223 | 0,391 | 1,000 | 1,000 | 0,684 | 0,499 |
| `j1_hyb_energy` | 0,226 | 0,321 | 1,000 | 1,000 | 0,684 | 0,499 |
| `j1_hyb_energy_core` | 0,228 | 0,396 | 1,000 | 1,000 | 0,684 | 0,474 |
| `k2_j2_ridge_s` | 0,230 | 0,427 | 1,000 | 1,000 | 0,624 | 0,307 |
| `j1_hyb_energy_fixed` | 0,238 | 0,687 | 1,000 | 1,000 | 0,599 | 0,438 |
| `k2_rb_hgb_s` | 0,241 | 0,604 | 1,000 | 1,000 | 0,281 | 0,245 |
| `j2_el_dev_var` | 0,243 | 0,785 | 1,000 | 1,000 | 0,319 | 0,245 |
| `j2` | 0,243 | 0,791 | 1,000 | 1,000 | 0,281 | 0,198 |
| `j4_detail_energy_easter` | 0,243 | 0,792 | 1,000 | 1,000 | 0,281 | 0,245 |
| `j4_detail_energy` | 0,243 | 0,797 | 1,000 | 1,000 | 0,281 | 0,233 |
| `j2_el_dev_se3` | 0,245 | 0,831 | 1,000 | 1,000 | 0,281 | 0,140 |
| `j2_el_trendbase` | 0,248 | 0,877 | 1,000 | 1,000 | 0,281 | 0,157 |
| `j3_combo` | 0,255 | 0,941 | 1,000 | 1,000 | 0,281 | 0,245 |
| `rb_updated` | 0,256 | – | 1,000 | 1,000 | 0,281 | 0,245 |
| `k0_c1` | 0,256 | 0,953 | 1,000 | 1,000 | 0,281 | 0,245 |
| `j2_el_raw` | 0,279 | 0,999 | 1,000 | 1,000 | 0,011 | 0,007 |
| `j4_detail_base` | 0,335 | 1,000 | 1,000 | 1,000 | 0,000 | 0,000 |

Identiska serier (räknas en gång): `j2_el_dev` = `j2`, `j1_comb_equal` = `avg_5050`.

Utan full täckning (inte med): `comp_fuel_el`.

Körlogg: `20261123T143421Z_v2_screen.csv` (p för screeningraderna är mot den egna basen).
