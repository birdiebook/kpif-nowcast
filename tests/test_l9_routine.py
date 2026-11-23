"""L9: the monthly routine gets the administered-price calendar and Snabb-KPI (no network)."""

from __future__ import annotations

import json
from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from kpif_nowcast import admin_calendar as ac
from kpif_nowcast import champion
from kpif_nowcast import manadsbrev as mb
from kpif_nowcast import observations as obs
from kpif_nowcast import pipeline
from kpif_nowcast import scorecard

EVENTS = ac.all_events()  # without local data: K13 end events use minus the start pe
NOV, DEC = pd.Period("2026-11", "M"), pd.Period("2026-12", "M")


def _ev(month, decided, pe=0.1, label="test"):
    return ac.AdminEvent(month, "07.3.5", "x", "one_off", pe, "assumption", decided, label, "https://example.org/a")


def _index(last="2026-10"):
    idx = pd.period_range("2024-01", last, freq="M")
    return pd.Series([100.0 + 0.1 * i for i in range(len(idx))], index=idx)


# ------------------------------------------------------------------ (a) information date


def test_known_at_requires_decision_by_information_date():
    e = _ev("2026-11", date(2026, 11, 25))
    assert ac.known(e, NOV)  # before the deadline 2026-12-04
    assert not ac.known_at(e, NOV, "2026-11-23")
    assert ac.known_at(e, NOV, "2026-11-25")  # decided that day: known at end of day
    assert ac.known_at(e, NOV, None)
    assert ac.why_not_used(e, NOV, "2026-11-23") == "beslut efter informationsdatumet"
    assert ac.why_not_used(_ev("2026-11", None), NOV, "2026-11-23") == "ej beslutad"
    assert ac.why_not_used(_ev("2026-11", date(2026, 12, 5)), NOV, "2026-12-31") == "beslut efter deadline"
    # the information date never widens the deadline rule
    assert not ac.known_at(_ev("2026-11", date(2026, 12, 5)), NOV, "2027-01-31")


def test_suggest_with_information_date():
    events = [_ev("2026-11", date(2026, 10, 1), 0.2), _ev("2026-11", date(2026, 11, 25), 0.3)]
    s = ac.suggest(NOV, events, info_date="2026-11-23")
    assert s.mm_pe == pytest.approx(0.2) and len(s.listed) == 1
    assert ac.suggest(NOV, events).mm_pe == pytest.approx(0.5)  # deadline rule only
    # the echo of past events also respects the information date
    past = [_ev("2026-10", date(2026, 9, 1), 0.12), _ev("2026-10", date(2026, 11, 24), 0.12)]
    assert ac.suggest(DEC, past, info_date="2026-11-23").echo_pe == pytest.approx(ac.echo(DEC, past[:1]))


def test_december_2026_suggestion_at_letter_date():
    s = ac.suggest(DEC, EVENTS, _index(), "2026-11-23")
    labels = " ".join(e.label for e in s.used)
    assert "Koldioxid" in labels and "Månadskort" in labels
    assert s.adjust == pytest.approx(0.52, abs=0.011)
    early = ac.suggest(DEC, EVENTS, _index(), "2026-06-01")  # CO2 end decided 2026-06-30, cards 2026-10-28
    assert early.used == [] and len(early.listed) >= 2
    assert ac.command(early) is None


def test_to_dict_and_write_outputs(tmp_path):
    j, m = ac.write_outputs("2026-12", "2026-11-23", tmp_path, EVENTS, _index())
    d = json.loads(j.read_text(encoding="utf-8"))
    assert d["status"] == "proposal" and "Johannes" in d["decision"]
    assert d["target_month"] == "2026-12" and d["information_date"] == "2026-11-23" and d["deadline"] == "2027-01-04"
    assert d["adjust_yy_pe"] == pytest.approx(0.52, abs=0.011)
    assert d["command"].startswith("python -m kpif_nowcast.forecast --adjust 0.5")
    assert all(u["sources"] and u["decided"] <= "2026-11-23" for u in d["used"])
    assert all("reason" in u for u in d["not_used"])
    text = m.read_text(encoding="utf-8")
    assert "Beslutade engångshändelser: förslag till manuell justering" in text
    assert "Johannes beslutar" in text and "--adjust 0.5" in text and "https://" in text


# ------------------------------------------------------------------ (a) pipeline step


def test_pipeline_admin_step(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "OUT_DIR", tmp_path)
    monkeypatch.setattr(ac, "_load_parts_and_index", lambda: (None, _index()))
    pipeline.admin_calendar("2026-12", today="2026-11-23")
    d = json.loads((tmp_path / "2026-12.json").read_text(encoding="utf-8"))
    assert d["information_date"] == "2026-11-23"
    pipeline.admin_calendar("2026-12", today="2027-03-01")  # information date capped at the deadline
    d = json.loads((tmp_path / "2026-12.json").read_text(encoding="utf-8"))
    assert d["information_date"] == "2027-01-04"


