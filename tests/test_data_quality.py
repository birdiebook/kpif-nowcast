"""Data tests run by the weekly job: the observation table (via DuckDB) and the processed files.

The real-data tests skip when the data has not been fetched; the synthetic test always runs and
shows that each check catches what it is meant to catch.
"""

from __future__ import annotations

import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR
from kpif_nowcast.observations import PATH as OBS_PATH
from kpif_nowcast.warehouse import CHECKS, connect, run_checks


@pytest.fixture(scope="module")
def results():
    if not OBS_PATH.exists():
        pytest.skip("data/observations.parquet missing: run python -m kpif_nowcast.pipeline fetch")
    return run_checks(connect())


@pytest.mark.parametrize("check", list(CHECKS))
def test_observations(results, check):
    bad = results[check]
    assert bad.empty, f"{check}: {len(bad)} violations\n{bad.head(10).to_string()}"


def test_checks_catch_violations(tmp_path):
    """Synthetic table with one duplicate key, one hole and one value known before its month ended."""
    kf = lambda p: pd.Timestamp(p) + pd.offsets.MonthEnd(0) + pd.Timedelta(days=20)  # noqa: E731
    rows = [("kpif_index", p, 100.0, kf(p), "backfill", pd.Timestamp("2026-11-01"))
            for p in ["2026-01", "2026-02", "2026-04"]]  # 2026-03 missing
    rows.append(rows[0])  # duplicate key
    rows.append(("kpif_yy", "2026-05", 1.0, pd.Timestamp("2026-05-10"), "fetch", pd.Timestamp("2026-05-10")))
    path = tmp_path / "obs.parquet"
    pd.DataFrame(rows, columns=["series", "period", "value", "known_from", "source", "fetched_at"]).to_parquet(path)
    res = run_checks(connect(path))
    assert len(res["unique_key"]) == 1
    assert list(res["no_gaps"]["series"]) == ["kpif_index"]
    assert list(res["known_from_after_period_end"]["series"]) == ["kpif_yy"]
    assert res["series_in_catalog"].empty


# ------------------------------------------------------------------ processed files


needs_processed = pytest.mark.skipif(not (PROCESSED_DIR / "kpif.csv").exists(), reason="data/processed missing")


def _contiguous(months: pd.Series) -> bool:
    idx = pd.PeriodIndex(months, freq="M")
    return idx.is_unique and len(idx) == (idx.max() - idx.min()).n + 1


@needs_processed
def test_kpif_monthly_complete():
    from kpif_nowcast.data import load_kpif

    k = load_kpif()
    assert _contiguous(k.index.to_series())
    assert k[["index", "yy_official"]].loc["1988-01":].notna().all().all()


@needs_processed
def test_components_five_per_month_and_sum_to_kpif():
    from kpif_nowcast.data import load_components, load_kpif

    c = load_components()
    per_month = c.groupby("month")["component"].nunique()
    assert (per_month == 5).all()
    assert _contiguous(per_month.index.to_series())
    # contributions add up to KPIF m/m within SCB's rounding
    total = c.pivot(index="month", columns="component", values="effect_month").sum(axis=1)
    mm = load_kpif()["mm_official"].reindex(total.index).dropna()
    assert (total.reindex(mm.index) - mm).loc["2005-01":].abs().max() < 0.1


@needs_processed
def test_features_unique_months_and_energy_history():
    from kpif_nowcast.features import load_features

    f = load_features()
    assert f.index.is_unique
    # J2 V2 trains from 2012: electricity must exist from then (Energinet backfill + elprisetjustnu.se)
    el = f["el_chg"].loc["2012-01":].dropna()
    assert _contiguous(el.index.to_series()) and el.index.min() <= pd.Period("2012-01", "M")
