# Status: autonom körning 3 (svensk data där överraskningarna sitter)

**Lås:** orkestrerare (molnsession) 2026-11-23T11:42Z · heartbeat 2026-11-23T11:42Z
**Start:** 2026-11-23 · **Bas:** main @ 129bbb0 · körning 2: STOP (bf11c0a)
**Varianter i körningen:** 0/6 (projektet totalt 51 + 0 = 51) · **Screening:** räknas inte mot taket
**Merge:** klara spår mergas till main av orkestreraren när pytest är grönt · **Brief:** [BRIEF.md](BRIEF.md) · regler: `docs/autonom-korning-2.md` på main, med ändringarna i briefen

**Miljö (avvikelse från briefen):** körningen går i en molncontainer (Linux), inte på `C:\dev`. Worktrees ligger under
`/home/user/kpif-auto3/<spår>`, grenar `auto3/<spår>`. Datan finns inte i containern från början, så allt hämtas från tomt
läge (`pipeline fetch`, samma väg som K2b:s onlinerepro). Nätet är en ny personlig miljö, `kpif-nowcast`, med en lista
över tillåtna källor (SCB, Riksbanken, Eurostat, KI, AF, Tillväxtanalys, Tillväxtverket, Kammarkollegiet, EI,
Hyresgästföreningen, Fastighetsägarna, FRED, NY Fed, FAO, Energinet, elprisetjustnu). Källås hålls med `flock` på
`/home/user/kpif-auto3/locks/<källa>.lock`.

## Spår

| Spår | Gren | Steg | Varianter | Senaste SHA | Resultat / BLOCKED | Tid / anrop / tokens |
|---|---|---|---|---|---|---|
| L1 Administrerade priser | auto3/l1 | väntar | – | – | – | – |
| L2 Resor | auto3/l2 | väntar | – | – | – | – |
| L3 Hyror | auto3/l3 | väntar | – | – | – | – |
| L4 Prospera | auto3/l4 | väntar | – | – | – | – |
| L5 El (rörliga avtal, nät) | auto3/l5 | väntar | – | – | – | – |
| L6 Kronan | auto3/l6 | väntar | – | – | – | – |
| L7 Snabb-KPI mot utfall | auto3/l7 | väntar | – | – | – | – |
| V2 Gemensam utvärdering | auto3/v2 | väntar (våg 1) | 0/6 | – | – | – |
| V3 Avslut | – | väntar (våg 2) | – | – | – | – |

## Källås
- Riksbanken: L4, L6 (turas om)
- SCB: L5, L7 (turas om)

## Logg
- 2026-11-23T11:42Z: körning 2 har STOP (bf11c0a). Körning 3 startad från main 129bbb0. Ny miljö `kpif-nowcast` med
  tillåtna källor (Default-miljön blockerade alla). Hämtning från tomt läge pågår (Energinet hastighetsbegränsar).
