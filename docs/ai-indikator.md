# Svensk AI-indikator

Skriven 2026-11-22 (jobb J7). Beskrivande, inga orsaksslutsatser. Kod: `src/kpif_nowcast/j7_ai.py`
(`python -m kpif_nowcast.j7_ai build`), data i dashboarden: `outputs/sverige/ai_indicator.json`.
Metoden bestämdes innan data hämtades ([docs/auto/j7/hypotes.md](auto/j7/hypotes.md)), med en
redovisad ändring efter resultat (huvudserien, se nedan).

## Kedjan vi följer
```
AI-spridning → kompetens och användning → produktivitet → enhetsarbetskostnad → inflation
(annonser, företag)                     (per bransch)
```
Indikatorn mäter de två första leden. Produktiviteten visas bredvid som utfall, inte som en del av indikatorn.

## 1. Efterfrågan på AI-kompetens i platsannonser (JobTech, CC0)
**Validering** ([docs/auto/j7/validering.md](auto/j7/validering.md)): 10 annonser per term från andra halvåret 2025
lästes. JobTech:s sökning är konceptbaserad: "artificiell intelligens" = "AI" och "machine learning" =
"maskininlärning", medan "deep learning" delas upp i två ord (0/10 relevanta). "generativ AI" träffar mest en
standardtext om AI i ansökan (1/10). Godkända: maskininlärning (10/10), AI (7/10, bred), LLM (10/10, liten).

**Mätbrott 2025 i "AI":** andelen gick från 6,9 till 72 per 10 000 annonser på ett år, samtidigt som
"artificiell intelligens" gick från 0,4 till 68. Det är en ändring i JobTech:s matchning, inte en tiodubbling.
Huvudserien är därför **"maskininlärning"**, som är stabil över åren (ändrat efter resultat).

| År | Maskininlärning per 10 000 annonser | Antal annonser totalt |
|---|---|---|
| 2016 | 3,3 | 686 137 |
| 2018 | 13,0 | 683 668 |
| 2019 | 22,5 | 641 602 |
| 2021 | 18,0 | 734 398 |
| 2022 | 13,0 | 1 060 191 |
| 2023 | 15,6 | 1 030 902 |
| 2024 | 23,5 | 717 333 |
| 2025 | 32,3 | 621 875 |

- Andelen steg snabbt 2016–2019, föll 2020–2022 och har stigit igen sedan 2023, till den högsta nivån hittills.
  Fallet 2022 sammanfaller med att antalet annonser totalt nådde rekord (nämnareffekt: många annonser i andra yrken).
- Per yrkesområde 2025 (per 10 000 annonser i området): Data/IT 298, naturvetenskap 173, pedagogik 80
  (mest forskartjänster), tekniska yrken 69, administration/ekonomi/juridik 13. I övriga yrken är det nästan noll.
  Spridningen utanför Data/IT och forskning är fortfarande liten.

## 2. Företagens AI-användning (Eurostat isoc_eb_ai, företag med 10+ anställda)
| År | Sverige | EU27 |
|---|---|---|
| 2021 | 9,9 % | 7,7 % |
| 2023 | 10,4 % | 8,1 % |
| 2024 | 25,1 % | 13,5 % |
| 2025 | 35,0 % | 20,0 % |

Sverige ligger före EU och avståndet har ökat sedan 2023. Hoppet 2023→2024 är stort för både Sverige
och EU. Det kan delvis bero på att enkätens frågor om AI-tekniker har ändrats. Det har inte verifierats i den
här körningen.

## 3. Produktivitet per bransch (Eurostat nama_10_lp_a21, real förädling per arbetad timme, 2015 = 100)
Data från nationalräkenskaperna (för Sverige SCB), reviderad i efterhand.

| Bransch | Sverige 2019 | Sverige 2023 | Sverige 2025 | EU27 2025 |
|---|---|---|---|---|
| J Information och kommunikation | 111 | 109 | **139** | 124 |
| M_N Företagstjänster | 101 | 109 | 113 | 111 |
| K Finans och försäkring | 114 | 103 | 102 | 105 |
| B–E Industri | 104 | 105 | 105 | 111 |
| G–I Handel, transport, hotell | 105 | 103 | 111 | 108 |
| F Bygg | 98 | 96 | 99 | 91 |

- I svensk informations- och kommunikationsbransch steg produktiviteten med 28 % på två år (2023→2025),
  mer än i EU (+5 %). Det sammanfaller i tid med AI-spridningen, men **säger inget om orsaken**: branschen
  domineras av ett fåtal stora bolag, sammansättningen och prisdeflatorn för programvara påverkar, och
  siffrorna revideras ofta. Finans (K), också AI-exponerad, visar ingen ökning.
- Övriga näringslivet följer inget tydligt AI-mönster.

## 4. Indikatorn
**AI-spridning Sverige** = snittet av z-värden (2017–2025) för (a) maskininlärningsandelen av annonserna och
(b) andelen företag som använder AI (bara år med data).

| 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| −1,53 | −0,70 | 0,58 | 0,10 | −0,43 | −0,71 | −0,58 | 0,57 | 1,57 |

Tolkning: spridningen ligger 2025 på sin högsta nivå, ca 1,6 standardavvikelser över snittet för perioden.
z-värdena beräknas över hela perioden, så indikatorn är beskrivande. Den ska inte användas som prognos-feature
utan att räknas om point-in-time.

## Begränsningar
- Annonser är efterfrågan, inte användning. Fritextsökningen är brusig och JobTech:s matchning kan ändras (som 2025).
- Två komponenter, korta serier (företagens användning finns bara vissa år). Indikatorn är grov.
- Ingen koppling till inflationen kan beläggas än. Produktivitetsökningen i J är det första tecknet att följa.

## Uppdatering
Kör `python -m kpif_nowcast.j7_ai build` (svar cachas per anrop i `data/raw/j7/`) eller
`python -m kpif_nowcast.sverige_dashboard`, som exporterar `ai_indicator.json` för dashboarden.
