# Status: autonom körning

**Lås:** orkestrerare 2026-11-22T22:28Z (lokal 2026-11-22 23:28)
**Start:** 2026-11-22 22:55
**Senaste heartbeat:** 2026-11-22 23:28
**Global varianttotal:** 23/50 (J3:s screening oräknad)
**Deadline:** måndag 2026-11-23 22:00
**Läge:** KÖR. J2 och J6 startar.

**Källås (hämtning):** inga

## Jobb

| Jobb | Gren | Worktree | Steg | Varianter | Senaste SHA | Resultat | BLOCKED |
|---|---|---|---|---|---|---|---|
| J2 Elmodellen | auto/j2-el | C:\dev\kpif-auto\j2 | KLAR (pushad, tag auto/j2-done) | 5/10 | 438480b | V2 j2_el_dev MAE 0,243 vs comp_fuel 0,316, Holm p 0,014 (5/50): klarade urvalsskärmen; vs rb_updated p 0,57 | – |
| J6 Arbetsförmedlingen | auto/j6-af | C:\dev\kpif-auto\j6 | KLAR (pushad) | – | 4eb95fe | 3 serier (varsel 1992–, inskrivna/öppet 1996–), kvalitetskontroll OK, ej uppladdat till Claude Data | – |
| J1 Hybrid | auto/j1-hybrid | C:\dev\kpif-auto\j1 | KLAR (pushad) | 8/10 | 327c91e | Klarade INTE skärmen. Bäst C1 50/50 rb_updated+j2: MAE 0,217 vs 0,256, p1 0,015, Holm 0,117 (13/50) | – |
| J3 Katalogtest | auto/j3-katalog | C:\dev\kpif-auto\j3 | KLAR (pushad) | 1/10 (+screening) | 1372e0e | Inget håller: 0/45 serier överlever BH på h=1/3/12; kombination p 0,43 (14/50) | – |
| J4 Detaljnivå | auto/j4-detalj | C:\dev\kpif-auto\j4 | KLAR (pushad) | 3/10 | 8eb63d3 | D2 0,243 vs comp_fuel 0,316, Holm 0,010 (17/50): klarade skärmen, OBEKRÄFTAD (revisionsläckage möjligt); = J2 V2 | – |
| J5 Osäkerhet | auto/j5-osakerhet | C:\dev\kpif-auto\j5 | KLAR (pushad) | 6/10 | de6d6ad | U4 EWMA 52/80/89 % (±5 OK), U2 rullande 36 OK; dagens metod 40/62/77 % (23/50) | – |
| J7 AI-indikator | auto/j7-ai | C:\dev\kpif-auto\j7 | KLAR (pushad) | – | dfaca1f | Indikator klar; 'AI'-termen har mätbrott 2025 → huvudserie maskininlärning; SE 35 % vs EU 20 % AI-företag | – |

## Logg
- 2026-11-22 22:55 Statusgren och worktree skapade från origin/main @ a8cd686. BRIEF.md sparad.
- 23:03 Ministeg OK: PYTHONPATH pekar på worktree, pytest 11 gröna, push till auto/status utan fråga. Backup data/observations.20261122.bak.parquet skapad.
- 23:03 kpif-auto-restart skapad (varje timme 00:30–21:30 måndag). **Varning:** appen sparade inte auto-läge på uppgiften; testväckningen fastnade på en behörighetsfråga och stoppades. Omstarter kan därför fastna. Huvudsessionen fortsätter så länge den kan.
- 23:03 Worktrees C:\dev\kpif-auto\j2 (auto/j2-el) och j6 (auto/j6-af) skapade från origin/main @ a8cd686, data kopierad.
- 11-22 23:05 J2 förregistrerad (V1–V5), auto/j2-el @ 450a18e.
- 11-22 23:07 J2 KLAR: V2 klarade urvalsskärmen mot comp_fuel. Fryst som skuggprognos från 2026-12 (tag auto/j2-done @ 438480b). J1 förgrenas från taggen.
- 11-22 23:08 J1 förregistrerad (8 varianter), bas auto/j2-done @ 438480b.
- 11-22 23:11 J1 KLAR: negativt (Holm 0,117). Ingen frysning. J3 startar med bas rb_updated från origin/main.
- 11-22 23:14 J3 KLAR: negativt, ingen serie behålls. Nästa: J6 (Arbetsförmedlingen).
- 11-22 23:17 J6: AF-hämtare (egen xlsx-läsare, ingen ny dependency). Källås AF.
- 11-22 23:18 J6 KLAR. Källås släppt. Nästa: J4 (detaljnivå).
- 11-22 23:19 J4 förregistrerad (D1–D3).
- 11-22 23:20 J4 KLAR: D2 klarade skärmen men obekräftad; fryst enligt regel, rekommendation J2 V2. Nästa: J5.
- 11-22 23:21 J5 förregistrerad (U1–U6).
- 11-22 23:23 J5 KLAR: U4 EWMA vald (förslag, ej aktiverat). Nästa: J7.
- 11-22 23:23 J7 startad. Källås JobTech/SCB/Eurostat.
- 11-22 23:28 J7 KLAR. Källås släppt. Alla jobb klara; skriver slutrapport.
