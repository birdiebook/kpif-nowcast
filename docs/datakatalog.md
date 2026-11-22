# Datakatalog

64 serier. Genererad av `python -m kpif_nowcast.catalog`.

## Inflation

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `kpif_index` | KPIF, index | M | 1987-01–2026-10 | 15 d | nej | SCB TAB6590 | Målvariabeln. |
| `kpif_yy` | KPIF, årstakt | M | 1988-01–2026-10 | 15 d | nej | SCB TAB6590 | Målvariabeln. |

## Energi och råvaror

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `brent_sek` | Brent i kronor (dag 1–25) | M | 2000-01–2026-10 | 1 d | nej | FRED + Riksbanken | Drivmedelspriser samma månad. |
| `gas_eu_usd` | Naturgas Europa (TTF) | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED | Gas → elpris och industrins kostnader. |

## Arbetsmarknad och löner

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `aku_unemp_nsa` | Arbetslöshet (AKU), ej säsongsrensad | M | 2001-01–2026-10 | 25 d | nej | SCB TAB6387 | Resursutnyttjande → löner → tjänstepriser. |
| `aku_unemp_sa` | Arbetslöshet (AKU), säsongsrensad | M | 2001-01–2026-10 | 25 d | ja | SCB TAB6387 | Som ovan, lättare att läsa men revideras. |
| `wage_private_nonmanual` | Månadslön tjänstemän, privat sektor | M | 2008-01–2026-08 | 60 d | ja | SCB TAB2564 | Löner är den största kostnaden i tjänstesektorn. |
| `wage_private_manual_hourly` | Timlön arbetare, privat sektor (exkl. övertid) | M | 2008-01–2026-08 | 60 d | ja | SCB TAB2550 | Som ovan. Stark säsong, använd årsförändring. |
| `wage_municipal_yy` | Månadslön kommuner, årstakt (preliminär) | M | 1999-01–2026-08 | 60 d | ja | SCB TAB1972 | Offentliga löner och avgifter. |
| `labour_cost_salaried_yy` | Arbetskostnadsindex tjänstemän, årstakt | M | 2009-01–2026-08 | 60 d | ja | SCB TAB3657 | Total arbetskostnad inkl. avgifter. |
| `labour_cost_workers_yy` | Arbetskostnadsindex arbetare, årstakt | M | 2009-01–2026-08 | 60 d | ja | SCB TAB3657 | Som ovan. |
| `vacancies` | Lediga jobb, hela ekonomin (ej säsongsrensat) | Q | 2009-03–2026-06 | 60 d | nej | SCB TAB6406 | Stramhet på arbetsmarknaden → lönetryck. |
| `aku_employed` | Sysselsatta 15–74 år (AKU, ej säsongsrensat) | M | 2001-01–2026-10 | 25 d | nej | SCB TAB6389 | Sysselsättning och efterfrågan. |
| `nier_labour_shortage` | Brist på arbetskraft, näringslivet | Q | 1996-06–2026-12 | 3 d | nej | KI | Lönetryck. |

## Hushållen

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `hh_consumption_yy` | Hushållens konsumtion (indikator), volym årstakt | M | 2020-01–2026-10 | 15 d | ja | SCB TAB6932 | Efterfrågetryck. Hur mycket företagen kan föra vidare kostnader. |
| `retail_volume_yy` | Detaljhandelns försäljningsvolym exkl. drivmedel, årstakt | M | 1992-01–2026-09 | 30 d | ja | SCB TAB3948 | Varuefterfrågan. |
| `hh_infl_exp_median` | Hushållens förväntade inflation 12 mån, median | M | 2015-04–2026-10 | 3 d | nej | KI | Förväntningar påverkar lönekrav och acceptans för prishöjningar. |
| `hh_infl_perceived_median` | Hushållens upplevda inflation, median | M | 2015-04–2026-10 | 3 d | nej | KI | Hur hushållen upplever prisutvecklingen nu. |
| `hh_price_exp_net` | Hushållens prisförväntningar 12 mån (nettotal) | M | 1996-01–2026-10 | 3 d | nej | KI | Lång serie (1996) för förväntningar. |
| `hh_saving_rate` | Hushållens sparkvot (säsongsrensad) | Q | 1993-03–2026-06 | 60 d | ja | SCB TAB4591 | Högt sparande = svagare konsumtion framåt. |
| `nier_conf_households` | Hushållens konfidensindikator | M | 1996-01–2026-10 | 3 d | ja | KI | Hushållens framtidstro → konsumtion. |

