"""K5: Sverigeläget v2 datasets and page, and the monthly letter (incl. an as-of test)."""

from __future__ import annotations

import json
import re

import pandas as pd
import pytest

from kpif_nowcast import manadsbrev as mb
from kpif_nowcast import observations as obs
from kpif_nowcast import sverige_dashboard as sd
from kpif_nowcast.data import PROCESSED_DIR

needs_data = pytest.mark.skipif(not obs.PATH.exists() or not (PROCESSED_DIR / "features.csv").exists(),
                                reason="data/observations.parquet or data/processed missing")
NEW = ["region", "af", "ai_indicator", "prisled", "forecast", "champion", "explain_summary", "explain_text",
       "explain_components",
       # run 3 (L10)
       "resor", "hyror", "prospera", "elmarknad", "kronan", "snabbkpi", "admin_events", "admin_yy", "admin_upcoming",
       "v2_eval"]


@pytest.fixture(scope="module")
def table():
    return obs.load()


@pytest.fixture(scope="module")
def inputs():
    from kpif_nowcast.shadow import load_inputs

    return load_inputs()


@pytest.fixture(scope="module")
def out(tmp_path_factory):
    d = tmp_path_factory.mktemp("sverige")
    failed = sd.main(out_dir=d, with_k2=False)
    return d, failed


def _rows(d, name):
    return json.loads((d / f"{name}.json").read_text(encoding="utf-8"))["rows"]


@needs_data
def test_dashboard_writes_all_sections(out):
    d, failed = out
    assert failed == []
    manifest = json.loads((d / "MANIFEST.json").read_text(encoding="utf-8"))
    listed = {f["file"] for f in manifest["files"]}
    assert "index.html" in listed
    for name in ["overview", "series", "pressure", "ai", *NEW]:
        assert f"{name}.json" in listed
        assert len(_rows(d, name)) > 0, name
    html = (d / "index.html").read_text(encoding="utf-8")
    for name in NEW:  # every new dataset is read by the page
        assert f'"{name}"' in html or f"data-source=\"{name}" in html, name


@needs_data
def test_page_fields_exist_in_datasets(out):
    """Every data-source/data-field pair in index.html names a column the dataset (or calc input) has."""
    d, _ = out
    html = (d / "index.html").read_text(encoding="utf-8")
    calcs = {"area_now": "pressure", "prisled_now": "prisled", "af_now": "af"}
    calc_fields = {"area_now": {"area", "area_label", "period", "pressure"},
                   "prisled_now": {"key", "group_label", "label", "period", "value", "value_3m_ago", "value_12m_ago"},
                   "af_now": {"key", "label", "period", "value", "value_3m", "yoy_pct", "value_3m_yoy_pct"}}
    checked = 0
    for tag in re.findall(r"<(?:span|b|div|th|p|table)[^>]*>", html):
        src = re.search(r'data-source="([^"]+)"', tag)
        fld = re.search(r'data-field="([^"]+)"', tag)
        if not src or not fld or " " in src.group(1):
            continue
        s, f = src.group(1), fld.group(1)
        cols = calc_fields[s] if s in calcs else set().union(*[r.keys() for r in _rows(d, s)])
        assert f in cols, (s, f)
        checked += 1
    # table headers: <table data-source=X> ... <th data-field=Y>
    for tbl in re.findall(r"<table[^>]*data-source=\"([^\"]+)\"[^>]*>(.*?)</table>", html, flags=re.S):
        s, body = tbl
        cols = calc_fields[s] if s in calcs else set().union(*[r.keys() for r in _rows(d, s)])
        for f in re.findall(r'<th[^>]*data-field="([^"]+)"', body):
            assert f in cols, (s, f)
            checked += 1
    assert checked > 30


@needs_data
def test_region_rules(out):
    d, _ = out
    rows = _rows(d, "region")
    assert not any(r["behind_national"] for r in rows)
    assert {r["measure"] for r in rows} <= set(sd.REGION_MEASURES)
    assert all(r["period"] <= "2026-03" for r in rows if r["measure"] == "af_varsel")
    assert all(r["tile_col"] is not None for r in rows if r["code"] != "00")


@needs_data
def test_forecast_rows_are_labelled(out):
    d, _ = out
    rows = _rows(d, "forecast")
    for r in rows:
        if r["kind"] in ("skugga", "kandidat"):
            assert "urvalsevidens" in r["evidence"]
    assert len({r["target_month"] for r in rows}) == 1


@needs_data
def test_letter_current_month(table, inputs):
    inp, info = inputs
    text = mb.build(info["target"], table=table, inp=inp, info=info, with_k2=False)
    for h in ["## Huvudbudskap", "## Prognosen för", "## Läget", "### Inflation och prisleden", "### Arbetsmarknad",
              "### Bostäder och krediter", "### Regionala skillnader", "### AI", "## Vad har ändrats sedan förra månaden"]:
        assert h in text, h
    assert "urvalsevidens" in text


@needs_data
def test_letter_uses_only_data_known_at_cutoff(table, inputs):
    """Letter for a past month: identical with and without observations known after its cutoff, and no later periods."""
    inp, info = inputs
    month = pd.Period("2026-06", "M")
    cutoff = mb.cutoff_for(month, today="2026-11-23")
    assert cutoff.date() == pd.Timestamp("2026-07-04").date()
    full = mb.build(month, table=table, inp=inp, info=info, today="2026-11-23", with_k2=False)
    cut = mb.build(month, table=table[table["known_from"] <= cutoff], inp=inp, info=info, today="2026-11-23", with_k2=False)
    assert full == cut
    assert "KPIF t.o.m. 2026-05" in full  # explanation: outcomes to month-1 only
    assert not re.search(r"2026-(0[7-9]|1[0-2])(?!-\d)", full)  # no period after the cutoff (dates like 2026-07-04 ok)
