# Datakatalog

346 serier: 105 nationella och 241 länsserier. Genererad av `python -m kpif_nowcast.catalog`.

## Inflation

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `kpif_index` | KPIF, index | M | 1987-01–2026-10 | 15 d | nej | SCB TAB6590 | Målvariabeln. |
| `kpif_yy` | KPIF, årstakt | M | 1988-01–2026-10 | 15 d | nej | SCB TAB6590 | Målvariabeln. |
| `kpif_xe_index` | KPIF exkl. energi (KPIF-XE), index | M | 1987-01–2026-10 | 15 d | nej | SCB TAB6593 | Underliggande inflation utan energipriser. |
| `kpif_goods_index` | KPIF varor, index | M | 1987-01–2026-10 | 15 d | ja | SCB TAB6627 | Varudelen av KPIF, påverkas av import- och producentpriser. |
| `kpif_services_index` | KPIF tjänster, index | M | 1987-01–2026-10 | 15 d | ja | SCB TAB6627 | Tjänstedelen av KPIF, driven av löner och hyror. |
| `easter_window_days` | Påskens resefönster: dagar i månaden | M | 2000-01–2030-12 | -366 d | nej | Kalender (gregoriansk påsk) | Påskresor höjer priset på paketresor, flyg och logi; K7: ≈ 0,01 pe KPIF per dag. |
| `easter_sunday_in_month` | Påskdagen infaller i månaden | M | 2000-01–2030-12 | -366 d | nej | Kalender (gregoriansk påsk) | Skiljer tidig påsk (mars) från sen (april). |
| `kpif_package_holidays_index` | KPIF paketresor (COICOP 09.8), index | M | 1989-01–2026-10 | 15 d | ja | SCB TAB6613 (09.8) | Resekomponenterna som står för största delen av tjänstefelet (K7). |
| `kpif_air_transport_index` | KPIF persontransport med flyg (COICOP 07.3.3), index | M | 1987-01–2026-10 | 15 d | ja | SCB TAB6613 (07.3.3) | Resekomponenterna som står för största delen av tjänstefelet (K7). |
| `kpif_accommodation_index` | KPIF logitjänster (COICOP 11.2), index | M | 1987-01–2026-10 | 15 d | ja | SCB TAB6613 (11.2) | Resekomponenterna som står för största delen av tjänstefelet (K7). |

## Prisleden: producent-, import- och planerade priser

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `ppi_hmpi_consumer` | Hemmamarknadspriser, konsumtionsvaror | M | 1990-01–2026-09 | 30 d | ja | SCB TAB3184 | Producent- och importpriser föregår konsumentpriserna på varor med några månader. |
| `ppi_impi_consumer` | Importpriser, konsumtionsvaror | M | 1990-01–2026-09 | 30 d | ja | SCB TAB3184 | Producent- och importpriser föregår konsumentpriserna på varor med några månader. |
| `ppi_itpi_consumer` | Priser inhemsk tillgång, konsumtionsvaror | M | 1990-01–2026-09 | 30 d | ja | SCB TAB3184 | Producent- och importpriser föregår konsumentpriserna på varor med några månader. |
| `ppi_itpi_consumer_xfood` | Priser inhemsk tillgång, konsumtionsvaror exkl. livsmedel | M | 1990-01–2026-09 | 30 d | ja | SCB TAB3184 | Producent- och importpriser föregår konsumentpriserna på varor med några månader. |
| `ppi_hmpi_food` | Hemmamarknadspriser, livsmedel (SPIN 10) | M | 1990-01–2026-09 | 30 d | ja | SCB TAB3184 | Producent- och importpriser föregår konsumentpriserna på varor med några månader. |
| `ppi_impi_food` | Importpriser, livsmedel (SPIN 10) | M | 1990-01–2026-09 | 30 d | ja | SCB TAB3184 | Producent- och importpriser föregår konsumentpriserna på varor med några månader. |
| `ki_prices_grocery` | Prisplaner dagligvaruhandeln (nettotal) | M | 2003-05–2026-10 | 3 d | nej | KI Konjunkturbarometern Barhanm.px | Företagens planerade prisändringar kommande 3 månader. |
| `ki_prices_durables` | Prisplaner sällanköpshandeln (nettotal) | M | 2000-02–2026-10 | 3 d | nej | KI Konjunkturbarometern Barhanm.px | Företagens planerade prisändringar kommande 3 månader. |
| `ki_prices_retail` | Prisplaner detaljhandeln (nettotal) | M | 2003-05–2026-10 | 3 d | nej | KI Konjunkturbarometern Barhanm.px | Företagens planerade prisändringar kommande 3 månader. |
| `ki_purchase_prices_grocery` | Inköpspriser dagligvaruhandeln, kommande 3 mån (nettotal) | M | 2015-10–2026-10 | 3 d | nej | KI Konjunkturbarometern Barhanm.px | Företagens planerade prisändringar kommande 3 månader. |
| `ki_prices_food_industry` | Prisplaner livsmedelsindustrin, hemma (nettotal) | M | 2000-01–2026-10 | 3 d | nej | KI Konjunkturbarometern Barindm.px | Företagens planerade prisändringar kommande 3 månader. |
| `ki_prices_consumer_industry` | Prisplaner konsumtionsvaruindustrin, hemma (nettotal) | M | 2000-01–2026-10 | 3 d | nej | KI Konjunkturbarometern Barindm.px | Företagens planerade prisändringar kommande 3 månader. |

