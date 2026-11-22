# Beslutslogg

Varje viktigt val, med mina egna ord. Kan jag inte förklara det här har jag
hittat min nästa lärfråga.

Mall:

```
## ÅÅÅÅ-MM-DD – Beslut
**Vad:** …
**Varför:** …
**Alternativ jag valde bort:** …
**Min gissning innan / vad som faktiskt hände:** …
**Öppna frågor:** …
```

---

## 2026-11-22 – Projektets ramar
**Vad:** Nowcasta KPIF, alltså nästa månads siffra innan SCB publicerar den.
**Varför:** Avgränsat, öppen data, och ett facit varje månad att lära mig av.
Makro på lång sikt har för få observationer och för många regimskiften för en start.
**Alternativ jag valde bort:** Valanalys (möjligt projekt 2), AI-produktivitet (inget facit än),
Polymarket (blir en sidovana för att träna kalibrering).
**Öppna frågor:** Hur nära Riksbanken kan en enkel modell komma?

## 2026-11-22 – Prognosen låses före snabb-KPI
**Vad:** Prognosen för månad t låses senast den 4:e i månad t+1, före SCB:s snabb-KPI.
**Varför:** Snabb-KPI (sedan okt 2024) ligger ~0,01 procentenheter från slutlig siffra.
Efter den finns inget kvar att förutse.
**Konsekvens:** Vid prognostillfället är senaste kända KPIF månad t-1.

## 2026-11-22 – Fas 2: baslinjer och mått
**Vad:** Alla modeller förutser månadsförändringen för t och räknas om till årstakt
via kända index för t-1 och t-12. Utvärdering mot SCB:s officiella årstakt (en decimal).
Mått: MAE i procentenheter (huvudmått), RMSE, och andel exakta träffar efter avrundning.
Riksbanken: senaste prognosomgång publicerad före deadline, där t fortfarande är prognos.
**Resultat 2015–2026 (141 mån), MAE:** Riksbanken 0,32 · säsong+trend 0,34 · naiv 0,38.
**Lärdomar:**
- "Samma månadsförändring som i fjol" är matematiskt identisk med "samma årstakt som förra månaden".
- Säsongsmodellerna är bäst över lång tid men sämst 2024–2026 (MAE 0,45 mot Riksbankens 0,33).
- Skillnaden mot Riksbanken (0,015) är för liten för att skilja från slump på 141 månader.
- Riksbankens prognos är oftast 1–3 månader gammal vid vår deadline.
**Öppna frågor:** Varför tappar säsongsmodellerna 2024–2026? Kandidater: elprisets
svängningar, COICOP 2018-bytet, ändrade säsongsmönster.

## 2026-11-22 – Fas 3: energipriser
**Vad:** Säsong+trend-baslinjen plus en korrigering för månadens energiprisrörelser:
drivmedel (Brent i SEK, dag 1–25, log-förändring) och el (spotpris SE3/SE4 viktat 70/30,
förändring i kr/kWh). Linjär regression utan intercept, expanderande fönster.
Elpriser bara från 2021-11 (elprisetjustnu.se) i väntan på ENTSO-E-nyckel.
**Resultat, MAE:**
- 2015–2026: drivmedelsmodell 0,316 · Riksbanken 0,320 · baslinje 0,335 (skillnaden mot Riksbanken är brus).
- 2024–2026 (34 mån): Riksbanken 0,33 · drivmedel+el 0,40 · naiv 0,40 · baslinje 0,45.
**Koefficienter (rimliga):** +10 % oljepris i kronor → ca +0,1 pe på KPIF samma månad.
+1 kr/kWh i spotpris → ca +0,8 pe.
**Lärdomar:**
- Energipriser förbättrar baslinjen tydligt 2024–2026 (0,45 → 0,40) men räcker inte för att nå Riksbanken.
- De största missarna är januari och mars–april (2026-03: +1,4 pe, 2025-01: −1,2 pe).
  Hypotes: engångshändelser som skatte- och momsändringar och årliga vikt-/avgiftsbyten.
  Sådant vet Riksbanken i förväg men syns inte i prisdata. Ej verifierat.
- Viktningen 70/30 mellan SE3 och SE4 är ett antagande.
**Nästa:** dela upp KPIF i komponenter (fas 4) för att se exakt vad som missas de månaderna.

## 2026-11-22 – Fas 4: komponentmodell
**Vad:** Prognos per analysgrupp i SCB:s TAB6628 (tjänster, varor, livsmedel, energi,
kapitalstock), på varje grupps *bidrag* till KPIF:s månadsförändring. Bidragen summerar
till KPIF m/m (avvikelse ~0,03 pe från avrundning). Energi får regressionskorrigering
(drivmedel + el), övriga grupper säsong+trend.
**Varför bidrag och inte index + vikter:** att kedja ihop gruppindex med SCB:s vikter
reproducerade inte KPIF tillräckligt exakt (indexfel 0,13 i snitt). Bidragen gör det.
**Resultat, MAE 2024–2026:** Riksbanken 0,33 · komponentmodell 0,375 · fas 3 0,395 · baslinje 0,45.
2015–2026 (bara drivmedel): komponentmodell 0,316 ≈ fas 3 0,316 ≈ Riksbanken 0,320.
**Var felet sitter 2024–2026 (MAE i pe av KPIF m/m):** energi 0,24 (från 0,35),
tjänster 0,19, varor 0,10, livsmedel 0,09, kapitalstock 0,01.
**Lärdomar:**
- Energi var största felkällan, och elpriset tar bort en tredjedel av energifelet.
- Januari är svårast: energin stiger mer än modellen tror (nätavgifter, skatter, vinterpris).
- April 2026: livsmedel föll kraftigt, troligen sänkt matmoms. Ej verifierat i källa.
- Tjänster är nu näst största felkällan, och där har vi ingen förklarande variabel än.
**Nästa kandidater:** (1) kalender över kända skatte-/avgiftsändringar, (2) Konjunkturinstitutets
prisplaner för tjänster och livsmedel, (3) längre elhistorik via ENTSO-E, (4) andel rörliga elavtal.

