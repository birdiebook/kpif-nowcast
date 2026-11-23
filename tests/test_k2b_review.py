"""K2b review: the information-set test has power, the flash correction works, K2's feature list is frozen."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.k2_ml import K2_CATALOG_KEYS, catalog_keys
from kpif_nowcast.k2b_review import realistic_flash
from kpif_nowcast.riksbank_benchmark import deadline


def test_k2_feature_set_l_is_frozen():
    keys = [k for k, _, _ in catalog_keys()]
    assert keys == list(K2_CATALOG_KEYS) and len(keys) == 43


def test_realistic_flash_moves_late_releases_past_the_deadline():
    obs = pd.DataFrame({
        "series": ["ea_flash_total", "ea_flash_food", "ea_flash_total", "ea_flash_total", "kix"],
        "period": ["2018-12", "2027-12", "2018-03", "2018-11", "2018-12"],
        "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        "known_from": pd.to_datetime(["2019-01-02", "2028-01-02", "2018-04-02", "2018-12-02", "2019-01-01"]),
    })
    out = realistic_flash(obs)
    for i, p in [(0, "2018-12"), (1, "2027-12"), (2, "2018-03")]:
        assert out["known_from"].iat[i] > deadline(pd.Period(p, "M")), p
    assert out["known_from"].iat[3] == obs["known_from"].iat[3]  # November: released before day 4
    assert out["known_from"].iat[4] == obs["known_from"].iat[4]  # other series untouched


from kpif_nowcast.data import PROCESSED_DIR  # noqa: E402

needs_data = pytest.mark.skipif(not (PROCESSED_DIR / "el_contracts.csv").exists(), reason="data missing")


@needs_data
def test_information_set_check_detects_a_code_leak(monkeypatch):
    """Sabotage: let build_design read catalog series 31 days past the deadline. The cut-vs-full
    comparison used in test_k2_ml must then see a different forecast (the check has power)."""
    pytest.importorskip("sklearn")
    import kpif_nowcast.k2_ml as k2
    from kpif_nowcast.data import load_components, load_el_contracts, load_kpif, load_riksbank_forecasts
    from kpif_nowcast.features import load_features
    from kpif_nowcast.j2_el import zone_monthly_spot
    from kpif_nowcast.observations import load as load_obs

    warnings.filterwarnings("ignore")
    kpif, comps, feats, contracts, se3, rb_fc, obs = (load_kpif(), load_components(), load_features(),
                                                     load_el_contracts(), zone_monthly_spot("SE3"),
                                                     load_riksbank_forecasts(), load_obs())
    monkeypatch.setattr(k2, "deadline", lambda t: deadline(t) + pd.Timedelta(days=31))
    t = pd.Period("2023-02", "M")
    d = deadline(t)
    full = k2.build_design(kpif, comps, feats, contracts, se3, rb_fc, obs)
    cut = k2.build_design(kpif.loc[: t - 1], comps[comps["month"] <= t - 1], feats.loc[:t],
                          contracts[contracts["month"] <= t - 1], se3.loc[:t],
                          rb_fc[rb_fc["published"] < d], obs[obs["known_from"] <= d])
    a, b = k2.forecast_at(cut, t, "k2_avg_ridge_l"), k2.forecast_at(full, t, "k2_avg_ridge_l")
    assert not np.isclose(a, b, rtol=0, atol=1e-10)
