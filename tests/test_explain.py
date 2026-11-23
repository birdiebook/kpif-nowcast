"""K3 explanations: the parts add up to the forecast, and the explanation for t uses only data known at t's deadline."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR
from kpif_nowcast.explain import COMPONENTS, build_history, error_history, explain_month, to_json
from kpif_nowcast.riksbank_benchmark import deadline
from kpif_nowcast.shadow import SHADOW_MODELS, Inputs

needs_data = pytest.mark.skipif(not (PROCESSED_DIR / "features.csv").exists(), reason="data/processed missing")
MONTHS = pd.PeriodIndex(["2024-01", "2024-11", "2025-01", "2025-08", "2026-03", "2026-10"], freq="M")


@pytest.fixture(scope="module")
def inputs():
    from kpif_nowcast.data import load_components, load_kpif, load_riksbank_forecasts
    from kpif_nowcast.features import load_features

    return Inputs(load_kpif(), load_components(), load_features(), load_riksbank_forecasts())


@pytest.fixture(scope="module")
def history(inputs):
    return build_history(inputs)


def cut(inp: Inputs, t: pd.Period) -> Inputs:
    """Exactly what is known at t's deadline: outcomes to t-1, energy prices for t, earlier vintages."""
    rb = inp.rb_fc[inp.rb_fc["published"] < deadline(t)]
    return Inputs(inp.kpif.loc[: t - 1], inp.comps[inp.comps["month"] <= t - 1], inp.feats.loc[:t], rb)


def assert_same(a, b, path="") -> None:
    if isinstance(a, dict):
        assert set(a) == set(b), f"{path}: keys {set(a) ^ set(b)}"
        for k in a:
            assert_same(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            assert_same(x, y, f"{path}[{i}]")
    elif isinstance(a, float) and isinstance(b, float):
        assert (math.isnan(a) and math.isnan(b)) or math.isclose(a, b, rel_tol=0, abs_tol=1e-10), f"{path}: {a} vs {b}"
    else:
        assert a == b, f"{path}: {a!r} vs {b!r}"


@needs_data
@pytest.mark.parametrize("t", MONTHS, ids=str)
def test_explanation_adds_up(history, t):
    e = explain_month(history, t)
    f, c = e["forecast"], e["components"]
    # same number as the live model (shadow comp_fuel_el = component_fuel_el_v1)
    live = SHADOW_MODELS["comp_fuel_el"].fn(history.inp)
    assert math.isclose(f["yy"], live.at[t, "yy_hat"], abs_tol=1e-12)
    assert math.isclose(sum(c[k]["mm_pp"] for k in COMPONENTS), f["mm_pp"], abs_tol=1e-12)
    for k in COMPONENTS:
        drivers = c[k]["trend_pp"] + c[k]["season_pp"] + c[k].get("el_pp", 0.0) + c[k].get("fuel_pp", 0.0)
        assert math.isclose(drivers, c[k]["mm_pp"], abs_tol=1e-10), k
    # change from last outcome: components + rest, drivers + rest; the rest is only SCB rounding
    assert math.isclose(sum(c[k]["change_yy"] for k in COMPONENTS) + e["change_rest_yy"], f["change_yy"], abs_tol=1e-12)
    assert math.isclose(sum(e["drivers_change_yy"].values()), f["change_yy"], abs_tol=1e-12)
    assert abs(e["change_rest_yy"]) < 0.1 and abs(e["drivers_change_yy"]["rest"]) < 0.1
    # rounded output (JSON) still adds up within rounding
    j = __import__("json").loads(to_json(e))
    assert abs(sum(j["components"][k]["mm_pp"] for k in COMPONENTS) - j["forecast"]["mm_pp"]) < 1e-3
    # error per component after the outcome
    o = e["outcome"]
    assert o is not None
    assert math.isclose(sum(o["per_component_yy"].values()) + o["rest_yy"], o["error_yy"], abs_tol=1e-12)
    assert math.isclose(o["error_yy"], f["yy"] - history.yy_official[t], abs_tol=1e-12)
    assert abs(o["rest_yy"]) < 0.1
    # shadow differences
    s = e["shadows"]
    j2 = s["j2_el_dev"]
    assert math.isclose(j2["diff_from_el_yy"] + j2["diff_from_fuel_yy"], j2["diff_vs_live_yy"], abs_tol=1e-10)
    q = s["j1_comb_equal"]
    assert math.isclose(q["from_riksbank_path"] + q["from_last_rb_miss"] + q["from_j2"], q["diff_vs_live_yy"],
                        abs_tol=1e-10)
    assert math.isclose(q["forecast_yy"], SHADOW_MODELS["j1_comb_equal"].fn(history.inp).at[t, "yy_hat"], abs_tol=1e-10)
    u = e["uncertainty"]
    assert u["band_90"][0] <= u["band_80"][0] <= u["band_50"][0] <= u["band_50"][1] <= u["band_80"][1] <= u["band_90"][1]


@needs_data
@pytest.mark.parametrize("t", MONTHS, ids=str)
def test_explanation_uses_only_deadline_data(inputs, history, t):
    """Everything except the outcome section is identical with and without data after t's deadline."""
    full = explain_month(history, t)
    live = explain_month(build_history(cut(inputs, t)), t)
    assert live["outcome"] is None and live["text_outcome"] == []
    assert full["outcome"] is not None
    for e in (full, live):
        e.pop("outcome")
        e.pop("text_outcome")
    assert_same(full, live)


@needs_data
def test_error_history_adds_up(history):
    h = error_history(history, "2015-01", "2026-10")
    assert h.index.min() == pd.Period("2015-01", "M") and len(h) >= 140
    parts = h[[f"e_{c}" for c in COMPONENTS] + ["e_rest"]].sum(axis=1)
    assert np.allclose(parts, h["error_yy"], atol=1e-12)
    assert h["e_rest"].abs().max() < 0.1
