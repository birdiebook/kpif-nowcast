# Status: autonom körning 2 (Sverige på djupet)

**Lås:** orkestrerare 2026-11-23T08:26Z (lokal 2026-11-23 09:26) · heartbeat 2026-11-23T08:26Z
**Start:** 2026-11-23 · **Bas:** main @ 42b717b
**Varianter i körningen:** 0/30 (projektet totalt 23 + 0 = 23)
**Merge:** klara spår mergas till main av orkestreraren (ändrat 2026-11-23) · **Brief:** [BRIEF.md](BRIEF.md) · regler: `docs/autonom-korning-2.md` på main

## Spår

| Spår | Gren | Worktree | Steg | Varianter | Senaste SHA | Resultat / BLOCKED |
|---|---|---|---|---|---|---|
| K0 Prisleden | auto2/k0 | C:\dev\kpif-auto2\k0 | pågår: katalog + screening | 0/2 (screening oräknad) | 42b717b | – |
| K1 Drift | auto2/k1 | C:\dev\kpif-auto2\k1 | pågår: pipeline, workflows | – | 42b717b | – |
| K2 ML | auto2/k2 | C:\dev\kpif-auto2\k2 | pågår: förregistrering | 0/10 | 42b717b | – |
| K3 Förklaring | – | – | väntar | – | – | – |
| K4 Regionalt | – | – | väntar | – | – | – |
| K5 Sverigeläget v2 | – | – | väntar (K1, K3, K4) | – | – | – |
| K6 Om lätt | – | – | väntar | – | – | – |

## Källlås
- SCB, KI, FRED, Riksbanken, Medlingsinstitutet, Swedavia: K0

## Logg
- 2026-11-23 10:05: Johannes: agentic first. Orkestreraren mergar klara spår till main när pytest är grönt (CLAUDE.md "Agentiskt arbete", main 63a07c6). Syftesändringen ligger nu på main; grenen auto2/syfte är ersatt.
- 2026-11-23 09:50: Johannes: nytt syfte (inte lärprojekt; bästa möjliga lösning och bild av Sverige via KPIF). CLAUDE.md, vision.md, beslutslogg och K2-texten uppdaterade på grenen auto2/syfte (d77c022), merge beslutar Johannes. Spåragenterna informerade.
- 2026-11-23 09:35: K0, K1, K2 startade (agenter). Variantbudget: K2 10, K0 2, K6 ≤4, reserv 14.
- 2026-11-23: kpif-auto2-restart skapad (varje timme :19). Sparades utan auto-läge; Johannes har slagit på Auto i appen.
- 2026-11-23: ministeg: worktrees k0–k2 från origin/main, data kopierad, PYTHONPATH pekar på worktree, pytest 39 passed / 4 skipped.
