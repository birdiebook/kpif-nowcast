# Status: autonom körning

**Lås:** orkestrerare 2026-11-22T22:05Z (lokal 2026-11-22 23:05)
**Start:** 2026-11-22 22:55
**Senaste heartbeat:** 2026-11-22 23:05
**Global varianttotal:** 5/50 (J3:s screening oräknad)
**Deadline:** måndag 2026-11-23 22:00
**Läge:** KÖR. J2 och J6 startar.

**Källås (hämtning):** inga

## Jobb

| Jobb | Gren | Worktree | Steg | Varianter | Senaste SHA | Resultat | BLOCKED |
|---|---|---|---|---|---|---|---|
| J2 Elmodellen | auto/j2-el | C:\dev\kpif-auto\j2 | förregistrerad, bygger | 5/10 | 450a18e | – | – |
| J6 Arbetsförmedlingen | auto/j6-af | – | ej startad | – | – | – | – |
| J1 Hybrid | auto/j1-hybrid | – | väntar på J2 | 0/10 | – | – | – |
| J3 Katalogtest | auto/j3-katalog | – | väntar på J1 | 0/10 | – | – | – |
| J4 Detaljnivå | auto/j4-detalj | – | ledig plats | 0/10 | – | – | – |
| J5 Osäkerhet | auto/j5-osakerhet | – | ledig plats | 0/10 | – | – | – |
| J7 AI-indikator | auto/j7-ai | – | ledig plats | – | – | – | – |

## Logg
- 2026-11-22 22:55 Statusgren och worktree skapade från origin/main @ a8cd686. BRIEF.md sparad.
- 23:03 Ministeg OK: PYTHONPATH pekar på worktree, pytest 11 gröna, push till auto/status utan fråga. Backup data/observations.20261122.bak.parquet skapad.
- 23:03 kpif-auto-restart skapad (varje timme 00:30–21:30 måndag). **Varning:** appen sparade inte auto-läge på uppgiften; testväckningen fastnade på en behörighetsfråga och stoppades. Omstarter kan därför fastna. Huvudsessionen fortsätter så länge den kan.
- 23:03 Worktrees C:\dev\kpif-auto\j2 (auto/j2-el) och j6 (auto/j6-af) skapade från origin/main @ a8cd686, data kopierad.
- 11-22 23:05 J2 förregistrerad (V1–V5), auto/j2-el @ 450a18e.
