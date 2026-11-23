# K2b: oberoende granskning av K2 (ML på residualen mot 50/50)

Granskare: K2b-agenten (har inte skrivit K2:s kod). Granskat: `src/kpif_nowcast/k2_ml.py` @ 415ba6f/25a6a6e,
`tests/test_k2_ml.py`, och allt K2 läser: `j1_hybrid.build_panel`/`ea_news`, `j2_el`, `features.py`,
`riksbank_benchmark.py`, `j3_screen.feature`/`transform`, `observations.as_of`, katalogens fördröjningar.
Granskningskörningar: `src/kpif_nowcast/k2b_review.py` (återanvänder K2:s frysta varianter, inga nya varianter),
råtabeller i `outputs/k2b/review_<scenario>.md` (inte i git), körloggar `experiments/runs/*_k2b_review_*.csv`.

## Dom: håller med förbehåll

Två av de tre varianterna klarar fortfarande urvalsskärmen efter att ett verkligt informationsläckage rättats:
**`k2_avg_ridge_l`** (MAE 0,200, Holm p 0,025) och **`k2_avg_ens_s`** (0,202, Holm 0,083), mot 50/50 0,217
(n = 141, 2015-02..2026-10). **`k2_avg_ridge_s` klarar den inte längre** (0,207, Holm 0,19).
Mekaniken (träningsfönster, imputering, standardisering, inre CV och hyperparameterval) läcker inte. Men:

1. **Läckage hittat och rättat:** Eurostats snabbestimat för december (och mars 2018 och januari 2026)
   publiceras efter vår deadline, men tabellen sa att de fanns två dagar efter månadens slut.
   `ea_news` är K2:s viktigaste feature, så detta drev en del av vinsten. Efter rättelsen krymper vinsten lite och ridge_s faller ut.
2. **Vinsten är liten och ojämn:** −0,014 till −0,017 pe, nästan bara 2020–2025. 2019 och 2026 är alla tre sämre än
   50/50 (2026: +0,018 till +0,025 på 10 månader). Utan 2022–23 är vinsten −0,008 till −0,012 och bara ridge_l har rå p < 0,05.
3. **Resultatet hänger på att publiceringsdatumen stämmer.** Ett planterat perfekt läckage av utfallet ger bara
   −0,04 i MAE (modellerna krymper hårt). Ett läckage som är hälften så stort som det skulle alltså kunna se ut som K2:s vinst.
   Därför är kontrollen av `known_from` det som avgör, inte MAE-nivån. Med en extra månads fördröjning på alla
   tidskänsliga serier finns ungefär halva vinsten kvar.
4. Alltså urvalsevidens: inte "slår". Skuggprognoserna avgör. Båda registreras som skuggor, med flashrättelsen inbyggd.

## (a) Information vid deadline per feature

| Feature | Källa och tidpunkt | Bedömning |
|---|---|---|
| bas `rb_updated` | senaste Riksbanksårgång med `published < deadline(t)` och `cutoff < t`, plus känd miss för t−1 (KPIF t−1 publiceras mitt i t) | ok |
| bas `j2` (J2 V2) | komponenter till t−1, energikorrektion med expanderande OLS (testat i J2), el hel månad t, Brent dag 1–25 | ok |
| `gap`, `energy_news`, `core_dev` | härledda ur ovan; `core_dev` är `shift(1)` | ok |
| `fuel_chg`, `el_dev` | `features.csv`: logdiff mot föregående månad; el mot samma månad tidigare år (bara bakåt) | ok |
| `last_resid_rb/j2` | utfall t−1 minus bas t−1 | ok |
| `ki_*_dev` | KI-enkät t−1 (`shift(1)`), avvikelse från rullande 12-månadersmedel (bakåt) | ok, försiktigt |
| `ea_news` | flash t minus flash t−1, `known_from <= deadline(t)`; backfill sätter `known_from` = periodslut + 2 dagar | **läcker 10 månader**, se nedan |
| `rb_months_ahead`, interaktioner | ur Riksbanksårgången | ok |
| 43 katalogserier (L) | `as_of(deadline(t))`, senaste period ≤ t, säsongsdifferens | se nedan |

