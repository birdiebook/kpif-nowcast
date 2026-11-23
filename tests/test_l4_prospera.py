"""L4: Prospera money market expectations from the Riksbank's figure data (no network)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from kpif_nowcast import catalog_prospera as cp
from kpif_nowcast.catalog import AREAS, CATALOG

ANM = ("Månadsdata. Den blå linjen avser genomsnittliga förväntningar, ljusblå staplar visar intervallet mellan "
       "den 25:e och 75:e percentilen och de grå linjerna utanför staplarna visar variationsbredden.")


def _sheet(title="Spridning i 5-åriga inflationsförväntningar, penningmarknadens aktörer",
           source="Origo Group och Riksbanken.", mean_label="Genomsnitt"):
    return [
        ["Diagram", 36.0],
        ["Rubrik", title],
        ["Enhet", "Procent"],
        ["Källor:", source],
        ["Anm.", ANM],
        [],
        [None, "Undre grå linje", "P25", mean_label, "P75", "Övre grå linje"],
        [43466.0, 1.4, 1.7, 1.878787879, 2.0, 2.4],  # 2019-01-01 as Excel serial
        [43497.0, 1.4, 1.7, 1.9, 2.0, 2.4],
        [43525.0, 1.3, None, 1.84, 2.0, 2.4],
        [],
        [None, None],
    ]


def test_parse_maps_columns_not_the_note():
    df = cp.parse_sheet(_sheet())
    assert list(df.index.astype(str)) == ["2019-01", "2019-02", "2019-03"]
    assert df.loc[pd.Period("2019-01", "M"), "mean"] == pytest.approx(1.878787879)
    assert df.loc[pd.Period("2019-01", "M"), "p25"] == 1.7 and df.loc[pd.Period("2019-01", "M"), "p75"] == 2.0
    assert pd.isna(df.loc[pd.Period("2019-03", "M"), "p25"])


def test_sheet_detection():
    assert cp.is_prospera_sheet(_sheet())
    assert cp.is_prospera_sheet(_sheet(mean_label="Medelvärde"))  # June 2026 wording
    assert not cp.is_prospera_sheet(_sheet(source="Nationella centralbanker och Riksbanken."))
    assert not cp.is_prospera_sheet(_sheet(title="Marknadens förväntningar på styrräntor"))
    other = [["Diagram", 4.0], ["Rubrik", "Marknadens förväntningar på styrräntor"], [None, "a", "b"]]
    df = cp.find_in_workbook({"Innehåll": [["x"]], "4": other, "36": _sheet()})
    assert df is not None and len(df) == 3
    assert cp.find_in_workbook({"4": other}) is None


def test_discovery_parsing():
    html = ('<a href="/sv/penningpolitik/penningpolitisk-rapport/2026/penningpolitiskt-beslut-juni-2026/">'
            '<a href="/sv/penningpolitik/penningpolitisk-rapport/2026/penningpolitiskt-beslut-november-2026/">'
            '<a href="/sv/penningpolitik/penningpolitisk-rapport/2025/penningpolitiskt-beslut-december-2025/">'
            '<a href="/sv/penningpolitik/penningpolitisk-rapport/2026/penningpolitiskt-beslut-juni-2026/">')
    pages = cp.decision_pages(html)
    assert [p.split("beslut-")[1] for p in pages] == ["november-2026/", "juni-2026/", "december-2025/"]
    page = ('<a href="/globalassets/media/rapporter/ppr/siffferunderlag/svenska/2026/'
            'sifferunderlag-penningpolitisk-rapport-september-2026.xlsx">'
            '<a href="/globalassets/media/rapporter/ppr/svenska/direktionens-rostning.xlsx">')
    assert cp.xlsx_links(page) == ["/globalassets/media/rapporter/ppr/siffferunderlag/svenska/2026/"
                                   "sifferunderlag-penningpolitisk-rapport-september-2026.xlsx"]


def test_specs():
    sp = cp.specs()
    assert [s.key for s in sp] == cp.keys()
    assert all(s.area in AREAS and s.freq == "M" and s.revised and s.lag_days == 3 for s in sp)
    keys = [s.key for s in CATALOG]
    assert len(keys) == len(set(keys)) and set(cp.keys()) <= set(keys)
    # KI household and firm expectations are separate series and must stay so (no duplicate of KI here)
    assert {"hh_infl_exp_median", "nier_firm_infl_exp_new"} <= set(keys)


def test_offline_uses_cache_only(tmp_path, monkeypatch):
    from kpif_nowcast.sources import rawcache

    monkeypatch.setattr(cp, "RAW_DIR", tmp_path)
    monkeypatch.setenv(rawcache.ENV, "1")
    with pytest.raises(rawcache.OfflineError):
        cp.source_file()
    (tmp_path / "prospera_source_20260101.json").write_text(json.dumps({"hit": "https://x/sifferunderlag-a.xlsx"}))
    with pytest.raises(rawcache.OfflineError):
        cp.source_file()  # the report file itself is not cached
    (tmp_path / "sifferunderlag-a_20260101.xlsx").write_bytes(b"")
    assert cp.source_file().name == "sifferunderlag-a_20260101.xlsx"


# ---------------------------------------------------------------- with data


@pytest.fixture(scope="module")
def table():
    from kpif_nowcast import observations as obs

    if not obs.PATH.exists():
        pytest.skip("no observation table")
    t = obs.load()
    if not set(cp.keys()) <= set(t["series"]):
        pytest.skip("Prospera series not fetched")
    return t


def test_quality(table):
    q = cp.quality(table)
    assert (q["rows"] > 0).all()
    assert (q["holes"] == 0).all() and (q["dup_keys"] == 0).all() and (q["kf_before_end"] == 0).all()


def test_values_plausible_and_ordered(table):
    from kpif_nowcast.observations import as_of

    m, lo, hi = (as_of(k, pd.Timestamp.today(), table) for k in cp.keys())
    assert m.between(0, 6).all() and (lo <= hi).all()
    assert (m.index.min() <= pd.Period("2019-12", "M"))
    # known at the deadline: month t is visible on day 4 of t+1
    last = m.index.max()
    seen = as_of("prospera_mm_5y_mean", (last + 1).to_timestamp() + pd.Timedelta(days=3), table)
    assert seen.index.max() == last
