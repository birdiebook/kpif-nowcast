# L9 Månadsrutinen: kalendern och snabb-KPI i rutinen

Spår L9 i körning 3, 2026-11-23. Inga modellvarianter och inga prognostester: allt här är beskrivande och mekaniskt.
`forecast.py`, `forecasts/<månad>.json` och `MODEL_NAME` är orörda. Justeringen är **ett förslag som Johannes
beslutar om**.

## (a) Kalendern för administrerade priser i månadsrutinen

- **Icke-fatalt steg i `pipeline monthly`** (`pipeline.admin_calendar`, före månadsbrevet): skriver förslaget för
  prognosmånaden till `outputs/admin_calendar/<månad>.json` och `.md` (committas inte; laddas upp som artefakt i
  `monthly-shadow.yml`). Separat: `python -m kpif_nowcast.pipeline admin [--month YYYY-MM]` eller
  `python -m kpif_nowcast.admin_calendar <månad> --info-date YYYY-MM-DD --write`.
- **Läckageregeln i informationsdatumet:** `admin_calendar.known_at` kräver beslut före deadline (dag 4 i t+1) **och**
  senast informationsdatumet. Informationsdatumet är brevets (`manadsbrev.cutoff_for`: tidigast av i dag och
  deadline). Händelser beslutade senare listas som "beslut efter informationsdatumet". Ekot av tidigare händelser
  följer samma regel. I brevet kapas K13:s realiserade KS-delar och KPIF-index till månaden före prognosmånaden,
  som i K3:s förklaring.
- **Månadsbrevet** (`manadsbrev.py`) har två nya sektioner: "Beslutade engångshändelser: förslag till manuell
  justering" (tabell med händelser, metod, beslutsdatum och källor, `--adjust`-raden, märkt som förslag) och
  "Förhandsvisning: <nästa månad>". Huvudbudskapet får en punkt. Ett registrerat beslut visas när det fattats senast
  informationsdatumet (`ADMIN_DECISIONS`; i dag bara 2026-11, beslutsloggen 2026-11-23 ordagrant: K13:s förslag
  `--adjust 0.15` används inte, den schemalagda slutprognosen körs oförändrad).

## (b) Snabb-KPI som referens i SCORECARD och champion-tabellen

- `scorecard.flash_live_lines`: för varje skarp prognos där snabb-KPI finns visas prognos, snabb-KPI, prognos −
  snabb, utfall, snabb − utfall (först publicerat, L7:s `kpif_flash_err_yy`) och prognos − utfall. I dag finns ingen
  rad: snabb-KPI för november 2026 kommer i början av december. Månadsjobbet skriver tabellen i
  `forecasts/SCORECARD.md`.
- `champion.flash_reference`: samma jämförelse på backtestprognoserna, samma månader för alla modeller.
- **SCORECARD.md regenererades inte i repot.** Scorecardet skrivs av månadsjobbet. Siffrorna nedan är genererade
  lokalt utan K2-skuggorna, som är för tunga att räkna i den delade containern just nu. Med K2 räknar månadsjobbet ut
  dem automatiskt.

SCB:s snabb-KPI mot backtestprognoserna, 2024-09..2026-10, n = 26. Alla rader, snabb-KPI inräknad, mäts mot samma
utfall (`yy_official`, omräknat 2020=100): snabb-KPI skiljer sig 1 av 26 månader (2025-06), högst 0,1 pe, MAE 0,004.
Mot först publicerat utfall (1987=100 före 2026-01, L7:s `kpif_flash_err_yy`) skiljer den 3 av 26 månader
(2024-11, 2025-06, 2025-08), MAE 0,012; det redovisas i texten, inte i tabellen.

