"""K9: longer horizons (3, 6, 12 months) - correct or shrink the Riksbank's forecast.

Preregistered in docs/auto2/k9/hypotes.md (exactly 4 variants). Origin o = last published KPIF month,
forecast date = day 4 of o+2 (horizon.origin_date), target = KPIF y/y in o+h.

Base RB = the latest Riksbank round published before the forecast date with cutoff c < o+h.
Features describe what happened between c and the forecast date (all via observations.as_of):
the Riksbank's own miss on month o, energy, krona, rates, NIER price plans, PPI, euro area HICP.

Variants
- k9_ridge_h3 / k9_ridge_h12: ridge on residual (actual - RB), alpha by nested TimeSeriesSplit(gap=h)
- k9_shrink_h12: 2 + w (RB - 2), w by no-intercept OLS, clipped to [0, 1]
- k9_miss_h6:   RB + phi * rb_miss, phi by no-intercept OLS

DM test: absolute-error loss, Newey-West (Bartlett) with lag h-1, HLN correction, t(n-1).

Run: python -m kpif_nowcast.k9_horizon
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from kpif_nowcast import observations as obs
from kpif_nowcast.evaluation import long_run_variance, t_two_sided_p
from kpif_nowcast.horizon import origin_date
from kpif_nowcast.k2_ml import RIDGE_GRID, _make

TARGET = 2.0
FIRST_ORIGIN = "2014-12"
EVAL = ("2015-01", "2026-10")
USED = ("2024-01", "2026-10")
N_SPLITS = 4
MIN_TRAIN = {"ridge": 36, "shrink": 24, "miss": 24}
SERIES = ["kpif_yy", "brent_sek", "kix", "policy_rate", "gvb_2y", "ki_prices_retail", "ki_services",
          "ppi_hmpi_consumer", "ea_hicp_total"]
FEATURES = ["rb_miss", "age", "rb_gap", "gap0", "brent_since", "kix_since", "rate_since", "gvb2_since",
            "ki_retail_since", "ki_services_since", "ppi_since", "ea_since"]
REVISED_FEATURES = {"ppi_since", "ea_since"}
OUT = Path(__file__).resolve().parents[2] / "docs" / "auto2" / "k9"
PRED_DIR = Path(__file__).resolve().parents[2] / "outputs"  # gitignored


@dataclass(frozen=True)
class Variant:
    h: int
    kind: str  # ridge | shrink | miss


VARIANTS = {
    "k9_ridge_h3": Variant(3, "ridge"),
    "k9_ridge_h12": Variant(12, "ridge"),
    "k9_shrink_h12": Variant(12, "shrink"),
    "k9_miss_h6": Variant(6, "miss"),
}
HORIZONS = [3, 6, 12]


# ------------------------------------------------------------------ design


def _value_at(s: pd.Series, p: pd.Period) -> float:
    s = s.loc[:p]
    return float(s.iloc[-1]) if len(s) else np.nan


def _last(s: pd.Series) -> float:
    return float(s.iloc[-1]) if len(s) else np.nan


def rb_info(rb: pd.DataFrame, when: pd.Timestamp, target: pd.Period, o: pd.Period):
    """(RB forecast for target, RB value for o in the same round, cutoff) - same choice as horizon.riksbank_for."""
    v = rb[["policy_round", "cutoff", "published"]].drop_duplicates()
    v = v[(v["published"] < when) & (v["cutoff"] < target)].sort_values("published")
    if v.empty:
        return None
    r = v.iloc[-1]
    path = rb[rb["policy_round"] == r["policy_round"]].set_index("month")["value"]
    if target not in path.index:
        return None
    return float(path[target]), float(path.get(o, np.nan)), r["cutoff"]


def feature_row(o: pd.Period, h: int, table: pd.DataFrame, rb: pd.DataFrame) -> dict | None:
    d = origin_date(o)
    info = rb_info(rb, d, o + h, o)
    if info is None:
        return None
    rb_t, rb_o, c = info
    s = {k: obs.as_of(k, d, table) for k in SERIES}
    yy = s["kpif_yy"].loc[:o]
    yy0 = _last(yy)
    since = lambda k: _last(s[k]) - _value_at(s[k], c)  # noqa: E731
    logsince = lambda k: 100 * np.log(_last(s[k]) / _value_at(s[k], c))  # noqa: E731
    ppi = s["ppi_hmpi_consumer"]
    ppi_yy = 100 * (ppi / ppi.shift(12) - 1) if len(ppi) else ppi
    ki3 = lambda k: s[k].iloc[-3:].mean() - _value_at(s[k], c) if len(s[k]) else np.nan  # noqa: E731
    return {
        "origin": o, "target": o + h, "cutoff": c, "rb": rb_t, "yy0": yy0,
        "rb_miss": (yy0 - rb_o) if o > c else 0.0,
        "age": (o - c).n,
        "rb_gap": rb_t - TARGET,
        "gap0": yy0 - TARGET,
        "brent_since": logsince("brent_sek"),
        "kix_since": logsince("kix"),
        "rate_since": since("policy_rate"),
        "gvb2_since": since("gvb_2y"),
        "ki_retail_since": ki3("ki_prices_retail"),
        "ki_services_since": ki3("ki_services"),
        "ppi_since": _last(ppi_yy.dropna()) - _value_at(ppi_yy.dropna(), c) if len(ppi) else np.nan,
        "ea_since": since("ea_hicp_total"),
    }


def build_design(h: int, table: pd.DataFrame, rb: pd.DataFrame, last: pd.Period | None = None) -> pd.DataFrame:
    """One row per origin. `actual` is KPIF y/y for o+h from the given table's latest vintage (NaN if unknown)."""
    table = table[table["series"].isin(SERIES)]
    final = obs.as_of("kpif_yy", "2100-01-01", table)
    last = last or final.index.max()
    rows = [r for o in pd.period_range(FIRST_ORIGIN, last, freq="M") if (r := feature_row(o, h, table, rb))]
    d = pd.DataFrame(rows).set_index("origin")
    d["actual"] = final.reindex(d["target"]).to_numpy()
    return d


