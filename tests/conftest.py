"""Shared test setup.

Thread limits: the K2 shadow models fit scikit-learn's HistGradientBoostingRegressor (OpenMP) in nested CV on
~100-140 rows, 33 fits per forecast. With the default one OpenMP thread per core, every boosting iteration pays
thread start/sync costs that dwarf the work, and with several pytest-xdist workers (or other jobs) on the same
cores the threads spin against each other: one nested fit took >12 min instead of ~2 s (docs/auto3/l8/resultat.md).
One thread per process is what parallel test runs want anyway. Set before numpy/scikit-learn are imported by any
test module (conftest.py is imported first); an explicit value in the environment wins.

Results: tests compare a model with itself (cut vs full data, same process, same thread count), so the thread
count cannot change what they check. Production runs are not affected (they do not import this file).
"""

from __future__ import annotations

import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import hashlib

import pandas as pd
import pytest


def _digest(obj) -> str:
    """Content hash of a frame/series (values, index, columns, dtypes); repr for everything else."""
    h = hashlib.sha256()
    if isinstance(obj, pd.DataFrame):
        h.update(pd.util.hash_pandas_object(obj, index=True).to_numpy().tobytes())
        h.update(repr((list(obj.columns), obj.dtypes.astype(str).tolist(), obj.shape)).encode())
    elif isinstance(obj, pd.Series):
        h.update(pd.util.hash_pandas_object(obj, index=True).to_numpy().tobytes())
        h.update(repr((obj.name, str(obj.dtype), obj.shape)).encode())
    else:
        h.update(repr(obj).encode())
    return h.hexdigest()


@pytest.fixture(scope="session")
def memo_champion():
    """Memoize champion.histories (every shadow model over the whole history, incl. K2's nested CV: minutes) on
    the content of its Inputs. sverige_dashboard.main and each manadsbrev.build call it; within one process the
    K5/K10 tests call it several times with identical inputs, and the function is deterministic, so a repeat
    returns a copy of the first result. The key includes the shadow registry (name and function identity), so a
    test that swaps a model gets a fresh computation. Used explicitly by test_k5.py and test_k10_pages.py.
    """
    from kpif_nowcast import champion
    from kpif_nowcast.shadow import SHADOW_MODELS

    original = champion.histories
    cache: dict = {}

    def histories(inp):
        key = (tuple((n, id(m.fn)) for n, m in SHADOW_MODELS.items()),
               tuple(_digest(getattr(inp, f)) for f in ("kpif", "comps", "feats", "rb_fc", "obs", "rows_from")))
        if key not in cache:
            cache[key] = original(inp)
        return cache[key].copy()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(champion, "histories", histories)
        yield cache
