"""V2 (run 3 wave 2): candidate list, selection rule, date rules, information set and reproducibility."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast import v2_screen as v2

NEW_MODULES = ("catalog_travel", "catalog_rents", "catalog_prospera", "catalog_el", "catalog_fx", "catalog_flash")


def _new_keys() -> list[str]:
    import importlib

    out = []
    for m in NEW_MODULES:
        out += importlib.import_module(f"kpif_nowcast.{m}").keys()
    return out


def test_candidates_cover_all_new_series_once():
    new = _new_keys()
    assert len(new) == 35
    assert set(v2.CANDIDATES) | set(v2.EXCLUDED) == set(new)
    assert not set(v2.CANDIDATES) & set(v2.EXCLUDED)
    assert len(v2.CANDIDATES) == 10 and len(v2.EXCLUDED) == 25
    assert {g for g, _ in v2.CANDIDATES.values()} == {"resor", "hyror", "el", "kronan"}


def test_j3_screen_keys_frozen_before_run3():
    """Registered J3 must not change when the catalog grows: frozen list = current monthly series minus run 3's."""
    from kpif_nowcast.j3_screen import screen_keys

    frozen = screen_keys()
    assert len(frozen) == 77
    assert frozen == [k for k in screen_keys(frozen=False) if k not in set(_new_keys())]


def test_k12_includes_run3():
    from kpif_nowcast import k12_global as k12

    assert ("v2_", "V2") in k12.TRACK_PREFIX
    assert "v2" in k12.FAMILIES and "v2_screen" in k12.FAMILIES["v2"][0]
    assert k12.track_of("v2_r_corr", "v2") == "V2" and k12.track_of(v2.SHADOW_NAME, "v2") == "ref"


def _prim(rows: dict) -> pd.DataFrame:
    return pd.DataFrame(rows, index=["p1", "bh_q", "diff"]).T


def test_choose_rule():
    prim = _prim({
        "sek_usd": [0.20, 0.50, -0.002],
        "kpif_package_holidays_index": [0.01, 0.08, -0.010],  # BH survivor
        "easter_window_days": [0.005, 0.20, -0.012],  # lowest raw p, but not a BH survivor, same group
        "kpi_rent_index": [0.03, 0.15, -0.004],
        "sek_eur": [0.02, 0.09, -0.003],  # BH survivor
        "el_contract_spot_share": [0.6, 0.9, 0.001],  # worsens the base: never chosen
    })
    chosen, tag = v2.choose(prim)
    assert chosen == ["kpif_package_holidays_index", "sek_eur", "kpi_rent_index"]
    assert tag == "2 av 3 överlevde BH"
    # eligibility (coverage rule) and the "only negative difference" rule
    chosen, tag = v2.choose(prim, eligible={"el_contract_spot_share", "sek_usd"})
    assert chosen == ["sek_usd"] and tag == "ingen överlevde BH"
    assert v2.choose(prim, eligible={"el_contract_spot_share"}) == ([], "ingen kandidat")


def test_variant_numbers():
    assert v2.variant_numbers(["v2_r_corr", "v2_a_corr"]) == {"v2_r_corr": 52, "v2_a_corr": 53}
    assert v2.variant_numbers(["v2_a_corr"]) == {"v2_a_corr": 52}


def _series(start: str, end: str, seed: int = 0) -> pd.Series:
    idx = pd.period_range(start, end, freq="M")
    return pd.Series(100 + np.random.default_rng(seed).normal(0, 1, len(idx)).cumsum(), index=idx)


def test_stale_rule():
    s = _series("2010-01", "2023-04")
    t = pd.Period("2023-07", "M")  # lag 1: p* = t-3 is still allowed (lag + 2)
    assert not np.isnan(v2.x_value("kpi_rent_index", "2020=100", s, t))
    assert np.isnan(v2.x_value("kpi_rent_index", "2020=100", s, t + 1))
    # guest nights: lag 3, so t - p* = 5 allowed, 6 not
    assert not np.isnan(v2.x_value("guest_nights_domestic", "tusental", s, pd.Period("2023-09", "M")))
    assert np.isnan(v2.x_value("guest_nights_domestic", "tusental", s, pd.Period("2023-10", "M")))


