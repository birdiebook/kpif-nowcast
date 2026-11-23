# K4 Regionala Sverige: resultat

**Status: klart.** Inga modellvarianter. K4 är bara deskriptivt och förbrukar 0 varianter. Inga MAE- eller
DM-resultat, eftersom inget prognostiseras.

## Vad som byggdes
- `src/kpif_nowcast/catalog_region.py`: 11 mått per län, totalt 241 serier i observationstabellen
  (`region_<mått>_<länskod>`, `00` = riket):

  | Mått | Källa | Frekv. | Period | Fördröjning | Rev. |
  |---|---|---|---|---|---|
  | `af_andel`: inskrivna arbetslösa, % av arbetskraften (BAS) | AF | M | 2023-01–2026-10 | 15 d | ja |
  | `af_andel_ak08`: samma, äldre registerbaserad arbetskraft | AF | M | 2008-01–2023-12 | 15 d | nej |
  | `af_inskrivna`: inskrivna arbetslösa, antal | AF | M | 1996-01–2026-10 | 15 d | nej |
  | `af_oppet`: öppet arbetslösa, antal | AF | M | 1996-01–2026-10 | 15 d | nej |
  | `af_varsel`: varsel, personer | AF | M | 1992-01–2026-03 | 15 d | ja |
  | `bas_arbetsloshet`: arbetslöshet 20–65 år | SCB TAB5663 | M | 2024-01–2026-08 | 60 d | ja |
  | `aku_arbetsloshet`: arbetslöshet 15–74 år | SCB TAB2923 | Q | 2005K1–2026K3 | 30 d | ja |
  | `smahus_pris`: småhus, köpeskilling medel (tkr) | SCB TAB1167 | Q | 1998K1–2026K3 | 30 d | ja |
  | `fpi_smahus`: fastighetsprisindex småhus | SCB TAB1148 | A | 1990–2025 | 180 d | ja |
  | `konkurser`: antal | Tillväxtanalys (öppen PxWeb) | M | 1996-01–2026-10 | 10 d | nej |
  | `befolkning`: folkmängd | SCB TAB1625 + TAB6473 | M | 2000-01–2026-09 | 45 d | nej |

- `src/kpif_nowcast/sources/xlsx_pivot.py`: läser pivotcachen i AF:s Excelfiler, där länsdatan finns. De synliga
  bladen visar bara riket. Ingen ny dependency.
- `catalog.REGIONAL` och `catalog.ALL`: länsserierna hålls utanför `CATALOG`, så J3/K2-listorna och den nationella
  dashboarden är oförändrade. `by_key`, `observations.refresh` och `warehouse` använder `ALL`. Valet står i
  beslutsloggen.
- `latest_by_county()` för K5 ger JSON-vänliga rader per mått och län med senaste period och värde, värdet ett år
  tidigare, förändring (procentenheter eller %), rang, `behind_national` och rutnätsposition (`tile`). Där finns
  också det härledda måttet `konkurser_per_10k` (tolv månader per 10 000 invånare). `frame(mått)` ger en hel
  tidsserietabell.
- `quality()` och `docs/auto2/k4/kvalitet.md`: kvalitetskontrollen är grön.
- `docs/datakatalog.md` är regenererad och innehåller alla 337 serier (96 nationella + 241 länsserier), med en
  sammanfattning per mått och en täckningstabell per län.
- `docs/auto2/k4/lage.md`: deskriptiv lägesbild av länen.
- Tester: `tests/test_catalog_region.py` (8 tester: länskoder, nycklar och katalogkrok, alla län per mått,
  pivotläsare på syntetisk fil, `latest_by_county` syntetiskt, informationsmängd, kvalitet, AF län mot riksfil).
  Hela sviten: 89 passed, 1 skipped (en körning under hög last fick 2 nätverksfel i test_j1_hybrid som inte hade med K4 att göra. Omkörning: grönt).

## Nyckelresultat (kvalitet)
- AF:s länsfil summerar **exakt** till J6:s riksfil för inskrivna och öppet arbetslösa (alla 370 månader).
  AF-andelen för riket stämmer med AF:s egen siffra.
- Inga hål utom i AKU per län, där SCB undertrycker små celler. Gotland saknar AKU efter 2016. AF:s åldersbrott
  2023 och 2026 syns inte i något län.
- Inga dubbletter, och inget known_from före periodens slut. Månad t av AF-data och konkurser är inte känd vid t:s
  deadline.

## BLOCKED
- **Varsel per län efter 2026-03:** AF har slutat uppdatera Excelfilen och hänvisar till Statistikverktyget, en
  interaktiv app utan fil eller dokumenterat API. Serien slutar 2026-03.
- **Länskarta (GeoJSON):** SCB:s WFS har inget länslager, bara DeSO/RegSO. Att slå ihop dem kräver ett nytt
  GIS-paket, och Lantmäteriets nedladdning kräver konto via Geotorget. Rutnätskarta i stället (`TILE_GRID`).
- **Fastighetsprisindex per län och kvartal:** SCB publicerar det inte (kvartal bara per riksområde). Årsindex plus
  kvartalsvisa medelpriser används.

## Vad lärde vi oss
- AF:s länsstatistik finns. Den ligger i pivotcachen i Excelfilerna och syns inte i bladen. En liten XML-läsare
  räcker, och en 420 MB uppackad fil läses på ~13 s.
- Registerbaserad arbetslöshet ger en stabil länsbild. AF-andelen och SCB:s BAS rangordnar länen nästan identiskt
  (korrelation 0,997). AKU per län är för brusig för jämförelse mellan län.
- Länsbilden nu: arbetslösheten är högst i Skåne, Södermanland, Västmanland och Gävleborg (7,6–8,2 % enligt AF) och
  lägst i Norrbotten och Gotland (3,4–3,7 %). Den har sjunkit i alla län på ett år. Småhuspriserna skiljer en faktor
  3,6 mellan Stockholm och Västernorrland. Konkurserna per invånare är högst i Stockholm och har ökat i fem län.
- Öppen fråga till K5: varselkartan kan bara visa läget till och med 2026-03. Riksserien `af_varsel` (J6) är
  aktuell.
