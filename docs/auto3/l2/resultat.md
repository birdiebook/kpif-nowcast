# L2 Resor: resultat

Kod: `src/kpif_nowcast/catalog_travel.py` (registrerad i `catalog.py` efter `catalog_prices`). Tester:
`tests/test_l2_travel.py` (12 tester, utan nät). Rådata cachas i `data/raw/l2/`. Kalender:
[publiceringskalender.md, avsnitt "Körning 3: L2"](../../publiceringskalender.md). Inga modellvarianter eller
prognostester, alltså inga p-värden.

## Serier (9 nya, alla månadsserier)

| Nyckel | Källa | Period | Fördröjning | Rev. |
|---|---|---|---|---|
| `guest_nights_total` | Eurostat tour_occ_nim (SE, hotell+stugbyar+vandrarhem+camping) | 2001-01–2026-08 | 80 d | ja |
| `guest_nights_domestic` | samma, totalt minus utländska | 2001-01–2026-08 | 80 d | ja |
| `guest_nights_foreign` | samma, utländska gäster | 2001-01–2026-08 | 80 d | ja |
| `guest_nights_hotel` | samma, hotell (NACE I551) | 1990-01–2026-08 | 80 d | ja |
| `easter_window_days` | kalender: dagar av påskens resefönster (påskdagen −9 till +1) i månaden, samma som K7 | 2000-01–(i år + 4)-12 | −366 d | nej |
| `easter_sunday_in_month` | kalender: 1 i påskdagens månad (mars eller april) | 2000-01–(i år + 4)-12 | −366 d | nej |
| `kpif_package_holidays_index` | SCB TAB6613, COICOP 09.8 | 1989-01–2026-10 | 15 d | ja |
| `kpif_air_transport_index` | SCB TAB6613, COICOP 07.3.3 | 1987-01–2026-10 | 15 d | ja |
| `kpif_accommodation_index` | SCB TAB6613, COICOP 11.2 | 1987-01–2026-10 | 15 d | ja |

Laddade i observationstabellen (3 518 rader). Inga dubbletter och inga hål. Alla lagerkontroller i
`warehouse.CHECKS` är gröna, också `known_from_after_period_end` med den negativa fördröjningen för påsken.

**Modelleringsval som spelar roll**
- **Gästnätter via Eurostat, inte via Tillväxtverket.** Tillväxtverket äger statistiken sedan 2022, och SCB:s
  tabeller TAB5295 och TAB3162 slutar 2021-12. Tillväxtverkets statistikportal går dock inte att nå från
  driftmiljön (se BLOCKED). Eurostat får månadsdata från Tillväxtverket. Serien är obruten från 1990, så någon
  skarvning mot SCB:s gamla tabell behövs inte.
- **Fördröjning 80 d, det vill säga t−3 vid deadline.** 2026-09 saknades fortfarande 2026-11-23, 54 dagar efter
  periodens slut, trots att Tillväxtverket publicerade månaden 2026-10-29. Enligt regelverket ska data skickas inom
  6 veckor och publiceras 1 dag till 1 månad därefter, alltså senast ca 73 dagar. Alla fördröjningar på 64–92 d ger
  samma informationsmängd (t−3), så 80 är konservativt utan att kosta något.
- **Brott 2001.** Totalt hoppar från 25,9 till 41,2 miljoner nätter per år (camping ingår från 2001). Därför börjar
  totalt, svenska och utländska 2001-01. Hotellserien har inget sådant brott och börjar 1990.
- **Svenska gäster = totalt − utländska.** Eurostat saknar den svenska uppdelningen 1991–2010 (utom 2001). Där
  alla tre finns stämmer identiteten exakt (212 av 212 månader).
- **Påsken med negativ fördröjning (−366 d).** Kalendern är känd i förväg. Med −366 d syns 12 månader framåt vid
  varje prognostidpunkt, vilket ger horisontmodellerna det de behöver. Det blir inget läckage, eftersom värdet
  faktiskt är känt. Lagret tillåter negativ fördröjning.
- **revised=True** för gästnätterna: siffrorna är preliminära till mars året efter, och den slutliga statistiken för
  2025 blev ca 2 % lägre än den preliminära. Även KPIF-delindexen har revised=True, eftersom historiken före 2026 är
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