**Flash-läckaget.** Eurostats releaser (koder `2-DDMMYYYY-AP`): december 2018 → 4 jan 2019, 2021 → 7 jan 2022,
2022 → 6 jan 2023, 2023 → 5 jan 2024, 2024 → 7 jan 2025, 2025 → 7 jan 2026; januari 2026 → 4 feb 2026; mars 2018
→ 4 april 2018 (påsk). Releasen kommer kl. 11, alltså efter deadline (dag 4, 00:00). Backfillen säger dag 2. I K2:s
backtest har därför december-raderna (och de två andra) ett `ea_news` och fem `ea_flash_*`-features som inte fanns.
Det gäller både prognosraden och träningsraderna. I skarp drift skulle `ea_news` för december bli 0.
Rättelse: `k2b_review.realistic_flash` sätter de kända releasetiderna och alla december till minst 5 januari.
De andra månaderna har jag inte kontrollerat en och en. Stickprov (jan/feb 2023–2025, okt–nov) ligger före dag 4,
men det kan finnas fler sena releaser (påsk, maj). Scenariot "back" nedan sätter en övre gräns för den risken.

**Samma fel finns i J1** (`j1_hyb_energy_ea` använder samma `ea_news`). Det berör inte de skuggade modellerna
(J1 C1 = 50/50 läser inte flash), men J1:s resultat för ea-varianten bör läsas med detta i minnet.

**Katalogserierna (bara L).** Fördröjningarna i katalogen är rimliga eller försiktiga för serier med lag ≥ 8
(FAO, GSCPI, AKU, löner, PPI, utlåning). Avvikelser:
- `gdp_ind_yy` (lag 35): för 30-dagarsmånader blir `known_from` exakt deadline 00:00, och `as_of` tar med `<=`.
  Det strider mot regeln `known_from < deadline` (83 rader). Serien är dessutom `revised=True`.
- `hh_consumption_yy` (lag 15) och `jobads_total` (lag 3, JobTechs historiska annonsfil) har jag inte kunnat
  verifiera i realtid. `jobads_total` är dessutom i praktiken reviderad: en ny hämtning dagen efter gav andra
  värden för 2026-05..10 (se resultat.md, avsnitt 3), trots `revised=False`.
- Alla tre är reviderade eller osäkra. K2:s diagnostik `k2_avg_ridge_lnr` (L utan de 24 reviderade serierna) gav
  samma MAE (0,199), så L:s vinst kommer inte från dem. Revisionsläckage i övrigt: samma slutsats.

**Frysningsfel (rättat):** `catalog_keys()` läste hela `catalog.CATALOG`. När K0 mergades (29 nya prisserier)
växte L tyst från 43 till 72 features på main @ 25a6a6e, så `k2_avg_ridge_l` på main var inte längre den frysta
varianten. Nu är listan fryst i `k2_ml.K2_CATALOG_KEYS` (test `test_k2_feature_set_l_is_frozen`). Med den
reproducerar min körning K2:s tabell exakt: 0,1989 / 0,2009 / 0,2064 och samma Holm-p.

## (b) Förbehandling och val inom fönstret
- `SimpleImputer(median)` och `StandardScaler` sitter i en `Pipeline` som anpassas i varje `fit`, både i inre CV och
  i slutlig refit. Därmed bara på träningsraderna. Boosting får NaN direkt. ok.
- Inget databeroende feature-urval. Listorna S och L är fasta, och griddarna är fasta och förregistrerade. ok.
- Hyperparametrar väljs per fönster med `TimeSeriesSplit(4)` på fönstrets rader. ok.

## (c) Mål och inre CV
- Träningsrader för t: `np.arange(i)` med känt mål, alltså månader s ≤ t−1. Utfallet för t−1 publiceras mitt i t,
  före deadline(t). Inget mål från t eller senare. ok.