## Bostäder och krediter

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `house_price_idx` | Fastighetsprisindex, småhus | Q | 1986-03–2026-09 | 30 d | ja | SCB TAB1150 | Förmögenhetseffekt på konsumtionen. |
| `mortgage_rate_new` | Bolåneränta, nya avtal (alla bindningstider) | M | 2005-09–2026-09 | 30 d | nej | SCB TAB5783 | Penningpolitikens genomslag på hushållen. |
| `hh_lending_growth` | Utlåning till hushåll, årstakt | M | 2006-01–2026-09 | 30 d | nej | SCB TAB4514 | Kreditcykel → efterfrågan. |
| `nfc_lending_growth` | Utlåning till icke-finansiella företag, årstakt | M | 2006-01–2026-09 | 30 d | nej | SCB TAB4514 | Investeringar och kreditvillkor. |
| `housing_starts` | Påbörjade bostäder (fler- och småhus) | Q | 1975-03–2026-06 | 60 d | ja | SCB TAB4572 | Byggcykeln och byggkostnadstryck. |
| `rent_change` | Hyresförändring, hyresrätter | A | 1969-12–2026-12 | -60 d | nej | SCB TAB6051 | Hyror är en stor och trög del av KPIF. Förhandlas i förväg. |

## Företagen

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `gdp_ind_yy` | BNP-indikatorn, årstakt (kalenderjusterad) | M | 2001-01–2026-09 | 35 d | ja | SCB TAB443 | Efterfrågetryck i ekonomin. |
| `ki_services` | Prisplaner tjänstesektorn (nettotal) | M | 2003-04–2026-10 | 3 d | nej | KI Konjunkturbarometern | Företagens planerade prishöjningar kommande 3 mån. |
| `nier_barometer` | Barometerindikatorn (KI) | M | 1996-07–2026-10 | 3 d | ja | KI | Samlad bild av efterfrågeläget. |
| `nier_conf_services` | Konfidensindikator tjänstesektorn | M | 1996-01–2026-10 | 3 d | ja | KI | Tjänsteefterfrågan → tjänstepriser. |
| `nier_conf_trade` | Konfidensindikator handeln | M | 1996-07–2026-10 | 3 d | ja | KI | Handelns läge → varupriser. |
| `nier_capacity_util_mfg` | Kapacitetsutnyttjande industrin | Q | 1996-06–2026-12 | 3 d | nej | KI | Resursutnyttjande (outputgap). |
| `nier_firm_infl_exp_old` | Företagens förväntade inflation 12 mån (gammal metod) | Q | 1987-09–2026-09 | 3 d | nej | KI | Inflationsförväntningar styr prissättning. |
| `nier_firm_infl_exp_new` | Företagens förväntade inflation 12 mån (ny metod) | Q | 2026-12–2026-12 | 3 d | nej | KI | Som ovan, från 2026K4. |
| `bankruptcies` | Konkurser, antal (alla branscher) | M | 2009-01–2026-10 | 10 d | nej | Tillväxtanalys | Finansiell stress och svag efterfrågan. |
| `ipi_yy` | Industriproduktion (B–D), årstakt | M | 2001-01–2026-09 | 45 d | ja | SCB TAB1872 | Varusidans aktivitet. |
| `service_prod_idx` | Tjänsteproduktionsindex (ej kalenderjusterat) | M | 2000-01–2026-09 | 45 d | ja | SCB TAB3854 | Tjänsteefterfrågan. |
| `industry_orders_yy` | Orderingång industrin, årstakt | M | 2001-01–2026-09 | 45 d | ja | SCB TAB1710 | Ledande indikator för varuefterfrågan. |

