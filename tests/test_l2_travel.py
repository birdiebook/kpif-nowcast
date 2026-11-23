"""L2 travel series: Easter calendar, guest nights (Eurostat), KPIF travel sub-indices. No network."""

from __future__ import annotations

import itertools
from datetime import date

import pandas as pd
import pytest

from kpif_nowcast import catalog_travel as ct
from kpif_nowcast.catalog import CATALOG, by_key
from kpif_nowcast.observations import PATH as OBS_PATH
from kpif_nowcast.observations import as_of, default_known_from
from kpif_nowcast.sources.rawcache import OfflineError


def _jsonstat(dims: dict[str, list[str]], values: dict[tuple, float]) -> dict:
    """Minimal JSON-stat 2.0 dataset with the given dimension codes and cell values."""
    ids = list(dims)
    flat = {}
    for i, combo in enumerate(itertools.product(*dims.values())):
        if combo in values:
            flat[str(i)] = values[combo]
    return {"id": ids, "size": [len(v) for v in dims.values()],
            "dimension": {k: {"category": {"index": {c: j for j, c in enumerate(v)}}} for k, v in dims.items()},
            "value": flat}


# ------------------------------------------------------------------ Easter


def test_easter_dates_and_window():
    assert [ct.easter_date(y) for y in (2019, 2024, 2025, 2026, 2030)] == [
        date(2019, 4, 21), date(2024, 3, 31), date(2025, 4, 20), date(2026, 4, 5), date(2030, 4, 21)]
    w = ct.easter_window_days(2030)
    assert w.index[0] == pd.Period("2000-01", "M") and w.index[-1] == pd.Period("2030-12", "M")
    assert (w.groupby(w.index.year).sum() == 11).all()  # the whole 11-day window every year
    assert w[pd.Period("2024-03", "M")] == 10 and w[pd.Period("2024-04", "M")] == 1  # 22 Mar .. 1 Apr
    assert w[pd.Period("2026-03", "M")] == 5 and w[pd.Period("2026-04", "M")] == 6  # 27 Mar .. 6 Apr
    assert w[pd.Period("2025-04", "M")] == 11
    assert set(w[~w.index.month.isin([3, 4])].unique()) == {0.0}


def test_easter_sunday_flag():
    s = ct.easter_sunday_in_month(2030)
    assert (s.groupby(s.index.year).sum() == 1).all()
    assert s[pd.Period("2024-03", "M")] == 1 and s[pd.Period("2024-04", "M")] == 0
    assert s[pd.Period("2026-04", "M")] == 1


def test_easter_has_fixed_end():
    """A fixed end: the default series doesn't depend on today's date (no new periods after a year change)."""
    assert ct.easter_window_days().index[-1] == pd.Period(f"{ct.EASTER_END}-12", "M")
    assert ct.easter_sunday_in_month().index[-1] == pd.Period(f"{ct.EASTER_END}-12", "M")
    assert ct.EASTER_END >= date.today().year + 10


def test_easter_refresh_after_year_change_keeps_checks_green(monkeypatch, tmp_path):
    """Backfill now, refresh next January: no new 'fetch' rows, warehouse checks stay clean."""
    from kpif_nowcast import observations as obs
    from kpif_nowcast.warehouse import connect, run_checks

    path = tmp_path / "obs.parquet"
    monkeypatch.setattr(obs, "PATH", path)
    first = obs.upsert("easter_window_days", ct.easter_window_days(), fetched_at=date(2026, 11, 23))
    assert first == len(ct.easter_window_days())
    assert obs.upsert("easter_window_days", ct.easter_window_days(), fetched_at=date(2027, 1, 5)) == 0
    checks = run_checks(connect(path))
    assert checks["known_from_after_period_end"].empty
    assert checks["fetched_known_from_not_after_fetch"].empty
    assert ct.quality(obs.load(raw=True)).loc["easter_window_days", "kf_too_early"] == 0


def test_calendar_series_kept_out_of_screen():
    from kpif_nowcast.j3_screen import screen_keys

    keys = screen_keys()
    assert "easter_window_days" not in keys and "easter_sunday_in_month" not in keys
    assert "guest_nights_total" in keys


def test_cache_max_age_below_weekly_cadence():
    assert ct.MAX_AGE_DAYS < 7


# ------------------------------------------------------------------ guest nights


def _nights_payload() -> dict:
    times = ["2000-12", "2001-01", "2001-02", "2099-01"]
    dims = {"freq": ["M"], "c_resid": ["DOM", "FOR", "TOTAL"], "unit": ["NR"],
            "nace_r2": ["I551-I553", "I551"], "geo": ["SE"], "time": times}
    vals = {}
    for t, (tot, fo) in zip(times, [(900, 100), (1000, 300), (2000, 500), (5, 1)]):
        vals[("M", "TOTAL", "NR", "I551-I553", "SE", t)] = tot
        vals[("M", "FOR", "NR", "I551-I553", "SE", t)] = fo
        vals[("M", "TOTAL", "NR", "I551", "SE", t)] = tot / 2
    vals[("M", "DOM", "NR", "I551-I553", "SE", "2001-02")] = 1500  # DOM only where Eurostat has it
    return _jsonstat(dims, vals)


