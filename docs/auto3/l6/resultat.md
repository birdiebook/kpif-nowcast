# L6 Kronan: resultat

## Vad som byggdes

- `src/kpif_nowcast/catalog_fx.py`: två nya nationella serier från Riksbankens SWEA, registrerade i
  `catalog.py` direkt efter `catalog_prices`. Rådata cachas i `data/raw/l6/riksbank_<serie>_<hämtdatum>.json`.
- Månadsvärdet är medelvärdet av de dagliga fixingkurserna. Bara hela månader tas med, och det avgörs mot
  **hämtdatumet för rådatafilen**, inte mot dagens datum. Mönstret i `catalog_prices` (cache i upp till 7 dagar
  plus `m.index < innevarande månad`) skulle annars kunna publicera en ofullständig månad: om en fil hämtad
  27 november återanvänds 2 december blir november ett medel av 19 av 21 bankdagar. Det testas uttryckligen.
- KIX (`kix`, SEKKIX92) fanns redan i katalogen och dupliceras inte. TCW (SEKTCW92) är nedlagd i SWEA (2021-06)
  och läggs inte till. Katalogens konvention för marknadsserier är nivå (som `kix` och `brent_sek`), så serierna
  är nivåer. Årsförändring räknas fram i modellsteget.
- `tests/test_l6_fx.py` (16 tester efter granskningen): månadsmedel, att ofullständig månad tas bort (också sista dagen i månaden,
  innan fixingen kl. 16.15), gammal cache, parsning med dubbletter och tomma värden, cacheval, placering i katalogen,
  known_from före deadline, plus datatester (inga hål, inga dubbletter, known_from ≥ periodslut + 1 d, rimliga nivåer,
  inget månadshopp över 15 %).
- **Oberoende kontroll av aggregeringen:** vårt månadsmedel jämfördes med Riksbankens egna månadsgenomsnitt
  (SWEA `ObservationAggregates`, M). Alla 406 månader 1993-01..2026-10 stämmer för båda serierna, med största
  avvikelse 5e-6 (Riksbanken avrundar till 5 decimaler). Antalet noteringar per månad stämmer också (minst 17).
  Riksbankens egna aggregat tar inte heller med den pågående månaden.

## Serier

| Nyckel | Serie | Från | Fördröjning | Rev. | Belägg |
|---|---|---|---|---|---|
| `sek_eur` | EUR/SEK, SEKEURPMI | 1993-01 | 1 d | nej | SWEA grupp 130: "Observations are published daily at 16.15"; `observationMaxDate` 2026-11-20 vid hämtning måndag 2026-11-23 |
| `sek_usd` | USD/SEK, SEKUSDPMI | 1993-01 | 1 d | nej | Som ovan |

Före 1999 är `sek_eur` ECU-kursen, inte euron (Riksbankens SWEA-kedjning; första notering 1993-01-04,
euron infördes 1999-01-01). Modeller som vill ha en ren eurokurs bör börja 1999-01.

Revised=nej: en fixing är en enskild notering utan vintagar, och SWEA har inget versionsbegrepp för
valutakurser. Det belägg som finns är att vår aggregering av dagens data stämmer exakt med Riksbankens
publicerade månadsgenomsnitt. En äldre hämtning att jämföra med fanns inte, så att historiska fixingar aldrig
korrigeras har inte kunnat verifieras empiriskt. Observationstabellen registrerar en eventuell ändring som
revision från och med nu.

## BLOCKED

Inget. Allt går mot `api.riksbank.se` (tillåten), utan nyckel.

## Läget i Sverige nu (data t.o.m. oktober 2026, dagliga t.o.m. 20 november)

| | feb 2026 | okt 2026 | 1–20 nov 2026 | år/år okt | snitt 5 år |
|---|---|---|---|---|---|
| EUR/SEK | 10,64 | 11,15 | 11,05 | +1,7 % | 11,08 |
| USD/SEK | 9,00 | 9,96 | 9,95 | +5,6 % | 10,09 |
| KIX | 114,1 | 122,0 | | +3,8 % | |

Kronan har försvagats under hela 2026 efter toppen i februari: +5 % mot euron, +11 % mot dollarn och +7 % i
KIX fram till oktober. Den har nu gett tillbaka det mesta av styrkan från vintern och ligger nära femårssnittet.
Försvagningen mot dollarn är större än mot euron, så den slår först mot det som prissätts i dollar
(drivmedel, råvaror). Novembers medel hittills ligger på oktobers nivå, men sista veckan har kronan försvagats
igen (11,21 respektive 10,20 den 20 november). För KPIF betyder det att stödet från en stark krona, som
dämpade varupriserna under första halvåret, har vänt till ett svagt uppåttryck på importpriser under 2027.

