# V2 Gemensam screening av körning 3:s nya serier: förregistrering

Skrivet 2026-11-23, innan någon screening, något prognosfel, någon korrelation mot målet eller något p-värde
har beräknats för serierna nedan. Bas: gren `auto3/v2` @ 93f3d91 (main 129bbb0 + våg 1 L1–L7).
Det enda som har lästs ur datan är täckning, frekvens, `known_from` och vilken period som är känd vid deadline
(data om tillgänglighet, inte om målet).

**Varianttal:** projektet har förbrukat 51 varianter före körning 3. Körningens tak är 6. V2 använder **högst 2**
(se avsnitt 4) och lämnar minst 4 i reserv. Screeningen räknas inte mot taket.

## Hypotes och gissning innan

Hypotes: någon av körning 3:s nya svenska serier, framför allt resepriser, påskens placering och kronan, bär
information om nästa månads KPIF-miss utöver den bästa skuggmodellen (`k2_avg_ridge_l`) och 50/50-snittet
(`avg_5050` = `j1_comb_equal`). Det troliga utfallet är ändå att ingen gör det. J3 (45 serier) och K0 (29 serier)
hittade inga överlevare, och K7 visade att påsken tillför lite utöver femårssäsongen.

**Gissning innan:**
- Screening, per bas: 0 överlevare efter BH (q = 0,10), högst 1. Störst chans har `kpif_package_holidays_index`
  (tjänstemissen sitter i resor) och `easter_window_days` (påskmånaderna). Storlek för den bästa:
  MAE-diff −0,001 till −0,006 pe.
- Gemensamt test: diff −0,006 till +0,002 pe mot respektive bas. Ingen variant klarar urvalsskärmen.
- Mot `k2_avg_ridge_l` är chansen mindre än mot 50/50, eftersom K2:s L-mängd redan innehåller `kix` och `brent_sek`.

## 1. Kandidatlista

Våg 1 lade till 35 serier i `catalog.CATALOG` (L2: 9, L3: 2, L4: 3, L5: 12, L6: 2, L7: 7). L1 är en kalender för
manuell justering utan katalogserier och testas inte. Alla 35 är bedömda nedan: **10 kandidater**, 25 utesluts i förväg.

### Gemensamma regler

- **Deadline:** dag 4 i t+1 (`riksbank_benchmark.deadline`). Ett värde används bara om `known_from ≤ deadline(t)`
  (`observations.as_of`). `known_from` = max(periodens slut + `lag_days`, sent releasedatum i
  `publication.LATE_RELEASES`).
- **Transformation:** exakt `j3_screen.transform`: värdet vid den senaste kända perioden p* ≤ t,
  säsongsdifferentierad månadsförändring x = Δv(p*) − Δv(p* − 12). Här är v = 100·log(nivå) för positiva
  nivåserier (index, gästnätter, valutakurser) och v = nivå för andelar i % och för dagar. Ingen kandidat är
  en tillväxtserie i J3:s mening.
- **Ny regel för inaktuella värden (bestämd före test, utifrån publiceringsläget):** x sätts till saknat om
  p* är äldre än seriens normala fördröjning plus 2 månader. Då är korrektionen inaktiv den månaden och raden
  tas inte med i träningen. Regeln slår bara till för elavtalen 2023-08..2024-07 (12 målmånader). TAB3571 för
  2023-05..2024-06 blev känd först 2024-09-27, och J3:s regel skulle annars upprepa x från 2023-04 i 15 månader.
- **Brott:** för `el_contract_spot_share` sätts x till saknat när transformen spänner över skiftet
  2023-01→2023-02, alltså när timpris började redovisas separat (L5: hopp på ca +4 pe). Det gäller p* = 2023-02
  (målmånad 2023-03) och p* = 2024-02. Den senare är aldrig senaste kända period och påverkar därför ingenting.
- **Minsta antal observationer:** x måste vara definierat från målmånad 2015-01, så att 24 träningsrader finns
  när primärperioden börjar 2017-02, och i minst 100 av primärperiodens 117 målmånader (2017-02..2026-10).
  Kravet följer K0:s lärdom: "lägst rå p" valde där SWESTR, som bara var aktiv 25 månader i den använda perioden.
  Gränsen 100 sattes efter att täckningen räknats (elavtalen: 104 av 117), men utan att något fel hade setts.

### Kandidater (10)

