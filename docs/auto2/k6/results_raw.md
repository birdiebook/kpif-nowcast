# K6 results (raw)

## Part 1: Swedish HICP old (ECOICOP 1) vs new (COICOP 2018), m/m %, 2001-2025

Energy groups:

|                                  |   n |   corr |   mad_pp |   max_pp |
|:---------------------------------|----:|-------:|---------:|---------:|
| TAB6613 04.5 vs HICP old CP045   | 300 | 0.9987 |   0.4145 |   3.2892 |
| HICP new CP045 vs HICP old CP045 | 300 | 1      |   0.0095 |   0.1788 |
| TAB6613 07.2 vs HICP old CP072   | 300 | 0.9963 |   0.0387 |   1.5798 |
| HICP new CP072 vs HICP old CP072 | 300 | 1      |   0.01   |   0.1258 |

Codes with 2 digits: 12, median corr 0.9989, median MAD 0.0179 pp, corr < 0.98: 3

Codes with 3 digits: 32, median corr 0.9986, median MAD 0.0206 pp, corr < 0.98: 9

Codes with 4 digits: 70, median corr 0.9997, median MAD 0.0070 pp, corr < 0.98: 17

3-digit groups (TAB6613 level 2), worst 15 by corr:

|       |   digits |   n |    corr |   mad_pp |   max_pp |
|:------|---------:|----:|--------:|---------:|---------:|
| CP092 |        3 | 300 | -0.0653 |   1.3784 |   6.7219 |
| CP081 |        3 | 300 | -0.0471 |   1.4126 |  11.368  |
| CP121 |        3 | 300 |  0.0643 |   0.5074 |   9.8839 |
| CP096 |        3 | 300 |  0.0865 |   7.3621 |  38.8011 |
| CP095 |        3 | 300 |  0.0985 |   2.7323 |  14.3437 |
| CP091 |        3 | 300 |  0.1823 |   1.1791 |   5.5811 |
| CP093 |        3 | 300 |  0.4982 |   0.6807 |   4.6561 |
| CP094 |        3 | 300 |  0.612  |   0.418  |   2.9523 |
| CP105 |        3 | 144 |  0.9088 |   0.0479 |   3.8316 |
| CP061 |        3 | 300 |  0.9923 |   0.0555 |   0.4566 |
| CP054 |        3 | 300 |  0.9932 |   0.0275 |   1.3675 |
| CP051 |        3 | 300 |  0.9946 |   0.0289 |   1.0236 |
| CP111 |        3 | 300 |  0.995  |   0.0137 |   0.2124 |
| CP012 |        3 | 300 |  0.9962 |   0.0338 |   1.0133 |
| CP032 |        3 | 300 |  0.998  |   0.0404 |   3.132  |

TAB6613: sum of 43 level-2 effects vs published KPIF m/m (1988-): {'n': 466, 'mad_pp': 0.0041920756208080985, 'max_pp': 0.014807998431689541}

## k6_fi_el_dev: FI, spot proxy SE3

HICP total new vs old dataset, m/m: {'n': 359, 'corr': np.float64(1.0), 'mad_pp': np.float64(0.0), 'max_pp': np.float64(0.0)}

## k6_dk_el_dev: DK, spot proxy SE4

HICP total new vs old dataset, m/m: {'n': 359, 'corr': np.float64(0.9942616257906257), 'mad_pp': np.float64(0.0395045782644777), 'max_pp': np.float64(0.1370798068522916)}

### k6_fi_el_dev 2015-2026

|                       |        0 |
|:----------------------|---------:|
| n                     | 142      |
| MAE_variant           |   0.2679 |
| MAE_seasonal_trend_5y |   0.2785 |
| MAE_naive_yy          |   0.3108 |
| diff_vs_ref           |  -0.0106 |
| dm_p_raw              |   0.2919 |
| holm_p                |   0.5839 |

### k6_fi_el_dev 2024-2026

|                       |       0 |
|:----------------------|--------:|
| n                     | 34      |
| MAE_variant           |  0.235  |
| MAE_seasonal_trend_5y |  0.2533 |
| MAE_naive_yy          |  0.265  |
| diff_vs_ref           | -0.0183 |
| dm_p_raw              |  0.207  |

### k6_fi_el_dev 2021-2023

|                       |       0 |
|:----------------------|--------:|
| n                     | 36      |
| MAE_variant           |  0.4713 |
| MAE_seasonal_trend_5y |  0.4728 |
| MAE_naive_yy          |  0.5667 |
| diff_vs_ref           | -0.0015 |
| dm_p_raw              |  0.9355 |

### k6_fi_el_dev 2015-2020

|                       |       0 |
|:----------------------|--------:|
| n                     | 72      |
| MAE_variant           |  0.1818 |
| MAE_seasonal_trend_5y |  0.1933 |
| MAE_naive_yy          |  0.2044 |
| diff_vs_ref           | -0.0115 |
| dm_p_raw              |  0.4877 |

Latest coefficients: {'b_fuel_chg': 1.3486, 'b_el_dev': -1.2767}; 2020-12: {'b_fuel_chg': 1.0122, 'b_el_dev': 2.192}

### k6_dk_el_dev 2015-2026

|                       |        0 |
|:----------------------|---------:|
| n                     | 142      |
| MAE_variant           |   0.3213 |
| MAE_seasonal_trend_5y |   0.3198 |
| MAE_naive_yy          |   0.3657 |
| diff_vs_ref           |   0.0015 |
| dm_p_raw              |   0.8553 |
| holm_p                |   0.8553 |

### k6_dk_el_dev 2024-2026

|                       |       0 |
|:----------------------|--------:|
| n                     | 34      |
| MAE_variant           |  0.2954 |
| MAE_seasonal_trend_5y |  0.2818 |
| MAE_naive_yy          |  0.3498 |
| diff_vs_ref           |  0.0136 |
| dm_p_raw              |  0.3231 |

### k6_dk_el_dev 2021-2023

|                       |       0 |
|:----------------------|--------:|
| n                     | 36      |
| MAE_variant           |  0.5617 |
| MAE_seasonal_trend_5y |  0.5356 |
| MAE_naive_yy          |  0.7295 |
| diff_vs_ref           |  0.0262 |
| dm_p_raw              |  0.1331 |

### k6_dk_el_dev 2015-2020

|                       |       0 |
|:----------------------|--------:|
| n                     | 72      |
| MAE_variant           |  0.2132 |
| MAE_seasonal_trend_5y |  0.2299 |
| MAE_naive_yy          |  0.1912 |
| diff_vs_ref           | -0.0166 |
| dm_p_raw              |  0.087  |

Latest coefficients: {'b_fuel_chg': 0.7706, 'b_el_dev': -2.2025}; 2020-12: {'b_fuel_chg': 0.623, 'b_el_dev': 4.6127}

Run log: `20261123T091208Z_k6_nordic.csv` (column dm_p_vs_rb_updated holds DM p vs seasonal_trend_5y here)
