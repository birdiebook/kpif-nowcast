"""L10: run-3 sections of Sverigeläget (travel, rents, Prospera, electricity, krona, flash CPI, calendar, V2)."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from kpif_nowcast import admin_calendar as ac
from kpif_nowcast import observations as obs
from kpif_nowcast import pages
from kpif_nowcast import sverige_dashboard as sd
from kpif_nowcast import sverige_sections as ss

needs_obs = pytest.mark.skipif(not obs.PATH.exists(), reason="data/observations.parquet missing")
RUN3 = ["resor", "hyror", "prospera", "elmarknad", "kronan", "snabbkpi", "admin_events", "admin_yy",
        "admin_upcoming", "v2_eval"]


def _table(series: dict[str, list[tuple[str, float, str]]]) -> pd.DataFrame:
    rows = [{"series": k, "period": p, "value": v, "known_from": pd.Timestamp(kf), "source": "t", "fetched_at": "t"}
            for k, obs_ in series.items() for p, v, kf in obs_]
    return pd.DataFrame(rows)


def _ev(month, pe, kind="one_off", decided=date(2026, 1, 1), coicop="07.2.2", normal=None):
    return ac.AdminEvent(month, coicop, "post", kind, pe, "assumption", decided, f"ev {month}", "https://x.se/a",
                         normal_pe=normal)


def test_run3_datasets_registered_and_read_by_the_page():
    assert set(RUN3) <= set(sd.DATASETS)
    need, _ = pages.page_datasets()
    assert set(RUN3) <= need, set(RUN3) - need


def test_cutoff_drops_values_not_yet_known():
    months = pd.period_range("2024-01", "2025-03", freq="M")
    t = _table({"sek_eur": [(str(p), 11.0 + i / 10, str((p + 1).to_timestamp().date())) for i, p in enumerate(months)]})
    rows = ss.fx_rows(t, cutoff="2025-03-01", start="2024-01")
    assert rows["period"].max() == "2025-02"  # 2025-03 is known from 2025-04-01
    assert (pd.to_datetime(rows["known_from"]) <= pd.Timestamp("2025-03-01")).all()
    feb = rows[rows["period"] == "2025-02"].iloc[0]
    assert feb["yoy_pct"] == pytest.approx((12.3 / 11.1 - 1) * 100)


def test_flash_outcome_is_flash_minus_error():
    t = _table({"kpif_flash_yy": [("2026-09", 1.5, "2026-10-08"), ("2026-10", 1.1, "2026-11-08")],
                "kpif_flash_err_yy": [("2026-09", 0.1, "2026-10-20"), ("2026-10", -0.2, "2026-11-20")]})
    r = ss.flash_rows(t, cutoff="2026-11-10").set_index("period")
    assert r.loc["2026-09", "outcome_yy"] == pytest.approx(1.4)
    assert r.loc["2026-10", "flash_yy"] == 1.1 and pd.isna(r.loc["2026-10", "err_yy"])  # not known yet
    assert pd.isna(r.loc["2026-10", "outcome_yy"])


def test_rent_rows_mark_partial_year():
    kpi = [(str(p), 100 * 1.04 ** (i / 12), str((p + 1).to_timestamp().date() + pd.Timedelta(days=14)))
           for i, p in enumerate(pd.period_range("2023-01", "2025-06", freq="M"))]
    t = _table({"kpi_rent_index": kpi, "rent_negotiated": [("2024-12", 5.15, "2024-06-30"), ("2025-12", 4.8, "2025-06-30")]})
    r = ss.rent_rows(t, cutoff="2025-07-20", first_year=2024).set_index("year")
    assert r.loc[2024, "negotiated_pct"] == 5.15 and not r.loc[2024, "kpi_partial"]
    assert r.loc[2024, "kpi_rent_yy"] == pytest.approx(4.0, abs=1e-6)
    assert r.loc[2025, "kpi_partial"] and r.loc[2025, "kpi_period"] == "2025-06"


def test_admin_yy_counts_a_level_change_for_twelve_months():
    events = [_ev("2026-12", 0.4), _ev("2027-03", -0.1, coicop="01"), _ev("2027-01", 0.2, decided=None),
              _ev("2027-01", 0.05, kind="recurring", coicop="13.3.0", normal=0.04)]
    yy = ss.admin_yy_rows(events, cutoff="2026-11-23", start="2026-11", end="2028-01")
    tot = yy.groupby("period")["total_pe"].first()
    assert tot["2026-11"] == 0.0
    assert tot["2026-12"] == pytest.approx(0.4)
    assert tot["2027-01"] == pytest.approx(0.41)  # + recurring excess 0.05 - 0.04; undecided event left out
    assert tot["2027-03"] == pytest.approx(0.31)
    assert tot["2027-11"] == pytest.approx(0.31)
    assert tot["2027-12"] == pytest.approx(-0.09)  # December event has dropped out after 12 months
    assert tot["2028-01"] == pytest.approx(-0.1)
    by = yy[yy["period"] == "2027-03"].set_index("group")["pe"]
    assert by["drivmedel"] == pytest.approx(0.4) and by["mat"] == pytest.approx(-0.1)
    assert yy.loc[yy["period"] == "2026-12", "future"].all() and not yy.loc[yy["period"] == "2026-11", "future"].any()


def test_admin_rows_respect_the_decision_date():
    events = [_ev("2026-12", 0.4, decided=date(2026, 6, 30)), _ev("2026-12", 0.1, decided=date(2026, 12, 1))]
    ev = ss.admin_event_rows(events, cutoff="2026-11-23")
    assert list(ev["status"]) == ["beslutad", "beslutas senare"]
    up = ss.admin_upcoming_rows(events, None, cutoff="2026-11-23").set_index("month")
    assert up.loc["2026-12", "adjust_yy"] == pytest.approx(0.4) and up.loc["2026-12", "n_not_used"] == 1


def test_admin_upcoming_december_2026_matches_calendar():
    """The real calendar: the routine's suggestion for 2026-12 is +0.52 pe (L1)."""
    up = ss.admin_upcoming_rows(cutoff="2026-11-23").set_index("month")
    assert up.loc["2026-12", "adjust_yy"] == pytest.approx(0.52, abs=0.011)


