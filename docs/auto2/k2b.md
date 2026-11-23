`kpif_nowcast.__file__` = `C:\dev\kpif-auto2\k2b\src\kpif_nowcast\__init__.py`, SHA: slutcommit på `auto2/k2b` är commiten som lägger till den här raden (innehåll t.o.m. 866e1af).
pytest: 83 passerade, 4 överhoppade.

# PR: K2b – oberoende granskning av K2, K2-skuggor i driften, nätbaserad reproducerbarhet

beror på: main@25a6a6e

**Dom över K2: håller med förbehåll.** Granskningen: [k2b/granskning.md](k2b/granskning.md). Resultat: [k2b/resultat.md](k2b/resultat.md).

- **Läckage hittat och rättat:** Eurostat-flashen för december, mars 2018 och januari 2026 publiceras efter deadline (dag 4).
  Backfillen sa dag 2, så `ea_news` läckte. Rättat i `k2b_review.realistic_flash`. Efter rättelsen klarar
  `k2_avg_ridge_l` (0,200, Holm 0,025) och `k2_avg_ens_s` (0,202, Holm 0,083) skärmen mot 50/50 (0,217).
  `k2_avg_ridge_s` gör det inte (Holm 0,19).
- **Frysningsfel rättat:** K2:s L-mängd växte från 43 till 72 serier när K0 mergades. Nu fryst i `k2_ml.K2_CATALOG_KEYS`.
- **Skuggor:** `k2_avg_ens_s` och `k2_avg_ridge_l` finns i `SHADOW_MODELS` med flashrättelsen. `pipeline monthly` hämtar
  flashen och K2:s serier. En K2-skugga blir FINAL före dag 4 bara när flashen för målmånaden finns.
  Skuggprognoser för 2026-11 (PRELIMINARY): 1,66 och 1,63. Champion/challenger-tabellen är uppdaterad.
- **Granskningskod:** `src/kpif_nowcast/k2b_review.py` (scenarierna base, decfix, fwd, back, plant och no2223).
  Tester i `tests/test_k2b_review.py` och utökade `tests/test_shadow.py`.
- **Nätbaserad reproducerbarhet:** ren klon utan data/ i `C:\dev\kpif-auto2\k2b-clean`, weekly + monthly online GRÖNA.
  Skuggprognoserna för 2026-11 och SCORECARD.md är identiska med worktreens. Enda dataskillnaden i K2:s serier är `jobads_total`
  (JobTech räknar om senaste månaderna). Se resultat.md, avsnitt 3.
- Inga nya varianter. `forecast.py`/`MODEL_NAME` och `forecasts/<månad>.json` är orörda. pytest grönt.

Rekommendation (inte gjord, delad kod): `observations.upsert` bör sätta `known_from` = hämtdatum (inte
`min(periodslut + lag, hämtdatum)`) för nya perioder, så att sena releaser inte dateras för tidigt framåt.

https://github.com/birdiebook/kpif-nowcast/compare/main...auto2/k2b?expand=1