## Energi och råvaror

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `brent_sek` | Brent i kronor (dag 1–25) | M | 2000-01–2026-10 | 1 d | nej | FRED + Riksbanken | Drivmedelspriser samma månad. |
| `gas_eu_usd` | Naturgas Europa (TTF) | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED | Gas → elpris och industrins kostnader. |

## Arbetsmarknad och löner

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `aku_unemp_nsa` | Arbetslöshet (AKU), ej säsongsrensad | M | 2001-01–2026-10 | 25 d | ja | SCB TAB6387 | Resursutnyttjande → löner → tjänstepriser. |
| `aku_unemp_sa` | Arbetslöshet (AKU), säsongsrensad | M | 2001-01–2026-10 | 25 d | ja | SCB TAB6387 | Som ovan, lättare att läsa men revideras. |
| `wage_private_nonmanual` | Månadslön tjänstemän, privat sektor | M | 2008-01–2026-08 | 60 d | ja | SCB TAB2564 | Löner är den största kostnaden i tjänstesektorn. |
| `wage_private_manual_hourly` | Timlön arbetare, privat sektor (exkl. övertid) | M | 2008-01–2026-08 | 60 d | ja | SCB TAB2550 | Som ovan. Stark säsong, använd årsförändring. |
| `wage_municipal_yy` | Månadslön kommuner, årstakt (preliminär) | M | 1999-01–2026-08 | 60 d | ja | SCB TAB1972 | Offentliga löner och avgifter. |
| `labour_cost_salaried_yy` | Arbetskostnadsindex tjänstemän, årstakt | M | 2009-01–2026-08 | 60 d | ja | SCB TAB3657 | Total arbetskostnad inkl. avgifter. |
| `labour_cost_workers_yy` | Arbetskostnadsindex arbetare, årstakt | M | 2009-01–2026-08 | 60 d | ja | SCB TAB3657 | Som ovan. |
| `vacancies` | Lediga jobb, hela ekonomin (ej säsongsrensat) | Q | 2009-03–2026-06 | 60 d | nej | SCB TAB6406 | Stramhet på arbetsmarknaden → lönetryck. |
| `aku_employed` | Sysselsatta 15–74 år (AKU, ej säsongsrensat) | M | 2001-01–2026-10 | 25 d | ja | SCB TAB6389 | Sysselsättning och efterfrågan. |
| `nier_labour_shortage` | Brist på arbetskraft, näringslivet | Q | 1996-06–2026-12 | 3 d | nej | KI | Lönetryck. |
| `af_varsel` | Varsel om uppsägning (personer) | M | 1992-01–2026-10 | 15 d | ja | Arbetsförmedlingen, tidigare statistik (web-varsel-bransch) | Ledande indikator för arbetslöshet: varsel föregår uppsägningar med 2–6 månader. |
| `af_inskrivna_arbetslosa` | Inskrivna arbetslösa, Arbetsförmedlingen | M | 1996-01–2026-10 | 15 d | nej | Arbetsförmedlingen, tidigare statistik (web-sok-riket) | Registerbaserad arbetslöshet, mindre brus än AKU. Svagare arbetsmarknad → lägre löne- och tjänsteinflation. |
| `af_oppet_arbetslosa` | Öppet arbetslösa, Arbetsförmedlingen | M | 1996-01–2026-10 | 15 d | nej | Arbetsförmedlingen, tidigare statistik (web-sok-riket) | Arbetslösa utanför program; påverkas mindre av politiska programvolymer. |

