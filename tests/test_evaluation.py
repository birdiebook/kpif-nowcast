"""Sanity checks for the hand-rolled statistics in evaluation.py."""

import numpy as np
import pytest

from kpif_nowcast.evaluation import dm_test, newey_west_lag, t_two_sided_p


@pytest.mark.parametrize("t, df, p", [(2.0, 10, 0.0734), (3.0, 5, 0.0301), (1.96, 1000, 0.0503), (0.0, 10, 1.0)])
def test_t_p_values_match_tables(t, df, p):
    assert t_two_sided_p(t, df) == pytest.approx(p, abs=1e-4)


def test_lag_rule():
    assert newey_west_lag(34) == 3
    assert newey_west_lag(141) == 4


def test_dm_sign_and_symmetry():
    rng = np.random.default_rng(0)
    e = rng.normal(size=200)
    worse = 1.5 * e
    res = dm_test(e, worse)
    assert res.mean_diff < 0 and res.p < 0.05
    assert dm_test(worse, e).p == pytest.approx(res.p)
