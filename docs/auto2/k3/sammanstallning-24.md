# Förklarade prognoser: 2024-11..2026-11

Genererad av `python -m kpif_nowcast.explain --docs`. Skarpa modellens prognos (component_fuel_el_v1) rekonstruerad med dagens data; fel = prognos − utfall.

## Huvudbudskap

- **24 månader med utfall:** MAE 0,393 pe, medelfel +0,048 pe (skuggor samma månader: J2 V2 0,276, 50/50 0,266). Använd period, bara rapport.
- **Felet per komponent (genomsnittligt absolut, pe):** energi 0,251, tjänster 0,203, varor 0,105, livsmedel 0,090, kapitalstock 0,013.
- **J5-bandets träffsäkerhet:** utfallet inom 50 %-bandet 42 %, 80 % 79 %, 90 % 92 % av månaderna (n = 24; litet urval, osäkert).
- **Senaste prognosen (2026-11):** KPIF november 2026: prognos 2,1 % (upp från 1,1 % i oktober; 2,05 med två decimaler, månadsförändring +0,67 %).

## Månad för månad (pe i årstakt)

| månad   |   prognos |   förra utfallet | huvuddrivare    |    el |   drivmedel | 80 %-band   |   utfall |    fel | största felkälla   |   J2 V2 fel |   50/50 fel |
|:--------|----------:|-----------------:|:----------------|------:|------------:|:------------|---------:|-------:|:-------------------|------------:|------------:|
| 2024-11 |      1.89 |              1.5 | varor +0,26     |  0.42 |        0.02 | 1,3–2,5     |      1.9 |  -0.01 | livsmedel −0,04    |       -0.24 |       -0.41 |
| 2024-12 |      1.96 |              1.9 | energi +0,32    | -0.09 |       -0    | 1,4–2,5     |      1.5 |   0.46 | energi +0,35       |        0.03 |        0.18 |
| 2025-01 |      0.97 |              1.5 | energi −0,47    |  0.05 |        0.12 | 0,4–1,5     |      2.2 |  -1.23 | energi −0,54       |       -0.82 |       -0.78 |
| 2025-02 |      2.47 |              2.2 | energi +0,16    |  0.16 |       -0.12 | 1,7–3,2     |      2.9 |  -0.43 | energi −0,28       |       -0.23 |       -0.26 |
| 2025-03 |      2.79 |              2.9 | energi −0,44    | -0.29 |       -0.16 | 2,1–3,5     |      2.3 |   0.49 | tjänster +0,20     |        0.47 |        0.26 |
| 2025-04 |      1.96 |              2.3 | energi −0,37    | -0.09 |       -0.12 | 1,2–2,7     |      2.3 |  -0.34 | energi −0,21       |       -0.16 |       -0.11 |
| 2025-05 |      2.37 |              2.3 | tjänster −0,36  |  0.04 |       -0.11 | 1,7–3,0     |      2.3 |   0.07 | tjänster +0,29     |        0.17 |        0.07 |
| 2025-06 |      2.71 |              2.3 | tjänster +0,18  | -0.18 |        0.13 | 2,0–3,3     |      2.8 |  -0.09 | tjänster −0,45     |       -0.3  |       -0.35 |
| 2025-07 |      2.77 |              2.8 | tjänster −0,10  |  0.11 |       -0.02 | 2,1–3,4     |      3   |  -0.23 | energi −0,30       |       -0.05 |       -0.07 |
| 2025-08 |      3.82 |              3   | energi +0,67    |  0.15 |       -0.05 | 3,2–4,4     |      3.3 |   0.52 | tjänster +0,35     |        0.2  |        0.06 |
| 2025-09 |      3.4  |              3.3 | energi +0,21    |  0.02 |       -0.04 | 2,8–4,0     |      3.1 |   0.3  | varor +0,22        |        0.31 |        0.13 |
| 2025-10 |      2.77 |              3.1 | energi −0,38    |  0.07 |       -0.06 | 2,2–3,3     |      3.1 |  -0.33 | energi −0,30       |        0.06 |       -0.16 |
| 2025-11 |      2.93 |              3.1 | energi −0,17    |  0.07 |       -0    | 2,3–3,5     |      2.3 |   0.63 | tjänster +0,34     |        0.3  |        0.27 |
| 2025-12 |      2.67 |              2.3 | energi +0,29    | -0.16 |       -0.05 | 2,1–3,3     |      2.1 |   0.57 | energi +0,43       |        0.16 |        0.31 |
| 2026-01 |      1.67 |              2.1 | varor −0,27     |  0.5  |        0.04 | 1,0–2,3     |      2   |  -0.33 | energi −0,53       |        0.11 |       -0.38 |
| 2026-02 |      1.63 |              2   | livsmedel −0,13 |  0.01 |        0.08 | 1,0–2,2     |      1.7 |  -0.07 | energi −0,14       |       -0.03 |       -0.04 |
| 2026-03 |      2.51 |              1.7 | energi +0,62    | -0.42 |        0.52 | 1,9–3,1     |      1.6 |   0.91 | energi +0,52       |        0.6  |        0.51 |
| 2026-04 |      1.55 |              1.6 | energi +0,19    | -0.07 |        0.16 | 0,9–2,2     |      0.8 |   0.75 | livsmedel +0,75    |        0.82 |        0.56 |
| 2026-05 |      0.81 |              0.8 | tjänster +0,16  |  0.21 |       -0.06 | 0,1–1,5     |      1.5 |  -0.69 | tjänster −0,40     |       -0.62 |       -0.64 |
| 2026-06 |      1.16 |              1.5 | tjänster −0,39  |  0.03 |       -0.2  | 0,4–1,9     |      1.3 |  -0.14 | tjänster −0,51     |       -0.13 |       -0.09 |
| 2026-07 |      0.62 |              1.3 | energi −0,51    | -0.21 |       -0.06 | −0,1–1,3    |      0.7 |  -0.08 | energi +0,28       |        0.05 |       -0.06 |
| 2026-08 |      1.1  |              0.7 | tjänster +0,29  |  0.07 |        0.11 | 0,4–1,7     |      0.7 |   0.4  | tjänster +0,35     |        0.03 |        0.06 |
| 2026-09 |      1.35 |              0.7 | energi +0,66    |  0.25 |        0.27 | 0,7–2,0     |      1.5 |  -0.15 | varor −0,09        |       -0.27 |       -0.13 |
| 2026-10 |      1.28 |              1.5 | livsmedel −0,13 |  0.07 |        0.13 | 0,7–1,9     |      1.1 |   0.18 | tjänster +0,17     |        0.45 |        0.5  |
| 2026-11 |      2.05 |              1.1 | energi +0,87    |  0.91 |       -0.32 | 1,5–2,6     |    nan   | nan    | nan                |      nan    |      nan    |

Per månad: `outputs/explain/<månad>.json` och `.md` (committas inte); exempel i `docs/auto2/k3/exempel-2026-11.json` och `docs/auto2/k3/forklaring-2026-11.md`.
