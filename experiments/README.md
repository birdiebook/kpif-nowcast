# Experiment

En CSV per körning i `runs/<utc>_<namn>.csv`, skriven av `python -m kpif_nowcast.backtest --name <namn>`.
En fil per körning gör att parallella spår aldrig krockar. Filerna committas, och ändras aldrig i efterhand.

Kolumner: `utc`, `git_sha` (`+dirty` = ocommittade ändringar), `variant`, `period`, `n`, `MAE`,
`dm_p_vs_rb_updated` (Diebold-Mariano-p mot "Riksbanken + senaste miss", se `src/kpif_nowcast/evaluation.py`).

Före varje ny variant: skriv hypotes och förväntat tecken i `docs/beslutslogg.md` under
"Min gissning innan". Modellval görs på 2015–2026. Perioden 2024–2026 är **använd**
(~50 varianter har redan testats där), så den rapporteras men väljer inga modeller.
