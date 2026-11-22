# J7 Svensk AI-indikator: plan och hypotes (skriven innan data hämtats)

Skriven 2026-11-22. Bas: origin/main @ a8cd686. J7 bygger ingen prognosmodell; inga varianter räknas mot taket.

## Hypotes
AI-spridningen syns tidigast i kompetensefterfrågan (platsannonser) och i företagens AI-användning, senare
(om alls) i produktiviteten i AI-exponerade branscher. Ingen orsaksslutsats dras.

**Min gissning innan:** AI-andelen av annonserna steg långsamt 2016–2022 och tydligt från 2023 (generativ AI).
"AI" som fritext är brusigt (andra betydelser), "maskininlärning"/"machine learning" har hög precision men
låg volym. Produktiviteten i informations- och kommunikationsbranschen (J) har ökat snabbare än i övriga
näringslivet både i Sverige och EU sedan 2015, men det finns inget tydligt AI-hack efter 2023 ännu.

## Metod (bestämd innan)
1. **Söktermer (JobTech historical ads, CC0):** "AI", "artificiell intelligens", "maskininlärning",
   "machine learning", "generativ AI", "LLM", "språkmodell", "deep learning".
2. **Validering:** 10 annonser per term från 2025 (API:ts standardsortering), rubrik + textutdrag runt
   träffen. Varje annons bedöms: *relevant* (efterfrågar eller beskriver AI/ML-kompetens eller AI-arbete) eller
   *inte*. Precision = andel relevanta. Termer med precision ≥ 0,7 ingår i indikatorn.
3. **Normerad annonsserie:** per år 2016–2025: antal annonser som matchar de godkända termerna / alla annonser,
   totalt och per yrkesområde (JobTech `stats=occupation-field`). Överlapp mellan termer hanteras genom att
   använda den bredaste godkända termen som huvudserie och redovisa de andra separat.
4. **Produktivitet per bransch:** real produktivitet per arbetad timme (Eurostat `nama_10_lp_a21`, RLPR_HW,
   2015 = 100, källa SCB:s nationalräkenskaper för Sverige), Sverige och EU27, AI-exponerade branscher
   (J information och kommunikation, K finans, M_N företagstjänster) mot övriga (B–E, F, G–I).
   Reviderad data.
5. **Indikator:** AI-spridning Sverige = snitt av z-värden (2017–2025) av (a) annonsandel och (b) andel företag
   som använder AI (Eurostat isoc_eb_ai, finns redan i katalogen). Produktiviteten hålls utanför
   indikatorn som utfall, så att spridning och effekt inte blandas. Jämförelse med EU: företagens
   AI-användning och branschproduktiviteten (annonser finns bara för Sverige).
6. Analys i `docs/ai-indikator.md`, data för dashboarden i `outputs/sverige/ai_indicator.json`.
