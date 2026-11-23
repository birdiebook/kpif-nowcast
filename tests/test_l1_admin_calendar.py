"""L1 administered-price calendar: structure, leakage rule, K13 reuse, the suggestion command."""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from kpif_nowcast import admin_calendar as ac
from kpif_nowcast import k13_tax
from kpif_nowcast.riksbank_benchmark import deadline

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ac.all_events()  # without local data: K13 end events use minus the start pe


def test_structure():
    assert len(ac.ADMIN_EVENTS) >= 20
    for e in EVENTS:
        assert re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", e.month), e
        assert e.kind in ac.KINDS and e.method in ac.METHODS, e
        assert re.fullmatch(r"\d\d(\.\d(\.\d)?)?", e.coicop), e
        assert e.label and e.post
        assert all(u.startswith("https://") for u in e.source.split()) or e.source == ac.DOC, e
        assert e.decided is None or e.decided <= ac.CURATED, e
        if e.pe is not None:
            assert abs(e.pe) < 1.0, e
        if e.method in ("weight_x_change", "observed"):
            assert e.weight and e.change_pct is not None, e
            assert e.pe == pytest.approx(e.weight * e.change_pct / 1000, abs=0.0015), e
        if e.kind == "recurring":
            assert e.normal_pe is None or e.pe is not None
        else:
            assert e.normal_pe is None


def test_coverage_from_2015_and_next_routines():
    months = {e.month for e in EVENTS}
    assert min(months) <= "2016-01"
    for m in ("2026-11", "2026-12", "2027-01"):
        assert m in months
    years = {int(m[:4]) for m in months}
    assert {2016, 2017, 2018, 2019, 2022, 2024, 2025, 2026, 2027} <= years


def test_k13_reused_not_duplicated():
    assert len(k13_tax.EVENTS) == 8  # K13's registered variants must stay reproducible
    k13 = [e for e in EVENTS if e.origin == "K13"]
    assert [e.month for e in k13] == sorted(ev.month for ev in k13_tax.EVENTS)
    keys = {(e.month, e.coicop) for e in k13}
    assert not [e for e in ac.ADMIN_EVENTS if (e.month, e.coicop) in keys]
    for e, ev in zip(sorted(k13, key=lambda x: x.month), sorted(k13_tax.EVENTS, key=lambda x: x.month)):
        if ev.kind == "start":
            assert e.pe == pytest.approx(ev.pe, abs=5e-4)
        for t in (ev.period, ev.period + 1, ev.period - 1):
            assert ac.known(e, t) == k13_tax.known(ev, t)


def test_k13_end_uses_realised_part_when_given():
    parts = pd.DataFrame({"en": [-0.20], "ne": [0.0]}, index=pd.PeriodIndex(["2026-07"], freq="M"))
    dec = next(e for e in ac.k13_events(parts) if e.month == "2026-12")
    assert dec.pe == pytest.approx(0.20) and dec.method == "scb_ks"
    dec0 = next(e for e in ac.k13_events(None) if e.month == "2026-12")
    assert dec0.pe == pytest.approx(0.398) and dec0.method == "assumption"


def _ev(month, decided, pe=0.1, kind="one_off", normal=None):
    return ac.AdminEvent(month, "07.3.5", "x", kind, pe, "assumption", decided, "test", "https://example.org",
                         normal_pe=normal)


def test_leakage_rule():
    t = pd.Period("2027-01", "M")
    dl = deadline(t).date()  # 2027-02-04
    assert dl == date(2027, 2, 4)
    events = [_ev("2027-01", dl), _ev("2027-01", date(2027, 2, 3), 0.2), _ev("2027-01", None, 0.4)]
    s = ac.suggest(t, events)
    assert s.mm_pe == pytest.approx(0.2)
    assert len(s.used) == 1 and len(s.listed) == 2
    # nothing from other months, and a later decision never leaks into an earlier target
    s2 = ac.suggest("2026-12", events + [_ev("2026-12", date(2027, 1, 5))])
    assert s2.mm_pe == 0.0 and s2.used == []


def test_recurring_only_excess():
    e = _ev("2027-01", date(2026, 9, 30), pe=0.010, kind="recurring", normal=0.041)
    assert e.suggest_pe == pytest.approx(-0.031)
    assert replace(e, normal_pe=None).suggest_pe == 0.0
    assert replace(e, pe=None).suggest_pe == 0.0


def test_echo_is_trend_share():
    t = pd.Period("2026-12", "M")
    events = [_ev("2026-11", date(2026, 10, 1), pe=0.12)]
    assert ac.echo(t, events) == pytest.approx(0.01)
    assert ac.echo(t, [_ev("2026-11", None, pe=0.12)]) == 0.0  # undecided: not in the echo either
    assert ac.echo(t, [_ev("2026-12", date(2026, 10, 1))]) == 0.0  # same month: not history


def test_suggestion_2026_12_and_2027_01():
    s = ac.suggest("2026-12", EVENTS)
    labels = " ".join(e.label for e in s.used)
    assert "Koldioxid" in labels and "Månadskort" in labels
    assert s.mm_pe == pytest.approx(0.398 + 0.156 * ac.SHARE_REST, abs=0.002)
    idx = pd.Series([100.0 + i * 0.1 for i in range(24)], index=pd.period_range("2025-01", periods=24, freq="M"))
    s_idx = ac.suggest("2026-12", EVENTS, idx)
    assert s_idx.yy_factor == pytest.approx(idx[pd.Period("2026-11", "M")] / idx[pd.Period("2025-12", "M")])
    assert s_idx.adjust == round(s_idx.mm_pe * s_idx.yy_factor, 2)
    j = ac.suggest("2027-01", EVENTS)
    assert all(e.decided is not None for e in j.used)
    assert any("Tobak" in e.label for e in j.listed)


def test_command(capsys, monkeypatch):
    monkeypatch.setattr(ac, "_load_parts_and_index", lambda: (None, None))
    ac.main(["2026-12"])
    out = capsys.readouterr().out
    m = re.search(r'--adjust (-?\d+\.\d\d) --note "admin_calendar 2026-12: ([^"]+)"', out)
    assert m and float(m.group(1)) == pytest.approx(0.51, abs=0.011)
    assert "Koldioxid" in m.group(2) and "https://" in m.group(2)
    ac.main(["2015-03"])
    assert "ingen justering" in capsys.readouterr().out
    ac.main(["--table"])
    table = capsys.readouterr().out.strip().splitlines()
    assert len(table) == len(EVENTS) + 2


def test_doc_lists_every_event():
    doc = (ROOT / "docs" / "administrerade-priser.md").read_text(encoding="utf-8")
    for e in EVENTS:
        assert f"| {e.month} | {e.coicop} |" in doc and e.label in doc, e
