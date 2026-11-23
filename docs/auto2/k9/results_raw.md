# K9 rådata (genererad av k9_horizon.py)

## Referenser per horisont, mål 2015-01..2026-10

| h | n | eff. n (n/h) | Riksbanken | 2 % | naiv | RB vs 2 %: diff, p tvåsidig | 2024–26: n, RB / 2 % / naiv |
|---|---|---|---|---|---|---|---|
| 3 | 139 | 46.3 | 0.489 | 1.368 | 0.668 | -0.878, 0.00 | 34, 0.391 / 0.621 / 0.603 |
| 6 | 136 | 22.7 | 0.814 | 1.371 | 1.104 | -0.557, 0.05 | 34, 0.511 / 0.621 / 1.074 |
| 12 | 130 | 10.8 | 1.388 | 1.385 | 1.885 | +0.002, 0.98 | 34, 0.619 / 0.621 / 2.206 |

## Varianter, mål 2015-01..2026-10 (förregistrerat)

| Variant | h | n | eff. n | aktiva | MAE | RB | diff | p ensidig rå | Holm p | 2 %: diff, p | naiv: diff, p | 2024–26 MAE / RB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `k9_ridge_h3` | 3 | 139 | 46.3 | 101 | 0.471 | 0.489 | -0.019 | 0.325 | 1.000 | -0.897, 0.00 | -0.198, 0.01 | 0.386 / 0.391 |
| `k9_ridge_h12` | 12 | 130 | 10.8 | 83 | 1.945 | 1.388 | +0.558 | 0.966 | 1.000 | +0.560, 0.03 | +0.060, 0.86 | 1.552 / 0.619 |
| `k9_shrink_h12` | 12 | 130 | 10.8 | 95 | 1.485 | 1.388 | +0.097 | 0.897 | 1.000 | +0.100, 0.16 | -0.400, 0.35 | 0.621 / 0.619 |
| `k9_miss_h6` | 6 | 136 | 22.7 | 107 | 0.833 | 0.814 | +0.020 | 0.681 | 1.000 | -0.537, 0.06 | -0.271, 0.11 | 0.671 / 0.511 |

## Bara aktiva månader (varianten skild från RB), mål 2015-01..2026-10

| Variant | n aktiva | eff. n | MAE | RB | diff | p ensidig |
|---|---|---|---|---|---|---|
| `k9_ridge_h3` | 101 | 33.7 | 0.569 | 0.595 | -0.026 | 0.326 |
| `k9_ridge_h12` | 83 | 6.9 | 2.845 | 1.971 | +0.874 | 0.972 |
| `k9_shrink_h12` | 95 | 7.9 | 1.887 | 1.753 | +0.133 | 0.896 |
| `k9_miss_h6` | 107 | 17.8 | 0.969 | 0.944 | +0.025 | 0.679 |

## Skattade parametrar (över ursprung där varianten är aktiv)

- `k9_ridge_h3`: alpha median 1e+03, min 10, max 3e+03, senaste 1e+03 (första aktiva ursprung 2018-03)
- `k9_ridge_h12`: alpha median 1e+03, min 0.1, max 3e+03, senaste 3e+03 (första aktiva ursprung 2018-12)
- `k9_shrink_h12`: w median 0.0346, min 0, max 1, senaste 0.108 (första aktiva ursprung 2017-12)
- `k9_miss_h6`: phi median 1.01, min 0.18, max 2.39, senaste 1.73 (första aktiva ursprung 2017-06)

`k9_ridge_h3` senaste anpassning (ursprung 2026-10, alpha 1000, intercept +0.178), standardiserade koefficienter: rb_miss +0.037, ppi_since +0.036, gvb2_since +0.026, brent_since +0.024, ea_since +0.023, ki_retail_since +0.016, gap0 +0.014, ki_services_since +0.013, rate_since -0.012, kix_since +0.010, rb_gap +0.009, age +0.002

`k9_ridge_h12` senaste anpassning (ursprung 2026-10, alpha 3000, intercept +0.879), standardiserade koefficienter: ki_retail_since +0.034, ea_since +0.032, ppi_since +0.029, rb_miss +0.021, ki_services_since +0.021, gvb2_since +0.020, brent_since +0.019, gap0 +0.015, kix_since +0.014, rb_gap -0.011, rate_since +0.003, age +0.002

## Diff mot RB per målår (MAE)

|   target |   k9_ridge_h3 |   k9_ridge_h12 |   k9_shrink_h12 |   k9_miss_h6 |
|---------:|--------------:|---------------:|----------------:|-------------:|
|     2015 |         0     |        nan     |         nan     |        0     |
|     2016 |         0     |          0     |           0     |        0     |
|     2017 |         0     |          0     |           0     |       -0.021 |
|     2018 |         0.009 |          0     |          -0.002 |        0.068 |
|     2019 |         0.014 |          0.101 |           0.068 |       -0.017 |
|     2020 |        -0.012 |          0.374 |           0.235 |       -0.137 |
|     2021 |         0.084 |          0.168 |          -0.006 |       -0.045 |
|     2022 |        -0.52  |          0.212 |          -0.112 |       -0.263 |
|     2023 |         0.223 |          2.544 |           0.867 |        0.184 |
|     2024 |         0.048 |          2.241 |          -0.038 |        0.062 |
|     2025 |        -0.096 |         -0.434 |          -0.173 |       -0.003 |
|     2026 |         0.042 |          1.004 |           0.261 |        0.471 |
