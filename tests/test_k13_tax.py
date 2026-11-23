"""K13 information-set tests.

1. With no events the cleaned model equals J2 V2 / the live component model exactly.
2. The forecast for t is identical with and without data after t's deadline: KPIF, components and KS tax
   effects at t-1, energy features and SE3 at t, TAB3571 at t-1, Riksbank vintages before the deadline,
   observations known by the deadline.
3. Tax events are used only when decided before the deadline (add-back and history cleaning).
"""

from __future__ import annotations

import warnings
from dataclasses import replace
from datetime import date

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR

if not (PROCESSED_DIR / "tax_effects.csv").exists() or not (PROCESSED_DIR / "el_contracts.csv").exists():
    pytest.skip("data/processed missing", allow_module_level=True)
pytest.importorskip("sklearn")

from kpif_nowcast.component_model import ENERGY, component_forecast
from kpif_nowcast.data import (load_components, load_el_contracts, load_kpif, load_riksbank_forecasts,
                               load_tax_effects)
from kpif_nowcast.features import load_features
from kpif_nowcast.j2_el import build_j2_features, j2_forecast, zone_monthly_spot
from kpif_nowcast.k13_tax import (EVENTS, TaxEvent, addback, clean_component_forecast, clean_design, j2_clean,
                                  ks_parts)
from kpif_nowcast.k2_ml import K2Runner, build_design
from kpif_nowcast.observations import load as load_obs
from kpif_nowcast.riksbank_benchmark import deadline

MONTHS = [pd.Period(m, "M") for m in ("2016-03", "2022-05", "2022-10", "2026-04", "2026-07", "2026-10")]


@pytest.fixture(scope="module")
def data():
    return dict(kpif=load_kpif(), comps=load_components(), feats=load_features(), contracts=load_el_contracts(),
                se3=zone_monthly_spot("SE3"), rb_fc=load_riksbank_forecasts(), obs=load_obs(),
                tax=load_tax_effects())


def _cut(d: dict, t: pd.Period) -> dict:
    dl = deadline(t)
    return dict(kpif=d["kpif"].loc[: t - 1], comps=d["comps"][d["comps"]["month"] <= t - 1],
                feats=d["feats"].loc[:t], contracts=d["contracts"][d["contracts"]["month"] <= t - 1],
                se3=d["se3"].loc[:t], rb_fc=d["rb_fc"][d["rb_fc"]["published"] < dl],
                obs=d["obs"][d["obs"]["known_from"] <= dl], tax=d["tax"].loc[: t - 1])


def _j2c(d: dict, events=EVENTS) -> pd.DataFrame:
    j2f = build_j2_features(d["feats"], d["contracts"], d["se3"])
    return j2_clean(d["kpif"]["index"], d["comps"], j2f, d["tax"], events)


def test_no_events_equals_raw_models(data):
    d = data
    j2f = build_j2_features(d["feats"], d["contracts"], d["se3"])
    raw = j2_forecast(d["kpif"]["index"], d["comps"], j2f, "j2_el_dev")["yy_hat"]
    mine = j2_clean(d["kpif"]["index"], d["comps"], j2f, None, [])["yy_hat"]
    pd.testing.assert_series_equal(raw, mine.reindex(raw.index), check_names=False, atol=1e-12, rtol=0)
    live = component_forecast(d["kpif"]["index"], d["comps"], d["feats"], {"energy": ENERGY})["yy_hat"]
    mine = clean_component_forecast(d["kpif"]["index"], d["comps"], d["feats"], {"energy": ENERGY}, None,
                                    [])["yy_hat"]
    pd.testing.assert_series_equal(live, mine.reindex(live.index), check_names=False, atol=1e-12, rtol=0)


