# Förklaring av KPIF-prognosen för november 2026

- **KPIF november 2026: prognos 2,1 %** (upp från 1,1 % i oktober; 2,05 med två decimaler, månadsförändring +0,67 %).
- Störst bidrag till förändringen i årstakt: energi +0,87 pe (prognos +1,18 pe på månadstakten mot +0,32 samma månad i fjol).
- Elpriset (22 dagar hittills) steg med 0,96 kr/kWh mot förra månaden (2,00 kr/kWh), vilket ger +0,91 pe på årstakten; oljepriset i kronor (drivmedel) −24 % ger −0,32 pe. Säsong och trend mot samma månad i fjol ger +0,33 pe.
- Övriga komponenter (förändring i årstakt): tjänster +0,18, varor −0,03, livsmedel −0,10, kapitalstock +0,01 pe.
- Osäkerhet (J5:s EWMA-band, förslag): 50 % 1,8–2,3 %, 80 % 1,5–2,6 %.
- Skuggmodeller: J2 V2 1,9 % (−0,19 pe mot skarpa; elen räknas som avvikelse från hur priset brukar ändras samma månad, +0,61 kr/kWh); 50/50 1,5 % (−0,53 pe; Riksbanken 1,7 % i 2026:3, senaste miss −0,55 pe ger rb_updated 1,2 %); K2-kandidaten 1,7 % (50/50 1,52 +0,16 pe; största ridge-bidrag el_dev +0,03 pe).
- Senaste miss (oktober 2026): prognos 1,28 %, utfall 1,1 %, fel +0,18 pe; störst tjänster +0,17 pe.

## Bidrag per komponent

Prognos 2,05 % i årstakt, +0,67 % på månaden. Bidragen i pe av KPIF:s månadsförändring (TAB6628); sista kolumnen är bidraget till förändringen från 1,1 % (2026-10), inklusive avrundning +0,025 i summaraden.

| komponent    |   prognos m/m (pe) |   trend |   säsong |   el |   drivmedel |   samma månad i fjol |   bidrag till ändrad årstakt |
|:-------------|-------------------:|--------:|---------:|-----:|------------:|---------------------:|-----------------------------:|
| energi       |              1.18  |   0.087 |    0.505 |  0.9 |      -0.312 |                0.323 |                        0.869 |
| tjänster     |             -0.255 |   0.062 |   -0.317 |  0   |       0     |               -0.43  |                        0.177 |
| varor        |             -0.143 |  -0.007 |   -0.137 |  0   |       0     |               -0.118 |                       -0.025 |
| livsmedel    |             -0.136 |  -0.076 |   -0.06  |  0   |       0     |               -0.039 |                       -0.099 |
| kapitalstock |              0.024 |   0.029 |   -0.005 |  0   |       0     |                0.018 |                        0.006 |
| summa        |              0.669 |   0.095 |   -0.013 |  0.9 |      -0.312 |               -0.247 |                        0.954 |

## Nyhetsdekomposition (förändring i årstakt mot förra utfallet, pe)

| källa | pe |
|---|---|
| säsong + trend mot samma månad i fjol | +0,333 |
| el | +0,912 |
| drivmedel | −0,317 |
| avrundning | +0,025 |
| **summa** | **+0,954** |

## Skuggmodeller mot den skarpa

- J2 V2: 1,86 % (−0,19 pe). Skillnaden kommer bara från energin: el −0,32, drivmedel +0,13 pe.
- 50/50: 1,52 % (−0,53 pe) = hälften Riksbankens bana (2026:3, 1,73 %, 3 mån efter brytpunkt) −0,16 + hälften senaste Riksbanksmissen −0,27 + hälften J2 V2 −0,10 pe.
- K2 `k2_avg_ens_s`: 1,68 % = 50/50 1,52 + ½ ridge +0,066 + ½ boosting +0,097 pe. Största ridge-bidrag: `el_dev` +0,033, `energy_x_age` +0,027, `fuel_chg` −0,025.

## Osäkerhet (J5 U4 EWMA, förslag)

50 % 1,76–2,33, 80 % 1,46–2,62, 90 % 1,29–2,86 % (238 tidigare fel, 2007-01..2026-10 (comp_fuel före 2023-12, sedan den skarpa modellen)).

Skarp prognosfil `forecasts/2026-11.json` (PRELIMINARY, 2026-11-22T21:02:38): 2,09 %, el 21 dagar, drivmedel till 2026-11-17. Förklaringen ovan är samma modell körd med dagens data (2,05 %, manuell justering i filen +0,00 pe); övrig skillnad beror på data som kommit efter filens körning (t.ex. fler dagars elpriser).

Informationsmängd: KPIF till och med 2026-10, energipriser för 2026-11, Riksbanksbana 2026:3; deadline 2026-12-04.
