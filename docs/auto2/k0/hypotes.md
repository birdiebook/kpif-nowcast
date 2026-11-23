# K0 Prisleden: förregistrering av screening och kombination

Skriven 2026-11-23 innan någon screening eller variant har körts. Bas: main @ 42b717b, gren `auto2/k0`.
Serierna: `src/kpif_nowcast/catalog_prices.py` (29 månadsserier, se [serier.md](serier.md)).

## Hypotes
Priser nära KPIF i kedjan (import- och hemmamarknadspriser för konsumtionsvaror och livsmedel,
handelns och industrins prisplaner, KPIF-XE/varor/tjänster, råvarupriser på mat, räntor) tillför
information om nästa månads KPIF utöver basmodellen. De flesta gör det inte, eftersom J3 visade att
katalogens 45 serier inte gjorde det och Fas 4b att KI:s prisplaner inte hjälpte komponentmodellen.

**Gissning innan:**
- h=1: 0–1 serie överlever BH (q = 0,10). Störst chans: `ppi_itpi_consumer_xfood`, `ppi_impi_food`,
  `ki_prices_grocery` (livsmedel och varor är trögare och föregås av led längre upp).
  Storlek för den bästa: MAE −0,003 till −0,010 pe mot rb_updated.
- h=3: 0–1 överlever (livsmedels-PPI eller dagligvaruhandelns prisplaner har bäst chans, 3–9 mån ledtid).
- h=12: ingen överlever.
- Kombinationen K0-C1: diff −0,000 till −0,010 pe, inte signifikant (p > 0,10). K0-C2: ingen förbättring av 50/50.

## Screening (samma protokoll som J3, räknas inte mot varianttaket)
Exakt J3:s protokoll ([docs/auto/j3/hypotes.md](../../auto/j3/hypotes.md)) och kod (`j3_screen.py`:
`transform`, `correct`, `run_h1`, `run_hk`, `score_table`, `bh`), men bara på de 29 nya serierna i
`catalog_prices.keys()`:
- Point-in-time via `observations.as_of(serie, deadline)`; h=1 deadline dag 4 i t+1; h=3/12 origin dag 4 i o+2.
- Transform x: säsongsdifferentierad månadsförändring (log ×100 för positiva nivåserier; nivå för
  nettotal och för `%`-enheter, dvs. räntor). Ingen K0-serie räknas som tillväxtserie.
- Korrektion = bas + b·(x − x̄), expanderande OLS utan intercept, minst 24 obs.
- Bas h=1: `rb_updated`; h=3/12: Riksbankens prognos vid origin.
- Primärt urval h=1: mål 2017-02..2026-10; också rapporterat 2015–2026. h=3/12: mål 2017-02..2026-10.
- Ensidigt DM (absolutfel, H1: lägre MAE), BH q = 0,10 per horisont, separat.
- Revised-serier (PPI, KPIF varor/tjänster, IMF-råvaror) flaggas. Överlever en sådan märks den
  "obekräftad (revisionsläckage möjligt)".

## Varianter (räknas mot taket): exakt två
Urvalsregel för de högst tre serierna (bestäms helt av screeningens h=1-primärtabell):
1. Ta serier som överlever BH (q < 0,10), i ordning efter rå p.
2. Om färre än tre överlever: fyll på med lägst rå p bland resten (märks "ingen/inte alla överlevde BH").
3. Högst en serie per källgrupp (PPI, KI, KPIF, IMF-råvaror, räntor), så att tre nästan identiska
   serier (t.ex. tre PPI-mått för samma varor) inte väljs. Hoppa över en serie vars grupp redan är vald.

- **K0-C1:** rb_updated + OLS (utan intercept, centrerat x) på de tre serierna, expanderande, minst 24 obs
  (`j3_screen.combined_h1`). Jämförs mot rb_updated, ensidigt DM, primärt urval 2017-02..2026-10,
  också 2015–2026.
- **K0-C2:** samma tre serier och samma skattning, men basen är 50/50-snittet av rb_updated och J2 V2
  (`j1_hybrid.build_panel`, `j1_comb_equal`), den bästa kända prognosen. Jämförs ensidigt mot 50/50.

Holm över de två varianterna redovisas bredvid rå p. 2024–2026 rapporteras bara.
pytest `tests/test_k0_prices.py` kräver identisk korrektion för t med och utan data efter t:s deadline.
