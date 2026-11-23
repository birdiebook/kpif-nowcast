# K11 Oberoende granskning av publiceringsfördröjningar och datakvalitet

**Dom: fel som påverkar.** <!--DOM-->

Granskat 2026-11-23 av en agent som inte skrev katalogen. 0 modellvarianter (omkörningen av K2 är en rättning).
Låsning: [docs/publiceringskalender.md](../../publiceringskalender.md) + `tests/test_publication_calendar.py`.

## Metod

Deadline för målmånad t är dag 4 i t+1 (`riksbank_benchmark.deadline`). `known_from = periodens slut + lag_days`
och `as_of` tar med värden med `known_from <= deadline`. Därför spelar en fördröjning bara roll vid vissa gränser:

| lag_days | Period modellen ser vid deadline | Läckage om verklig publicering sker senare än |
|---|---|---|
| ≤ 4 | t | dag 4 i t+1 |
| 5–32 | t−1 | dag 4 i t+1 (32–35 d efter t−1, beror på månadens längd) |
| 35 | t−1 i månader med 31 dagar, annars t−2 | dag 4 i t+1 (35 d) |
| 36–63 | t−2 | dag 4 i t+1 (≥ 63 d) |

För varje serie jämfördes antagen fördröjning med belagd fördröjning från officiella källor: SCB PxWeb v2
`updated`/`lastPeriod` (senaste publiceringen, en per tabell), SCB:s statistiknyheter (historiska datum),
KI:s publikationslista (34 barometrar 2024–2026), Eurostats euro-indikatorer (releasekoden `2-DDMMYYYY-ap`
innehåller datumet; alla flashmånader 2017-08..2026-10 provades för dag 4–7), FAO:s releasekalender 2026, BLS
historiska releasedatum för PPI, FRED-sidor och Riksbankens beslutsdatum. Inga stora hämtningar (råfiler i
`data/raw/k11/`, inte i git).

## Fel som påverkar (läckage)

Fyra serier hade för kort fördröjning så att modellen vid deadline såg en period som inte var publicerad.
Alla fyra ingår i K2:s feature-mängd L; euroområdets flash ingår även i `ea_news` (mängd S, och J1).

| Serie | Antagen | Belagd | Belägg (stickprov) | Läckande målmånader 2015–2026 |
|---|---|---|---|---|
| `gdp_ind_yy` (BNP-indikatorn) | 35 d | 38–41 d vanliga månader, 28–30 d kvartalets sista månad | SCB statistiknyheter: nov 2022 → 2023-01-10, jul 2023 → 2023-09-08, jan 2024 → 2024-03-08, feb 2024 → 2024-04-10, apr 2024 → 2024-06-10, okt 2024 → 2024-12-10, feb 2025 → 2025-04-10, maj 2025 → 2025-07-10, aug 2025 → 2025-10-10, jul 2026 → 2026-09-10, aug 2026 → 2026-10-09; kvartalsslut: jun 2022 → 07-28, sep 2023 → 10-30, dec 2023 → 01-29, mar 2024 → 04-29, sep 2025 → 10-29, sep 2026 → 10-29 | mars, maj, augusti, december (35 d når dag 4 bara efter en 31-dagarsmånad; då sågs t−1 som i själva verket kom dag 8–10) |
| `hh_consumption_yy` (hushållens konsumtionsindikator, TAB6932) | 15 d | ny metod 10–13 d från 2026; den gamla indikatorn ca 40 d | SCB: maj 2026 → 2026-06-10, okt 2026 → 2026-11-11/13 (PxWeb `updated`); SCB 2026-05: månads- och veckoindikatorn slås ihop med ny metod (moms- och kortdata), serierna börjar 2019; den gamla indikatorn publicerades med BNP-indikatorn (aug 2025 → 2025-10-10) | alla månader 2019–2026-05: t−1 sågs, i verkligheten fanns bara t−2 (och då med gammal metod) |
| `ea_flash_*` (5 serier) | 2 d | −1 till +7 d; **december 4–7 d** | Eurostat releasekoder: dec 2017 → 2018-01-05, dec 2018 → 2019-01-04, dec 2019 → 2020-01-07, dec 2020 → 2021-01-07, dec 2021 → 2022-01-07, dec 2022 → 2023-01-06, dec 2023 → 2024-01-05, dec 2024 → 2025-01-07, dec 2025 → 2026-01-07; övriga månader <!--EAOVR--> | december 2017, 2019–2025 (8 månader): decemberflash användes för december fast den kom 1–3 dagar efter deadline |
| `freight_ppi_deepsea` (BLS PPI via FRED) | 15 d | 8–20 d normalt; 30–75 d sep–dec 2025 | BLS *Historical release dates for the PPI*: normala releaser dag 8–20 (januari ofta 13–20); not 8–11: sep 2025 → 2025-11-25, okt 2025 → 2026-01-14, nov 2025 → 2026-01-14, dec 2025 → 2026-01-30 | 2025-10, 2025-11, 2025-12 (shutdown) |

