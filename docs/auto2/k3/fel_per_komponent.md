# Prognosfel per komponent 2015–2026

Genererad av `python -m kpif_nowcast.explain --docs` (2015-01..2026-10, n = 142).
Fel = prognos − utfall i årstakt (pe), positivt = för hög prognos. Felet delas exakt upp per komponent: k · (prognos för komponentens bidrag − SCB:s bidrag), k = index(t−1)/index(t−12). "Avrundning" är SCB:s avrundning av bidragen och av den officiella årstakten (0,1).

Modell: J2 V2 (`j2_el_dev`), den enda komponentmodellen med el över hela perioden. Tjänster, varor, livsmedel och kapitalstock prognostiseras identiskt i alla tre komponentmodellerna (säsong + 12-månaderstrend), så de kolumnerna gäller även den skarpa modellen. Bara energi skiljer (tabell 4).

## Sammanfattning

- **Andel av kvadratfelet (MSE) 2015–2026:** tjänster 37 %, energi 21 %, varor 20 %, livsmedel 20 %, kapitalstock 1 %. Andelen är medel(e_c · e)/medel(e²) och summerar till 100 % med avrundningen; en komponent vars fel tar ut andra komponenters fel kan få negativ andel.
- **Över tid:** största felkällan per period: 2015–2019 tjänster (49 %); 2020–2021 tjänster (53 %); 2022–2023 energi (27 %); 2024–2026 tjänster (34 %).
- **MAE totalt per period:** 2015–2019 0,164 (n = 60); 2020–2021 0,258 (n = 24); 2022–2023 0,409 (n = 24); 2024–2026 0,252 (n = 34); 2015–2026 0,242 (n = 142).
- **Energi i den skarpa modellen:** genomsnittligt absolut energifel 2024–2026 0,242 pe mot J2 V2 0,128 och bara drivmedel 0,340 (n = 34, använd period).

## 1. Andel av kvadratfelet per period (%)

|           |   energi |   tjänster |   varor |   livsmedel |   kapitalstock |   avrundning |
|:----------|---------:|-----------:|--------:|------------:|---------------:|-------------:|
| 2015–2019 |       20 |         49 |      19 |          12 |             -0 |            0 |
| 2020–2021 |       18 |         53 |      14 |          10 |              1 |            4 |
| 2022–2023 |       27 |         23 |      27 |          22 |              0 |            1 |
| 2024–2026 |       16 |         34 |      17 |          29 |              4 |           -1 |
| 2015–2026 |       21 |         37 |      20 |          20 |              1 |            1 |

## 2. Genomsnittligt absolut fel per komponent och period (pe i årstakt)

|           |   n |   MAE total |   energi |   tjänster |   varor |   livsmedel |   kapitalstock |   avrundning |
|:----------|----:|------------:|---------:|-----------:|--------:|------------:|---------------:|-------------:|
| 2015–2019 |  60 |       0.164 |    0.076 |      0.129 |   0.083 |       0.058 |          0.006 |        0.025 |
| 2020–2021 |  24 |       0.258 |    0.09  |      0.154 |   0.096 |       0.062 |          0.003 |        0.024 |
| 2022–2023 |  24 |       0.409 |    0.251 |      0.202 |   0.157 |       0.135 |          0.003 |        0.027 |
| 2024–2026 |  34 |       0.252 |    0.128 |      0.196 |   0.099 |       0.086 |          0.012 |        0.027 |
| 2015–2026 | 142 |       0.242 |    0.121 |      0.162 |   0.101 |       0.078 |          0.007 |        0.026 |

## 3. Medelfel (bias) per komponent och period (pe, positivt = för hög)

|           |   total |   energi |   tjänster |   varor |   livsmedel |   kapitalstock |   avrundning |
|:----------|--------:|---------:|-----------:|--------:|------------:|---------------:|-------------:|
| 2015–2019 |  -0.006 |   -0.008 |     -0     |  -0.001 |       0     |          0.001 |        0.002 |
| 2020–2021 |  -0.001 |    0.01  |      0     |  -0.002 |      -0.001 |         -0.002 |       -0.007 |
| 2022–2023 |   0.061 |    0.056 |     -0.011 |   0.004 |       0.006 |          0.003 |        0.004 |
| 2024–2026 |   0.04  |   -0.014 |      0.023 |   0.011 |       0.025 |         -0.003 |       -0.002 |
| 2015–2026 |   0.017 |    0.005 |      0.004 |   0.002 |       0.007 |         -0     |       -0     |

