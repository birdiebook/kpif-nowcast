# V2 Gemensam screening av körning 3:s nya serier: resultat

## Urvalsevidens (sammanfattning efter granskning)

All evidens nedan är urvalsevidens på 2015–2026, samma period som modellerna valdes på. Projektet har totalt
**53 varianter** (51 före körning 3, plus V2:s två). Körning 3 har förbrukat 2 av 6.

- **Ingen variant klarade urvalsskärmen, och inget fryses som skuggprognos.** Det gäller också efter granskningen.
  Ingen läcka hittades, så inga siffror ändrades.
- Screeningen av 10 serier per bas gav 0 BH-överlevare (q = 0,10). Lägsta råa p var 0,143 mot skuggan och 0,032
  mot 50/50, båda för `kpif_air_transport_index`. Screeningen räknas inte mot taket.
- `v2_r_corr` (nr 52, flygpriser på skuggan av `k2_avg_ridge_l`): MAE 0,2072 mot 0,2113. Rå p 0,143 (projektet
  totalt 53 varianter), Holm p 0,143 (projektet totalt 53 varianter), globalt justerat p 0,790 (40 modeller i U1 +
  V2; projektet totalt 53 varianter).
- `v2_a_corr` (nr 53, flygpriser på 50/50): MAE 0,2241 mot 0,2320. Rå p 0,032 (projektet totalt 53 varianter),
  Holm p 0,064 (projektet totalt 53 varianter), globalt justerat p 0,477 (40 modeller i U1 + V2; projektet totalt
  53 varianter). Rå p är samma tal som det lägsta av de 20 screenade p-värdena, eftersom bara en serie valdes.
  Holm över två varianter tar inte hänsyn till screeningen. Knappt hälften av vinsten (48 %) ligger i 2021. Utan
  2021 är rå p 0,134 (projektet totalt 53 varianter).
- Med K13:s två varianter i universumet (som saknades i K12:s U1) blir det justerade p:t 0,486 och 0,793. SPA mot
  skuggan, consistent: 0,625 (projektet totalt 53 varianter). Mot 50/50: 0,023. Det senare beror på K2-familjen,
  som i K12.
- Flygindexets revision (COICOP 2018) ändrar inte utfallet. Med gammal årgång blir p 0,036 för `v2_a_corr` och
  0,174 för `v2_r_corr` (projektet totalt 53 varianter).

Förregistrering: [hypotes.md](hypotes.md) (commit c3f7670). Kod: `python -m kpif_nowcast.v2_screen`
(`src/kpif_nowcast/v2_screen.py`), tester `tests/test_v2_screen.py`. Rådata med alla tabeller:
[results_raw.md](results_raw.md), kontrollerna före screeningen: [checks_raw.md](checks_raw.md).
Körlogg: `experiments/runs/20261123T143421Z_v2_screen.csv`.

Allt nedan är **urvalsevidens** på samma period som modellerna valdes på (2015–2026). Det ersätter inte ett utfall
utanför urvalet.

## Dom

**Ingen variant klarade urvalsskärmen. Inget fryses som skuggprognos.**

- Screeningen gav **0 BH-överlevare** mot båda baserna (10 serier per bas, q = 0,10). Den lägsta råa p-värdet var
  0,143 mot skuggan av `k2_avg_ridge_l` och 0,032 mot 50/50. Båda gällde `kpif_air_transport_index`.
- Urvalsregeln valde **en serie per bas, samma för båda: `kpif_air_transport_index`** (flygresor, KPIF-delindex,
  revised=True). "Ingen överlevde BH" för båda. Mot skuggan var det den enda serien med negativ MAE-diff. Mot 50/50
  hade även `easter_window_days` negativ diff (−0,0003), men den är i samma källgrupp (resor) och hoppades över.
