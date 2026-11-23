"""L5: electricity contract shares and grid fees (catalog_el). No network: synthetic inputs, real data skipped."""

from __future__ import annotations

import pandas as pd
import pytest

from kpif_nowcast import catalog_el as el
from kpif_nowcast.catalog import by_key
from kpif_nowcast.observations import PATH as OBS_PATH
from kpif_nowcast.publication import known_from

# ------------------------------------------------------------------ Ei sheet


def _ei_rows() -> list[list]:
    """Layout of Ei's household archive: code row, label row, 'ReNamn' row with years, then operators."""
    years = ["2003", "2004", "2005"]
    codes = ["NT2000", "NT2000", "NT2000", "NT4000", None, None]  # blank cells repeat the code to the left
    return [
        [None, None, None, *codes],
        [None, None, None, *(["Villa 16A, 5 000 kWh/år, totalt kr/år"] * 3), *(["Villa 20A"] * 3)],
        ["ReNamn", "Företag", "Gruppnamn", *years, *years],
        # operator A: old row to 2003, new row from 2004 (as the real file does)
        ["R1", "A", "", 1000.0, "", "", 2000.0, "", ""],
        ["R1", "A", "", "", 1100.0, 1100.0, "", 2100.0, 2000.0],
        ["R2", "B", "", 900.0, 950.0, 940.0, 0.0, 1900.0, 1950.0],  # 0 = not reported
        ["R3", "C", "", 1200.0, 1300.0, 1400.0, 2400.0, "", 2500.0],
        [None],
    ]


def test_parse_ei_fills_codes_and_skips_text():
    long = el.parse_ei(_ei_rows())
    assert set(long["code"]) == {"NT2000", "NT4000"}
    assert set(long["year"]) == {2003, 2004, 2005}
    assert len(long[(long["operator"] == "R1") & (long["code"] == "NT2000")]) == 3


def test_ei_median_drops_zeros_and_sits_on_december():
    long = el.parse_ei(_ei_rows())
    s = el.ei_median(long, "NT4000")
    assert list(s.index.astype(str)) == ["2003-12", "2004-12", "2005-12"]
    assert s["2003-12"] == pytest.approx(2200.0)  # median of 2000, 2400 (the 0 is dropped)


def test_ei_raise_share_pairs_rows_then_operators():
    long = el.parse_ei(_ei_rows())
    s = el.ei_raise_share(long, "NT2000", min_pairs=2)
    # 2004: rows break for R1, so operators with one value per year: A 1000->1100, B 900->950, C up -> 100 %
    assert s["2004-12"] == pytest.approx(100.0)
    # 2005: same rows: A flat, B down, C up -> 1 of 3
    assert s["2005-12"] == pytest.approx(100 / 3)


def test_ei_archive_url_from_page():
    page = ('<a href="/download/18.1/1/Hush%C3%A5llskunder-eln%C3%A4tsf%C3%B6retagens-eln%C3%A4tsavgifter.xlsx">'
            "Hushållskunder xlsx</a>"
            '<a href="/download/18.2/2/Hush%C3%A5llskunder.xlsx"><span>Hushållskunder 1999-2026 xlsx</span></a>')
    assert el.ei_archive_url(page) == "https://ei.se/download/18.2/2/Hush%C3%A5llskunder.xlsx"
    with pytest.raises(ValueError):
        el.ei_archive_url("<html>no links</html>")


# ------------------------------------------------------------------ SCB


def _tab3571() -> pd.DataFrame:
    rows = []
    for tid, vals in {"2023M01": {"rorligt": 58.9, "anvisat": 9.4},
                      "2023M02": {"rorligt": 52.4, "timpris": 10.4, "anvisat": 8.5}}.items():
        for typ, v in vals.items():
            rows.append({"Elomrade": "00", "Avtalstyp": typ, "ContentsCode": "000003NN", "Tid": tid, "value": v})
    return pd.DataFrame(rows)


