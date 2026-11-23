# K0 Prisleden: resultat (urvalsevidens)

Förregistrering: [hypotes.md](hypotes.md). Serier: [serier.md](serier.md). Råtabeller för alla 29 serier och
tre horisonter: [results_raw.md](results_raw.md). Körning: `experiments/runs/20261123T084148Z_k0_screen.csv`.
Screeningen räknas inte mot taket. K0 förbrukar **2 varianter** (K0-C1, K0-C2). Global total: 23 före
körning 2 + 2 = 25, plus det andra spår i körning 2 förbrukar (se STATUS).

## Byggt
- `catalog_prices.py`: 29 nya månadsserier i observationstabellen, med publiceringsfördröjning och
  revised-flagga. Grupperna är PPI, KPIF-XE/varor/tjänster, KI:s pris- och inköpsplaner, IMF-råvaror för
  mat samt statsobligationsräntor och SWESTR. Kvalitetskontrollen är grön.
- `k0_screen.py`: J3:s protokoll oförändrat (samma kod), sedan de två förregistrerade varianterna.
- `tests/test_k0_prices.py`: katalog, cache, urvalsregel, datakvalitet och informationsmängd. Screeningens
  korrektion och kombinationen för t är identiska med och utan data efter t:s deadline.

## Screening (BH q = 0,10 per horisont)
| Horisont | Bas (MAE) | Bästa serie | Diff | p ensidigt (rå) | BH-q | Överlever BH |
|---|---|---|---|---|---|---|
| h=1, 2017-02..2026-10 (n=117) | rb_updated 0,281 | ppi_hmpi_food (rev.) | −0,004 | 0,32 | 0,99 | 0 av 29 |
| h=1, 2015–2026 (n=141) | rb_updated 0,256 | ppi_hmpi_food (rev.) | −0,003 | 0,32 | 0,99 | 0 av 29 |
| h=3 (n=117) | Riksbanken 0,546 | cocoa_usd (rev.) | −0,002 | 0,40 | 0,99 | 0 av 29 |
| h=12 (n=117) | Riksbanken 1,480 | swestr | −0,001 | 0,21 | 1,00 | 0 av 29 |

Ingen serie överlever. Gissningen var 0–1 på h=1 och h=3. PPI för livsmedel hamnade överst på h=1, men
skillnaden är för liten för att skiljas från slump.

## Varianter
Urvalsregeln: ingen serie överlevde BH. Därför valdes de tre med lägst rå p, högst en per källgrupp:
`ppi_hmpi_food` (PPI), `rapeseed_oil_usd` (IMF), `swestr` (räntor). SWESTR finns först från 2021-09. Med
kravet på 24 träningsmånader blir korrektionen därför aktiv först från 2024-10. Den är alltså bara aktiv i
25 månader, och alla ligger i den redan använda perioden 2024–26.

| Variant | Bas | Period | MAE | Bas-MAE | Diff | p ensidigt | Holm-p (2) | n | aktiva |
|---|---|---|---|---|---|---|---|---|---|
| K0-C1 | rb_updated | 2017-02..2026-10 | 0,281 | 0,281 | +0,000 | 0,51 | 0,51 | 117 | 25 |
| K0-C1 | rb_updated | 2015–2026 | 0,256 | 0,256 | +0,000 | 0,51 | – | 141 | 25 |
| K0-C2 | 50/50 rb_updated + J2 V2 | 2017-02..2026-10 | 0,226 | 0,232 | −0,006 | 0,049 | 0,097 | 117 | 25 |
| K0-C2 | 50/50 rb_updated + J2 V2 | 2015–2026 | 0,212 | 0,217 | −0,005 | 0,050 | – | 141 | 25 |
| K0-C2 | 50/50 | 2024–26 (använd, bara rapport) | 0,227 | 0,246 | −0,019 | 0,038 | – | 34 | 25 |

**K0-C2 klarade urvalsskärmen formellt** (Holm-p 0,097 < 0,10), men är **obekräftad
(revisionsläckage möjligt)**: två av tre serier (PPI och rapsolja) är reviderade. Tre saker till
försvagar resultatet:
- Hela vinsten kommer från 25 månader 2024-10..2026-10, alltså den period som redan använts för modellval.
  Före dess är prognosen identisk med 50/50.
- Koefficienterna är skattade på 24–48 månader. Tre månader (2025-11, 2026-10, 2024-10) står för 63 % av
  vinsten.
- Störst vikt har SWESTR (−0,28 pe per pe i säsongsdifferentierad månadsändring). Det finns ingen tydlig
  mekanism för att den ska förutsäga KPIF:s miss en månad framåt.

K0-C1 med samma serier ovanpå rb_updated ger exakt ingenting.

## Slutsats: inget håller
Ingen prisledsserie tillför något robust utöver rb_updated, Riksbanken eller 50/50-snittet. K0-C2:s formella
träff är för tunn för att frysas som skuggprognos: få månader, använd period, reviderade data och oklar
mekanism. **Rekommendation:** frys inte K0-C2. Serierna behålls i katalogen för dashboarden ("läget i
prisleden") och som indata till K2:s ML-spår, där de kan prövas med nästlad validering.

## Vad lärde vi oss
- J3:s resultat håller även för priser närmare KPIF. En säsongsdifferentierad månadsnyhet som linjär
  korrektion fångar inget som Riksbankens uppdaterade prognos eller J2:s elmodell inte redan har.
  Producent- och importpriser för konsumtionsvaror och livsmedel, handelns prisplaner och råvarupriser på mat
  ger alla |diff| ≤ 0,004 pe.
- Gissningen stämde i stort: 0 överlevare, kombinationen nära noll mot rb_updated. Att en kombination fick
  rå p ≈ 0,05 mot 50/50 men inte mot rb_updated tyder snarare på brus än på signal. Samma serier borde
  hjälpa båda baserna om de bar information om priser.
- Urvalsregeln "lägst rå p" kan välja en kort serie (SWESTR från 2021). Då testas kombinationen på mycket
  färre månader än screeningen. En framtida regel bör kräva full täckning från 2015.
- Rätt form slår bredd: värdet ligger fortfarande i att modellera rätt komponent (som J2 gjorde för el), inte
  i fler makroserier som fria korrektioner.
