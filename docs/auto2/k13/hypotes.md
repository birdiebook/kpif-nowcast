# K13 Skatterensad bas: förregistrering

Skriven 2026-11-23 innan något fel för 2015–2026 har beräknats för varianterna nedan.
Bas: main @ 80bc02f (K0–K4, K6–K9 mergade), gren `auto2/k13`. K13:s tak: **högst 2 varianter**
(körning 2 har 26 av 30 förbrukade). Kod: `src/kpif_nowcast/k13_tax.py`. Inga nya datahämtningar
(skatteeffekterna finns redan i `data/processed/tax_effects.csv`, SCB TAB6592/TAB6593/TAB6746).
Källor för händelserna: [docs/skattekalender.md](../../skattekalender.md).

## Varför
K8 (öppen fråga/lärdom 3): momssänkningen på livsmedel 2026-04 (−0,76 pe på KPIF m/m) ligger kvar i
12-månaderstrenden till 2027-03 och i aprilsäsongen i fem år. Samma sak gäller de tillfälliga drivmedels- och
elskattesänkningarna 2026. Alla modeller med basen säsong + 12-månaderstrend (den skarpa, J2 V2 och via J2
även K2-ensemblen) läser alltså in engångssänkningar som om de vore underliggande prisutveckling.

Fas 4b testade en rensning av **all** KS-effekt (även de återkommande januari- och julieffekterna) och blev
sämre i snitt. Här rensas bara **identifierade engångshändelser**, och bara den del av KS-effekten som hör
till händelsens komponent.

## Uppställning
**Skatteeffekt per månad:** `tax_total = KPIF m/m − KPIF-KS m/m` (SCB:s mekaniska beräkning med fullt
genomslag), delad i en energidel och en icke-energidel med KPIF-XE vs KPIF-XE-KS (finns från 2020):
- icke-energidel `ne_t = tax_xe_own_t · (1 − w_energy,t)`
- energidel `en_t = tax_total_t − ne_t`

**Händelsekalender** (`k13_tax.EVENTS`; beslutsdatum = riksdagsbeslut, angivet som "senast"-datum):

| Månad | Komponent | Del | Händelse | Typ | Beslut senast |
|---|---|---|---|---|---|
| 2022-05 | energy | en | Tillfälligt sänkt energiskatt bensin/diesel (1,05 kr/l + moms), prop. 2021/22:221 | start | 2022-04-30 |
| 2022-10 | energy | en | Samma sänkning upphör 2022-09-30 (solnedgång i lagen) | slut (av 2022-05) | 2022-04-30 |
| 2026-01 | energy | en | Sänkt energiskatt på el (BP 2026) | start | 2025-11-30 |
| 2026-04 | food | ne | Matmomsen 12 → 6 % 2026-04-01–2027-12-31 (BP 2026) | start | 2025-11-30 |
| 2026-05 | energy | en | Tillfälligt sänkt energiskatt bensin/diesel till EU-minimum 2026-05-01–09-30, prop. 2025/26:236 | start | 2026-04-30 |
| 2026-07 | energy | en | Tillfälligt sänkt koldioxidskatt bensin/diesel 2,40 kr/l 2026-07-01–11-30, prop. 2025/26:275 | start | 2026-06-30 |
| 2026-10 | energy | en | Energiskattesänkningen från 2026-05 upphör | slut (av 2026-05) | 2026-04-30 |
| 2026-12 | energy | en | Koldioxidskattesänkningen från 2026-07 upphör | slut (av 2026-07) | 2026-06-30 |