| # | Nyckel | Källgrupp | Frekv. | Period känd vid deadline(t) | Transformation | Rev. | x definierat |
|---|---|---|---|---|---|---|---|
| 1 | `easter_window_days` | resor | M, kalender (lag −366) | t (kalendern är känd i förväg; J3-transformen kapar vid p* ≤ t) | Δe(t) − Δe(t−12), dagar, ingen log | nej | 2015-01–, alla 117 |
| 2 | `kpif_package_holidays_index` | resor | M, 15 d | t−1 | säsongsdiff. Δ100·log | ja | 2015-01–, alla 117 |
| 3 | `kpif_air_transport_index` | resor | M, 15 d | t−1 | säsongsdiff. Δ100·log | ja | 2015-01–, alla 117 |
| 4 | `kpif_accommodation_index` | resor | M, 15 d | t−1 | säsongsdiff. Δ100·log | ja | 2015-01–, alla 117 |
| 5 | `guest_nights_domestic` | resor | M, 80 d | t−3 | säsongsdiff. Δ100·log | ja | 2015-01–, alla 117 |
| 6 | `guest_nights_foreign` | resor | M, 80 d | t−3 | säsongsdiff. Δ100·log | ja | 2015-01–, alla 117 |
| 7 | `kpi_rent_index` | hyror | M, 15 d | t−1 | säsongsdiff. Δ100·log | ja | 2015-01–, alla 117 |
| 8 | `el_contract_spot_share` | el | M, 28 d + sena releaser | t−1 (2023-08..2024-07 inaktuellt → saknat) | säsongsdiff. Δ i pe, ingen log; brottregeln ovan | ja | 2015-01–, 104 av 117 |
| 9 | `sek_eur` | kronan | M, 1 d | t | säsongsdiff. Δ100·log | nej | 2015-01–, alla 117 |
| 10 | `sek_usd` | kronan | M, 1 d | t | säsongsdiff. Δ100·log | nej | 2015-01–, alla 117 |

Perioden som är känd vid deadline är kontrollerad med `as_of` för målmånaderna 2016-03, 2020-07, 2024-01 och
2026-10. Alla kandidatrader i observationstabellen är `backfill`. Inga hämtrader finns, så L7:s fynd 3
(hämtdag = releasedag) kan inte påverka.

Kommentarer:
- **Påsken är kandidat.** Ingen av baserna har en påskvariabel: K2:s S- och L-mängder saknar den, och 50/50 är
  rb_updated + J2 V2. Påsken fanns bara i J4- och K7-varianter (`j4_detail_energy_easter`, `k7_*`), inte i
  baserna. Målet är årstakt. Påskens bidrag till missen i årstakt är ungefär β·[(e(t) − e(t−1)) − (e(t−12) − e(t−13))],
  och det är exakt J3-transformen. Det behövs alltså ingen särskild påskform.
- **KPIF-delindexen (2–4, 7)** är delar av själva målet och publiceras samtidigt med KPIF för t−1, alltså före
  deadline. De fungerar som persistens för tjänstemissen. Historiken före 2026 är SCB:s omräkning till COICOP 2018
  (revised=True, se avsnitt 6).
- **Kronan (9–10):** säsongsdifferentierad månadsförändring, samma regel som `kix` i K2:s L-mängd. Inga
  alternativa laggar (1–9 mån eller årstakt) testas. Det skulle bli fler test utan förregistrerat val.

### Uteslutna i förväg (25)

| Nycklar | Skäl |
|---|---|
| `guest_nights_total` | Summan av svenska och utländska gästnätter (identitet i 212 av 212 månader), alltså redundant. |
| `guest_nights_hotel` | Delmängd av totalen (hotell), samma källa och fördröjning. Den spär ut BH-familjen utan ny mekanism. |
| `easter_sunday_in_month` | Grövre version av samma kalender som `easter_window_days`, och starkt kollinjär med den. |
| `rent_negotiated` | Årsserie med 11 värden (2016–2026). Årets utfall blir känt tidigast 30 juni, efter januari–april när det spelar roll (L3, användning punkt 1). Det ger för få aktiva månader för en korrektion. |
| `prospera_mm_5y_mean`, `_p25`, `_p75` | Börjar 2019-01, så x finns från 2020-02 och korrektionen är aktiv först från 2022-02 (57 av 117 månader, mest i den använda perioden). Kravet ovan uppfylls inte. Serien är dessutom nästan konstant 2024–26, och L4 väntar sig inget värde på 1 månads sikt. |
| `el_contract_hourly_share` | Börjar 2023-02 (x definierat i 26 målmånader). |
| `el_contract_fixed_share`, `el_contract_default_share` | Kompositionsdata: andelarna summerar till ca 100 %, så ändringarna speglar `el_contract_spot_share`. Spot-andelen är den med en mekanism, nämligen genomslaget av spotpriset. |
| `el_grid_price_flat`, `_house`, `_house_heat`, `_house_heat_unw`, `ei_grid_fee_flat`, `_house`, `_house_heat`, `ei_grid_fee_raise_share` | Årsserier med ett relevant värde per år (januari), alltså högst 10 aktiva målmånader i primärperioden. Årets tariff är inte känd vid januari-deadline (L5:s läckagefälla), bara fjolårets. Underlag för manuell `--adjust` i januari tillsammans med L1, vilket Johannes beslutar. |
| `kpif_flash_yy`, `kpif_flash_mm`, `kpif_xe_flash_yy`, `kpif_xe_flash_mm` | Börjar 2024-09 (26 månader). Med fördröjning 8 d är snabb-KPI för t aldrig känd vid deadline dag 4, och för t−1 finns redan utfallet (L7, punkt 2). |
| `kpif_flash_err_yy`, `kpif_flash_err_mm`, `kpif_xe_flash_err_yy` | Börjar 2024-09 och är nästan alltid 0. Kvalitetskontroll, ingen prediktor (L7, punkt 3). |

