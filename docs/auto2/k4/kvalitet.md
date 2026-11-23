# K4 Regionala Sverige: kvalitetskontroll

Hämtat 2026-11-23. 241 länsserier i observationstabellen: 11 mått × 21 län + riket. Undantaget är
fastighetsprisindex, där Kalmar och Gotland redovisas tillsammans, så det måttet har 20 serier + riket.
Totalt 51 557 rader, alla `source=backfill`. Kontrollerna körs med `python -m kpif_nowcast.catalog_region`
(tabellerna nedan), `python -m kpif_nowcast.warehouse` (DuckDB-kontrollerna från K1, nu över alla 337 serier) och
`tests/test_catalog_region.py`. **Status: grön.**

## Nycklar och modell
- En serie per mått och län: `region_<mått>_<länskod>` (`00` = riket, `0809` = Kalmar + Gotland). Det passar den
  befintliga (series, period)-modellen utan ny kolumn. `catalog_region.frame(mått)` sätter ihop ett mått som tabell
  med perioder × län.
- Länsserierna ligger i `catalog.REGIONAL`, inte i `catalog.CATALOG`. Därför ändras inte kandidatlistorna i
  `j3_screen` och `k2_ml` eller den nationella dashboarden. `by_key()`, `observations.refresh()` och
  `warehouse.catalog_frame()` använder `catalog.ALL` (= CATALOG + REGIONAL).

## Resultat
| Kontroll | Utfall |
|---|---|
| Unika nycklar (series, period, known_from) | 0 dubbletter |
| known_from ≥ periodens slut | 0 brott |
| Negativa värden | 0 |
| Alla län finns per mått | ja, 21 (FPI: 20 + 0809) + riket |
| Hål inne i serierna | 62, alla i AKU per län (SCB undertrycker celler med för få observationer, `..`). Inga andra hål |
| DuckDB-kontrollerna (K1) | alla 8 ok; AKU-länen undantas från `no_gaps` via `KNOWN_GAP_PREFIXES` med orsak |
| Informationsmängd | AF-andel, AF-antal och konkurser: månad t är inte känd vid t:s deadline (dag 4 i t+1), t−1 är det (pytest) |

## Summa av länen mot riket
| Mått | Kontroll | Utfall |
|---|---|---|
| Konkurser | summa län = riket | exakt (riket *är* summan: tabellen saknar riksrad) |
| Folkmängd | summa län / riket − 1 | max 0,0002 % |
| Inskrivna arbetslösa (AF) | riket (summa inkl. okänt län) mot J6:s riksfil `af_inskrivna_arbetslosa` | **exakt lika** alla 370 månader |
| Öppet arbetslösa (AF) | samma mot `af_oppet_arbetslosa` | exakt lika alla 370 månader |
| Inskrivna/öppet, okänt län | andel av riket utan län | snitt 0,07 / 0,08 %, max 1,3 / 2,4 % (2022-07) |
| Varsel (AF) | länsfilens riksrad mot J6:s `af_varsel` | exakt 1992–2004 och 2020–2026; 2010–2019 en månad med 0,14 %; 2005–2009 avvikelse i 15 av 60 månader (max 10,8 %, 2005-07), snitt −0,5 % |
| Varsel, okänt län | "Inga uppgifter" som andel av riket | snitt 0,04 %, max 7,9 % (2021-05) |
| Andelar (AF, BAS, AKU) | riket inom länens min–max | 100 % av perioderna |
| AF-andel riket | mot AF:s egen siffra i filen (blad Andel, "Totalt") | 6,5367 % 2023-01 och 6,6421 % 2026-03, samma som AF |
| Småhuspris, FPI | riket inom länens min–max | 100 % |

Varselavvikelsen 2005–2009 kommer från två olika AF-filer. J6 tar riket 2005– från avdelningsbladens
"Totalsumma" i branschfilen, och länsfilen har en egen riksrad. Båda är AF:s publicerade siffror. Felet är inte vårt,
men orsaken är inte utredd.

## Mätbrott och särdrag (dokumenterade, inte justerade)
- **AF:s åldersgränser:** inskrivna 16–64 år t.o.m. 2022, 16–65 år 2023–2025, 16–66 år från 2026. Det syns inte i
  länen. Januariförändringen 2023 och 2026 ligger inom |z| < 2 mot januari 2015–2025 i alla län (största: Norrbotten
  −1,8 och Skåne +1,3 år 2023).