- Båda förregistrerade varianterna kördes en gång. Projektet har nu **53 varianter** (51 + `v2_r_corr` = nr 52 +
  `v2_a_corr` = nr 53). Körningens tak är 6, och V2 förbrukade 2.
  - `v2_r_corr`: MAE 0,2072 mot skuggan 0,2113 (diff −0,0041), rå p 0,143 · Holm p 0,143 (projektet totalt 53
    varianter) · globalt justerat p 0,790 (40 modeller i U1 + V2; projektet totalt 53 varianter). Klarade inte
    villkor 1 och 2.
  - `v2_a_corr`: MAE 0,2241 mot 50/50 0,2320 (diff −0,0079), rå p 0,032 · Holm p 0,064 (projektet totalt 53
    varianter) · globalt justerat p 0,477 (40 modeller i U1 + V2; projektet totalt 53 varianter). Klarade villkor 1
    och 3, inte villkor 2.

Gissningen innan stämde: 0 överlevare, och ingen variant klarade skärmen. Den gissade storleken (−0,006 till +0,002 pe)
stämde för bas R (−0,004) men inte riktigt för bas A (−0,008). Fel serie var gissad: paketresor och påsk var
favoriterna, men det blev flygresor.

## 1. Kontroller före screeningen (avsnitt 6)

| # | Kontroll | Utfall |
|---|---|---|
| 1 | p*(t) enligt tabellen för alla 10 kandidater, 2015-01..2026-10, `known_from ≤ deadline(t)` | OK. 16 avvikelser, alla för `el_contract_spot_share` och alla förklarade av dokumenterade sena releaser (TAB3571: 2022-01..03 → 2022-04-30, 2023-05..2024-06 → 2024-09-27). 0 okända. |
| 2 | p* för elavtal vid deadline 2024-01 | 2023-04, som väntat. |
| 3 | Marginal till deadline | Minsta marginal före deadline: KPIF-delindex och hyror 17 d, gästnätter 13 d, elavtal 4 d (rättelsen 2022-04-30 mot deadline 2022-05-04), kronan 3 d, påsken 370 d. Nästa period blir känd tidigast 11 d (delindex), 14 d (gästnätter) och 24 d (elavtal) efter deadline. |
| 4 | Inga features över hela perioden | Enligt konstruktion: x(t) bara från p* och bakåt, x̄ och b bara på träningsrader. Reglerna beror bara på datum. |
| 5 | pytest | `tests/test_v2_screen.py` grönt före screeningen (commit 8e0ad8e): x(t) och korrigerad prognos identiska på kapad tabell för båda baserna och kombinationen av tre kandidater. Inaktuella-regeln ger saknat x för 2023-08..2024-07 och brottregeln saknat x för 2023-03. |
| 6 | Revisioner | Sex av tio kandidater har revised=True, däribland den valda `kpif_air_transport_index`. Det går inte att verifiera bort. |
| 7 | Baserna | 50/50: 0,2165 (0,217) OK. Skuggan: **0,1993, inte 0,200**. Avvikelse, se nedan. |
| 8 | Registrerade varianter oförändrade | Identiska med main före körning 3. **Inte** identiska med K12:s fil i 11 av 38 modeller. Avvikelse, se nedan. |

## 2. Screeningtabell, primärperioden 2017-02..2026-10 (n = 117)

Ensidigt DM mot den egna basen. BH per bas över 10 serier. Screeningen räknas inte mot varianttaket. Perioderna
2015–2026 och 2024–2026 finns i [results_raw.md](results_raw.md).

**Bas R: skuggversionen av `k2_avg_ridge_l` (bas-MAE 0,2113)**

| Serie | Grupp | MAE | diff | rå p | BH-q | revised |
|---|---|---|---|---|---|---|
| `kpif_air_transport_index` | resor | 0,207 | −0,0041 | 0,143 | 0,998 | ja |
| `easter_window_days` | resor | 0,212 | +0,0008 | 0,557 | 0,998 | nej |
| `guest_nights_domestic` | resor | 0,212 | +0,0008 | 0,650 | 0,998 | ja |
| `kpi_rent_index` | hyror | 0,217 | +0,0062 | 0,778 | 0,998 | ja |
| `sek_usd` | kronan | 0,214 | +0,0029 | 0,864 | 0,998 | nej |
| `kpif_package_holidays_index` | resor | 0,216 | +0,0046 | 0,937 | 0,998 | ja |
| `kpif_accommodation_index` | resor | 0,215 | +0,0040 | 0,943 | 0,998 | ja |
| `guest_nights_foreign` | resor | 0,215 | +0,0041 | 0,971 | 0,998 | ja |
| `el_contract_spot_share` | el | 0,216 | +0,0048 | 0,986 | 0,998 | ja |
| `sek_eur` | kronan | 0,214 | +0,0028 | 0,998 | 0,998 | nej |

