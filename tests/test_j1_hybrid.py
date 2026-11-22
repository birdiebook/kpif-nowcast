"""J1 information-set test: the hybrid forecast for t is identical with and without data after t's deadline.

Cut: KPIF/components at t-1, energy features and SE3 spot at t, TAB3571 at t-1, Riksbank vintages
published before the deadline, observations with known_from <= deadline. Indexing test only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR

if not (PROCESSED_DIR / "el_contracts.csv").exists():
    pytest.skip("data/processed missing", allow_module_level=True)

from kpif_nowcast.data import load_components, load_el_contracts, load_kpif, load_riksbank_forecasts
from kpif_nowcast.features import load_features
from kpif_nowcast.j1_hybrid import VARIANTS, build_panel, j1_forecast
from kpif_nowcast.j2_el import zone_monthly_spot
from kpif_nowcast.observations import load as load_obs
from kpif_nowcast.riksbank_benchmark import deadline

MONTHS = pd.period_range("2015-03", "2026-10", freq="M")[::13]


@pytest.fixture(scope="module")
def data():
    return (load_kpif(), load_components(), load_features(), load_el_contracts(), zone_monthly_spot("SE3"),
            load_riksbank_forecasts(), load_obs())


@pytest.fixture(scope="module")
def full(data):
    panel = build_panel(*data)
    return panel, {v: j1_forecast(panel, v) for v in VARIANTS}


def test_j1_uses_only_deadline_data(data, full):
    kpif, comps, feats, contracts, se3, rb_fc, obs = data
    _, full_fc = full
    for t in MONTHS:
        d = deadline(t)
        panel = build_panel(kpif.loc[: t - 1], comps[comps["month"] <= t - 1], feats.loc[:t],
                            contracts[contracts["month"] <= t - 1], se3.loc[:t],
                            rb_fc[rb_fc["published"] < d], obs[obs["known_from"] <= d])
        assert panel.index.max() == t
        for v in VARIANTS:
            live = j1_forecast(panel, v)
            assert np.isclose(live[t], full_fc[v][t], rtol=0, atol=1e-10), f"{v} {t}: {live[t]} vs {full_fc[v][t]}"


def test_parameter_free_variants(full):
    panel, fc = full
    np.testing.assert_allclose(fc["j1_comb_equal"], 0.5 * panel["rb_updated"] + 0.5 * panel["j2"])
    np.testing.assert_allclose(fc["j1_hyb_energy_fixed"], panel["rb_updated"] + panel["energy_news"])
