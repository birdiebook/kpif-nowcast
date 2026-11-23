# Status: autonom körning 2 (Sverige på djupet)

**Lås:** orkestrerare 2026-11-23T08:49Z · heartbeat 2026-11-23T08:49Z
**Start:** 2026-11-23 · **Bas:** main @ 42b717b
**Varianter i körningen:** 11/30 (projektet totalt 23 + 11 = 34) · **main:** 25a6a6e
**Merge:** klara spår mergas till main av orkestreraren (ändrat 2026-11-23) · **Brief:** [BRIEF.md](BRIEF.md) · regler: `docs/autonom-korning-2.md` på main

## Spår

| Spår | Gren | Worktree | Steg | Varianter | Senaste SHA | Resultat / BLOCKED |
|---|---|---|---|---|---|---|
| K0 Prisleden | auto2/k0 | k0 | **KLAR, mergad** (25a6a6e) | 2/2 | d1a2a2f | 29 serier (PPI, KPIF-XE, varor/tjänster, KI prisplaner, FRED-råvaror, räntor/SWESTR). Screening: 0/29 överlever BH. K0-C2 på 50/50: 0,226 mot 0,232, Holm 0,097, obekräftad (revisionsläckage möjligt) → inte fryst. **Inget håller.** BLOCKED: Medlingsinstitutet (PDF/sessionsproxy), Swedavia (403), hotellnätter (slutar 2021). |
| K1 Drift | auto2/k1 | k1 | **KLAR, mergad** (a6fe532) | – | 3d376c1 | pipeline.py, shadow.py, 2 workflows (schedule/dispatch, nu aktiva på main), DuckDB + 12 datatester, champion/challenger i SCORECARD. Offline-repro identisk. Onlinerepro → K2b. |
| K2 ML | auto2/k2 | k2 | **KLAR, mergad** (806e943) | 9/10 | 4ef395e | Urvalsevidens (34 varianter totalt): k2_avg_ridge_l 0,199 (Holm 0,014), k2_avg_ens_s 0,201 (0,055), k2_avg_ridge_s 0,206 (0,083) mot 50/50 0,217 → **klarade urvalsskärmen**. Granskas oberoende i K2b innan skugga. |
| K2b Granskning + K2-skugga + onlinerepro | auto2/k2b | k2b | pågår | 0 | 25a6a6e | – |
| K3 Förklaring | auto2/k3 | k3 | pågår | – | 25a6a6e | – |
| K4 Regionalt | auto2/k4 | k4 | pågår | – | 25a6a6e | – |
| K5 Sverigeläget v2 | – | – | väntar (K3, K4) | – | – | – |
| K6 Om lätt | – | – | väntar | ≤4 | – | – |

## Källlås
- SCB (regional), Arbetsförmedlingen: K4 (K2b får göra en liten onlinerepro mot SCB)

## Logg
- 2026-11-23T08:49Z: K2, K1, K0 klara; pytest grönt på sammanslaget main (74 passed); mergade och pushade. K3, K4, K2b startade från 25a6a6e.
- 2026-11-23 10:05: Johannes: agentic first. Orkestreraren mergar klara spår till main när pytest är grönt (CLAUDE.md "Agentiskt arbete", main 63a07c6). Syftesändringen ligger nu på main; grenen auto2/syfte är ersatt.
- 2026-11-23 09:50: Johannes: nytt syfte (inte lärprojekt; bästa möjliga lösning och bild av Sverige via KPIF). CLAUDE.md, vision.md, beslutslogg och K2-texten uppdaterade på grenen auto2/syfte (d77c022), merge beslutar Johannes. Spåragenterna informerade.
- 2026-11-23 09:35: K0, K1, K2 startade (agenter). Variantbudget: K2 10, K0 2, K6 ≤4, reserv 14.
- 2026-11-23: kpif-auto2-restart skapad (varje timme :19). Sparades utan auto-läge; Johannes har slagit på Auto i appen.
- 2026-11-23: ministeg: worktrees k0–k2 från origin/main, data kopierad, PYTHONPATH pekar på worktree, pytest 39 passed / 4 skipped.
