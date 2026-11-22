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
