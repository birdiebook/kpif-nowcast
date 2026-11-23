"""K11: publication lags and revision flags are locked to docs/publiceringskalender.md.

Changing a Spec's lag_days or revised flag, or a documented late release, without updating the
document (and its evidence) makes these tests fail, so the change is visible in review.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from kpif_nowcast.catalog import CATALOG
from kpif_nowcast.observations import as_of
from kpif_nowcast.publication import LATE_RELEASES, enforce, known_from

DOC = Path(__file__).resolve().parents[1] / "docs" / "publiceringskalender.md"
ROW = re.compile(r"^\| `([a-z0-9_]+)` \| (-?\d+) \| (ja|nej) \|")
LATE_ROW = re.compile(r"^\| `([a-z0-9_*]+)` \| (\d{4}-\d{2}) \| (\d{4}-\d{2}-\d{2}) \|")


def _doc_rows():
    lags, late = {}, {}
    for line in DOC.read_text(encoding="utf-8").splitlines():
        if m := ROW.match(line):
            lags[m.group(1)] = (int(m.group(2)), m.group(3) == "ja")
        elif m := LATE_ROW.match(line):
            late.setdefault(m.group(1), {})[m.group(2)] = m.group(3)
    return lags, late


def test_every_national_spec_is_documented():
    lags, _ = _doc_rows()
    keys = {s.key for s in CATALOG}
    assert keys - lags.keys() == set(), f"not in {DOC.name}: {sorted(keys - lags.keys())}"
    assert lags.keys() - keys == set(), f"in {DOC.name} but not in CATALOG: {sorted(lags.keys() - keys)}"


def test_lags_and_revised_flags_match_document():
    lags, _ = _doc_rows()
    bad = {s.key: ((s.lag_days, s.revised), lags[s.key]) for s in CATALOG if (s.lag_days, s.revised) != lags[s.key]}
    assert not bad, f"catalog (lag, revised) != {DOC.name}: {bad}"


def test_late_releases_match_document():
    _, late = _doc_rows()
    expanded = {}
    for pattern, dates in late.items():
        keys = [k for k in LATE_RELEASES if re.fullmatch(pattern.replace("*", ".*"), k)]
        assert keys, f"{pattern} in {DOC.name} matches no series in publication.LATE_RELEASES"
        for k in keys:
            expanded[k] = dates
    assert expanded == LATE_RELEASES


def test_enforce_only_moves_known_from_later():
    """A December flash backfilled with lag 2 is hidden at the 4 January deadline; nothing moves earlier."""
    rows = [("ea_flash_total", p, v, pd.Timestamp(p) + pd.offsets.MonthEnd(0) + pd.Timedelta(days=2), "backfill",
             pd.Timestamp("2026-11-22")) for p, v in [("2017-11", 1.5), ("2017-12", 1.4)]]
    rows.append(("kpif_yy", "2017-11", 1.9, pd.Timestamp("2017-12-30"), "backfill", pd.Timestamp("2026-11-22")))
    t = pd.DataFrame(rows, columns=["series", "period", "value", "known_from", "source", "fetched_at"])
    e = enforce(t)
    assert (e["known_from"] >= t["known_from"]).all()
    assert e.loc[1, "known_from"] == pd.Timestamp(LATE_RELEASES["ea_flash_total"]["2017-12"])
    assert e.loc[2, "known_from"] == t.loc[2, "known_from"]  # kpif_yy stored later than its lag: kept
    seen = as_of("ea_flash_total", pd.Timestamp("2018-01-04"), e)
    assert list(seen.index.astype(str)) == ["2017-11"]


def test_known_from_uses_later_of_lag_and_release():
    kf = known_from("freight_ppi_deepsea", pd.PeriodIndex(["2025-08", "2025-09"], freq="M"), 21)
    assert list(kf) == [pd.Timestamp("2025-09-21"), pd.Timestamp("2025-11-25")]


def test_k2_feature_set_l_is_frozen():
    """K2's L must not grow with the catalog (it did: 43 -> 72 series when K0 was merged)."""
    from kpif_nowcast.k2_ml import L_KEYS, catalog_keys

    assert len(L_KEYS) == 43 and [k for k, _, _ in catalog_keys()] == [k for k in L_KEYS]