Rättning: `gdp_ind_yy` och `hh_consumption_yy` 45 d (avrundat mot senare; kvartalsslutens snabbare BNP-indikator
och den nya konsumtionsindikatorns 10–13 d utnyttjas därmed inte, vilket är konservativt). `ea_flash_*` och
`freight_ppi_deepsea` får sina faktiska releasedatum i `publication.py` (`known_from = max(slut + lag, release)`),
frakt-PPI dessutom 21 d.

## Fel som inte påverkar

Antagen fördröjning kortare än belagd, men utan läckage eftersom samma period syns vid deadline ändå (rättade
för att följa regeln "avrunda mot senare"; inga feature-värden ändras):

| Serie | Antagen → ny | Belagd | Belägg |
|---|---|---|---|
| `ea_hicp_total` | 20 → 26 | 17–25 d | Eurostat: dec 2023 → 2024-01-17, dec 2025 → 2026-01-19, jan 2026 → 2026-02-25 |
| `fao_food_idx`, `fao_cereals`, `fao_dairy` | 8 → 10 | 2–9 d | FAO:s releasekalender 2026 (dec 2025 → 9 jan, övriga 2–8) |

Granskade och OK (detaljer per serie i [publiceringskalender.md](../../publiceringskalender.md)): KPIF-serierna
(12 d), AKU (16–20 d mot 25), löner/AKI (59–60 d mot 60; gräns ≥ 63), detaljhandel (20–30 d mot 30; gräns ≥ 32),
bolåneränta och utlåning (27 d), IPI/tjänsteproduktion/order (41 d mot 45), PPI (26 d mot 30), alla KI-serier
(publiceras dag 19–30 i mätmånaden, 34 releaser 2024–2026, antaget 3 d efter), Riksbankens dagliga serier,
Brent (veckovis på FRED, dag 1–25 finns före dag 4), IMF-råvaror (ca 22 d mot 60), GSCPI, konkurser (5 d mot 10),
kvartalsserierna (59 d mot 60). Riksbankens prognosdatum (`published`) stämmer med besluten
(2023-11-23, 2024-03-27, 2025-09-23).

Marginaler värda att känna till: löner 59–60 d mot 60 (gränsen för läckage är ≥ 63 d, så ofarligt även om SCB
publicerar en dag senare), detaljhandel 29–30 d mot 30 (gräns ≥ 32).

## revised-flaggor

| Serie | Flagga | I praktiken | Åtgärd |
|---|---|---|---|
| `aku_unemp_nsa`, `aku_employed` | nej | 2001–2020 är *länkade data* efter SCB:s omläggning 2021 (TAB6387/6389, tabellnot), inte det som publicerades då | **nej → ja** |
| `aku_unemp_sa` | ja | som ovan + säsongsrensning | OK |
| `hh_consumption_yy`, `gdp_ind_yy` | ja | serierna är bakåtskattade (TAB6932 med ny metod från 2026, BNP-indikatorn med senaste NR) | OK, och värdena 2019–2026 fanns inte i denna form i realtid |
| `kpif_*`, `kpif_xe_index` | nej | KPI revideras inte | OK |
| `kpif_goods_index`, `kpif_services_index` | ja | COICOP 2018-omräkning | OK |
| `ea_flash_*` | nej | första publicering, fryst | OK |
| KI-nettotal (`ki_*`, `hh_*` från KI) | nej | ej säsongsrensade nettotal revideras inte | OK (inte verifierat mot vintages) |
| KI-indikatorer (`nier_*`) | ja | säsongsrensade | OK |
| `mortgage_rate_new`, `*_lending_growth` | nej | finansmarknadsstatistiken korrigeras ibland | lämnat; inte belagt |
| `bankruptcies` | nej | Tillväxtanalys senaste månader kan kompletteras | lämnat; inte belagt |
| `jobads_*` | nej | rekonstruktion från JobTech historical (ingen realtidsvintage) | lämnat; öppen fråga |
| Riksbanken, Brent | nej | marknadsdata | OK |

Ingen vintagehistorik finns i observationstabellen (bara backfill + två dagars hämtningar, inga
revisionsrader), så revideringar gick inte att mäta direkt; bedömningen bygger på källornas dokumentation.
Flaggändringen påverkar inte de frysta varianterna (L använder alla serier), bara K2:s diagnostik
`k2_avg_ridge_lnr` (som nu skulle utesluta 26 i stället för 24 serier) och J3/K0:s revised-kolumn.

