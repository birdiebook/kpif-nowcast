# Autonom körning 2: Sverige på djupet

Skriven 2026-11-23. Körning 1 (J1–J7) var klar på 30 minuter, eftersom jobben var skrivna i
människotempo och tog slut när variant-taket nåddes. Körning 2 är dimensionerad för att fylla
tiden: sex spår och en prioriterad backlog som körs tills den är tom eller Johannes skriver STOP.

**Fokus är Sverige.** Andra länder ingår bara om datan går att få utan krångel (se K6).

## Vad som gäller från körning 1

Allt i [autonom-korning.md](autonom-korning.md) gäller oförändrat, utom det som står nedan:
miljö och worktrees (nu `C:\dev\kpif-auto2\<spår>`), dataregler, informationsmängd och pytest per
modell, förregistrering, Holm-justering, ordvalet "klarade urvalsskärmen", status på `auto/status`,
förbjudna åtgärder. Statusfilen blir `docs/auto2/STATUS.md` och briefen `docs/auto2/BRIEF.md`.

**Ändringar:**
- **Ingen hård deadline.** Stopp när backloggen är tom, när Johannes skriver STOP i statusfilen
  eller när två väckningar i rad inte gett framsteg (STALLED).
- **Varianttak för modeller:** 30 nya varianter i körningen (projektet har förbrukat 23).
  Datahämtning, drift, dashboard och dokumentation har inget tak.
- **Högst 3 spår samtidigt.**
- **Ett spår som blir klart lämnar sin plats till nästa post i backloggen**, inte till STOP.
- **Datatillgång:** om en källa kräver konto, betalning, inloggning eller skrapning mot villkoren
  markeras den BLOCKED (orsak i STATUS) och spåret går vidare. Lägg ingen tid på att forcera.

## Förutsättningar (Johannes)

1. J2 och J1 ligger på main (klart 2026-11-23). J3–J7 mergas före start, eller så förgrenas K4
   från `auto/j6-af` + `auto/j7-ai` och K3 från `auto/j5-osakerhet` (skriv bas-SHA i rapporten).
2. Omstartsuppgiften `kpif-auto2-restart` skapas med **auto-läge påslaget**. Testa en riktig
   väckning innan körningen lämnas. Om den fastnar på en behörighetsfråga slår Johannes på
   auto-läge för uppgiften i appen; annars körs utan omstart.
3. Keep-awake, nätström, inget viloläge (som körning 1).

## Spåren

### K1. Drift: skuggprognoserna går själva (fas 6, del 1)
**Varför:** urvalsevidens blir riktig evidens först när modellerna prognostiserar månader de
aldrig sett. Det ska ske utan Johannes dator.
- GitHub Actions: veckohämtning (söndag) och prognoskörning (dag 1–4) för `comp_fuel` (skarp),
  J2 V2, 50/50-snittet och K2:s eventuella kandidat. Skuggprognoser skrivs till
  `forecasts/shadow/<modell>/<månad>.json`; den skarpa `forecasts/<månad>.json` rörs inte.
- Data lagras i Actions-cache/artifacts (inget nytt konto). Objektlagring är ett senare beslut.
- DuckDB-vy över `observations.parquet` och enkla datatester (unika nycklar, inga hål,
  `known_from` ≥ periodens slut). dbt bara om det blir enklare än Python-testerna.
- Champion/challenger-tabell i `forecasts/SCORECARD.md`: alla modeller, samma månader.
- Workflow-filer pushas på grenen. **Aktivering (merge) beslutar Johannes.**
**Klart:** en lokal körning av workflow-stegen (`act` eller motsvarande skript) går grönt och
skuggprognosen för 2026-11 är reproducerbar från ren checkout.

### K2. ML-spåret: kan en riktig ML-modell slå 50/50-snittet?
**Varför:** lärandet. Johannes vill förstå modern prediktiv modellering, och det ärliga svaret
på "hjälper ML här?" är värt mycket även om det är nej.
- Kandidater: ridge/lasso på komponentmodellens features plus katalogserierna, och gradient
  boosting (scikit-learn `HistGradientBoostingRegressor`) på samma features.
- **Nästlad validering:** hyperparametrar väljs inom varje expanderande fönster (inre
  tidsserie-CV), så att 2015–26 bara används en gång för utvärdering.
- Mål: residualen mot `rb_updated` respektive mot J2 V2, inte KPIF direkt.
- Förklara modellen: feature-vikter per år (ridge) och permutationsvikt (boosting), i klartext.
- Högst 10 varianter. Jämför mot `rb_updated`, J2 V2 och 50/50.
**Klart:** resultattabell med MAE, DM-p (rå och Holm) och en kort text "vad lärde vi oss".

### K3. Förklarade prognoser
**Varför:** en prognos man inte kan förklara går inte att lita på eller lära sig av.
- `explain.py`: för varje prognosmånad, bidrag per komponent och vad som ändrats sedan förra
  prognosen (nyhetsdekomposition: el, drivmedel, säsong, senaste miss).
- Efter utfall: felet uppdelat per komponent. Historik 2015–26 som tabell.
- J5:s EWMA-band används i förklaringen (förslag, `forecast.py` rörs inte).
**Klart:** förklaring för de senaste 24 månaderna och för 2026-11, som JSON och markdown.

### K4. Regionala Sverige
**Varför:** läget i Sverige är inte ett tal. Regionala skillnader i arbetslöshet, bostadspriser
och konkurser gör dashboarden mer levande.
- Länsserier från SCB och Arbetsförmedlingen: arbetslöshet/inskrivna, varsel, bostadspriser,
  konkurser, befolkning. Egen katalogmodul `catalog_region.py`.
- Bara deskriptivt. Inga prognostester utan förregistrering.
**Klart:** serierna i observationstabellen, kvalitetskontroll grön, dokumenterade i datakatalogen.

### K5. Sverigeläget v2
- Nya sektioner: regional karta (K4), Arbetsförmedlingen (J6), AI-indikatorn (J7),
  skuggprognoserna och förklaringen (K1, K3).
- Ladda upp till dashboarden i Claude Data (länk i `CLAUDE.local.md`). Kontrollera sidan.
- Generera månadsbrev `docs/manadsbrev/2026-11.md` från datan: läget, prognosen, vad som
  ändrats. Ett skript, så att det går att upprepa varje månad.
**Klart:** dashboarden visar de nya sektionerna och månadsbrevet är genererat av skript.

### K6. Bara om det är lätt
Var och en tidsboxas till ett försök. Fungerar det inte: en rad i STATUS och vidare.
- Historiska vintages för reviderade svenska serier (Riksbankens och KI:s arkiv). Om det går:
  testa om J4:s D2 håller utan revisionsläckage.
- Nordiska grannländers HICP via Eurostat (redan i katalogen) som extra test av J2:s elmetod.

## Backlog (körs i ordning när ett spår blir ledigt)

1. K1, K2, K3 startar direkt.
2. K4 när en plats blir ledig, sedan K5 (behöver K1, K3, K4).
3. K6.
4. Veckohämtningen (`observations`, `features`, `sverige_dashboard`) som sista steg, så att
   dashboarden är färsk när Johannes läser.
5. Slutrapport överst i STATUS, sedan STOP.

## Slutrapport

Per spår: vad som byggdes, resultat (modeller märkta som urvalsevidens med global varianttotal),
vad som blev BLOCKED och varför, och länk till jämförelsen mot main. Rekommenderad mergeordning.