Inte med (motiverat i skattekalendern): återkommande januarihöjningar (indexering av punktskatter) och den
återkommande julieffekten i KS 2019–2025 (fångas av säsongen, fas 4b); restaurangmomsen 2012-01 (före
uppdelningen finns, och tjänstebidraget visar inget synligt genomslag, residual −0,01 pe; valet gjordes efter att
ha sett den siffran, före variantkörning); ROT 2025-05/2026-01 och tandvårdsstödet 67+ 2026-01 (januari blandar
händelser som tar ut varandra, påverkar inte 2026-11); avgifter som SCB inte rensar i KS (halverat månadskort i
kollektivtrafiken 2026-07–12, förskoletaxan 2026-07). Månadskortet tas upp separat i rapporten för 2026-11/12.

**Rensning av historiken (för mål t):** för varje händelsemånad s < t dras den realiserade KS-delen (`en_s`
eller `ne_s`) från komponentens bidrag. KS för s publiceras med KPI för s (~den 13:e i s+1), alltså före
deadline(t) för alla s ≤ t−1. Säsong, trend och J2:s energikorrektion skattas på de rensade bidragen.

**Tillägg i prognosmånaden t:** bara om händelsen har beslutsdatum < deadline(t) (dag 4 i t+1).
- start: SCB:s KS-del för t (SCB:s mekaniska beräkning från skattesats och vikter, med fullt genomslag; den går
  att göra före deadline, men själva siffran publiceras efter. Risken för läckage är storleken, inte tecknet eller
  tidpunkten, och den redovisas med en känslighetskoll).
- slut: minus den realiserade KS-delen i startmånaden (känd före deadline, helt ex ante).

## Varianter (exakt två, båda räknas mot taket)
1. **`k13_j2_clean`** – J2 V2 (`j2_el_dev`: säsong + 12-månaderstrend per komponent, energikorrektion med
   `fuel_chg` och `el_dev` från 2012) på rensade bidrag, plus tillägget i prognosmånaden. Referens: J2 V2
   orensad.
2. **`k13_ens_clean`** – `k2_avg_ens_s` (ridge + boosting på residualen av 50/50-snittet, feature set S, nästlad
   CV, oförändrad i övrigt) där J2-delen byts mot `k13_j2_clean`: `avg = 0,5·rb_updated + 0,5·k13_j2_clean`.
   De J2-härledda featurena (`gap`, `last_resid_j2`, `gap_x_age`, `energy_news`, `energy_x_age`, `core_dev`) räknas
   om från den rensade J2. Referens: `k2_avg_ens_s` orensad.

**Test:** DM på absolutfel, ensidigt (H1: varianten har lägre MAE än sin referens), Holm över de två.
Period 2015-02..2026-10 (n = 141, samma som K2/K8). 2024–2026 rapporteras bara.

**Rapporteras också (inte i Holm-familjen):** MAE utan händelsemånaderna (isolerar basens effekt från
tillägget); prognoserna för 2026-11 och 2026-12 med och utan rensning för den skarpa modellen
(`component_fuel_el_v1`, bara punktprognoser, inga fel beräknas), J2 V2 och K2-ensemblen; en känslighetskoll där
tillägget i startmånader skalas ±20 %.

## Gissning innan
- **`k13_j2_clean` mot J2 V2:** MAE −0,008 till −0,015. Mest från händelsemånaderna (2026-04 ensam ≈ −0,005,
  2026-07 ≈ −0,003), resten från trenden efter händelserna. Rå ensidig p 0,02–0,15; Holm p < 0,10 med ~50 %
  sannolikhet. Utan händelsemånader: −0,001 till −0,004.
- **`k13_ens_clean` mot `k2_avg_ens_s`:** −0,003 till −0,008 (halva vikten på J2, och Riksbankens prognos har
  redan med beslutade skatter). Holm p > 0,10 troligt.
- **2026-11:** den rensade basen ger ~+0,1 pe högre årstakt än den orensade för J2 V2 och den skarpa modellen
  (sänkningarna 2026-01, -04, -05, -07 och höjningen -10 tas bort ur 12-månaderstrenden; inget tillägg i
  november). 2026-12: ytterligare ~+0,4 pe från att koldioxidskattesänkningen upphör.
