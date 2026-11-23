"""K4: county series - keys, catalog hook, parsers, point-in-time availability and quality."""

from __future__ import annotations

import zipfile

import pandas as pd
import pytest

from kpif_nowcast import catalog_region as cr
from kpif_nowcast import observations as obs
from kpif_nowcast.catalog import ALL, CATALOG, REGIONAL, by_key
from kpif_nowcast.riksbank_benchmark import deadline


def test_county_codes():
    assert len(cr.COUNTIES) == 21
    cases = {"Stockholms": "01", "Västra Götalands län": "14", "Västra Götaland": "14", "08 Kalmars län": "08",
             "Blekinges": "10", "Dalarnas län": "20", "Örebro": "18", "Västmanlands": "19",
             "Västernorrland": "22", "Västerbottens län": "24", "Riket": "00", "Uppgift saknas": None,
             "Inga uppgifter": None}
    for label, code in cases.items():
        assert cr.county_code(label) == code, label
    assert set(cr.TILE_GRID) == set(cr.COUNTIES) and len(set(cr.TILE_GRID.values())) == 21


def test_specs_keys_and_hook():
    keys = cr.keys()
    assert len(keys) == len(set(keys)) == len(REGIONAL)
    assert all(k in by_key() for k in keys)
    assert not any(s.key.startswith("region_") for s in CATALOG)  # national candidate lists unchanged
    assert len({s.key for s in ALL}) == len(ALL)
    for s in REGIONAL:
        assert s.area == "region" and s.freq in ("M", "Q", "A") and s.lag_days >= 10 and s.source
        m, code = cr.parse_key(s.key)
        assert m in cr.BY_MEASURE and code in cr.NAMES


def test_every_measure_has_all_counties():
    for m in cr.MEASURES:
        assert m.codes[0] == cr.NATIONAL
        covered = set(m.codes) - {cr.NATIONAL}
        if m.key == "fpi_smahus":
            assert covered == (set(cr.COUNTIES) - {"08", "09"}) | {"0809"}
        else:
            assert covered == set(cr.COUNTIES), m.key


def _pivot_xlsx(path):
    """Minimal workbook with one pivot cache: fields PERIOD, LAN (shared items) and TOT (numbers)."""
    m = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    definition = (f'<pivotCacheDefinition {m} recordCount="3"><cacheFields count="3">'
                  '<cacheField name="PERIOD"><sharedItems count="2"><s v="2026-01"/><s v="2026-02"/></sharedItems></cacheField>'
                  '<cacheField name="LAN"><sharedItems count="2"><s v="Stockholm"/><s v="Uppgift saknas"/></sharedItems></cacheField>'
                  '<cacheField name="TOT"><sharedItems containsNumber="1"/></cacheField>'
                  '</cacheFields></pivotCacheDefinition>')
    records = (f'<pivotCacheRecords {m} count="3">'
               '<r><x v="0"/><x v="0"/><n v="10"/></r><r><x v="1"/><x v="0"/><n v="12.5"/></r>'
               '<r><x v="1"/><x v="1"/><m/></r></pivotCacheRecords>')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/pivotCache/pivotCacheDefinition1.xml", definition)
        z.writestr("xl/pivotCache/pivotCacheRecords1.xml", records)


def test_pivot_cache_reader(tmp_path):
    from kpif_nowcast.sources.xlsx_pivot import read_pivot_cache

    p = tmp_path / "t.xlsx"
    _pivot_xlsx(p)
    df = read_pivot_cache(p, 1)
    assert list(df.columns) == ["PERIOD", "LAN", "TOT"]
    assert df["PERIOD"].tolist() == ["2026-01", "2026-02", "2026-02"]
    assert df["LAN"].tolist() == ["Stockholm", "Stockholm", "Uppgift saknas"]
    assert df["TOT"].iloc[:2].tolist() == [10.0, 12.5] and pd.isna(df["TOT"].iloc[2])
    assert list(read_pivot_cache(p, 1, ["LAN"]).columns) == ["LAN"]


def _table(rows):
    df = pd.DataFrame(rows, columns=["series", "period", "value"])
    df["known_from"] = pd.Timestamp("2026-11-01")
    df["source"], df["fetched_at"] = "backfill", pd.Timestamp("2026-11-01")
    return df


