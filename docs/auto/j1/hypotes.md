# J1 Hybridmodell: förregistrering

Skriven 2026-11-22 innan något fel för 2015–2026 har beräknats för varianterna nedan.
Bas: taggen `auto/j2-done` @ 438480b (J2 klarade urvalsskärmen). Komponentmodellen nedan är J2:s
V2 `j2_el_dev` ("j2").

## Hypotes
`rb_updated` saknar bara information efter Riksbankens cutoff. Den viktigaste är månad t:s energipriser,
som J2-modellen fångar men Riksbanken inte kan känna till. En kombination av rb_updated och j2, eller
rb_updated plus j2:s energinyhet, är bättre än rb_updated. Vinsten bör vara störst när prognosomgången är
2–3 månader gammal och nära noll vid 1 månad.

**Min gissning innan:** bästa variant ca 0,215–0,225 i MAE (rb_updated 0,256, j2 0,243), alltså −0,03
till −0,04. Ensidigt p kring 0,02–0,10 före Holm; efter Holm över 8 varianter kanske strax över 0,10.
Energinyheten med fast β = 1 (H1) är troligen nästan lika bra som de skattade varianterna.

## Jämförelse och godkänt
- Jämförelsemodell: `rb_updated`. Nästlad jämförelse: **ensidigt** DM-test (absolutfel), riktning
  "varianten har lägre MAE". Holm-justering över alla 8 varianter. Råa p bredvid.
- Godkänt: Holm-p < 0,10 på 2015-01..2026-10 (alla månader med rb_updated och j2, n ≈ 141), och inte sämre
  än rb_updated på 2024–2026 (använd, bara rapport). Även rapport: MAE efter prognosomgångens ålder 1/2/3+,
  och delurvalet från 2017-02 där alla skattningar har ≥24 tidigare observationer.
- Skrivs aldrig som "slår rb_updated". En variant som klarar skärmen fryses som skuggprognos.

## Gemensamma regler
- Allt som skattas (vikter, β) skattas med expanderande fönster på månader < t vars utfall är kända vid
  deadline (KPIF för t−1 publiceras mitten av t). Före 24 tidigare observationer används ett förregistrerat
  startvärde (anges per variant), så att alla varianter täcker hela 2015–2026.
- energy_news_t = j2:s energikorrektion för t (pe av m/m): β̂·[fuel_chg, el_dev], skattad i J2-modellen.
- core_dev_{t−1} = summan över icke-energikomponenter av (utfall − säsongsbaslinje) för t−1, pe.
- ea_news_t = euroområdets snabbestimat (total, första publicering) för t minus för t−1, via
  `observations.as_of(…, deadline(t))`. Finns från 2017-08; saknas → 0.

## Varianter (exakt lista, 8 st)
| # | Namn | Prognos | Startvärde (<24 obs) |
|---|---|---|---|
| C1 | `j1_comb_equal` | 0,5·rb_updated + 0,5·j2 | – (inget skattas) |
| C2 | `j1_comb_invmse` | vikter ∝ 1/MSE av tidigare fel (expanderande) | 0,5/0,5 |
| C3 | `j1_comb_ols` | rb_updated + β·(j2 − rb_updated), β = OLS utan intercept på tidigare fel, klipps till [0, 1] | β = 0,5 |
| C4 | `j1_comb_ols_age` | som C3 men separat β för prognosomgångens ålder 1, 2, ≥3 mån (kräver ≥12 obs per ålder, annars C3:s β) | β = 0,5 |
| H1 | `j1_hyb_energy_fixed` | rb_updated + energy_news (β = 1, inget skattas) | – |
| H2 | `j1_hyb_energy` | rb_updated + β·energy_news, β = OLS utan intercept | β = 1 |
| H3 | `j1_hyb_energy_core` | rb_updated + OLS på [energy_news, core_dev_{t−1}] | (1, 0) |
| H4 | `j1_hyb_energy_ea` | rb_updated + OLS på [energy_news, ea_news] | (1, 0) |

Inga reviderade serier (ea_flash är första publicering, fryst; Spec revised=False).
pytest `tests/test_j1_hybrid.py` kräver identisk prognos för t med och utan data efter t:s deadline.