## 2. Screeningprotokoll (räknas inte mot varianttaket)

- **Två baser, var för sig:**
  - **R:** `k2_avg_ridge_l` exakt som skuggprognosen `shadow.SHADOW_MODELS["k2_avg_ridge_l"]`, med frusen
    L-mängd (`k2_ml.K2_CATALOG_KEYS`, 43 serier) och K2b:s rättelse av flashdatumen (`k2b_review.realistic_flash`).
    Det är den version som körs som skugga, och det är den som får en korrektion om något fryses.
  - **A:** `avg_5050` = `j1_comb_equal` (`k0_screen.fifty_fifty_frame`).
- **Mål:** residualen utfall − basprognos, KPIF årstakt, h = 1 (`yy_official`).
- **Korrektion per serie:** `j3_screen.correct` oförändrad. Prognos = bas + b·(x(t) − x̄), där b skattas med OLS
  utan intercept på centrerat x över tidigare målmånader s ≤ t−1 med publicerat utfall (`h1_usable`).
  Fönstret är expanderande, med minst 24 träningsrader (`MIN_TRAIN`). x̄ och b räknas bara på träningsraderna.
- **Test:** `j3_screen.score_table`: ensidigt DM-test på absolutfel (`evaluation.dm_test`, h = 1,
  H1: lägre MAE än basen), mot basen.
- **BH:** Benjamini–Hochberg, q = 0,10, per bas över de 10 kandidaterna (två familjer). Rå p och BH-q
  redovisas för alla 10.
- **Perioder:** primärt 2017-02..2026-10 (n ≈ 117, samma som J3/K0). Urvalet görs bara här. Rapporteras också:
  2015-01..2026-10 (korrektionen är inaktiv före 2017-02) och 2024-01..2026-10 (använd period, bara rapport).
- Serier med revised=True märks i tabellen.
- **Reproducerbarhet först:** se avsnitt 6, punkterna 7–8. Screeningen körs från en ny modul
  (`src/kpif_nowcast/v2_screen.py`) med kandidatlistan ovan hårdkodad, inte genererad ur `CATALOG`.

## 3. Urvalsregel (bestäms helt av primärtabellen, separat per bas)

1. Ordning: först BH-överlevare (q < 0,10) efter rå p, sedan övriga efter rå p.
2. Bara serier med negativ MAE-diff mot basen (rå ensidig p < 0,5) får väljas. En serie som försämrar basen
   fylls inte på.
3. Högst en serie per källgrupp (resor, hyror, el, kronan; Prospera och snabb-KPI har inga kandidater). En serie
   vars grupp redan är vald hoppas över.
4. Högst tre serier. Märkning som K0: "alla överlevde BH", "k av n överlevde BH" eller "ingen överlevde BH".
5. Uppfyller ingen serie punkt 2 körs ingen variant för den basen. Den förbrukar då ingen variant och redovisas
   som "ingen kandidat".

**Per bas, inte samma uppsättning.** Residualerna skiljer sig: K2:s L-mängd innehåller redan `kix`,
`brent_sek` och euroområdets flash, men det gör inte 50/50. En gemensam uppsättning vald på den ena basen
skulle testa fel sak på den andra. K0 visade också att samma serier gav p ≈ 0,05 mot den ena basen och
ingenting mot den andra. Priset för valet per bas är mer urvalsfrihet. Det tas om hand av Holm över varianterna
och av det globala testet över alla projektets varianter (avsnitt 4). Väljer båda baserna samma serier är det
i sin ordning.

