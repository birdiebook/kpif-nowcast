"""J2 information-set test: the forecast for t is identical with and without data after t's deadline.

Cut: KPIF and components at t-1, energy features at t, contracts (TAB3571) at t-1, SE3 spot at t.
Like test_information_set.py this is an indexing test; revised TAB3571 vintages would not be caught.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR

if not (PROCESSED_DIR / "el_contracts.csv").exists():
    pytest.skip("data/processed missing", allow_module_level=True)

from kpif_nowcast.data import load_components, load_el_contracts, load_kpif
from kpif_nowcast.features import load_features
from kpif_nowcast.j2_el import VARIANTS, build_j2_features, holm, j2_forecast, same_month_dev, zone_monthly_spot

MONTHS = pd.period_range("2015-01", "2026-10", freq="M")[::11]


@pytest.fixture(scope="module")
def data():
    return load_kpif(), load_components(), load_features(), load_el_contracts(), zone_monthly_spot("SE3")


@pytest.mark.parametrize("variant", list(VARIANTS))
def test_j2_uses_only_deadline_data(data, variant):
    kpif, comps, feats, contracts, se3 = data
    full = j2_forecast(kpif["index"], comps, build_j2_features(feats, contracts, se3), variant)["yy_hat"]
    for t in MONTHS:
        j2f = build_j2_features(feats.loc[:t], contracts[contracts["month"] <= t - 1], se3.loc[:t])
        live = j2_forecast(kpif["index"].loc[: t - 1], comps[comps["month"] <= t - 1], j2f, variant)["yy_hat"]
        assert live.index.max() == t
        assert np.isclose(live[t], full[t], rtol=0, atol=1e-10), f"{variant} {t}: {live[t]} vs {full[t]}"


def test_same_month_dev_is_past_only():
    x = pd.Series(np.arange(40.0), index=pd.period_range("2010-01", periods=40, freq="M"))
    d = same_month_dev(x)
    assert np.isnan(d.iloc[11]) and d.iloc[12] == 12.0  # t=12: x_t - x_{t-12}
    assert d.iloc[24] == 24 - np.mean([12, 0])


def test_holm():
    adj = holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj == pytest.approx({"a": 0.03, "c": 0.06, "b": 0.06})
