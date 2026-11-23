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
| L1 Administrerade priser | auto3/l1 | bygger (våg 1) | – | – | – | – |
| L2 Resor | auto3/l2 | bygger (våg 1) | – | – | – | – |
| L3 Hyror | auto3/l3 | bygger (våg 1) | – | – | – | – |
| L4 Prospera | auto3/l4 | bygger (våg 1) | – | – | – | – |
| L5 El (rörliga avtal, nät) | auto3/l5 | bygger (våg 1) | – | – | – | – |
| L6 Kronan | auto3/l6 | bygger (våg 1) | – | – | – | – |
| L7 Snabb-KPI mot utfall | auto3/l7 | bygger (våg 1) | – | – | – | – |
| V2 Gemensam utvärdering | auto3/v2 | väntar (våg 1) | 0/6 | – | – | – |
| V3 Avslut | – | väntar (våg 2) | – | – | – | – |

## Källås
- Riksbanken: L4, L6 (turas om)
- SCB: L5, L7 (turas om)

## Logg
- 2026-11-23T11:50Z: våg 1 startad: L1–L7 parallellt i ett arbetsflöde (bygg → oberoende granskning av fördröjningar/läckage → rättning). Worktrees från main 129bbb0.
- 2026-11-23T11:42Z: körning 2 har STOP (bf11c0a). Körning 3 startad från main 129bbb0. Ny miljö `kpif-nowcast` med
  tillåtna källor (Default-miljön blockerade alla). Hämtning från tomt läge pågår (Energinet hastighetsbegränsar).