## 4. Gemensamt test (en gång)

**Varianter: högst 2 av körningens 6.**

| Namn | Bas | Korrektion | Varianttal i projektet |
|---|---|---|---|
| `v2_r_corr` | `k2_avg_ridge_l` (skuggversionen, bas R) | `j3_screen.combined_h1` på de valda x för bas R: OLS utan intercept, centrerat, expanderande, minst 24 rader, samma inaktuella-regel och brottregel | 52 |
| `v2_a_corr` | `avg_5050` (bas A) | samma, på de valda x för bas A | 53 |

Körs bara en av dem (avsnitt 3, punkt 5) blir projektets total 52. Inga andra varianter, inga omtag och inga
tillägg efter resultat. Ett tillägg skulle märkas post hoc och räknas mot taket.

**Mått och test:**
- MAE på KPIF årstakt, h = 1, primärt 2017-02..2026-10. Även 2015-01..2026-10 och 2024-01..2026-10
  (bara rapport).
- Ensidigt DM (absolutfel) mot den egna basen, rå p. Holm över de varianter som faktiskt körs (1 eller 2), på
  primärperioden.
- Bredvid varje p står projektets totala varianttal, till exempel "rå p 0,xx · Holm p 0,xx (projektet: 53 varianter)".
- Sekundärt (rapport, inget kriterium): båda varianterna också mot rb_updated.

**Globalt test (som K12, `k12_global`):**
- Universum: K12:s U1 (35 registrerade h=1-varianter plus referenserna rb_updated, `avg_5050` och j2) plus körning
  3:s nya varianter. Dessutom skuggversionen av `k2_avg_ridge_l` (K2b-rättad) som ribba för `v2_r_corr`. K12:s
  orättade `k2_avg_ridge_l` ligger kvar i universumet som förut. De nya serierna läggs in via K12:s
  `outputs/k12/extra/*.csv`-mekanism. Resultatet skrivs till `docs/auto3/v2/`, inte över K12:s fil.
- Ribbor: rb_updated, `avg_5050` och `k2_avg_ridge_l` (skugga).
- Urval: K12:s gemensamma 2015-01..2026-10 (n = 141), där de nya varianterna är lika med basen före 2017-02.
- Stationär bootstrap (Politis–Romano), **medelblocklängd 3 månader** (primär, fast), B = 9 999,
  seed 20261123. Känslighet: block 1, 6 och 12.
- Redovisas: Hansens SPA (lower, consistent, upper), White RC, Romano–Wolf StepM (10 %), MCS (90 %, T_max och T_R)
  och urvalsbias (E[max förbättring] under H0), allt som i K12.

## 5. Kriterium: "klarade urvalsskärmen"

En variant klarar urvalsskärmen om **alla tre** villkoren gäller:
1. **Holm p < 0,10** mot den egna basen (ensidigt DM, primärperioden 2017-02..2026-10).
2. **Globalt justerat p < 0,10** mot den egna basen: K12:s max-t-justerade p (Hansen-recentrerat,
   studentiserat, enstegs Romano–Wolf över hela universumet), block 3, där ribban är den egna basen.
3. **Inte högre MAE än basen 2024-01..2026-10**, samma skydd som K2:s skärm.

**Motivering:**
- Villkor 1 är projektets standard (J2, K0, K2) och kontrollerar för körningens egna varianter.
- Villkor 2 är modellspecifikt. SPA-p för ribban `avg_5050` säger bara om *någon* modell i universumet är bättre
  än 50/50, och K12 fann redan p = 0,025 tack vare `k2_avg_ridge_l`. Den skulle alltså godkänna `v2_a_corr` vad den
  än gör. Det justerade p:t frågar i stället om just denna variant är bättre än sin bas när alla projektets
  varianter räknas. Det är K12:s StepM-logik.
- Villkor 3 är K2:s skydd mot en vinst som bara kommer från tidigt i perioden.
- Med ribban `k2_avg_ridge_l` är villkor 2 svårt, eftersom få modeller ligger nära den bästa. Det är avsiktligt,
  för att en korrektion på den bästa skuggmodellen ska vara mer än brus.

Känsligheten vid block 6 och 12 redovisas. Ett justerat p ≥ 0,10 där märks "känslig för blocklängd" men
ändrar inte beslutet, som låses vid block 3.

