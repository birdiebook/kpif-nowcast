"""K7 information-set test: each variant's forecast for t is identical with and without data after t's deadline.

Cut: KPIF/components at t-1, energy features and SE3 spot at t, TAB3571 at t-1, Riksbank vintages published
before the deadline, observations with known_from <= deadline. The calendar (Easter) is known in advance.
"""

from __future__ import annotations

import warnings
from datetime import date

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
from kpif_nowcast.k7_services import (VARIANTS, build_k7, easter_days, seasonal_trend_median,
                                      services_forecast, services_regressors)
from kpif_nowcast.observations import load as load_obs
from kpif_nowcast.riksbank_benchmark import deadline

MONTHS = [pd.Period(m, "M") for m in ("2016-04", "2019-08", "2023-01", "2026-10")]


@pytest.fixture(scope="module")
def data():
    return (load_kpif(), load_components(), load_features(), load_el_contracts(), zone_monthly_spot("SE3"),
            load_riksbank_forecasts(), load_obs())


def _cut(data, t):
    kpif, comps, feats, contracts, se3, rb_fc, obs = data
    d = deadline(t)
    return (kpif.loc[: t - 1], comps[comps["month"] <= t - 1], feats.loc[:t], contracts[contracts["month"] <= t - 1],
            se3.loc[:t], rb_fc[rb_fc["published"] < d], obs[obs["known_from"] <= d])


@pytest.fixture(scope="module")
def full(data):
    # K2 only for the tested months (row positions), so the test stays fast
    probe = build_k7(*data, k2_rows=None)
    return build_k7(*data, k2_rows=[probe.index.get_loc(t) for t in MONTHS])


def test_k7_uses_only_deadline_data(data, full):
    warnings.filterwarnings("ignore")
    for t in MONTHS:
        cut = _cut(data, t)
        live = build_k7(*cut, k2_rows=[-1])
        assert live.index.max() == t and np.isnan(live["actual"].iat[-1])
        for name in VARIANTS:
            a, b = live[name].iat[-1], full.loc[t, name]
            assert np.isfinite(a) and np.isclose(a, b, rtol=0, atol=1e-10), f"{name} {t}: {a} vs {b}"


def test_services_forecast_past_only(data):
    comps = data[1]
    t = pd.Period("2021-08", "M")
    for m in ("A", "B"):
        full = services_forecast(comps, m)["fc"]
        live = services_forecast(comps[comps["month"] <= t - 1], m)["fc"]
        assert live.index.max() == t
        assert np.isclose(live[t], full[t], rtol=0, atol=1e-12)


def test_median_seasonal_ignores_one_outlier_year():
    idx = pd.period_range("2000-01", periods=12 * 7, freq="M")
    x = pd.Series(np.tile(np.r_[1.0, np.zeros(11)], 7), index=idx)
    x.iloc[12 * 4] = 50.0  # one abnormal January
    f = seasonal_trend_median(x)
    # January in year 7: four normal Januaries and one outlier in the window -> median ignores the outlier
    dev_normal = 1.0 - 1.0 / 12
    assert f.iloc[12 * 6] == pytest.approx(x.iloc[12 * 5: 12 * 6].mean() + dev_normal)


def test_easter_days_and_regressors(data):
    e = easter_days(pd.period_range("2019-01", "2019-12", freq="M"))  # Easter 2019-04-21
    assert e.sum() == 11 and e[pd.Period("2019-04", "M")] == 11
    e16 = easter_days(pd.period_range("2016-03", "2016-04", freq="M"))  # Easter 2016-03-27
    assert e16.tolist() == [11.0, 0.0]
    regs = services_regressors(data[1], pd.Period("2026-11", "M"))
    assert (regs.loc[regs.index.month != 1, "jan_dev"] == 0).all()
    assert regs.loc["1995-01":, "jan_dev"].notna().all()
