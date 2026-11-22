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
- **Fas 4** – prognos per komponent (energi, livsmedel, varor, tjänster) viktad med SCB:s vikter
- **Fas 5** – längre horisont (3–12 mån): arbetslöshet, löner, BNP, krona

Uppdatera listan när en fas är klar.

## Tekniska konventioner

- Python. Kod i `src/kpif_nowcast/`, utforskning i `notebooks/`.
- Data committas aldrig. Allt hämtas med skript så att det är reproducerbart.
  Spara rådata med hämtdatum. Licensvillkor kontrolleras per källa.
- Inga hemligheter i koden – använd `.env` (se `.env.example`).
- Backtest ska vara **expanding window / rolling origin**: träna bara på data före
  varje prognosmånad.
- Kod och kommentarer på engelska (publikt repo), dokumentation i `docs/` på svenska.
- Repot är **publikt**. Inga personliga uppgifter eller jobbsökningsanteckningar här.