## Omkörning av K2:s frysta varianter

**Reproduktion först.** Med lagrad data och K2:s feature-mängd (43 katalogserier) återskapas K2 exakt
(ridge_l 0,1989, ens_s 0,2009, ridge_s 0,2064; Holm 0,014 / 0,055 / 0,083). Men `k2_ml` på main @ 51fa62f
ger inte K2:s variant: `catalog_keys()` tog *alla* månadsserier i katalogen, så L växte från 43 till 72 när K0:s
prisledsserier mergades. Då blir `k2_avg_ridge_l` 0,2025 (Holm 0,095) redan utan rättning. **Rättat:** L är nu
fryst till K2:s 43 serier (`k2_ml.L_KEYS`, test i `test_publication_calendar.py`).

**Ändrade feature-celler** (målmånader 2015-02..2026-10, `python -m kpif_nowcast.k11_audit diff`):
`cat_gdp_ind_yy` 81 månader, `cat_hh_consumption_yy` 80, `cat_ea_flash_*` 6–8 (decembrar), `ea_news` 7
(decembrar, påverkar även S-varianterna), `cat_freight_ppi_deepsea` 3 (2025-10..12). Inga andra.

**Resultat 2015-02..2026-10, n = 141** (DM ensidigt mot 50/50-snittet, Holm över K2:s 8 varianter, samma
protokoll som K2; `k2_rerun_k2set_raw.md` / `k2_rerun_k2set_corrected.md`):

| Variant | MAE före | MAE efter | p rå före → efter | Holm före → efter | Skärmen (Holm < 0,10 och 2024–26 ≤ 50/50) |
|---|---|---|---|---|---|
| `k2_avg_ridge_l` | 0,1989 | **0,2000** | 0,002 → 0,002 | 0,014 → **0,018** | klarar fortfarande |
| `k2_avg_ens_s` | 0,2009 | **0,2020** | 0,008 → 0,012 | 0,055 → **0,082** | klarar fortfarande |
| `k2_avg_ridge_s` | 0,2064 | **0,2073** | 0,014 → 0,022 | 0,083 → **0,132** | **klarar inte längre** |
| 50/50 (referens) | 0,2165 | 0,2165 | | | |

Mot `rb_updated`: Holm 0,039 / 0,040 / 0,045 efter rättning (alla tre < 0,05). 2018-02..2026-10 (ML aktiv,
n = 105): 0,213 / 0,216 / 0,223 mot 50/50 0,235 (Holm 0,011 / 0,068 / 0,118). 2024–26 (använd, n = 34): 0,230 /
0,218 / 0,227 mot 0,246, inget signifikant (Holm ≥ 0,35); alla tre fortfarande lägre än 50/50.

Med L = 72 serier (main före frysningen) blir `k2_avg_ridge_l` 0,2050 efter rättning (Holm 0,154), alltså
under skärmen; den varianten är dock inte K2:s förregistrerade (`k2_rerun_main_*.md`).

**Varning:** vinsterna krymper med ca 0,001 pe MAE och p-värdena stiger. `k2_avg_ridge_s` faller under
urvalsskärmen. `k2_avg_ridge_l` och `k2_avg_ens_s` klarar den fortfarande, men `k2_avg_ens_s` (K2:s huvudkandidat)
har nu Holm 0,082 i stället för 0,055. De här är fortfarande urvalsevidens, inte bekräftelse.

## Rättningar i grenen

- `src/kpif_nowcast/publication.py` (nytt): sena releaser (`LATE_RELEASES`) och `enforce()`, som flyttar
  `known_from` för backfill-rader till `max(slut + lag, release)`. Flyttar bara senare, aldrig tidigare.
- `observations.load()` tillämpar `enforce()` (`load(raw=True)` ger lagrad tabell). Det betyder att rättningen
  gäller direkt efter merge, utan att `data/observations.parquet` byggs om. `default_known_from` (nya hämtningar)
  använder samma kalender. `upsert` skriver tillbaka den lagrade tabellen.
- `catalog.py`: `gdp_ind_yy` 35 → 45, `hh_consumption_yy` 15 → 45, `freight_ppi_deepsea` 15 → 21,
  `ea_hicp_total` 20 → 26, FAO 8 → 10; `aku_unemp_nsa`, `aku_employed` revised → ja; noter med belägg.
- `docs/publiceringskalender.md` + `tests/test_publication_calendar.py`: låser fördröjning och revised-flagga
  för alla 96 nationella serier och listan över sena releaser.
- `src/kpif_nowcast/k11_audit.py`: omkörning av K2 och diff av feature-celler.

## BLOCKED / inte belagt

<!--BLOCKED-->

## Vad lärde vi oss

<!--LARDOM-->
