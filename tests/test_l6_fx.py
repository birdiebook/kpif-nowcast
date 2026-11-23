"""L6: EUR/SEK and USD/SEK catalog entries, monthly means, incomplete months, cache and data quality."""

from __future__ import annotations

import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast import catalog_fx as fx
from kpif_nowcast.catalog import AREAS, CATALOG


def _daily(start: str, end: str, value=None) -> pd.Series:
    idx = pd.bdate_range(start, end)
    vals = np.arange(len(idx), dtype=float) if value is None else np.full(len(idx), value)
    return pd.Series(vals, index=idx)


def _payload(s: pd.Series) -> str:
    return json.dumps([{"date": f"{d:%Y-%m-%d}", "value": v} for d, v in s.items()])


# ---------------------------------------------------------------- catalog entries


def test_specs():
    sp = {s.key: s for s in fx.specs()}
    assert set(sp) == {"sek_eur", "sek_usd"}
    for s in sp.values():
        assert s.area in AREAS and s.freq == "M" and s.lag_days == 1 and not s.revised
        assert s.link and s.note and s.source.startswith("Riksbanken SWEA SEK")


def test_registered_once_after_catalog_prices():
    """Registered once, as one contiguous block after K0's price chain (other run-3 modules may sit in between)."""
    from kpif_nowcast import catalog_prices

    keys = [s.key for s in CATALOG]
    assert len(keys) == len(set(keys))
    last_k0 = keys.index(catalog_prices.keys()[-1])
    first_fx = keys.index(fx.keys()[0])
    assert first_fx > last_k0
    assert keys[first_fx:first_fx + len(fx.keys())] == fx.keys()


def test_kix_not_duplicated():
    """KIX is in catalog.py already; this module adds only the bilateral rates."""
    assert "kix" in {s.key for s in CATALOG}
    assert "SEKKIX92" not in {sid for _, sid, *_ in fx.FX}


def test_known_from_before_deadline():
    from kpif_nowcast.observations import default_known_from

    per = pd.period_range("2025-01", "2026-10", freq="M")
    for k in fx.keys():
        kf = pd.DatetimeIndex(default_known_from(k, per))
        end = (per + 1).to_timestamp() - pd.Timedelta(days=1)
        deadline = (per + 1).to_timestamp() + pd.Timedelta(days=3)  # day 4 of t+1
        assert (kf > end).all() and (kf <= deadline).all()


# ---------------------------------------------------------------- monthly mean and incomplete months


def test_monthly_mean_is_mean_of_daily_values():
    d = pd.concat([_daily("2026-01-01", "2026-01-31", 10.0), _daily("2026-02-01", "2026-02-28")])
    m = fx.monthly_mean(d, date(2026, 3, 1))
    assert list(m.index.astype(str)) == ["2026-01", "2026-02"]
    assert m["2026-01"] == 10.0
    assert m["2026-02"] == pytest.approx(np.arange(20).mean())  # 20 bank days in Feb 2026


def test_incomplete_month_dropped():
    d = _daily("2026-01-01", "2026-02-13", 1.0)
    assert list(fx.monthly_mean(d, date(2026, 2, 13)).index.astype(str)) == ["2026-01"]
    # also on the last day of the month: the fetch may predate the 16:15 fixing
    d = _daily("2026-01-01", "2026-01-30", 1.0)
    assert fx.monthly_mean(d, date(2026, 1, 31)).empty
    assert list(fx.monthly_mean(d, date(2026, 2, 1)).index.astype(str)) == ["2026-01"]


def test_stale_cache_does_not_publish_incomplete_month(tmp_path, monkeypatch):
    """A file fetched 27 Nov and reused on 2 Dec: November is incomplete in it, so it must not appear."""
    monkeypatch.setattr(fx, "RAW_DIR", tmp_path / "l6")
    (tmp_path / "l6").mkdir()
    (tmp_path / "l6" / "riksbank_SEKEURPMI_20261127.json").write_text(
        _payload(_daily("1993-01-04", "2026-11-27", 11.0)), encoding="utf-8")
    daily, fetched = fx.raw_daily("SEKEURPMI", today=date(2026, 12, 2))
    assert fetched == date(2026, 11, 27)
    assert str(fx.monthly_mean(daily, fetched).index.max()) == "2026-10"


