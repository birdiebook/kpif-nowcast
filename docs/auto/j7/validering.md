# J7 Validering av söktermer (JobTech historical ads)

Bedömt av agenten 2026-11-22 genom att läsa rubrik och textutdrag runt träffen. Definition av *relevant*:
annonsen säger att jobbet innebär att utveckla, leda eller använda AI/ML. Standardtexter om AI i
rekryteringsprocessen (chattbot, "du får använda generativ AI i ansökan") räknas som **inte** relevanta.

## Två stickprov
1. **Förregistrerat:** 10 annonser per term från 2025 med API:ts standardsortering. Den visade sig vara
   *relevanssortering*: alla 80 annonser har termen i rubriken, och alla bedömdes relevanta. Stickprovet
   överskattar därför precisionen och används inte för beslut.
2. **Tillagt efter det första stickprovet** (metodfix, inte en modellvariant): 10 annonser per term från
   2025-06..2025-12, sorterade på publiceringsdatum (`sort=pubdate-desc`). Det ligger närmare ett slumpurval.
   Råmaterialet finns i `outputs/j7_validation_sample_pubdate.csv` (inte i git).

## Resultat (stickprov 2)
| Term | Träffar jun–dec 2025 | Relevanta / 10 | Kommentar | Godkänd (≥ 0,7) |
|---|---|---|---|---|
| AI | 3 693 | 7 | 3 strikt AI-kompetens, 4 "använda AI i jobbet", 3 ej relevanta | ja (bred) |
| artificiell intelligens | 3 618 | 7 | **Samma annonser som "AI"**: JobTech expanderar synonymer | redundant |
| maskininlärning | 1 149 | 10 | | ja |
| machine learning | 1 144 | 10 | **Samma annonser som "maskininlärning"** | redundant |
| generativ AI | 115 | 1 | 9 av 10 är standardtexten "om du väljer att använda generativ AI i din jobbansökan" | nej |
| LLM | 56 | 10 | | ja (liten volym) |
| språkmodell | 5 | 4 av 5 | En AI-chattbot i rekryteringen | ja (försumbar volym) |
| deep learning | 5 577 | 0 | Söker på "deep" och "learning" var för sig | nej |

## Slutsatser
- JobTech:s fritext är **konceptbaserad**: svenska och engelska synonymer ger samma träffar, och fraser
  med två ord kan delas upp. Termer måste därför valideras på resultaten, inte på ordet.
- **Huvudserie (enligt förregistreringen, bredaste godkända termen): "AI".** Precision ca 0,7, med stor
  osäkerhet (n = 10 ger ett 95 %-intervall på ungefär 0,35–0,93). Den fångar AI *i arbetet* i bred mening.
  Risk: standardtexter om generativ AI i ansökan räknas med och växer sannolikt från 2024. Det kan blåsa upp
  ökningen de senaste åren.
- **Robusthetsserie: "maskininlärning"** (precision 1,0, smalare, inga standardtexter). Den bör visa samma
  riktning som huvudserien om ökningen är verklig.
- generativ AI och deep learning ska inte användas.

## Ändrat efter resultat: huvudserien byts till "maskininlärning"
När årsserierna 2016–2025 byggdes syntes ett **brott i "AI"-serien 2025**:
| År | "AI" per 10 000 annonser | "artificiell intelligens" | "maskininlärning" |
|---|---|---|---|
| 2023 | 3,3 | 0,3 | 15,6 |
| 2024 | 6,9 | 0,4 | 23,5 |
| 2025 | 72,4 | 67,6 | 32,3 |

Före 2025 ger "artificiell intelligens" nästan inga träffar och "AI" få, men 2025 ger de nästan samma
annonser. Synonymexpansionen (eller berikningen av annonserna) i JobTech verkar alltså ha ändrats för 2025.
Tiodubblingen är ett mätbrott, inte en verklig ökning. Valideringen gjordes på 2025, där termen fungerar,
och fångade därför inte brottet. "maskininlärning" och "machine learning" ger samma träffar alla år, så den
serien har ingen sådan förändring. **Huvudserien blir "maskininlärning"**, i strid med förregistreringens regel
(bredaste godkända termen). Det redovisas här och i analysen. "AI" redovisas, men bara med brottsvarning.
Dessutom: "LLM" har träffar redan 2016 (10 st). Det är troligen juristexamen (Master of Laws), alltså falska
träffar före ~2023.
