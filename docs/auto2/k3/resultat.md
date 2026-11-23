# K3 Förklarade prognoser – resultat

**Förbrukade varianter: 0.** K3 bygger ingen ny prognosserie. Allt är exakta räkneidentiteter över prognoser som
redan finns: den skarpa modellen (`component_fuel_el_v1`), J2 V2 (`j2_el_dev`), J1 C1 50/50 och K2:s kandidat
`k2_avg_ens_s`. Därför finns ingen förregistrering och inga DM-tester. `forecast.py` och `forecasts/<månad>.json`
är orörda.

## Vad som byggdes

- `src/kpif_nowcast/explain.py`. För varje prognosmånad t:
  - **Bidrag per komponent** (TAB6628: energi, tjänster, varor, livsmedel, kapitalstock) i pe av KPIF:s
    månadsförändring, uppdelade på trend (12-månadersmedel), säsong samt el och drivmedel för energi. Bidragen
    summerar exakt till modellens månadsprognos.
  - **Nyhetsdekomposition** av förändringen i årstakt sedan förra utfallet. Den är exakt:
    `yy_hat[t] − yy[t−1] = Σ_c k·(f_c[t] − e_c[t−12]) + avrundning` med `k = I[t−1]/I[t−12]`. Den delas både
    per komponent och per drivare: säsong + trend mot samma månad i fjol, el och drivmedel. Avrundningen är
    SCB:s avrundning av bidragen och av den officiella årstakten, alltid under 0,1 pe.
  - **Senaste miss:** den skarpa modellens prognos för t−1 mot utfallet, per komponent, och Riksbankens senaste
    miss (korrektionen i rb_updated).
  - **Skuggmodellerna mot den skarpa.** För J2 V2 skiljer bara energikorrektionen, uppdelad på el och drivmedel.
    För 50/50 gäller `50/50 − skarp = ½(RB_t − skarp) + ½·senaste RB-miss + ½(J2 − skarp)`. För K2:s
    `k2_avg_ens_s` gäller `= 50/50 + ½ ridge + ½ boosting`, där ridge-delen delas exakt per feature (största tre
    redovisas) och boosting-delen ligger i en klump.
  - **Osäkerhet:** J5:s EWMA-band (U4, λ = 0,9) runt den skarpa prognosen. Bandet bygger på tidigare fel till och
    med t−1: den skarpa modellens fel från 2023-12, comp_fuel:s fel före det. Bandet är ett förslag och
    `forecast.py`:s intervall är oförändrade.
  - **Efter utfall:** felet (prognos − utfall) delat per komponent, `Σ_c k·(f_c[t] − e_c[t]) + avrundning`,
    plus träff i J5-bandet och skuggornas fel.
  - Svensk klartext med huvudbudskapet först (`text`, `text_outcome`), skriven för att kunna läggas i K5:s
    månadsbrev.
- **Utdata:** `outputs/explain/<månad>.json` och `.md` för de senaste 24 månaderna och målmånaden, plus
  `sammanstallning.md`, `fel_per_komponent.csv` och `.md` (gitignorerat). Committade exempel ligger i
  `docs/auto2/k3/`: `exempel-2026-11.json`, `forklaring-2026-11.md`, `sammanstallning-24.md` och
  `fel_per_komponent.md`.
- **Pipeline:** `python -m kpif_nowcast.pipeline explain` och som sista steg i `pipeline monthly`. Där är steget
  inte fatalt, så att ett fel inte stoppar skuggprognoserna. Workflow `monthly-shadow.yml` laddar upp
  `outputs/explain` som Actions-artefakt (90 dagar). Inga committade filer skrivs av steget.
- **Tester** (`tests/test_explain.py`, 13 st):
  - Bidragen summerar till prognosen, och prognosen är identisk med skuggan `comp_fuel_el`.
  - Drivare + avrundning summerar till förändringen, och felets delar summerar till felet.
  - 50/50- och J2-skillnaderna summerar.
  - Informationsmängden: förklaringen för t, utom utfallsdelen, är identisk med och utan data efter t:s deadline.
    Testat för 6 månader 2024–2026.

  K2-delen täcks av K2:s eget informationstest.

