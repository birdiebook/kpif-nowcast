# Agentkalibrering: vad ett spår kostar

Mätdata för storleksbedömning (se CLAUDE.md, "Storleksbedömning"). En rad per spår, fylls på
efter varje körning. Tumreglerna överst justeras när siffrorna ändras.

## Tumregler (senast justerade 2026-11-23, körning 2)

- Ett väl avgränsat spår med tester: **ca 13–18 min, 40–60 verktygsanrop och 180–200k tokens**.
- Det gäller oavsett typ (data, drift, ML, förklaring). Typen verkar spela mindre roll än avgränsningen.
- **Undantag: datatunga spår med många källor och udda format** (K4: 3 källor, Excel-pivotcache, 241 serier)
  tar ungefär dubbelt så lång tid: cirka 30 min, 110 anrop och 260k tokens. Räkna dem som 2 spår, eller dela per källa.
- Med 3 spår parallellt ger det cirka 10–12 spår per timme. Orkestrerarens merge och pytest på main
  tar 2–4 min per spår.
- Körning 1 var dimensionerad i människotempo (7 jobb) och tog slut efter 30 minuter.
- **Användningsfönster:** K0–K6 (sex spår plus orkestrering, 3 parallellt) använde ca **20 % av ett
  5-timmarsfönster**. Ett fönster rymmer alltså ungefär **30 spår**. Med 3 parallella spår blev
  parallelliteten flaskhalsen och inte budgeten. Kör **5–6 spår parallellt** och dimensionera
  backloggen till ca 25 spår per fönster, med reserv för granskning.

- **Granskningsspår** som kontrollerar mot externa källor (K2b, K11) tar 70–75 min, styrt av väntan på nät
  och hastighetsbegränsningar, inte av arbete. De gav ändå körningens viktigaste fynd (två verkliga läckor).
  Starta dem tidigt och parallellt med annat.
- **Körning 2 totalt:** 17 spår på ca 3,5 h väggtid. Modellspåren var de snabbaste (10–22 min). Med 6
  parallella spår blev orkestrerarens merge och pytest på main (2–15 min per merge, växer med sviten) en ny
  flaskhals. Nästa gång: merga i omgångar och kör pytest en gång per omgång.

## Mätningar

| Datum | Körning | Spår | Typ | Tid (min) | Verktygsanrop | Tokens (k) | Leverans |
|---|---|---|---|---|---|---|---|
| 2026-11-22 | 1 | J1–J7 (7 jobb, 2 parallellt) | blandat | ~30 totalt | – | – | 23 varianter, 7 grenar |
| 2026-11-23 | 2 | K2 ML | modell | 14,8 | 45 | 178 | 9 varianter, nästlad CV, 41 tester |
| 2026-11-23 | 2 | K1 Drift | drift | 17,2 | 52 | 203 | pipeline, 2 workflows, 12 datatester, repro |
| 2026-11-23 | 2 | K0 Prisleden | data + screening | 17,7 | 61 | 193 | 29 serier, screening, 2 varianter |
| 2026-11-23 | 2 | K3 Förklaring | analys | 13,1 | 42 | 180 | explain.py, 13 tester, 24 mån historik |
| 2026-11-23 | 2 | K6 Om lätt (vintages, nordisk el) | data + test | 13,2 | 25 | 129 | 2 varianter, 1 BLOCKED-del ersatt med kontroll |
| 2026-11-23 | 2 | K4 Regionalt | data (många källor) | 30,2 | 111 | 264 | 241 länsserier, xlsx-pivotläsare, kvalitetskontroll |
| 2026-11-23 | 2 | K9 Horisont 3–12 | modell | 10,2 | 44 | 146 | 4 varianter (negativt) |
| 2026-11-23 | 2 | K7 Tjänster | modell | 10,7 | 32 | 164 | 5 varianter (negativt) |
| 2026-11-23 | 2 | K13 Skatterensad bas | modell + kalender | 17,6 | 57 | 207 | 2 varianter, skattekalender 2005–27 |
| 2026-11-23 | 2 | K8 Livsmedel | modell | 21,7 | 41 | 197 | 4 varianter (negativt) |
| 2026-11-23 | 2 | K12 Globalt test | utvärdering | 24,9 | 51 | 193 | SPA/StepM/MCS i numpy, omkörbart |
| 2026-11-23 | 2 | K10 Pages | drift + frontend | 28,4 | 81 | 185 | shim, workflow, lokal webbläsarkontroll |
| 2026-11-23 | 2 | K5 Sverigeläget v2 | frontend + text | 31,7 | 102 | 315 | 9 dataset, sida, månadsbrev |
| 2026-11-23 | 2 | K2b Granskning + onlinerepro | granskning + drift | 74,2 | 132 | 262 | läckage hittat; ~50 min väntan på nätbaserad hämtning |
| 2026-11-23 | 2 | K11 Publiceringskalender | granskning (många källor) | 74,4 | 170 | 309 | 4 läckor hittade; Eurostat 429 gjorde det långsamt |
