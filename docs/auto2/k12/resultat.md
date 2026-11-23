# K12 Globalt test över alla modellvarianter: resultat

Genererad av `python -m kpif_nowcast.k12_global` (kod @ 5f91077). Inga nya varianter (0 förbrukade). Bootstrap B = 9999, stationär bootstrap, medelblocklängd 3 månader, seed 20261123. Förlust = absolutfel (MAE). Allt är urvalsevidens på samma urval som modellerna valdes på.

## Dom

**Den bästa håller även globalt, men marginalen mot 50/50 är liten.** `k2_avg_ridge_l` är bättre än både rb_updated och 50/50 även när alla 35 varianter räknas: SPA p = 0,035 mot rb_updated och 0,025 mot 50/50 (högst 0,083 resp. 0,050 för blocklängd 3–6), och Romano–Wolf StepM (10 %) pekar ut den mot båda ribborna (justerat p 0,038 resp. 0,042).

- Urval: 2015-01..2026-10, gemensamt för alla serier, **n = 141**. 35 registrerade h=1-varianter + referenserna rb_updated, 50/50 och J2 V2 (U1), plus 5 fas 2–4-modeller (U2).
- Bästa variant: `k2_avg_ridge_l`, MAE 0,199 mot rb_updated 0,256 och 50/50 0,217. Den skiljer sig från 50/50 i 105 av 141 månader (K2 = 50/50 före 2018-02).
- **Urvalsbias i pe MAE.** Om alla 37 modeller vore exakt lika bra som ribban skulle den bästa ändå se ut att vinna med i snitt 0,022 pe mot rb_updated (90 %-kvantil 0,045) och 0,022 pe mot 50/50 (90 % 0,038). Observerat bästa: 0,057 resp. 0,018. Grovt biasjusterat: ≈ 0,035 pe mot rb_updated, ≈ -0,005 pe mot 50/50.
- **Varför SPA ändå kan godkänna mot 50/50 när den råa vinsten ligger inom brusbandet:** maximum av råa vinster domineras av modeller som skiljer sig mycket från ribban och därför har stort brus (White RC p = 0,624). SPA studentiserar: `k2_avg_ridge_l` är 50/50 plus en liten, stabil korrektion, så dess vinst är liten men ovanligt säker. Studentiserat är bästa t under H0 i snitt 1,78 (90 % 2,55), observerat 3,09. Mot rb_updated: 1,20 (90 % 2,23), observerat 2,70.
- **Model Confidence Set (90 %, T_max)** innehåller 36 av 38 modeller; rb_updated ingår, 50/50 ingår. Utanför: `j2_el_raw`, `j4_detail_base`. MCS jämför varje modell med *snittet* av mängden och har låg styrka med n = 141 och så här korrelerade modeller. Den säger att datan inte räcker för att rangordna de flesta, inte att de är lika bra. StepM besvarar den skarpare frågan "vilka slår ribban".
- Förbehåll: K2b fann att ea_news läckte i tre månader (flashdatum); med K2b:s rättelse är `k2_avg_ridge_l` 0,200. Rättelsen är inte med här (koden på main används). Allt gäller samma urval som modellerna valdes på; det ersätter inte ett utfall utanför urvalet. Skuggprognoserna från 2026-12 är det riktiga testet.

## Globala test (U1, primär blocklängd)

| Ribba | n modeller | SPA lower | SPA consistent | SPA upper | White RC | E[max förbättring] H0 | 90 % | observerat max | StepM 10 % väljer |
|---|---|---|---|---|---|---|---|---|---|
| rb_updated | 37 | 0,034 | 0,035 | 0,038 | 0,035 | 0,022 | 0,045 | 0,057 | `avg_5050`, `k0_c2`, `k2_avg_ridge_s`, `k2_avg_lasso_s`, `k2_avg_hgb_s`, `k2_avg_ens_s`, `k2_avg_ridge_l`, `k2_rb_ridge_s`, `k2_avg_ridge_lnr`, `k7_med_half`, `k7_cal_half`, `k8_fixed`, `k8_ridge`, `k8_ridge_nr`, `k8_ens_ridge` |
| avg_5050 | 37 | 0,020 | 0,025 | 0,026 | 0,624 | 0,022 | 0,038 | 0,018 | `k2_avg_ridge_l`, `k2_avg_ridge_lnr` |