def test_contract_share_counts_missing_hourly_as_zero(monkeypatch):
    monkeypatch.setattr(el, "scb_frame", lambda table, codes: _tab3571())
    spot = el.contract_share("rorligt", "timpris")()
    assert spot["2023-01"] == pytest.approx(58.9)
    assert spot["2023-02"] == pytest.approx(62.8)
    hourly = el.contract_share("timpris")()
    assert list(hourly.index.astype(str)) == ["2023-02"]
    with pytest.raises(ValueError):
        el.contract_share("nosuchtype")()


def test_grid_price_on_december(monkeypatch):
    df = pd.DataFrame({"Kundkategori": ["3", "3", "1"], "Viktat": ["viktat"] * 3,
                       "ContentsCode": ["000006QI"] * 3, "Tid": ["2025", "2026", "2026"], "value": [52.2, 55.9, 113.6]})
    monkeypatch.setattr(el, "scb_frame", lambda table, codes: df)
    s = el.grid_price("3")()
    assert list(s.index.astype(str)) == ["2025-12", "2026-12"] and s.iloc[-1] == pytest.approx(55.9)


# ------------------------------------------------------------------ information set


def test_specs_registered_with_lags():
    specs = by_key()
    for k in el.keys():
        assert k in specs and specs[k].area == "energi"
    assert {specs[k].freq for k in el.keys() if k.startswith("el_contract")} == {"M"}
    assert {specs[k].freq for k in el.keys() if "grid" in k} == {"A"}
    assert all(specs[k].revised for k in el.keys() if k.startswith(("el_contract", "ei_")))


def test_january_deadline_sees_last_year_grid_and_previous_month_contracts():
    """At the January Y deadline (4 Feb Y) the 1 January Y tariff is unknown, Y-1 known; contracts up to Dec."""
    deadline = pd.Timestamp("2026-02-04")
    grid = known_from("el_grid_price_house_heat", pd.PeriodIndex(["2025-12", "2026-12"], freq="M"), el.LAG_GRID)
    assert grid[0] <= deadline < grid[1]
    assert grid[1] >= pd.Timestamp("2026-06-11")  # later than both documented 2026 releases
    c = known_from("el_contract_spot_share", pd.PeriodIndex(["2025-12", "2026-01"], freq="M"), el.LAG_CONTRACTS)
    assert c[0] <= deadline < c[1]
    # Annual series: conservative lag 0, known from 31 December Y (only the 2026 release date is documented).
    assert grid[0] == pd.Timestamp("2025-12-31")


def test_contract_corrections_known_only_from_correction_date():
    """TAB3571 May 2023-Jun 2024 was corrected 2024-09-27; the wrong first releases are not available."""
    for k in [k for k in el.keys() if k.startswith("el_contract")]:
        kf = known_from(k, pd.PeriodIndex(["2023-04", "2023-05", "2024-06", "2024-07", "2022-02"], freq="M"),
                        el.LAG_CONTRACTS)
        assert list(kf) == [pd.Timestamp("2023-05-28"), pd.Timestamp("2024-09-27"), pd.Timestamp("2024-09-27"),
                            pd.Timestamp("2024-08-28"), pd.Timestamp("2022-04-30")]


@pytest.mark.skipif(not OBS_PATH.exists(), reason="data/observations.parquet missing")
def test_l5_series_in_observation_table():
    from kpif_nowcast.observations import load

    t = load()
    t = t[t["series"].isin(el.keys())]
    if t.empty:
        pytest.skip("L5 series not fetched")
    assert not t.duplicated(["series", "period", "known_from"]).any()
    share = t[t["series"].str.startswith("el_contract")]
    assert share["value"].between(0, 100).all()
    fixed = t[t["series"] == "el_contract_fixed_share"]
    if not fixed.empty:
        assert fixed["period"].min() == "2013-04"