- Inre CV: valideringsdelarna ligger efter träningsdelarna i tid. Alla rader ligger före t, så den inre CV:n kan inte se t:s
  framtid. Det finns inget gap mellan inre tränings- och valideringsdel. Det gör hyperparametervalet något optimistiskt,
  men det är inget läckage mot den yttre utvärderingen.
- `tests/test_k2_ml.py` (data kapad vid deadline ger identisk prognos) är rätt byggt. Det kapar dock `feats` som
  redan är beräknade. Jag kontrollerade därför `features.py` för hand: bara `shift`/`diff`/`rolling` bakåt.
- **Testets styrka:** `test_information_set_check_detects_a_code_leak` låter `build_design` läsa katalogen 31 dagar
  efter deadline. Samma jämförelse slår då larm. Begränsning: testet kontrollerar bara att koden respekterar
  `known_from`. Det kan inte upptäcka felaktiga `known_from` i tabellen, vilket var precis felet med flashen.

## (d) Förregistrering
`3964396` (09:31:41) förregistrerar hypotes, 8 varianter, S (14 features), L-regeln, griddar och Holm-familjer.
Koden kom i `2318fa7` (09:33:23), testet i `415ba6f` (09:34:57), och enda körloggen är `20261123T083753Z_k2_ml.csv`
(09:37:53 lokal tid). `hypotes.md` är oförändrad sedan 3964396. Koden stämmer med förregistreringen (S, uteslutna
nycklar, MIN_TRAIN 36, griddar). Att koden kom två minuter efter förregistreringen tyder på att den skrevs innan.
Jag hittar inga tidigare körloggar i någon worktree, men en okommitterad provkörning går inte att utesluta. K2:s
gissning ("ingen klarar") var fel åt fel håll för att det ska se riggat ut.

## (e) Sabotage och känslighet (2015-02..2026-10, n = 141, MAE; 50/50 = 0,2165)

| Scenario | ridge_s | ens_s | ridge_l | Vad det visar |
|---|---|---|---|---|
| base (K2, reproduktion) | 0,2064 | 0,2009 | 0,1989 | exakt K2 |
| **decfix** (rätt flashdatum) | **0,2071** | **0,2022** | **0,1996** | det rättade resultatet |
| fwd: alla katalogserier + flash en månad framåt (framtida data) | 0,2093 | 0,2039 | 0,2079 | **sämre**, se nedan |
| back: en månads extra fördröjning | 0,2125 | 0,2073 | 0,2078 | ungefär halva vinsten kvar |
| plant: flash ersatt med KPIF-utfallet (positiv kontroll) | 0,1869 | 0,1852 | 0,1881 | läckage syns, men bara −0,03 |

- **fwd blev sämre, inte bättre.** Att förskjuta serierna en månad ger modellen nästa månads siffror, och de säger mindre
  om KPIF för t än samma månads siffror. Signalen ligger alltså i rätt månad, inte i "mer data". Därför visar fwd inte
  att utvärderingen kan upptäcka läckage. Det gör den positiva kontrollen "plant": KPIF-förändringen för t planterad i
  `ea_news` ger tydligt lägre MAE (ML-aktiva månader 0,193–0,197 mot 0,211–0,222). Men den hårda krympningen gör att
  även ett perfekt läckage bara ger cirka −0,04. Ett läckage av K2:s storlek (−0,015) syns alltså inte på MAE-nivån.
  Därför är datumgranskningen i (a) det som bär domen.
- **back:** med en månads extra fördröjning på varje tidskänslig serie (flash, KI, marknadsdata) är vinsten −0,004 /
  −0,009 / −0,009 (rå p 0,12 / 0,047 / 0,009). Det är en övre gräns för vad okontrollerade sena releaser kan kosta.
- Instabilitet: att flytta en enda flashmånad (mars 2018) ändrade ridge_l från 0,2013 till 0,1996, eftersom
  hyperparametervalet slår om. Tredje decimalen är brus.

