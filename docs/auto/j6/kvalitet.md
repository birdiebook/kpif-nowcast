# J6 Arbetsförmedlingens data: resultat och kvalitetskontroll

Hämtat 2026-11-22 från "tidigare statistik" (filerna för 2026-10, uppladdade 2026-11-10 enligt
tidsstämpeln i nedladdningslänken). Inga modellvarianter: J6 är ett datajobb och räknas inte mot taket.

## Serier
| Nyckel | Period | n | Luckor | Negativa | Min | Max | Största |y/y| |
|---|---|---|---|---|---|---|---|
| `af_varsel` | 1992-01–2026-10 | 418 | 0 | 0 | 1 176 | 42 420 | 1 189 % (2020-03) |
| `af_inskrivna_arbetslosa` | 1996-01–2026-10 | 370 | 0 | 0 | 194 950 | 624 645 | 77 % (2009-08) |
| `af_oppet_arbetslosa` | 1996-01–2026-10 | 370 | 0 | 0 | 122 187 | 510 583 | 77 % (2009-05) |

Extremvärdena är verkliga händelser (pandemivarslen mars 2020, finanskrisen 2009). Kvalitetskontrollen är godkänd.

## Brott och hur de hanteras
- **Åldersgrupper (inskrivna, öppet arbetslösa):** 16–64 år t.o.m. 2022, 16–65 år 2023–2025, 16–66 år från 2026.
  Ingen överlappning publiceras, så serien lagras som publicerad. Brottet syns inte i datan: januariförändringen
  för inskrivna arbetslösa var +1,6 % 2023 och +1,0 % 2026, mot +1,1 till +1,9 % andra år 2015–2025
  (öppet arbetslösa: +3,2 % 2023, något över intervallet −0,1 till +2,8 %). Effekten bedöms som liten
  men kan inte mätas exakt.
- **SNI-byten (varsel):** 2002 → 2007 (2010) → 2025 (2025-12). Bara riket totalt används, och det beror inte på
  branschindelningen. 1992–2004 från branschbladets "Summa", 2005– från avdelningsbladens "Totalsumma".
  Överlapp 2005–2009: snittavvikelse 35 personer (0,9 %), max 292. 2010–2019: snitt 1 (0,02 %).
- **Revision:** varselserien från 2019-11 uppdaterades 2025-06-30 (står i filen), därför `revised=True`.
  För inskrivna finns ingen sådan uppgift i filen, men det är inte verifierat att serien aldrig revideras.

## Publiceringsfördröjning
Oktoberfilerna laddades upp 2026-11-10, alltså ca 10 dagar efter månadens slut. `lag_days = 15`
(avrundat mot senare publicering). Vid vår deadline (dag 4 i t+1) är alltså månad t−1 känd, inte t.
Det kontrolleras i `tests/test_catalog_af.py`.

## Teknik
- Länkarna byts varje månad: sidan skrapas efter filnamnsmönstret (`web-varsel-bransch-199201-ÅÅÅÅ-MM.xlsx`,
  `web-sok-riket-ÅÅÅÅ-MM.xlsx`). En fil vars namn redan finns i cachen hämtas inte igen. Högst 3 försök
  med exponentiell backoff.
- venv saknar openpyxl. I stället för att ändra den delade miljön läses xlsx med en liten egen läsare
  (`sources/xlsx_lite.py`, zip + XML).
- Licens: Arbetsförmedlingen anger att statistiken får användas med källangivelse. Det är inte
  verifierat mot en licenstext i den här körningen.

## Gjort
- `python -m kpif_nowcast.observations af_varsel af_inskrivna_arbetslosa af_oppet_arbetslosa` (i worktreen).
- `python -m kpif_nowcast.sverige_dashboard`: serierna finns i `outputs/sverige/*.json` (y/y, tecken −1).
  **Inte uppladdat** till dashboarden i Claude Data; det gör Johannes (eller nästa veckohämtning efter merge).
- `docs/datakatalog.md` genererad på nytt (67 serier).
