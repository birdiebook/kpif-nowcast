# K10 Sverigeläget på GitHub Pages (fas 6): resultat

Skriven 2026-11-23. Inga modellvarianter (0 förbrukade). Inget publicerat ännu: Pages måste slås på en gång i
repots inställningar (se sist).

## Vad som byggdes

Samma sida som i Claude Data (`src/kpif_nowcast/templates/sverige_index.html`) körs nu också som en fristående statisk
sida. Den byggs av Actions efter varje hämtning, så Sverigeläget blir aktuellt utan manuell uppladdning.

| Fil | Vad |
|---|---|
| `src/kpif_nowcast/templates/dash-shim.js` | Ersätter Claude Data-API:t `dash` med bara de delar sidan använder: `dash.data(id)` (läser `data/<id>.json` med fetch och ger `{status: loading/ok/error, data}`), `dash.calc(id, {inputs, fn})` (räknas om när indata kommit, fel sprids), `dash.draw(name, fn)` (ritar alla `[data-draw=name]`; `dash.draw(name)` ritar om direkt, vilket länsväljarna använder) och `dash.colors` (CSS-variabler, så färgerna följer ljust/mörkt läge). Allt ritas om när ett dataset kommer och när fönstrets bredd ändras. `dash.params`, `setParams` och `onData` används inte av sidan och finns inte med. |
| `src/kpif_nowcast/templates/site_shell.html` | HTML-skal: designvariablerna som Claude Data annars ger (`--color-*`, `--cds-*`, typsnitt) för ljust och mörkt läge (`prefers-color-scheme`, kan tvingas med `data-theme`), d3 7.9.0 från cdnjs med exakt version och SRI, shimmen och sidfot med byggtid och länk till repot. |
| `src/kpif_nowcast/pages.py` | `page_datasets()` läser ut vilka dataset sidan läser (alla mönster: `dash.data`, `rows`, `failed`, `src:`, calc-`inputs`, `data-source`), minus calcs. `build_site()` skriver `site/`: `index.html`, `dash-shim.js`, `.nojekyll`, `data/<id>.json` och `data/build.json` (byggtid, skrivna och saknade dataset). Den inbäddade källkoden i JSON-filernas meta tas bort (meta länkar redan till repot), vilket minskar varje fil med ~32 kB. |
| `pipeline.py` | `python -m kpif_nowcast.pipeline site [--offline]`: kör `sverige_dashboard` (till `outputs/sverige/`) och bygger `site/`. |
| `.github/workflows/pages.yml` | Triggas av `workflow_run` (avslutad och lyckad) på "Weekly data fetch" och "Monthly shadow forecasts", samt `workflow_dispatch`. Återställer samma Actions-cache (`kpif-data-`) som weekly-fetch sparar (bara restore), bygger offline, `actions/upload-pages-artifact@v3` och `actions/deploy-pages@v4`. Behörigheter `contents: read`, `pages: write`, `id-token: write`. Inga hemligheter, ingen push. |
| `.gitignore` | `site/` (byggs i CI). |
| `tests/test_k10_pages.py` | 5 tester, se nedan. |

Ändringar i sidan (gäller även Claude Data-versionen):
- Värmekartan använder korta områdesnamn (texten före ":") när namnen tar mer än 38 % av bredden. På mobil tog
  "Prisleden: producent-, import- och planerade priser" annars ~300 av 313 px och själva kartan försvann.
- `min-width: 0` på raderna i områdeskorten, så att långa serienamn kortas med "…" i stället för att trycka ut kortet.

Månadsjobbet ingår som trigger eftersom det committar nya skuggprognoser; då uppdateras prognosdelen samma dag.

## Verifierat

Lokalt (`python -m kpif_nowcast.pipeline site --offline`, 129 s, med data/ i worktree):
- Alla 13 dataset som sidan läser skrevs (`af, ai, ai_indicator, champion, explain_components, explain_summary,
  explain_text, forecast, overview, pressure, prisled, region, series`), inga saknade, inga misslyckade sektioner.
  `site/` är ~2,1 MB (series 1,06 MB, prisled 0,59 MB).
