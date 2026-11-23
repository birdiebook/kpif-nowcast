# L8 Snabbare testsvit: resultat

**Status:** klar. Samma 205 insamlade tester (identisk `--collect-only`-lista före/efter), inga assertions ändrade,
inga bootstrap-replikat minskade, ingen produktionskod ändrad.

## Huvudfyndet: OpenMP-trådar, inte testerna

K2-skuggmodellerna (`k2_avg_ens_s`) anpassar scikit-learns `HistGradientBoostingRegressor` i nästlad CV
(8 parameterkombinationer × 4 delningar + omanpassning = 33 anpassningar per prognosmånad, ca 130 rader). Standard
är en OpenMP-tråd per kärna. På så små data kostar trådsynkroniseringen mer än arbetet, och med flera
pytest-xdist-arbetare och andra spårs sviter på samma 4 kärnor snurrar trådarna mot varandra:

| En nästlad HGB-anpassning (130 rader, 14 features) | Väggtid |
|---|---|
| standard (4 OpenMP-trådar), last ~25 | **> 12 min**, avbruten |
| `OMP_NUM_THREADS=1` | **2,1 s** (1,6 s CPU) |

Det var därför sviten tog > 40 min och såg ut att hänga i `test_shadow`, `test_k5` och `test_k10`. Åtgärd:
`tests/conftest.py` sätter `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` och `MKL_NUM_THREADS` till 1 (`setdefault`,
så ett uttryckligt värde i miljön vinner) innan numpy och scikit-learn importeras. Testerna jämför en modell med
sig själv (avskuren mot full data, samma process, samma trådantal), så trådantalet kan inte ändra vad de prövar.
Produktion importerar inte conftest och påverkas inte.

## Övriga ändringar (små diffar i befintliga testfiler)

| Fil | Ändring | Varför det är samma test |
|---|---|---|
| `tests/conftest.py` | session-fixturen `memo_champion`: `champion.histories` (alla skuggmodeller över hela historiken, inkl. K2) memoiseras på innehållshash av `Inputs` + skuggregistret | funktionen är deterministisk; upprepat anrop med identiska indata ger en kopia av första resultatet. Annan indata eller utbytt modell ger ny beräkning |
| `tests/test_k5.py`, `tests/test_k10_pages.py` | `pytestmark = usefixtures("memo_champion")` | `test_letter_uses_only_data_known_at_cutoff` byggde champion-tabellen två gånger på samma avskurna `Inputs` (447 → 121 s) |
| `tests/test_shadow.py` | långsamma K2-modeller: en fulldata-körning från första kontrollmånaden i stället för en per månad | en K2-rad beror bara på designen och sin egen position (`K2Runner.forecast(name, i)`), så `full[t]` är identiskt; designen byggs en gång i stället för tre (ridge_l: 43 s per bygge) |
| `tests/test_k9_horizon.py` | designerna per horisont byggs vid första användning | med xdist byggde varje arbetare alla tre horisonterna (142 s setup); nu bara den horisont arbetaren testar |
| `pyproject.toml`, `ci/requirements.txt` | `pytest-xdist` i dev-beroenden (3.8.0 pinnad i CI) | – |

Ingen `slow`-markör behövdes: de tunga testerna (K5/K10 dashboard och brev, K2-skuggor) är nu några minuter var
och körs som förut. Workflows kör inte pytest, så `-n auto` i workflows var inte aktuellt.

## Mätning (samma container, 4 kärnor delade med andra spårs sviter; lasten varierade)

| Körning | Väggtid | CPU totalt (user+sys, ≈ seriell tid på ledig maskin) | Last |
|---|---|---|---|
| Före, `-n 2` | avbruten efter 37 min vid ~78 %, fast i HGB | – | 20–40 |
| Före, orkestrerarens `-n 4` på merge1 | > 50 min (pågick fortfarande) | – | 20–40 |
| Endast trådgränsen, `-n 4` | 16,5 min | 18,7 min | 25–30 |
| **Alla ändringar, `-n 4`** | **11,0 min** | **11,7 min** | 6–17 |

Den långsammaste testen är nu `test_k10_pages::test_site_build_writes_every_dataset_the_page_reads` (454 s vägg
under last, en full champion-körning), följd av `test_k5::test_letter_current_month` (397 s) och K2-skuggtesterna
(289 och 263 s). På en ledig maskin bör `-n 4` landa nära den längsta enskilda testen, ca 4–6 min; det kunde inte
mätas här eftersom andra spår körde sina sviter samtidigt (osäkert). En separat seriell körning gjordes inte av
samma skäl; CPU-summan 11,7 min är den bästa uppskattningen av seriell tid (före: > 40 min enligt orkestreraren).

## Att notera

- **Befintligt fel på merge1, inte orsakat av L8:** `tests/test_l6_fx.py::test_registered_once_right_after_catalog_prices`
  faller eftersom L2:s gästnattsserier hamnade mellan `catalog_prices` och `sek_eur/sek_usd` i `CATALOG` vid
  mergen. Rättas i katalogordningen eller testet av orkestreraren.
- `data/processed/el_contracts.csv` saknas i containern, så `test_k2_ml`, `test_k7_services` och några till
  hoppas över här. På en maskin med filen kör de K2 med HGB och vinner också på trådgränsen.
- Andra spår (l10, v2) körde sina sviter med 17–18 trådar per arbetare under mätningen: de får trådgränsen först
  när L8 är mergad.
- Rekommendation, inte gjord (skuggprognosernas siffror): `OMP_NUM_THREADS=1` även i `monthly-shadow.yml`
  skulle snabba upp K2-skuggorna i CI men kan ge skillnader i sista decimalen i HGB och bör beslutas separat.

## Kalibrering

Start 2026-11-23T13:33Z, slut se commit. Ca 60 verktygsanrop. Det mesta av tiden var väntan på svitkörningar
under hög last.
