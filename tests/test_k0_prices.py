"""K0: catalog entries, cache logic, data quality and the information set of the screen and variants."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast import catalog_prices as cp
from kpif_nowcast.catalog import AREAS, CATALOG


def test_specs_unique_and_complete():
    keys = [s.key for s in CATALOG]
    assert len(keys) == len(set(keys))
    for s in cp.specs():
        assert s.area in AREAS and s.freq == "M" and s.source and s.lag_days >= 1


def test_revised_flags():
    sp = {s.key: s for s in cp.specs()}
    assert all(sp[k].revised for k in sp if k.startswith("ppi_") or k.endswith("_usd"))
    assert not sp["kpif_xe_index"].revised and sp["kpif_goods_index"].revised
    assert not any(sp[k].revised for k in sp if k.startswith(("ki_", "gvb_", "swestr")))


def test_fresh_cache_age(tmp_path, monkeypatch):
    monkeypatch.setattr(cp, "RAW_DIR", tmp_path / "k0")
    monkeypatch.setattr(cp, "MAIN_RAW", tmp_path)
    (tmp_path / "k0").mkdir()
    (tmp_path / "k0" / "fred_X_20261101.csv").write_text("a")
    (tmp_path / "fred_X_20261120.csv").write_text("b")
    assert cp._fresh("fred_X_*.csv", today=date(2026, 11, 23)).name == "fred_X_20261120.csv"
    assert cp._fresh("fred_X_*.csv", today=date(2026, 12, 30)) is None


def test_choose_rule():
    from kpif_nowcast.k0_screen import choose

    prim = pd.DataFrame({"p1": [0.01, 0.02, 0.03, 0.04, 0.05], "bh_q": [0.05, 0.5, 0.5, 0.5, 0.5]},
                        index=["ppi_a", "ppi_b", "ki_a", "coffee_usd", "gvb_2y"])
    chosen, tag = choose(prim)
    assert chosen == ["ppi_a", "ki_a", "coffee_usd"] and tag == "1 of 3 survived BH"


# ---------------------------------------------------------------- with data

from kpif_nowcast.data import PROCESSED_DIR  # noqa: E402

needs_data = pytest.mark.skipif(not (PROCESSED_DIR / "kpif.csv").exists(), reason="data/processed missing")


@pytest.fixture(scope="module")
def table():
    from kpif_nowcast import observations as obs

    t = obs.load()
    if not set(cp.keys()) <= set(t["series"]):
        pytest.skip("K0 series not fetched")
    return t


@needs_data
def test_quality(table):
    q = cp.quality(table)
    assert (q["rows"] > 0).all()
    assert (q["holes"] == 0).all() and (q["dup_keys"] == 0).all() and (q["kf_before_end"] == 0).all()


KEYS = ["ppi_impi_food", "ki_prices_grocery", "kpif_xe_index", "gvb_2y"]
MONTHS = [pd.Period(m, "M") for m in ["2018-03", "2021-07", "2023-01", "2026-10"]]


@needs_data
def test_screen_and_combination_use_only_deadline_data(table):
    from kpif_nowcast.catalog import by_key
    from kpif_nowcast.data import load_kpif, load_riksbank_forecasts
    from kpif_nowcast.j3_screen import combined_h1, run_h1
    from kpif_nowcast.riksbank_benchmark import deadline

    kpif, rb_fc = load_kpif(), load_riksbank_forecasts()
    ku = [(k, by_key()[k].unit) for k in KEYS]
    f, full, xs = run_h1(kpif, rb_fc, table, ku)
    combo = combined_h1(f, xs, KEYS[:3])
    for t in MONTHS:
        d = deadline(t)
        fl, live, xl = run_h1(kpif.loc[: t - 1], rb_fc[rb_fc["published"] < d], table[table["known_from"] <= d], ku)
        for k in KEYS:
            assert np.isclose(live[k][t], full[k][t], rtol=0, atol=1e-10), f"{k} {t}"
        cl = combined_h1(fl, xl, KEYS[:3])
        assert np.isclose(cl[t], combo[t], rtol=0, atol=1e-10), f"combo {t}"


@needs_data
def test_c2_correction_uses_only_past_rows(table):
    """K0-C2: the 50/50 base is tested in test_j1_hybrid; here the correction on top of a base must not
    depend on later rows or on observations after the deadline."""
    from kpif_nowcast.catalog import by_key
    from kpif_nowcast.data import load_kpif, load_riksbank_forecasts
    from kpif_nowcast.j3_screen import combined_h1, feature
    from kpif_nowcast.riksbank_benchmark import deadline

    kpif = load_kpif()
    idx = pd.period_range("2015-01", "2026-10", freq="M")
    rng = np.random.default_rng(0)
    f = pd.DataFrame({"base": kpif["yy_official"].shift(1).reindex(idx) + rng.normal(0, 0.1, len(idx)),
                      "actual": kpif["yy_official"].reindex(idx)})
    keys = KEYS[:3]
    dates = {t: deadline(t) for t in idx}
    xs = {k: feature(k, by_key()[k].unit, table, dates, {t: t for t in idx}) for k in keys}
    full = combined_h1(f, xs, keys)
    for t in MONTHS:
        d = deadline(t)
        cut = table[table["known_from"] <= d]
        fl = f.loc[:t].copy()
        fl.loc[t, "actual"] = np.nan  # outcome of t not known at its deadline
        xl = {k: feature(k, by_key()[k].unit, cut, {s: dates[s] for s in fl.index}, {s: s for s in fl.index})
              for k in keys}
        assert np.isclose(combined_h1(fl, xl, keys)[t], full[t], rtol=0, atol=1e-10), f"{t}"