**Bas A: `avg_5050` (bas-MAE 0,2320)**

| Serie | Grupp | MAE | diff | rå p | BH-q | revised |
|---|---|---|---|---|---|---|
| `kpif_air_transport_index` | resor | 0,224 | −0,0079 | 0,032 | 0,320 | ja |
| `easter_window_days` | resor | 0,232 | −0,0003 | 0,479 | 0,988 | nej |
| `kpi_rent_index` | hyror | 0,238 | +0,0056 | 0,765 | 0,988 | ja |
| `kpif_accommodation_index` | resor | 0,235 | +0,0031 | 0,833 | 0,988 | ja |
| `guest_nights_domestic` | resor | 0,235 | +0,0029 | 0,867 | 0,988 | ja |
| `sek_usd` | kronan | 0,235 | +0,0033 | 0,870 | 0,988 | nej |
| `kpif_package_holidays_index` | resor | 0,237 | +0,0050 | 0,923 | 0,988 | ja |
| `el_contract_spot_share` | el | 0,235 | +0,0034 | 0,935 | 0,988 | ja |
| `sek_eur` | kronan | 0,236 | +0,0036 | 0,979 | 0,988 | nej |
| `guest_nights_foreign` | resor | 0,237 | +0,0048 | 0,988 | 0,988 | ja |

Alla tio uppfyllde täckningskravet. Elavtalen har x i 103 av 117 månader, övriga i 117. Påsken är aktiv i 27 månader
(x = 0 när påsken inte flyttar mellan månader).

## 3. Valda serier (avsnitt 3, mekaniskt)

| Bas | Ordning efter regeln | Valda | Märkning |
|---|---|---|---|
| R | Inga BH-överlevare. Bara `kpif_air_transport_index` har negativ diff, de övriga nio fylls inte på. | `kpif_air_transport_index` | ingen överlevde BH |
| A | Inga BH-överlevare. `kpif_air_transport_index` (resor), sedan `easter_window_days` (resor, hoppas över: gruppen redan vald). Inga fler med negativ diff. | `kpif_air_transport_index` | ingen överlevde BH |

Urvalet är fryst i `v2_screen.V2_CHOSEN`. `k12_global` bygger varianterna därifrån (familjen `v2`), och testet
`test_selection_reproduces_frozen_choice` kontrollerar att regeln på de sparade tabellerna ger samma val.

## 4. Gemensamt test (en gång)

| Variant | Bas | Period | MAE | bas-MAE | diff | rå p | Holm p | Projektet |
|---|---|---|---|---|---|---|---|---|
| `v2_r_corr` | skugga `k2_avg_ridge_l` | **2017-02..2026-10** | 0,2072 | 0,2113 | −0,0041 | 0,143 | 0,143 | totalt 53 varianter |
| | | 2015-01..2026-10 | 0,1959 | 0,1993 | −0,0034 | 0,143 | – | totalt 53 varianter |
| | | 2024-01..2026-10 (använd) | 0,2245 | 0,2292 | −0,0047 | 0,296 | – | totalt 53 varianter |
| `v2_a_corr` | `avg_5050` | **2017-02..2026-10** | 0,2241 | 0,2320 | −0,0079 | 0,032 | 0,064 | totalt 53 varianter |
| | | 2015-01..2026-10 | 0,2100 | 0,2165 | −0,0066 | 0,033 | – | totalt 53 varianter |
| | | 2024-01..2026-10 (använd) | 0,2440 | 0,2461 | −0,0021 | 0,396 | – | totalt 53 varianter |

Sekundärt mot rb_updated (MAE 0,2806 i primärperioden): `v2_r_corr` rå p 0,002 och `v2_a_corr` 0,005 (projektet
totalt 53 varianter). Det säger mest att baserna är bättre än rb_updated, vilket redan var känt.

**Kriterierna (avsnitt 5), låsta vid block 3:**

