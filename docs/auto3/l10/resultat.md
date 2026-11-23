# L10 Dashboards (förberedelse): resultat

Spår i körning 3, våg 1b. Förbereder Sverigeläget (Claude Data) och Pages-dashboarden med körning 3:s nya
serier och kalendern för administrerade priser. Ingen uppladdning till Claude Data: orkestreraren gör den i våg 3.
Inga modellvarianter och inga prognostester.

## Vad som byggdes

- `src/kpif_nowcast/sverige_sections.py`: tio nya dataset. Varje byggare tar observationstabellen och en
  brytdag och använder bara rader med `known_from` ≤ brytdagen (standard: byggdagen). Varje rad har
  `known_from` för värdet den visar.
  | Dataset | Innehåll |
  |---|---|
  | `admin_yy` | Engångshändelsernas bidrag till KPIF:s årstakt per månad 2016–2028, per grupp (drivmedel, elskatt, matmoms, kollektivtrafik/flyg, övrigt). En nivåändring räknas i tolv månader. Bara beslutade händelser. |
  | `admin_upcoming` | Månadsrutinens förslag (`admin_calendar.suggest`) för kommande månader: **2026-12 +0,52 pe**, 2027-01 −0,03, 2028-01 +0,78 (2026-11 +0,04). |
  | `admin_events` | Alla 34 händelser med effekt, beslutsdatum, källa och status idag (beslutad / ej beslutad). |
  | `snabbkpi` | Snabb-KPI för KPIF och KPIF-XE mot första utfall (utfall = snabb − fel), från 2024-09. |
  | `resor` | KPIF paketresor, flyg och logi (årstakt), gästnätter svenska/utländska (årsförändring av tremånaderssumma), påskens resefönster per år. |
  | `hyror` | Förhandlat utfall per år (2016–2026) mot KPI-hyrornas årsförändring i december; innevarande år markerat. |
  | `elmarknad` | Avtalsandelar per månad, Ei-nätavgifter per typkund och andel nätområden som höjde. |
  | `kronan` | EUR/SEK och USD/SEK, nivå och årsförändring. |
  | `prospera` | 5-åriga förväntningar, medel och P25–P75, mot 2 %. |
  | `v2_eval` | Läser `docs/auto3/v2/resultat.md` om filen finns (rubriker, stycken, punkter, tabeller), annars en rad "kommer". V2:s filer rörs inte. |
- `sverige_dashboard.py`: dataseten skrivs i ett eget steg per dataset (ett fel stoppar inte de andra), är
  registrerade i `DATASETS` och listas därmed i `MANIFEST.json`. Metan bäddar in `sverige_sections.py`.
- `templates/sverige_index.html`: åtta nya sektioner (Administrerade priser, Snabb-KPI mot utfall, Resor,
  Hyror, Elmarknaden, Kronan, Inflationsförväntningar, Utvärdering av de nya serierna), var och en med en mening
  om kopplingen till inflationen. Pages-sidan använder samma mall, så `pages.py` behövde inga ändringar.
- Tester: `tests/test_l10_sections.py` (10 tester: brytdag/known_from, utfall = snabb − fel, tolvmånadersregeln
  för kalendern, beslutsdatum, +0,52 för 2026-12, V2-parsning med och utan fil, riktiga data). `test_k5.py` kräver
  nu även de nya dataseten.

## Kontroll

- Bygge: `sverige_dashboard.main` skrev alla dataset till `outputs/sverige/` med `MANIFEST.json` (23 filer), och
  `pages.build_site` byggde sidan från dem. Champion-steget (K2-backtest, oförändrat) hoppades över i den lokala
  körningen: i den delade containern tog det över 30 minuter och det fristående bygget stoppades av tidsgränsen.
  `MANIFEST.json` saknar därför `champion.json` lokalt; våg 3 kör hela bygget. Alla körning 3-dataset byggdes
  på några sekunder.
- Playwright (chromium, deviceScaleFactor 1, 1280 och 390 px): inga konsolfel utom 404 för det medvetet
  saknade `champion.json`, ingen horisontell scroll, alla åtta nya sektioner har ritade diagram eller text med data. d3 från cdnjs var blockerat i containern; testet
  serverade samma fil från npm (`d3@7.9.0`, SRI-hashen stämmer). Skärmbilder i `/tmp/claude-0/l10-shots/`
  (inte committade).

## Att veta inför våg 3

- **Fel som fanns före L10 på `auto3/merge1`:** `tests/test_l6_fx.py::test_registered_once_right_after_catalog_prices`
  faller, eftersom mergen lade `catalog_travel` före `catalog_fx` i `catalog.py`. Testet förväntar sig att `sek_eur`
  kommer direkt efter `catalog_prices`. L10 rör inte katalogen; orkestreraren rättar testet eller ordningen.

- Ladda upp de tio nya JSON-filerna och `index.html` enligt `outputs/sverige/MANIFEST.json`.
- "Kända per idag" följer katalogens `known_from` strikt. Ei:s och SCB:s nätavgifter för år Y räknas som kända
  först 31 december Y (L5:s konservativa regel), så 2026 syns inte förrän vid årsskiftet trots att tarifferna
  publicerades i maj.
- Kalenderns årstaktsbidrag räknar m/m-effekten som effekt på årstakten (faktor ≈ 1); `admin_upcoming` använder
  `suggest` med indexfaktorn (1,014), därav +0,52 mot 0,513.
- Champion-steget i `sverige_dashboard` (K2-backtesten) styr byggtiden helt; L8 tittar på testsvitens hastighet.
