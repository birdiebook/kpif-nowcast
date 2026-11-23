# L2 Resor: resultat

Kod: `src/kpif_nowcast/catalog_travel.py` (registrerad i `catalog.py` efter `catalog_prices`). Tester:
`tests/test_l2_travel.py` (15 tester, utan nät). Rådata cachas i `data/raw/l2/`. Kalender:
[publiceringskalender.md, avsnitt "Körning 3: L2"](../../publiceringskalender.md). Inga modellvarianter eller
prognostester, alltså inga p-värden.

## Serier (9 nya, alla månadsserier)

| Nyckel | Källa | Period | Fördröjning | Rev. |
|---|---|---|---|---|
| `guest_nights_total` | Eurostat tour_occ_nim (SE, hotell+stugbyar+vandrarhem+camping) | 2001-01–2026-08 | 80 d | ja |
| `guest_nights_domestic` | samma, totalt minus utländska | 2001-01–2026-08 | 80 d | ja |
| `guest_nights_foreign` | samma, utländska gäster | 2001-01–2026-08 | 80 d | ja |
| `guest_nights_hotel` | samma, hotell (NACE I551) | 1990-01–2026-08 | 80 d | ja |
| `easter_window_days` | kalender: dagar av påskens resefönster (påskdagen −9 till +1) i månaden, samma som K7 | 2000-01–2050-12 (fast slut) | −366 d | nej |
| `easter_sunday_in_month` | kalender: 1 i påskdagens månad (mars eller april) | 2000-01–2050-12 (fast slut) | −366 d | nej |
| `kpif_package_holidays_index` | SCB TAB6613, COICOP 09.8 | 1989-01–2026-10 | 15 d | ja |
| `kpif_air_transport_index` | SCB TAB6613, COICOP 07.3.3 | 1987-01–2026-10 | 15 d | ja |
| `kpif_accommodation_index` | SCB TAB6613, COICOP 11.2 | 1987-01–2026-10 | 15 d | ja |

Laddade i observationstabellen (3 998 rader efter granskningen). Inga dubbletter och inga hål. Alla lagerkontroller i
`warehouse.CHECKS` är gröna, också `known_from_after_period_end` med den negativa fördröjningen för påsken.

**Modelleringsval som spelar roll**
- **Gästnätter via Eurostat, inte via Tillväxtverket.** SCB producerade inkvarteringsstatistiken t.o.m.
  referensåret 2024 och Tillväxtverket från 2025 (Tillväxtverkets PM "Inkvartering 2025"), så ett
  producentbrott 2024/2025 är möjligt. SCB:s databastabeller TAB5295 och TAB3162 slutar 2021-12. Tillväxtverkets statistikportal går dock inte att nå från
  driftmiljön (se BLOCKED). Eurostat får månadsdata från Tillväxtverket. Serien är obruten från 1990, så någon
  skarvning mot SCB:s gamla tabell behövs inte.
- **Fördröjning 80 d, det vill säga t−3 vid deadline.** 2026-09 saknades fortfarande 2026-11-23, 54 dagar efter
  periodens slut, trots att Tillväxtverket publicerade månaden 2026-10-29. Enligt regelverket ska data skickas inom
  6 veckor och publiceras 1 dag till 1 månad därefter, alltså senast ca 73 dagar. Fördröjningar på 67–93 d ger alltid
  exakt t−3 vid deadline (64–66 d ger ibland t−2), och läckage för t−3 uppstår först om verklig fördröjning
  > 93 d. 80 är alltså konservativt utan att kosta något. Sexveckorsregeln gäller från 2020. Historiken
  1990–2019 vilar på att SCB själv publicerade samma månader (~t+35), inte på Eurostats fördröjning.
- **Brott 2001.** Totalt hoppar från 25,9 till 41,2 miljoner nätter per år (camping ingår från 2001). Därför börjar
  totalt, svenska och utländska 2001-01. Hotellserien har inget sådant brott och börjar 1990.