## 2026-11-22 – Fas 4b: Konjunkturinstitutets prisplaner – ingen effekt
**Vad:** Företagens förväntade försäljningspriser kommande 3 månader (nettotal, ej
säsongsrensat) för tjänstesektorn, dagligvaruhandeln och sällanköpshandeln, som
korrigering för tjänster, livsmedel respektive varor. Två varianter: nivå och avvikelse
från eget 12-månaderssnitt. Enkätmånad t-1 används för prognos av t.
**Varför ej säsongsrensat:** säsongsrensningen skattas om på hela serien, så gamla värden
ändras i efterhand. Det vore läckage.
**Resultat, MAE:** 2024–2026: 0,375 → 0,369 (avvikelse) / 0,375 (nivå).
2015–2026: 0,316 → 0,311 / 0,319. På komponentnivå är förbättringen ≤ 0,002 pe.
**Slutsats:** Prisplanerna tillför i praktiken inget en månad framåt. Trenden fångar redan
samma information. Skillnaden mellan varianterna är brus, och att välja den som råkade vinna
på testperioden vore överanpassning. Huvudmodellen förblir komponentmodell med drivmedel + el.
Prisplanerna kan vara mer värda för längre horisonter (fas 5).

## 2026-11-22 – Fas 4b: skattekalender – hjälper vid stora händelser, inte i snitt
**Vad:** Skatteeffekt per månad = KPIF m/m − KPIF med konstant skatt (KPIF-KS, SCB TAB6592).
Skatteändringar beslutas i förväg, så effekten för månad t räknas som känd vid deadline
(antagande: full genomslag, som i SCB:s KS-metod). Historiken rensas från skatteeffekter,
modellen körs på rensade data och månadens kända skatteeffekt läggs tillbaka.
Fördelning mellan energi och övrigt via KPIF-XE-KS (finns från ~2020), annars efter vikt.
**Verifierat mot källor:** matmomsen halverades 12 → 6 % från 1 april 2026 (regeringen, SCB:
livsmedel −5,5 % i april). Sänkt skatt på bensin/diesel juli 2026 (SCB, TV4/TT). Samma
månad sänktes också kollektivtrafik- och förskoleavgifter, men det är avgifter och syns inte i KS.
**Resultat, MAE:** 2024–2026: 0,375 → 0,388. 2015–2026: 0,316 → 0,327.
April 2026 går från 0,75 till 0,03 i fel, men övriga månader blir något sämre.
**Varför sämre i snitt (hypoteser):** de återkommande små skatteändringarna (januari +0,1–0,3,
juli −0,2) fångas redan av säsongsmönstret, så rensningen tillför brus. Genomslaget är inte
alltid fullt eller omedelbart. Och de största kvarvarande missarna (jan 2025, mars 2026)
har ingen skatteeffekt alls. De är el, nätavgifter och annat.
**Beslut:** Skattekalendern ingår inte i huvudmodellen. Vid skarpa prognoser görs en
**manuell justering för stora, beslutade engångshändelser** (t.ex. momsändringar), vilket
också är så professionella prognosmakare arbetar.

## 2026-11-22 – Skarpa prognoser och första preliminära prognos (november 2026)
**Vad:** `forecast.py` gör prognos för månaden efter senast publicerade KPIF med
huvudmodellen (komponentmodell, drivmedel + el), sparar den som JSON i `forecasts/` och
committas före snabb-KPI. Status FINAL bara om data för hela månaden finns och körningen
sker senast den 4:e. Osäkerhetsintervall = empiriska felkvantiler från backtesten 2024–2026
(50 %: ±0,34, 80 %: ±0,54). Manuell justering möjlig med motivering.
**Preliminär prognos 2026-11 (gjord 22 nov):** 2,1 % (80 %: 1,5–2,6). Riksbanken (sept): 1,73.
Senaste utfall (okt): 1,1.
**Varför så högt:** elpriset i november är extremt hittills (SE3 ~1,8 kr/kWh mot 0,8 i okt,
SE4 ~2,7 mot 1,6), vilket ger energi ett bidrag på +1,2 pe. Oljepriset i kronor föll ~25 %
och drar ner. Övriga komponenter är svagt negativa (säsong).
**Risker:** elpriset kan falla resten av månaden (21 av 30 dagar kända). Elbidraget är en
extrapolation nära kanten av vad modellen sett sedan 2021. Kontrollera före slutlig prognos
om några skatter eller avgifter ändras i november.