## Hushållen

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. | Källa | Koppling |
|---|---|---|---|---|---|---|---|
| `hh_consumption_yy` | Hushållens konsumtion (indikator), volym årstakt | M | 2020-01–2026-10 | 45 d | ja | SCB TAB6932 | Efterfrågetryck. Hur mycket företagen kan föra vidare kostnader. |
| `retail_volume_yy` | Detaljhandelns försäljningsvolym exkl. drivmedel, årstakt | M | 1992-01–2026-09 | 30 d | ja | SCB TAB3948 | Varuefterfrågan. |
| `hh_infl_exp_median` | Hushållens förväntade inflation 12 mån, median | M | 2015-04–2026-10 | 3 d | nej | KI | Förväntningar påverkar lönekrav och acceptans för prishöjningar. |
| `hh_infl_perceived_median` | Hushållens upplevda inflation, median | M | 2015-04–2026-10 | 3 d | nej | KI | Hur hushållen upplever prisutvecklingen nu. |
| `hh_price_exp_net` | Hushållens prisförväntningar 12 mån (nettotal) | M | 1996-01–2026-10 | 3 d | nej | KI | Lång serie (1996) för förväntningar. |
| `hh_saving_rate` | Hushållens sparkvot (säsongsrensad) | Q | 1993-03–2026-06 | 60 d | ja | SCB TAB4591 | Högt sparande = svagare konsumtion framåt. |
| `nier_conf_households` | Hushållens konfidensindikator | M | 1996-01–2026-10 | 3 d | ja | KI | Hushållens framtidstro → konsumtion. |
| `guest_nights_total` | Gästnätter totalt (hotell, stugbyar, vandrarhem, camping) | M | 2001-01–2026-08 | 80 d | ja | Eurostat tour_occ_nim (TOTAL, I551-I553) | Efterfrågan på resor och logi; logi och paketresor är en stor del av tjänstefelet. |
| `guest_nights_domestic` | Gästnätter, svenska gäster | M | 2001-01–2026-08 | 80 d | ja | Eurostat tour_occ_nim (DOM, I551-I553) | Efterfrågan på resor och logi; logi och paketresor är en stor del av tjänstefelet. |
| `guest_nights_foreign` | Gästnätter, utländska gäster | M | 2001-01–2026-08 | 80 d | ja | Eurostat tour_occ_nim (FOR, I551-I553) | Efterfrågan på resor och logi; logi och paketresor är en stor del av tjänstefelet. |
| `guest_nights_hotel` | Gästnätter på hotell | M | 1990-01–2026-08 | 80 d | ja | Eurostat tour_occ_nim (TOTAL, I551) | Efterfrågan på resor och logi; logi och paketresor är en stor del av tjänstefelet. |

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
| `gdp_ind_yy` | BNP-indikatorn, årstakt (kalenderjusterad) | M | 2001-01–2026-09 | 45 d | ja | SCB TAB443 | Efterfrågetryck i ekonomin. |
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
| `ea_hicp_total` | Euroområdet, inflation (HIKP), slutlig | M | 1997-01–2026-10 | 26 d | ja | Eurostat prc_hicp_minr | Lång historik (1997) för omvärldens inflation. |
| `fao_food_idx` | FAO:s livsmedelsprisindex | M | 1990-01–2026-10 | 10 d | ja | FAO | Världsmarknadspriser på mat → svenska matpriser med 3–9 mån. |
| `fao_cereals` | FAO spannmålsprisindex | M | 1990-01–2026-10 | 10 d | ja | FAO | Spannmål → bröd, foder, kött. |
| `fao_dairy` | FAO mejeriprisindex | M | 1990-01–2026-10 | 10 d | ja | FAO | Mejeripriser. |
| `wheat_usd` | Vete, världsmarknadspris | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED | Livsmedelskedjan. |
| `gscpi` | Global Supply Chain Pressure Index | M | 1998-01–2026-10 | 22 d | ja | NY Fed | Flaskhalsar i globala leveranskedjor → varupriser (2021–22). |
| `freight_ppi_deepsea` | Fraktpriser sjöfart (US PPI) | M | 1988-06–2026-10 | 21 d | ja | BLS via FRED | Fraktkostnader → importpriser. |
| `coffee_usd` | Kaffe (arabica, other mild), världsmarknadspris | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED PCOFFOTMUSDM | Råvarupriser → svenska livsmedelspriser med fördröjning. |
| `cocoa_usd` | Kakao, världsmarknadspris | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED PCOCOUSDM | Råvarupriser → svenska livsmedelspriser med fördröjning. |
| `sugar_usd` | Socker, världsmarknad, världsmarknadspris | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED PSUGAISAUSDM | Råvarupriser → svenska livsmedelspriser med fördröjning. |
| `beef_usd` | Nötkött, världsmarknadspris | M | 2010-05–2026-09 | 60 d | ja | IMF via FRED PBEEFUSDM | Råvarupriser → svenska livsmedelspriser med fördröjning. |
| `pork_usd` | Griskött, världsmarknadspris | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED PPORKUSDM | Råvarupriser → svenska livsmedelspriser med fördröjning. |
| `poultry_usd` | Fågel, världsmarknadspris | M | 2003-01–2026-09 | 60 d | ja | IMF via FRED PPOULTUSDM | Råvarupriser → svenska livsmedelspriser med fördröjning. |
| `palm_oil_usd` | Palmolja, världsmarknadspris | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED PPOILUSDM | Råvarupriser → svenska livsmedelspriser med fördröjning. |
| `soy_oil_usd` | Sojaolja, världsmarknadspris | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED PSOILUSDM | Råvarupriser → svenska livsmedelspriser med fördröjning. |
| `rapeseed_oil_usd` | Rapsolja, världsmarknadspris | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED PROILUSDM | Råvarupriser → svenska livsmedelspriser med fördröjning. |
| `sunflower_oil_usd` | Solrosolja, världsmarknadspris | M | 1992-01–2026-09 | 60 d | ja | IMF via FRED PSUNOUSDM | Råvarupriser → svenska livsmedelspriser med fördröjning. |

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
| `gvb_2y` | Statsobligationsränta 2 år | M | 1987-01–2026-10 | 1 d | nej | Riksbanken SWEA SEGVB2YC | Marknadens ränteförväntningar och finansiella villkor. |
| `gvb_5y` | Statsobligationsränta 5 år | M | 1987-01–2026-10 | 1 d | nej | Riksbanken SWEA SEGVB5YC | Marknadens ränteförväntningar och finansiella villkor. |
| `gvb_10y` | Statsobligationsränta 10 år | M | 1987-01–2026-10 | 1 d | nej | Riksbanken SWEA SEGVB10YC | Marknadens ränteförväntningar och finansiella villkor. |
| `swestr` | SWESTR (dagslåneränta) | M | 2021-09–2026-10 | 1 d | nej | Riksbanken SWESTR API | Kortränta som styrräntan styr; från 2021-09. |

