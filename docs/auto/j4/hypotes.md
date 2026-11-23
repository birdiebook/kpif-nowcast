# J4 KPIF underifrån på detaljnivå: förregistrering

Skriven 2026-11-22 innan något fel för 2015–2026 har beräknats för varianterna nedan.
Bas: origin/main @ a8cd686. Data: TAB6613 (KPIF per COICOP 2018), nivå 2 (43 grupper),
bidrag till KPIF:s månadsförändring (`effect_month`, pe). Summan av bidragen avviker från KPIF m/m
med i snitt 0,004 pe (avrundning).

**Revisionsvarning:** värden före 2026 är SCB:s omräkning till COICOP 2018 (delvis modellskattad), inte
det som publicerades då. Allt som bygger på TAB6613 är därför `revised`. En variant som klarar skärmen
märks **"obekräftad (revisionsläckage möjligt)"**. SCB:s detaljindex för t används aldrig för t (bara t.o.m. t−1).

## Hypotes
De stora överraskningarna sitter i några få delindex: el (04.5), drift av fordon inkl. drivmedel (07.2),
persontransporter inkl. flyg (07.3), paketresor (09.8) och logi (11.2). Med egna modeller för dem blir
summan bättre än femgruppsmodellen.

**Min gissning innan:** D1 (bara säsong + trend per grupp) är ungefär lika bra som comp_fuel eller något
sämre (fler, brusigare skattningar). D2 (el och drivmedel på rätt delindex) blir klart bättre än comp_fuel,
i nivå med J2:s el-modell (~0,25). Påsken (D3) ger lite till, mest i mars och april. Ingen variant nära
att skiljas från rb_updated.

## Jämförelse och godkänt
- Jämförelsemodell: `comp_fuel` (femgruppsmodellen på origin/main). Också rapporterat mot `rb_updated`.
- Godkänt (regel 5): lägre MAE än comp_fuel med DM p < 0,10 (tvåsidigt) på 2015-01..2026-10, Holm över
  de tre varianterna, och inte sämre 2024–2026 (använd, bara rapport).
- Diagnostik (inte variant): vilka 10–15 grupper bidrar mest till D1:s fel 2015–26
  (andel av totalfelets varians, cov(e_i, e_tot)/var(e_tot), och MAE per grupp).

## Varianter (exakt lista, 3 st)
Alla: per grupp `seasonal_trend_additive` (5-årig säsong + 12-mån trend) på bidraget, data t.o.m. t−1,
grupper utan data före sin start = 0. Summa → KPIF m/m → y/y via känt index. Korrektioner med
expanderande OLS utan intercept, träning från 2012-01, minst 24 månader.

| # | Namn | Vad |
|---|---|---|
| D1 | `j4_detail_base` | Bara baslinjen per grupp |
| D2 | `j4_detail_energy` | D1 + korrektion av 04.5 på el_dev (el_chg minus snitt för samma kalendermånad senaste ≤5 år) och av 07.2 på fuel_chg |
| D3 | `j4_detail_energy_easter` | D2 + påskkorrektion för 07.3, 09.8 och 11.2 var för sig: regressor = påskdummy_t (påskdagen i månad t) minus snittet av påskdummyn samma kalendermånad senaste ≤5 år |

pytest `tests/test_j4_detail.py`: identisk prognos för t med och utan data efter t:s deadline.
