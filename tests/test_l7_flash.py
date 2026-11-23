"""L7: Snabb-KPI catalog entries, parsing, lags against documented release dates, and data quality."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from kpif_nowcast import catalog_flash as cf
from kpif_nowcast.catalog import AREAS, CATALOG

KEYS = ["kpif_flash_yy", "kpif_flash_mm", "kpif_xe_flash_yy", "kpif_xe_flash_mm",
        "kpif_flash_err_yy", "kpif_flash_err_mm", "kpif_xe_flash_err_yy"]


def _payload(values: dict[tuple[str, str, str], float]) -> dict:
    """Synthetic json-stat2 with dimensions PrelAggr x ContentsCode x Tid."""
    aggr = sorted({k[0] for k in values})
    cont = sorted({k[1] for k in values})
    tid = sorted({k[2] for k in values})
    dims = {"PrelAggr": aggr, "ContentsCode": cont, "Tid": tid}
    flat = [values.get((a, c, t)) for a in aggr for c in cont for t in tid]
    return {"id": list(dims), "value": flat,
            "dimension": {d: {"category": {"index": {code: i for i, code in enumerate(v)}}} for d, v in dims.items()}}


def test_specs_registered():
    keys = [s.key for s in CATALOG]
    assert cf.keys() == KEYS and set(KEYS) <= set(keys) and len(keys) == len(set(keys))
    for s in cf.specs():
        assert s.area in AREAS and s.freq == "M" and not s.revised
        assert s.lag_days == (cf.LAG_ERR if "_err_" in s.key else cf.LAG_FLASH)


def _deadline(t: pd.Period) -> pd.Timestamp:
    """Day-4 deadline for target month t (00:00), as in forecast.py / horizon.origin_date."""
    return (t + 1).to_timestamp() + pd.Timedelta(days=3)


def test_flash_never_known_at_day4_deadline(tmp_path, monkeypatch):
    """Backfilled flash for t is not in as_of(day-4 deadline of t), also when SCB released on day 4.

    A live fetch made on a day-4 release day is stored with known_from = fetch date (00:00) and is
    therefore visible at that deadline: documented caveat (module docstring, resultat.md).
    """
    from kpif_nowcast import observations as obs
    from kpif_nowcast import publication

    monkeypatch.setattr(obs, "PATH", tmp_path / "obs.parquet")
    day4 = [p for p, (f, _) in cf.RELEASES.items() if pd.Timestamp(f).day == 4]
    assert day4  # the case that matters: release on the deadline day
    per = pd.PeriodIndex(sorted(cf.RELEASES), freq="M")
    obs.upsert("kpif_flash_yy", pd.Series(1.0, index=per), fetched_at=date(2026, 11, 23))
    for p in per:
        assert p not in obs.as_of("kpif_flash_yy", _deadline(p)).index, p
        assert p in obs.as_of("kpif_flash_yy", (p + 1).to_timestamp() + pd.Timedelta(days=8)).index  # day 9
    kf = publication.known_from("kpif_flash_yy", per, cf.LAG_FLASH)
    assert (kf > pd.DatetimeIndex([_deadline(p) for p in per])).all()

    # live fetch on a day-4 release day: known_from = that day 00:00 = the deadline (caveat)
    t = pd.Period("2027-02", "M")
    obs.upsert("kpif_flash_yy", pd.Series([2.0], index=pd.PeriodIndex([t])), fetched_at=date(2027, 3, 4))
    assert t in obs.as_of("kpif_flash_yy", _deadline(t)).index


def test_lags_cover_every_documented_release():
    for per, (flash, ordinary) in cf.RELEASES.items():
        end = pd.Period(per, "M").end_time.normalize()
        assert pd.Timestamp(flash) <= end + pd.Timedelta(days=cf.LAG_FLASH), per
        assert pd.Timestamp(ordinary) <= end + pd.Timedelta(days=cf.LAG_ERR), per
        assert pd.Timestamp(flash) < pd.Timestamp(ordinary), per
    assert min(cf.RELEASES) == str(cf.FIRST_RELEASE)


def test_flash_from_drops_back_calculated_months():
    v = {}
    for t, x in [("2024M08", 1.2), ("2024M09", 1.1), ("2024M10", 1.5)]:
        v[(cf.FLASH_KPIF, cf.FLASH_YY, t)] = x
        v[(cf.FLASH_KPIF, cf.FLASH_MM, t)] = 0.1
        v[(cf.FLASH_XE, cf.FLASH_YY, t)] = 2.0
        v[(cf.FLASH_XE, cf.FLASH_MM, t)] = 0.2
    s = cf.flash_from(_payload(v), cf.FLASH_KPIF, cf.FLASH_YY)
    assert list(s.index.astype(str)) == ["2024-09", "2024-10"] and list(s) == [1.1, 1.5]
    assert list(cf.flash_from(_payload(v), cf.FLASH_XE, cf.FLASH_MM)) == [0.2, 0.2]


def test_error_from_aligns_and_rounds():
    idx = pd.PeriodIndex(["2024-09", "2024-10", "2024-11"], freq="M")
    flash = pd.Series([1.1, 1.5, 1.9], index=idx)
    final = pd.Series([1.0, 1.5], index=idx[:2])
    e = cf.error_from(flash, final)
    assert list(e.index.astype(str)) == ["2024-09", "2024-10"] and list(e) == [0.1, 0.0]


def test_final_from_splices_at_rebase():
    idx = pd.period_range("2025-11", "2026-02", freq="M")
    old = pd.Series([1.8, 1.5, 9.9, 9.9], index=idx)
    new = pd.Series([1.9, 1.6, 2.0, 1.7], index=idx)
    f = cf.final_from(old, new)
    assert list(f.index.astype(str)) == ["2025-11", "2025-12", "2026-01", "2026-02"]
    assert list(f) == [1.8, 1.5, 2.0, 1.7]


def test_specs_name_both_final_tables():
    for s in cf.specs():
        if "_err_" in s.key:
            assert "TAB591" in s.source and "TAB659" in s.source and "1987=100" in s.note


def test_cache_age_and_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(cf, "RAW_DIR", tmp_path)
    (tmp_path / "scb_TAB6445_20261101.json").write_text("{}")
    (tmp_path / "scb_TAB6445_20261120.json").write_text("{}")
    (tmp_path / "scb_TAB64450_20261121.json").write_text("{}")  # other table, must not match
    assert cf._cached("TAB6445", today=date(2026, 11, 23)).name == "scb_TAB6445_20261120.json"
    assert cf._cached("TAB6445", today=date(2026, 12, 30)) is None
    assert cf._cached("TAB6445", today=date(2026, 12, 30), max_age=None).name == "scb_TAB6445_20261120.json"
    from kpif_nowcast.sources import rawcache

    monkeypatch.setenv(rawcache.ENV, "1")
    with pytest.raises(rawcache.OfflineError):
        cf._payload("TAB6590")


# ---------------------------------------------------------------- with data


@pytest.fixture(scope="module")
def table():
    from kpif_nowcast import observations as obs

    t = obs.load()
    if not set(KEYS) <= set(t["series"]):
        pytest.skip("L7 series not in data/observations.parquet (run python -m kpif_nowcast.observations)")
    return t[t["series"].isin(KEYS)].copy()


def test_quality(table):
    assert not table.duplicated(["series", "period", "known_from"]).any()
    for k in KEYS:
        t = table[table["series"] == k]
        per = pd.PeriodIndex(t["period"], freq="M")
        assert per.min() == cf.FIRST_RELEASE, k
        assert len(pd.period_range(per.min(), per.max(), freq="M")) == per.nunique(), f"{k}: holes"
        end = (per + 1).to_timestamp() - pd.Timedelta(days=1)
        assert (pd.to_datetime(t["known_from"]).to_numpy() >= end.to_numpy()).all(), k


def test_values_plausible(table):
    w = table.sort_values("known_from").pivot_table(index="period", columns="series", values="value", aggfunc="last")
    assert w[["kpif_flash_yy", "kpif_xe_flash_yy"]].abs().max().max() < 15
    assert w[["kpif_flash_err_yy", "kpif_flash_err_mm", "kpif_xe_flash_err_yy"]].abs().max().max() <= 0.5


# First-published finals from SCB's news releases "Konsumentprisindex (KPI), <month> <year>" where the
# rebased 2020=100 tables differ by 0.1 (granskning, docs/auto3/l7/resultat.md).
FIRST_PUBLISHED = {
    ("kpif_flash_err_yy", "2024-11"): (1.9, 1.8),  # (flash, first-published final), release 2024-12-12
    ("kpif_flash_err_mm", "2024-12"): (0.3, 0.3),  # release 2025-01-15 (TAB6590: 0.2)
    ("kpif_xe_flash_err_yy", "2024-12"): (2.1, 2.0),  # release 2025-01-15 (TAB6593: 2.1)
    ("kpif_flash_err_yy", "2025-08"): (3.3, 3.2),  # release 2025-09-11 (TAB6590: 3.3)
}


def test_errors_use_first_published_final(table):
    w = table.sort_values("known_from").pivot_table(index="period", columns="series", values="value", aggfunc="last")
    for (key, per), (fl, fin) in FIRST_PUBLISHED.items():
        assert w.loc[per, key] == pytest.approx(round(fl - fin, 1)), (key, per)
    assert (table["source"] != "revision").all()
