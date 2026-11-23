ultracode.

Kör autonom körning 3 i C:\dev\kpif-nowcast (GitHub birdiebook/kpif-nowcast): mer svensk data där överraskningarna sitter, sedan en gemensam utvärdering.

## Läs först
CLAUDE.md (särskilt "Agentiskt arbete" och "Storleksbedömning"), docs/vision.md, docs/autonom-korning-2.md (dess regler gäller utom där denna prompt säger annat), docs/agentkalibrering.md, de sista posterna i docs/beslutslogg.md och slutrapporten i docs/auto2/STATUS.md på grenen auto/status.
Kontrollera först att körning 2 har STOP i sin STATUS. Står det inte där: avsluta och säg till.

## Upplägg
- Status i docs/auto3/STATUS.md på auto/status. Spara denna prompt ordagrant som docs/auto3/BRIEF.md.
- Worktrees under C:\dev\kpif-auto3\<spår>, grenar auto3/<spår>.
- Klara spår mergas till main av orkestreraren när pytest är grönt (enligt CLAUDE.md).
- Skyddat som förut: forecast.py, forecasts/ (den skarpa prognosen), byte av huvudmodell, schemalagda uppgifter (rör inte kpif-final-forecast-2026-11).
- Logga tid, anrop och tokens per spår i STATUS (kalibreringen).
- Fokus Sverige. Källor som kräver konto, betalning, inloggning, PDF-tolkning i stor skala eller skrapning mot villkoren: BLOCKED med orsak, sedan vidare.
- Ingen omstartsuppgift. Den har inte fungerat. Orkestrera från sessionen.

## Våg 1: datainsamling, alla spår parallellt
Källås per källa (Riksbanken: L4 och L6, SCB: L5 och L7 turas om).
- L1 Kalender för administrerade priser: moms, punktskatter, kollektivtrafikkort, elnätsavgifter, sophämtning, vatten, tandvård och liknande, från 2015. En rad per händelse: datum, KPIF-post, uppskattad effekt i procentenheter och källa (länk). Bygg på K13:s skatterensning. Ingen statistisk test: kalendern är mekanisk och blir ett förslag till manuell justering i månadsrutinen (`--adjust` med källa i noten). Användningen beslutar Johannes.
- L2 Resor (77 % av tjänstefelet): Tillväxtverkets gästnätter (ersätter SCB-tabellen som slutar 2021), påskens placering som feature, Kammarkollegiets resegarantistatistik om den finns som tabell.
- L3 Hyresförhandlingar: årliga utfall från Hyresgästföreningen och Fastighetsägarna som liten tabell, med källa per år.
- L4 Prospera (Riksbanken): marknadens inflationsförväntningar, om Excel-filerna går att läsa stabilt.
- L5 El: andel rörliga elavtal (SCB TAB3571) och elnätsavgifter (SCB och Energimarknadsinspektionen), för januarieffekten.
- L6 Kronan: EUR/SEK och USD/SEK var för sig (Riksbanken SWEA).
- L7 Snabb-KPI mot slutligt utfall som egen serie (SCB).
Varje serie: egen katalogmodul, publiceringsfördröjning med källa i publiceringskalendern, revised-flagga, datatester gröna, dokumenterad i datakatalogen.

## Våg 2: gemensam utvärdering, efter att våg 1 är klar
- En förregistrerad screening av alla nya serier från L2–L7 tillsammans, som korrektion på bästa skuggmodell (K2:s ridge) och på 50/50. BH-kontroll. Screeningen räknas inte mot varianttaket.
- Högst tre serier testas ihop, en gång. Varianttak för körningen: 6. Ange projektets totala varianttal bredvid varje p-värde. SPA-test över alla projektets varianter, som K12.
- Skriv "klarade urvalsskärmen", aldrig "slår". En modell som klarar skärmen fryses som skuggprognos.

## Våg 3: avslut
Uppdatera Sverigeläget (Claude Data, länk i CLAUDE.local.md) och Pages-dashboarden med de nya serierna och kalendern. Kör veckohämtningen sist. Skriv slutrapporten överst i STATUS: per spår vad som byggdes, vad som blev BLOCKED och varför, och utvärderingen märkt som urvalsevidens. Skriv sedan STOP.

Ge mig statuslänken https://github.com/birdiebook/kpif-nowcast/blob/auto/status/docs/auto3/STATUS.md vid start.
