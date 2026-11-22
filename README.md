# kpif-nowcast

Nowcasting Swedish inflation (KPIF): predicting next month's figure before
Statistics Sweden (SCB) publishes it, and benchmarking it against naive baselines
and the Riksbank's own forecasts.

> **Status: learning project, work in progress.** Vision (Swedish): [`docs/vision.md`](docs/vision.md).

## Why

I work in BI and data engineering and want to grow into predictive modelling.
This project is how I'm learning it. The goal isn't to beat the Riksbank. It's
to understand forecasting properly: honest validation, data leakage, baselines,
and why models miss when they miss.

## How it's built: agentic, human-steered

The code is written mostly by an AI coding agent (Claude Code). My job is the
one that matters in modern ML work: framing the problem, choosing the evaluation
setup, reviewing the agent's output critically, and owning the decisions.
The reasoning behind those decisions is logged in
[`docs/beslutslogg.md`](docs/beslutslogg.md) (in Swedish).

## Approach

1. **Baselines first**: last month, same month last year, moving average.
2. **Honest backtest**: rolling origin, using only data available at each forecast date.
3. **High-frequency drivers**: electricity spot prices and fuel prices, observable before release.
4. **Bottom-up**: forecast KPIF components separately and aggregate with SCB's weights.
5. **Longer horizons**: labour market, wages, GDP and the krona.

## Repository layout

```
src/kpif_nowcast/   code
notebooks/          exploration
docs/               decision log, data sources (Swedish)
data/               not committed – fetched by scripts
```

## Live forecasts

Every month a forecast is made and committed **before** SCB's flash estimate (~day 4–8
of the following month). The git commit timestamp is the proof. See
[`forecasts/SCORECARD.md`](forecasts/SCORECARD.md) for forecasts vs outcomes.

```
python -m kpif_nowcast.forecast                         # forecast next month
python -m kpif_nowcast.forecast --adjust -0.3 --note "VAT cut"   # with manual judgement
python -m kpif_nowcast.scorecard                        # after SCB's release
```

## Results

**Phase 2: baselines (2015–2026, 141 months, KPIF y/y one month ahead)**

| Forecast | MAE (pp) |
|---|---|
| Riksbank (latest forecast available at our deadline) | 0.32 |
| Seasonal pattern + 12-month trend | 0.34 |
| Naive (same y/y as last month) | 0.38 |

A simple seasonal baseline is already close to the Riksbank over the full period,
but clearly worse in 2024–2026.

**Phase 3: adding energy prices**

| Forecast | MAE 2015–2026 | MAE 2024–2026 |
|---|---|---|
| Riksbank | 0.32 | 0.33 |
| Baseline + fuel (Brent in SEK) | 0.32 | 0.45 |
| Baseline + fuel + electricity spot | – | 0.40 |
| Seasonal baseline | 0.34 | 0.45 |

Energy prices help, but the Riksbank is still ahead in recent years. The biggest misses
are January and March–April, likely one-off tax and fee changes that are known in advance
but invisible in price data.

**Phase 4: bottom-up by component**

Each KPIF component's contribution to the monthly change (services, goods, food, energy,
capital stock) is forecast separately and summed. Energy gets the price correction.

| Forecast | MAE 2024–2026 |
|---|---|
| Riksbank | 0.33 |
| Component model (fuel + electricity) | 0.375 |
| Phase 3 model | 0.395 |
| Seasonal baseline | 0.45 |

Remaining error is mostly energy (January fee and tax changes) and services.

Adding NIER business survey price plans (services, grocery and specialty retail) made no
meaningful difference one month ahead (0.375 → 0.369, within noise), so they're left out of
the main model for now.

A tax-change calendar (from SCB's CPIF at constant taxes) nails the April 2026 food VAT cut
(error 0.75 → 0.03 pp) but makes the average slightly worse (0.375 → 0.388): routine tax
changes are already in the seasonal pattern. Large one-off policy changes will instead be
handled as a manual adjustment in live forecasts.

**Phase 5: longer horizons (MAE 2015–2026, pp y/y)**

| Forecast | 3 months | 6 months | 12 months |
|---|---|---|---|
| Riksbank | **0.49** | **0.81** | **1.39** |
| Gradient boosting (macro features) | 0.63 | 1.04 | 1.82 |
| Reversion to target | 0.68 | 1.15 | 1.60 |
| Naive | 0.67 | 1.10 | 1.89 |
| "Inflation will be 2 %" | 1.37 | 1.37 | **1.39** |

Beyond the nowcast the Riksbank wins clearly, and at 12 months simply assuming the 2 % target
is as good as the Riksbank. Macro data has too few independent observations for ML to shine.
Features are built point-in-time from a versioned observation table (`known_from`), so
publication lags are respected (revisions before today's vintage are not).

Electricity prices: [Elpriset just nu.se](https://www.elprisetjustnu.se) (ENTSO-E data).
Oil: FRED. Exchange rates and forecasts: Sveriges Riksbank. CPI: Statistics Sweden (CC0).

Run it yourself:

```
python -m venv .venv && .venv/Scripts/pip install -e .
python -m kpif_nowcast.data             # fetch CPIF + Riksbank forecasts
python -m kpif_nowcast.backtest         # phase 2 scores + chart in outputs/
python -m kpif_nowcast.sources.elpris   # electricity prices (slow first time, cached)
python -m kpif_nowcast.features         # monthly energy features
python -m kpif_nowcast.backtest_phase3  # phase 3 scores + chart
python -m kpif_nowcast.backtest_phase4  # phase 4 component model
```
