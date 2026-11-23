"""K6 information-set test: the Nordic forecast for t is identical with and without data after t's deadline.

Cut: HICP up to t-1, spot and Brent up to t. Synthetic data, so it runs without the raw cache.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.k6_nordic import REFERENCE, compare, nordic_forecast, regressors


@pytest.fixture(scope="module")
def synthetic():
    rng = np.random.default_rng(6)
    months = pd.period_range("2008-01", "2026-10", freq="M")
    spot = pd.Series(0.5 + rng.normal(0, 0.1, len(months)).cumsum(), index=months)
    brent = pd.Series(60 * np.exp(rng.normal(0, 0.05, len(months)).cumsum()), index=months)
    regs = regressors(spot, brent)
    mm = 0.15 + 0.4 * np.sin(np.arange(len(months)) * 2 * np.pi / 12) + 5 * regs["el_dev"].fillna(0).to_numpy()
    index = pd.Series(100 * np.cumprod(1 + (mm + rng.normal(0, 0.1, len(months))) / 100), index=months)
    return index, spot, brent


@pytest.mark.parametrize("col", ["variant", REFERENCE])
def test_nordic_uses_only_deadline_data(synthetic, col):
    index, spot, brent = synthetic
    full = nordic_forecast(index, regressors(spot, brent))[col]
    for t in pd.period_range("2015-01", "2026-10", freq="M")[::7]:
        live = nordic_forecast(index.loc[: t - 1], regressors(spot.loc[:t], brent.loc[:t]))[col]
        assert live.index.max() == t
        assert np.isclose(live[t], full[t], rtol=0, atol=1e-10), f"{col} {t}: {live[t]} vs {full[t]}"


def test_correction_helps_when_el_drives_prices(synthetic):
    index, spot, brent = synthetic
    res = nordic_forecast(index, regressors(spot, brent)).loc["2015-01":"2026-10"].dropna()
    mae = res[["variant", REFERENCE]].sub(res["actual"], axis=0).abs().mean()
    assert mae["variant"] < mae[REFERENCE]


def test_compare():
    idx = pd.period_range("2010-01", periods=30, freq="M")
    a = pd.Series(np.arange(30.0), index=idx)
    out = compare(a, a + 0.5)
    assert out["n"] == 30 and out["corr"] == pytest.approx(1.0) and out["mad_pp"] == pytest.approx(0.5)
