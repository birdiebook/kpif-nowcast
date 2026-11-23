"""J5 information-set test: the interval for t is identical with and without data after t's deadline.

Cut: KPIF/components at t-1, energy features at t. The interval for t depends on errors of months <= t-1
(whose point forecasts use data up to their own deadline) and on el/fuel for t.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR

if not (PROCESSED_DIR / "kpif.csv").exists():
    pytest.skip("data/processed missing", allow_module_level=True)

from kpif_nowcast.component_model import ENERGY_FUEL_ONLY, component_forecast
from kpif_nowcast.data import load_components, load_kpif
from kpif_nowcast.features import load_features
from kpif_nowcast.j5_intervals import METHODS, _conformal, clopper_pearson, sequential

MONTHS = [pd.Period(m, "M") for m in ["2015-06", "2020-04", "2022-09", "2026-10"]]


def _inputs(kpif, comps, feats):
    fc = component_forecast(kpif["index"], comps, feats, {"energy": ENERGY_FUEL_ONLY})["yy_hat"]
    err = (kpif["yy_official"].reindex(fc.index) - fc)
    x = pd.DataFrame({"abs_el": feats["el_chg"].abs(), "abs_fuel": feats["fuel_chg"].abs()})
    return err, x


@pytest.fixture(scope="module")
def data():
    return load_kpif(), load_components(), load_features()


@pytest.mark.parametrize("method", METHODS)
def test_j5_uses_only_deadline_data(data, method):
    kpif, comps, feats = data
    err, x = _inputs(kpif, comps, feats)
    for t in MONTHS:
        e_cut, x_cut = _inputs(kpif.loc[: t - 1], comps[comps["month"] <= t - 1], feats.loc[:t])
        e_cut.loc[t] = 0.0  # placeholder outcome for t (unknown); only used as the row index
        full = sequential(err.loc[:t], x, method, start=str(t))
        live = sequential(e_cut, x_cut, method, start=str(t))
        np.testing.assert_allclose(live.loc[t].to_numpy(), full.loc[t].to_numpy(), rtol=0, atol=1e-10)


def test_conformal_and_ci():
    s = np.arange(1, 101, dtype=float)
    assert _conformal(s, 0.8) == 81.0
    lo, hi = clopper_pearson(80, 100)
    assert 0.70 < lo < 0.72 and 0.87 < hi < 0.89
