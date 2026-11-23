"""K9 information-set test: the forecast for origin o is identical with and without data after o's forecast date.

Cut: observations with known_from <= forecast date (day 4 of o+2), Riksbank rounds published before it.
Covers all four preregistered variants (ridge h=3 and h=12, shrink h=12, miss h=6).
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR
from kpif_nowcast.observations import PATH as OBS_PATH

if not (PROCESSED_DIR / "riksbank_kpif_forecasts.csv").exists() or not OBS_PATH.exists():
    pytest.skip("data missing", allow_module_level=True)
pytest.importorskip("sklearn")

from kpif_nowcast import k9_horizon as k9
from kpif_nowcast.data import load_riksbank_forecasts
from kpif_nowcast.horizon import origin_date
from kpif_nowcast.observations import load as load_obs

ORIGINS = {"k9_ridge_h3": "2022-05", "k9_ridge_h12": "2023-03", "k9_shrink_h12": "2022-09", "k9_miss_h6": "2021-11"}


@pytest.fixture(scope="module")
def data():
    table = load_obs()
    return table[table["series"].isin(k9.SERIES)], load_riksbank_forecasts()


@pytest.fixture(scope="module")
def designs(data):
    table, rb = data
    return {h: k9.build_design(h, table, rb) for h in (3, 6, 12)}


@pytest.mark.parametrize("name", list(k9.VARIANTS))
def test_forecast_uses_only_data_known_at_forecast_date(name, data, designs):
    warnings.filterwarnings("ignore")
    table, rb = data
    v = k9.VARIANTS[name]
    o = pd.Period(ORIGINS[name], "M")
    d = origin_date(o)
    full, params = k9.forecast(designs[v.h], o, v.kind, v.h)
    assert params["active"], "test origin must be after the start rule"
    cut = k9.forecast_at(name, o, table[table["known_from"] <= d], rb[rb["published"] < d])
    assert np.isclose(full, cut, atol=1e-10)


def test_falls_back_to_riksbank_before_start(designs):
    d = designs[12]
    o = d.index[5]
    for kind in ("ridge", "shrink"):
        f, p = k9.forecast(d, o, kind, 12)
        assert not p["active"] and f == d.at[o, "rb"]


def test_training_rows_have_published_targets(designs):
    d = designs[12]
    o = pd.Period("2022-01", "M")
    assert (k9.train_rows(d, o)["target"] <= o).all()


def test_dm_hac_sign_and_holm():
    rng = np.random.default_rng(0)
    e_b = rng.normal(0, 1, 200)
    r = k9.dm_hac(e_b * 0.5, e_b, h=3)
    assert r["diff"] < 0 and r["p1"] < 0.01
    p = pd.Series({"a": 0.01, "b": 0.04, "c": 0.5})
    assert list(k9.holm(p).round(3)) == [0.03, 0.08, 0.5]