def test_break_rule():
    s = _series("2010-01", "2026-10")
    unit = "% av hushållens avtal"
    for p in ("2023-02", "2024-02"):  # the transform spans 2023-01 -> 2023-02
        assert np.isnan(v2.x_value("el_contract_spot_share", unit, s.loc[:p], pd.Period(p, "M") + 1))
    for p in ("2023-01", "2023-03", "2024-01", "2024-03"):
        x = v2.x_value("el_contract_spot_share", unit, s.loc[:p], pd.Period(p, "M") + 1)
        from kpif_nowcast.j3_screen import transform

        assert x == transform(s.loc[:p], "el_contract_spot_share", unit, pd.Period(p, "M") + 1)
    # other series are not affected by the break
    assert not np.isnan(v2.x_value("kpi_rent_index", "2020=100", s.loc[:"2023-02"], pd.Period("2023-03", "M")))


# ---------------------------------------------------------------- with data

from kpif_nowcast.data import PROCESSED_DIR  # noqa: E402

needs_data = pytest.mark.skipif(not (PROCESSED_DIR / "kpif.csv").exists(), reason="data/processed missing")
MONTHS = [pd.Period(m, "M") for m in ["2018-03", "2021-07", "2023-03", "2024-01", "2026-10"]]
IDX = pd.period_range("2015-01", "2026-10", freq="M")


@pytest.fixture(scope="module")
def table():
    from kpif_nowcast import observations as obs

    t = obs.load()
    if not set(v2.CANDIDATES) <= set(t["series"]):
        pytest.skip("run 3 series not fetched")
    return t


@pytest.fixture(scope="module")
def xs_full(table):
    return v2.features(table, IDX)


@needs_data
def test_rules_on_data(xs_full):
    xs, ps = xs_full
    el = xs["el_contract_spot_share"]
    assert el.loc["2023-08":"2024-07"].isna().all() and len(el.loc["2023-08":"2024-07"]) == 12
    assert np.isnan(el[pd.Period("2023-03", "M")])
    assert el.loc["2017-02":"2023-02"].notna().all() and el.loc["2024-09":].notna().all()
    assert str(ps.loc[pd.Period("2024-01", "M"), "el_contract_spot_share"]) == "2023-04"
    cov = v2.coverage(xs)
    assert cov["ok"].all()
    for k in v2.CANDIDATES:
        if k != "el_contract_spot_share":
            assert xs[k].loc["2015-01":].notna().all(), k


@needs_data
def test_known_at_deadline(table, xs_full):
    _, ps = xs_full
    dev = v2.check_known_at_deadline(ps, table)
    assert (dev["kind"] != "unknown").all()
    assert set(dev["series"]) <= {"el_contract_spot_share"}
    for t in MONTHS:
        for k, (_, lag) in v2.CANDIDATES.items():
            if k != "el_contract_spot_share":
                assert ps.loc[t, k] == t - lag, (k, t)


@needs_data
def test_features_identical_on_cut_table(table, xs_full):
    from kpif_nowcast.riksbank_benchmark import deadline

    xs, _ = xs_full
    for t in MONTHS:
        cut = table[table["known_from"] <= deadline(t)]
        xl, _ = v2.features(cut, pd.PeriodIndex([t]))
        for k in v2.CANDIDATES:
            a, b = xl[k][t], xs[k][t]
            assert (np.isnan(a) and np.isnan(b)) or a == b, (k, t)


def _bases(table):
    """Both bases: A recomputed (k0_screen.fifty_fifty_frame), R from the V2 cache of the shadow run."""
    out = {"A": v2.restrict(v2.base_a())}
    path = v2.CACHE / "base_r.csv"
    if path.exists():
        from kpif_nowcast.k12_global import _read_cache

        out["R"] = v2.restrict(_read_cache(path))
    return out


COMBO = ["kpif_air_transport_index", "kpi_rent_index", "sek_eur"]  # includes the series chosen for both bases
SINGLES = sorted(set(COMBO) | {"kpif_package_holidays_index"} | {k for v in (v2.V2_CHOSEN or {}).values() for k in v})


