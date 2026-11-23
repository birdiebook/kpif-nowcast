# K5 Sverigeläget v2 och månadsbrev: resultat

Skriven 2026-11-23. Inga modellvarianter (0 förbrukade). Inget laddades upp till Claude Data; det gör orkestreraren
utifrån `outputs/sverige/MANIFEST.json`.

## Vad som byggdes

### 1. Sverigeläget v2 (`src/kpif_nowcast/sverige_dashboard.py`)
`python -m kpif_nowcast.sverige_dashboard` skriver till `outputs/sverige/` (gitignorerat):

| Fil | Innehåll | Rader |
|---|---|---|
| `overview.json`, `series.json`, `pressure.json`, `ai.json` | v1, oförändrad metod | 92 / 15 043 / 2 221 / 466 |
| `prisled.json` | K0: KPIF, KPIF-XE, varor, tjänster, PPI konsumtionsvaror och livsmedel, KI:s prisplaner, råvaror, räntor (styrränta, SWESTR, stat 2/10 år, bolån), från 2015 | 3 309 |
| `af.json` | J6: inskrivna, öppet arbetslösa, varsel (riket) med tremånadersmedel och årsförändring, från 2010 | 606 |
| `region.json` | K4 `latest_by_county()` för AF-andel, AKU, småhuspris, konkurser per 10 000, varsel; rader med `behind_national` borttagna (3 AKU-län); varsel per län t.o.m. 2026-03 | 107 |
| `ai_indicator.json` | J7: maskininlärning och AI per 10 000 annonser per år, företagens AI-användning, indikatorn | 39 |
| `forecast.json` | skarp prognos (fil), skuggor (`forecasts/shadow/`), K2-kandidat, rb_updated, Riksbanken; kolumn `evidence` | 7 |
| `champion.json` | `champion.table` (samma som SCORECARD.md) | 5 |
| `explain_summary.json`, `explain_text.json`, `explain_components.json` | K3:s förklaring för målmånaden, utan utfallsdelen | 1 / 7 / 6 |
| `index.html` | sidan (kopia av `src/kpif_nowcast/templates/sverige_index.html`) | |
| `MANIFEST.json` | filnamn, dataset-id, titel och beskrivning för alla 14 filer | |

Sidan följer v1:s upplägg: en Claude Data-dashboardsida (`<meta name="dash-one-writer">`) som läser varje dataset
med `dash.data('<id>')` och ritar med d3 från plattformen. Den har inga relativa sökvägar och inga externa skript.
Varje JSON-fil laddas alltså upp som asset och registreras som `datasets/<id>`, där `<id>` är filnamnet utan `.json`.
Nya sektioner: Prognosen (skarp, band, alla prognoser med typ, förklaring, bidrag per komponent, J5-band,
champion/challenger), Prisleden (sex diagram och en tabell), Arbetsförmedlingen, Länen (rutnätskarta med val av mått
och av nivå eller förändring, plus tabell), AI-indikatorn (två diagram i AI-linsen). Ingressen nämner också den skarpa
prognosen. Område "prisled" ingår nu i värmekartan.

Andra ändringar i v1-datan:
- K0:s index och råvarupriser visas som årsförändring i `overview`/`series`. Tidigare visades de som nivå.
- Statsobligationsräntor och SWESTR har tecken −1 i trycket, som styrräntan.
- Den gamla J7-raden försökte bygga om indikatorn via JobTech och Eurostat och hämtade då från nätet om råcachen
  saknades. Raden är ersatt av `ai_indicator_rows`, som bara läser observationstabellen. Andelarna per år stämmer
  med `docs/ai-indikator.md` (maskininlärning 2016–2025: 3,3 / 7,0 / 13,0 / 22,5 / 19,0 / 18,0 / 13,0 / 15,6 /
  23,5 / 32,4). Uppdelningen per yrkesområde och produktiviteten per bransch finns bara i J7:s dokument.

### 2. Månadsbrev (`src/kpif_nowcast/manadsbrev.py`)
`python -m kpif_nowcast.manadsbrev 2026-11` (eller `python -m kpif_nowcast.pipeline manadsbrev [--month]`) skriver
`docs/manadsbrev/<månad>.md`. Brevet har huvudbudskap, prognosen (skarp, skuggor märkta, förklaring, bidrag,
osäkerhet, champion/challenger) och läget (inflation och prisled, arbetsmarknad, bostäder, län och AI). Därefter
kommer "vad har ändrats" mot förra månadens informationsdatum och sist källorna.
- **Informationsdatum** = tidigast av i dag och målmånadens deadline (dag 4 i nästa månad, till dagens slut).
  Observationstabellen klipps på `known_from`, prognosfilerna på `made_at`. Processad data klipps som i
  `tests/test_explain.py`: KPIF och komponenter t.o.m. månaden före, energipriser för månaden och Riksbanksbanor
  publicerade före deadline. Utfallsdelen av förklaringen används aldrig.
