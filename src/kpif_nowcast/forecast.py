"""Live forecast of next month's KPIF, logged before SCB's flash estimate.

Run:  python -m kpif_nowcast.forecast [--adjust PP --note "why"]

- Refreshes all data, forecasts the month after the latest published KPIF.
- Main model: bottom-up component model with fuel + electricity (see docs/beslutslogg.md).
- --adjust: manual judgement in percentage points on the y/y forecast, for big decided
  one-off events (e.g. VAT changes) that the model can't see. Always give a --note.
- Writes forecasts/<month>.json. A forecast is FINAL only if made on day 1-4 of the
  following month with complete electricity and fuel data; earlier runs are PRELIMINARY.
- The file is committed to git before the flash estimate; the commit time is the proof.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd

from kpif_nowcast import data as data_mod
from kpif_nowcast.component_model import ENERGY, component_forecast
from kpif_nowcast.features import ZONE_WEIGHTS, build_features, electricity_monthly, fuel_proxy_daily
from kpif_nowcast.riksbank_benchmark import DEADLINE_DAY, riksbank_at_deadline

FORECAST_DIR = Path(__file__).resolve().parents[2] / "forecasts"
MODEL_NAME = "component_fuel_el_v1"
EVAL_START = "2024-01"


def error_bands(index: pd.Series, actual: pd.Series, comps: pd.DataFrame, feats: pd.DataFrame) -> dict:
    """Empirical absolute-error quantiles of the same model in the backtest (y/y, pp)."""
    hist = component_forecast(index, comps, feats, {"energy": ENERGY})["yy_hat"]
    err = (hist - actual).loc[pd.Period(EVAL_START, "M"):].dropna()
    return {
        "backtest_from": EVAL_START,
        "backtest_n": int(len(err)),
        "backtest_mae": round(float(err.abs().mean()), 3),
        "abs_err_p50": round(float(err.abs().quantile(0.5)), 2),
        "abs_err_p80": round(float(err.abs().quantile(0.8)), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adjust", type=float, default=0.0, help="manual adjustment of y/y, pp")
    parser.add_argument("--note", default="", help="reason for the adjustment")
    parser.add_argument("--no-refresh", action="store_true", help="use already downloaded data")
    args = parser.parse_args()
    if args.adjust and not args.note:
        parser.error("--adjust requires --note")

    if not args.no_refresh:
        data_mod.refresh()
    kpif, comps = data_mod.load_kpif(), data_mod.load_components()
    index, actual = kpif["index"], kpif["yy_official"]
    target = kpif.index.max() + 1

    el = electricity_monthly(min_days=1)  # allow a partial target month, flagged below
    fuel_daily = fuel_proxy_daily()
    feats = build_features(el, fuel_daily)

    # Data completeness for the target month
    month_days = target.days_in_month
    el_days = int(el["el_days"].get(target, 0))
    fuel_days = fuel_daily[fuel_daily.index.to_period("M") == target]
    fuel_last = fuel_days.index.max().date().isoformat() if len(fuel_days) else None

    today = pd.Timestamp.today().normalize()
    deadline = (target + 1).to_timestamp() + pd.Timedelta(days=DEADLINE_DAY - 1)
    complete = el_days >= month_days and fuel_last is not None and pd.Timestamp(fuel_last).day >= 20
    status = "FINAL" if complete and today <= deadline else ("LATE" if today > deadline else "PRELIMINARY")

    res = component_forecast(index, comps, feats, {"energy": ENERGY})
    if target not in res.index:
        raise SystemExit(f"No forecast for {target}: missing features (el_days={el_days}, fuel_last={fuel_last})")
    row = res.loc[target]
    model_yy = float(row["yy_hat"])
    final_yy = model_yy + args.adjust

    rb = riksbank_at_deadline(data_mod.load_riksbank_forecasts(), pd.PeriodIndex([target]))
    rb_value = float(rb["riksbank"].iloc[0]) if len(rb) else None
    rb_round = str(rb["rb_round"].iloc[0]) if len(rb) else None

    bands = error_bands(index, actual, comps, feats)
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = None

    out = {
        "target_month": str(target),
        "status": status,
        "made_at": datetime.now().isoformat(timespec="seconds"),
        "deadline": deadline.date().isoformat(),
        "model": MODEL_NAME,
        "code_commit": commit,
        "forecast_yy": round(final_yy, 2),
        "forecast_yy_rounded": round(final_yy, 1),
        "model_yy": round(model_yy, 2),
        "manual_adjustment_pp": args.adjust,
        "manual_note": args.note,
        "forecast_mm_pp": round(float(row["mm_hat_pp"]) + 0.0, 2),
        "components_pp": {c[3:]: round(float(v), 3) for c, v in row.items() if c.startswith("fc_")},
        "range_50": [round(final_yy - bands["abs_err_p50"], 1), round(final_yy + bands["abs_err_p50"], 1)],
        "range_80": [round(final_yy - bands["abs_err_p80"], 1), round(final_yy + bands["abs_err_p80"], 1)],
        "error_bands": bands,
        "riksbank": {"forecast_yy": rb_value, "policy_round": rb_round},
        "last_known": {"month": str(kpif.index.max()), "yy": float(actual.iloc[-1])},
        "inputs": {
            "el_spot_sek_kwh": round(float(feats.loc[target, "el_spot"]), 4),
            "el_chg": round(float(feats.loc[target, "el_chg"]), 4),
            "el_days": el_days,
            "el_zone_weights": ZONE_WEIGHTS,
            "brent_sek": round(float(feats.loc[target, "brent_sek"]), 1),
            "fuel_chg": round(float(feats.loc[target, "fuel_chg"]), 4),
            "fuel_last_day": fuel_last,
        },
    }
    FORECAST_DIR.mkdir(exist_ok=True)
    path = FORECAST_DIR / f"{target}.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nKPIF {target}: {final_yy:.2f} % y/y  (rounded {final_yy:.1f})  [{status}]")
    print(f"  50% range {out['range_50']}, 80% range {out['range_80']}")
    print(f"  Riksbank ({rb_round}): {rb_value}   last known {kpif.index.max()}: {actual.iloc[-1]}")
    print(f"  Data: electricity {el_days}/{month_days} days, fuel through {fuel_last}. Deadline {deadline.date()}")
    print(f"  Saved {path.relative_to(FORECAST_DIR.parent)}")


if __name__ == "__main__":
    main()
