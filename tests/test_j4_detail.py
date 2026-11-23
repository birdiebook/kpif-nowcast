"""J4 information-set test: the detail forecast for t is identical with and without data after t's deadline.

Cut: KPIF and TAB6613 detail at t-1, energy features at t. Indexing test only (TAB6613 is back-calculated).
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR

if not (PROCESSED_DIR / "cpif_detail.csv").exists():
    pytest.skip("data/processed missing", allow_module_level=True)

from kpif_nowcast.data import load_cpif_detail, load_kpif
from kpif_nowcast.features import load_features
from kpif_nowcast.j4_detail import VARIANTS, easter, j4_forecast, regressors

MONTHS = pd.period_range("2015-02", "2026-10", freq="M")[::17]


@pytest.fixture(scope="module")
def data():
    return load_kpif(), load_cpif_detail(), load_features()


@pytest.mark.parametrize("variant", list(VARIANTS))
def test_j4_uses_only_deadline_data(data, variant):
    kpif, detail, feats = data
    full = j4_forecast(kpif["index"], detail, regressors(feats), variant)["yy_hat"]
    for t in MONTHS:
        live = j4_forecast(kpif["index"].loc[: t - 1], detail[detail["month"] <= t - 1],
                           regressors(feats.loc[:t]), variant)["yy_hat"]
        assert live.index.max() == t
        assert np.isclose(live[t], full[t], rtol=0, atol=1e-10), f"{variant} {t}"


def test_easter_dates():
    assert easter(2024) == date(2024, 3, 31)
    assert easter(2025) == date(2025, 4, 20)
    assert easter(2019) == date(2019, 4, 21)