- Steg i `pipeline monthly` efter explain. Ett fel där stoppar inte skuggorna (`strict=False`). Månadsjobbet
  committar `docs/manadsbrev` (`.github/workflows/monthly-shadow.yml`).
- Brevet för november 2026 är genererat och committat: `docs/manadsbrev/2026-11.md`.

### 3. Tester (`tests/test_k5.py`, 6 tester)
- Dashboardens generering körs utan fel och alla 13 dataset plus `index.html` finns i MANIFEST och har rader. Varje
  nytt dataset-id läses av sidan.
- Varje par `data-source`/`data-field` och varje `<th data-field>` i `index.html` finns som kolumn i datasetet
  eller i calcen (`area_now`, `prisled_now`, `af_now`).
- Länsreglerna: inga `behind_national`-rader, varsel per län ≤ 2026-03, rutnätsposition finns.
- Skuggor och kandidat är märkta "urvalsevidens".
- Månadsbrevet för aktuell månad innehåller alla sektioner.
- **As-of:** brevet för 2026-06 är identiskt med och utan observationer kända efter 2026-07-04. Förklaringen använder
  KPIF t.o.m. 2026-05, och ingen period efter informationsdatumet förekommer.

## Kontroll av sidan (exakt vad som verifierats)
Jag serverade `outputs/` med `python -m http.server 8765 --bind 127.0.0.1` och öppnade
`outputs/sverige_preview/harness.html` i den inbyggda webbläsaren. Den filen är en lokal attrapp av plattformens
`dash`-API (data/calc/draw/colors) och laddar d3 7.9.0 från cdnjs, `../sverige/index.html` och
`../sverige/<id>.json`. Den finns bara för kontrollen och står inte i MANIFEST.
- Alla 55 `data-draw`-element fylldes, inga skriptfel, 19 SVG-diagram ritades. Tabellraderna: prognoser 7,
  komponenter 6, champion 5, prisled 24, län 22, alla serier 92.
- Sidtexten lästes och stämmer med JSON-filerna. Ingressen säger "prognosen för november 2026 är 2,1 %", skarp 2,09
  med 50 % 1,7–2,4 och 80 % 1,5–2,6, Riksbanken 1,73, förklaringens text, bidragen och J5-bandet.
- Länsväljaren provades för alla mått: AKU visar 19 län och "Saknas: Norrb, Gotl, Kalm". Varsel visar 2026-03 med
  noten om att AF slutat uppdatera. Även småhus och konkurser (nivå och förändring) provades.
- Skärmbilder i ljust läge på skrivbordsbredd och i mörkt läge på mobilbredd (375 px). Ingen horisontell scroll på
  sidan (tabellerna scrollar i sin ram). Prognosdiagrammets etiketter klipptes först på mobil och är åtgärdade.
- Inte verifierat: sidan i den riktiga Claude Data-dashboarden. Plattformens egna mark-kontroller (`check`/`runs`)
  körs först efter uppladdning.

## BLOCKED
- J7:s råcache (JobTech och Eurostat per bransch) finns inte i någon worktree. Ny hämtning är inte tilldelad K5,
  därför räknas indikatorn på observationstabellen. Uppdelningen per yrkesområde och produktiviteten per bransch
  saknas i dashboarden.
- Varsel per län efter 2026-03 (redan BLOCKED i K4).

## Vad lärde vi oss
- Dashboarden (v1 och v2) visar senaste versionen av varje serie utan klippning på known_from. Den kan alltså visa
  siffror som enligt katalogens publiceringsfördröjning ännu inte "är kända", till exempel företagens AI-användning
  2025. AI-indikatorn för 2025 blir därför 1,57 i dashboarden men 1,92 i brevet, som klipps per 2026-11-23 och
  saknar 2025 års enkät. Brevet är den strikta versionen. Ska dashboarden klippas på i dag krävs en rad i
  `main()` (`cut_table(table, today)`). Det har jag inte gjort, eftersom v1 medvetet visar senaste version.
- Det mesta av "läget" är beskrivande nivåer och förändringar. Brevet drar inga orsaksslutsatser. Det enda
  "bidrag" som nämns är modellens bokföring (K3), och det står så i texten.
- Varsel per län som enskild månad är mycket brusigt (Kronoberg +629 % på ett år). Kartans förändringsläge för
  varsel säger lite. Ett tremånaders- eller tolvmånadersmedel per län vore bättre, men det kräver en ändring i K4:s
  `latest_by_county`.
