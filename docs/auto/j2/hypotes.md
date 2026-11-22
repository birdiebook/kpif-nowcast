# J2 Elmodellen på lång historik: förregistrering

Skriven 2026-11-22 innan något fel för 2015–2026 har beräknats för någon av varianterna nedan.
Bas: origin/main @ a8cd686.

## Hypotes
Med elpriser från 2011-12 kan elkorrigeringen skattas från 2012 och utvärderas på 2015–2026.
Komponentmodellen med el (`comp_fuel_el`) blir bättre än `comp_fuel` även där, inte bara 2024–26.

**Min gissning innan:** Rå el (V1) ger liten förbättring, ca −0,01 till −0,02 pe i MAE, för att
säsongsfaktorn redan bär elprisets säsong (dubbelräkning). Fixen (V2/V3) ger ca −0,02 till −0,04 pe.
Rörliga avtal (V4) ger lite till eftersom andelen steg kraftigt efter 2022. Zonvikten (V5) spelar
ingen roll (SE3 och SE4 är starkt korrelerade). Ingen variant kommer i närheten av rb_updated
(0,256). Sannolikt klarar ingen DM p < 0,10 mot comp_fuel efter Holm, eftersom minsta upptäckbara
skillnad är ca 0,06–0,08 pe.

## Jämförelse och godkänt
- Jämförelsemodell: `comp_fuel` (drivmedel, korrigering tränad från 2005-01). Också rapporterat mot `rb_updated`.
- Godkänt (förbättringsplanens regel 5): MAE lägre än comp_fuel med DM p < 0,10 (tvåsidigt, absolutfel)
  på 2015–2026, och inte sämre på 2024–2026 (använd period, bara rapport).
- Holm-justering över de fem varianterna (V1–V5) mot comp_fuel. Råa p redovisas bredvid.
- Gemensamt urval: månader 2015-01..2026-10 där alla varianter, comp_fuel och rb_updated finns.

## Varianter (exakt lista, 5 st)
Alla: komponentmodellen (säsong + 12-månaders trend per komponent), energikomponentens fel
regresseras med expanderande fönster (OLS utan intercept, min 24 månader) från 2012-01.
Övriga komponenter oförändrade (ingen korrigering).

| # | Namn | Energikorrigering | Ändring |
|---|---|---|---|
| V1 | `j2_el_raw` | fuel_chg, el_chg | Som dagens ENERGY men tränad från 2012-01 i stället för 2021-12 |
| V2 | `j2_el_dev` | fuel_chg, el_dev | el_dev_t = el_chg_t − medel av el_chg samma kalendermånad de senaste upp till 5 åren (minst 1 år). Fixar dubbelräkningen |
| V3 | `j2_el_trendbase` | fuel_chg, el_chg | Alternativ fix: energikomponentens baslinje = bara 12-månaders trend (ingen säsongsfaktor), elens säsong får komma via el_chg |
| V4 | `j2_el_dev_var` | fuel_chg, el_dev × rörlig andel | Rörlig andel = (rörligt + timpris) i riket, TAB3571, månad t−1 (publiceras ~23:e i t, före deadline). Före 2013-04 fylls första kända värdet bakåt (bara träningsrader före 2015). **TAB3571 är reviderad i efterhand → revised=True, klarar varianten skärmen märks den "obekräftad (revisionsläckage möjligt)"** |
| V5 | `j2_el_dev_se3` | fuel_chg, el_dev (bara SE3) | Känslighet för zonvikten: SE3 100 % i stället för SE3/SE4 70/30. Konsumtionsviktade vikter per elområde kräver en källa vi inte har; därför en ytterpunkt i stället för en påhittad vikt |

## Januari (dokumentation, ingen variant)
Elnätsavgifter per 1 januari (TAB3950) publiceras först i maj. Januari år Y kan därför bara använda
ändringen till 1 januari Y−1. En enkel regel (förra årets nätprisändring som januaritillägg) är
möjlig men inte förregistrerad här, och testas inte.

## Informationsmängd
För mål t: KPIF och komponenter t.o.m. t−1, el och drivmedel för t (kända vid deadline dag 4 i t+1),
rörlig andel t.o.m. t−1. pytest `tests/test_j2_el.py` kräver att prognosen för t blir identisk
med och utan data efter t:s deadline.