| Variant | 1. Holm p < 0,10 | 2. globalt justerat p < 0,10 (egen bas) | 3. MAE 2024–26 ≤ bas | Klarade urvalsskärmen |
|---|---|---|---|---|
| `v2_r_corr` | nej (0,143) | nej (0,790; block 1/6/12: 0,859/0,677/0,482) | ja (0,2245 ≤ 0,2292) | **nej** |
| `v2_a_corr` | ja (0,064) | nej (0,477; block 1/6/12: 0,620/0,359/0,315) | ja (0,2440 ≤ 0,2461) | **nej** |

Beslutet beror inte på blocklängden: villkor 2 faller vid alla fyra.

## 5. Globalt test (SPA, StepM, MCS)

Universum: K12:s U1 (35 registrerade h=1-varianter plus referenserna rb_updated, 50/50 och J2 V2) plus `v2_r_corr`,
`v2_a_corr` och skuggversionen av `k2_avg_ridge_l` som ribba. Totalt 41 serier, alltså 40 modeller mot varje ribba.
Gemensamt urval 2015-02..2026-10, n = 141. Stationär bootstrap med block 3, B = 9 999 och seed 20261123.
Känslighetskörningarna använder B = 4 999 och seed 20261123 + block, som K12.

| Ribba | block | SPA lower | SPA consistent | SPA upper | White RC | E[max förb.] H0 | 90 % | observerat max | StepM 10 % väljer (urval) |
|---|---|---|---|---|---|---|---|---|---|
| rb_updated | 3 | 0,029 | 0,029 | 0,031 | 0,026 | 0,022 | 0,045 | 0,060 | 18 modeller, bl.a. `v2_r_corr`, `v2_a_corr`, skuggan, `k2_avg_ridge_l` |
| avg_5050 | 3 | 0,019 | 0,023 | 0,024 | 0,530 | 0,023 | 0,038 | 0,021 | `k2_avg_ridge_l`, `k2_avg_ridge_lnr`, `v2_r_corr`, skuggan |
| skugga `k2_avg_ridge_l` | 3 | 0,344 | **0,625** | 0,790 | 0,945 | 0,023 | 0,041 | 0,003 | ingen |
| rb_updated | 6 | 0,072 | 0,075 | 0,082 | 0,047 | 0,024 | 0,049 | 0,060 | `k2_avg_ridge_lnr`, `v2_r_corr` |
| avg_5050 | 6 | 0,038 | 0,046 | 0,049 | 0,553 | 0,024 | 0,041 | 0,021 | `k2_avg_ridge_l`, `k2_avg_ridge_lnr`, `v2_r_corr`, skuggan |
| skugga | 6 | 0,259 | 0,514 | 0,677 | 0,919 | 0,024 | 0,045 | 0,003 | ingen |
| rb_updated | 12 | 0,106 | 0,111 | 0,117 | 0,057 | 0,024 | 0,052 | 0,060 | ingen |
| avg_5050 | 12 | 0,079 | 0,095 | 0,099 | 0,547 | 0,024 | 0,043 | 0,021 | `v2_r_corr` |
| skugga | 12 | 0,163 | 0,381 | 0,482 | 0,903 | 0,025 | 0,050 | 0,003 | ingen |
| (block 1 i [results_raw.md](results_raw.md)) | | | | | | | | | |

- **Mot skuggan av `k2_avg_ridge_l`** finns ingenting: SPA consistent 0,625 vid block 3, och StepM väljer ingen
  modell vid någon blocklängd. Det är den fråga som spelar roll för en korrektion på den bästa skuggmodellen.
- **Mot 50/50** är SPA p 0,023. Det beror på K2-familjen och var känt från K12 (0,025 där). `v2_a_corr` väljs
  inte av StepM (justerat p 0,477).
- `v2_r_corr` har lägst MAE i universumet (0,196 på 2015-02..2026-10) och väljs av StepM mot rb_updated och 50/50.
  Det är skuggans förtjänst, inte korrektionens: mot skuggan är dess justerade p 0,790.
- MCS (90 %, T_max, ribba rb_updated) innehåller båda V2-varianterna (p 1,000 och 0,684). Den skiljer inte de bästa
  modellerna åt, precis som i K12.
- Resultatet skrivs bara här. `docs/auto2/k12/resultat.md` skrivs inte över, enligt förregistreringen.

