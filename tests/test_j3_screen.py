"""J3 information-set test: a screened correction for t is identical with and without data after t's deadline.

Cut: KPIF at t-1, Riksbank vintages published before the deadline, observations with known_from <= deadline.
A fixed subset of series (fast, covers growth / level / balance transforms). Indexing test only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR

if not (PROCESSED_DIR / "kpif.csv").exists():
    pytest.skip("data/processed missing", allow_module_level=True)

from kpif_nowcast import observations as obs
from kpif_nowcast.catalog import CATALOG
from kpif_nowcast.data import load_kpif, load_riksbank_forecasts
from kpif_nowcast.j3_screen import bh, run_h1, run_hk, transform
from kpif_nowcast.riksbank_benchmark import deadline

KEYS = ["brent_sek", "ea_flash_energy", "ki_services", "aku_unemp_nsa"]
MONTHS = [pd.Period(m, "M") for m in ["2018-03", "2021-07", "2023-01", "2026-10"]]


@pytest.fixture(scope="module")
def data():
    units = {s.key: s.unit for s in CATALOG}
    return load_kpif(), load_riksbank_forecasts(), obs.load(), [(k, units[k]) for k in KEYS]


def test_h1_uses_only_deadline_data(data):
    kpif, rb_fc, table, ku = data
    _, full, _ = run_h1(kpif, rb_fc, table, ku)
    for t in MONTHS:
        d = deadline(t)
        _, live, _ = run_h1(kpif.loc[: t - 1], rb_fc[rb_fc["published"] < d], table[table["known_from"] <= d], ku)
        for k in KEYS:
            assert np.isclose(live[k][t], full[k][t], rtol=0, atol=1e-10), f"{k} {t}"


def test_h3_uses_only_origin_data(data):
    from kpif_nowcast.j3_screen import origin_date

    kpif, rb_fc, table, ku = data
    _, full = run_hk(kpif, rb_fc, table, ku, 3)
    for o in [pd.Period("2019-05", "M"), pd.Period("2024-02", "M")]:
        d = origin_date(o)
        _, live = run_hk(kpif.loc[:o], rb_fc[rb_fc["published"] < d], table[table["known_from"] <= d], ku, 3)
        for k in KEYS:
            assert np.isclose(live[k][o], full[k][o], rtol=0, atol=1e-10, equal_nan=True), f"{k} {o}"


def test_transform_rules():
    idx = pd.period_range("2020-01", periods=30, freq="M")
    yy = pd.Series(np.arange(30.0), index=idx)
    assert transform(yy, "x_yy", "%", idx[-1]) == 1.0
    lvl = pd.Series(np.exp(np.arange(30.0) / 100), index=idx)  # constant 1 % growth -> seasonal diff 0
    assert transform(lvl, "lvl", "index", idx[-1]) == pytest.approx(0.0, abs=1e-9)
    assert np.isnan(transform(lvl, "lvl", "index", idx[5]))


def test_bh():
    q = bh(pd.Series({"a": 0.01, "b": 0.04, "c": 0.03}))
    assert q.to_dict() == pytest.approx({"a": 0.03, "c": 0.04, "b": 0.04})
