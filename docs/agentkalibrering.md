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
