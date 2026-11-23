# CLAUDE.md – kpif-nowcast

## Vad projektet är

Ett projekt som står på egna meriter. Det bygger **bästa möjliga nowcast och prognos av
svensk KPIF-inflation** (nästa månads siffra innan SCB publicerar den, och längre horisonter),
och genom KPIF-linsen **bästa möjliga bild av läget i Sverige**.

**Målet är bästa möjliga lösning.** Varje val ska ge snabb och effektiv progress med kvalitet:
högre träffsäkerhet, bättre data vid rätt tidpunkt, stabil drift och en tydligare bild av Sverige.
Det är inte ett lärprojekt. Pedagogik är inget mål i sig.

Arbetssättet är agentiskt: agenten skriver koden och gör räknejobbet, Johannes
styr, granskar och fattar besluten.

Johannes bakgrund: BI och data engineering. Han kan SQL, pipelines och datakvalitet
väl – förklara inte det.

## Arbetsregler

Håll det enkelt och fokusera på det som gör skillnad för resultatet. Välj den lösning som
ger bäst resultat och snabbast progress, inte den som är lättast att lära sig av.

1. **Förklara kort** de modelleringsval som spelar roll: vad och varför, så att de går att granska.
2. **Stanna bara vid verkliga beslutspunkter** (uppdelning i tränings-/testdata,
   utvärderingsmått, prognoshorisont). Ge en rekommendation, inte en meny.
3. **Flagga läckagerisk direkt.** All data måste vara sådan som fanns tillgänglig vid
   prognostidpunkten: publiceringsfördröjning, reviderade siffror, features beräknade
   över hela perioden.
4. **Jämför alltid mot baslinje** – naiva baslinjer och, där det finns, Riksbankens prognos.
5. **Var ärlig om osäkerhet.** Säg när en förbättring kan vara slump, och när något
   inte gick att verifiera.
6. **Beslutsloggen** (`docs/beslutslogg.md`) uppdateras kort vid viktiga val.

## Agentiskt arbete (AI-agentic first)

Projektet ska tänja gränserna för vad AI-agenter kan leverera själva.
- **Bedöm arbete i agentlinsen, inte människolinsen.** Omfattning, tidsåtgång, ambitionsnivå och
  vad som är "för stort" bedöms utifrån vad agenter klarar: parallella spår, dygnet runt, minuter
  per uppgift. Uppskatta inte i människotimmar, och skala inte ned planer för att de skulle vara
  mycket för en människa. Flaskhalsen är kvalitetskontroll och tillgång till data, inte arbetstid.

### Storleksbedömning

- **Enheten är ett agentspår:** en avgränsad leverans med tester, av en agent i egen worktree.
  Den aktuella kostnaden per spår (tid, verktygsanrop, tokens) står i
  [`docs/agentkalibrering.md`](docs/agentkalibrering.md). Läs den innan en körning planeras.
- **Kapacitet = parallella spår × tid.** Utgå från användningsfönstret (5 h, se kalibreringen), inte från ett fast tak på antal spår. Dimensionera backloggen så att den fyller körningen
  (till exempel en natt), med reserv. Ett jobb bedöms som "1 spår", "3 spår parallellt",
  "1 spår + granskning", aldrig i timmar eller dagar.
- **Taket sätts av de verkliga flaskhalsarna:**
  - Statistisk budget: varianttak och använd period. Det är den knappaste resursen.
  - Datatillgång: konto, PDF eller 403 ger BLOCKED.
  - Verifiering: ett oberoende granskningsspår per positivt resultat som ska användas.
  - Johannes beslut: byte av huvudmodell.
  - Kalendertid: live-utfall kommer en gång i månaden.
- **"För stort"** betyder att något inte går att verifiera eller avgränsa. Det delas upp i spår,
  utan att ambitionen sänks.
- **Kalibrera efter varje körning:** logga tid, anrop och tokens per spår i
  `docs/agentkalibrering.md`, och justera tumreglerna när siffrorna ändras. Agenten levererar hela vägen
till main. Den väntar inte på godkännande för det som går att verifiera med tester och regler.
- **Agenten får committa, merga och pusha till `main`** när pytest är grönt på det sammanslagna
  resultatet och reglerna ovan är uppfyllda. Parallella spår kör på egna grenar och worktrees
  (`auto*/<spår>`) och mergas till main av orkestreraren när spåret är klart. Små ändringar
  (dokumentation, fixar) får committas direkt på main.
- Agenten får aktivera GitHub Actions-workflows (genom merge) när en lokal körning av stegen är grön.
- **Skyddat, fortfarande Johannes beslut:** byte av huvudmodell (`MODEL_NAME` i `forecast.py`).
  Skarpa prognoser i `forecasts/<månad>.json` skrivs bara av månadsrutinen och skrivs aldrig om
  i efterhand, eftersom tidsstämpeln är beviset.
- **Aldrig:** force-push, omskrivning av historik på main, radera andras grenar, data eller hemligheter i git.
- Förregistrering, läckagetester, Holm-justering och ärlig rapportering gäller oförändrat. De är det
  som gör att agentens resultat går att lita på utan manuell granskning.

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
- **Körning 2** – Sverige på djupet ✅ (17 spår K0–K13, slutrapport i `docs/auto2/STATUS.md` på `auto/status`):
  prisled, regional data, ML på residualen (`k2_avg_ridge_l`/`k2_avg_ens_s` som skuggor), förklaringar,
  publiceringskalender (`publication.py`), skattekalender (`docs/skattekalender.md`), månadsbrev.
- **Fas 6** – drift oberoende av egen dator, delvis ✅: GitHub Actions (veckohämtning, skuggprognoser,
  Pages), DuckDB-datatester, champion/challenger i SCORECARD. Kvar: objektlagring, MLflow,
  revisionsversioner (vintages) i observationstabellen.

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
