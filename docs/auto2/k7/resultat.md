# K7 Tjänstekomponenten: resultat (urvalsevidens)

Förregistrering: [hypotes.md](hypotes.md) (commit b27f89b, före körningen). Kod: `src/kpif_nowcast/k7_services.py`
(b8ed849). Körning: `experiments/runs/20261123T093401Z_k7_services.csv`. Alla tabeller: [results_raw.md](results_raw.md).

**Förbrukade varianter: 5 av 5** (T1 `k7_med_half`, T2 `k7_med_full`, T3 `k7_cal_half`, T4 `k7_cal_full`,
T5 `k7_k2_cal_full`). Körning 2: 18 av 30, projektet 41. Inga tillägg efter resultat.

## Vad som byggdes
- **Tjänstemodell A:** J2 V2:s tjänstedel med median i stället för medel av de fem senaste årens säsongsavvikelser
  (robust mot pandemisomrarna 2021–2022).
- **Tjänstemodell B:** A plus expanderande OLS (från 1995) på två regressorer: `easter_dev`, alltså hur många dagar
  av påskens resefönster (påskdagen −9 till +1) som ligger i månaden, mot femårssnittet, och `jan_dev`, alltså
  decemberårstakten för tjänster mot femårssnittet, bara i januari.
- Kombinationer: "half" = 0,5·rb_updated + 0,5·j2s, "full" = 50/50 + hela tjänsteändringen, T5 = `k2_avg_ens_s` +
  hela tjänsteändringen.
- `tests/test_k7_services.py`: alla fem prognoser för t är identiska med och utan data efter t:s deadline
  (2016-04, 2019-08, 2023-01, 2026-10). Det finns också tester av medianen, påskfönstret och regressorerna. Hela pytest är grönt (109 passed, 1 skipped).
- Ingen ny data. TAB6613 används inte (inget revisionsläckage utöver det J2 V2 redan har).

## Resultat 2015-02..2026-10, n = 141 (förregistrerat kriterium)

| Variant | MAE | Bas | diff mot bas | p ensidig rå | Holm p | diff mot andra ref. (p tvåsidig) |
|---|---|---|---|---|---|---|
| T1 `k7_med_half` | 0,216 | 50/50 (0,217) | −0,001 | 0,27 | 1 | +0,015 mot K2 (0,018) |
| T2 `k7_med_full` | 0,218 | 50/50 | +0,001 | 0,64 | 1 | +0,017 mot K2 (0,007) |
| T3 `k7_cal_half` | 0,216 | 50/50 | −0,001 | 0,31 | 1 | +0,015 mot K2 (0,022) |
| T4 `k7_cal_full` | 0,219 | 50/50 | +0,003 | 0,75 | 1 | +0,018 mot K2 (0,006) |
| T5 `k7_k2_cal_full` | 0,210 | `k2_avg_ens_s` (0,201) | +0,010 | 0,99 | 1 | −0,006 mot 50/50 (0,42) |

**Ingen variant klarade urvalsskärmen.** Ingen frysning och inget förslag till skuggprognos.

- 2024–2026 (använd, bara rapport, n = 34): T1 −0,001, T3 −0,002, T2 +0,006, T4 +0,007 mot 50/50 (0,246), T5 +0,021
  mot K2 (0,217).
- Per år: ingen variant vinner jämnt. "half" vinner −0,005 till −0,010 2015, 2023 och 2024 men förlorar 2026.
  "full" förlorar mest 2026 (+0,025). T5 är sämre än K2 i 9 av 12 år.
- **Tjänstedelen själv (pe av KPIF m/m):** 2015–2026: baslinjen 0,157, A 0,162, B 0,160. **Ren kontroll
  2000–2009 (n = 120, inte sedd före förregistreringen):** baslinjen 0,067, A 0,068, B 0,069. Ingen av modellerna
  slår den enkla femårssäsongen, varken under perioden jag tittat på eller den rena.
- Per kalendermånad 2015–2026: medianen hjälper som väntat i augusti (0,273 → 0,234) och februari. Men den förlorar mer i
  juni, juli och december. Påskregressorn minskar felet i mars och april (0,104 → 0,084, 0,196 → 0,185).
  Januariregressorn ökar felet i januari (0,256 → 0,264 2015–2026, 0,144 → 0,156 2000–2009).
- Koefficienter (B): påsken ger +0,009–0,010 pe per dag sedan 2016 (rätt tecken; sen påsk mot tidig ger ≈ ±0,05 pe
  i april). Före 2008 låg den nära noll. Januari: +0,05 pe per pe årstakt, stabil över hela perioden. Ändå hjälper
  den inte utanför urvalet.

## Gissningen innan
Fel i riktningen för modellerna, rätt i slutsatsen. Jag gissade att A och B skulle minska tjänstefelet med 2–10 %.
I stället ökade det med 2–3 %, även på den rena perioden 2000–2009. Att ingen variant skulle klara skärmen stämde.

## BLOCKED
Inget. Ingen ny datahämtning, inga nya paket.

## Vad lärde vi oss
1. **Tjänstefelet är till största delen resor och går inte att få bort med säsongs- och kalendertrick.**
   Paketresor, flyg och logi står för ~75 % av tjänstefelets varians. Femårsmedlet är svårt att slå. Medianen
   kastar bort för mycket information i normala år, mer än den vinner på pandemisomrarna. Det gäller också
   2000–2009, då det inte fanns några avvikande år.
2. **Påskeffekten finns men är liten** (≈ 0,01 pe per påskdag i månaden, ±0,05 pe i april). Den förklarar bara en
   bråkdel av aprilfelen, som är upp till 0,4 pe. Den del av påskeffekten som går att förutse ligger redan till stor del i
   femårssnittet.
3. **Januariomprissättningen skalar inte förutsägbart med förra årets tjänsteinflation.** Den stora missen 2023
   (−0,83 pe) var en engångshändelse som en regressor på decemberårstakten inte fångar utan att förlora andra år.
4. **Rättelsen ska inte läggas ovanpå K2.** K2-ensemblen har redan lärt sig en del av tjänstemissen
   (via `core_dev` och senaste missar). En extra tjänstejustering ovanpå den förstör mer än den ger (+0,010).
5. **Slutsats för prognosen:** med den information vi har vid deadline är tjänstedelen nära oförutsägbar utöver
   säsong och trend. För att komma vidare krävs riktiga prisdata för resor (bokningspriser för charter och flyg
   för målmånaden). Det finns inte bland de fria källor vi har. Annars får man acceptera felet och låta
   osäkerhetsbandet (J5) spegla att sommar, april och januari är svårare. Nästa förbättring av punktprognosen
   bör sökas i livsmedel (29 % av kvadratfelet 2024–2026) snarare än i tjänster.
