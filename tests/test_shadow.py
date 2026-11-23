"""Shadow forecasts: information set per registered model, write rules, and workflow hygiene.

Any model added to SHADOW_MODELS (e.g. K2's candidate) is picked up by the information-set test.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from kpif_nowcast.data import PROCESSED_DIR
from kpif_nowcast.riksbank_benchmark import deadline
from kpif_nowcast.shadow import SHADOW_MODELS, Inputs, should_write, status

REPO = Path(__file__).resolve().parents[1]
WORKFLOW_DIRS = [REPO / ".github" / "workflows", REPO / "ci" / "workflows"]
needs_data = pytest.mark.skipif(not (PROCESSED_DIR / "features.csv").exists(), reason="data/processed missing")
MONTHS = pd.period_range("2015-03", "2026-10", freq="M")[::9]  # fixed sample, includes recent months
MONTHS = MONTHS.append(pd.PeriodIndex(["2024-06", "2025-12", "2026-10"], freq="M"))


@pytest.fixture(scope="module")
def inputs():
    from kpif_nowcast.data import load_components, load_kpif, load_riksbank_forecasts
    from kpif_nowcast.features import load_features

    from kpif_nowcast.observations import load

    return Inputs(load_kpif(), load_components(), load_features(), load_riksbank_forecasts(), load())


def cut(inp: Inputs, t: pd.Period) -> Inputs:
    """Exactly what is known at t's deadline: outcomes to t-1, energy prices for t, earlier vintages,
    observations with known_from <= deadline (as_of's rule). rows_from=t, as in the live run."""
    rb = inp.rb_fc[inp.rb_fc["published"] < deadline(t)]
    obs = inp.obs[inp.obs["known_from"] <= deadline(t)]
    return Inputs(inp.kpif.loc[: t - 1], inp.comps[inp.comps["month"] <= t - 1], inp.feats.loc[:t], rb, obs, t)


# expensive models (nested CV per month) are checked on fewer months
SLOW = {"k2_avg_ens_s", "k2_avg_ridge_l"}
SLOW_MONTHS = pd.PeriodIndex(["2019-06", "2023-02", "2026-10"], freq="M")


@needs_data
@pytest.mark.parametrize("name", list(SHADOW_MODELS))
def test_shadow_model_uses_only_deadline_data(inputs, name):
    from dataclasses import replace

    slow = name in SLOW
    full = None if slow else SHADOW_MODELS[name].fn(inputs)["yy_hat"]
    checked = 0
    for t in SLOW_MONTHS if slow else MONTHS:
        if slow:
            full = SHADOW_MODELS[name].fn(replace(inputs, rows_from=t))["yy_hat"]
        if t not in full.index or pd.isna(full[t]):
            continue
        live = SHADOW_MODELS[name].fn(cut(inputs, t))["yy_hat"]
        assert live.index.max() == t, f"{name} {t}: cut data should forecast exactly month t"
        assert np.isclose(live[t], full[t], rtol=0, atol=1e-10), f"{name} {t}: {live[t]} vs {full[t]}"
        checked += 1
    assert checked >= 3, f"{name}: too few months checked ({checked})"


@needs_data
def test_j2_shadow_does_not_need_contract_data(inputs):
    """The shadow passes empty contract/SE3 frames; J2 V2 must be identical to the J2 run with them."""
    from kpif_nowcast.data import load_el_contracts
    from kpif_nowcast.j2_el import build_j2_features, j2_forecast, zone_monthly_spot

    if not (PROCESSED_DIR / "el_contracts.csv").exists():
        pytest.skip("el_contracts.csv missing")
    j2f = build_j2_features(inputs.feats, load_el_contracts(), zone_monthly_spot("SE3"))
    ref = j2_forecast(inputs.kpif["index"], inputs.comps, j2f, "j2_el_dev")["yy_hat"]
    shadow = SHADOW_MODELS["j2_el_dev"].fn(inputs)["yy_hat"]
    pd.testing.assert_series_equal(shadow, ref, check_names=False)


@needs_data
def test_comb_equal_matches_j1(inputs):
    from kpif_nowcast.j1_hybrid import build_panel, j1_forecast
    from kpif_nowcast.observations import PATH, load

    if not (PROCESSED_DIR / "el_contracts.csv").exists() or not PATH.exists():
        pytest.skip("J1 inputs missing")
    from kpif_nowcast.data import load_el_contracts
    from kpif_nowcast.j2_el import zone_monthly_spot

    panel = build_panel(inputs.kpif, inputs.comps, inputs.feats, load_el_contracts(), zone_monthly_spot("SE3"),
                        inputs.rb_fc, load())
    ref = j1_forecast(panel, "j1_comb_equal")
    shadow = SHADOW_MODELS["j1_comb_equal"].fn(inputs)["yy_hat"].reindex(ref.index)
    assert np.allclose(shadow, ref, rtol=0, atol=1e-12)


def test_status_rule():
    t = pd.Period("2026-11", "M")
    assert status(t, 30, "2026-11-25", pd.Timestamp("2026-12-02"))[0] == "FINAL"
    assert status(t, 30, "2026-11-25", pd.Timestamp("2026-12-04"))[0] == "FINAL"
    assert status(t, 22, "2026-11-17", pd.Timestamp("2026-11-23"))[0] == "PRELIMINARY"
    assert status(t, 30, "2026-11-19", pd.Timestamp("2026-12-01"))[0] == "PRELIMINARY"  # fuel too short
    assert status(t, 30, "2026-11-25", pd.Timestamp("2026-12-05"))[0] == "LATE"


@pytest.mark.parametrize("old, new, force, expected", [
    (None, "PRELIMINARY", False, True),
    ("PRELIMINARY", "FINAL", False, True),
    ("PRELIMINARY", "PRELIMINARY", False, True),
    ("PRELIMINARY", "LATE", False, False),
    ("FINAL", "FINAL", False, False),
    ("FINAL", "PRELIMINARY", False, False),
    ("FINAL", "FINAL", True, True),
])
def test_write_rule(tmp_path, old, new, force, expected):
    path = tmp_path / "2026-11.json"
    if old:
        path.write_text(json.dumps({"status": old}), encoding="utf-8")
    assert should_write(path, new, force) is expected


def _workflows() -> list[Path]:
    return [p for d in WORKFLOW_DIRS if d.exists() for p in sorted(d.glob("*.yml"))]


def test_workflows_exist_and_only_run_on_schedule_or_by_hand():
    files = _workflows()
    assert {p.name for p in files} >= {"weekly-fetch.yml", "monthly-shadow.yml"}
    for p in files:
        text = p.read_text(encoding="utf-8")
        on_block = re.search(r"^on:\n((?:[ \t]+.*\n|\n)+)", text, re.M).group(1)
        triggers = set(re.findall(r"^  (\w+):", on_block, re.M))
        # workflow_run (K10 pages.yml) only follows this repo's own scheduled workflows: still no push/PR trigger
        assert triggers <= {"schedule", "workflow_dispatch", "workflow_run"}, f"{p.name}: triggers {triggers}"
        if "workflow_run" in triggers:
            names = set(re.findall(r'"([^"]+)"', re.search(r"workflows:\s*\[([^\]]*)\]", on_block).group(1)))
            assert names <= {"Weekly data fetch", "Monthly shadow forecasts"}, f"{p.name}: follows {names}"
        assert "secrets." not in text, f"{p.name} must not need secrets"


def test_workflows_run_the_pipeline_commands():
    """The local runner (scripts/run_workflow_locally.py) runs these same commands."""
    text = {p.name: p.read_text(encoding="utf-8") for p in _workflows()}
    assert "python -m kpif_nowcast.pipeline weekly" in text["weekly-fetch.yml"]
    assert "python -m kpif_nowcast.pipeline monthly" in text["monthly-shadow.yml"]


def test_raw_cache_latest_and_prune(tmp_path):
    from kpif_nowcast.sources import rawcache

    for d in ["20261101", "20261108", "20261115"]:
        (tmp_path / f"scb_TAB1_abc123_{d}.json").write_text("{}", encoding="utf-8")
        (tmp_path / f"fao_ffpi.csv_{d}").write_text("", encoding="utf-8")
    (tmp_path / "scb_TAB1_20261120.json").write_text("{}", encoding="utf-8")  # untagged: other name
    assert rawcache.latest(tmp_path, "scb_TAB1_abc123", ".json").name == "scb_TAB1_abc123_20261115.json"
    assert rawcache.latest(tmp_path, "scb_TAB1", ".json").name == "scb_TAB1_20261120.json"
    removed = rawcache.prune(tmp_path, keep=2)
    assert sorted(p.name for p in removed) == ["fao_ffpi.csv_20261101", "scb_TAB1_abc123_20261101.json"]


def test_offline_blocks_network():
    import requests

    from kpif_nowcast.sources import rawcache

    rawcache.block_network()
    try:
        with pytest.raises(rawcache.OfflineError):
            requests.get("https://example.invalid/")
    finally:
        rawcache.unblock_network()


def test_k2_shadows_wait_for_the_flash():
    """A K2 shadow is only FINAL before the deadline day once the target month's euro-area flash is in."""
    t = pd.Period("2026-11", "M")
    empty = pd.DataFrame(columns=["series", "period", "value", "known_from"])
    obs = pd.DataFrame({"series": ["ea_flash_total"], "period": ["2026-10"], "value": [2.0],
                        "known_from": [pd.Timestamp("2026-11-02")]})
    for name in ("k2_avg_ens_s", "k2_avg_ridge_l"):
        ready = SHADOW_MODELS[name].ready
        assert ready is not None
        assert not ready(Inputs(None, None, None, None, empty), t)
        assert not ready(Inputs(None, None, None, None, obs), t)
        obs_t = pd.concat([obs, obs.assign(period="2026-11")], ignore_index=True)
        assert ready(Inputs(None, None, None, None, obs_t), t)
