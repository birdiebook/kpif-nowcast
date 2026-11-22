"""J7: AI indicator helpers. Uses only cached responses; skips when the cache is empty."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.j7_ai import RAW, ROOT, build, snippet, tidy_rows, zscore


def test_snippet_matches_whole_word_only():
    assert "AI" in snippet("Vi söker en AI-utvecklare", "AI")
    assert snippet("detail and maintenance", "AI").startswith("(termen")


def test_zscore():
    z = zscore(pd.Series([1.0, 2.0, 3.0]))
    assert np.isclose(z.mean(), 0) and np.isclose(z.std(), 1)


@pytest.mark.skipif(not RAW.exists() or not any(RAW.glob("search_*.json")), reason="JobTech cache empty")
def test_build_from_cache():
    approved = json.loads((ROOT / "docs" / "auto" / "j7" / "approved_terms.json").read_text(encoding="utf-8"))
    assert approved[0] == "maskininlärning"
    res = build(approved)
    share = res["share"]["maskininlärning"]
    assert share.index.min() == 2016 and share.index.max() == 2025 and (share > 0).all()
    rows = tidy_rows(res)
    assert {"ad_share_per_10k", "firm_ai_use_pct", "productivity_per_hour_2015_100"} <= set(rows["series"])