# ------------------------------------------------------------------ models


def fit_ridge(X: np.ndarray, y: np.ndarray, h: int):
    """Alpha by inner TimeSeriesSplit with gap=h (no overlap between inner train and validation targets)."""
    from sklearn.model_selection import TimeSeriesSplit

    n = len(y)
    splits = list(TimeSeriesSplit(n_splits=N_SPLITS, gap=h, test_size=(n - h) // (N_SPLITS + 1)).split(X))
    best, best_mae = None, np.inf
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for params in RIDGE_GRID:
            errs = [np.abs(_make("ridge", params).fit(X[tr], y[tr]).predict(X[va]) - y[va]) for tr, va in splits]
            mae = float(np.mean(np.concatenate(errs)))
            if mae < best_mae:
                best, best_mae = params, mae
        return _make("ridge", best).fit(X, y), best


def train_rows(d: pd.DataFrame, o: pd.Period) -> pd.DataFrame:
    """Rows whose target was published before the forecast date for origin o (target <= o)."""
    return d[(d["target"] <= o) & d["actual"].notna()]


def forecast(d: pd.DataFrame, o: pd.Period, kind: str, h: int) -> tuple[float, dict]:
    """Forecast for origin o and fitted parameters. Falls back to RB when there are too few training rows."""
    row = d.loc[o]
    tr = train_rows(d, o)
    if len(tr) < MIN_TRAIN[kind]:
        return float(row["rb"]), {"active": False}
    resid = (tr["actual"] - tr["rb"]).to_numpy()
    if kind == "ridge":
        model, params = fit_ridge(tr[FEATURES].to_numpy(dtype=float), resid, h)
        x = d.loc[[o], FEATURES].to_numpy(dtype=float)
        return float(row["rb"] + model.predict(x)[0]), {"active": True, "alpha": params["alpha"], "model": model}
    if kind == "shrink":
        g = (tr["rb"] - TARGET).to_numpy()
        w = float(np.clip(((tr["actual"] - TARGET).to_numpy() * g).sum() / (g**2).sum(), 0, 1))
        return float(TARGET + w * (row["rb"] - TARGET)), {"active": True, "w": w}
    m = tr["rb_miss"].to_numpy()
    phi = float((resid * m).sum() / (m**2).sum()) if (m**2).sum() > 0 else 0.0
    return float(row["rb"] + phi * row["rb_miss"]), {"active": True, "phi": phi}


def run_variant(d: pd.DataFrame, name: str) -> pd.DataFrame:
    v = VARIANTS[name]
    out = []
    for o in d.index:
        f, p = forecast(d, o, v.kind, v.h)
        out.append({"origin": o, "pred": f, **{k: val for k, val in p.items() if k != "model"}})
    return pd.DataFrame(out).set_index("origin")


def forecast_at(name: str, o: pd.Period, table: pd.DataFrame, rb: pd.DataFrame) -> float:
    """Forecast for origin o using only data known on the forecast date (for the information-set test)."""
    v = VARIANTS[name]
    d = build_design(v.h, table, rb, last=o)
    return forecast(d, o, v.kind, v.h)[0]


# ------------------------------------------------------------------ evaluation


def dm_hac(e_a, e_b, h: int) -> dict:
    """DM on |e|: Newey-West (Bartlett) lag h-1, HLN correction, t(n-1). p1 = one-sided H1 'a better'."""
    ea, eb = np.asarray(e_a, float), np.asarray(e_b, float)
    ok = ~(np.isnan(ea) | np.isnan(eb))
    dd = np.abs(ea[ok]) - np.abs(eb[ok])
    n = len(dd)
    hln = math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    se = math.sqrt(max(long_run_variance(dd, h - 1), 0.0) / n) / hln
    mean = float(dd.mean())
    if se == 0:
        return {"n": n, "diff": mean, "p2": np.nan, "p1": np.nan}
    stat = mean / se
    p2 = t_two_sided_p(stat, n - 1)
    return {"n": n, "diff": mean, "stat": stat, "p2": p2, "p1": p2 / 2 if stat < 0 else 1 - p2 / 2}


def holm(p: pd.Series) -> pd.Series:
    order = p.sort_values().index
    m, run, out = len(p), 0.0, {}
    for i, k in enumerate(order):
        run = max(run, min(1.0, (m - i) * p[k]))
        out[k] = run
    return pd.Series(out)[p.index]


def window(f: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    sel = (f["target"] >= pd.Period(start, "M")) & (f["target"] <= pd.Period(end, "M"))
    return f[sel & f["actual"].notna()]


def main() -> None:
    from kpif_nowcast.data import load_riksbank_forecasts
    from kpif_nowcast.evaluation import log_run

    warnings.filterwarnings("ignore")
    table, rb = obs.load(), load_riksbank_forecasts()
    designs = {h: build_design(h, table, rb) for h in HORIZONS}
    frames = {}
    for h, d in designs.items():
        f = d[["target", "actual", "rb", "yy0"]].copy()
        f["two"] = TARGET
        for name, v in VARIANTS.items():
            if v.h == h:
                r = run_variant(d, name)
                f[name] = r["pred"]
                f[f"{name}__active"] = r["active"]
                for c in r.columns.difference(["pred", "active"]):
                    f[f"{name}__{c}"] = r[c]
        frames[h] = f
        PRED_DIR.mkdir(parents=True, exist_ok=True)
        f.assign(origin=f.index.astype(str), target=f["target"].astype(str)).to_csv(
            PRED_DIR / f"k9_predictions_h{h}.csv", index=False)

    lines, log_rows = [], []
    # references per horizon
    lines.append("## Referenser per horisont, mål 2015-01..2026-10\n")
    lines.append("| h | n | eff. n (n/h) | Riksbanken | 2 % | naiv | RB vs 2 %: diff, p tvåsidig | "
                 "2024–26: n, RB / 2 % / naiv |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for h, f in frames.items():
        w = window(f, *EVAL)
        e_rb, e_2, e_nv = w["rb"] - w["actual"], w["two"] - w["actual"], w["yy0"] - w["actual"]
        r = dm_hac(e_rb, e_2, h)
        u = window(f, *USED)
        mae = lambda c: (u[c] - u["actual"]).abs().mean()  # noqa: E731
        lines.append(f"| {h} | {len(w)} | {len(w)/h:.1f} | {e_rb.abs().mean():.3f} | {e_2.abs().mean():.3f} | "
                     f"{e_nv.abs().mean():.3f} | {r['diff']:+.3f}, {r['p2']:.2f} | "
                     f"{len(u)}, {mae('rb'):.3f} / {mae('two'):.3f} / {mae('yy0'):.3f} |")
    # variants
    res = {}
    for name, v in VARIANTS.items():
        f = frames[v.h]
        for label, (s, e) in {"eval": EVAL, "used": USED}.items():
            w = window(f, s, e)
            e_v = w[name] - w["actual"]
            act = w[f"{name}__active"].astype(bool)
            rec = {"MAE": e_v.abs().mean(), "MAE_rb": (w["rb"] - w["actual"]).abs().mean(), "n": len(w),
                   "n_eff": len(w) / v.h, "n_active": int(act.sum())}
            rec["rb"] = dm_hac(e_v, w["rb"] - w["actual"], v.h)
            rec["two"] = dm_hac(e_v, w["two"] - w["actual"], v.h)
            rec["naive"] = dm_hac(e_v, w["yy0"] - w["actual"], v.h)
            wa = w[act]
            rec["active"] = dm_hac(wa[name] - wa["actual"], wa["rb"] - wa["actual"], v.h) if len(wa) > v.h + 2 else None
            rec["MAE_act"] = (wa[name] - wa["actual"]).abs().mean() if len(wa) else np.nan
            rec["MAE_rb_act"] = (wa["rb"] - wa["actual"]).abs().mean() if len(wa) else np.nan
            res[(name, label)] = rec
    p1 = pd.Series({n: res[(n, "eval")]["rb"]["p1"] for n in VARIANTS})
    ph = holm(p1)
    lines.append("\n## Varianter, mål 2015-01..2026-10 (förregistrerat)\n")
    lines.append("| Variant | h | n | eff. n | aktiva | MAE | RB | diff | p ensidig rå | Holm p | 2 %: diff, p | "
                 "naiv: diff, p | 2024–26 MAE / RB |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name, v in VARIANTS.items():
        r, u = res[(name, "eval")], res[(name, "used")]
        lines.append(
            f"| `{name}` | {v.h} | {r['n']} | {r['n_eff']:.1f} | {r['n_active']} | {r['MAE']:.3f} | {r['MAE_rb']:.3f} | "
            f"{r['rb']['diff']:+.3f} | {r['rb']['p1']:.3f} | {ph[name]:.3f} | {r['two']['diff']:+.3f}, {r['two']['p2']:.2f} | "
            f"{r['naive']['diff']:+.3f}, {r['naive']['p2']:.2f} | {u['MAE']:.3f} / {u['MAE_rb']:.3f} |")
        log_rows.append({"variant": name, "period": f"{EVAL[0]}..{EVAL[1]}", "n": r["n"], "MAE": round(r["MAE"], 4),
                         "dm_p_vs_rb_updated": ""})
        log_rows.append({"variant": name, "period": f"{USED[0]}..{USED[1]}", "n": u["n"], "MAE": round(u["MAE"], 4),
                         "dm_p_vs_rb_updated": ""})
    lines.append("\n## Bara aktiva månader (varianten skild från RB), mål 2015-01..2026-10\n")
    lines.append("| Variant | n aktiva | eff. n | MAE | RB | diff | p ensidig |")
    lines.append("|---|---|---|---|---|---|---|")
    for name, v in VARIANTS.items():
        r = res[(name, "eval")]
        a = r["active"]
        if a:
            lines.append(f"| `{name}` | {a['n']} | {a['n']/v.h:.1f} | {r['MAE_act']:.3f} | {r['MAE_rb_act']:.3f} | "
                         f"{a['diff']:+.3f} | {a['p1']:.3f} |")
    # parameters
    lines.append("\n## Skattade parametrar (över ursprung där varianten är aktiv)\n")
    for name, v in VARIANTS.items():
        f = frames[v.h]
        col = {"ridge": "alpha", "shrink": "w", "miss": "phi"}[v.kind]
        s = f[f"{name}__{col}"].dropna()
        lines.append(f"- `{name}`: {col} median {s.median():.3g}, min {s.min():.3g}, max {s.max():.3g}, "
                     f"senaste {s.iloc[-1]:.3g} (första aktiva ursprung {s.index[0]})")
    # ridge coefficients at the last fit
    for name in ("k9_ridge_h3", "k9_ridge_h12"):
        v = VARIANTS[name]
        d = designs[v.h]
        o = d.index.max()
        tr = train_rows(d, o)
        model, params = fit_ridge(tr[FEATURES].to_numpy(dtype=float), (tr["actual"] - tr["rb"]).to_numpy(), v.h)
        coef = pd.Series(model[-1].coef_, index=FEATURES).round(3)
        lines.append(f"\n`{name}` senaste anpassning (ursprung {o}, alpha {params['alpha']}, intercept "
                     f"{model[-1].intercept_:+.3f}), standardiserade koefficienter: "
                     + ", ".join(f"{k} {c:+.3f}" for k, c in coef.sort_values(key=abs, ascending=False).items()))
    # per-year diff
    lines.append("\n## Diff mot RB per målår (MAE)\n")
    years = {}
    for name, v in VARIANTS.items():
        w = window(frames[v.h], *EVAL)
        years[name] = ((w[name] - w["actual"]).abs() - (w["rb"] - w["actual"]).abs()).groupby(
            w["target"].map(lambda p: p.year)).mean()
    lines.append(pd.DataFrame(years).round(3).to_markdown())
    text = "\n".join(lines) + "\n"
    (OUT / "results_raw.md").write_text("# K9 rådata (genererad av k9_horizon.py)\n\n" + text, encoding="utf-8")
    path = log_run("k9_horizon", log_rows)
    print(text)
    print("logged", path)


if __name__ == "__main__":
    main()