def test_pipeline_admin_step_not_fatal_in_monthly(monkeypatch, capsys):
    def boom(*a, **k):
        raise RuntimeError("no data")

    monkeypatch.setattr(ac, "write_outputs", boom)
    pipeline.admin_calendar("2026-12", strict=False)
    assert "WARNING: admin calendar failed" in capsys.readouterr().out
    with pytest.raises(RuntimeError):
        pipeline.admin_calendar("2026-12")


def test_pipeline_steps_not_fatal_on_import_error(monkeypatch, capsys):
    import builtins

    real_import = builtins.__import__

    def failing(name, globals=None, locals=None, fromlist=(), level=0):
        if fromlist and any(f in ("admin_calendar", "manadsbrev", "explain") for f in fromlist):
            raise ImportError("simulated")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", failing)
    pipeline.admin_calendar("2026-12", strict=False)
    pipeline.manadsbrev("2026-12", strict=False)
    pipeline.explain(strict=False)
    out = capsys.readouterr().out
    assert "WARNING: admin calendar failed" in out and "WARNING: monthly letter failed" in out
    assert "WARNING: explanation failed" in out
    with pytest.raises(ImportError):
        pipeline.admin_calendar("2026-12")


def test_monthly_runs_admin_before_letter(monkeypatch):
    calls = []
    for name in ["fetch", "fetch_shadow_observations", "shadow", "scorecard", "explain", "admin_calendar", "manadsbrev"]:
        monkeypatch.setattr(pipeline, name, lambda *a, _n=name, **k: calls.append((_n, k.get("strict"))))
    pipeline.main(["monthly"])
    names = [c[0] for c in calls]
    assert names.index("admin_calendar") < names.index("manadsbrev")
    assert ("admin_calendar", False) in calls  # non-fatal


# ------------------------------------------------------------------ (a) monthly letter


def test_letter_admin_section_respects_cutoff():
    events = [_ev("2026-11", date(2026, 10, 1), 0.04, "tidig"), _ev("2026-11", date(2026, 11, 25), 0.3, "sen")]
    lines, facts = mb.section_admin(NOV, pd.Timestamp("2026-11-23 23:59:59"), events, _index())
    text = "\n".join(lines)
    assert "## Beslutade engångshändelser: förslag till manuell justering" in text
    assert "Johannes beslutar" in text and "--adjust 0.04" in text
    assert "beslut efter informationsdatumet" in text and "| sen |" not in text
    assert facts["admin"].mm_pe == pytest.approx(0.04)
    assert "**Beslut:**" in text  # the 2026-11 decision was made 2026-11-23, by the cutoff
    lines, _ = mb.section_admin(NOV, pd.Timestamp("2026-11-22 23:59:59"), events, _index())
    assert "**Beslut:**" not in "\n".join(lines)
    lines, facts = mb.section_admin(NOV, pd.Timestamp("2026-12-04 23:59:59"), events, _index())
    assert facts["admin"].mm_pe == pytest.approx(0.34)


def _rb_fc():
    rows = []
    for rnd, cutoff, pub, val in [("2026:3", "2026-08", "2026-09-24", 2.0), ("2026:4", "2026-10", "2026-11-25", 9.9)]:
        for m in pd.period_range("2026-09", "2027-12", freq="M"):
            rows.append({"policy_round": rnd, "cutoff": pd.Period(cutoff, "M"), "published": pd.Timestamp(pub),
                         "month": m, "value": val})
    return pd.DataFrame(rows)


def test_letter_preview_next_month():
    lines, facts = mb.section_preview(NOV, pd.Timestamp("2026-11-23 23:59:59"), EVENTS, _index(), _rb_fc(),
                                      {"live": 2.1})
    text = "\n".join(lines)
    assert text.startswith("## Förhandsvisning: december 2026")
    assert "Koldioxid" in text and "+0,52 pe" in text and "Johannes beslutar" in text
    assert facts["preview"].adjust == pytest.approx(0.52, abs=0.011)
    assert facts["rb_next"] == 2.0  # the round published after the cutoff is not used
    assert "2026:4" not in text


def test_admin_inputs_cut_to_previous_month(monkeypatch):
    idx = pd.period_range("2026-01", "2026-12", freq="M")
    parts = pd.DataFrame({"en": 0.0, "ne": 0.0}, index=idx)
    parts.loc[pd.Period("2026-07", "M"), "en"] = -0.5
    monkeypatch.setattr(ac, "_load_parts_and_index", lambda: (parts, pd.Series(100.0, index=idx)))
    events, index = mb.admin_inputs(pd.Period("2026-06", "M"))
    assert index.index.max() == pd.Period("2026-05", "M")
    co2_end = next(e for e in events if e.month == "2026-12" and e.origin == "K13")
    assert co2_end.method == "assumption"  # the realised July part is not known for a June letter
    events, _ = mb.admin_inputs(DEC)
    co2_end = next(e for e in events if e.month == "2026-12" and e.origin == "K13")
    assert co2_end.pe == pytest.approx(0.5) and co2_end.method == "scb_ks"


