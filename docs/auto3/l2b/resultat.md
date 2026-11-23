# L2b Tillväxtverkets portal: resultat

**Status: BLOCKED för data, delvis levererat.** Inga nya serier. Eurostat-serierna från L2 (`guest_nights_*`, 80 d)
ligger kvar oförändrade. Levererat: Tillväxtverkets publiceringsfördröjning belagd för åtta månader, revisionsregeln
bekräftad och en nivåjämförelse Tillväxtverket mot Eurostat. Inga modellvarianter, inga p-värden.

## Varför BLOCKED
- Värden nås nu (HTTP 200), men `tillvaxtdata.tillvaxtverket.se/statistikportal` är en DivePort-portal (Dimensional
  Insight, Tomcat). Sidan har `<meta name="robots" content="noindex, nofollow">` och `/robots.txt` saknas (404).
- Den har inget öppet, maskinläsbart gränssnitt. Det finns inget PxWeb-API och ingen CSV- eller xlsx-fil med stabil
  URL. Tillväxtverkets sidor om inkvartering länkar bara till portalen och till PDF:er (kvalitetsdeklarationer,
  statistikens framställning, årliga PM). Data hämtas bara genom portalens interna JSON-RPC (`/statistikportal/rpc/...`,
  `instance-rpc/<portlet>`), som kräver session-id och CSRF-token från `state.js`. Det är odokumenterat och
  sessionsbundet, alltså interaktiv skrapning av ett BI-gränssnitt.
- Behörighetssystemet nekade ett första RPC-anrop (`nav-get-pages`) som obehörig åtkomst. Jag har inte försökt runt det.
- Väg framåt (Johannes): be Tillväxtverket (inkvartering@tillvaxtverket.se) om en öppen fil eller ett API för riket per
  månad, eller godkänn uttryckligen att portalens RPC används. Tillväxtverket är statistikansvarig myndighet, och
  officiell statistik ska vara fritt tillgänglig. Själva datan är alltså inte problemet, utan att det saknas ett
  sanktionerat maskingränssnitt.

## Publiceringsfördröjning (belagd, se [publiceringskalendern, avsnitt L2b](../../publiceringskalender.md))
- 2026-08 → 2026-09-29 (29 d), 2026-09 → 2026-10-29 (29 d; portalens "Data uppdaterad").
- Från SCB:s publiceringskalender, NV1701, publiceras hos Tillväxtverket: 2026-10 → 2026-11-26 (26 d),
  2026-11 → 12-22 (22 d), 2026-12 → 2027-01-28 (28 d), 2027-01 → 02-26 (26 d), 2027-02 → 03-30 (30 d),
  2027-03 → 04-29 (29 d). Slutlig årsstatistik 2026 → 2027-03-30.
- **22–30 d bekräftat.** Det ger t−1 vid deadline, mot t−3 via Eurostat. En framtida serie bör ha `lag_days=30`.
- **revised=True.** Månadssiffrorna är preliminära. Anläggningarna kan revidera till och med mars året efter, och
  slutlig statistik fastställs i mars. För 2025 blev den slutliga statistiken ca 2 % lägre än den preliminära
  (Tillväxtverkets sida "Inkvartering", frågor och svar, och PM "Inkvartering 2025").

## Jämförelse mot Eurostat (överlapp, miljoner gästnätter)
Tillväxtverket enligt PM "Inkvartering 2025" (slutlig) och nyheten "Stark sommar för svensk turism" (2026-09-29,
preliminär). Eurostat enligt senaste vintage i `observations.parquet`.

| | Tillväxtverket | Eurostat (L2) | Kommentar |
|---|---|---|---|
| Hotell 2025 | 43,2 | 43,19 | samma |
| Totalt 2025 | 70,8 | 65,68 | Tillväxtverkets total räknar sannolikt med SoL (förmedlade privata stugor och lägenheter), ca 5 M |
| Svenska 2025 | 51,4 (+1,0 okänt hemland) | 48,20 | Eurostats svenska = totalt − utländska, alltså inklusive okänt hemland. Skillnaden är mest SoL |
| Utländska 2025 | 18,4 | 17,48 | |
| Totalt 2025 mot 2024 | +2,5 % | +2,9 % | |
| Sommar (jun–aug) 2026 mot 2025, totalt | +3,6 % | +4,1 % | |
| … hotell | +5,6 % | +5,4 % | |
| … svenska | +2,4 % (21,0 M) | +2,3 % (20,61 M) | |
| … utländska | +6,2 % (9,8 M) | +8,1 % (9,50 M) | största avvikelsen |

- Hotellserien stämmer i nivå, och de svenska gästernas utveckling stämmer på 0,1 pe. Totalen ligger på en annan
  nivå (SoL ingår inte i Eurostats I551–I553), men tillväxttakterna ligger inom ca 0,5 pe. Undantaget är utländska
  gäster sommaren 2026 (+8,1 % mot +6,2 %). Det kan bero på olika vintage (Eurostat har senare revideringar,
  Tillväxtverket jämför preliminärt 2026 mot slutligt 2025) eller på SoL. Jag har inte kunnat verifiera vilket.
- **Månadsförändringar kunde inte jämföras.** Tillväxtverkets månadsdata finns bara i portalen. PM:et ger bara att
  april hade den största ökningen 2025 (diagrammet visar +12 %), och Eurostat ger också +12,0 % för april 2025.
- Slutsats: Eurostat är en bra proxy för Tillväxtverket när det gäller hotell och svenska gäster. Det man förlorar är
  fördröjningen (t−3 mot t−1), inte innehållet.

## Ändrade filer
- `docs/publiceringskalender.md`: nytt avsnitt "Körning 3: L2b" (inga nyckelrader, så kalendertestet påverkas inte).
- `src/kpif_nowcast/catalog_travel.py`: bara modulens docstring (portalen nås men är inte maskinläsbar, och SoL-skillnaden).
  Inget beteende ändrat.
