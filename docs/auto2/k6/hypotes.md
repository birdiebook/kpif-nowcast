# K6 Bara om det är lätt: förregistrering

Skriven 2026-11-23 innan något fel har beräknats för varianterna nedan. Bas: main @ 564c508.
Varianttak för K6: högst 4. Här registreras **2** (körning 2 har förbrukat 11 av 30, projektet 34).
Källor: Eurostat (och redan cachade svenska elpriser/Brent/Riksbankens valutakurser). Varje del är ett försök.

## Del 1: vintages för reviderade svenska serier (datakontroll, 0 varianter)

**Problem:** J4 D2 (`j4_detail_energy`, MAE 0,243) är "obekräftad (revisionsläckage möjligt)" eftersom
TAB6613 före 2026 är SCB:s omräkning till COICOP 2018. Riktiga vintages av COICOP 2018-grupperna finns
inte: grupperna publicerades första gången 2026. Riksbanken och KI arkiverar inga KPI-detaljindex.
Därför markeras "D2 med vintage-data" som **BLOCKED** i förväg, utan att någon variant körs.

**Ersättningskontroll (ingen prognosserie, ingen variant):** Eurostat har kvar den gamla HIKP-datamängden
`prc_hicp_midx` (ECOICOP 1, fryst 2025-12, sådan den publicerades under gamla klassificeringen) bredvid den nya
`prc_hicp_minr` (COICOP 2018, omräknad). För Sverige jämförs månadsförändringen (index m/m, %) 2001–2025 i
- HIKP gammal mot HIKP ny, grupp för grupp (alla koder som finns i båda), särskilt 04.5 (el, gas m.m.),
  04.5.1 (el) och 07.2 (drift av fordon; drivmedel ligger här);
- HIKP gammal mot TAB6613 (KPIF-detalj, omräknad), för 04.5 och 07.2 (annan omfattning och vikt, så
  bara en rimlighetskontroll);
- att summan av TAB6613:s 43 bidrag är lika med den publicerade KPIF-månadsförändringen (som inte revideras).

**Kriterium, satt i förväg:** om 04.5 och 07.2 har korrelation ≥ 0,98 och medelabsolut skillnad ≤ 0,10 pe
mellan gammal och ny HIKP, säger vi att omräkningen praktiskt taget inte ändrat de två grupper som D2:s vinst
kommer från. Det lyfter inte märkningen av D2 (övriga 41 grupper är fortfarande omräknade), men visar om
vinsten mot comp_fuel kan bero på revision i energigrupperna.

**Gissning:** energigrupperna är i stort sett oförändrade (korrelation > 0,99); grupper i division 09–13 där
COICOP 2018 flyttat innehåll (t.ex. paketresor, personlig omsorg) skiljer sig tydligt.

## Del 2: J2:s elmetod på grannländers HIKP (2 varianter)

**Hypotes:** J2 V2:s idé (el som avvikelse från samma kalendermånad de senaste ≤ 5 åren, plus drivmedel, som
korrigering ovanpå en säsong + trend-baslinje) förbättrar en nowcast av HIKP även i Danmark och Finland, där
hushållens elpris också följer Nord Pool. Ett robusthetstest av metoden, inte en svensk prognos.

**Data:** HIKP totalindex (2015 = 100) för DK och FI från Eurostat `prc_hicp_minr` (coicop18=TOTAL, unit=I15),
kontrollerat mot gamla `prc_hicp_midx` (CP00) för att se att totalen inte reviderats. Grannländernas egna
spotpriser finns inte i våra källor (Energinet ingår inte i K6:s källås; elprisetjustnu.se har bara svenska
områden). Därför används **kopplade svenska områden som ombud**: SE3 för Finland, SE4 för Danmark (DK2 och SE4
har oftast samma pris), månadsmedel av dagspriser omräknat till EUR/kWh med Riksbankens SEK/EUR (månadsmedel).
Drivmedel: Brent i EUR, dag 1–25 (samma fönster som `features.fuel_proxy_daily`), logförändring.

**Informationsmängd för månad t:** HIKP till och med t−1 (DK publicerar ~10:e, FI ~15:e i t, alltså före
deadline dag 4 i t+1), spotpris och Brent för t (kända vid månadens slut). HIKP revideras i princip inte; den
nya datamängden är dock omräknad till COICOP 2018 på totalnivå, vilket kontrolleras mot den gamla.

**Gemensamt för varianterna:** baslinje = `seasonal_trend_additive` på HIKP m/m (%) (5-årig säsong +
12-månaders trend, samma som komponentmodellens per komponent). Korrigering = `fit_correction`: OLS utan
intercept på [fuel_chg, el_dev], expanderande fönster från 2012-01, minst 24 månader, koefficienter för t bara
från månader < t. el_dev_t = el_chg_t − medel av el_chg samma kalendermånad de senaste upp till 5 åren (minst 1),
el_chg = förändring i EUR/kWh. Prognos i årstakt via `yy_from_mm`.

| # | Namn | Land | Elombud |
|---|---|---|---|
| N1 | `k6_fi_el_dev` | Finland | SE3 |
| N2 | `k6_dk_el_dev` | Danmark | SE4 |

**Jämförelse (inte varianter, befintliga baslinjetyper):** `seasonal_trend_5y` (samma baslinje utan korrigering)
är referens. `naive_yy` (förra månadens årstakt) rapporteras.

**Godkänt (samma regel som J2):** lägre MAE än referensen med DM p < 0,10 (tvåsidigt, absolutfel) på
2015-01..2026-10, Holm över N1 och N2, och inte sämre 2024–2026 (rapporteras; för grannländerna inte en använd
period, men samma uppdelning). Gemensamt urval per land: månader där variant, referens och utfall finns.

**Gissning innan:** båda blir bättre än referensen. Danmark mer (hushållen har mest rörliga avtal, DK2 ≈ SE4):
ca −0,06 pe i MAE. Finland mindre (fler fasta avtal före 2022, FI och SE3 skiljer sig mer): ca −0,03 pe.
Vinsten kommer nästan helt 2021–2023. Danmark klarar skärmen, Finland troligen inte.
