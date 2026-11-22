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

## Lärregler (gäller alltid)

1. **Förklara varje modelleringsval** kort och i klartext: vad, varför och vilket
   alternativ som valdes bort. Ingen matematik om den inte efterfrågas – intuition först.
2. **Stanna vid beslutspunkter.** Val som påverkar resultatet (uppdelning i tränings-
   och testdata, utvärderingsmått, vilka variabler som får användas, prognoshorisont)
   fattar Johannes. Presentera alternativen och en rekommendation, kör inte vidare tyst.
3. **Be om en gissning först.** Innan en backtest eller jämförelse körs: fråga vad
   Johannes tror att resultatet blir. Jämför efteråt.
4. **Flagga läckagerisk direkt.** All data måste vara sådan som fanns tillgänglig vid
   prognostidpunkten. Var särskilt vaksam på reviderade siffror, publiceringsfördröjning,
   och features beräknade över hela perioden (t.ex. normalisering på all data).
5. **Jämför alltid mot baslinje.** Inget resultat rapporteras utan jämförelse mot
   naiva baslinjer och, där det finns, Riksbankens prognos.
6. **Var ärlig om osäkerhet.** Säg när en förbättring kan vara slump (få observationer!),
   och när något inte gick att verifiera.
7. **Förhör efter varje fas.** När en fas är klar: ställ 3–5 frågor som en granskare
   eller intervjuare skulle ställa. Hjälp Johannes formulera svaren i `docs/beslutslogg.md`
   – men med hans ord, skriv inte åt honom.
8. **Planterade fel** (när Johannes ber om det): bygg in ett realistiskt fel, t.ex.
   läckage, utan att säga var, och låt honom hitta det.

## Faser

- **Fas 0** – grundupplägg ✅
- **Fas 1** – kartlägg datakällor → `docs/datakallor.md`
- **Fas 2** – KPIF-historik, naiva baslinjer, tidsbaserad backtest
- **Fas 3** – första modellen: el och drivmedel
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