- Serverat med `python -m http.server` och öppnat i den inbyggda webbläsaren (Chromium):
  - d3 7.9.0 laddades från cdnjs (med SRI). Alla 13 dataset och de tre calcs (`area_now`, `prisled_now`, `af_now`)
    har status ok. Alla 55 `data-draw`-element ritades: inget "—" och inget "kunde inte laddas". Sidan hade 19 svg
    och tabellerna 9 / 7 / 24 / 22 / 92 rader. Ingressen fylldes ("…KPIF låg på 1,1 % i okt 2026. Den skarpa
    prognosen för november 2026 är 2,1 %."). Inga konsolfel och inga 4xx.
  - 1280×900 i ljust läge (skärmbild) och 375×812 (mobil) i mörkt läge (skärmbild). Mörkt läge: bakgrund, paneler,
    linjefärg och axeltext byter värden. På mobil ingen horisontell scroll (scrollWidth = 375).
  - Interaktion: byte av mått i länsväljaren ritar om länstexten. Byte av serie i utforskaren ritar om diagrammet.
  - Felväg: ett dataset som saknas ger status error, och det gör även en calc som bygger på det.
- Inte verifierat: att workflowet går i Actions. Det kan bara köras efter merge till main och efter att Pages slagits
  på. `configure-pages` stoppar med ett tydligt fel om Pages är avstängt. Inte heller testat: Safari/Firefox, eller
  hur sidan beter sig när cachen är kall (då stoppar jobbet med "run 'Weekly data fetch' first").
- Kvar, kosmetiskt: på mobil klipps slutetiketten i tre små diagram ("Euroområdet 0,6", "Maskininlärning 27,3",
  "Programvara 10,5") några pixlar i högerkanten av svg:n. Siffrorna går att läsa i tooltipen.

Pytest: `tests/test_k10_pages.py` (5 tester):
1. Dataseten sidan läser = `sverige_dashboard.DATASETS`, och calcs = de tre kända.
2. Parsern hittar alla mönster sidan använder för att namnge ett dataset.
3. `build_site` från falska JSON-filer: alla dataset skrivs utan kodmeta, skalet har doctype och viewport, d3 med exakt
   version laddas före shimmen och shimmen före sidans skript, inga platshållare är kvar, mörkt läge finns och ett
   saknat dataset listas utan att bygget fallerar.
4. Shimmen exporterar varje `dash.*` som sidan använder.
5. (kräver data) Hela bygget skriver varje dataset som sidan läser, med rader.

## BLOCKED
Inget.

## Publicitet och data
Sajten är publik. Den innehåller bara de aggregerade dataseten som Sverigeläget redan visar: officiell statistik och
öppna marknadsserier, projektets prognoser och metod. Inga personuppgifter och inga hemligheter. Licensvillkoren för
att publicera de härledda serierna är inte kontrollerade per källa i det här spåret, se öppna frågor.

## Vad lärde vi oss
- Sidan var redan nästan fristående: den använder bara fyra delar av `dash`. Därför räcker en shim på ~80 rader, och
  Claude Data och Pages kan dela exakt samma HTML. Ändras sidan, ändras båda.
- `requestAnimationFrame` körs aldrig i en bakgrundsflik. Första versionen av shimmen ritade därför ingenting när
  fliken var dold, trots att all data hade laddats. Omritningen schemaläggs nu med `setTimeout`.
- Mobilbredden visade ett fel som också finns i Claude Data: det långa områdesnamnet åt upp värmekartan.

## Johannes behöver göra (en gång)
1. Repot på GitHub → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Efter merge: Actions → "Pages (Sverigeläget)" → Run workflow, eller vänta på söndagens veckohämtning.
   Adressen blir `https://birdiebook.github.io/kpif-nowcast/`.