## Regionalt: län

En serie per mått och län: `region_<mått>_<länskod>` (01 Stockholm … 25 Norrbotten, 00 riket). Bara deskriptivt, ingår inte i de nationella kandidatlistorna. Kvalitet: `docs/auto2/k4/kvalitet.md`.

| Mått | Serie | Frekv. | Från–till (riket) | Län | Fördröjning | Rev. | Källa | Anmärkning |
|---|---|---|---|---|---|---|---|---|
| `region_af_andel_*` | Inskrivna arbetslösa, andel av arbetskraften (AF) | M | 2023-01–2026-10 | 21 | 15 d | ja | Arbetsförmedlingen, tidigare statistik (web-Inskrivna-arbetslosa-andel-av-bas) | Från 2023-01. Arbetskraft från SCB:s BAS (16–65 år 2023–2025, 16–66 år från 2026). revised=True: nämnaren kan uppdateras när ny BAS-årgång kommer (inte verifierat). |
| `region_af_andel_ak08_*` | Inskrivna arbetslösa, andel av registerbaserad arbetskraft (AF, äldre bas) | M | 2008-01–2023-12 | 21 | 15 d | nej | Arbetsförmedlingen, tidigare statistik (web-inskrivna-arbetslosa-andel-av-reg-ak2008-2023-12) | 2008-01–2023-12, avslutad. Annan nämnare än af_andel: brott 2023, se kvalitet.md. |
| `region_af_inskrivna_*` | Inskrivna arbetslösa (AF) | M | 1996-01–2026-10 | 21 | 15 d | nej | Arbetsförmedlingen, tidigare statistik (web-sok-lan-kom) | Från 1996-01. Åldersbrott 16–64 / 16–65 (2023–2025) / 16–66 (2026–). Riket inkl. okänt län. |
| `region_af_oppet_*` | Öppet arbetslösa (AF) | M | 1996-01–2026-10 | 21 | 15 d | nej | Arbetsförmedlingen, tidigare statistik (web-sok-lan-kom) | Som af_inskrivna. |
| `region_af_varsel_*` | Varsel om uppsägning, personer (AF) | M | 1992-01–2026-03 | 21 | 15 d | ja | Arbetsförmedlingen, tidigare statistik (web-varsel-lan) | 1992-01–2026-03: AF uppdaterar inte filen efter 2026-03 (BLOCKED därefter). Län efter företagets organisationsnummer. Riket inkl. 'Inga uppgifter'. |
| `region_bas_arbetsloshet_*` | Arbetslöshet 20–65 år (SCB BAS) | M | 2024-01–2026-08 | 21 | 60 d | ja | SCB TAB5663 | Från 2024-01, preliminär statistik. |
| `region_aku_arbetsloshet_*` | Arbetslöshet 15–74 år (AKU) | Q | 2005-03–2026-09 | 21 | 30 d | ja | SCB TAB2923 | Från 2005K1. Beräknad som arbetslösa/(arbetslösa+sysselsatta) ur tusental; ej säsongsrensad. Stor osäkerhet i små län (SCB anger felmarginal). |
| `region_smahus_pris_*` | Försålda småhus, köpeskilling medelvärde | Q | 1998-03–2026-09 | 21 | 30 d | ja | SCB TAB1167 | Från 1998K1. Medelpris, inte kvalitetsjusterat: påverkas av vilka hus som säljs. Senaste kvartalet preliminärt. |
| `region_fpi_smahus_*` | Fastighetsprisindex permanenta småhus (1990=100) | A | 1990-12–2025-12 | 20 | 180 d | ja | SCB TAB1148 | 1990–2025. Kalmar och Gotland redovisas tillsammans (0809). |
| `region_konkurser_*` | Konkurser, antal | M | 1996-01–2026-10 | 21 | 10 d | nej | Tillväxtanalys 11_konkurser_manad_lan | Från 1996-01. Riket = summan av länen. |
| `region_befolkning_*` | Folkmängd | M | 2000-01–2026-09 | 21 | 45 d | nej | SCB TAB1625 + TAB6473 | Från 2000-01, vid månadens slut. |

