# Status: autonom körning 2 (Sverige på djupet)

**Lås:** orkestrerare 2026-11-23T07:32Z (lokal 2026-11-23 08:32) · heartbeat 2026-11-23T07:32Z
**Start:** 2026-11-23 · **Bas:** main @ 42b717b
**Varianter i körningen:** 0/30 (projektet totalt 23 + 0 = 23)
**Brief:** [BRIEF.md](BRIEF.md) · regler: `docs/autonom-korning-2.md` på main

## Spår

| Spår | Gren | Worktree | Steg | Varianter | Senaste SHA | Resultat / BLOCKED |
|---|---|---|---|---|---|---|
| K0 Prisleden | auto2/k0 | C:\dev\kpif-auto2\k0 | ministeg klart (pytest 39 ok) | 0 (screening oräknad) | 42b717b | – |
| K1 Drift | auto2/k1 | C:\dev\kpif-auto2\k1 | worktree klar | – | 42b717b | – |
| K2 ML | auto2/k2 | C:\dev\kpif-auto2\k2 | worktree klar | 0/10 | 42b717b | – |
| K3 Förklaring | – | – | väntar | – | – | – |
| K4 Regionalt | – | – | väntar | – | – | – |
| K5 Sverigeläget v2 | – | – | väntar (K1, K3, K4) | – | – | – |
| K6 Om lätt | – | – | väntar | – | – | – |

## Källlås
(ingen)

## Logg
- 2026-11-23: ministeg: worktrees k0–k2 från origin/main, data kopierad, PYTHONPATH pekar på worktree, pytest 39 passed / 4 skipped.
