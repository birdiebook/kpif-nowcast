# CLAUDE.md – kpif-nowcast

## Vad projektet är

Ett **lärprojekt** där Johannes lär sig prediktiv modellering genom att bygga en
nowcast av svensk KPIF-inflation (nästa månads siffra innan SCB publicerar den).

Arbetssättet är agentiskt: agenten skriver koden och gör räknejobbet, Johannes
styr, granskar och fattar besluten. **Målet är lika mycket Johannes förståelse
som modellens träffsäkerhet.** En snabb lösning som han inte förstår är ett
misslyckande för projektet.

Johannes bakgrund: BI och data engineering. Han kan SQL, pipelines och datakvalitet
väl – förklara inte det. Förklara istället ML-, statistik- och prognoskoncept.

## Arbetsregler

Håll det enkelt och fokusera på det som gör skillnad för resultatet. Inga
quizfrågor eller pedagogiska övningar om Johannes inte ber om det.

1. **Förklara kort** de modelleringsval som spelar roll: vad och varför, i klartext.
2. **Stanna bara vid verkliga beslutspunkter** (uppdelning i tränings-/testdata,
   utvärderingsmått, prognoshorisont). Ge en rekommendation, inte en meny.
3. **Flagga läckagerisk direkt.** All data måste vara sådan som fanns tillgänglig vid
   prognostidpunkten: publiceringsfördröjning, reviderade siffror, features beräknade
   över hela perioden.
4. **Jämför alltid mot baslinje** – naiva baslinjer och, där det finns, Riksbankens prognos.
5. **Var ärlig om osäkerhet.** Säg när en förbättring kan vara slump, och när något
   inte gick att verifiera.
6. **Beslutsloggen** (`docs/beslutslogg.md`) uppdateras kort vid viktiga val.

## Faser

- **Fas 0** – grundupplägg ✅
- **Fas 1** – kartlägg datakällor → `docs/datakallor.md` ✅
- **Fas 2** – KPIF-historik, naiva baslinjer, tidsbaserad backtest ✅
  (`python -m kpif_nowcast.data` hämtar, `python -m kpif_nowcast.backtest` utvärderar)
- **Fas 3** – första modellen: el och drivmedel ✅ (el bara från 2021-11; ENTSO-E-nyckel saknas)
  (`python -m kpif_nowcast.sources.elpris`, `python -m kpif_nowcast.features`, `python -m kpif_nowcast.backtest_phase3`)
- **Fas 4** – prognos per komponent (bidrag till m/m från TAB6628) ✅ (`python -m kpif_nowcast.backtest_phase4`)
- **Fas 4b** – förbättringar: KI-prisplaner ✅ (ingen effekt), skattekalender ✅ (bara vid stora
  händelser → manuell justering), kvar: ENTSO-E, rörliga elavtal, januari-energi
- **Fas 5** – längre horisont (3–12 mån) ✅: versionerad observationstabell
  (`python -m kpif_nowcast.observations`, `as_of()`), backtest `python -m kpif_nowcast.horizon`.
  Riksbanken vinner tydligt; 12 mån ≈ "det blir 2 %".
- **Fas 5b** – datakatalog ✅: 64 serier i åtta områden i `catalog.py` (en `Spec` per serie),
  hämtas med `python -m kpif_nowcast.observations [nycklar]`, dokumenteras i `docs/datakatalog.md`
  (`python -m kpif_nowcast.catalog`). Dashboard "Sverigeläget" i Claude Data (länk i `CLAUDE.local.md`):
  `python -m kpif_nowcast.sverige_dashboard` skriver `outputs/sverige/*.json` + `index.html`, laddas upp
  som assets och datasets. Kvar: test av prognosvärde,
  Arbetsförmedlingen (varsel, inskrivna, kräver skrapning av xlsx). Vision: `docs/vision.md`.
- Redigera filer med svenska tecken via Edit/Python, **aldrig PowerShell Get/Set-Content**
  (PS 5.1 läser som ANSI och förstör å/ä/ö).
- **Fas 5c** – autonoma jobb J1–J7 (`docs/forbattringsplan.md`) ✅: J2 (`j2_el.py`) och J1
  (`j1_hybrid.py`) mergade, körs som skuggprognoser från 2026-12. J3–J7 också mergade.
- **Körning 2** – Sverige på djupet, spår K0–K6: `docs/autonom-korning-2.md`
- **Fas 6** – drift oberoende av egen dator (upplägg A, se beslutsloggen 2026-11-22):
  GitHub Actions + Parquet i objektlagring + DuckDB, dbt för transformationer/tester,
  MLflow, champion/challenger, Pages-dashboard

Uppdatera listan när en fas är klar.

## Månadsrutin (skarp prognos)

1. **Dag 1–4 i månaden efter prognosmånaden** (före snabb-KPI): `python -m kpif_nowcast.forecast`.
   Status ska bli FINAL (hel månad el, drivmedel till minst den 20:e).
2. Kolla om stora beslutade engångshändelser träffar månaden (moms, skatter, avgifter,
   t.ex. om tillfälligt sänkt drivmedelsskatt löper ut). Justera i så fall med
   `--adjust <pe> --note "<varför>"` och ange källa i noten.
3. Committa och pusha `forecasts/<månad>.json` direkt – tidsstämpeln är beviset.
4. Efter SCB:s slutliga siffra (~12–15:e): `python -m kpif_nowcast.data` och
   `python -m kpif_nowcast.scorecard`, committa `forecasts/SCORECARD.md`.
5. Efter steg 3 och 4: `python -m kpif_nowcast.export_dashboard` och ladda upp filerna i
   `outputs/dashboard/` till dashboarden i Claude Data (länk i `CLAUDE.local.md`, committas inte):
   ny asset per fil, uppdatera sedan `datasets/<id>` (`source.url` och `updated`).

## Tekniska konventioner

- Python. Kod i `src/kpif_nowcast/`, utforskning i `notebooks/`.
- Data committas aldrig. Allt hämtas med skript så att det är reproducerbart.
  Spara rådata med hämtdatum. Licensvillkor kontrolleras per källa.
- Inga hemligheter i koden – använd `.env` (se `.env.example`).
- Backtest ska vara **expanding window / rolling origin**: träna bara på data före
  varje prognosmånad.
- Kod och kommentarer på engelska (publikt repo), dokumentation i `docs/` på svenska.
- Repot är **publikt**. Inga personliga uppgifter eller jobbsökningsanteckningar här.
