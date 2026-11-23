# Vision

> **Förstå svensk ekonomi genom inflationen, och visa det varje månad, öppet och ärligt.**

Projektet står på egna meriter. Målet är **bästa möjliga lösning**: en så träffsäker
inflationsprognos som möjligt och den bästa bilden av läget i Sverige, sedd genom KPIF.
Varje val ska ge snabb och effektiv progress med kvalitet. Det är tre saker som hänger ihop:
en prognos, en bild av Sverige och ett sätt att arbeta.

## 1. Kärnan: en ärlig inflationsprognos varje månad

Varje månad gör vi en prognos av KPIF och **committar den innan SCB:s snabb-KPI** kommer.
Tidsstämpeln i git är beviset. Utfallet och vårt fel redovisas oavsett hur det gick.

Målet är att **på kort sikt (nästa månad) vara i nivå med Riksbanken**. Backtesten säger att det
är möjligt (MAE 0,32 mot 0,32 över 2015–2026). Nu ska det visas skarpt, månad för månad.

## 2. Bredden: en levande bild av läget i Sverige

Inflationen är slutpunkten för nästan allt som händer i ekonomin. Projektet bygger en
**datakatalog med 50+ serier i åtta områden**:

| Område | Exempel |
|---|---|
| Inflation | KPIF och dess komponenter, Riksbankens prognoser |
| Energi och råvaror | elpriser per elområde, olja, gas |
| Arbetsmarknad och löner | arbetslöshet, löner, lediga jobb, arbetskraftsbrist |
| Hushållen | konsumtion, detaljhandel, konfidens, inflationsförväntningar, sparande |
| Bostäder och krediter | bostadspriser, bolåneräntor, utlåning, hyror, byggande |
| Företagen | barometerindikatorn, prisplaner, kapacitetsutnyttjande, konkurser, produktion |
| Omvärlden | euroområdets inflation, globala matpriser, frakt, leveranskedjor |
| AI och produktivitet | arbetsproduktivitet, AI-användning i företag, AI-kompetens i platsannonser |

Varje värde lagras med **när det blev känt** (`known_from`). Bilden kan alltså spelas upp
exakt som den såg ut ett visst datum, och modellerna testas utan facit i handen.
Ovanpå katalogen byggs en **dashboard över läget i Sverige** som visar hur varje område
hänger ihop med inflationen just nu.

## 3. AI-linsen: hur påverkar AI svensk ekonomi?

Den kanske viktigaste ekonomiska frågan de kommande åren är om AI höjer produktiviteten. Om
den gör det sjunker kostnaden per producerad enhet, vilket i sin tur pressar inflationen.
Kedjan vi vill följa:

```
AI-spridning → investeringar och kompetens → produktivitet → enhetsarbetskostnad → inflation
(företag, annonser)  (programvara, AI-jobb)   (BNP/timme)      (löner/produktivitet)   (KPIF)
```

Här finns inget facit ännu, och det ska sägas rakt ut. Målet är att bygga **en svensk
AI-indikator** som följer kedjan över tid och jämför Sverige med euroområdet. Då syns det
när, eller om, effekten dyker upp i siffrorna.

## 4. Arbetssättet: agentiskt, men människan äger besluten

Koden skrivs mest av en AI-agent. Människan formulerar problemet, väljer utvärdering,
granskar kritiskt och fattar besluten. Varje viktigt val står i
[`beslutslogg.md`](beslutslogg.md). Projektet är därmed också ett exempel på hur modern
analys och ML görs: mindre handarbete, mer omdöme.

## Principer

1. **Ärlighet före träffsäkerhet.** Prognoser låses före utfallet. Negativa resultat redovisas
   lika tydligt som positiva (KI-prisplanerna och skattekalendern hjälpte inte, och det står i loggen).
2. **Bara det som var känt då.** Inget läckage: publiceringsfördröjningar och revideringar
   hanteras med `known_from`.
3. **Enkelt först.** En ny variabel eller modell ska förtjäna sin plats genom att slå en enkel
   baslinje på lång historik, inte bara på en kort testperiod.
4. **Öppen data, reproducerbart.** Allt hämtas med skript från öppna källor. Data committas aldrig.
5. **Bredd med syfte.** Varje serie i katalogen ska ha en tydlig koppling till inflationen
   eller till AI-frågan.

## Vad vi redan har lärt oss

- En enkel modell med säsongsmönster och energipriser är **i nivå med Riksbanken en månad framåt**.
- **Elpriset** är den enskilt viktigaste variabeln månad för månad. Januari är svårast.
- **På längre sikt vinner Riksbanken tydligt**, och på 12 månader är "det blir 2 %" lika bra som Riksbanken.
- **Avancerad ML slår inte enkla modeller på makrodata.** Det finns för få oberoende observationer.
  Värdet ligger i rätt data vid rätt tidpunkt, inte i tyngre algoritmer.

## Färdplan

| När | Vad |
|---|---|
| **Nu** | Datakatalogen (50+ serier, åtta områden), dashboard över läget i Sverige, test av vilka serier som förbättrar prognosen |
| **Nästa** | Bättre nowcast: euroområdets snabbestimat, januari-el (nätavgifter, skatt), längre elhistorik, kombination med Riksbanken |
| **Sedan** | Drift utan egen dator (fas 6): GitHub Actions, DuckDB, dbt, MLflow, champion/challenger |
| **På sikt** | Svensk AI-indikator och produktivitetsanalys. Ett kort månadsbrev om inflationen och läget i Sverige |

## Hur vi vet att det lyckas

- **12 månader i rad** med skarpa prognoser publicerade före utfallet, med ett fel i nivå med Riksbanken.
- En dashboard över läget i Sverige som **uppdateras automatiskt** varje månad.
- En AI-indikator för Sverige med historik och jämförelse mot EU.
- Ett projekt som går att visa och förklara: problem, data, metod, resultat och misstag.

## Vad projektet inte är

Det är inte investeringsrådgivning eller en tradingstrategi. Det försöker inte förutse allt.
Det är ett försök att förstå en sak riktigt bra, inflationen, och genom den se resten av ekonomin.