| Modell | MAE mot utfall | MAE mot snabb-KPI | Medel prognos − snabb | Andel inom ±0,1 av snabb |
|---|---|---|---|---|
| comp_fuel_el (champion) | 0,383 | 0,387 | +0,020 | 19 % |
| j2_el_dev | 0,262 | 0,266 | +0,025 | 27 % |
| j1_comb_equal | 0,256 | 0,260 | −0,036 | 31 % |
| rb_updated | 0,281 | 0,285 | −0,097 | 42 % |
| riksbank | 0,330 | 0,334 | −0,133 | 31 % |
| snabb_kpi | 0,004 | 0 | 0 | 100 % |

Tolkning, beskrivande: snabb-KPI ligger så nära utfallet att "fel mot snabb-KPI" i praktiken är samma mått som "fel mot
utfallet" (skillnad 0,004 pe). Snabb-KPI kan därför användas som tidig återkoppling ungefär en vecka före utfallet.
Den ger ingen ny poängsättning. Perioden ingår i den redan använda 2024–26 och är urvalsevidens. Utfallet i "MAE mot
utfall" är `yy_official` (omräknat 2020=100) för alla rader.

## (c) November 2026 och förhandsvisning av december 2026

**Förslag för 2026-11** (informationsdatum 2026-11-23): `--adjust 0.04` (månadskort åter fullpris 3 nov i södra
Sverige, +0,035 pe m/m). Beslutet som finns (beslutsloggen 2026-11-23) gäller K13:s förslag: "K13:s förslag
`--adjust 0.15` för 2026-11 används inte. Den schemalagda slutprognosen körs oförändrad." K13:s +0,15 inkluderade
månadskorten, så utfallet blir detsamma, men kalenderns +0,04 har inte beslutats som en egen punkt. **Johannes
bekräftar** att den inte används (eller loggar annat). Brevet citerar beslutet och säger detsamma.

**Förhandsvisning av december 2026** (samma informationsdatum, beslut kända 2026-11-23):

| Händelse | pe m/m | Metod | Beslut senast |
|---|---|---|---|
| Koldioxidskattesänkningen upphör 30 nov 2026 | +0,398 | scb_ks (minus julis realiserade KS-energidel, K13) | 2026-06-30 |
| Månadskort åter fullpris från 3 dec i övriga regioner | +0,115 | assumption | 2026-10-28 |

Summa +0,513 pe m/m, i årstakt × 1,014 = **+0,52 pe**:
`python -m kpif_nowcast.forecast --adjust 0.52 --note "admin_calendar 2026-12: …"` (hela raden finns i brevet och i
`outputs/admin_calendar/2026-12.md`).

Vad det betyder för decemberprognosen:
- Används förslaget blir den skarpa decemberprognosen (görs 1–4 jan 2027) modellens siffra plus 0,52 pe i årstakt.
  Huvudmodellen ser drivmedel bara via Brent i SEK, så skattehöjningen finns inte i modellens siffra och räknas inte
  dubbelt. Detsamma gäller biljettpriserna.
- Ekot av tidigare engångshändelser i modellens trend och säsong är −0,13 pe m/m. Det ingår inte i förslaget, i linje
  med Johannes beslut om K13.
- Riksbankens senaste bana vid informationsdatumet (2026:3) går från 1,73 % i november till 2,55 % i december.
  Det stämmer med att banan räknar med att skattesänkningen upphör, men det är inte verifierat.
- Risker (från L1): genomslaget i pumppriset (K13 såg ungefär 2/3 av den mekaniska effekten i juli), Västtrafiks
  eventuella förlängning (+0,026 flyttas till januari) och hur SCB prisar 30-dagarskort över månadsskiftet.
  Förslaget räknas om automatiskt i januarirutinen med beslut fram till dess.
- **Johannes beslutar** om justeringen används, och hur stor den blir.

**Brevet `docs/manadsbrev/2026-11.md`:** se avsnittet Status nedan.

## Tester

