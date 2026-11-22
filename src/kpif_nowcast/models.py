"""Phase 3 model: seasonal-trend baseline + correction from energy prices.

    KPIF m/m (t) = seasonal_trend_mm(t) + b_fuel * fuel_chg(t) + b_el * el_chg(t) + error

The baseline handles seasonality and trend; the regression only learns how much
of this month's energy price moves pass through to KPIF. No intercept: the
baseline is already unbiased, and with few observations every extra parameter costs.

Fitted with an expanding window: the coefficients for month t are estimated on
months strictly before t only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kpif_nowcast.baselines import mm_change, seasonal_trend_mm, yy_from_mm


def expanding_energy_model(
    index: pd.Series,
    features: pd.DataFrame,
    feature_cols: list[str],
    train_start: str,
    min_train: int = 24,
) -> pd.DataFrame:
    """Returns per month: y/y forecast, and the coefficients used."""
    base_mm = seasonal_trend_mm(index)
    resid = (mm_change(index) - base_mm).rename("resid")
    data = pd.concat([resid, base_mm.rename("base_mm"), features[feature_cols]], axis=1)
    data = data.loc[pd.Period(train_start, "M"):].dropna(subset=["base_mm", *feature_cols])

    out = {}
    months = data.index
    for i, t in enumerate(months):
        train = data.iloc[:i].dropna(subset=["resid"])
        if len(train) < min_train:
            continue
        X, y = train[feature_cols].to_numpy(), train["resid"].to_numpy()
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        mm_hat = data.loc[t, "base_mm"] + data.loc[t, feature_cols].to_numpy() @ coef
        out[t] = {"mm_hat": mm_hat, "n_train": len(train), **{f"b_{c}": b for c, b in zip(feature_cols, coef)}}

    res = pd.DataFrame(out).T
    res.index = pd.PeriodIndex(res.index, freq="M")
    res["yy_hat"] = yy_from_mm(index, res["mm_hat"].reindex(index.index)).reindex(res.index)
    return res