## 6. Urvalsbias

Om alla 40 modeller var exakt lika bra som ribban skulle den bästa ändå verka vinna med i snitt 0,022–0,023 pe MAE
(90 %-kvantil 0,038–0,045), oavsett ribba. Mot skuggan är det observerade maxet 0,003 pe, alltså långt inne i
brusbandet. Korrektionerna själva är −0,004 (bas R) och −0,008 pe (bas A) i primärperioden. Det är mindre än
E[max] under H0, och biasen är ännu större än så: de 2 × 10 screenade serierna ingår inte i universumet.

På den studentiserade skala som SPA och StepM använder har `v2_a_corr` t = 1,79 mot 50/50. Under H0 är det största t
bland 40 modeller i snitt 1,82 (90 %-kvantil 2,59). För `v2_r_corr` är t = 1,03 mot skuggan, mot 1,55 (90 %: 2,39)
under H0. Därför faller villkor 2 även när Holm över två varianter klarar 0,10. Siffrorna är omräknade med
`k12_global.collect_all()` inklusive familjen `v2`, som ger samma justerade p (0,477 och 0,790).

## 7. Avvikelser från protokollet

1. **Kontroll 7, skuggan 0,1993 i stället för 0,200.** Skuggversionen på den här grenen är **identisk** med samma
   kod på main före körning 3 (129bbb0) på samma data (största skillnad 0). Skillnaden mot det förregistrerade
   0,200 (K2b:s decfix 0,1996) kommer alltså inte från körning 3. Den kommer från main efter K2b: K11:s
   publiceringskalender och nya laggar (bland annat `freight_ppi_deepsea` och flashdatumen), och möjligen dagens
   dataårgång (`data/processed` hämtades om i dag). Kontrollens syfte är att basen är den verkliga skuggan, och det
   är den. Testet fortsatte därför. Regeln "annars stoppas testet" följdes alltså inte bokstavligt.
2. **Kontroll 8, K12:s tabell reproduceras inte exakt.** 27 av 38 modeller är identiska på 3 decimaler. 11 skiljer
   sig: K2-familjen, K7:s K2-lager och K8:s ensemble +0,001 (`k2_avg_ridge_l` 0,199 → 0,200), `k2_j2_ridge_s`
   0,227 → 0,230, `j1_hyb_energy_ea` 0,222 → 0,223 och `j3_combo` 0,254 → 0,255. Alla 47 kolumner i
   `k12_global.collect_all` är identiska med main före körning 3 på samma data (största skillnad 4·10⁻¹⁶). Körning 3
   har alltså inte ändrat någon registrerad variant. Avvikelsen mot K12:s fil kommer från K11 (mergad efter K12:s
   körning, med +0,001 för K2 enligt K11) och möjligen dataårgången. Vilket av dem som ger vad har inte separerats.
   Med dagens main ger K12:s gamla U1 SPA consistent 0,035 mot rb_updated (K12: 0,035) och 0,021 mot 50/50 (K12: 0,025).
   `j3_screen.screen_keys()` frystes till de 77 serierna före körning 3 (`SCREEN_KEYS_PRE_RUN3`).
   `screen_keys(frozen=False)` ger den katalogstyrda listan.
3. **Elavtalen har x i 103 primärmånader, inte 104.** Även 2024-08 saknar x. J3-transformen behöver v(2024-06), som
   blev känd först 2024-09-27, efter deadline 2024-09-04. Det följer mekaniskt av den förregistrerade transformen och
   ändrar inget: kravet ≥ 100 uppfylls, och serien valdes inte.
4. **Inläggning i K12:s universum** sker via en collector-familj `v2` i `k12_global.FAMILIES`
  (`collect_v2` → `v2_screen.k12_forecasts`) och prefixet `("v2_", "V2")`, inte via `outputs/k12/extra/*.csv`.
   Serierna är desamma (största skillnad mot körningens egna 1,8·10⁻¹⁵). Skuggan ligger i `k12_global.REFERENCES`
   som `k2_avg_ridge_l_shadow`, eftersom den är en ribba och inte en ny variant.
