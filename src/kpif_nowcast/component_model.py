"""Phase 4: bottom-up model on KPIF components.

SCB publishes each analysis group's contribution ("effect") to KPIF's monthly
change, in percentage points; the five contributions sum to KPIF m/m (up to rounding).
We forecast each contribution separately and sum them:

- services, goods, food, capital stock: seasonal pattern + 12-month trend
- energy: the same baseline + expanding-window regression on this month's
  electricity spot change and fuel proxy change (no intercept)

The KPIF m/m forecast (pp) is then turned into y/y via the known index.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kpif_nowcast.baselines import seasonal_trend_additive, yy_from_mm


def energy_correction(
    effect: pd.Series, base: pd.Series, features: pd.DataFrame, cols: list[str], train_start: str, min_train: int = 24
) -> pd.DataFrame:
    """Expanding-window regression of (energy effect - baseline) on energy price changes."""
    data = pd.concat([(effect - base).rename("resid"), features[cols]], axis=1)
    data = data.loc[pd.Period(train_start, "M"):].dropna(subset=cols)
    out = {}
    for i, t in enumerate(data.index):
        train = data.iloc[:i].dropna(subset=["resid"])
        if len(train) < min_train:
            continue
        coef, *_ = np.linalg.lstsq(train[cols].to_numpy(), train["resid"].to_numpy(), rcond=None)
        out[t] = {"correction": float(data.loc[t, cols].to_numpy() @ coef), **{f"b_{c}": b for c, b in zip(cols, coef)}}
    res = pd.DataFrame(out).T
    res.index = pd.PeriodIndex(res.index, freq="M")
    return res


def component_forecast(
    index: pd.Series, components: pd.DataFrame, features: pd.DataFrame, energy_cols: list[str], train_start: str
) -> pd.DataFrame:
    effects = components.pivot(index="month", columns="component", values="effect_month")
    effects = effects.reindex(pd.period_range(effects.index.min(), effects.index.max() + 1, freq="M"))
    base = effects.apply(seasonal_trend_additive)  # includes next (unpublished) month

    corr = energy_correction(effects["energy"], base["energy"], features, energy_cols, train_start)
    fc = base.copy()
    fc["energy"] = base["energy"] + corr["correction"]
    fc = fc.reindex(corr.index)

    out = fc.add_prefix("fc_")
    out["mm_hat_pp"] = fc.sum(axis=1)
    out["yy_hat"] = yy_from_mm(index, (out["mm_hat_pp"] / 100).reindex(index.index)).reindex(out.index)
    return out.join(corr.drop(columns="correction"))