def test_j2_clean_uses_only_deadline_data(data):
    full = _j2c(data)
    for t in MONTHS:
        cut = _j2c(_cut(data, t))
        for col in ("yy_hat", "mm_hat_pp", "tax_addback", "fc_energy", "fc_food"):
            a, b = full.at[t, col], cut.at[t, col]
            assert np.isfinite(a), f"{col} {t}"
            assert np.isclose(a, b, rtol=0, atol=1e-10), f"{col} {t}: {a} vs {b}"


def test_live_model_clean_uses_only_deadline_data(data):
    def run(d):
        return clean_component_forecast(d["kpif"]["index"], d["comps"], d["feats"], {"energy": ENERGY},
                                        d["tax"], EVENTS)["yy_hat"]
    full = run(data)
    for t in (pd.Period("2026-07", "M"), pd.Period("2026-10", "M")):
        assert np.isclose(full[t], run(_cut(data, t))[t], rtol=0, atol=1e-10)


def test_ensemble_clean_uses_only_deadline_data(data):
    warnings.filterwarnings("ignore")

    def run(d, t):
        des = build_design(d["kpif"], d["comps"], d["feats"], d["contracts"], d["se3"], d["rb_fc"], d["obs"],
                           with_catalog=False)
        dc = clean_design(des, _j2c(d))
        return K2Runner(dc).forecast("k2_avg_ens_s", dc.index.get_loc(t))

    for t in (pd.Period("2026-04", "M"), pd.Period("2026-10", "M")):
        a, b = run(data, t), run(_cut(data, t), t)
        assert np.isclose(a, b, rtol=0, atol=1e-10), f"{t}: {a} vs {b}"


def test_events_only_after_decision(data):
    parts = ks_parts(data["tax"], data["comps"])
    cols = ["capital_stock", "energy", "food", "goods", "services"]
    t = pd.Period("2026-04", "M")
    vat = next(e for e in EVENTS if e.month == "2026-04")
    assert addback(t, parts, [vat], cols)["food"] == pytest.approx(vat.pe)
    # decided on or after the deadline (2026-05-04): not used
    late = replace(vat, decided=deadline(t).date())
    assert (addback(t, parts, [late], cols) == 0).all()
    just_before = replace(vat, decided=date(2026, 5, 3))
    assert addback(t, parts, [just_before], cols)["food"] == pytest.approx(vat.pe)
    # a late decision also removes the event from history cleaning: forecast for 2026-05 equals no-event run
    nxt = t + 1
    a = _j2c(data, [late]).at[nxt, "yy_hat"]
    b = _j2c(data, []).at[nxt, "yy_hat"]
    c = _j2c(data, [vat]).at[nxt, "yy_hat"]
    assert np.isclose(a, b, atol=1e-12) and not np.isclose(a, c, atol=1e-6)
    # an event in a future month never touches the forecast for t
    future = TaxEvent("2026-12", "energy", "en", "start", date(2026, 6, 30), "test", pe=1.0)
    assert np.isclose(_j2c(data, [future]).at[pd.Period("2026-10", "M"), "yy_hat"],
                      _j2c(data, []).at[pd.Period("2026-10", "M"), "yy_hat"], atol=1e-12)


def test_end_event_uses_start_month_only(data):
    parts = ks_parts(data["tax"], data["comps"])
    cols = ["capital_stock", "energy", "food", "goods", "services"]
    end = next(e for e in EVENTS if e.month == "2026-10")
    cut_parts = parts.loc[:"2026-09"]
    assert addback(end.period, parts, EVENTS, cols)["energy"] == pytest.approx(-parts.at[pd.Period("2026-05", "M"),
                                                                                         "en"])
    assert addback(end.period, cut_parts, EVENTS, cols)["energy"] == addback(end.period, parts, EVENTS, cols)["energy"]


def test_calendar_decided_before_effect():
    for e in EVENTS:
        assert pd.Timestamp(e.decided) < e.period.to_timestamp(), e.label
        assert (e.kind == "start") == (e.pe is not None) and (e.kind == "end") == (e.start_of is not None)
