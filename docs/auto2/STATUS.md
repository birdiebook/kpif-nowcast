# Status: autonom körning 2 (Sverige på djupet)

**Lås:** orkestrerare 2026-11-23T09:25Z · heartbeat 2026-11-23T09:25Z
**Start:** 2026-11-23 · **Bas:** main @ 42b717b
**Varianter i körningen:** 13/30 (projektet totalt 23 + 13 = 36) · **main:** 51fa62f · **parallellt:** 6 (höjt från 3)
**Merge:** klara spår mergas till main av orkestreraren (ändrat 2026-11-23) · **Brief:** [BRIEF.md](BRIEF.md) · regler: `docs/autonom-korning-2.md` på main

## Spår

| Spår | Gren | Worktree | Steg | Varianter | Senaste SHA | Resultat / BLOCKED |
|---|---|---|---|---|---|---|
| K0 Prisleden | auto2/k0 | k0 | **KLAR, mergad** (25a6a6e) | 2/2 | d1a2a2f | 29 serier (PPI, KPIF-XE, varor/tjänster, KI prisplaner, FRED-råvaror, räntor/SWESTR). Screening: 0/29 överlever BH. K0-C2 på 50/50: 0,226 mot 0,232, Holm 0,097, obekräftad (revisionsläckage möjligt) → inte fryst. **Inget håller.** BLOCKED: Medlingsinstitutet (PDF/sessionsproxy), Swedavia (403), hotellnätter (slutar 2021). |
| K1 Drift | auto2/k1 | k1 | **KLAR, mergad** (a6fe532) | – | 3d376c1 | pipeline.py, shadow.py, 2 workflows (schedule/dispatch, nu aktiva på main), DuckDB + 12 datatester, champion/challenger i SCORECARD. Offline-repro identisk. Onlinerepro → K2b. |
| K2 ML | auto2/k2 | k2 | **KLAR, mergad** (806e943) | 9/10 | 4ef395e | Urvalsevidens (34 varianter totalt): k2_avg_ridge_l 0,199 (Holm 0,014), k2_avg_ens_s 0,201 (0,055), k2_avg_ridge_s 0,206 (0,083) mot 50/50 0,217 → **klarade urvalsskärmen**. Granskas oberoende i K2b innan skugga. |
| K2b Granskning + K2-skugga + onlinerepro | auto2/k2b | k2b | pågår | 0 | 25a6a6e | – |
| K3 Förklaring | auto2/k3 | k3 | **KLAR, mergad** (52191e2) | 0 | 4f7a154 | explain.py: bidrag per komponent, nyhetsdekomposition, felet per komponent, EWMA-band. 2026-11: 2,05 % (el +0,91, drivmedel −0,32). Fel 2015–26: tjänster 37 % av kvadratfelet, energi 21, varor 20, livsmedel 20. Inkopplat i pipeline monthly. |
| K4 Regionalt | auto2/k4 | k4 | **KLAR, mergad** (f74d2bb) | 0 | d60864c | 241 länsserier (AF andel/antal/varsel, SCB BAS/AKU/småhuspris/FPI/folkmängd, Tillväxtanalys konkurser), kvalitet grön (AF-länssumma = riket alla 370 mån). Skåne 8,2 % / Norrbotten 3,4 %, lägre än i fjol i alla län. BLOCKED: varsel per län efter 2026-03 (AF slutade med fil), GeoJSON (konto/GIS), FPI per kvartal. |
| K5 Sverigeläget v2 | auto2/k5 | k5 | pågår (dashboard v2, månadsbrev) | – | f74d2bb | – |
| K6 Om lätt | auto2/k6 | k6 | **KLAR, mergad**  | 2/4 | 0734d09 | Vintages TAB6613 BLOCKED (finns inte); ersatt med kontroll gammal/ny HIKP: el och drivmedel identiska (r 1,000) → J4 D2:s vinst är ingen revisionseffekt. Nordisk el: FI −0,011 (Holm 0,58), DK +0,002 (0,86), klarade inte skärmen; el-HIKP i FI/DK följer spot med en månads lagg, metoden är SCB-specifik. |
| K7 Tjänster | auto2/k7 | k7 | pågår | 0/5 | 51fa62f | – |
| K8 Livsmedel | auto2/k8 | k8 | pågår | 0/4 | 51fa62f | – |
| K9 Horisont 3–12 | auto2/k9 | k9 | pågår | 0/4 | 51fa62f | – |
| K10 Pages-dashboard (fas 6) | – | – | väntar (K5) | – | – | – |
| K11 Granskning publiceringsdatum | auto2/k11 | k11 | pågår | 0 | 51fa62f | – |

## Källlås
- SCB (regional), Arbetsförmedlingen: K4
- Riksbanken, KI, Eurostat: K6 (K2b får göra en liten onlinerepro mot SCB)

## Logg
- 2026-11-23T09:25Z: Johannes: K0–K6 använde ~20 % av ett 5-timmarsfönster. Parallellitet höjd till 6 och backloggen utökad med K7 tjänster (37 % av felet), K8 livsmedel, K9 horisont 3–12, K10 Pages (efter K5) och K11 granskning av publiceringsfördröjningar. Variantbudget: K7 5, K8 4, K9 4 → max 26/30.
- 2026-11-23T09:22Z: K6 och K4 klara, mergade (96 passed på main f74d2bb). K5 startad. Kalibrering uppdaterad.
- 2026-11-23T09:05Z: K3 klar, mergad (87 passed på main). K6 startad. CLAUDE.md fick "Storleksbedömning" och docs/agentkalibrering.md (564c508).
- 2026-11-23T08:49Z: K2, K1, K0 klara; pytest grönt på sammanslaget main (74 passed); mergade och pushade. K3, K4, K2b startade från 25a6a6e.
- 2026-11-23 10:05: Johannes: agentic first. Orkestreraren mergar klara spår till main när pytest är grönt (CLAUDE.md "Agentiskt arbete", main 63a07c6). Syftesändringen ligger nu på main; grenen auto2/syfte är ersatt.
- 2026-11-23 09:50: Johannes: nytt syfte (inte lärprojekt; bästa möjliga lösning och bild av Sverige via KPIF). CLAUDE.md, vision.md, beslutslogg och K2-texten uppdaterade på grenen auto2/syfte (d77c022), merge beslutar Johannes. Spåragenterna informerade.
- 2026-11-23 09:35: K0, K1, K2 startade (agenter). Variantbudget: K2 10, K0 2, K6 ≤4, reserv 14.
- 2026-11-23: kpif-auto2-restart skapad (varje timme :19). Sparades utan auto-läge; Johannes har slagit på Auto i appen.
- 2026-11-23: ministeg: worktrees k0–k2 från origin/main, data kopierad, PYTHONPATH pekar på worktree, pytest 39 passed / 4 skipped.
