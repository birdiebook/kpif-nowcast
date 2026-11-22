# J4 resultat (urvalsevidens, obekräftat)

Körning: `experiments/runs/20261122T222015Z_j4_detail.csv`. Full tabell och diagnostik: [results_raw.md](results_raw.md).
Globalt varianttotal vid körningen: **17/50**. TAB6613 är SCB:s omräkning (revised): allt nedan är
**obekräftat (revisionsläckage möjligt)**.

## 2015-01..2026-10, n = 141
| Variant | MAE | Diff mot comp_fuel | DM p (rå, tvåsidigt) | Holm p | DM p mot rb_updated |
|---|---|---|---|---|---|
| D2 j4_detail_energy | 0,243 | −0,072 | 0,003 | 0,010 | 0,57 |
| D3 j4_detail_energy_easter | 0,243 | −0,072 | 0,003 | 0,010 | 0,57 |
| D1 j4_detail_base | 0,335 | +0,019 | 0,078 | 0,078 | 0,001 |
| comp_fuel | 0,316 | – | – | – | 0,03 |
| rb_updated | 0,256 | | | | – |

2024–2026 (använd): D2 0,246, D3 0,256, D1 0,447, comp_fuel 0,443. Ingen variant sämre än comp_fuel.

## Tolkning
- D2 och D3 klarade urvalsskärmen mot comp_fuel, men **obekräftat** (omräknad detaljdata).
- **Detaljnivån i sig hjälper inte:** D1 (bara säsong + trend per grupp) är *sämre* än femgruppsmodellen
  (+0,019, p = 0,08). Hela vinsten kommer från el och drivmedel på rätt delindex, och D2 hamnar exakt
  där J2:s V2 hamnar (0,243) utan detaljdata. J2 V2 är därför att föredra: samma träffsäkerhet, ingen
  revisionsrisk.
- **Påsken (D3) tillför inget** på 2015–26 och är något sämre 2024–26.
- Diagnostik (D1, andel av totalfelets varians): el 61 %, livsmedel 9 %, paketresor 7 %,
  persontransporter 4 %. Efter el- och drivmedelskorrektion (D3) är de största källorna paketresor 18 %,
  livsmedel 17 %, el 13 %, persontransporter 9 %. Livsmedel och resor är de som återstår.
- Gissningen innan stämde: D1 lite sämre, D2 i nivå med J2, påsken liten.

## Frysning
D2 klarade skärmen och fryses enligt regeln som skuggprognos från 2026-12 (auto/j4-detalj, SHA i
docs/auto/j4.md), märkt **obekräftad (revisionsläckage möjligt)**. Rekommendation: följ hellre J2 V2,
som ger samma sak utan detaljdata.
