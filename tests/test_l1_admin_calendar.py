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
    assert any("tobak" in e.label.lower() for e in j.listed)


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


# ---------------------------------------------------------------- L1b: primary-source check (2026-11-23)
def test_every_event_has_verification_note():
    for e in EVENTS:
        assert e.verified.startswith(ac.VERIFIED_PREFIX), e
        if e.verified.startswith("2026-11-23"):
            assert any(u.startswith(("https://data.riksdagen.se/", "https://www.riksdagen.se/",
                                     "https://www.skatteverket.se/", "https://www.regeringen.se/",
                                     "https://www.scb.se/")) for u in e.source.split()) or e.origin == "K13", e


def test_k13_events_unchanged_and_decision_fix_only_later():
    # K13's variants must stay reproducible: EVENTS untouched, fixes live in admin_calendar only
    assert [(e.month, e.decided) for e in k13_tax.EVENTS][3] == ("2026-04", date(2025, 11, 30))
    for month, fixed in ac.K13_DECIDED_FIX.items():
        orig = next(e for e in k13_tax.EVENTS if e.month == month)
        assert fixed > orig.decided  # a fix may only move a decision later (never create leakage)
        conv = next(e for e in EVENTS if e.origin == "K13" and e.month == month)
        assert conv.decided == fixed and conv.decided < deadline(conv.period).date()
    assert set(ac.K13_VERIFIED) == {e.month for e in k13_tax.EVENTS}


def test_verified_corrections():
    by = {(e.month, e.coicop, e.kind): e for e in EVENTS}
    assert by[("2016-01", "07.2.2", "one_off")].decided == date(2015, 11, 25)
    assert all("H301SkU18" not in e.source for e in EVENTS)  # wrong betänkande (decided March 2016)
    assert by[("2025-05", "04.3", "one_off")].decided == date(2025, 5, 7)
    assert by[("2028-01", "01", "end")].decided == date(2026, 2, 25)
    tob = by[("2027-01", "02.3", "one_off")]
    assert tob.pe == 0.0 and tob.decided == date(2026, 11, 12)
    assert by[("2025-07", "07.2.2", "one_off")].pe == 0.0  # tax cut offset by the reduction obligation
    assert by[("2027-01", "13.3.0", "recurring")].decided == date(2026, 9, 24)


def test_suggestions_unchanged_by_source_check():
    assert ac.suggest("2026-12", EVENTS).mm_pe == pytest.approx(0.398 + 0.156 * ac.SHARE_REST, abs=0.002)
    assert ac.suggest("2027-01", EVENTS).mm_pe == pytest.approx(-0.026, abs=0.002)


# ---------------------------------------------------------------- L1b review round (2026-11-23)
DECIDED_SNAPSHOT = {  # L1b, 2026-11-23: every decision date checked against a primary source
    ('2016-01', '07.2.2', 'Höjd energiskatt'): '2015-11-25',
    ('2016-01', '07.2.4', 'Höjd trängselska'): '2015-12-31',
    ('2017-07', '05.3.1', 'Ny kemikalieskat'): '2016-11-24',
    ('2018-04', '07.3.3', 'Ny flygskatt (la'): '2017-11-30',
    ('2019-01', '08.3.9', 'Radio- och tv-av'): '2018-11-14',
    ('2019-07', '06.2.2', 'Ny metod för all'): '2019-08-14',
    ('2022-05', '07.2.2', 'Tillfälligt sänk'): '2022-04-30',
    ('2022-10', '07.2.2', 'Sänkningen från '): '2022-04-30',
    ('2024-01', '07.2.2', 'Reduktionsplikte'): '2023-11-30',
    ('2025-05', '04.3', 'ROT-avdraget 30 '): '2025-05-07',
    ('2025-07', '06.1.1', 'Höjt högkostnads'): '2025-05-22',
    ('2025-07', '07.2.2', 'Energiskatten på'): '2025-05-22',
    ('2025-07', '07.3.3', 'Flygskatten avsk'): '2024-11-27',
    ('2026-01', '04.3', 'ROT 50 % upphör '): '2025-05-07',
    ('2026-01', '04.5.1', 'Sänkt energiskat'): '2025-11-30',
    ('2026-01', '06.2.2', 'Tandvårdsstöd fö'): '2025-12-08',
    ('2026-04', '01', 'Matmomsen 12 → 6'): '2026-02-25',
    ('2026-05', '07.2.2', 'Tillfälligt sänk'): '2026-04-30',
    ('2026-07', '07.2.2', 'Tillfälligt sänk'): '2026-06-30',
    ('2026-07', '07.3.5', 'Halverat pris på'): '2026-06-25',
    ('2026-07', '09.4.6', 'Dansbandsmoms 25'): '2026-05-20',
    ('2026-07', '10.1.0', 'Fribelopp i maxt'): '2026-06-30',
    ('2026-07', '13.3.0', 'Fribelopp i maxt'): '2026-06-30',
    ('2026-10', '07.2.2', 'Energiskattesänk'): '2026-04-30',
    ('2026-11', '07.3.5', 'Månadskort åter '): '2026-10-28',
    ('2026-12', '07.2.2', 'Koldioxidskattes'): '2026-06-30',
    ('2026-12', '07.3.5', 'Månadskort åter '): '2026-10-28',
    ('2027-01', '02.3', 'Aviserad tobakss'): '2026-11-12',
    ('2027-01', '04.4', 'Kommunala VA- oc'): None,
    ('2027-01', '04.5.1', 'Energiskatt på e'): '2026-11-12',
    ('2027-01', '04.5.1', 'Elnätsavgifter i'): None,
    ('2027-01', '07.2.2', 'Ordinarie indexe'): '2026-11-23',
    ('2027-01', '07.3.5', 'Halland: rabatte'): '2026-10-28',
    ('2027-01', '07.3.5', 'Västtrafik: förl'): None,
    ('2027-01', '13.3.0', 'Prisbasbeloppet '): '2026-09-24',
    ('2028-01', '01', 'Matmomsen 6 → 12'): '2026-02-25',
}


def test_decision_dates_frozen():
    # Guards the leakage rule for L1 rows as well as K13 rows: a decision date may change only together with
    # this snapshot, after a primary-source check (an earlier date needs the source in `verified`).
    got = {(e.month, e.coicop, e.label[:16]): e.decided.isoformat() if e.decided else None for e in EVENTS}
    assert got == DECIDED_SNAPSHOT
    assert all(e.decided is None or e.decided <= ac.CURATED for e in EVENTS)


def test_flight_tax_abolition_and_review_fixes():
    by = {(e.month, e.coicop, e.kind): e for e in EVENTS}
    fly = by[("2025-07", "07.3.3", "one_off")]
    assert fly.pe < 0 and fly.decided == date(2024, 11, 27) and fly.in_ks and "sfs-2017-1200" in fly.source
    assert "HC01FiU1" in by[("2025-07", "07.2.2", "one_off")].source  # tax cut decided in BP 2025
    s = ac.suggest("2026-12", EVENTS)
    assert "skatteverket.se" in s.note().split(";")[0]  # CO2 end cites Skatteverket's December rates first
    assert "[delvis verifierad]" in s.note() and "sfs-2026-1391" in s.note()
    assert "[overifierad]" in ac.suggest("2027-01", EVENTS).note()
    assert "varav delvis verifierat" in ac.report(s)