## Resultat

**2026-11 (PRELIMINARY, data till 2026-11-22):**
- Prognosen är 2,05 % (den skarpa filen säger 2,09 % med 21 i stället för 22 elprisdagar), upp från 1,1 %.
- Av ökningen på +0,95 pe står elen för +0,91 pe: spotpriset steg 0,96 kr/kWh till 2,00 kr/kWh. Drivmedel ger
  −0,32 pe (oljepriset i kronor −24 %), och säsong och trend mot november i fjol ger +0,33 pe.
- J5-band: 80 % 1,46–2,62 %.
- Skuggorna ligger alla lägre: J2 V2 1,86 % (−0,19 pe, el), K2 1,68 %, 50/50 1,52 %. 50/50 hamnar lägst
  eftersom Riksbanken låg på 1,73 % och missade med −0,55 pe i oktober.

**24 månader 2024-11..2026-10 (använd period, bara rapport):**
- Den skarpa modellens MAE är 0,393, att jämföra med J2 V2 0,276 och 50/50 0,266 på samma månader.
- Genomsnittligt absolut fel per komponent: energi 0,251, tjänster 0,203, varor 0,105, livsmedel 0,090,
  kapitalstock 0,013 pe.
- J5-bandets täckning är 42/79/92 % för 50/80/90 %-banden (n = 24, för litet för att skilja från nominellt).

**Historik 2015–2026** (J2 V2, n = 142; `fel_per_komponent.md`):
- Tjänster står för mest fel: 37 % av kvadratfelet. Därefter kommer energi 21 %, varor 20 %, livsmedel 20 % och
  kapitalstock 1 %.
- Tjänster var största felkällan 2015–2019 (49 %), 2020–2021 (53 %) och 2024–2026 (34 %). Energi var störst
  2022–2023 (27 %), då MAE totalt var som högst (0,41).
- Livsmedel har vuxit och står för 29 % 2024–2026 och 43 % hittills 2026.
- Medelfelet per komponent är nära noll i alla perioder, med undantag för energi 2022–2023 (+0,06).

**Energi i den skarpa modellen:** genomsnittligt absolut energifel 2024–2026 är 0,242 pe. J2 V2 har 0,128 och
modellen med bara drivmedel 0,340 (n = 34). Eftersom de andra komponenterna prognostiseras identiskt är hela
skillnaden mellan den skarpa modellen och J2 V2 energikorrektionen. Det är urvalsevidens på en använd period, inte
ett nytt test.

## BLOCKED

Inget.

## Vad lärde vi oss

- **Felet sitter mest i tjänster, inte i energin.** Över 2015–2026 kommer drygt en tredjedel av kvadratfelet
  från tjänster, som modellen bara prognostiserar med säsong + trend. Energi dominerar bara under
  energikrisen 2022–2023. Nästa förbättring av punktprognosen bör därför sökas i tjänster (och på senare tid
  livsmedel), inte i fler elvarianter.
- **Den skarpa modellens elkorrektion är dess svaga punkt just nu.** Den skiljer sig från J2 V2 bara i energin, och
  på de senaste 24 månaderna har den MAE 0,393 mot J2 V2:s 0,276. Det stöder J2:s och J1:s resultat. Bytet av huvudmodell beslutar Johannes.
- **November 2026 är en elmånad.** Prognosen 2,1 % står och faller med elpriset (+0,9 pe). Skuggorna är
  0,2–0,5 pe lägre, så spridningen mellan modellerna är ovanligt stor. Det är värt att nämna i månadsbrevet.
- **J5-bandet verkar rimligt kalibrerat på 80/90 %** och möjligen för smalt på 50 %, men 24 månader räcker inte
  för att säga det.