@needs_data
def test_correction_uses_only_deadline_data(table, xs_full):
    """x(t) and the corrected forecast for t are identical when the observation table is cut at deadline(t)
    and outcomes from t on are removed; both bases, single candidates and a three-series combination."""
    from kpif_nowcast.j3_screen import combined_h1, correct, h1_usable
    from kpif_nowcast.riksbank_benchmark import deadline

    xs, _ = xs_full
    bases = _bases(table)
    for b, f in bases.items():
        full_single = {k: correct(f["base"], f["actual"], xs[k].reindex(f.index), h1_usable(f.index)) for k in SINGLES}
        combos = {"combo": COMBO, **({"chosen": v2.V2_CHOSEN[b]} if v2.V2_CHOSEN and v2.V2_CHOSEN.get(b) else {})}
        full_combo = {c: combined_h1(f, xs, ks) for c, ks in combos.items()}
        for t in MONTHS:
            cut = table[table["known_from"] <= deadline(t)]
            fl = f.loc[:t].copy()
            fl.loc[t, "actual"] = np.nan
            xl, _ = v2.features(cut, fl.index, SINGLES)
            for k in SINGLES:
                live = correct(fl["base"], fl["actual"], xl[k].reindex(fl.index), h1_usable(fl.index))
                assert np.isclose(live[t], full_single[k][t], rtol=0, atol=1e-10), (b, k, t)
            for c, ks in combos.items():
                assert np.isclose(combined_h1(fl, xl, ks)[t], full_combo[c][t], rtol=0, atol=1e-10), (b, c, t)
    if "R" not in bases:
        pytest.skip("base R cache missing (run python -m kpif_nowcast.v2_screen); only base A checked")


def _cut_inputs(inp: dict, t: pd.Period) -> dict:
    """Every input of the 50/50 panel as it was at deadline(t): outcomes and components up to t-1, el/fuel
    features up to t, Riksbank forecasts published before the deadline, observations known by the deadline."""
    from kpif_nowcast.riksbank_benchmark import deadline

    d = deadline(t)
    month = lambda df: pd.PeriodIndex(df["month"].astype(str), freq="M")  # noqa: E731
    return dict(inp,
                kpif=inp["kpif"].loc[:t - 1], comps=inp["comps"][month(inp["comps"]) <= t - 1],
                feats=inp["feats"].loc[:t], contracts=inp["contracts"][month(inp["contracts"]) <= t],
                se3=inp["se3"].loc[:t], rb_fc=inp["rb_fc"][pd.to_datetime(inp["rb_fc"]["published"]) < d],
                obs=inp["obs"][inp["obs"]["known_from"] <= d])


@needs_data
def test_v2_a_corr_end_to_end_on_cut_inputs():
    """Review fix (V2 granskning): base A is recomputed from inputs cut at deadline(t), the chosen series' x from
    the cut observation table, and the correction is refitted; v2_a_corr(t) equals the full-sample value."""
    from kpif_nowcast.j1_hybrid import j1_forecast
    from kpif_nowcast.j3_screen import combined_h1
    from kpif_nowcast.k12_global import _panel

    if not (v2.V2_CHOSEN and v2.V2_CHOSEN.get("A")):
        pytest.skip("V2 not run yet")
    keys = v2.V2_CHOSEN["A"]
    inp = v2._inputs()
    fa = v2.restrict(v2.base_a(inp))
    xs, _ = v2.features(inp["obs"], fa.index, keys)
    full = combined_h1(fa, xs, keys)
    for t in [pd.Period(m, "M") for m in ["2018-03", "2021-07", "2024-07", "2026-10"]]:
        ci = _cut_inputs(inp, t)
        p = _panel(ci)
        if t not in p.index:
            p = p.reindex(p.index.union(pd.PeriodIndex([t])))
        fl = v2.restrict(pd.DataFrame({"base": j1_forecast(p, "j1_comb_equal"), "actual": p["actual"]})).loc[:t]
        assert np.isclose(fl.loc[t, "base"], fa.loc[t, "base"], rtol=0, atol=1e-10), t
        assert np.isnan(fl.loc[t, "actual"]) or t not in ci["kpif"].index
        fl.loc[t, "actual"] = np.nan
        xl, _ = v2.features(ci["obs"], fl.index, keys)
        assert np.isclose(combined_h1(fl, xl, keys)[t], full[t], rtol=0, atol=1e-10), t


@needs_data
def test_selection_reproduces_frozen_choice():
    """The frozen V2_CHOSEN is what the preregistered rule gives on the saved primary screen tables."""
    if v2.V2_CHOSEN is None:
        pytest.skip("V2 not run yet")
    for b in ("R", "A"):
        path = v2.CACHE / f"screen_{b}.csv"
        if not path.exists():
            pytest.skip("screen tables missing (run python -m kpif_nowcast.v2_screen)")
        prim = pd.read_csv(path, index_col=0)
        assert v2.choose(prim)[0] == v2.V2_CHOSEN[b], b
