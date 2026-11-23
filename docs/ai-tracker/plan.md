# AI-tracker – plan för ett nytt publikt repo

Skriven 2026-11-23. Planen ligger tillfälligt i kpif-nowcast och flyttas till det nya repots `docs/`
när det skapas. Arbetsnamn: **`ai-rollout-tracker`** (kod på engelska, dokumentation på svenska).

## 1. Vision

> **Följ AI-utrullningen i världen kvantitativt, neutralt och öppet, och se när utvecklingen ändrar takt.**

Projektet följer om AI-utvecklingen accelererar, håller takten eller bromsar in, gren för gren. Det ska
synas tidigt när något fundamentalt ändras, i båda riktningarna. Det tar inte ställning för en tes.
Alla mått registreras i förväg, och en ögonblicksbild committas varje månad. Tidsstämpeln i git är
beviset för hur bilden såg ut vid varje tidpunkt.

Projektet är fristående från placeringar. Den som vill koppla det till en portfölj gör det i ett
privat lager som läser de publika utfallen (se avsnitt 9).

## 2. Principer

1. **Neutral spårning, inga larm.** Varje gren beskrivs med ett tillstånd: accelererar, stabil eller bromsar
   in. En förstärkning är lika mycket en signal som en försvagning.
2. **Takt och förändring i takt före nivå.** Skiften syns först i accelerationen.
3. **Förregistrerade mått.** Vilka serier som följs, hur takten beräknas och hur tillståndet klassas
   låses i `docs/mattregister.md` innan data analyseras. Ändringar loggas med motivering och datum.
   Det skyddar mot att man i efterhand väljer de serier som passar.
4. **Ingen läcka.** Varje värde lagras med `known_from`: inlämningsdatum för SEC-dokument, publiceringsdatum
   för månadsdata och datum för transkript. Revideringar sparas som nya versioner. Allt kan spelas upp
   `as_of()` ett visst datum.
5. **Baslinjer.** Varje nowcast jämförs mot en naiv baslinje och mot bolagens egen guidance där den finns.
   Guidance fyller samma roll som Riksbankens prognos i kpif-nowcast.
6. **Ärlighet om osäkerhet.** Kvartalsserier är korta och har ofta regimbrott efter 2023. Den statistiska
   budgeten är mindre än för KPIF. Det mesta i projektet är därför strukturerad övervakning och
   bara en mindre del prognos.
7. **Metoden följer målet.** Ramverket från kpif-nowcast återanvänds där det passar och byts ut där
   något annat fungerar bättre.

## 3. Grenar (vad som spåras)

| # | Gren | Fråga | Exempel på mått |
|---|---|---|---|
| G1 | Förmåga | Ökar förmågan i samma takt? | Fördubblingstid för METR time horizon, frontier-benchmarks (Epoch), träningsberäkning |
| G2 | Kostnad | Hur snabbt faller priset per förmåga? | Pris per token vid given förmågenivå, halveringstid |
| G3 | Användning | Hur brett och djupt används AI? | Andel företag som använder AI (Census BTOS, Eurostat, SCB), tokenvolymer, nedladdningar |
| G4 | Intäkter | Går det att tjäna pengar på det? | Molntillväxt, Nvidias datacenterintäkter, rapporterade AI-intäkter, AI-intäkter i förhållande till capex |
| G5 | Investeringar och finansiering | Hur stor är capex, och hur finansieras den? | Capex för de fyra största hyperscalers, capex/OCF, skuldemissioner |
| G6 | Utbud och halvledare | Hur går leveranskedjan? | TSMC:s månadsintäkt, Koreas halvledarexport, taiwanesiska exportordrar, GPU-hyrpriser |
| G7 | Fysiska flaskhalsar | Räcker kraft och nät? | Elförbrukning i datacenter, köer för nätanslutning, elpriser |
| G8 | Arbete och produktivitet | Syns effekter i ekonomin? | Arbetsproduktivitet, AI i platsannonser, sysselsättning i exponerade yrken |
| G9 | Forskning och öppen ekosystem | Hur snabbt rör sig fältet? | arXiv-inlämningar, öppna modeller, nedladdningar från Hugging Face |

G8 är den svagaste grenen statistiskt: effekterna är långsamma och svåra att skilja från konjunkturen.
Den följs ändå, och det sägs rakt ut.

## 4. Mått per gren

Varje gren har fyra mått per serie:

