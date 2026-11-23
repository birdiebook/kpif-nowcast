"""L3 rents: the hand-curated negotiation table, catalog entries, known_from and the comparison helpers."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from kpif_nowcast import catalog_rents as cr
from kpif_nowcast.catalog import AREAS, CATALOG
from kpif_nowcast.publication import known_from


def test_negotiation_table_is_clean():
    df = cr.negotiations_frame()
    assert df["year"].is_unique and list(df["year"]) == sorted(df["year"])
    assert list(df["year"]) == list(range(df["year"].min(), df["year"].max() + 1))  # no holes
    assert df["pct"].between(-1, 10).all()
    assert df["source"].str.match(r"https://www\.(hyresgastforeningen|fastighetsagarna)\.se/").all()
    assert not set(df["year"]) & set(cr.MISSING_YEARS)
    assert set(range(2010, 2028)) == set(df["year"]) | set(cr.MISSING_YEARS)


def test_documented_dates_are_before_known_from():
    """known_from (30 June of the rent year) must not be earlier than any documented public date."""
    for o in cr.NEGOTIATIONS:
        kf = known_from("rent_negotiated", pd.PeriodIndex([f"{o.year}-12"], freq="M"), cr.LAG_NEGOTIATED)[0]
        assert kf == pd.Timestamp(f"{o.year}-06-30")
        if o.public_by:
            assert pd.Timestamp(o.public_by) <= kf - pd.Timedelta(days=60), o.year  # at least two months margin


def test_specs():
    sp = {s.key: s for s in cr.specs()}
    assert set(sp) == {"rent_negotiated", "kpi_rent_index"}
    assert all(s.area in AREAS and s.source for s in sp.values())
    assert sp["rent_negotiated"].freq == "A" and sp["rent_negotiated"].lag_days == -184
    assert sp["kpi_rent_index"].freq == "M" and sp["kpi_rent_index"].lag_days == 15
    assert all(s.revised for s in sp.values())
    keys = [s.key for s in CATALOG]
    assert len(keys) == len(set(keys)) and set(sp) <= set(keys)


def test_negotiated_series_on_december(tmp_path, monkeypatch):
    monkeypatch.setattr(cr, "RAW_DIR", tmp_path)
    s = cr.negotiated()
    assert (s.index.month == 12).all() and s[pd.Period("2026-12", "M")] == 3.4
    assert len(list(tmp_path.glob("rent_negotiations_*.csv"))) == 1  # dated raw copy


def test_fresh_cache_age(tmp_path, monkeypatch):
    monkeypatch.setattr(cr, "RAW_DIR", tmp_path)
    (tmp_path / "scb_TAB6598_x_20261101.json").write_text("{}")
    (tmp_path / "scb_TAB6598_x_20261120.json").write_text("{}")
    assert cr._fresh("scb_TAB6598_x_*.json", today=date(2026, 11, 23)).name.endswith("20261120.json")
    assert cr._fresh("scb_TAB6598_x_*.json", today=date(2026, 12, 30)) is None


def _synthetic_index() -> pd.Series:
    """Index that rises by the negotiated rate each year: 75 % in Jan-Apr, 25 % in May-Aug."""
    idx = pd.period_range("2015-01", "2025-12", freq="M")
    neg = {o.year: o.pct for o in cr.NEGOTIATIONS}
    level, vals = 100.0, []
    for p in idx:
        g = neg.get(p.year, 1.0) / 100
        step = (1 + g) ** (0.75 / 4) if p.month <= 4 else (1 + g) ** (0.25 / 4) if p.month <= 8 else 1.0
        level *= step
        vals.append(level)
    return pd.Series(vals, index=idx)


def test_compare_recovers_synthetic_pass_through():
    c = cr.compare(rent_index=_synthetic_index())
    full = c.loc[2016:2025]
    assert (full["gap_dec_dec"].abs() < 1e-9).all()
    assert ((full["share_jan_apr"] - 0.75).abs() < 0.01).all()
    assert pd.isna(c.loc[2026, "kpi_dec_dec"])  # index ends 2025-12


def test_monthly_profile_shape():
    prof = cr.monthly_profile(_synthetic_index(), years=range(2016, 2026))
    assert prof.shape == (10, 12)
    assert (prof.loc[:, 9:12].abs() < 1e-9).all().all()


# ---------------------------------------------------------------- with data


def test_series_in_observation_table():
    from kpif_nowcast import observations as obs

    t = obs.load()
    if not set(cr.keys()) <= set(t["series"]):
        pytest.skip("L3 series not fetched: python -m kpif_nowcast.observations rent_negotiated kpi_rent_index")
    for key in cr.keys():
        x = t[t["series"] == key]
        assert not x.duplicated(["period", "known_from"]).any()
    neg = t[t["series"] == "rent_negotiated"]
    assert (pd.to_datetime(neg["known_from"]).dt.strftime("%m-%d") == "06-30").all()
    kpi = t[t["series"] == "kpi_rent_index"]
    per = pd.PeriodIndex(kpi["period"], freq="M")
    assert len(per.unique()) == (per.max() - per.min()).n + 1  # no holes
    end = (per + 1).to_timestamp() - pd.Timedelta(days=1)
    assert (pd.to_datetime(kpi["known_from"]).to_numpy() >= end.to_numpy()).all()