def test_parse():
    s = fx.parse([{"date": "2026-01-02", "value": 11.5}, {"date": "2026-01-05", "value": None},
                  {"date": "2026-01-01", "value": 11.4}])
    assert list(s.index) == [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02")]
    with pytest.raises(ValueError):
        fx.parse([{"date": "2026-01-02", "value": 1.0}, {"date": "2026-01-02", "value": 2.0}])


def test_fresh_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(fx, "RAW_DIR", tmp_path / "l6")
    (tmp_path / "l6").mkdir()
    (tmp_path / "l6" / "riksbank_SEKUSDPMI_20261101.json").write_text("[]")
    (tmp_path / "riksbank_SEKUSDPMI_20261120.json").write_text("[]")
    (tmp_path / "l6" / "riksbank_SEKUSDPMI_20261120.json").write_text("[]")
    (tmp_path / "l6" / "riksbank_SEKUSDPMI_20261230.json").write_text("[]")  # future: ignored
    hit = fx._fresh("SEKUSDPMI", today=date(2026, 11, 23))
    assert hit == tmp_path / "l6" / "riksbank_SEKUSDPMI_20261120.json"
    assert fx._fresh("SEKUSDPMI", today=date(2026, 12, 29)) is None
    assert fx._fresh("SEKEURPMI", today=date(2026, 11, 23)) is None


def test_main_raw_cache_from_other_modules_ignored(tmp_path, monkeypatch):
    """data/raw/riksbank_SEKEURPMI_<date>.json from fetch_swea(start='2011-01-01') must not be reused."""
    monkeypatch.setattr(fx, "RAW_DIR", tmp_path / "l6")
    (tmp_path / "riksbank_SEKEURPMI_20261123.json").write_text(
        _payload(_daily("2011-01-03", "2026-11-20", 9.0)), encoding="utf-8")
    assert fx._fresh("SEKEURPMI", today=date(2026, 11, 23)) is None
    called = []

    def fake_download(sid, start=fx.START, tries=6):
        called.append((sid, start))
        return _payload(_daily("1993-01-04", "2026-11-20", 10.0))

    monkeypatch.setattr(fx, "_download", fake_download)
    daily, _ = fx.raw_daily("SEKEURPMI", today=date(2026, 11, 23))
    assert called == [("SEKEURPMI", "1993-01-01")]
    assert daily.index.min() == pd.Timestamp("1993-01-04")


def test_truncated_cache_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(fx, "RAW_DIR", tmp_path / "l6")
    (tmp_path / "l6").mkdir()
    (tmp_path / "l6" / "riksbank_SEKUSDPMI_20261123.json").write_text(
        _payload(_daily("2000-01-03", "2026-11-20", 9.0)), encoding="utf-8")
    with pytest.raises(ValueError, match="starts 2000-01-03"):
        fx.raw_daily("SEKUSDPMI", today=date(2026, 11, 23))


def test_offline_replays_old_cache(tmp_path, monkeypatch):
    """KPIF_OFFLINE: newest file in data/raw/l6 regardless of age; no file -> OfflineError, no download."""
    from kpif_nowcast.sources import rawcache

    monkeypatch.setattr(fx, "RAW_DIR", tmp_path / "l6")
    monkeypatch.setenv(rawcache.ENV, "1")
    monkeypatch.setattr(fx, "_download", lambda *a, **k: pytest.fail("network in offline mode"))
    with pytest.raises(rawcache.OfflineError):
        fx.raw_daily("SEKUSDPMI", today=date(2027, 3, 1))
    (tmp_path / "l6").mkdir()
    (tmp_path / "l6" / "riksbank_SEKUSDPMI_20261123.json").write_text(
        _payload(_daily("1993-01-04", "2026-11-20", 9.0)), encoding="utf-8")
    daily, fetched = fx.raw_daily("SEKUSDPMI", today=date(2027, 3, 1))  # 98 days old
    assert fetched == date(2026, 11, 23)
    assert str(fx.monthly_mean(daily, fetched).index.max()) == "2026-10"


# ---------------------------------------------------------------- with data


@pytest.fixture(scope="module")
def table():
    from kpif_nowcast import observations as obs

    t = obs.load()
    if not set(fx.keys()) <= set(t["series"]):
        pytest.skip("L6 series not fetched")
    return t


def test_quality(table):
    q = fx.quality(table)
    assert (q["rows"] > 0).all()
    assert (q["holes"] == 0).all() and (q["dup_keys"] == 0).all() and (q["kf_before_end_plus_lag"] == 0).all()
    assert (q["from"] == "1993-01").all()


def test_levels_plausible(table):
    for k, lo, hi in [("sek_eur", 7.5, 12.5), ("sek_usd", 5.0, 12.0)]:
        t = table[table["series"] == k].sort_values("period")
        v = t["value"].to_numpy()
        assert (v > lo).all() and (v < hi).all()
        assert np.abs(np.diff(np.log(v))).max() < 0.15  # no month-to-month jump above 15 %


def _cached(name: str):
    hits = sorted(fx.RAW_DIR.glob(f"{name}_*.json"))
    if not hits:
        pytest.skip(f"{name} not cached")
    return hits[-1]


@pytest.mark.parametrize("sid", ["SEKEURPMI", "SEKUSDPMI"])
def test_matches_riksbank_monthly_averages(sid):
    """Our mean equals the Riksbank's own monthly average (SWEA ObservationAggregates, 5 decimals)."""
    p = _cached(f"riksbank_{sid}")
    agg = json.loads(_cached(f"riksbank_agg_M_{sid}").read_text(encoding="utf-8"))
    rb = pd.Series({pd.Period(f"{a['year']}-{a['seqNr']:02d}", "M"): a["average"] for a in agg})
    n = pd.Series({pd.Period(f"{a['year']}-{a['seqNr']:02d}", "M"): a["observationCount"] for a in agg})
    daily = fx.parse(json.loads(p.read_text(encoding="utf-8")))
    mine = fx.monthly_mean(daily, fx._file_date(p))
    common = mine.index.intersection(rb.index)
    assert len(common) >= len(mine) - 1
    assert (mine[common] - rb[common]).abs().max() < 1e-5
    counts = daily.groupby(daily.index.to_period("M")).size()
    assert (counts[common] == n[common]).all() and counts[common].min() >= 15
