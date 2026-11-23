"""Shadow forecasts: every candidate model forecasts the same month as the live model, logged to git.

Backtest results are selection evidence (the models were chosen on 2015-2026). Real evidence only
comes from months the models have never seen. Each shadow model writes
forecasts/shadow/<model>/<month>.json at the same time as the live forecast; the live
forecasts/<month>.json and forecast.py are not touched.

Models are registered in SHADOW_MODELS (adding a model = one line). Each model is a function of
the same inputs and returns its whole forecast series (history + target month), so the same
function also gives the backtest for the champion/challenger table.

Write rule: a FINAL file is never overwritten (the commit time is the proof); a PRELIMINARY one is
replaced by a newer run; a LATE run never replaces an existing file. --force overrides.

Run: python -m kpif_nowcast.shadow [--offline] [--as-of YYYY-MM-DD] [--force]
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import pandas as pd

from kpif_nowcast.component_model import ENERGY, component_forecast
from kpif_nowcast.forecast import FORECAST_DIR, MODEL_NAME
from kpif_nowcast.j2_el import build_j2_features, j2_forecast
from kpif_nowcast.riksbank_benchmark import DEADLINE_DAY, riksbank_at_deadline

SHADOW_DIR = FORECAST_DIR / "shadow"


@dataclass
class Inputs:
    """Everything the models may use. kpif/comps up to t-1, feats including target month t."""

    kpif: pd.DataFrame
    comps: pd.DataFrame
    feats: pd.DataFrame
    rb_fc: pd.DataFrame
    obs: pd.DataFrame | None = None  # versioned observation table (K2: euro-area flash, catalog series)
    # Expensive models (K2: nested CV per month) forecast only months >= rows_from (earlier rows left out).
    # The live run sets it to the target month; cheap models ignore it.
    rows_from: pd.Period | None = None


# ------------------------------------------------------------------ models


def comp_fuel_el(inp: Inputs) -> pd.DataFrame:
    """The live model (component_fuel_el_v1) re-run as a shadow: same code, same inputs."""
    res = component_forecast(inp.kpif["index"], inp.comps, inp.feats, {"energy": ENERGY})
    return res[["yy_hat", "mm_hat_pp"]]


_NO_CONTRACTS = pd.DataFrame({"month": pd.PeriodIndex([], freq="M"), "zone": [], "contract": [], "share": []})


def j2_el_dev(inp: Inputs) -> pd.DataFrame:
    """J2 V2: electricity as deviation from the same month's change in earlier years, trained from 2012.

    Uses only fuel_chg and el_dev; the contract-share and SE3 inputs of build_j2_features feed other
    J2 variants, so empty frames are passed (tested to give identical forecasts).
    """
    j2f = build_j2_features(inp.feats, _NO_CONTRACTS, pd.Series(dtype=float, index=pd.PeriodIndex([], freq="M")))
    return j2_forecast(inp.kpif["index"], inp.comps, j2f, "j2_el_dev")[["yy_hat", "mm_hat_pp"]]


def rb_updated(inp: Inputs, months: pd.PeriodIndex) -> pd.Series:
    rb = riksbank_at_deadline(inp.rb_fc, months, inp.kpif["yy_official"])
    return rb["rb_updated"]


def j1_comb_equal(inp: Inputs) -> pd.DataFrame:
    """J1 C1: 0.5 * rb_updated + 0.5 * J2 V2. No estimated parameters."""
    j2 = j2_el_dev(inp)["yy_hat"]
    rbu = rb_updated(inp, j2.index)
    return pd.DataFrame({"yy_hat": (0.5 * rbu + 0.5 * j2.reindex(rbu.index)).dropna()})


def _k2(name: str) -> Callable[[Inputs], pd.DataFrame]:
    """K2 frozen variant (k2_ml.VARIANTS) with the K2b information-set correction of the euro-area flash.

    Each row t of the design uses data known at deadline(t); the observation table gets the real release
    date for flash periods published after day 4 of the next month (k2b_review.realistic_flash), which the
    backfill dates two days after the period end. Contract and SE3 inputs are not used by K2 (only J2 V2).
    """

    def fn(inp: Inputs) -> pd.DataFrame:
        from kpif_nowcast.k2_ml import K2Runner, build_design
        from kpif_nowcast.k2b_review import realistic_flash
        from kpif_nowcast.observations import load as load_obs

        obs = realistic_flash(load_obs() if inp.obs is None else inp.obs)
        empty_se3 = pd.Series(dtype=float, index=pd.PeriodIndex([], freq="M"))
        d = build_design(inp.kpif, inp.comps, inp.feats, _NO_CONTRACTS, empty_se3, inp.rb_fc, obs,
                         with_catalog=name.endswith("_l"))
        run = K2Runner(d)
        rows = [i for i, t in enumerate(d.index) if inp.rows_from is None or t >= inp.rows_from]
        return pd.DataFrame({"yy_hat": [run.forecast(name, i) for i in rows]}, index=d.index[rows])

    return fn


def _flash_published(inp: Inputs, target: pd.Period) -> bool:
    """K2 readiness: the euro-area flash for the target month is in the observation table."""
    obs = inp.obs
    if obs is None or obs.empty:
        return False
    return bool(((obs["series"] == "ea_flash_total") & (obs["period"].astype(str) == str(target))).any())


@dataclass
class ShadowModel:
    fn: Callable[[Inputs], pd.DataFrame]
    description: str
    # Extra inputs a model's backtest assumes are known at the deadline. If not yet in the data, a FINAL run
    # before the deadline day is downgraded to PRELIMINARY, so a later run (days 2-4) replaces it.
    ready: Callable[[Inputs, pd.Period], bool] | None = None


SHADOW_MODELS: dict[str, ShadowModel] = {
    "comp_fuel_el": ShadowModel(comp_fuel_el, f"Live model {MODEL_NAME} as a shadow (champion)"),
    "j2_el_dev": ShadowModel(j2_el_dev, "J2 V2: el deviation from same month earlier years, 2012-"),
    "j1_comb_equal": ShadowModel(j1_comb_equal, "J1 C1: 50/50 of rb_updated and J2 V2"),
    # K2 candidates, registered by K2b after the review (docs/auto2/k2b/granskning.md)
    "k2_avg_ens_s": ShadowModel(_k2("k2_avg_ens_s"), "K2: 50/50 + mean of ridge and boosting residual (14 features)",
                                _flash_published),
    "k2_avg_ridge_l": ShadowModel(_k2("k2_avg_ridge_l"), "K2: 50/50 + ridge residual (14 + 43 catalog features)",
                                  _flash_published),
}
CHAMPION = "comp_fuel_el"


# ------------------------------------------------------------------ inputs and status


def load_inputs() -> tuple[Inputs, dict]:
    """Same data path as forecast.py: processed KPIF/components/Riksbank, features with a partial target month."""
    from kpif_nowcast import data as data_mod
    from kpif_nowcast.features import build_features, electricity_monthly, fuel_proxy_daily

    kpif, comps = data_mod.load_kpif(), data_mod.load_components()
    el = electricity_monthly(min_days=1)
    fuel_daily = fuel_proxy_daily()
    feats = build_features(el, fuel_daily)
    target = kpif.index.max() + 1
    fuel_days = fuel_daily[fuel_daily.index.to_period("M") == target]
    info = {
        "target": target,
        "el_days": int(el["el_days"].get(target, 0)),
        "fuel_last_day": fuel_days.index.max().date().isoformat() if len(fuel_days) else None,
    }
    from kpif_nowcast.observations import load as load_obs

    return Inputs(kpif, comps, feats, data_mod.load_riksbank_forecasts(), load_obs()), info


def status(target: pd.Period, el_days: int, fuel_last: str | None, today: pd.Timestamp) -> tuple[str, str]:
    """Same rule as forecast.py: FINAL = complete electricity, fuel to >= the 20th, before the deadline."""
    deadline = (target + 1).to_timestamp() + pd.Timedelta(days=DEADLINE_DAY - 1)
    complete = el_days >= target.days_in_month and fuel_last is not None and pd.Timestamp(fuel_last).day >= 20
    st = "FINAL" if complete and today <= deadline else ("LATE" if today > deadline else "PRELIMINARY")
    return st, deadline.date().isoformat()


def should_write(path: Path, new_status: str, force: bool) -> bool:
    if force or not path.exists():
        return True
    old = json.loads(path.read_text(encoding="utf-8")).get("status")
    return old == "PRELIMINARY" and new_status in ("PRELIMINARY", "FINAL")


def _commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                             cwd=FORECAST_DIR.parent)
        return out.stdout.strip() or None
    except OSError:
        return None


def make_record(name: str, res: pd.DataFrame, inp: Inputs, info: dict, today: pd.Timestamp) -> dict:
    target = info["target"]
    st, dl = status(target, info["el_days"], info["fuel_last_day"], today)
    yy = float(res.loc[target, "yy_hat"])
    rec = {
        "target_month": str(target),
        "model": name,
        "description": SHADOW_MODELS[name].description,
        "status": st,
        "deadline": dl,
        "forecast_yy": round(yy, 2),
        "forecast_yy_rounded": round(yy, 1),
        "forecast_mm_pp": round(float(res.loc[target, "mm_hat_pp"]), 2) if "mm_hat_pp" in res else None,
        "last_known": {"month": str(inp.kpif.index.max()), "yy": float(inp.kpif["yy_official"].iloc[-1])},
        "inputs": {
            "el_days": info["el_days"],
            "fuel_last_day": info["fuel_last_day"],
            "el_chg": round(float(inp.feats.loc[target, "el_chg"]), 4),
            "fuel_chg": round(float(inp.feats.loc[target, "fuel_chg"]), 4),
        },
        # run metadata: excluded when comparing two runs for reproducibility
        "run": {"made_at": datetime.now().isoformat(timespec="seconds"), "code_commit": _commit(),
                "as_of": today.date().isoformat()},
    }
    return rec


def run(as_of: str | None = None, force: bool = False, models: list[str] | None = None) -> dict[str, str]:
    """Compute and write all shadow forecasts for the next unpublished month. Returns model -> action."""
    today = pd.Timestamp(as_of) if as_of else pd.Timestamp.today().normalize()
    inp, info = load_inputs()
    target = info["target"]
    inp.rows_from = target  # the live run needs the target month only
    actions = {}
    for name in models or list(SHADOW_MODELS):
        res = SHADOW_MODELS[name].fn(inp)
        if target not in res.index or pd.isna(res.loc[target, "yy_hat"]):
            raise SystemExit(f"{name}: no forecast for {target} (el_days={info['el_days']}, fuel={info['fuel_last_day']})")
        rec = make_record(name, res, inp, info, today)
        model = SHADOW_MODELS[name]
        if (rec["status"] == "FINAL" and model.ready is not None and not model.ready(inp, target)
                and today.date().isoformat() < rec["deadline"]):
            rec["status"] = "PRELIMINARY"
            rec["waiting_for"] = "euro-area flash for the target month (expected by day 3)"
        path = SHADOW_DIR / name / f"{target}.json"
        if should_write(path, rec["status"], force):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            actions[name] = f"wrote {rec['status']} {rec['forecast_yy']:.2f}"
        else:
            actions[name] = "kept existing (FINAL, or this run is LATE)"
        print(f"{name:16s} {target}: {rec['forecast_yy']:.2f} % y/y [{rec['status']}] -> {actions[name]}")
    print(f"Data: electricity {info['el_days']}/{target.days_in_month} days, fuel through {info['fuel_last_day']}")
    return actions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="read data/raw only, no network")
    parser.add_argument("--as-of", help="date used for FINAL/PRELIMINARY/LATE (default today)")
    parser.add_argument("--force", action="store_true", help="overwrite even FINAL files")
    parser.add_argument("models", nargs="*")
    args = parser.parse_args()
    if args.offline:
        from kpif_nowcast.pipeline import go_offline

        go_offline()
    run(args.as_of, args.force, args.models or None)


if __name__ == "__main__":
    main()
