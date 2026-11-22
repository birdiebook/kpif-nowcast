"""Export the datasets behind the Claude Data dashboard as JSON files.

Run: python -m kpif_nowcast.export_dashboard

Writes outputs/dashboard/<dataset>.json, each as {"rows": [...], "meta": [...]}.
`meta` carries this script's own source, so every number on the dashboard can be
traced to the code that produced it. The files are uploaded to the dashboard by hand
(or by the agent) after each monthly run; nothing here talks to the network.

Datasets:
- kpif:           official KPIF y/y and m/m (SCB, TAB6590)
- backtest:       one-month-ahead forecasts per month, as they would have been made at the
                  deadline (expanding window), for the main model, naive baselines and the Riksbank
- contributions:  each component's contribution to KPIF m/m (SCB, TAB6628), plus the live forecast's
- drivers:        electricity spot and fuel proxy vs the energy contribution
- live_forecasts: every logged live forecast (forecasts/*.json) with its outcome once published
- riksbank_path:  the latest Riksbank KPIF forecast path beyond its cutoff
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import pandas as pd

from kpif_nowcast.baselines import all_baselines
from kpif_nowcast.component_model import ENERGY, component_forecast
from kpif_nowcast.data import load_components, load_kpif, load_riksbank_forecasts
from kpif_nowcast.features import load_features
from kpif_nowcast.forecast import EVAL_START, FORECAST_DIR, MODEL_NAME
from kpif_nowcast.riksbank_benchmark import riksbank_at_deadline

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "dashboard"
HISTORY_START = "2000-01"
BACKTEST_START = "2015-01"
CONTRIB_START = "2019-01"


def _clean(v):
    """JSON-safe scalar: NaN/inf -> None, numpy -> python, periods -> 'YYYY-MM'."""
    if v is None:
        return None
    if isinstance(v, pd.Period):
        return str(v)
    if isinstance(v, pd.Timestamp):
        return v.date().isoformat()
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float):
        return None if not math.isfinite(v) else round(v, 4)
    return v


def _rows(df: pd.DataFrame) -> list[dict]:
    return [{k: _clean(v) for k, v in rec.items()} for rec in df.to_dict(orient="records")]


def _write(name: str, df: pd.DataFrame, inputs: str) -> None:
    code = Path(__file__).read_text(encoding="utf-8")
    payload = {
        "rows": _rows(df),
        "meta": [
            {"label": "export_dashboard.py", "value": code, "type": "code", "lang": "python"},
            {"label": "Input", "value": inputs},
            {"label": "Exported", "value": datetime.now().isoformat(timespec="seconds")},
            {"label": "Repository", "value": "https://github.com/birdiebook/kpif-nowcast"},
        ],
    }
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"  {path.relative_to(ROOT)}: {len(df)} rows")


def live_forecasts(kpif: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for path in sorted(FORECAST_DIR.glob("*.json")):
        f = json.loads(path.read_text(encoding="utf-8"))
        month = pd.Period(f["target_month"], "M")
        outcome = kpif["yy_official"].get(month)
        rb = f["riksbank"]["forecast_yy"]
        rows.append(
            {
                "month": f["target_month"],
                "status": f["status"],
                "made_at": f["made_at"],
                "model": f["model"],
                "forecast_yy": f["forecast_yy"],
                "forecast_yy_rounded": f["forecast_yy_rounded"],
                "forecast_mm_pp": f["forecast_mm_pp"],
                "lo50": f["range_50"][0],
                "hi50": f["range_50"][1],
                "lo80": f["range_80"][0],
                "hi80": f["range_80"][1],
                "backtest_n": f["error_bands"]["backtest_n"],
                "riksbank_yy": rb,
                "rb_round": f["riksbank"]["policy_round"],
                "last_month": f["last_known"]["month"],
                "last_yy": f["last_known"]["yy"],
                "change_vs_last": round(f["forecast_yy"] - f["last_known"]["yy"], 2),
                "outcome_yy": outcome,
                "error": None if outcome is None or pd.isna(outcome) else round(f["forecast_yy"] - outcome, 2),
                "error_rb": None if outcome is None or pd.isna(outcome) or rb is None else round(rb - outcome, 2),
                "manual_adjustment_pp": f["manual_adjustment_pp"],
                "manual_note": f["manual_note"],
                "el_spot": f["inputs"]["el_spot_sek_kwh"],
                "el_chg": f["inputs"]["el_chg"],
                "el_days": f["inputs"]["el_days"],
                "brent_sek": f["inputs"]["brent_sek"],
                "fuel_chg": f["inputs"]["fuel_chg"],
                "fuel_last_day": f["inputs"]["fuel_last_day"],
                "deadline": f["deadline"],
                "components": f["components_pp"],
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    kpif, comps, feats = load_kpif(), load_components(), load_features()
    rb_all = load_riksbank_forecasts()
    index, actual = kpif["index"], kpif["yy_official"]

    # kpif
    k = kpif.loc[pd.Period(HISTORY_START, "M"):].reset_index()
    k = k.rename(columns={"yy_official": "yy", "mm_official": "mm"})[["month", "yy", "mm", "index"]]
    _write("kpif", k, "SCB TAB6590 (KPIF, 2020=100)")

    # backtest: same functions as forecast.py / the phase 2 and 4 backtests
    preds = all_baselines(index)[["naive_yy", "seasonal_trend_5y"]]
    rb = riksbank_at_deadline(rb_all, kpif.index)
    preds = preds.join(rb[["riksbank", "rb_round"]])
    model = component_forecast(index, comps, feats, {"energy": ENERGY})["yy_hat"]
    preds["model"] = model.loc[pd.Period(EVAL_START, "M"):]  # the model's own evaluation window
    bt = preds.join(actual.rename("actual"), how="inner").loc[pd.Period(BACKTEST_START, "M"):]
    bt = bt.dropna(subset=["actual"]).reset_index()
    bt = bt[["month", "actual", "model", "naive_yy", "seasonal_trend_5y", "riksbank", "rb_round"]]
    _write(
        "backtest",
        bt,
        f"Expanding-window forecasts, model {MODEL_NAME} from {EVAL_START}; "
        "Riksbank = latest vintage published before day 4 of the following month",
    )

    # contributions: outcomes + the latest live forecast
    eff = comps.loc[comps["month"] >= pd.Period(CONTRIB_START, "M"), ["month", "component", "effect_month"]]
    eff = eff.rename(columns={"effect_month": "pp"}).assign(kind="utfall")
    live = live_forecasts(kpif)
    fc_rows = []
    for _, r in live.iterrows():
        if r["outcome_yy"] is not None and not pd.isna(r["outcome_yy"]):
            continue  # published: the outcome rows already cover it
        for comp, pp in r["components"].items():
            fc_rows.append({"month": r["month"], "component": comp, "pp": pp, "kind": "prognos"})
    contrib = pd.concat([eff, pd.DataFrame(fc_rows)], ignore_index=True)
    contrib["month"] = contrib["month"].astype(str)
    contrib = contrib.sort_values(["month", "component"]).dropna(subset=["pp"])
    _write("contributions", contrib, "SCB TAB6628 (effect on KPIF m/m, pp) + forecasts/*.json")

    # drivers: monthly electricity and fuel inputs vs energy's contribution
    energy = comps[comps["component"] == "energy"].set_index("month")["effect_month"].rename("energy_pp")
    drv = feats[["el_spot", "el_chg", "brent_sek", "fuel_chg"]].join(energy, how="outer")
    drv = drv.loc[pd.Period(CONTRIB_START, "M"):].reset_index().rename(columns={"index": "month"})
    drv["month"] = drv["month"].astype(str)
    drv["partial"] = False
    for _, r in live.iterrows():  # the forecast month's inputs, possibly from a partial month
        if r["month"] in set(drv["month"]) and not pd.isna(drv.loc[drv["month"] == r["month"], "el_spot"]).all():
            continue
        drv = drv[drv["month"] != r["month"]]
        extra = {
            "month": r["month"], "el_spot": r["el_spot"], "el_chg": r["el_chg"], "brent_sek": r["brent_sek"],
            "fuel_chg": r["fuel_chg"], "energy_pp": None, "partial": r["status"] != "FINAL",
        }
        drv = pd.concat([drv, pd.DataFrame([extra])], ignore_index=True)
    drv = drv.sort_values("month")
    _write(
        "drivers",
        drv[["month", "el_spot", "el_chg", "brent_sek", "fuel_chg", "energy_pp", "partial"]],
        "elprisetjustnu.se (ENTSO-E) SE3/SE4 70/30, FRED DCOILBRENTEU x Riksbank SEK/USD, SCB TAB6628",
    )

    _write("live_forecasts", live.drop(columns="components"), "forecasts/*.json + SCB TAB6590 outcomes")

    # riksbank_path: latest round, forecast months only
    latest = rb_all.sort_values("published")["policy_round"].iloc[-1]
    path = rb_all[rb_all["policy_round"] == latest].copy()
    cutoff = pd.Period(path["cutoff"].iloc[0], "M")
    path["month"] = path["month"].apply(lambda m: pd.Period(m, "M"))
    path = path[(path["month"] > cutoff) & (path["month"] <= cutoff + 24)]
    path = path.assign(month=path["month"].astype(str))[["month", "value", "policy_round", "cutoff", "published"]]
    _write("riksbank_path", path.rename(columns={"value": "yy"}), "Riksbank SEMCPIFNAYNA forecast vintages")


if __name__ == "__main__":
    main()