## Kronans genomslag på importpriser (kort)

- **Kedjan:** växelkurs → importpriser (producentprisindex, `ppi_impi_consumer`, `ppi_impi_food`) →
  konsumentpriser på varor (`kpif_goods_index`). Genomslaget är snabbt och nästan fullt i importpriserna i
  producentledet, men långsamt och ofullständigt i konsumentledet. Där ingår inhemska kostnader (handel, logistik,
  löner), och priser ändras i omgångar.
- **Storleksordning:** i Riksbankens och Konjunkturinstitutets analyser brukar en 10 procent svagare krona (KIX)
  höja KPIF med i storleksordningen 0,5–1 procentenhet, utspritt över ett till två år. Effekten är störst och
  snabbast på livsmedel, importerade varor och energi. Siffrorna är inte verifierade i detta spår och ska
  behandlas som en a priori-storlek.
- **Valuta per komponent:** drivmedel och el följer råvarupriset i dollar respektive euro samma månad.
  Det fångas redan av `brent_sek` och elpriset i SEK. Livsmedel och kläder importeras mest från euroområdet och
  följer EUR/SEK med flera månaders eftersläpning. Det är därför serierna hålls isär i stället för att bara
  använda KIX.
- **Asymmetri och läge:** genomslaget anses större när kronan försvagas och efterfrågan är stark. Med svag
  efterfrågan 2026 är ett mindre genomslag än tumregeln troligare.

## Användning i våg 2

- Feature: år/år-förändring (eller log-förändring över 3, 6 och 12 månader) av `sek_eur` och `sek_usd`, laggad
  1–9 månader, som korrektion på varu- och livsmedelskomponenterna. Ett naturligt test är `sek_eur` mot
  livsmedel/varor och `sek_usd` mot energi, utöver det `brent_sek` redan fångar.
- Informationsset: hela månad t finns dag 1 i t+1, alltså före deadline dag 4. Serien kan därför användas
  för målmånad t utan läckage.
- Risk för överlapp: `kix`, `brent_sek` och importpriserna bär delvis samma information. Det bör vägas in vid valet
  av högst tre serier.

## Granskning

En oberoende granskare lämnade fem fynd. Alla bedömdes mot källan och stämde. Fyra rättades, och det femte
dokumenterades.

1. **Fel, rättat: fel startmånad efter merge.** `_fresh()` letade också i `data/raw/` och kunde där plocka
   `riksbank_SEKEURPMI_<datum>.json` och `riksbank_SEKUSDPMI_<datum>.json`, som `sources.riksbank.fetch_swea()`
   skriver med start 2011-01 (energinet) eller 2000-01 (features). I main hade serierna då börjat 2011-01
   respektive 2000-01. Det var inget läckage, men span och tester stämde inte. Kontrollerat: filerna i
   huvudcheckouten börjar 2011-01-03 och 2000-01-03. Rättning: `data/raw/` söks inte längre (`MAIN_RAW` är
   borttagen), och `raw_daily()` vägrar dessutom rådata som börjar senare än START + 10 dagar. Nya tester:
   en fil i `data/raw/` från 2011 ignoreras och en nedladdning från 1993-01-01 görs, och en trunkerad cache
   ger ValueError. Kontrollerat också med huvudcheckoutens filer kopierade in: båda serierna börjar 1993-01.
2. **Mindre, rättat: offline-läge saknades.** Med `KPIF_OFFLINE` spelar `raw_daily()` nu upp den nyaste filen
   i `data/raw/l6`, oavsett ålder, via `rawcache.require()`. Saknas fil blir det OfflineError och ingen
   nedladdning. Det testas.
3. **Mindre, rättat: ECU före 1999.** Det står nu i noten för `sek_eur` i `catalog_fx.specs()`, i
   moduldokumentationen och ovan.
4. **Mindre, rättat: formuleringen om "tillbaka styrkan".** Den lyder nu "gett tillbaka". Granskaren
   kontrollerade övriga siffror i lägestabellen och fann att de stämmer.
5. **Mindre, dokumenterat (ingen kodändring): fördröjningen är verifierad vid en enda tidpunkt.** SWEA har inga
   historiska publiceringstidpunkter per period. Fördröjningen bygger på Riksbankens publiceringsregel (kl. 16.15
   samma bankdag) och på kontroller 2026-11-23, egen och granskarens. Marginalen mot deadline dag 4 är 3 dagar.
   revised=False bygger på metoden (en fixing har inga vintagar) och inte på en jämförelse mellan vintagar. Detta
   står nu också i publiceringskalendern.

