"""K12: SPA, StepM, MCS and the stationary bootstrap behave sensibly on synthetic data."""

import numpy as np
import pandas as pd

from kpif_nowcast.k12_global import (
    analyse,
    dedupe,
    mcs,
    politis_white_block,
    spa_test,
    stationary_bootstrap_indices,
)

N, K, B = 140, 20, 999


def _errors(rng, n=N, k=K, rho=0.5):
    """AR(1)-correlated errors for k models sharing a common component (like real forecast variants)."""
    common = np.zeros(n)
    eps = rng.normal(size=n)
    for t in range(1, n):
        common[t] = rho * common[t - 1] + eps[t]
    return common[:, None] * 0.25 + rng.normal(scale=0.2, size=(n, k))


def test_bootstrap_indices_shape_and_blocks():
    rng = np.random.default_rng(0)
    idx = stationary_bootstrap_indices(100, 500, 5.0, rng)
    assert idx.shape == (500, 100) and idx.min() >= 0 and idx.max() < 100
    cont = np.mean(np.diff(idx, axis=1) % 100 == 1)  # share of steps that continue a block
    assert abs(cont - (1 - 1 / 5)) < 0.02


def test_politis_white_white_noise_short_ar_long():
    rng = np.random.default_rng(1)
    assert politis_white_block(rng.normal(size=500)) < 3
    x = np.zeros(500)
    e = rng.normal(size=500)
    for t in range(1, 500):
        x[t] = 0.8 * x[t - 1] + e[t]
    assert politis_white_block(x) > 5


def test_spa_finds_clearly_better_model():
    rng = np.random.default_rng(2)
    e = _errors(rng, k=K + 1)
    loss_b = np.abs(e[:, K])  # benchmark as good as the noise models ...
    loss = np.abs(e[:, :K])
    loss[:, 0] = loss[:, 0] * 0.6  # ... and model 0 is clearly better than everything
    idx = stationary_bootstrap_indices(N, B, 4.0, np.random.default_rng(3))
    r = spa_test(loss_b, loss, idx)
    assert r["p"]["consistent"] < 0.05
    assert r["stepm"][0.10][0] and r["stepm"][0.10].sum() <= 2
    assert r["adj_p"][0] < 0.05


def test_spa_noise_only_high_p_and_selection_bias_positive():
    rng = np.random.default_rng(4)
    ps, sbs = [], []
    for rep in range(10):
        e = _errors(rng, k=K + 1)
        loss = np.abs(e)
        idx = stationary_bootstrap_indices(N, 499, 4.0, np.random.default_rng(100 + rep))
        r = spa_test(loss[:, 0], loss[:, 1:], idx)
        ps.append(r["p"]["consistent"])
        sbs.append((r["boot_dbar"] - r["dbar"]).max(axis=1).mean())
    assert np.median(ps) > 0.3  # under H0 p should be roughly uniform or larger (conservative)
    assert min(sbs) > 0  # expected best-of-K improvement under H0 is positive


def test_mcs_keeps_best_drops_bad():
    rng = np.random.default_rng(5)
    e = _errors(rng, k=8)
    loss = np.abs(e)
    loss[:, 0] *= 0.5  # clearly best
    loss[:, 7] *= 2.0  # clearly worst
    idx = stationary_bootstrap_indices(N, B, 4.0, np.random.default_rng(6))
    for stat in ("max", "R"):
        p = mcs(loss, idx, stat)
        assert p[0] == 1.0
        assert p[7] < 0.10
        assert np.all((p >= 0) & (p <= 1))


def test_mcs_noise_keeps_most():
    rng = np.random.default_rng(7)
    loss = np.abs(_errors(rng, k=8))
    idx = stationary_bootstrap_indices(N, B, 4.0, np.random.default_rng(8))
    p = mcs(loss, idx, "max")
    assert np.sum(p >= 0.10) >= 6


def test_analyse_and_dedupe_end_to_end():
    rng = np.random.default_rng(9)
    e = _errors(rng, k=5)
    err = pd.DataFrame(e, columns=["rb_updated", "a", "b", "c", "d"])
    err["a"] = err["rb_updated"] * 0.5
    err["dup"] = err["b"]
    err2, alias = dedupe(err, prefer=("rb_updated",))
    assert alias == {"dup": "b"} and "dup" not in err2
    r = analyse(err2, "rb_updated", 4.0, 499, 0)
    assert r["models"][int(np.argmax(r["spa"]["dbar"]))] == "a"
    assert r["spa"]["p"]["consistent"] < 0.05
    assert r["mcs_max"]["a"] == 1.0
