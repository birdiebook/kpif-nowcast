# J3 Systematiskt prognostest av datakatalogen: förregistrering

Skriven 2026-11-22 innan någon screening har körts. Bas: origin/main @ a8cd686.
Basmodell h=1: `rb_updated` (från origin/main, enligt briefen; J1 klarade inte skärmen).
Basmodell h=3 och h=12: Riksbankens prognos för o+h från senaste omgång publicerad före origin-datumet
(som i `horizon.py`).

## Hypotes
Några av katalogens 45 månadsserier (alla `freq == "M"` utom `kpif_index` och `kpif_yy`) tillför
information utöver basmodellen. De flesta gör det inte.

**Min gissning innan:** h=1: 0–2 serier överlever Benjamini-Hochberg (q = 0,10). Störst chans har
`brent_sek` och `ea_flash_energy`/`ea_flash_total` (energi efter Riksbankens cutoff). h=3 och h=12:
ingen överlever, eftersom Riksbanken redan är svår att slå där.

## Protokoll (lika för alla serier)
- **Point-in-time:** värden via `observations.as_of(serie, deadline)`. h=1: deadline(t) = dag 4 i t+1.
  h=3/12: origin-datum dag 4 i o+2 (som `horizon.origin_date`). Senaste kända period p* ≤ målmånad.
- **Transform x:** om nyckeln slutar på `_yy`, enheten börjar med "% årstakt" eller nyckeln slutar på
  `_growth`: x = v[p*] − v[p*−1]. Annars säsongsdifferentierad månadsförändring:
  x = Δv[p*] − Δv[p*−12], där Δ är förändring mot föregående månad, i log ×100 om alla värden > 0
  och enheten inte innehåller "%", "nettotal", "std" eller "100 = normalt", annars i nivå.
- **Korrektion:** prognos = bas + b·(x − x̄), där x̄ och b skattas med expanderande fönster (OLS utan
  intercept på centrerat x) på mål vars utfall var publicerat vid prognosdatumet. Minst 24 obs, annars 0.
- **Utvärdering:** primärt urval h=1: 2017-02..2026-10 (n ≈ 117, då en korrektion kan vara aktiv),
  också rapporterat 2015–2026. h=3/12: mål 2017-02..2026-10. Ensidigt DM-test (absolutfel,
  H1: lägre MAE än basen; för h>1 Newey-West-lag enligt evaluation.py och HLN med h). BH med q = 0,10
  per horisont, separat. Rangordnad tabell med MAE, diff, rå p, BH-q, revised-flagga och n aktiva månader.
- **Revised:** serier med `revised=True` flaggas. En serie som överlever BH tack vare sådan data märks
  "obekräftad (revisionsläckage möjligt)".
- **Kombination (räknas som 1 variant i globala taket):** de högst tre h=1-serier som överlever BH testas
  tillsammans en gång (OLS på alla tre). Överlever ingen: de tre med lägst rå p testas tillsammans en gång
  och märks "ingen överlevde BH". Holm-p för den enda kombinationen = rå p (en test).
- Screeningen räknas inte mot globala taket (briefen).

pytest `tests/test_j3_screen.py` kräver identisk prognos för t med och utan data efter t:s deadline.
