"""J6: Arbetsförmedlingen series - parsing, catalog hook and point-in-time availability.

J6 builds no forecast, so the information-set test checks what a forecast for t may see:
with a 15-day lag, AF data for month t is NOT known at t's deadline (day 4 of t+1), month t-1 is.
"""

from __future__ import annotations

import pandas as pd
import pytest

from kpif_nowcast import observations as obs
from kpif_nowcast.catalog import by_key
from kpif_nowcast.catalog_af import _cached, _period, parse_sok, parse_varsel
from kpif_nowcast.riksbank_benchmark import deadline

KEYS = ["af_varsel", "af_inskrivna_arbetslosa", "af_oppet_arbetslosa"]


def test_specs_in_catalog():
    cat = by_key()
    for k in KEYS:
        assert k in cat and cat[k].freq == "M" and cat[k].lag_days >= 15
    assert cat["af_varsel"].revised


def test_period_labels():
    assert _period("199201") == pd.Period("1992-01", "M")
    assert _period("2026-10") == pd.Period("2026-10", "M")
    assert _period("SNI_KOD") is None


@pytest.mark.parametrize("name,parser,start", [
    ("web-varsel-bransch-199201-2026-10.xlsx", parse_varsel, "1992-01"),
    ("web-sok-riket-2026-10.xlsx", lambda p: parse_sok(p)["Inskrivna arbetslösa"], "1996-01"),
])
def test_parsers_on_cached_files(name, parser, start):
    path = _cached(name)
    if path is None:
        pytest.skip("AF file not cached")
    s = parser(path).dropna()
    assert s.index.min() == pd.Period(start, "M")
    assert len(pd.period_range(s.index.min(), s.index.max(), freq="M").difference(s.index)) == 0
    assert (s >= 0).all()


def test_af_month_t_not_known_at_deadline():
    table = obs.load()
    if table[table["series"] == "af_varsel"].empty:
        pytest.skip("AF series not loaded")
    for t in [pd.Period(m, "M") for m in ["2015-06", "2020-03", "2026-09"]]:
        for k in KEYS:
            s = obs.as_of(k, deadline(t), table)
            assert s.index.max() == t - 1, f"{k} {t}: latest known {s.index.max()}"
