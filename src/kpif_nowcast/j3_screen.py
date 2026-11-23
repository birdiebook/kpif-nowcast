"""J3: screen every monthly catalog series as a correction on the base model (h=1, 3, 12).

Protocol preregistered in docs/auto/j3/hypotes.md. Base: rb_updated (h=1) and the Riksbank's
forecast at the origin date (h=3, 12). Correction = b * (x - mean_past(x)), b by expanding OLS
without intercept on past targets whose outcome was published at the forecast date.

Run: python -m kpif_nowcast.j3_screen
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kpif_nowcast import observations as obs
from kpif_nowcast.riksbank_benchmark import deadline

MIN_TRAIN = 24
EXCLUDE = {"kpif_index", "kpif_yy"}
PRIMARY = ("2017-02", "2026-10")
NO_LOG_UNITS = ("%", "nettotal", "std", "100 = normalt")


def screen_keys() -> list[str]:
    from kpif_nowcast.catalog import CATALOG

    # lag_days < 0: deterministic calendars (L2 Easter), not indicators to screen
    return [s.key for s in CATALOG if s.freq == "M" and s.key not in EXCLUDE and s.lag_days >= 0]


def is_growth(key: str, unit: str) -> bool:
    return key.endswith("_yy") or unit.startswith("% årstakt") or key.endswith("_growth")


def transform(s: pd.Series, key: str, unit: str, last: pd.Period) -> float:
    """x at the latest known period p* <= last (preregistered rule)."""
    s = s.loc[:last].dropna()
    if s.empty:
        return np.nan
    p = s.index.max()
    s = s.reindex(pd.period_range(s.index.min(), p, freq="M"))
    if is_growth(key, unit):
        return float(s.iloc[-1] - s.iloc[-2]) if len(s) >= 2 else np.nan
    use_log = (s.dropna() > 0).all() and not any(u in unit for u in NO_LOG_UNITS)
    v = np.log(s) * 100 if use_log else s
    if len(v) < 14:
        return np.nan
    d = v.diff()
    return float(d.iloc[-1] - d.iloc[-13])


def feature(key: str, unit: str, table: pd.DataFrame, dates: dict, lasts: dict) -> pd.Series:
    """x per forecast row: as known at dates[row], latest period <= lasts[row]."""
    sub = table[table["series"] == key]
    return pd.Series({r: transform(obs.as_of(key, dates[r], sub), key, unit, lasts[r]) for r in dates}, dtype=float)


def correct(base: pd.Series, actual: pd.Series, x: pd.Series, usable) -> pd.Series:
    """Expanding correction. usable(i) -> positional indices of training rows for row i."""
    r = (actual - base).to_numpy()
    xv = x.to_numpy()
    out = base.to_numpy().copy()
    for i in range(len(base)):
        if np.isnan(xv[i]):
            continue
        j = np.asarray(usable(i), dtype=int)
        j = j[~np.isnan(r[j]) & ~np.isnan(xv[j])] if len(j) else j
        if len(j) < MIN_TRAIN:
            continue
        xbar = xv[j].mean()
        xc = xv[j] - xbar
        denom = xc @ xc
        if denom <= 0:
            continue
        b = (xc @ r[j]) / denom
        out[i] += b * (xv[i] - xbar)
    return pd.Series(out, index=base.index)


def bh(p: pd.Series) -> pd.Series:
    """Benjamini-Hochberg adjusted q-values."""
    p = p.dropna().sort_values()
    m = len(p)
    q = (p * m / np.arange(1, m + 1)).iloc[::-1].cummin().iloc[::-1].clip(upper=1)
    return q


def h1_frame(kpif: pd.DataFrame, rb_fc: pd.DataFrame) -> pd.DataFrame:
    from kpif_nowcast.riksbank_benchmark import riksbank_at_deadline

    actual = kpif["yy_official"]
    months = pd.period_range("2015-01", kpif.index.max() + 1, freq="M")
    rb = riksbank_at_deadline(rb_fc, months, actual).dropna(subset=["rb_updated"])
    return pd.DataFrame({"base": rb["rb_updated"], "actual": actual.reindex(rb.index)})


def h1_usable(index: pd.PeriodIndex):
    # row j (target s) usable for row i (target t) if s <= t-1: outcome of t-1 is out mid-month t
    return lambda i: np.arange(i)


def run_h1(kpif, rb_fc, table, keys_units, extra_x: dict | None = None) -> tuple[pd.DataFrame, dict]:
    f = h1_frame(kpif, rb_fc)
    dates = {t: deadline(t) for t in f.index}
    lasts = {t: t for t in f.index}
    xs = extra_x or {k: feature(k, u, table, dates, lasts) for k, u in keys_units}
    preds = {k: correct(f["base"], f["actual"], xs[k].reindex(f.index), h1_usable(f.index)) for k in xs}
    return f, preds, xs


def origin_date(o: pd.Period) -> pd.Timestamp:
    return (o + 2).to_timestamp() + pd.Timedelta(days=3)


def hk_frame(kpif: pd.DataFrame, rb_fc: pd.DataFrame, h: int) -> pd.DataFrame:
    from kpif_nowcast.horizon import riksbank_for

    actual = kpif["yy_official"]
    rows = {}
    for o in pd.period_range("2012-01", kpif.index.max(), freq="M"):
        b = riksbank_for(rb_fc, origin_date(o), o + h)
        if not np.isnan(b):
            rows[o] = {"target": o + h, "base": b, "actual": actual.get(o + h, np.nan)}
    return pd.DataFrame(rows).T.astype({"base": float, "actual": float})


def run_hk(kpif, rb_fc, table, keys_units, h: int):
    f = hk_frame(kpif, rb_fc, h)
    dates = {o: origin_date(o) for o in f.index}
    lasts = {o: o + 1 for o in f.index}
    origins = f.index
    usable = lambda i: np.where(origins + h <= origins[i])[0]  # noqa: E731  targets published at origin
    xs = {k: feature(k, u, table, dates, lasts) for k, u in keys_units}
    preds = {k: correct(f["base"], f["actual"], xs[k].reindex(f.index), usable) for k in xs}
    return f, preds


def score_table(f: pd.DataFrame, preds: dict, start: str, end: str, h: int, revised: dict,
                target_col: str | None = None) -> pd.DataFrame:
    from kpif_nowcast.evaluation import dm_test

    tgt = f[target_col] if target_col else pd.Series(f.index, index=f.index)
    sel = (tgt >= pd.Period(start, "M")) & (tgt <= pd.Period(end, "M")) & f["actual"].notna()
    fs = f[sel]
    e_base = (fs["base"] - fs["actual"]).to_numpy()
    rows = {}
    for k, p in preds.items():
        e = (p[sel] - fs["actual"]).to_numpy()
        r = dm_test(e, e_base, h=h)
        p1 = r.p / 2 if r.mean_diff < 0 else 1 - r.p / 2
        rows[k] = {"MAE": np.mean(np.abs(e)), "diff": r.mean_diff, "p1": p1, "n": r.n,
                   "n_active": int((p[sel] != fs["base"]).sum()), "revised": revised.get(k, False)}
    t = pd.DataFrame(rows).T
    t["bh_q"] = bh(t["p1"].astype(float))
    t.attrs["base_mae"] = float(np.mean(np.abs(e_base)))
    t.attrs["n"] = len(fs)
    return t.sort_values("p1")


def main() -> None:
    import warnings
    from pathlib import Path

    from kpif_nowcast.catalog import CATALOG
    from kpif_nowcast.data import load_kpif, load_riksbank_forecasts
    from kpif_nowcast.evaluation import dm_test, log_run

    warnings.filterwarnings("ignore")
    kpif, rb_fc, table = load_kpif(), load_riksbank_forecasts(), obs.load()
    specs = {s.key: s for s in CATALOG}
    keys_units = [(k, specs[k].unit) for k in screen_keys()]
    revised = {k: specs[k].revised for k in specs}

    lines, log_rows = [], []
    f1, p1, xs = run_h1(kpif, rb_fc, table, keys_units)
    tabs = {}
    for label, (s, e) in {"h=1 primary 2017-02..2026-10": PRIMARY, "h=1 2015-2026": ("2015-01", "2026-10")}.items():
        t = score_table(f1, p1, s, e, 1, revised)
        tabs[label] = t
        lines.append(f"## {label} (base rb_updated MAE {t.attrs['base_mae']:.3f}, n={t.attrs['n']})\n\n"
                     f"{t.astype({'MAE': float, 'diff': float, 'p1': float}).round(3).to_markdown()}\n")
    for h in (3, 12):
        fh, ph = run_hk(kpif, rb_fc, table, keys_units, h)
        t = score_table(fh, ph, *PRIMARY, h, revised, target_col="target")
        tabs[f"h={h}"] = t
        lines.append(f"## h={h}, targets 2017-02..2026-10 (base Riksbank MAE {t.attrs['base_mae']:.3f}, n={t.attrs['n']})\n\n"
                     f"{t.astype({'MAE': float, 'diff': float, 'p1': float}).round(3).to_markdown()}\n")
    for label, t in tabs.items():
        for k, row in t.iterrows():
            log_rows.append({"variant": f"j3_{k}", "period": label, "n": int(row["n"]), "MAE": round(float(row["MAE"]), 4),
                             "dm_p_vs_rb_updated": round(float(row["p1"]), 4)})
        print(label, t.head(8)[["MAE", "diff", "p1", "bh_q", "revised"]], sep="\n")

    # Combination (one preregistered variant): BH survivors at h=1 primary, else top-3 raw p
    prim = tabs["h=1 primary 2017-02..2026-10"]
    surv = prim[prim["bh_q"] < 0.10].index[:3].tolist()
    chosen, tag = (surv, "BH survivors") if surv else (prim.index[:3].tolist(), "no BH survivor: top-3 raw p")
    combo = combined_h1(f1, xs, chosen)
    sel = (f1.index >= pd.Period(PRIMARY[0], "M")) & (f1.index <= pd.Period(PRIMARY[1], "M")) & f1["actual"].notna()
    e_c = (combo[sel] - f1["actual"][sel]).to_numpy()
    e_b = (f1["base"][sel] - f1["actual"][sel]).to_numpy()
    r = dm_test(e_c, e_b)
    pc = r.p / 2 if r.mean_diff < 0 else 1 - r.p / 2
    lines.append(f"## Combination ({tag}): {', '.join(chosen)}\n\nMAE {np.mean(np.abs(e_c)):.3f} vs rb_updated "
                 f"{np.mean(np.abs(e_b)):.3f}, diff {r.mean_diff:+.3f}, one-sided p {pc:.3f}, n {r.n}\n")
    log_rows.append({"variant": "j3_combo", "period": "h=1 primary", "n": r.n, "MAE": round(float(np.mean(np.abs(e_c))), 4),
                     "dm_p_vs_rb_updated": round(pc, 4)})
    print(lines[-1])
    path = log_run("j3_screen", log_rows)
    lines.append(f"Run log: `{path.name}`\n")
    root = Path(__file__).resolve().parents[2]
    (root / "docs" / "auto" / "j3" / "results_raw.md").write_text("\n".join(lines), encoding="utf-8")


def combined_h1(f: pd.DataFrame, xs: dict, keys: list[str]) -> pd.Series:
    """rb_updated + OLS (no intercept, centred) on several x's, expanding, min 24 rows."""
    r = (f["actual"] - f["base"]).to_numpy()
    X = np.column_stack([xs[k].reindex(f.index).to_numpy() for k in keys])
    out = f["base"].to_numpy().copy()
    for i in range(len(f)):
        if np.isnan(X[i]).any():
            continue
        j = np.arange(i)
        j = j[~np.isnan(r[j]) & ~np.isnan(X[j]).any(axis=1)]
        if len(j) < MIN_TRAIN:
            continue
        xbar = X[j].mean(axis=0)
        b = np.linalg.lstsq(X[j] - xbar, r[j], rcond=None)[0]
        out[i] += (X[i] - xbar) @ b
    return pd.Series(out, index=f.index)


if __name__ == "__main__":
    main()