## 4. Energi: genomsnittligt absolut fel i tre komponentmodeller (pe i årstakt)

|           |   J2 V2 (el_dev) |   comp_fuel (bara drivmedel) |   skarpa (el_chg, från 2023-12) |   n skarpa |
|:----------|-----------------:|-----------------------------:|--------------------------------:|-----------:|
| 2015–2019 |            0.076 |                        0.112 |                         nan     |          0 |
| 2020–2021 |            0.09  |                        0.205 |                         nan     |          0 |
| 2022–2023 |            0.251 |                        0.55  |                           0.138 |          1 |
| 2024–2026 |            0.128 |                        0.34  |                           0.242 |         34 |
| 2015–2026 |            0.121 |                        0.256 |                           0.239 |         35 |

## 5. Per år: genomsnittligt absolut fel (pe)

|   år |   n |   MAE total |   energi |   tjänster |   varor |   livsmedel |   kapitalstock |   avrundning |
|-----:|----:|------------:|---------:|-----------:|--------:|------------:|---------------:|-------------:|
| 2015 |  12 |       0.136 |    0.092 |      0.145 |   0.085 |       0.061 |          0.011 |        0.028 |
| 2016 |  12 |       0.206 |    0.11  |      0.147 |   0.095 |       0.058 |          0.003 |        0.023 |
| 2017 |  12 |       0.231 |    0.066 |      0.154 |   0.075 |       0.03  |          0.007 |        0.021 |
| 2018 |  12 |       0.138 |    0.042 |      0.092 |   0.076 |       0.061 |          0.007 |        0.025 |
| 2019 |  12 |       0.107 |    0.071 |      0.106 |   0.083 |       0.081 |          0.002 |        0.028 |
| 2020 |  12 |       0.193 |    0.095 |      0.132 |   0.095 |       0.066 |          0     |        0.021 |
| 2021 |  12 |       0.323 |    0.085 |      0.175 |   0.098 |       0.058 |          0.006 |        0.026 |
| 2022 |  12 |       0.45  |    0.253 |      0.172 |   0.163 |       0.138 |          0.002 |        0.025 |
| 2023 |  12 |       0.368 |    0.25  |      0.231 |   0.15  |       0.131 |          0.004 |        0.029 |
| 2024 |  12 |       0.185 |    0.103 |      0.153 |   0.081 |       0.07  |          0.01  |        0.032 |
| 2025 |  12 |       0.27  |    0.106 |      0.194 |   0.108 |       0.058 |          0.022 |        0.026 |
| 2026 |  10 |       0.312 |    0.186 |      0.251 |   0.109 |       0.139 |          0.004 |        0.022 |

## 6. Per år: andel av kvadratfelet (%)

|   år |   energi |   tjänster |   varor |   livsmedel |   kapitalstock |   avrundning |
|-----:|---------:|-----------:|--------:|------------:|---------------:|-------------:|
| 2015 |        4 |         40 |      44 |          17 |             -2 |           -3 |
| 2016 |       45 |         49 |      -0 |           6 |             -1 |            1 |
| 2017 |       15 |         54 |      25 |           6 |              0 |            0 |
| 2018 |       -2 |         40 |      25 |          28 |              4 |            5 |
| 2019 |        4 |         62 |      13 |          23 |             -2 |           -0 |
| 2020 |       14 |         53 |      26 |           3 |             -0 |            4 |
| 2021 |       19 |         52 |      10 |          13 |              1 |            4 |
| 2022 |       38 |         18 |      29 |          15 |              0 |            0 |
| 2023 |       10 |         32 |      23 |          33 |              1 |            2 |
| 2024 |       26 |         25 |      17 |          25 |              4 |            4 |
| 2025 |        8 |         34 |      36 |          13 |             11 |           -2 |
| 2026 |       19 |         38 |       3 |          43 |             -0 |           -2 |

Månadsdata: `outputs/explain/fel_per_komponent.csv` (committas inte).