def test_admin_groups():
    assert ss.admin_group("07.2.2")[0] == "drivmedel" and ss.admin_group("01")[0] == "mat"
    assert ss.admin_group("07.3.5")[0] == "resor" and ss.admin_group("06.2.2")[0] == "ovrigt"
    assert ss.admin_group("04.5.1")[0] == "el" and ss.admin_group("04.4")[0] == "ovrigt"


def test_v2_rows_missing_and_present(tmp_path):
    missing = ss.v2_rows(tmp_path / "resultat.md")
    assert len(missing) == 1 and missing.iloc[0]["status"] == "kommer"
    f = tmp_path / "resultat.md"
    f.write_text("# V2 resultat\n\nIngen serie klarade\nurvalsskärmen.\n\n- punkt ett\n- punkt två\n\n"
                 "| Serie | p |\n|---|---|\n| sek_eur | 0,4 |\n", encoding="utf-8")
    r = ss.v2_rows(f)
    assert list(r["kind"]) == ["heading", "paragraph", "bullet", "bullet", "table_row", "table_row"]
    assert r.iloc[1]["text"] == "Ingen serie klarade urvalsskärmen."
    assert r.iloc[5]["cells"] == ["sek_eur", "0,4"]
    assert (r["status"] == "klar").all()


@needs_obs
def test_real_sections_have_data_known_today():
    table = obs.load()
    today = ss.cutoff_today()
    built = ss.build_all(table, today)
    for name in RUN3:
        assert len(built[name]) > 0, name
    for name in ["resor", "prospera", "elmarknad", "kronan"]:
        kf = pd.to_datetime(built[name]["known_from"].dropna())
        assert len(kf) and (kf <= today).all(), name
    res = built["resor"]
    assert {"guests", "prices", "easter"} <= set(res["group"])
    easter = res[res["group"] == "easter"]
    assert ((easter["march_days"] + easter["april_days"]) == 11).all()  # the 11-day window is in March-April
    pro = built["prospera"]
    assert (pro["p25"] <= pro["p75"]).all() and pro["mean"].between(0, 6).all()  # mean can lie outside P25-P75
    el = built["elmarknad"]
    assert {"contracts", "grid_fee", "grid_raise"} <= set(el["group"])
    assert set(built["kronan"]["key"]) == {"sek_eur", "sek_usd"}