### Länsserier: täckning per län

| Kod | Län | `af_andel` | `af_andel_ak08` | `af_inskrivna` | `af_oppet` | `af_varsel` | `bas_arbetsloshet` | `aku_arbetsloshet` | `smahus_pris` | `fpi_smahus` | `konkurser` | `befolkning` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 00 | Riket | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 01 | Stockholm | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 03 | Uppsala | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 04 | Södermanland | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 05 | Östergötland | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 06 | Jönköping | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 07 | Kronoberg | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-06–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 08 | Kalmar | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-06 | 1998-03–2026-09 |  | 1996-01–2026-10 | 2000-01–2026-09 |
| 09 | Gotland | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-06–2016-06 | 1998-03–2026-09 |  | 1996-01–2026-10 | 2000-01–2026-09 |
| 10 | Blekinge | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 12 | Skåne | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 13 | Halland | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 14 | Västra Götaland | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 17 | Värmland | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 18 | Örebro | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 19 | Västmanland | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 20 | Dalarna | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 21 | Gävleborg | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 22 | Västernorrland | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 23 | Jämtland | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 24 | Västerbotten | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-09 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 25 | Norrbotten | 2023-01–2026-10 | 2008-01–2023-12 | 1996-01–2026-10 | 1996-01–2026-10 | 1992-01–2026-03 | 2024-01–2026-08 | 2005-03–2026-06 | 1998-03–2026-09 | 1990-12–2025-12 | 1996-01–2026-10 | 2000-01–2026-09 |
| 0809 | Kalmar och Gotland |  |  |  |  |  |  |  |  | 1990-12–2025-12 |  |  |

