"""K8 information-set test: the food correction and total forecast for t are identical with and without data
after t's deadline.

Cut: KPIF/components at t-1, energy features and SE3 spot at t, TAB3571 at t-1, Riksbank vintages published
before the deadline, observations with known_from <= deadline, SEK/USD daily fixings up to the deadline.
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
from kpif_nowcast.j1_hybrid import build_panel
from kpif_nowcast.j2_el import zone_monthly_spot
from kpif_nowcast.k8_food import (FIXED_COLS, build_food_design, corrections, forecast_at, ridge_cols,
                                  sekusd_daily)
from kpif_nowcast.observations import load as load_obs
from kpif_nowcast.riksbank_benchmark import deadline

MONTHS = [pd.Period(m, "M") for m in ("2016-03", "2022-07", "2026-10")]


@pytest.fixture(scope="module")
def data():
    return (load_kpif(), load_components(), load_features(), load_el_contracts(), zone_monthly_spot("SE3"),
            load_riksbank_forecasts(), load_obs(), sekusd_daily())


def test_k8_uses_only_deadline_data(data):
    warnings.filterwarnings("ignore")
    kpif, comps, feats, contracts, se3, rb_fc, obs, fx = data
    panel = build_panel(kpif, comps, feats, contracts, se3, rb_fc, obs)
    for t in MONTHS:
        dl = deadline(t)
        full = forecast_at(kpif, comps, obs, fx, panel, t)
        kc, cc, oc = kpif.loc[: t - 1], comps[comps["month"] <= t - 1], obs[obs["known_from"] <= dl]
        pc = build_panel(kc, cc, feats.loc[:t], contracts[contracts["month"] <= t - 1], se3.loc[:t],
                         rb_fc[rb_fc["published"] < dl], oc)
        cut = forecast_at(kc, cc, oc, fx[fx.index <= dl], pc, t)
        assert set(full) == set(cut)
        for k in full:
            assert np.isfinite(full[k]), f"{k} {t}"
            assert np.isclose(full[k], cut[k], rtol=0, atol=1e-10), f"{k} {t}: {full[k]} vs {cut[k]}"


def test_features_complete_and_zero_start(data):
    kpif, comps, *_, obs, fx = data
    d = build_food_design(kpif, comps, obs, fx, last=pd.Period("2026-10", "M"))
    assert not d.loc["2008-01":, ridge_cols() + FIXED_COLS].isna().any().any()
    c = corrections(d, pd.PeriodIndex([d.index[10]]))
    assert (c.to_numpy() == 0).all()  # fewer than MIN_TRAIN rows: no correction