- **AF:s andel av arbetskraften byter nämnare 2023:** `af_andel_ak08` (registerbaserad arbetskraft, 2008–2023) och
  `af_andel` (BAS, 2023–). Under överlappet 2023 skiljer de sig med −0,03 procentenheter i riket och högst 0,12
  (Skåne). Serierna lagras separat och skarvas inte.
- **AF-andel, okänd kommun:** varje månad finns en post med inskrivna utan kommun och därmed utan arbetskraft (ca
  2 000 personer 2023-01). Den ingår i riket, precis som AF räknar, men inte i något län. Därför ligger riket något
  över ett vägt snitt av länen.
- **Varsel per län:** AF uppdaterar inte länsfilen efter 2026-03 ("Framöver hänvisas till Statistikverktyget").
  Serien slutar där (BLOCKED, se resultat.md). Länet avgör företagets organisationsnummer. 7 av ~8 600 länsceller är
  tomma. Årsbladens radsummor visar att de betyder 0, och de lagras som 0.
- **AKU per län:** kvartal, ej säsongsrensad, beräknad som arbetslösa / (arbetslösa + sysselsatta) ur tusental. SCB
  undertrycker små celler. Gotland saknar värden efter 2016K2, och Kalmar och Norrbotten saknar 2026K3.
  `latest_by_county` markerar sådana län med `behind_national`. Felmarginalerna är stora, så AKU används inte för
  länsjämförelse i lage.md.
- **BAS-arbetslöshet (TAB5663):** finns bara från 2024-01 och är preliminär (revised=True). Den rangordnar länen
  nästan exakt som AF-andelen (korrelation 0,997 över länen 2026-08), på lägre nivå (riket 5,2 mot 6,3 %).
- **Småhus, köpeskilling:** ett medelvärde, inte kvalitetsjusterat, och senaste kvartalet är preliminärt. Små län har
  få försäljningar, så förändringar på över 10 % på ett år förekommer.
- **Fastighetsprisindex per län:** finns bara årsvis (TAB1148). Kvartalsindex finns bara för riksområden (TAB1150),
  inte län, och används inte. Kalmar och Gotland ligger ihop.
- **Länsindelning:** dagens 21 län gäller sedan 1998 (Skåne 1997, Västra Götaland 1998). Alla källor redovisar även
  tidigare år (AF från 1992/1996, Tillväxtanalys från 1996) efter dagens indelning. Det syns ingen skarv.
- **Folkmängd:** två SCB-tabeller skarvas, TAB1625 (2000–2024) och TAB6473 (2025–). Ingen överlappning finns, och
  skarven syns inte (riket 2024-12 → 2025-01 är en normal månadsförändring).
- **Publiceringsfördröjning** (avrundad mot senare publicering): AF 15 d (som J6), Tillväxtanalys 10 d (tabellen
  uppdaterad 2026-11-05 för oktober), BAS 60 d (augusti publicerad 2026-10-27), AKU 30 d (K3 publicerad 2026-10-16),
  småhus 30 d (K3 2026-10-23), folkmängd 45 d (september 2026-11-11), FPI 180 d (2025 publicerad 2026-06-05).
- **revised-flaggan:** ja för AF-andel (nämnaren kan uppdateras, inte verifierat), varsel (som J6), BAS, AKU,
  småhuspris och FPI (preliminära värden). Nej för AF-antal, konkurser och folkmängd. AF:s antal har inte
  verifierats som oreviderade; flaggan följer J6.

## Licenser
- SCB: CC0. Tillväxtanalys: öppna data via PxWeb utan konto. Arbetsförmedlingen: statistiken får användas med
  källangivelse (enligt J6, inte verifierat mot en licenstext).

## Länskarta (GeoJSON): BLOCKED
SCB:s öppna geodata (WFS `geodata.scb.se/geoserver/stat`) har DeSO, RegSO och tätorter men inget länslager. Ett
länslager skulle kräva att DeSO-polygonerna slås ihop, och det behöver ett nytt GIS-paket (shapely/geopandas).
Lantmäteriets nedladdningar går via Geotorget, som kräver konto. Ingen fil har lagrats. I stället finns
`catalog_region.TILE_GRID`, en rutnätskarta med kolumn och rad per län ungefär geografiskt. `latest_by_county()`
skickar med den som `tile`, så K5 kan rita en rutnätskarta eller en tabell.