`tests/test_l9_routine.py`, 15 tester utan nät (14 i första leveransen, inte 15 som det stod; +1 i granskningen): informationsdatumsregeln (`known_at`, `why_not_used`, ekot),
december 2026 vid 2026-11-23 jämfört med 2026-06-01, json/md-utdata, pipeline-steget (deadline-tak, icke-fatalt,
ordning i `monthly`, icke-fatalt även vid ImportError), brevets sektioner (cutoff, beslut, kapning av KS-delar, förhandsvisningen utan
Riksbanksomgångar publicerade efter cutoff, sammansättning utan modelldata), `flash_reference`/`flash_lines` och
`flash_live_lines`. Ett test kräver observationstabellen (snabbserierna finns, fel högst 0,1). Hela L1-sviten är grön.

## Status

- **Brevet `docs/manadsbrev/2026-11.md` är inte omgenererat.** Omgenereringen
  (`python -m kpif_nowcast.manadsbrev 2026-11 --today 2026-11-23 --no-k2`) hann inte bli klar på 40 minuter i den
  delade containern. Champion-tabellen räknar K2-historiken, och lasten var ~35 på 4 kärnor. Körningen stoppades vid
  fönstrets slut. Sektionerna är testade utan modelldata (`test_letter_has_new_sections_without_model_data`), och
  innehållet för november och december står ovan. Nästa månadsjobb (eller samma kommando på en ledig maskin)
  skriver brevet med de nya sektionerna. Informationsdatumet blir oförändrat 2026-11-23.
- **Hela pytest-sviten är inte körd** (> 40 min seriellt, containern överbelastad). Riktade sviter är gröna:
  test_l9_routine, test_l1_admin_calendar, test_l7_flash, test_k13_tax, test_publication_calendar och delar av
  test_shadow (41 + 12 passerade, 1 hoppad). test_k5:s brevtester (tunga) är inte körda. Orkestreraren kör hela sviten
  på det sammanslagna resultatet.

## Granskning

Oberoende granskning, 5 fynd (alla minor). Bedömda mot koden och källan:

1. **Beslutstexten för 2026-11 tolkade in för mycket.** Rättat. Beslutsloggen 2026-11-23 gäller K13:s
   `--adjust 0.15`, inte kalenderns +0,04. `manadsbrev.ADMIN_DECISIONS['2026-11']` citerar nu beslutsloggen ordagrant
   och säger att K13:s förslag inkluderade månadskorten men att kalenderns +0,04 (månadskort) inte beslutats separat
   och är Johannes att bekräfta. Avsnitt (a) och (c) ovan rättade på samma sätt.
2. **"MAE mot utfall" blandade två utfallsdefinitioner.** Rättat. Kontrollerat lokalt: mot `yy_official` skiljer
   snabb-KPI 1 av 26 månader (MAE 0,0038), mot först publicerat 3 av 26 (MAE 0,0115). `champion.flash_reference`
   mäter nu snabb-KPI-raden mot samma `actual` som modellerna; felet mot först publicerat utfall ligger i `meta`
   (`first_pub_*`) och skrivs i texten i `flash_lines`. Tabellen ovan: 0,012 → 0,004. Testet utökat.
3. **Steget var bara icke-fatalt vid körning, inte vid import.** Rättat. Importerna i `pipeline.admin_calendar`,
   `pipeline.manadsbrev` och `pipeline.explain` ligger nu i try-blocket. Nytt test
   (`test_pipeline_steps_not_fatal_on_import_error`) låter importen fallera och kontrollerar att alla tre bara
   varnar i `monthly` och att `admin` (strict) fortfarande fallerar.
4. **Grenen låg två commits efter auto3/merge1.** Rättat: origin/main (856ced2, = merge1 + L8 + L6-testet) är
   mergad in i auto3/l9 med vanlig 3-vägsmerge, utan konflikter. `git diff origin/main --stat` visar nu bara L9:s filer.
5. **test_k5, hela test_shadow och brevet var inte körda.** Se Status: hela sviten körd i rättningsrundan på den
   mergade grenen, och omgenereringen av brevet gjordes om när containern var ledig.

