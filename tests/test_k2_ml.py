"""K2 information-set test: the ML forecast for t is identical with and without data after t's deadline.

Cut: KPIF/components at t-1, energy features and SE3 spot at t, TAB3571 at t-1, Riksbank vintages
published before the deadline, observations with known_from <= deadline. Covers ridge with catalog
series (L), boosting, and the ridge+boosting ensemble.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR

if not (PROCESSED_DIR / "el_contracts.csv").exists():
    pytest.skip("data/processed missing", allow_module_level=True)
pytest.importorskip("sklearn")

from kpif_nowcast.data import load_components, load_el_contracts, load_kpif, load_riksbank_forecasts
from kpif_nowcast.features import load_features
from kpif_nowcast.j2_el import zone_monthly_spot
from kpif_nowcast.k2_ml import MIN_TRAIN, build_design, forecast_at
from kpif_nowcast.observations import load as load_obs
from kpif_nowcast.riksbank_benchmark import deadline

MONTHS = [pd.Period(m, "M") for m in ("2019-06", "2023-02", "2026-10")]
NAMES = ["k2_avg_ridge_l", "k2_rb_hgb_s", "k2_avg_ens_s"]


@pytest.fixture(scope="module")
def data():
    return (load_kpif(), load_components(), load_features(), load_el_contracts(), zone_monthly_spot("SE3"),
            load_riksbank_forecasts(), load_obs())


@pytest.fixture(scope="module")
def full_design(data):
    return build_design(*data)


def test_k2_uses_only_deadline_data(data, full_design):
    warnings.filterwarnings("ignore")
    kpif, comps, feats, contracts, se3, rb_fc, obs = data
    for t in MONTHS:
        d = deadline(t)
        cut = build_design(kpif.loc[: t - 1], comps[comps["month"] <= t - 1], feats.loc[:t],
                           contracts[contracts["month"] <= t - 1], se3.loc[:t],
                           rb_fc[rb_fc["published"] < d], obs[obs["known_from"] <= d])
        assert cut.index.max() == t
        assert np.isnan(cut["actual"].iat[-1])
        for name in NAMES:
            a, b = forecast_at(cut, t, name), forecast_at(full_design, t, name)
            assert np.isclose(a, b, rtol=0, atol=1e-10), f"{name} {t}: {a} vs {b}"


def test_start_value_is_5050(full_design):
    d = full_design
    i = 5
    assert i < MIN_TRAIN
    for name in NAMES:
        assert np.isclose(forecast_at(d, d.index[i], name), d["avg"].iat[i])