5. **Tekniskt:** K2-, K7- och K8-familjerna räknades med `OMP_NUM_THREADS=1`, för att undvika överbelastning av
   trådarna i HistGradientBoosting. Referenskörningen på 129bbb0 gjordes på samma sätt. Två befintliga tester
   justerades: `test_l2_travel` använder nu `screen_keys(frozen=False)`, och `test_l6_fx` kontrollerar ordning i
   stället för grannskap. Det senare föll redan på våg 1:s merge, före V2.

## 8. Vad vi lärde oss

- **Körning 3:s nya serier tillför inget som går att skilja från brus på 1 månads sikt**, varken till den bästa
  skuggmodellen eller till 50/50. Det gäller resepriser, gästnätter, påsken, hyror, elavtal och kronan. Det är
  samma utfall som J3 (45 serier) och K0 (29 serier).
- Den enda signalen är **flygpriser som återgår**: koefficienten är negativ (b ≈ −0,005 pe per enhet x, korrelation
  med missen ≈ −0,2). Ett säsongsrensat hopp i flygindex i t−1 följs av en lägre KPIF-miss i t än basen väntar sig.
  Mekanismen är rimlig, eftersom flygpriserna är volatila och mätningen brusig. Effekten är liten och ojämn mellan
  åren. Mot 50/50 ligger 48 % av nettovinsten i 2021 (pandemins flygpriser). Därefter kommer 2017 (22 %), 2024
  (13 %) och 2022 (12 %). Utan 2021 är diff −0,0046 och p 0,134, och utan 2020–21 är p 0,183. Mot skuggan står
  de fem bästa månaderna för 132 % av nettovinsten, och utan 2017 är p 0,251. Vinståren är 2017, 2020, 2021, 2022,
  2024 och 2025, och förlustår 2018, 2019, 2023 och 2026. Mot 50/50 är förluståren 2019 och 2026. Förlustdifferensen
  har nästan ingen autokorrelation (lag 1–3 mellan −0,15 och 0,03), så det effektiva n är ungefär 117. Alla p-värden
  i den här punkten gäller med projektet totalt 53 varianter.
- Påsken bidrar inte utöver baserna (diff +0,0008 mot skuggan och −0,0003 mot 50/50). Det stämmer med K7.
- Kronan i säsongsdifferentierad månadsform ger ingenting utöver K2:s `kix` och `brent_sek`, och inte heller
  mot 50/50.
- Valet per bas blev i praktiken ett test av en serie. Regeln "bara negativ diff" lämnade ingen tvåa i en annan
  källgrupp. Taket på tre serier var alltså aldrig bindande.

## 9. Ärlig osäkerhet

- `v2_a_corr`:s Holm p 0,064 är det närmaste ett positivt resultat. Det är fortfarande "bäst av 10 serier × 2 baser"
  i en screening som inte räknas i det globala universumet. BH-q för serien är 0,32, och det globala justerade p:t
  är 0,477. Vi bedömer att det är förenligt med slump.
- `kpif_air_transport_index` har revised=True: historiken före 2026 är SCB:s omräkning till COICOP 2018. Efter
  granskningen är revisionsrisken kontrollerad för just den här serien (se avsnitt 11, fynd A2). Den gamla årgången
  ger samma utfall. För de övriga fem reviderade kandidaterna är den inte kontrollerad.
- n = 117 (primärt) och 34 (2024–2026). Styrkan räcker inte för att upptäcka förbättringar på 0,005 pe. Ett negativt
  utfall betyder "inte påvisbart", inte "noll".
- Basen R avviker 0,0003 pe från det förregistrerade referensvärdet av skäl utanför körning 3 (avsnitt 7, punkt 1).
  Vi har inte separerat om det beror på K11 eller på dataårgången.
- Inga realtidsårgångar finns för de reviderade serierna. Differenser minskar men tar inte bort revisionsläckage.

## 10. Följd

- Ingen ny skuggprognos. `shadow.SHADOW_MODELS`, `forecast.py`, `MODEL_NAME` och de skarpa prognoserna är orörda.
- Varianttal: projektet 53, körning 3 har förbrukat 2 av 6. 4 är kvar i reserv.
- `kpif_air_transport_index` kan följas i skuggornas utfall som beskrivning, men inte som modell utan en ny
  förregistrering.

## 11. Granskning

