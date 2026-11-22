# kpif-nowcast

Nowcasting Swedish inflation (KPIF): predicting next month's figure before
Statistics Sweden (SCB) publishes it, and benchmarking it against naive baselines
and the Riksbank's own forecasts.

> **Status: learning project, work in progress.**

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

## Results

**Phase 2: baselines (2015–2026, 141 months, KPIF y/y one month ahead)**

| Forecast | MAE (pp) |
|---|---|
| Riksbank (latest forecast available at our deadline) | 0.32 |
| Seasonal pattern + 12-month trend | 0.34 |
| Naive (same y/y as last month) | 0.38 |

A simple seasonal baseline is already close to the Riksbank over the full period,
but clearly worse in 2024–2026. Next: electricity and fuel prices.

Run it yourself:

```
python -m venv .venv && .venv/Scripts/pip install -e .
python -m kpif_nowcast.data       # fetch data
python -m kpif_nowcast.backtest   # scores + chart in outputs/
```
