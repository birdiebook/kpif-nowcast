"""Indexing test: each forecast for month t must be reproducible from data cut at the deadline.

We cut KPIF and components at t-1 and features at t (this month's energy prices
are known at the deadline), rerun the model, and require exactly the same forecast
as in the full-sample backtest. This catches code that accidentally reads month t's
outcome or later rows (a shift in the wrong direction, a feature computed over
the whole period).

It is an indexing test, NOT a leakage test: the data on disk is today's vintage,
so revised figures or re-estimated series would pass unnoticed.

Needs data/processed (python -m kpif_nowcast.data); skipped otherwise.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR

if not (PROCESSED_DIR / "kpif.csv").exists():
    pytest.skip("data/processed missing: run python -m kpif_nowcast.data", allow_module_level=True)

from kpif_nowcast.baselines import all_baselines
from kpif_nowcast.component_model import ENERGY, ENERGY_FUEL_ONLY, component_forecast
from kpif_nowcast.data import load_components, load_kpif, load_riksbank_forecasts
from kpif_nowcast.features import load_features
from kpif_nowcast.riksbank_benchmark import deadline, riksbank_at_deadline

M = lambda s: pd.Period(s, "M")  # noqa: E731
MONTHS_LONG = pd.period_range("2015-01", "2026-10", freq="M")[::7]  # fixed sample, not random
MONTHS_EL = pd.period_range("2024-01", "2026-10", freq="M")[::4]  # electricity only from 2021-11


@pytest.fixture(scope="module")
def data():
    return load_kpif(), load_components(), load_features(), load_riksbank_forecasts()


def cut(kpif, comps, feats, t):
    return kpif.loc[: t - 1], comps[comps["month"] <= t - 1], feats.loc[:t]


@pytest.mark.parametrize("spec_name, months", [("fuel", MONTHS_LONG), ("fuel_el", MONTHS_EL)])
def test_component_model_uses_only_deadline_data(data, spec_name, months):
    kpif, comps, feats, _ = data
    spec = {"energy": ENERGY_FUEL_ONLY if spec_name == "fuel" else ENERGY}
    full = component_forecast(kpif["index"], comps, feats, spec)["yy_hat"]
    for t in months:
        k, c, f = cut(kpif, comps, feats, t)
        live = component_forecast(k["index"], c, f, spec)["yy_hat"]
        assert live.index.max() == t, f"{t}: cut data should forecast exactly month t"
        assert np.isclose(live[t], full[t], rtol=0, atol=1e-10), f"{spec_name} {t}: {live[t]} vs {full[t]}"


def test_baselines_use_only_t_minus_1(data):
    kpif = data[0]
    full = all_baselines(kpif["index"])
    for t in MONTHS_LONG:
        idx = kpif["index"].loc[: t - 1].reindex(pd.period_range(kpif.index.min(), t, freq="M"))
        live = all_baselines(idx).loc[t]
        np.testing.assert_allclose(live.to_numpy(), full.loc[t].to_numpy(), rtol=0, atol=1e-10)


def test_rb_updated_uses_only_published_vintages_and_t_minus_1(data):
    kpif, _, _, rb_fc = data
    actual = kpif["yy_official"]
    full = riksbank_at_deadline(rb_fc, kpif.index, actual)
    for t in MONTHS_LONG.intersection(full.index):  # some months have no usable vintage
        live = riksbank_at_deadline(rb_fc[rb_fc["published"] < deadline(t)], pd.PeriodIndex([t]), actual.loc[: t - 1])
        assert live.loc[t, "rb_updated"] == pytest.approx(full.loc[t, "rb_updated"], abs=1e-12)
        assert live.loc[t, "riksbank"] == full.loc[t, "riksbank"]


def test_rb_updated_golden_numbers_fixed_window(data):
    """Locked to 2015-01..2026-10 so new months do not move the numbers."""
    kpif, _, _, rb_fc = data
    actual = kpif["yy_official"]
    rb = riksbank_at_deadline(rb_fc, kpif.index, actual).loc[M("2015-01") : M("2026-10")]
    err = rb[["riksbank", "rb_updated"]].sub(actual.reindex(rb.index), axis=0).dropna()
    assert len(err) == 141
    assert err["riksbank"].abs().mean() == pytest.approx(0.320, abs=1e-3)
    assert err["rb_updated"].abs().mean() == pytest.approx(0.256, abs=1e-3)
    one_month = rb["rb_months_ahead"] == 1
    assert (rb.loc[one_month, "rb_updated"] == rb.loc[one_month, "riksbank"]).all()