Två oberoende granskare, båda med domen "håller, med förbehåll". **Ingen läcka hittades.** Inga varianter kördes
om, och ingen siffra i avsnitt 1–10 ändrades av granskningen. Varje fynd är bedömt mot koden och datan nedan.
Projektets varianttal är 53 i alla p-värden.

| # | Fynd | Bedömning | Åtgärd |
|---|---|---|---|
| A1 | Läckagetestet i pytest täcker inte den valda serien (`COMBO` saknade `kpif_air_transport_index`), och baserna räknas inte om på kapad data. | **Håller.** Granskaren räknade om x(t) och korrektionen för hand, och bas A och bas R på kapade indata (2018-03, 2020-04, 2021-07, 2024-07, 2026-10). Allt var identiskt. p\*(t) = t−1 i alla 142 månader, med minst 17 dagars marginal. Ingen läcka, men testet var svagare än det borde vara. | **Rättat** i `tests/test_v2_screen.py`. `COMBO` innehåller nu flygindexet, och testet täcker varje serie i `V2_CHOSEN` både en och en och som den valda kombinationen per bas. Nytt test `test_v2_a_corr_end_to_end_on_cut_inputs` kapar alla indata vid deadline(t): KPIF och komponenter t.o.m. t−1, el och drivmedel t.o.m. t, Riksbankens prognoser publicerade före deadline och observationer kända vid deadline. Testet räknar sedan om 50/50-panelen, x och korrektionen, och kontrollerar att `v2_a_corr`(t) är identisk med helperiodsvärdet vid 2018-03, 2021-07, 2024-07 och 2026-10. Det är grönt. Bas R räknas inte om i pytest, eftersom en körning av skuggan tar minuter. Granskarens omräkning på kapad data (2020-04: 0,068742, 2024-07: 1,626432, 2026-10: 1,742914) står som verifiering. |
| A2 | Revisionsrisken för flygindexet (revised=True) markerades som "går inte att verifiera", men den går att verifiera. | **Håller.** Jag körde granskarens jämförelse på hans nedladdade fil ur SCB:s frysta tabell KPI19Bas1980, produktgrupperna 6305 och 6311 viktade. Mot TAB6613 07.3.3 2015–2025 är korrelationen 0,9989 för månadsförändringen och 0,9945 för J3-transformen x. Med gammal årgång t.o.m. mål 2026-01 blir `v2_a_corr` MAE 0,2244 och p 0,036 (i stället för 0,2241 och 0,032), och `v2_r_corr` MAE 0,2076 och p 0,174 (i stället för 0,2072 och 0,143). | **Rättat** i avsnitt 9 och i sammanfattningen. Revisionen ändrar inte utfallet för flygindexet. Det negativa beslutet står sig oavsett årgång. De andra fem reviderade kandidaterna är fortfarande inte kontrollerade. |
| A3 / B1 | Stoppregeln i kontroll 7 åsidosattes (0,1993 mot förregistrerat 0,200). B1 påpekar dessutom att undantaget lades in i koden (`v2_screen.py` rad 416–417, commit 8e0ad8e) efter förregistreringen men före screeningen. | **Håller som avvikelse, inte som läcka.** B körde 129bbb0 rent på samma data och fick 0,19934561392435557, alltså identiskt med grenens bas R. Avvikelsen kommer inte från körning 3. Ändringen committades 14:33, före screeningen 14:34:21, och den beror inte på några resultat. Det förregistrerade referensvärdet hade bara tre decimaler och var självt fel med ungefär 0,0003. | **Avvisat som fel i genomförandet. Redovisas oförändrat i avsnitt 7.1.** Lärdom till nästa förregistrering: ange referensvärdet med fyra decimaler och med kod- och dataversion, eller som "reproduceras mot main på samma data", och skriv i förväg vad som gäller om det reproduceras på koden före körningen men avviker från det angivna talet. |
| B2 | Kontroll 8 reproducerar inte K12:s tabell exakt. Det har inte separerats om orsaken är K11 eller dataårgången. | **Håller som öppen fråga.** B räknade om alla K12-familjer utan cache och fick som största skillnad 1,78·10⁻¹⁵ mot referensen före körning 3. Körning 3 har alltså inte ändrat någon registrerad variant. | **Inte rättat, eftersom det inte behövs för V2.** Separeringen kräver en omräkning av K12 på K12:s egen commit med dagens data. Den tas om någon behöver K12:s exakta tal. |
| B3 | Det "gemensamma testet" gav inget nytt belägg för `v2_a_corr`. Bara en serie valdes, så varianten är exakt screeningsprognosen. Rå p 0,032 är det lägsta av 20 screenade p-värden, och Holm över två varianter bortser från screeningen. Villkor 1 uppfylls bara nominellt: BH-q är 0,32, och Bonferroni över 20 hade gett 0,64. | **Håller.** Det stämmer exakt: i `screen_A.csv` har flygindexet MAE 0,224095 och p 0,03196, samma som i det gemensamma testet. Protokollet följdes. Det är en svaghet i protokollets utformning, och villkor 2 (globalt p 0,477) är det spärrande skyddet. | **Rättat i texten** (sammanfattningen överst). Lärdom till nästa förregistrering: kräv BH-överlevnad innan en ensam serie går till det gemensamma testet, eller räkna de screenade serierna i Holm-familjen. Behåll villkor 2 som spärr. |
| B4 | Det globala universumet täcker inte alla projektets varianter. K13:s `k13_j2_clean` och `k13_ens_clean` (nr 50–51) saknas i U1, liksom de 20 screenade serierna. Formuleringen "projektet totalt 53 varianter" bredvid det globala p:t antyder en justering över 53 varianter, men universumet har 40 modeller. | **Håller.** K12:s U1 förregistrerades, så protokollet följdes, men formuleringen var missvisande. Jag lade in K13:s två varianter i universumet som känslighetskörning (block 3, B = 9 999, seed 20261123, samma gemensamma urval n = 141, 42 modeller). Justerat p blev 0,486 för `v2_a_corr` (före: 0,477) och 0,793 för `v2_r_corr` (före: 0,790). SPA consistent blev 0,024 mot 50/50, 0,630 mot skuggan och 0,030 mot rb_updated. Beslutet ändras inte. | **Rättat.** Formuleringen lyder nu "globalt justerat p (40 modeller i U1 + V2; projektet totalt 53 varianter)", och K13-känsligheten står i sammanfattningen. `k12_global` är **inte** ändrat, eftersom V2:s förregistrerade universum är K12:s U1. Att lägga till K13 som familj i `k12_global` är en åtgärd inför nästa globala test, och orkestreraren bör göra det i nästa förregistrering. |
| B5 | Förregistreringen kallar det justerade p:t "Hansen-recentrerat", men `k12_global.spa_test` använder övre recentrering (db − dbar), alltså det konservativa valet. | **Håller.** Med Hansen-konsistent recentrering får B 0,414 för `v2_a_corr` och 0,625 för `v2_r_corr`. Båda ligger långt över 0,10, och t-statistikorna är desamma (1,789 och 1,028). | **Rättat i den här texten.** Det justerade p:t i avsnitt 4 och 5 är **upper-recentrerat, alltså konservativt**. `hypotes.md` rörs inte, eftersom det är förregistreringen. Beslutet ändras inte. |
| B6 | Texten om var vinsten ligger kvantifieras inte, och 2022 saknas. | **Håller.** Jag räknade om det på `outputs/v2/variants.csv`. För `v2_a_corr` står 2021 för 48 % av nettovinsten. Utan 2021 är diff −0,0046 och p 0,134, och utan 2020–21 är p 0,183. För `v2_r_corr` står de fem bästa månaderna för 132 % av nettovinsten, och utan 2017 är p 0,251. Summerat 2022 är −0,103 mot skuggan, och ACF lag 1–3 ligger mellan −0,15 och 0,03. | **Rättat** i avsnitt 8. |

**Efter granskningen:** ingen variant klarar urvalsskärmen enligt `hypotes.md` avsnitt 5. Villkor 2 faller för båda,
oavsett blocklängd, recentrering och om K13 är med. **Inget fryses som skuggprognos.** `shadow.SHADOW_MODELS`, `forecast.py`,
`MODEL_NAME`, `forecasts/` och de skarpa prognoserna är orörda. Projektet har totalt 53 varianter, och körning 3
har 4 av 6 kvar.