- **Svenska gäster = totalt − utländska.** Eurostat saknar den svenska uppdelningen 1991–2010 (utom 2001). Där
  alla tre finns stämmer identiteten exakt (212 av 212 månader).
- **Påsken med negativ fördröjning (−366 d).** Kalendern är känd i förväg. Med −366 d syns 12 månader framåt vid
  varje prognostidpunkt, vilket ger horisontmodellerna det de behöver. Det blir inget läckage, eftersom värdet
  faktiskt är känt. Lagret tillåter negativ fördröjning. Serierna har fast slutår 2050, så alla perioder kommer
  in i första backfill. Påskserierna hålls utanför Sverigeläget-dashboarden och J3-screeningen (lag < 0).
- **revised=True** för gästnätterna: siffrorna är preliminära tills den slutliga årsstatistiken kommer. Även KPIF-delindexen har revised=True, eftersom historiken före 2026 är
  SCB:s omräkning till COICOP 2018. Det är samma bedömning som för `kpif_goods_index` och samma revisionsrisk som K7
  undvek i TAB6613.
- (d) KPIF-delindex för paketresor, flyg och logi fanns inte i katalogen tidigare (kontrollerat med grep i
  `catalog*.py`). De ligger nu som egna serier, ingen dubblering.

## BLOCKED
- **Tillväxtverkets statistikportal** (`tillvaxtdata.tillvaxtverket.se/statistikportal`): värden finns inte i
  miljöns lista (proxyn svarar 403, WebFetch får ENOTFOUND). Jag har inte kunnat se om portalen har ett
  maskinläsbart API eller nedladdning. Den vägen ger t−1 vid deadline (Tillväxtverkets publiceringsplan: 22–30 d,
  t.ex. sep 2026 → 2026-10-29), mot t−3 via Eurostat. Johannes kan lägga till värden. Därefter behöver formatet
  undersökas.
- **Kammarkollegiets resegarantistatistik:** det finns ingen statistiktabell. Webbplatsen har bara ett register
  över reseaktörer med resegaranti (ögonblicksbild, 1 604 träffar, export till csv) och blanketter i PDF (t.ex.
  "Utfall resor föregående period", som är reseaktörernas egen inrapportering). Någon tidsserie över ställda
  garantier eller omsättning publiceras inte.

## Läget i Sverige nu
- **Gästnätter jan–aug 2026: +2,7 % mot samma period 2025** (svenska +1,8 %, utländska +5,0 %, hotell +3,1 %).
  Sommaren var stark: juli +5,7 %, utländska +10,7 %. Augusti mattades av till +1,9 %. Turistefterfrågan växer
  måttligt och drivs av utländska gäster. Hushållens egen efterfrågan på inhemska resor ökar bara svagt. Varning:
  Tillväxtverket skriver att utländska gästnätter underrapporterades 2024, så jämförelser över 2024–2025 ska tolkas
  försiktigt.
- **Resepriserna i KPIF:** paketresor låg på +9 till +13 % i årstakt maj–sep och föll till +1,1 % i oktober.
  Flyg låg på +8,7 % i oktober och logi på +2,1 %. Resepriserna har alltså drivit upp tjänsteinflationen under
  sommaren och hösten, men paketreseeffekten verkar ha klingat av i oktober.
- **Påsken 2027 är tidig (28 mars).** Hela resefönstret (11 dagar) ligger i mars 2027 och inget i april, mot 5
  dagar i mars och 6 i april 2026. Med K7:s skattning, **≈ 0,01 pe KPIF per påskdag** (+0,009–0,010 sedan 2016,
  sen mot tidig påsk ≈ ±0,05 pe i april), ger det ungefär +0,06 pe på KPIF m/m i mars 2027 och −0,06 pe i april
  2027, jämfört med 2026 års placering. Effekten är liten mot aprilfelen, som är upp till 0,4 pe (K7).