## (f) Utan 2022–23 och per år (decfix)
- Tränat och utvärderat utan 2022-01..2023-12 (base-data, n = 117): ridge_s 0,1884, ens_s 0,1884, ridge_l 0,1852
  mot 50/50 0,1971 (rå p 0,034 / 0,048 / 0,018). Bara utvärderat utan 2022–23 (decfix): −0,005 / −0,008 / −0,012,
  rå p 0,16 / 0,09 / 0,03. Energikrisen bär alltså ungefär hälften av vinsten. Resten är svag men åt samma håll.
- Per år, diff mot 50/50 (decfix; ridge_s / ens_s / ridge_l):

| År | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (10 mån) |
|---|---|---|---|---|---|---|---|---|---|
| ridge_s | −0,005 | +0,014 | −0,010 | +0,005 | −0,042 | −0,016 | −0,021 | −0,048 | +0,015 |
| ens_s | −0,005 | +0,006 | −0,004 | −0,002 | −0,065 | −0,024 | −0,034 | −0,060 | +0,025 |
| ridge_l | −0,008 | +0,008 | −0,049 | −0,021 | −0,051 | −0,033 | −0,039 | −0,022 | +0,018 |

- 2024–26 (använd period, bara rapport, decfix): ens_s 0,220, ridge_l 0,230 mot 50/50 0,246. Båda inte sämre
  än 50/50, så skärmens andra villkor håller.

## (g) DM och Holm
- `evaluation.dm_test`: absolutfelsförlust, Newey–West-varians, Harvey–Leybourne–Newbold-korrektion, t-fördelning.
  `j1_hybrid.dm_one_sided`: p/2 om medeldiffen < 0, annars 1 − p/2. Det är rätt ensidigt test för H1 "varianten har lägre MAE".
  Nästlingen motiverar ensidigt test: 50/50 är specialfallet residual = 0.
- `j2_el.holm`: stegvis Holm med monoton maxning. Kontrollerat för hand. Familjen är K2:s 8 förregistrerade
  per referens, som förregistrerat. Rätt familj för frågan.
- 36 identiska månader (2015-02..2018-01, före MIN_TRAIN) ingår i n = 141. De ändrar knappt t-statistikan
  (nollor sänker både medel och varians), och delurvalet 2018-02.. (n = 105) ger samma bild.
- Utöver familjen: projektet har nu 32 varianter totalt, och Holm över 8 tar inte hänsyn till de andra 24.
  Ridge_l:s Holm-p 0,025 skulle klara en familj på cirka 30 bara med nöd (rå p 0,003 · 30 ≈ 0,09). Ens_s skulle inte klara den.

## Följder
- `k2_avg_ens_s` och `k2_avg_ridge_l` registreras som skuggor, med `realistic_flash` inbyggd (samma
  informationsmängd som rättad backtest; skuggornas historik = decfix-serierna exakt).
- `k2_avg_ridge_s` registreras inte.
- **Skarp drift måste ha samma information som backtesten.** Backtesten antar att flashen för t finns vid deadline
  (dag 4). Månadsjobbet körs 05:23 UTC dag 1–4, och K1:s statusregel ger FINAL redan dag 1 när el och drivmedel är
  kompletta. Flashen kommer ofta dag 1–3 kl. 11. Därför: (1) `pipeline monthly` hämtar nu flashen och K2:s 43 serier
  (`fetch_shadow_observations`), och (2) en K2-skugga blir bara FINAL före dag 4 om flashen för t finns i tabellen
  (`ShadowModel.ready`). Annars blir den PRELIMINARY och ersätts av nästa dags körning. Dag 4 blir den FINAL ändå.
- **Rekommendation till main (inte gjort här, berör delad kod):** `observations.upsert` sätter för nya perioder
  `known_from = min(periodslut + lag, hämtdatum)`. För en release som kommer senare än katalogens lag (som december-
  flashen) blir det fel även framåt. `max` med första hämtdatum vore den säkra regeln för hämtade rader. Den
  är först ett problem när framtida backtester läser hämtade rader, men det är just det skuggorna gör.