**Vid godkänt:** varianten fryses som skuggprognos med en rad i `shadow.SHADOW_MODELS`, med de valda serierna
hårdkodade. Readiness som K2 (`_flash_published` för `v2_r_corr`), plus att varje vald series förväntade period
(enligt tabellen i avsnitt 1) ska finnas i observationstabellen, annars PRELIMINARY. Den skarpa prognosen,
`MODEL_NAME` och `forecast.py` rörs inte. Innehåller de valda serierna revised=True-serier (alla utom påsken och
kronan) märks resultatet **"obekräftad (revisionsläckage möjligt)"**. Frysningen sker ändå, eftersom skuggan
är testet utanför urvalet. Formuleringen är alltid "klarade urvalsskärmen", aldrig "slår".

**Annars:** inget fryses, och resultatet redovisas ärligt som negativt i `docs/auto3/v2/resultat.md`.

## 6. Läckagekontroller (körs före screeningen och före det gemensamma testet)

1. **Känt vid deadline, per kandidat och målmånad 2015-01..2026-10:** p*(t) ska stämma med tabellen i avsnitt 1
   (påsk och krona t, KPIF-delindex, hyror och elavtal t−1, gästnätter t−3), och varje använd rad ska ha
   `known_from ≤ deadline(t)`. Avvikelser listas. En okänd avvikelse stoppar testet.
2. **Sena releaser:** TAB3571:s rättelser (2022-01..03 → 2022-04-30, 2023-05..2024-06 → 2024-09-27) ska ge
   p* = 2023-04 vid deadline 2024-01 (stämmer redan vid läsning). Hyresserien och snabb-KPI ingår inte.
3. **Publiceringsgränser:** KPIF-delindex för januari publiceras dag 18–20 i februari, långt före gränsen på 32 d
   för t−1 vid dag 4. Gästnätter: 80 d ger t−3, och läckage uppstår först vid en verklig fördröjning över 93 d
   (L2). Fixing för sista bankdagen sker kl. 16.15 samma dag, vilket ger 3 dagars marginal (L6).
4. **Inga features beräknade över hela perioden:** x(t) använder bara värden till och med p*. x̄ och b räknas
   bara på träningsrader med publicerat utfall. Ingen standardisering eller säsongsrensning görs över hela
   urvalet. Inaktuella-regeln och brottregeln beror bara på datum, inte på värden.
5. **pytest** (`tests/test_v2_screen.py`, utan nät): x(t) och den korrigerade prognosen för t ska vara identiska
   när observationstabellen kapas till `known_from ≤ deadline(t)` och utfall efter t−1 tas bort. Det testas för
   båda baserna och för en kombination av tre kandidater (som `test_k0_prices`). Dessutom testas att
   inaktuella-regeln ger saknat x för 2023-08..2024-07 och att brottregeln ger saknat x för 2023-03.
6. **Revisioner:** sex av tio kandidater har revised=True. KPIF-delindexen före 2026 är COICOP 2018-omräkning,
   gästnätterna är preliminära med ett möjligt producentbrott 2024/2025 och underrapporterade utländska nätter
   2024, och elavtalen är rättade 2022–2024. Inga realtidsårgångar finns. Därför används differenser, inte nivåer,
   och resultatet märks som i avsnitt 5. Det går inte att verifiera bort.
7. **Basen reproduceras:** skuggversionen av `k2_avg_ridge_l` ska ge MAE 0,200 på 2015-02..2026-10 (K2b decfix,
   n = 141), och `avg_5050` 0,217 (K12). Annars stoppas testet.
8. **Redan registrerade varianter oförändrade:** K12:s per-modelltabell (37 modeller, MAE med 3 decimaler,
   [docs/auto2/k12/resultat.md](../../auto2/k12/resultat.md)) ska reproduceras exakt med våg 1:s större
   `CATALOG`. K2:s L-mängd, J3:s och K0:s kombinationer (`k12_global.J3_COMBO_KEYS`, `K0_COMBO_KEYS`) och
   `k0_screen` (`catalog_prices.keys()`) är redan frusna. `j3_screen.screen_keys()` växer däremot med våg 1.
   Den fryses till läget före körning 3, det vill säga katalogens månadsserier minus de 35 nya, innan
   något körs. Hittas en avvikelse fryses den modulens lista på samma sätt innan testet.

Ordning: kontroll 1–3 och 7–8 körs, pytest (5) blir grönt, screeningen körs, urvalet görs mekaniskt, det
gemensamma testet körs en gång och sedan K12-testet. Den här filen committas och pushas innan något av det görs.