## Omvärlden

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `ea_flash_total` | Euroområdet, inflation snabbestimat: totalt | M | 2017-08–2026-10 | 2 d | nej | Eurostat prc_hicp_fp/fpd (FLS) | Publiceras före vår deadline. Gemensamma rörelser i energi, mat, varor. |
| `ea_flash_energy` | Euroområdet, inflation snabbestimat: energi | M | 2017-08–2026-10 | 2 d | nej | Eurostat prc_hicp_fp/fpd (FLS) | Publiceras före vår deadline. Gemensamma rörelser i energi, mat, varor. |
| `ea_flash_food` | Euroområdet, inflation snabbestimat: livsmedel | M | 2017-08–2026-10 | 2 d | nej | Eurostat prc_hicp_fp/fpd (FLS) | Publiceras före vår deadline. Gemensamma rörelser i energi, mat, varor. |
| `ea_flash_goods` | Euroområdet, inflation snabbestimat: industrivaror | M | 2017-08–2026-10 | 2 d | nej | Eurostat prc_hicp_fp/fpd (FLS) | Publiceras före vår deadline. Gemensamma rörelser i energi, mat, varor. |
| `ea_flash_services` | Euroområdet, inflation snabbestimat: tjänster | M | 2017-08–2026-10 | 2 d | nej | Eurostat prc_hicp_fp/fpd (FLS) | Publiceras före vår deadline. Gemensamma rörelser i energi, mat, varor. |
| `ea_hicp_total` | Euroområdet, inflation (HIKP), slutlig | M | 1997-01–2026-10 | 20 d | ja | Eurostat prc_hicp_minr | Lång historik (1997) för omvärldens inflation. |
| `fao_food_idx` | FAO:s livsmedelsprisindex | M | 1990-01–2026-10 | 8 d | ja | FAO | Världsmarknadspriser på mat → svenska matpriser med 3–9 mån. |
| `fao_cereals` | FAO spannmålsprisindex | M | 1990-01–2026-10 | 8 d | ja | FAO | Spannmål → bröd, foder, kött. |
| `fao_dairy` | FAO mejeriprisindex | M | 1990-01–2026-10 | 8 d | ja | FAO | Mejeripriser. |
| `wheat_usd` | Vete, världsmarknadspris | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED | Livsmedelskedjan. |
| `gscpi` | Global Supply Chain Pressure Index | M | 1998-01–2026-10 | 22 d | ja | NY Fed | Flaskhalsar i globala leveranskedjor → varupriser (2021–22). |
| `freight_ppi_deepsea` | Fraktpriser sjöfart (US PPI) | M | 1988-06–2026-10 | 15 d | ja | BLS via FRED | Fraktkostnader → importpriser. |

## AI och produktivitet

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `hours_worked_yy` | Arbetade timmar (nationalräkenskaper), årstakt | Q | 1981-03–2026-06 | 60 d | ja | SCB TAB4643 | Nämnare i produktiviteten (BNP per timme). |
| `gdp_real_q` | BNP, fasta priser (produktionssidan) | Q | 1981-03–2026-06 | 60 d | ja | SCB TAB3112 | Täljare i produktiviteten. |
| `hours_worked_q` | Arbetade timmar, hela ekonomin | Q | 1980-03–2026-06 | 60 d | ja | SCB TAB4643 | Nämnare i produktiviteten. |
| `lp_hour_yy_se` | Arbetsproduktivitet per timme, Sverige, årstakt | Q | 1994-03–2026-06 | 60 d | ja | Eurostat namq_10_lp_ulc | Högre produktivitet sänker enhetsarbetskostnaden → lägre inflationstryck. AI:s väg in i makro. |
| `lp_hour_yy_ea` | Arbetsproduktivitet per timme, euroområdet, årstakt | Q | 1996-03–2026-06 | 60 d | ja | Eurostat namq_10_lp_ulc | Jämförelse för Sverige. |
| `software_investment_q` | Investeringar i programvara och databaser, fasta priser | Q | 1981-03–2026-06 | 60 d | ja | SCB TAB3108 | Digitala/AI-investeringar som ledande signal för produktivitet. |
| `ai_use_firms_se` | Företag som använder AI, Sverige (10+ anställda) | A | 2021-12–2025-12 | 345 d | nej | Eurostat isoc_eb_ai | AI-spridningen i näringslivet. |
| `ai_use_firms_eu` | Företag som använder AI, EU27 (10+ anställda) | A | 2021-12–2025-12 | 345 d | nej | Eurostat isoc_eb_ai | Jämförelse för Sverige. |
| `jobads_total` | Publicerade platsannonser (Platsbanken) | M | 2016-01–2026-10 | 3 d | nej | JobTech historical ads | Nämnare för AI-andelen. Även en signal för efterfrågan på arbetskraft. |
| `jobads_ml` | Platsannonser som nämner "maskininlärning" | M | 2016-01–2026-10 | 3 d | nej | JobTech historical ads | Efterfrågan på AI-kompetens. |
| `jobads_ai` | Platsannonser som nämner "AI" | M | 2016-01–2026-10 | 3 d | nej | JobTech historical ads | Efterfrågan på AI-kompetens. |

## Penningpolitik och krona

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `kix` | Kronindex KIX (högre = svagare krona) | M | 1992-11–2026-10 | 1 d | nej | Riksbanken SWEA | Svagare krona → dyrare import med fördröjning. |
| `policy_rate` | Styrränta | M | 1994-06–2026-10 | 1 d | nej | Riksbanken SWEA | Stramare penningpolitik dämpar efterfrågan. |

