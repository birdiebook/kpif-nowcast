# Publiceringskalender: fördröjning och revidering per katalogserie

Låst av `tests/test_publication_calendar.py`: kolumnerna *Fördröjning* och *Rev.* måste vara lika med `Spec.lag_days` och `Spec.revised` i `catalog.py`/`catalog_prices.py`/`catalog_af.py`, och tabellen över sena releaser måste vara lika med `publication.LATE_RELEASES`. Ändrar du en fördröjning: uppdatera raden och belägget.

**Regel.** Fördröjning = dagar efter periodens slut tills värdet säkert är publicerat (avrundat mot senare). Deadline för målmånad t är dag 4 i t+1. En serie med fördröjning ≤ 4 d ger period t; 5–32 d ger t−1 (gränsen beror på månadens längd); 35–63 d ger t−2. Läckage uppstår bara när modellen ser en period som i verkligheten inte var publicerad vid deadline, så *gräns* anger hur sent värdet kan komma utan att det blir läckage.

Granskning, metod och dom: [auto2/k11/granskning.md](auto2/k11/granskning.md). Länsserierna (`catalog_region.py`) ingår inte här.

| Nyckel | Fördröjning | Rev. | Belagd fördröjning (d) | Belägg | Dom |
|---|---|---|---|---|---|
| `kpif_index` | 15 | nej | 12 (okt 2026 → 2026-11-12) | SCB PxWeb v2 `updated` TAB6590/6593/6627 | OK; gräns för läckage ≥ 32 d |
| `kpif_yy` | 15 | nej | 12 (okt 2026 → 2026-11-12) | SCB PxWeb v2 `updated` TAB6590/6593/6627 | OK; gräns för läckage ≥ 32 d |
| `brent_sek` | 1 | nej | veckovis (FRED uppd. 2026-11-18 med data t.o.m. 11-17) | FRED DCOILBRENTEU | OK (dag 1–25 finns före dag 4) |
| `aku_unemp_nsa` | 25 | ja | 16–20 (jan 2025 → 02-17, jan 2026 → 02-16, okt 2026 → 11-20) | SCB statistiknyheter AKU, PxWeb `updated` TAB6387/6389 | OK. Rev.: nej → ja för nsa/employed (länkade data 2001–2020) |
| `aku_unemp_sa` | 25 | ja | 16–20 (jan 2025 → 02-17, jan 2026 → 02-16, okt 2026 → 11-20) | SCB statistiknyheter AKU, PxWeb `updated` TAB6387/6389 | OK |
| `gdp_ind_yy` | 45 | ja | 38–41 vanliga månader (11 stickprov 2022-11..2026-08), 28–30 kvartalets sista månad (6 stickprov) | SCB statistiknyheter BNP-indikator, t.ex. feb 2024 → 2024-04-10, aug 2025 → 2025-10-10 | **FÖR KORT (35) → 45** |
| `kix` | 1 | nej | 0–1 bankdag | Riksbanken SWEA/SWESTR, dagliga | OK (hela månaden före dag 4) |
| `policy_rate` | 1 | nej | 0–1 bankdag | Riksbanken SWEA/SWESTR, dagliga | OK (hela månaden före dag 4) |
| `ki_services` | 3 | nej | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `wage_private_nonmanual` | 60 | ja | 59–60 (maj 2026 → 07-30, aug 2026 → 10-29) | SCB KLP-sidan ("två månader efter"), PxWeb `updated` TAB2564/2550/1972/3657 | OK; gräns ≥ 63 d |
| `wage_private_manual_hourly` | 60 | ja | 59–60 (maj 2026 → 07-30, aug 2026 → 10-29) | SCB KLP-sidan ("två månader efter"), PxWeb `updated` TAB2564/2550/1972/3657 | OK; gräns ≥ 63 d |
| `wage_municipal_yy` | 60 | ja | 59–60 (maj 2026 → 07-30, aug 2026 → 10-29) | SCB KLP-sidan ("två månader efter"), PxWeb `updated` TAB2564/2550/1972/3657 | OK; gräns ≥ 63 d |
| `labour_cost_salaried_yy` | 60 | ja | 59–60 (maj 2026 → 07-30, aug 2026 → 10-29) | SCB KLP-sidan ("två månader efter"), PxWeb `updated` TAB2564/2550/1972/3657 | OK; gräns ≥ 63 d |
| `labour_cost_workers_yy` | 60 | ja | 59–60 (maj 2026 → 07-30, aug 2026 → 10-29) | SCB KLP-sidan ("två månader efter"), PxWeb `updated` TAB2564/2550/1972/3657 | OK; gräns ≥ 63 d |
| `vacancies` | 60 | nej | 59 (2026K2 → 08-28) | SCB PxWeb `updated` | OK, ingår ej i K2 |
| `aku_employed` | 25 | ja | 16–20 (jan 2025 → 02-17, jan 2026 → 02-16, okt 2026 → 11-20) | SCB statistiknyheter AKU, PxWeb `updated` TAB6387/6389 | OK. Rev.: nej → ja för nsa/employed (länkade data 2001–2020) |
| `hours_worked_yy` | 60 | ja | 59 (2026K2 → 08-28) | SCB PxWeb `updated` | OK, ingår ej i K2 |
| `hh_consumption_yy` | 45 | ja | ny metod 10–13 (maj 2026 → 06-10, okt 2026 → 11-13); gamla indikatorn ca 40 (följde BNP-indikatorn) | SCB statistiknyheter hushållens konsumtion 2026, PxWeb `updated` TAB6932 | **FÖR KORT (15) → 45**; serien finns i denna form först 2026 |
| `retail_volume_yy` | 30 | ja | 20–30 (nov 2024 → 12-20, mar 2025 → 04-29, jun 2026 → 07-30, aug 2026 → 09-30, sep 2026 → 10-29) | SCB/TT, PxWeb `updated` TAB3948 | OK; gräns ≥ 32 d |
| `hh_infl_exp_median` | 3 | nej | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `hh_infl_perceived_median` | 3 | nej | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `hh_price_exp_net` | 3 | nej | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `hh_saving_rate` | 60 | ja | 59 (2026K2 → 08-28) | SCB PxWeb `updated` | OK, ingår ej i K2 |
| `ea_flash_total` | 2 | nej | −1 till +7; december 4–7 (se sena releaser) | Eurostat euro-indikatorer, releasekod 2-DDMMYYYY-ap, 2017-08..2026-10 | **FÖR KORT för sena releaser → datum i publication.py** |
| `ea_flash_energy` | 2 | nej | −1 till +7; december 4–7 (se sena releaser) | Eurostat euro-indikatorer, releasekod 2-DDMMYYYY-ap, 2017-08..2026-10 | **FÖR KORT för sena releaser → datum i publication.py** |
| `ea_flash_food` | 2 | nej | −1 till +7; december 4–7 (se sena releaser) | Eurostat euro-indikatorer, releasekod 2-DDMMYYYY-ap, 2017-08..2026-10 | **FÖR KORT för sena releaser → datum i publication.py** |
| `ea_flash_goods` | 2 | nej | −1 till +7; december 4–7 (se sena releaser) | Eurostat euro-indikatorer, releasekod 2-DDMMYYYY-ap, 2017-08..2026-10 | **FÖR KORT för sena releaser → datum i publication.py** |
| `ea_flash_services` | 2 | nej | −1 till +7; december 4–7 (se sena releaser) | Eurostat euro-indikatorer, releasekod 2-DDMMYYYY-ap, 2017-08..2026-10 | **FÖR KORT för sena releaser → datum i publication.py** |
| `ea_hicp_total` | 26 | ja | 17–25 (dec 2023 → 01-17, dec 2025 → 01-19, jan 2026 → 02-25) | Eurostat euro-indikatorer | för kort (20) men ofarlig → 26 |
| `fao_food_idx` | 10 | ja | 2–9 (2026: 9 jan, 6 feb, … 6 nov) | FAO FFPI release-kalender 2026 | för kort (8) men ofarlig → 10 |
| `fao_cereals` | 10 | ja | 2–9 (2026: 9 jan, 6 feb, … 6 nov) | FAO FFPI release-kalender 2026 | för kort (8) men ofarlig → 10 |
| `fao_dairy` | 10 | ja | 2–9 (2026: 9 jan, 6 feb, … 6 nov) | FAO FFPI release-kalender 2026 | för kort (8) men ofarlig → 10 |
| `gas_eu_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `wheat_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `gscpi` | 22 | ja | ca 4:e bankdagen; okt 2026 fanns 2026-11-22 | NY Fed, observationstabellen (1 stickprov) | OK (för lång) |
| `freight_ppi_deepsea` | 21 | ja | 8–20 normalt (BLS 2015–2025), 30–75 för sep–dec 2025 (shutdown) | BLS, Historical release dates for the PPI (not 8–11) | **FÖR KORT: läckage 2025-10..12 → 21 + datum i publication.py** |
| `gdp_real_q` | 60 | ja | 59 (2026K2 → 08-28) | SCB PxWeb `updated` | OK, ingår ej i K2 |
| `hours_worked_q` | 60 | ja | 59 (2026K2 → 08-28) | SCB PxWeb `updated` | OK, ingår ej i K2 |
| `lp_hour_yy_se` | 60 | ja | – | – | ej granskad (ingår ej i K2/K0) |
| `lp_hour_yy_ea` | 60 | ja | – | – | ej granskad (ingår ej i K2/K0) |
| `software_investment_q` | 60 | ja | 59 (2026K2 → 08-28) | SCB PxWeb `updated` | OK, ingår ej i K2 |
| `ai_use_firms_se` | 345 | nej | – | – | ej granskad (ingår ej i K2/K0) |
| `ai_use_firms_eu` | 345 | nej | – | – | ej granskad (ingår ej i K2/K0) |
| `jobads_total` | 3 | nej | okt 2026 fanns 2026-11-22 | JobTech historical API (ingen releasekalender) | ej belagd; serien är en rekonstruktion |
| `jobads_ml` | 3 | nej | okt 2026 fanns 2026-11-22 | JobTech historical API (ingen releasekalender) | ej belagd; serien är en rekonstruktion |
| `jobads_ai` | 3 | nej | okt 2026 fanns 2026-11-22 | JobTech historical API (ingen releasekalender) | ej belagd; serien är en rekonstruktion |
| `house_price_idx` | 30 | ja | 23 (2026K3 → 10-23) | SCB PxWeb `updated` TAB1150 | OK, ingår ej i K2 |
| `mortgage_rate_new` | 30 | nej | 27 (sep 2026 → 10-27) | SCB PxWeb `updated` TAB5783/4514 (1 stickprov) | OK; gräns ≥ 32 d |
| `hh_lending_growth` | 30 | nej | 27 (sep 2026 → 10-27) | SCB PxWeb `updated` TAB5783/4514 (1 stickprov) | OK; gräns ≥ 32 d |
| `nfc_lending_growth` | 30 | nej | 27 (sep 2026 → 10-27) | SCB PxWeb `updated` TAB5783/4514 (1 stickprov) | OK; gräns ≥ 32 d |
| `housing_starts` | 60 | ja | 54 (2026K3 → 11-23) | SCB PxWeb `updated` TAB4572 | OK, ingår ej i K2 |
| `rent_change` | -60 | nej | −90 (2026 → 2026-10-02) | SCB PxWeb `updated` TAB6051 | OK, ingår ej i K2 |
| `nier_barometer` | 3 | ja | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `nier_conf_services` | 3 | ja | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `nier_conf_trade` | 3 | ja | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `nier_conf_households` | 3 | ja | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `nier_capacity_util_mfg` | 3 | nej | kvartalsfrågor i jan/apr/jul/okt-barometern; 2026K4 fanns 2026-11-22 | konj.se, observationstabellen | OK (för lång), ingår ej i K2 |
| `nier_labour_shortage` | 3 | nej | kvartalsfrågor i jan/apr/jul/okt-barometern; 2026K4 fanns 2026-11-22 | konj.se, observationstabellen | OK (för lång), ingår ej i K2 |
| `nier_firm_infl_exp_old` | 3 | nej | kvartalsfrågor i jan/apr/jul/okt-barometern; 2026K4 fanns 2026-11-22 | konj.se, observationstabellen | OK (för lång), ingår ej i K2 |
| `nier_firm_infl_exp_new` | 3 | nej | kvartalsfrågor i jan/apr/jul/okt-barometern; 2026K4 fanns 2026-11-22 | konj.se, observationstabellen | OK (för lång), ingår ej i K2 |
| `bankruptcies` | 10 | nej | 5 (okt 2026 → 11-05) | Tillväxtanalys PxWeb `updated` (1 stickprov) | OK (för lång) |
| `ipi_yy` | 45 | ja | 41 (sep 2026 → 11-10) | SCB PxWeb `updated` TAB1872/3854/1710 (1 stickprov) | OK; gräns ≥ 63 d |
| `service_prod_idx` | 45 | ja | 41 (sep 2026 → 11-10) | SCB PxWeb `updated` TAB1872/3854/1710 (1 stickprov) | OK; gräns ≥ 63 d |
| `industry_orders_yy` | 45 | ja | 41 (sep 2026 → 11-10) | SCB PxWeb `updated` TAB1872/3854/1710 (1 stickprov) | OK; gräns ≥ 63 d |
| `af_varsel` | 15 | ja | 10 (okt 2026 → 11-10) | catalog_af (J6) | OK, ingår ej i K2 |
| `af_inskrivna_arbetslosa` | 15 | nej | 10 (okt 2026 → 11-10) | catalog_af (J6) | OK, ingår ej i K2 |
| `af_oppet_arbetslosa` | 15 | nej | 10 (okt 2026 → 11-10) | catalog_af (J6) | OK, ingår ej i K2 |
| `ppi_hmpi_consumer` | 30 | ja | 26 (sep 2026 → 10-26) | SCB PxWeb `updated` TAB3184 (1 stickprov) | OK; gräns ≥ 32 d |
| `ppi_impi_consumer` | 30 | ja | 26 (sep 2026 → 10-26) | SCB PxWeb `updated` TAB3184 (1 stickprov) | OK; gräns ≥ 32 d |
| `ppi_itpi_consumer` | 30 | ja | 26 (sep 2026 → 10-26) | SCB PxWeb `updated` TAB3184 (1 stickprov) | OK; gräns ≥ 32 d |
| `ppi_itpi_consumer_xfood` | 30 | ja | 26 (sep 2026 → 10-26) | SCB PxWeb `updated` TAB3184 (1 stickprov) | OK; gräns ≥ 32 d |
| `ppi_hmpi_food` | 30 | ja | 26 (sep 2026 → 10-26) | SCB PxWeb `updated` TAB3184 (1 stickprov) | OK; gräns ≥ 32 d |
| `ppi_impi_food` | 30 | ja | 26 (sep 2026 → 10-26) | SCB PxWeb `updated` TAB3184 (1 stickprov) | OK; gräns ≥ 32 d |
| `kpif_xe_index` | 15 | nej | 12 (okt 2026 → 2026-11-12) | SCB PxWeb v2 `updated` TAB6590/6593/6627 | OK; gräns för läckage ≥ 32 d |
| `kpif_goods_index` | 15 | ja | 12 (okt 2026 → 2026-11-12) | SCB PxWeb v2 `updated` TAB6590/6593/6627 | OK; gräns för läckage ≥ 32 d |
| `kpif_services_index` | 15 | ja | 12 (okt 2026 → 2026-11-12) | SCB PxWeb v2 `updated` TAB6590/6593/6627 | OK; gräns för läckage ≥ 32 d |
| `ki_prices_grocery` | 3 | nej | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `ki_prices_durables` | 3 | nej | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `ki_prices_retail` | 3 | nej | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `ki_purchase_prices_grocery` | 3 | nej | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `ki_prices_food_industry` | 3 | nej | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `ki_prices_consumer_industry` | 3 | nej | −12 till −1 (dag 19–30 i mätmånaden) | konj.se, 34 releaser 2024-01..2026-10 (t.ex. 2024-12-20, 2025-12-19, 2026-10-29) | OK (för lång, ofarlig) |
| `coffee_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `cocoa_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `sugar_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `beef_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `pork_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `poultry_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `palm_oil_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `soy_oil_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `rapeseed_oil_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `sunflower_oil_usd` | 60 | ja | ca 22 (sep 2026 → FRED 2026-10-22); okt 2026 saknades 2026-11-23 | FRED seriesida PWHEAMTUSDM, K0 | OK (för lång) |
| `gvb_2y` | 1 | nej | 0–1 bankdag | Riksbanken SWEA/SWESTR, dagliga | OK (hela månaden före dag 4) |
| `gvb_5y` | 1 | nej | 0–1 bankdag | Riksbanken SWEA/SWESTR, dagliga | OK (hela månaden före dag 4) |
| `gvb_10y` | 1 | nej | 0–1 bankdag | Riksbanken SWEA/SWESTR, dagliga | OK (hela månaden före dag 4) |
| `swestr` | 1 | nej | 0–1 bankdag | Riksbanken SWEA/SWESTR, dagliga | OK (hela månaden före dag 4) |

## Sena releaser (known_from = releasedatum)

`known_from = max(periodens slut + fördröjning, releasedatum)`, se `src/kpif_nowcast/publication.py`.

| Serie | Period | Releasedatum | Källa |
|---|---|---|---|
| `ea_flash_*` | 2017-12 | 2018-01-05 | Eurostat 2-05012018-ap |
| `ea_flash_*` | 2019-12 | 2020-01-07 | Eurostat 2-07012020-ap |
| `ea_flash_*` | 2020-12 | 2021-01-07 | Eurostat 2-07012021-ap |
| `ea_flash_*` | 2021-12 | 2022-01-07 | Eurostat 2-07012022-ap |
| `ea_flash_*` | 2022-12 | 2023-01-06 | Eurostat 2-06012023-ap |
| `ea_flash_*` | 2023-12 | 2024-01-05 | Eurostat 2-05012024-ap |
| `ea_flash_*` | 2024-12 | 2025-01-07 | Eurostat 2-07012025-ap |
| `ea_flash_*` | 2025-12 | 2026-01-07 | Eurostat 2-07012026-ap |
| `freight_ppi_deepsea` | 2025-09 | 2025-11-25 | BLS, historical release dates for the PPI |
| `freight_ppi_deepsea` | 2025-10 | 2026-01-14 | BLS, historical release dates for the PPI |
| `freight_ppi_deepsea` | 2025-11 | 2026-01-14 | BLS, historical release dates for the PPI |
| `freight_ppi_deepsea` | 2025-12 | 2026-01-30 | BLS, historical release dates for the PPI |

## Körning 3: L5

El: andel avtalstyper (SCB TAB3571), elnätspriser 1 januari (SCB TAB3950) och nätbolagens tariffer (Energimarknadsinspektionen). Årsvärden ligger på december; år Y = tariff 1 januari Y. Negativ fördröjning betyder publicering under året (som `rent_change`).

| Nyckel | Fördröjning | Rev. | Belagd fördröjning (d) | Belägg | Dom |
|---|---|---|---|---|---|
| `el_contract_spot_share` | 28 | ja | 23–24 (sep 2026 → 10-23, okt 2026 → 11-24 planerat) | SCB PxWeb `updated` TAB3571 (sep 2026 → 2026-10-23), scb.se/en0301 "Nästa publicering: 2026-11-24" (okt 2026), ei.se "Kunder per avtalstyp": "uppdateras runt den 22:a i varje månad med en månads fördröjning"; revideringar i tabellnoten (jan–mar 2022, maj 2023–jun 2024) | OK; gräns för läckage ≥ 32 d (t−1 vid deadline) |
| `el_contract_hourly_share` | 28 | ja | 23–24 (sep 2026 → 10-23, okt 2026 → 11-24 planerat) | SCB PxWeb `updated` TAB3571 (sep 2026 → 2026-10-23), scb.se/en0301 "Nästa publicering: 2026-11-24" (okt 2026), ei.se "Kunder per avtalstyp": "uppdateras runt den 22:a i varje månad med en månads fördröjning"; revideringar i tabellnoten (jan–mar 2022, maj 2023–jun 2024) | OK; gräns för läckage ≥ 32 d (t−1 vid deadline) |
| `el_contract_fixed_share` | 28 | ja | 23–24 (sep 2026 → 10-23, okt 2026 → 11-24 planerat) | SCB PxWeb `updated` TAB3571 (sep 2026 → 2026-10-23), scb.se/en0301 "Nästa publicering: 2026-11-24" (okt 2026), ei.se "Kunder per avtalstyp": "uppdateras runt den 22:a i varje månad med en månads fördröjning"; revideringar i tabellnoten (jan–mar 2022, maj 2023–jun 2024) | OK; gräns för läckage ≥ 32 d (t−1 vid deadline) |
| `el_contract_default_share` | 28 | ja | 23–24 (sep 2026 → 10-23, okt 2026 → 11-24 planerat) | SCB PxWeb `updated` TAB3571 (sep 2026 → 2026-10-23), scb.se/en0301 "Nästa publicering: 2026-11-24" (okt 2026), ei.se "Kunder per avtalstyp": "uppdateras runt den 22:a i varje månad med en månads fördröjning"; revideringar i tabellnoten (jan–mar 2022, maj 2023–jun 2024) | OK; gräns för läckage ≥ 32 d (t−1 vid deadline) |
| `el_grid_price_flat` | 0 | nej | −223 (2026 → 2026-05-22) | SCB PxWeb `updated` TAB3950 2026-05-22 (2026 års tariffer), kvalitetsdeklaration en0301_kd_2026_v1_20260522; docs/datakallor.md ("publiceras ~maj") | OK, konservativt: känd från 31 dec år Y. Bara 2026 är belagt; kvalitetsdeklarationen en0301_kd_2023_v1_20240925 tyder på att tidigare år kan ha kommit senare (t.ex. september). År Y okänt vid januari-deadline Y, känt vid Y+1 |
| `el_grid_price_house` | 0 | nej | −223 (2026 → 2026-05-22) | SCB PxWeb `updated` TAB3950 2026-05-22 (2026 års tariffer), kvalitetsdeklaration en0301_kd_2026_v1_20260522; docs/datakallor.md ("publiceras ~maj") | OK, konservativt: känd från 31 dec år Y. Bara 2026 är belagt; kvalitetsdeklarationen en0301_kd_2023_v1_20240925 tyder på att tidigare år kan ha kommit senare (t.ex. september). År Y okänt vid januari-deadline Y, känt vid Y+1 |
| `el_grid_price_house_heat` | 0 | nej | −223 (2026 → 2026-05-22) | SCB PxWeb `updated` TAB3950 2026-05-22 (2026 års tariffer), kvalitetsdeklaration en0301_kd_2026_v1_20260522; docs/datakallor.md ("publiceras ~maj") | OK, konservativt: känd från 31 dec år Y. Bara 2026 är belagt; kvalitetsdeklarationen en0301_kd_2023_v1_20240925 tyder på att tidigare år kan ha kommit senare (t.ex. september). År Y okänt vid januari-deadline Y, känt vid Y+1 |
| `el_grid_price_house_heat_unw` | 0 | nej | −223 (2026 → 2026-05-22) | SCB PxWeb `updated` TAB3950 2026-05-22 (2026 års tariffer), kvalitetsdeklaration en0301_kd_2026_v1_20260522; docs/datakallor.md ("publiceras ~maj") | OK, konservativt: känd från 31 dec år Y. Bara 2026 är belagt; kvalitetsdeklarationen en0301_kd_2023_v1_20240925 tyder på att tidigare år kan ha kommit senare (t.ex. september). År Y okänt vid januari-deadline Y, känt vid Y+1 |
| `ei_grid_fee_flat` | 0 | ja | −203 (arkivfil 2026 → 2026-06-11); −233 (2022–2026-filen → 2026-05-12) | ei.se "Nätavgifter – elnät": fil 2022–2026 daterad 2026-05-12, arkivfil 1999–2026 (den som hämtas) 2026-06-11 (tidsstämpel i länken, Last-Modified); sidan: sent beslut om myndighetsavgift 2026 gav blandad inrapportering | OK, konservativt: känd från 31 dec år Y (bara 2026 belagt). Rev.: ja, sena eller rättade inrapporteringar ändrar medianen (ej verifierat bakåt) |
| `ei_grid_fee_house` | 0 | ja | −203 (arkivfil 2026 → 2026-06-11); −233 (2022–2026-filen → 2026-05-12) | ei.se "Nätavgifter – elnät": fil 2022–2026 daterad 2026-05-12, arkivfil 1999–2026 (den som hämtas) 2026-06-11 (tidsstämpel i länken, Last-Modified); sidan: sent beslut om myndighetsavgift 2026 gav blandad inrapportering | OK, konservativt: känd från 31 dec år Y (bara 2026 belagt). Rev.: ja, sena eller rättade inrapporteringar ändrar medianen (ej verifierat bakåt) |
| `ei_grid_fee_house_heat` | 0 | ja | −203 (arkivfil 2026 → 2026-06-11); −233 (2022–2026-filen → 2026-05-12) | ei.se "Nätavgifter – elnät": fil 2022–2026 daterad 2026-05-12, arkivfil 1999–2026 (den som hämtas) 2026-06-11 (tidsstämpel i länken, Last-Modified); sidan: sent beslut om myndighetsavgift 2026 gav blandad inrapportering | OK, konservativt: känd från 31 dec år Y (bara 2026 belagt). Rev.: ja, sena eller rättade inrapporteringar ändrar medianen (ej verifierat bakåt) |
| `ei_grid_fee_raise_share` | 0 | ja | −203 (arkivfil 2026 → 2026-06-11); −233 (2022–2026-filen → 2026-05-12) | ei.se "Nätavgifter – elnät": fil 2022–2026 daterad 2026-05-12, arkivfil 1999–2026 (den som hämtas) 2026-06-11 (tidsstämpel i länken, Last-Modified); sidan: sent beslut om myndighetsavgift 2026 gav blandad inrapportering | OK, konservativt: känd från 31 dec år Y (bara 2026 belagt). Rev.: ja, sena eller rättade inrapporteringar ändrar medianen (ej verifierat bakåt) |

Rättelserna i TAB3571 läggs som sena releaser (`publication.LATE_RELEASES`): de ursprungliga, felaktiga
värdena finns inte kvar, så de rättade värdena räknas som kända först från rättelsedatum. Datum för
revideringen 2022 anges bara som "April 2022", så sista april används.

| Serie | Period | Releasedatum | Källa |
|---|---|---|---|
| `el_contract_*` | 2022-01 | 2022-04-30 | TAB3571 tabellnot: "In April 2022, revisions were made" (dag okänd, sista april) |
| `el_contract_*` | 2022-02 | 2022-04-30 | TAB3571 tabellnot: "In April 2022, revisions were made" (dag okänd, sista april) |
| `el_contract_*` | 2022-03 | 2022-04-30 | TAB3571 tabellnot: "In April 2022, revisions were made" (dag okänd, sista april) |
| `el_contract_*` | 2023-05 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2023-06 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2023-07 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2023-08 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2023-09 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2023-10 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2023-11 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2023-12 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2024-01 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2024-02 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2024-03 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2024-04 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2024-05 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
| `el_contract_*` | 2024-06 | 2024-09-27 | TAB3571 tabellnot: "2024-09-27 Data for May 2023 up to and including June 2024 has been corrected" |