def test_guest_nights_domestic_is_total_minus_foreign(monkeypatch):
    monkeypatch.setattr(ct, "_get_json", lambda *a, **k: _nights_payload())
    dom = ct.nights("DOM", start="2001-01")()
    assert list(dom.index.astype(str)) == ["2001-01", "2001-02"]  # 2000-12 cut by start, 2099 future dropped
    assert list(dom) == [0.7, 1.5]  # thousands
    hotel = ct.nights("TOTAL", "I551")()
    assert list(hotel) == [0.45, 0.5, 1.0]


def test_offline_without_cache_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("KPIF_OFFLINE", "1")
    monkeypatch.setattr(ct, "RAW_DIR", tmp_path)
    with pytest.raises(OfflineError):
        ct.nights_frame()


def test_cache_is_reused(monkeypatch, tmp_path):
    monkeypatch.setattr(ct, "RAW_DIR", tmp_path)
    import json

    (tmp_path / f"{ct.NIGHTS_NAME}_{date.today():%Y%m%d}.json").write_text(json.dumps(_nights_payload()))
    monkeypatch.setattr("requests.get", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")))
    assert ct.nights("FOR")().iloc[-1] == 0.5


# ------------------------------------------------------------------ KPIF sub-indices


def test_kpif_frame(monkeypatch):
    dims = {"VaruTjanstegrupp": ["09.8", "07.3.3", "11.2"], "ContentsCode": [ct.KPIF_INDEX],
            "Tid": ["2026M09", "2026M10"]}
    vals = {(c, ct.KPIF_INDEX, t): v for (c, t), v in
            {("09.8", "2026M09"): 150.0, ("09.8", "2026M10"): 159.2, ("11.2", "2026M10"): 157.1}.items()}
    w = ct.kpif_frame(_jsonstat(dims, vals))
    assert w.loc[pd.Period("2026-10", "M"), "09.8"] == 159.2
    assert pd.isna(w.loc[pd.Period("2026-09", "M"), "11.2"])


# ------------------------------------------------------------------ catalog and leakage


def test_specs_registered_with_lags():
    keys = ct.keys()
    assert len(keys) == len(set(keys)) == 9
    assert set(keys) <= {s.key for s in CATALOG}
    spec = by_key()
    assert all(spec[k].lag_days == ct.LAG_NIGHTS and spec[k].revised for k in keys if k.startswith("guest_"))
    assert all(spec[k].lag_days < 0 and not spec[k].revised for k in keys if k.startswith("easter_"))
    assert all(spec[k].lag_days == 15 and spec[k].revised for k in keys if k.startswith("kpif_"))


def test_guest_nights_information_set_at_deadline():
    """Lag 80: at the 4 December deadline (target November) the latest guest-night month is August."""
    per = pd.period_range("2026-06", "2026-10", freq="M")
    kf = default_known_from("guest_nights_total", per)
    t = pd.DataFrame({"series": "guest_nights_total", "period": per.astype(str), "value": 1.0,
                      "known_from": kf, "source": "backfill", "fetched_at": pd.Timestamp("2026-11-23")})
    assert str(as_of("guest_nights_total", pd.Timestamp("2026-12-04"), t).index.max()) == "2026-08"


def test_easter_known_a_year_ahead():
    per = pd.period_range("2027-01", "2027-12", freq="M")
    kf = default_known_from("easter_window_days", per)
    assert kf.max() <= pd.Timestamp("2026-12-31")


def test_warehouse_allows_negative_lag_only_for_easter(tmp_path):
    from kpif_nowcast.warehouse import connect, run_checks

    rows = [("easter_window_days", "2027-04", 7.0, pd.Timestamp("2026-04-29"), "backfill", pd.Timestamp("2026-11-23")),
            ("guest_nights_total", "2026-10", 5.0, pd.Timestamp("2026-10-20"), "backfill", pd.Timestamp("2026-11-23"))]
    path = tmp_path / "obs.parquet"
    pd.DataFrame(rows, columns=["series", "period", "value", "known_from", "source", "fetched_at"]).to_parquet(path)
    bad = run_checks(connect(path))["known_from_after_period_end"]
    assert list(bad["series"]) == ["guest_nights_total"]


# ------------------------------------------------------------------ real data (skips without fetched data)


def test_observation_table_quality():
    if not OBS_PATH.exists():
        pytest.skip("data/observations.parquet missing")
    q = ct.quality()
    if (q["rows"] == 0).any():
        pytest.skip(f"L2 series not fetched: {list(q.index[q['rows'] == 0])}")
    assert (q["holes"] == 0).all() and (q["dup_keys"] == 0).all() and (q["kf_too_early"] == 0).all()
    assert q.loc["guest_nights_total", "from"] == "2001-01"