1. **Nivå**
2. **Takt**: årlig tillväxt, eller fördubblings- och halveringstid för G1 och G2.
3. **Förändring i takt** (acceleration).
4. **Överraskning**: utfall minus guidance eller vår egen nowcast, där sådan finns.

Måtten visas mot seriens egen historik som percentil eller z-värde. Per gren beräknas sedan:

- **Diffusionsindex**: andelen av grenens serier som accelererar (som i PMI). Det är enkelt att granska och
  symmetriskt.
- **Strukturbrott i takten**: changepoint-detektion som anger när trendtillväxten skiftade, åt vilket håll
  och med vilken säkerhet. Metoden väljs och förregistreras i fas 5.

Tillståndet per gren (accelererar, stabil eller bromsar in) följer en förregistrerad regel ovanpå de två
måtten. Regeln bestäms innan data analyseras.

## 5. Nowcastmål (det som får en scorecard)

| Mål | Frekvens | Ledande data | Baslinjer |
|---|---|---|---|
| **N1: capex för de fyra största hyperscalers** (MSFT, GOOGL, AMZN, META) | kvartal | TSMC:s månadsintäkt, Koreas export, taiwanesiska exportordrar, tidigare guidance | naiv (förra kvartalet, trend) och bolagens guidance |
| **N2: TSMC:s månadsintäkt** | månad (~10:e) | Koreas export (20-dagarsdata ~21:a), taiwanesiska exportordrar | naiv och kvartalsguidance utslagen per månad |
| N3: Nvidias datacenterintäkter | kvartal | N1, N2 | bolagets intäktsguidance |
| N4: Census BTOS, andel AI-användande företag | varannan vecka | trend, G3-serier | slumpvandring |

N1 är förstahandsvalet. Det är det viktigaste enskilda måttet för G5, SEC XBRL ger strukturerad historik
gratis, och baslinjen (guidance) är tydlig. Prognoserna committas före rapportdatum och skrivs aldrig om,
precis som `forecasts/<månad>.json` i kpif-nowcast. Läckagerisk: capex i XBRL avser kvartalets *utbetalningar
för anläggningstillgångar* (exklusive finansiell leasing). Måttdefinitionen måste låsas per bolag, eftersom
bolagen redovisar olika.

## 6. Datakällor (första utkast, licenser inte verifierade)

Varje källas villkor kontrolleras i fas 1 innan något publiceras. Ingen rådata committas. Från rapporter
och transkript publiceras bara extraherade siffror med källhänvisning, aldrig själva texten.

| Gren | Källa | Frekvens | Format | Att kontrollera |
|---|---|---|---|---|
| G1 | Epoch AI data hub | löpande | CSV | licens (troligen CC-BY) |
| G1 | METR time horizon | ojämnt | publicerade data | format, uppdateringstakt |
| G1, G2 | Artificial Analysis | löpande | webb/API | villkor för vidarepublicering |
| G2, G3 | OpenRouter rankings (tokenvolymer per modell) | vecka | webb | villkor, urvalsbias (bara OpenRouter-trafik) |
| G3 | US Census BTOS (AI-frågan) | varannan vecka | CSV | public domain |
| G3 | Eurostat `isoc_eb_ai`, SCB | år | API | öppna |
| G3 | Anthropic Economic Index | ojämnt | datasets | licens, urval |
| G3, G9 | Hugging Face Hub (nedladdningar) | löpande | API | villkor |
| G4, G5 | SEC EDGAR XBRL (companyfacts) | kvartal | JSON API | gratis, kräver User-Agent med kontakt (generisk) |
| G4, G5 | Kvartalsrapporter och transkript | kvartal | PDF/HTML | upphovsrätt: bara extraherade siffror |
| G6 | TSMC IR, månadsintäkt | månad | HTML | öppen |
| G6 | Koreas tullverk, export (10-, 20-dagars, månad) | 10 dagar | webb | format, åtkomst |
| G6 | Taiwans finansdepartement, exportordrar | månad | webb | format |
| G6 | GPU-hyrpriser | löpande | webb/API | ingen etablerad källa: eget forskningsspår |
| G7 | EIA (el), LBNL (anslutningsköer) | månad/år | API/PDF | öppna |
| G8 | FRED (BLS-produktivitet, BEA-investeringar) | kvartal | API | öppen |
| G8 | Indeed Hiring Lab (AI i annonser) | månad | GitHub CSV | licens |
| G8 | JobTech (Sverige), återanvänd från kpif-nowcast J7 | löpande | API | CC0 |
| G9 | arXiv (cs.AI, cs.LG, cs.CL) | månad | API | metadata CC0 |

