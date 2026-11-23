# J5 resultat (urvalsevidens)

Körning: `experiments/runs/20261122T222244Z_j5_intervals.csv` (kolumnen MAE innehåller pinball-förlusten). Full tabell och träffgrad per år:
[results_raw.md](results_raw.md). Punktprognos comp_fuel, sekventiella intervall, utvärdering 2015-01..2026-10
(n = 142, minst 36 månaders inkörning). Globalt varianttotal: **23/50**. Konfidensintervall: Clopper-Pearson 95 %
(för smala, eftersom träffarna är autokorrelerade).

## Alla månader
| Metod | 50 % (KI) | 80 % (KI) | 90 % (KI) | Inom ±5 pe? | Pinball | Bredd 80 % |
|---|---|---|---|---|---|---|
| U1 abs_all | 40 (32–49) | 62 (53–70) | 77 (70–84) | nej | 0,094 | 0,62 |
| U2 abs_36 | 49 (41–58) | 77 (70–84) | 89 (82–93) | **ja** | 0,086 | 0,98 |
| U3 signed_all | 40 (32–49) | 63 (54–71) | 73 (64–80) | nej | 0,096 | 0,61 |
| U4 ewma | 52 (44–61) | 80 (72–86) | 89 (82–93) | **ja** | **0,085** | 0,99 |
| U5 scaled_energy | 40 (32–49) | 68 (60–76) | 76 (68–83) | nej | 0,086 | 0,82 |
| U6 qreg_energy | 35 (27–43) | 63 (55–71) | 77 (69–83) | nej | 0,092 | 0,69 |

## Oroliga och lugna månader (översta/nedersta tredjedelen av |el_chg|, n = 48 vardera)
| Metod | Orolig 50/80/90 | Lugn 50/80/90 |
|---|---|---|
| U1 abs_all | 33 / 44 / 60 | 50 / 79 / 92 |
| U2 abs_36 | 42 / 67 / 79 | 54 / 88 / 98 |
| U4 ewma | 40 / 71 / 81 | 60 / 85 / 96 |
| U5 scaled_energy | 38 / 67 / 73 | 44 / 75 / 81 |

## Tolkning
- **Hypotesen höll delvis.** Felbanden är mycket riktigt för smala i oroliga månader (U1: 44 % träff i 80 %-bandet).
  Men gissningen om *varför* var fel: det är inte främst elprisets svängning i månaden som driver felen, utan
  att felnivån skiftar över tid (lugnt 2015–2020, stora fel 2021–2023). Metoder som glömmer gamla fel
  (U2 rullande 36 mån, U4 EWMA) klarar det; att skala med |el_chg| (U5, U6) gör det inte.
- U4 och U2 klarade urvalsskärmen (alla tre nivåerna inom ±5 pe). U4 har något lägre pinball (0,0852 mot 0,0855),
  en skillnad som är försumbar.
- Inget band är rätt i oroliga månader. U4 täcker 71 % i 80 %-bandet där och 85 % i lugna. Banden är alltså
  fortfarande för smala när det stormar, bara mindre fel än i dag.
- Gissningen att expanderande metoder skulle ligga inom ±5 pe var fel; de undertäcker med 10–18 pe.

## Valt och förslag (aktiveras inte)
**U4 `j5_ewma`** (λ = 0,9, golv 0,05). Se [forslag_forecast.md](forslag_forecast.md) för hur det skulle kopplas in
i `forecast.py`. Filen är inte ändrad (briefen förbjuder det). Johannes beslutar.
