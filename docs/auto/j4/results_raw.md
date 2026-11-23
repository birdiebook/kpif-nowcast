## 2015-2026 (n=141)

|                         |   MAE |   RMSE |   bias |   n |   exact_hit_% |   diff_vs_comp_fuel |   dm_p_vs_comp_fuel |   holm_p |   dm_p_vs_rb_updated |
|:------------------------|------:|-------:|-------:|----:|--------------:|--------------------:|--------------------:|---------:|---------------------:|
| j4_detail_energy_easter | 0.243 |  0.314 |  0.018 | 141 |        18.44  |              -0.072 |               0.003 |    0.01  |                0.567 |
| j4_detail_energy        | 0.243 |  0.313 |  0.018 | 141 |        19.149 |              -0.072 |               0.003 |    0.01  |                0.573 |
| rb_updated              | 0.256 |  0.38  | -0.046 | 141 |        17.73  |             nan     |             nan     |  nan     |              nan     |
| comp_fuel               | 0.316 |  0.441 |  0.011 | 141 |        16.312 |             nan     |             nan     |  nan     |                0.031 |
| riksbank                | 0.32  |  0.474 | -0.066 | 141 |        17.021 |             nan     |             nan     |  nan     |                0.005 |
| j4_detail_base          | 0.335 |  0.448 |  0.005 | 141 |        12.766 |               0.019 |               0.078 |    0.078 |                0.001 |

## 2024-2026 (used) (n=34)

|                         |   MAE |   RMSE |   bias |   n |   exact_hit_% |   diff_vs_comp_fuel |   dm_p_vs_comp_fuel |   holm_p |   dm_p_vs_rb_updated |
|:------------------------|------:|-------:|-------:|----:|--------------:|--------------------:|--------------------:|---------:|---------------------:|
| j4_detail_energy        | 0.246 |  0.322 |  0.043 |  34 |        20.588 |              -0.197 |               0.001 |    0.002 |                0.645 |
| j4_detail_energy_easter | 0.256 |  0.332 |  0.043 |  34 |        17.647 |              -0.187 |               0.002 |    0.005 |                0.808 |
| rb_updated              | 0.267 |  0.357 | -0.029 |  34 |        20.588 |             nan     |             nan     |  nan     |              nan     |
| riksbank                | 0.326 |  0.402 | -0.034 |  34 |        14.706 |             nan     |             nan     |  nan     |                0.058 |
| comp_fuel               | 0.443 |  0.547 |  0.017 |  34 |         5.882 |             nan     |             nan     |  nan     |                0     |
| j4_detail_base          | 0.447 |  0.546 |  0.007 |  34 |         8.824 |               0.004 |               0.75  |    0.75  |                0     |

## Top 15 groups by share of total error variance, j4_detail_base, 2015-2026

|   coicop |   var_share_% |   MAE_pp | label                                     |
|---------:|--------------:|---------:|:------------------------------------------|
|      4.5 |        61.494 |    0.235 | ELECTRICITY, GAS AND OTHER FUELS          |
|      1.1 |         8.89  |    0.069 | FOOD                                      |
|      9.8 |         7.081 |    0.087 | PACKAGE HOLIDAYS                          |
|      7.3 |         4.202 |    0.065 | PASSENGER TRANSPORT SERVICES              |
|      4.2 |         2.738 |    0.023 | IMPUTED RENTAL PAYMENTS FOR HOUSING       |
|      7.2 |         2.44  |    0.105 | OPERATION OF PERSONAL TRANSPORT EQUIPMENT |
|      5.1 |         2.197 |    0.021 | FURNITURE, FURNISHINGS, AND LOOSE CARPETS |
|      3.1 |         1.507 |    0.058 | CLOTHING                                  |
|      8.1 |         1.499 |    0.022 | INFORMATION AND COMMUNICATION EQUIPMENT   |
|      5.2 |         1.264 |    0.014 | HOUSEHOLD TEXTILES                        |
|     13.1 |         1.258 |    0.014 | PERSONAL CARE                             |
|      1.2 |         1.144 |    0.016 | NON-ALCOHOLIC BEVERAGES                   |
|      3.2 |         0.972 |    0.011 | FOOTWEAR                                  |
|      4.1 |         0.843 |    0.009 | ACTUAL RENTAL PAYMENTS MADE FOR HOUSING   |
|      8.3 |         0.824 |    0.026 | INFORMATION AND COMMUNICATION SERVICES    |

## Top 15 groups by share of total error variance, j4_detail_energy_easter, 2015-2026

|   coicop |   var_share_% |   MAE_pp | label                                     |
|---------:|--------------:|---------:|:------------------------------------------|
|      9.8 |        18.296 |    0.086 | PACKAGE HOLIDAYS                          |
|      1.1 |        17.325 |    0.069 | FOOD                                      |
|      4.5 |        13.466 |    0.084 | ELECTRICITY, GAS AND OTHER FUELS          |
|      7.3 |         8.969 |    0.063 | PASSENGER TRANSPORT SERVICES              |
|      7.2 |         7.652 |    0.081 | OPERATION OF PERSONAL TRANSPORT EQUIPMENT |
|      3.1 |         6.139 |    0.058 | CLOTHING                                  |
|      4.2 |         3.873 |    0.023 | IMPUTED RENTAL PAYMENTS FOR HOUSING       |
|      8.1 |         3.256 |    0.022 | INFORMATION AND COMMUNICATION EQUIPMENT   |
|      1.2 |         2.26  |    0.016 | NON-ALCOHOLIC BEVERAGES                   |
|     13.1 |         2.129 |    0.014 | PERSONAL CARE                             |
|      3.2 |         1.642 |    0.011 | FOOTWEAR                                  |
|      5.1 |         1.566 |    0.021 | FURNITURE, FURNISHINGS, AND LOOSE CARPETS |
|     11.1 |         1.513 |    0.02  | FOOD AND BEVERAGE SERVING SERVICES        |
|      8.3 |         1.357 |    0.026 | INFORMATION AND COMMUNICATION SERVICES    |
|      7.1 |         1.291 |    0.012 | PURCHASE OF VEHICLES                      |

Run log: `20261122T222015Z_j4_detail.csv`
