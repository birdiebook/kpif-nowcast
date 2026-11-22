# J3 resultat (urvalsevidens)

Körning: `experiments/runs/20261122T221405Z_j3_screen.csv`. Rangordnade tabeller för alla 45 serier och tre horisonter:
[results_raw.md](results_raw.md). Screeningen räknas inte mot taket; kombinationen räknas som 1 variant
(global total efter J3: **14/50**).

## Sammanfattning
| Horisont | Bas (MAE) | Bästa serie | Diff | p ensidigt (rå) | BH-q | Överlever BH (q < 0,10) |
|---|---|---|---|---|---|---|
| h=1, 2017-02..2026-10 | rb_updated 0,281 | ea_flash_goods | −0,004 | 0,22 | 1,00 | 0 av 45 |
| h=1, 2015–2026 | rb_updated 0,256 | ea_flash_goods | −0,004 | 0,22 | 1,00 | 0 av 45 |
| h=3 | Riksbanken 0,546 | jobads_ml | −0,006 | 0,027 | 0,98 | 0 av 45 |
| h=12 | Riksbanken 1,480 | fao_dairy (revised) | −0,006 | 0,25 | 0,99 | 0 av 45 |

Kombinationen (ingen överlevde BH, därför de tre med lägst rå p: ea_flash_goods, ea_flash_food,
ki_services): MAE 0,279 mot 0,281, p = 0,43, n = 117. Negativt.

## Tolkning
- **Inget håller.** Ingen katalogserie, i den förregistrerade enkla formen (säsongsdifferentierad
  månadsnyhet som linjär korrektion), tillför något utöver rb_updated eller Riksbanken. Det är ett
  giltigt utfall och stämmer med gissningen för h=3/12. För h=1 trodde jag på brent och euroområdets
  energi; ingen av dem hjälper.
- Varför hjälper J2:s el men inte katalogens energi? Elpriset finns inte i katalogen, och J2 använder
  energin genom energikomponentens vikt och säsong, inte som en fri korrektion på y/y. Brent ovanpå
  rb_updated ger inget, sannolikt för att drivmedel redan syns i rb_updated:s miss för t−1.
- h=3: jobads_ml har rå p 0,027 men BH-q 0,98, vilket är vad man väntar sig av en slumpträff bland 45.
- Inga revised-serier överlever, så revisionsläckage är inte aktuellt.

## Rekommendation
Behåll ingen serie. Nästa steg för h=1 är snarare J2-modellen i kombination (J1:s C1) än fler
makroserier. Värdet ligger i rätt data i rätt form, inte i bredd.
