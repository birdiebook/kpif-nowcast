# Varianter (global logg)

Globalt tak 50, högst 10 per jobb. En variant är förbrukad när förregistreringen är committad.
J3:s screening räknas inte.

| # total | Jobb | Variant | Förregistrerad (SHA) | MAE 2015–26 | n | DM-p (rå) | Holm-p | Run-id |
|---|---|---|---|---|---|---|---|---|
| 1–5 | J2 | V1 j2_el_raw, V2 j2_el_dev, V3 j2_el_trendbase, V4 j2_el_dev_var (revised), V5 j2_el_dev_se3 | 450a18e | | | | | |
| (resultat 1–5) | J2 | V1 0,279 · V2 0,243 · V3 0,248 · V4 0,243 · V5 0,245 vs comp_fuel 0,316 | 450a18e | se rad | 141 | 0,039 · 0,003 · 0,009 · 0,005 · 0,004 | 0,039 · 0,014 · 0,018 · 0,015 · 0,015 | 20261122T220640Z_j2_el |
| 6–13 | J1 | C1 equal, C2 invmse, C3 ols, C4 ols_age, H1 energy_fixed, H2 energy, H3 energy_core, H4 energy_ea | 9c2f5a3 | | | | | |
| (resultat 6–13) | J1 | C1 0,217 · C2 0,216 · C3 0,217 · C4 0,222 · H1 0,238 · H2 0,226 · H3 0,228 · H4 0,222 vs rb_updated 0,256 | 9c2f5a3 | se rad | 141 | ensidigt 0,015 · 0,020 · 0,023 · 0,034 · 0,216 · 0,065 · 0,089 · 0,080 | 0,117 · 0,139 · 0,139 · 0,172 · 0,261 · 0,261 · 0,261 · 0,261 | 20261122T221013Z_j1_hybrid |
| 14 | J3 | kombination ea_flash_goods+ea_flash_food+ki_services (ingen överlevde BH) | 32694a6 | 0,279 (vs 0,281, 2017–26) | 117 | ensidigt 0,43 | 0,43 (en test) | 20261122T221405Z_j3_screen |
| 15–17 | J4 | D1 detail_base, D2 detail_energy, D3 detail_energy_easter (TAB6613 revised) | 6ecd5cf | | | | | |
| (resultat 15–17) | J4 | D1 0,335 · D2 0,243 · D3 0,243 vs comp_fuel 0,316 | 6ecd5cf | se rad | 141 | 0,078 · 0,003 · 0,003 | 0,078 · 0,010 · 0,010 | 20261122T222015Z_j4_detail |
| 18–23 | J5 | U1 abs_all, U2 abs_36, U3 signed_all, U4 ewma, U5 scaled_energy, U6 qreg_energy | 767f2e4 | | | | | |
| (resultat 18–23) | J5 | träff 50/80/90: U1 40/62/77 · U2 49/77/89 · U3 40/63/73 · U4 52/80/89 · U5 40/68/76 · U6 35/63/77 | se rad | pinball U4 0,085 | 142 | – | – | 20261122 j5_intervals |

**Löpande total: 23/50**


## Körning 2 (tak 30)
| # | Spår | Varianter | SHA | Resultat |
|---|---|---|---|---|
| 24–31 | K2 | k2_avg_ridge_s, k2_avg_lasso_s, k2_avg_hgb_s, k2_avg_ens_s, k2_avg_ridge_l, k2_rb_ridge_s, k2_j2_ridge_s, k2_rb_hgb_s (förreg. 3964396) | 4ef395e | se docs/auto2/k2/resultat.md |
| 32 | K2 | k2_avg_ridge_lnr (diagnostik, tillagd efter resultat, utanför Holm) | 4ef395e | 0,199 |
| 33–34 | K0 | K0-C1 (på rb_updated), K0-C2 (på 50/50) | afa36e7 | 0,281 vs 0,281; 0,226 vs 0,232 (Holm 0,097) |

**Löpande total: 34 (körning 2: 11/30)**