SPA: H0 = ingen modell har lägre förväntad MAE än ribban. *consistent* är Hansens rekommenderade p; *lower*/*upper* ger gränser. White RC = ostudentiserad, övre recentrering. StepM = Romano–Wolf steg-ned, familjevis felrisk 10 % över hela universum.

## Känslighet

| Universum / blocklängd | Ribba | SPA consistent | White RC | E[max] H0 | `k2_avg_ridge_l` justerat p | 90 %-MCS (antal) |
|---|---|---|---|---|---|---|
| U1 registrerade varianter + referenser, block 3 | rb_updated | 0,035 | 0,035 | 0,022 | 0,038 | 36 |
| U1 registrerade varianter + referenser, block 3 | avg_5050 | 0,025 | 0,624 | 0,022 | 0,042 | 36 |
| U2 U1 + fas 2–4-modeller, block 3 | rb_updated | 0,035 | 0,065 | 0,030 | 0,043 | 36 |
| U2 U1 + fas 2–4-modeller, block 3 | avg_5050 | 0,025 | 0,759 | 0,030 | 0,043 | 36 |
| U1, block 1 | rb_updated | 0,008 | 0,026 | 0,021 | 0,009 | 36 |
| U1, block 1 | avg_5050 | 0,032 | 0,576 | 0,020 | 0,056 | 36 |
| U1, block 6 | rb_updated | 0,083 | 0,059 | 0,023 | 0,091 | 36 |
| U1, block 6 | avg_5050 | 0,050 | 0,637 | 0,024 | 0,058 | 36 |
| U1, block 12 | rb_updated | 0,121 | 0,070 | 0,024 | 0,128 | 36 |
| U1, block 12 | avg_5050 | 0,093 | 0,630 | 0,024 | 0,098 | 36 |

Blocklängd: Politis–White-skattning (median över förlustdifferenserna) = 1,0 mot rb_updated, 1,0 mot 50/50; avrundad och begränsad till 3–6 månader (Riksbankens prognosomgång lever 2–4 månader, så felen är korrelerade inom en omgång). 1 och 12 visas som ytterlägen.

## Per modell (U1, primär blocklängd)

| Modell | Spår | MAE | diff mot rb_updated | DM p ensidig (rå) | max-t justerat p mot rb_updated | justerat p mot 50/50 | MCS p (T_max) | MCS p (T_R) |
|---|---|---|---|---|---|---|---|---|
| `k2_avg_ridge_l` | K2 | 0,199 | -0,057 | 0,004 | 0,038 | 0,042 | 1,000 | 1,000 |
| `k2_avg_ridge_lnr` | K2 | 0,199 | -0,056 | 0,004 | 0,038 | 0,026 | 0,932 | 0,993 |
| `k2_avg_ens_s` | K2 | 0,201 | -0,055 | 0,005 | 0,045 | 0,135 | 0,932 | 0,993 |
| `k8_ens_ridge` | K8 | 0,201 | -0,055 | 0,005 | 0,047 | 0,157 | 0,932 | 0,993 |
| `k2_avg_hgb_s` | K2 | 0,201 | -0,054 | 0,006 | 0,054 | 0,366 | 0,932 | 0,993 |
| `k2_avg_ridge_s` | K2 | 0,206 | -0,049 | 0,008 | 0,062 | 0,211 | 0,801 | 0,466 |
| `k7_k2_cal_full` | K7 | 0,210 | -0,045 | 0,016 | 0,107 | 0,960 | 0,801 | 0,332 |
| `k0_c2` | K0 | 0,212 | -0,044 | 0,008 | 0,058 | 0,576 | 0,801 | 0,463 |
| `k2_avg_lasso_s` | K2 | 0,212 | -0,043 | 0,011 | 0,083 | 0,923 | 0,801 | 0,239 |
| `k2_rb_ridge_s` | K2 | 0,213 | -0,043 | 0,010 | 0,074 | 0,997 | 0,801 | 0,466 |
| `k8_fixed` | K8 | 0,214 | -0,041 | 0,012 | 0,085 | 0,860 | 0,801 | 0,239 |
| `k8_ridge_nr` | K8 | 0,215 | -0,041 | 0,013 | 0,089 | 0,688 | 0,801 | 0,222 |
| `k7_med_half` | K7 | 0,216 | -0,040 | 0,013 | 0,089 | 0,990 | 0,801 | 0,239 |
| `k7_cal_half` | K7 | 0,216 | -0,040 | 0,011 | 0,079 | 0,996 | 0,801 | 0,241 |
| `k8_ridge` | K8 | 0,216 | -0,040 | 0,015 | 0,101 | 0,947 | 0,801 | 0,191 |
| `j1_comb_invmse` | J1 | 0,216 | -0,039 | 0,020 | 0,134 | 1,000 | 0,801 | 0,222 |
| `avg_5050` | ref | 0,217 | -0,039 | 0,015 | 0,101 | – | 0,801 | 0,167 |
| `j1_comb_ols` | J1 | 0,217 | -0,038 | 0,023 | 0,156 | 1,000 | 0,801 | 0,258 |
| `k7_med_full` | K7 | 0,218 | -0,038 | 0,018 | 0,119 | 1,000 | 0,801 | 0,191 |
| `k7_cal_full` | K7 | 0,219 | -0,036 | 0,018 | 0,118 | 1,000 | 0,786 | 0,210 |
| `j1_hyb_energy_ea` | J1 | 0,222 | -0,033 | 0,080 | 0,375 | 1,000 | 0,801 | 0,527 |
| `j1_comb_ols_age` | J1 | 0,222 | -0,033 | 0,034 | 0,205 | 1,000 | 0,801 | 0,241 |
| `j1_hyb_energy` | J1 | 0,226 | -0,030 | 0,065 | 0,315 | 1,000 | 0,801 | 0,466 |
| `k2_j2_ridge_s` | K2 | 0,227 | -0,029 | 0,068 | 0,360 | 1,000 | 0,801 | 0,412 |
| `j1_hyb_energy_core` | J1 | 0,228 | -0,027 | 0,089 | 0,393 | 1,000 | 0,801 | 0,466 |
| `j1_hyb_energy_fixed` | J1 | 0,238 | -0,017 | 0,216 | 0,681 | 1,000 | 0,590 | 0,422 |
| `k2_rb_hgb_s` | K2 | 0,241 | -0,015 | 0,170 | 0,605 | 1,000 | 0,307 | 0,207 |
| `j2_el_dev_var` | J2 | 0,243 | -0,013 | 0,278 | 0,779 | 1,000 | 0,324 | 0,239 |
| `j2` | ref | 0,243 | -0,013 | 0,282 | 0,786 | 1,000 | 0,307 | 0,179 |
| `j4_detail_energy_easter` | J4 | 0,243 | -0,012 | 0,283 | 0,788 | 1,000 | 0,307 | 0,210 |
| `j4_detail_energy` | J4 | 0,243 | -0,012 | 0,287 | 0,792 | 1,000 | 0,307 | 0,207 |
| `j2_el_dev_se3` | J2 | 0,245 | -0,010 | 0,315 | 0,824 | 1,000 | 0,307 | 0,116 |
| `j2_el_trendbase` | J2 | 0,248 | -0,008 | 0,370 | 0,874 | 1,000 | 0,307 | 0,133 |
| `j3_combo` | J3 | 0,254 | -0,001 | 0,431 | 0,912 | 1,000 | 0,307 | 0,241 |
| `rb_updated` | ref | 0,256 | 0,000 | – | – | 1,000 | 0,307 | 0,239 |
| `k0_c1` | K0 | 0,256 | 0,000 | 0,505 | 0,951 | 1,000 | 0,307 | 0,239 |
| `j2_el_raw` | J2 | 0,279 | 0,023 | 0,841 | 0,999 | 1,000 | 0,014 | 0,008 |
| `j4_detail_base` | J4 | 0,335 | 0,079 | 1,000 | 1,000 | 1,000 | 0,000 | 0,001 |

Justerat p = andel bootstrapdragningar där den största studentiserade förbättringen bland *alla* modeller (under H0) är minst modellens egen (enstegs max-t, konservativ). MCS p ≥ 0,10 = i 90 %-MCS.

## Inventering

| Familj | Status |
|---|---|
| refs | beräknad |
| phase | beräknad |
| j1 | beräknad |
| j2 | beräknad |
| j3 | beräknad |
| j4 | beräknad |
| k0 | beräknad |
| k2 | beräknad |
| k7 | beräknad |
| k8 | beräknad |

Identiska serier (räknas en gång): `j2_el_dev` = `j2`, `j1_comb_equal` = `avg_5050`.

Utan full täckning på urvalet (inte med): `comp_fuel_el`.

Inte med, med orsak:

- J5 (U1–U6): intervallmetoder runt comp_fuel, ingen egen punktprognos.
- K6 (N1, N2): prognoser för Finlands och Danmarks HIKP, inte KPIF.
- K9 (4 varianter): horisont 3–12 månader, annat mål och överlappande fel.
- J3/K0-screeningarna (45 + 29 serier): räknades inte mot taket och ingår inte; kombinationerna (`j3_combo`, `k0_c1`, `k0_c2`) ingår. Om screeningarna räknades skulle urvalsbiasen bli större, inte mindre.
- K1, K3, K4: inga modellvarianter.
- K2b: inga nya varianter. K2b:s rättelse av flashdatumen (ea_news) ändrar K2-varianterna marginellt (0,199 → 0,200); här används koden på main.
- K8 tas med automatiskt när `k8_food` finns på main (samma kod som K8:s main).

## Reproduktionskontroll (MAE här mot körloggen)

Egen MAE räknas på det gemensamma urvalet; loggens på spårets eget urval (kan skilja en månad).

| Modell | MAE här | MAE logg | n logg | körning |
|---|---|---|---|---|
| `k2_avg_ridge_l` | 0,199 | 0,199 | 141 | 20261123T083753Z_k2_ml |
| `k2_avg_ridge_lnr` | 0,199 | 0,199 | 141 | 20261123T083943Z_k2_ml_posthoc |
| `k2_avg_ens_s` | 0,201 | 0,194 | 134 | 20261123T100622Z_k13_tax |
| `k8_ens_ridge` | 0,201 | 0,201 | 141 | 20261123T093910Z_k8_food |
| `k2_avg_hgb_s` | 0,201 | 0,201 | 141 | 20261123T083753Z_k2_ml |
| `k2_avg_ridge_s` | 0,206 | 0,206 | 141 | 20261123T083753Z_k2_ml |
| `k7_k2_cal_full` | 0,210 | 0,210 | 141 | 20261123T093401Z_k7_services |
| `k0_c2` | 0,212 | 0,212 | 141 | 20261123T084148Z_k0_screen |
| `k2_avg_lasso_s` | 0,212 | 0,212 | 141 | 20261123T083753Z_k2_ml |
| `k2_rb_ridge_s` | 0,213 | 0,213 | 141 | 20261123T083753Z_k2_ml |
| `k8_fixed` | 0,214 | 0,214 | 141 | 20261123T093910Z_k8_food |
| `k8_ridge_nr` | 0,215 | 0,215 | 141 | 20261123T093910Z_k8_food |
| `k7_med_half` | 0,216 | 0,216 | 141 | 20261123T093401Z_k7_services |
| `k7_cal_half` | 0,216 | 0,216 | 141 | 20261123T093401Z_k7_services |
| `k8_ridge` | 0,216 | 0,216 | 141 | 20261123T093910Z_k8_food |
| `j1_comb_invmse` | 0,216 | 0,216 | 141 | 20261122T221013Z_j1_hybrid |
| `avg_5050` | 0,217 | 0,210 | 134 | 20261123T100622Z_k13_tax |
| `j1_comb_ols` | 0,217 | 0,217 | 141 | 20261122T221013Z_j1_hybrid |
| `k7_med_full` | 0,218 | 0,218 | 141 | 20261123T093401Z_k7_services |
| `k7_cal_full` | 0,219 | 0,219 | 141 | 20261123T093401Z_k7_services |
| `j1_hyb_energy_ea` | 0,222 | 0,222 | 141 | 20261122T221013Z_j1_hybrid |
| `j1_comb_ols_age` | 0,222 | 0,222 | 141 | 20261122T221013Z_j1_hybrid |
| `j1_hyb_energy` | 0,226 | 0,226 | 141 | 20261122T221013Z_j1_hybrid |
| `k2_j2_ridge_s` | 0,227 | 0,227 | 141 | 20261123T083753Z_k2_ml |
| `j1_hyb_energy_core` | 0,228 | 0,228 | 141 | 20261122T221013Z_j1_hybrid |
| `j1_hyb_energy_fixed` | 0,238 | 0,238 | 141 | 20261122T221013Z_j1_hybrid |
| `k2_rb_hgb_s` | 0,241 | 0,241 | 141 | 20261123T083753Z_k2_ml |
| `j2_el_dev_var` | 0,243 | 0,243 | 141 | 20261122T220640Z_j2_el |
| `j2` | 0,243 | 0,236 | 134 | 20261123T100622Z_k13_tax |
| `j4_detail_energy_easter` | 0,243 | 0,243 | 141 | 20261122T222015Z_j4_detail |
| `j4_detail_energy` | 0,243 | 0,243 | 141 | 20261122T222015Z_j4_detail |
| `j2_el_dev_se3` | 0,245 | 0,245 | 141 | 20261122T220640Z_j2_el |
| `j2_el_trendbase` | 0,248 | 0,248 | 141 | 20261122T220640Z_j2_el |
| `rb_updated` | 0,256 | 0,243 | 134 | 20261123T100622Z_k13_tax |
| `k0_c1` | 0,256 | 0,256 | 141 | 20261123T084148Z_k0_screen |
| `j2_el_raw` | 0,279 | 0,279 | 141 | 20261122T220640Z_j2_el |
| `j4_detail_base` | 0,335 | 0,335 | 141 | 20261122T222015Z_j4_detail |

`kpif_nowcast.__file__` = `C:\dev\kpif-nowcast\src\kpif_nowcast\__init__.py`. K2:s L-mängd: k2_ml.K2_CATALOG_KEYS (on main).