def test_latest_by_county_synthetic():
    rows = []
    for code, (a, b) in {"00": (6.0, 6.5), "01": (7.0, 6.0), "03": (5.0, 5.5)}.items():
        rows += [(f"region_af_andel_{code}", "2025-10", a), (f"region_af_andel_{code}", "2026-10", b)]
    for code, v in {"00": 1000.0, "01": 600.0, "03": 400.0}.items():
        rows += [(f"region_konkurser_{code}", str(p), v / 12) for p in pd.period_range("2025-11", "2026-10", freq="M")]
        rows += [(f"region_befolkning_{code}", "2026-10", v * 100)]
    out = cr.latest_by_county(_table(rows))
    andel = {r["code"]: r for r in out if r["measure"] == "af_andel"}
    assert andel["01"]["change"] == pytest.approx(-1.0) and andel["01"]["change_kind"] == "pp"
    assert andel["01"]["rank"] == 1 and andel["03"]["rank"] == 2 and "rank" not in andel["00"]
    assert andel["01"]["tile"] == list(cr.TILE_GRID["01"]) and andel["00"]["tile"] is None
    assert not any(r["behind_national"] for r in andel.values())
    per = {r["code"]: r for r in out if r["measure"] == "konkurser_per_10k"}
    assert per["01"]["value"] == pytest.approx(100.0) and per["01"]["period"] == "2026-10"
    import json

    json.dumps(out)  # JSON-friendly


# ------------------------------------------------------------------ real data (skips when not loaded)


@pytest.fixture(scope="module")
def table():
    t = obs.load()
    if t.empty or not t["series"].str.startswith("region_").any():
        pytest.skip("regional series not loaded: python -m kpif_nowcast.observations <catalog_region.keys()>")
    return t


def test_af_month_t_not_known_at_deadline(table):
    for t in [pd.Period(m, "M") for m in ["2024-06", "2026-09"]]:
        for k in ["region_af_andel_01", "region_af_inskrivna_25", "region_konkurser_12"]:
            s = obs.as_of(k, deadline(t), table)
            assert s.index.max() == t - 1, f"{k} {t}: latest known {s.index.max()}"


def test_quality(table):
    q = cr.quality(table)
    s, m = q["series"], q["measures"]
    assert (s["rows"] > 0).all(), s[s["rows"] == 0].index.tolist()
    assert (s["dup_keys"] == 0).all() and (s["kf_before_end"] == 0).all() and (s["negative"] == 0).all()
    holes = s[s["holes"] > 0].index
    assert all(k.startswith("region_aku_arbetsloshet_") for k in holes), list(holes)  # SCB suppresses small cells
    assert (m["missing_codes"] == "").all()
    # sum of counties vs national total: exact for bankruptcies and AF counts (national = sum incl. unknown county)
    assert m.loc["konkurser", "sum_vs_national_max_abs_pct"] == 0
    # AF: the national total also holds persons/notices without a known county (mean < 0.1 %, max 1.3-7.9 %
    # in single months, see docs/auto2/k4/kvalitet.md), so the counties sum to slightly less
    for k, worst in [("af_inskrivna", 2.0), ("af_oppet", 3.0), ("af_varsel", 10.0)]:
        assert -0.2 < m.loc[k, "sum_vs_national_mean_pct"] <= 0
        assert m.loc[k, "sum_vs_national_max_abs_pct"] < worst
    assert m.loc["befolkning", "sum_vs_national_max_abs_pct"] < 0.01
    for k in ["af_andel", "af_andel_ak08", "bas_arbetsloshet"]:
        assert m.loc[k, "national_inside_county_range_share"] == 1.0


def test_af_county_sum_matches_national_af_file(table):
    """Sum of the county file equals AF's national file (J6) for registered and openly unemployed."""
    for reg, nat in [("af_inskrivna", "af_inskrivna_arbetslosa"), ("af_oppet", "af_oppet_arbetslosa")]:
        n = obs.as_of(nat, "2100-01-01", table)
        if n.empty:
            pytest.skip("J6 national series not loaded")
        r = cr.frame(reg, table)["00"]
        both = pd.concat([r, n], axis=1, join="inner").dropna()
        assert len(both) > 300
        dev = (both.iloc[:, 0] / both.iloc[:, 1] - 1).abs()
        assert dev.max() < 0.01, dev.idxmax()