## Användning i våg 2
- `easter_window_days`: avvikelse mot femårssnittet för samma månad (K7:s `easter_dev`) som korrektion i mars och
  april. K7 visade dock att den tillför lite utöver femårssäsongen. Den bör bara vara en kandidat om screeningen
  har utrymme.
- `kpif_package_holidays_index`, `kpif_air_transport_index`, `kpif_accommodation_index`: senaste m/m-avvikelse mot
  säsong (t−1 vid deadline) som persistensfeature för tjänstemissen. Revisionsrisken från COICOP-omräkningen
  måste hanteras som i J4/K7, till exempel genom att bara använda avvikelser i stället för nivåer, eller genom att
  testa på perioden från 2026.
- Gästnätter (t−3, årstakt eller avvikelse mot säsong) som efterfrågeindikator för logi och paketresor. Fördröjningen
  gör den svag för nowcasten. Den passar bättre i horisontmodellerna och i Sverigeläget. Om Tillväxtverkets portal
  öppnas (t−1) blir serien betydligt mer användbar.

## Granskning

En oberoende granskare lämnade sex fynd. Alla bedömdes mot koden och källorna.

- **Rättat (wrong): påskserierna bröt lagerkontrollen efter årsskiftet.** Med rullande slutår (i år + 4) hade
  första veckokörningen 2027 lagt till 2031-01–12 som `fetch` med hämtdatum som `known_from`, vilket
  `known_from_after_period_end` flaggar. Det stämde. Granskarens alternativ (b), att använda kalenderdatum även
  för fetch-rader, hade i stället brutit `fetched_known_from_not_after_fetch`. Lösningen blev (a): fast slutår
  `EASTER_END = 2050`. Lokala tabellen byggdes om (påskraderna togs bort och laddades om som backfill), och ett
  nytt test kör backfill 2026-11-23 och refresh 2027-01-05 och kontrollerar att inga rader tillkommer och att
  `run_checks()` och `quality()` är rena.
- **Rättat (wrong): tröskelsiffrorna.** Det stämde: T−2 syns vid fördröjning ≤ 63–66 d och T−3 vid ≤ 93–96 d.
  Texten säger nu 67–93 d för exakt t−3, och läckage först vid > 93 d. Valet 80 d påverkas inte.
- **Rättat (minor): tunt belägg för 80 d.** Jag noterar i kalendern och här att sexveckorsregeln gäller från 2020
  och att historiken före 2020 vilar på SCB:s egen publicering. Uppföljning: första förekomst av SE 2026-09, -10
  och -11 i fetch-raderna som veckokörningarna nu skriver ska alla vara ≤ 80 d.
- **Rättat (minor): producent.** SCB producerade statistiken t.o.m. 2024 och Tillväxtverket från 2025. Det möjliga
  brottet 2024/2025 nämns nu. Påståendet om "slutlig 2025 ca 2 % lägre" hade ingen källa och är borttaget.
- **Rättat (minor): påskserierna i dashboard och J3.** `sverige_dashboard.v1_datasets` och `j3_screen.screen_keys`
  hoppar nu över serier med negativ fördröjning. Serierna ligger kvar i `CATALOG`, eftersom briefen bara tillåter
  registreringsblocket i `catalog.py`. Övriga nya L2-serier kommer med i J3 vid nästa omkörning, vilket är väntat.
- **Delvis rättat (minor): rådatacachen.** `MAX_AGE_DAYS` är nu 6 i `catalog_travel`, så söndagsjobbet hämtar
  varje vecka, och modulen rensar själv `data/raw/l2` till de 4 senaste versionerna (samma antal som
  `pipeline prune`). Den gemensamma rättningen av `rawcache.prune` (rglob) och av k0/k4 lämnas till orkestreraren,
  eftersom den rör andra spårs filer.