def test_letter_has_new_sections_without_model_data(monkeypatch):
    """Assembly: the calendar sections and the headline bullet are in the letter even without the explanation."""
    def no_cut(*a, **k):
        raise ValueError("no model data in this test")

    monkeypatch.setattr(mb, "cut_inputs", no_cut)
    monkeypatch.setattr(ac, "_load_parts_and_index", lambda: (None, None))
    idx = pd.period_range("2024-01", "2026-12", freq="M")
    inp = SimpleNamespace(kpif=pd.DataFrame({"index": [100.0 + 0.1 * i for i in range(len(idx))]}, index=idx),
                          rb_fc=_rb_fc())
    text = mb.build("2026-11", table=obs._empty(), inp=inp, info={}, today="2026-11-23", with_k2=False)
    assert "## Beslutade engångshändelser: förslag till manuell justering" in text
    assert "## Förhandsvisning: december 2026" in text
    assert "Beslutade engångshändelser (kalendern för administrerade priser, förslag)" in text
    assert text.index("## Beslutade engångshändelser") < text.index("## Förhandsvisning") < text.index("## Läget")


# ------------------------------------------------------------------ (b) Snabb-KPI as a reference


def _flash_case():
    m = pd.period_range("2024-09", "2024-12", freq="M")
    actual = pd.Series([1.0, 1.5, 2.0, 2.5], index=m)
    flash = pd.Series([1.0, 1.6, 2.0, 2.5], index=m)
    pred = pd.DataFrame({"a": [1.2, 1.5, 2.0, 2.4], "b": [1.0, 1.0, None, 2.5]}, index=m)
    return pred, actual, flash


def test_flash_reference_same_months_and_flash_row():
    pred, actual, flash = _flash_case()
    df, meta = champion.flash_reference(pred, actual, flash)
    assert meta["n"] == 3  # 2024-11 missing for b -> dropped for all
    assert df.loc["a", "MAE mot snabb-KPI"] == pytest.approx((0.2 + 0.1 + 0.1) / 3)
    assert df.loc["a", "MAE mot utfall"] == pytest.approx((0.2 + 0.0 + 0.1) / 3)
    assert df.loc["b", "Andel inom ±0,1 av snabb"] == pytest.approx(2 / 3)
    assert df.loc["snabb_kpi", "MAE mot utfall"] == pytest.approx(0.1 / 3)
    assert meta["flash_n_nonzero"] == 1 and meta["flash_max_abs"] == pytest.approx(0.1)
    # the flash row is always measured against the same outcome as the models; the error against the
    # first-published outcome is reported separately, never mixed into the table
    err = pd.Series([0.0, 0.2, 0.0, 0.0], index=flash.index)
    df2, meta2 = champion.flash_reference(pred, actual, flash, err)
    assert df2.loc["snabb_kpi", "MAE mot utfall"] == pytest.approx(0.1 / 3) and meta2["flash_n_nonzero"] == 1
    assert meta2["first_pub_n"] == 3 and meta2["first_pub_n_nonzero"] == 1
    assert meta2["first_pub_mae"] == pytest.approx(0.2 / 3)
    assert "först publicerat utfall" in "\n".join(champion.flash_lines(df2, meta2))
    assert "först publicerat utfall" not in "\n".join(champion.flash_lines(df, meta))
    text = "\n".join(champion.flash_lines(df, meta))
    assert "### Snabb-KPI som referens" in text and "n = 3" in text and "p-värde" not in text
    assert "Ingen månad" in "\n".join(champion.flash_lines(*champion.flash_reference(pred, actual, flash.iloc[:0])))


def test_scorecard_flash_live_lines():
    live = pd.DataFrame({"month": [pd.Period("2026-11", "M"), pd.Period("2026-12", "M"), pd.Period("2027-01", "M")],
                         "forecast_yy": [2.12, 2.6, 2.0], "outcome": [2.0, None, None]})
    flash = pd.Series([2.1, 2.4], index=pd.PeriodIndex(["2026-11", "2026-12"], freq="M"))
    text = "\n".join(scorecard.flash_live_lines(live, flash))
    assert "2026-11" in text and "2026-12" in text and "2027-01" not in text
    assert "0.02" in text and "0.1" in text and "0.12" in text  # prognos−snabb, snabb−utfall, prognos−utfall
    assert "0.2" in text  # 2026-12: forecast − flash before the outcome
    empty = "\n".join(scorecard.flash_live_lines(live, flash.iloc[:0]))
    assert "finns ännu inte" in empty


needs_obs = pytest.mark.skipif(not obs.PATH.exists(), reason="data/observations.parquet missing")


@needs_obs
def test_flash_series_in_observation_table():
    fl, err = champion.load_flash()
    assert fl.index.min() == pd.Period("2024-09", "M") and len(fl) >= 26
    assert err.abs().max() <= 0.1 + 1e-9