Betalkällor (konsensus, Similarweb, Sensor Tower, Bloomberg) markeras BLOCKED. Kärnan byggs utan dem.

## 7. Arkitektur (återanvänt från kpif-nowcast)

| kpif-nowcast | ai-rollout-tracker |
|---|---|
| `catalog.py` med en `Spec` per serie | samma mönster, en `Spec` per serie och gren |
| `observations.py` med `known_from` och `as_of()` | samma, plus versioner per revidering från start (det som saknas i kpif-nowcast fas 6) |
| `publication.py` | rapportkalender: kvartalsrapporter, TSMC, Korea, BTOS |
| `forecasts/<månad>.json`, `SCORECARD.md`, champion/challenger | samma för N1–N4 |
| `manadsbrev` | månatlig ögonblicksbild `snapshots/<månad>.json` + kort brev |
| `warehouse.py` (DuckDB-datatester) | samma |
| Actions: veckohämtning, månadskörning, Pages | samma |
| – | nytt: `extract/` för LLM-extraktion ur rapporter och transkript |

**Ramverket kopieras, det paketeras inte.** Ett gemensamt bibliotek ger beroenden mellan repona innan det är
klart vad som faktiskt är gemensamt. Om båda projekten lever vidare bryts det ut senare.

**LLM-extraktion** (guidance, AI-intäkter, capex-kommentarer): varje värde sparas med dokument, sida eller
tidsstämpel och ett ordagrant citat. Ett granskningsspår kontrollerar ett slumpmässigt urval mot källan
innan extraktionen används i något mått. Felfrekvensen redovisas.

## 8. Faser

| Fas | Innehåll | Leverans | Storlek |
|---|---|---|---|
| 0 | Repo, CLAUDE.md, struktur och CI kopierade från kpif-nowcast | grönt pytest, Actions | 1 spår |
| 1 | Kartlägg källor och licenser | `docs/datakallor.md`, BLOCKED-lista | 3 spår parallellt (per gren-grupp) |
| 2 | Måttregister och första katalogen (~20 kärnserier, minst en per gren) | `docs/mattregister.md`, `catalog.py`, observationer med `known_from` | 4–5 spår + 1 läckagegranskning |
| 3 | N1 och N2: backtest med rolling origin mot naiv baslinje och guidance | backtest, scorecard, första skarpa prognos | 2 spår + 1 granskning |
| 4 | LLM-extraktion av guidance och AI-intäkter ur rapporter | `extract/`, urvalsgranskning med felfrekvens | 2 spår + 1 granskning |
| 5 | Diffusionsindex, strukturbrott, tillståndsregel (förregistrerad) | månatlig ögonblicksbild v1 | 2 spår + 1 granskning |
| 6 | Dashboard på Pages, månadsbrev | publik sida | 1–2 spår |
| 7 | Bredd: G7, G8, Europa och Sverige (koppling till kpif-nowcasts AI-indikator), GPU-hyrpriser | fler serier | 4+ spår |

Fas 0–3 ryms i en körning (cirka 15 spår inklusive granskning, enligt `docs/agentkalibrering.md`).
Fas 4–6 i nästa. Flaskhalsarna är licenskontroll, åtkomst till källor och kalendertiden: N1 får ett skarpt
utfall per kvartal, N2 ett per månad.

## 9. Det privata lagret

Kopplingen till placeringar hålls helt utanför det publika repot, i `CLAUDE.local.md` eller ett litet privat
repo. Det lagret läser publika ögonblicksbilder och scorecard, viktar grenarna efter exponering och skriver
aldrig tillbaka. Det publika repot innehåller inga personliga uppgifter och inga innehav.

## 10. Beslut för Johannes

| Beslut | Rekommendation |
|---|---|
| Repots namn | `ai-rollout-tracker` |
| Första nowcastmål | N1 (capex för de fyra största hyperscalers), N2 parallellt eftersom den ger månatliga utfall |
| Ramverk | kopiera nu, bryt ut gemensamt bibliotek senare vid behov |
| Kodlicens | MIT för koden. Data omfattas av källornas egna villkor |
| Start | skapa det tomma publika repot och lägg till det i sessionen. Sedan körs fas 0–3 |
