# K0 Prisleden: nya katalogserier

Modul: `src/kpif_nowcast/catalog_prices.py` (kopplas in sist i `catalog.py`). Hämtas med
`python -m kpif_nowcast.observations <nycklar>` och kontrolleras med `python -m kpif_nowcast.catalog_prices`.
Råhämtningar: `data/raw/k0/`. En cachad fil som är högst 7 dagar gammal återanvänds. Tidigare cachade filer
i `data/raw/` (KPIF-XE, två KI-serier) återanvändes, så de hämtades inte igen.
29 serier, alla månatliga. Fördröjningen är dagar efter periodens slut och avrundad mot senare publicering.

| Grupp | Nycklar | Källa | Fördr. | Rev. | Från | Not |
|---|---|---|---|---|---|---|
| PPI | `ppi_hmpi_consumer`, `ppi_impi_consumer`, `ppi_itpi_consumer`, `ppi_itpi_consumer_xfood`, `ppi_hmpi_food`, `ppi_impi_food` | SCB TAB3184 (HMPI/IMPI/ITPI, MIG konsumtionsvaror resp. SPIN 10 livsmedel), 2020=100 | 30 d | ja | 1990-01 | September 2026 publicerades 2026-10-26. Senaste månaderna är preliminära. |
| KPIF | `kpif_xe_index` | SCB TAB6593 | 15 d | nej | 1987-01 | KPI revideras inte. |
| KPIF | `kpif_goods_index`, `kpif_services_index` | SCB TAB6627 (V, T) | 15 d | ja | 1987-01 | Indelningen före 2026 är troligen SCB:s omräkning till COICOP 2018. |
| KI | `ki_prices_grocery`, `ki_prices_durables`, `ki_prices_retail`, `ki_purchase_prices_grocery` | KI Barhanm (dagligvaru-, sällanköps-, detaljhandel; fråga 202 försäljningspriser resp. 250 inköpspriser, kommande 3 mån) | 3 d | nej | 2000–2015 | Nettotal, ej säsongsrensad (O). Inköpspriser finns från 2015-10. |
| KI | `ki_prices_food_industry`, `ki_prices_consumer_industry` | KI Barindm (BLIVS, BCONS; fråga 202 försäljningspriser hemma) | 3 d | nej | 2000-01 | Som ovan. |
| Råvaror | `coffee_usd`, `cocoa_usd`, `sugar_usd`, `beef_usd`, `pork_usd`, `poultry_usd`, `palm_oil_usd`, `soy_oil_usd`, `rapeseed_oil_usd`, `sunflower_oil_usd` | IMF Primary Commodity Prices via FRED (fredgraph.csv, ingen nyckel) | 60 d | ja | 1992-01 (nöt 2010-05, fågel 2003-01) | Samma konvention som `wheat_usd`. Den 2026-11-23 var senaste månad 2026-09, alltså mer än 54 dagars fördröjning för oktober. |
| Räntor | `gvb_2y`, `gvb_5y`, `gvb_10y` | Riksbanken SWEA (SEGVB2YC/5YC/10YC) | 1 d | nej | 1987-01 | Månadsmedel av dagliga noteringar, bara hela månader. |
| Räntor | `swestr` | Riksbankens SWESTR-API | 1 d | nej | 2021-09 | Månadsmedel. |

**Kvalitetskontroll** (`catalog_prices.quality()`, även som pytest): 29/29 serier har rader, inga dubbla
nycklar (serie, period, known_from), inga hål inom serien och ingen `known_from` före periodens slut. Alla
96 katalognycklar är unika.

## BLOCKED / ej tillagt
- **Medlingsinstitutet, avtalsmässiga löneökningar:** finns bara i PDF ("Löneutvecklingen i Sverige").
  MI:s PxWeb-databas nås bara via en sessionsproxy (jsessionid) och innehåller konjunkturlönestatistik, som
  redan finns i katalogen via SCB. Ingen skrapning.
- **Swedavia, flygpassagerare:** statistiksidan svarar HTTP 403 på skript.
- **SCB, hotellnätter:** SCB:s tabeller (TAB5295, TAB3162) slutar 2021-12. Statistiken ligger nu hos
  Tillväxtanalys, som inte tillhör spårets källor.
- **Riksbanken, Prospera:** ej försökt (Excel-fil). Prioriterades bort när kärnserierna var klara.
- **KI:s prisplaner för tjänster** (`ki_services`) fanns redan i `catalog.py` och lades inte till igen.
