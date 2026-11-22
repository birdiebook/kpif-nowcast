"""Phase 5: KPIF y/y 3, 6 and 12 months ahead (direct forecasts).

Origin o = last published KPIF month. The forecast is made on the same date as the
nowcast for o+1 (day 4 of month o+2). Horizon h targets month o+h.

Features are built point-in-time with observations.as_of(origin date), so the ragged
edge (GDP indicator ~1 month behind, LFS ~3 weeks) is respected. Caveat: backfilled
values are today's vintage, so revisions of the GDP indicator still leak in.

Models (expanding window, refit every origin):
- naive:      y/y stays at today's level
- target:     y/y equals the 2 % inflation target
- reversion:  gap to 2 % shrinks by an estimated factor rho_h
- ridge:      linear regression with shrinkage on all features (standardized on training data)
- gbm:        shallow gradient-boosted trees on the same features (the "ML" model)
All models except naive/target predict the change in y/y from origin to target.

Run: python -m kpif_nowcast.horizon
"""

from __future__ import annotations

import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from kpif_nowcast import observations as obs
from kpif_nowcast.backtest import OUT_DIR
from kpif_nowcast.data import load_riksbank_forecasts

HORIZONS = [3, 6, 12]
TARGET = 2.0
FIRST_ORIGIN = "2003-01"
MIN_TRAIN = 60
FEATURES = [
    "gap", "yy_mom3", "unemp_chg12", "unemp_level12", "gdp_yy", "kix_chg12",
    "rate", "rate_chg12", "brent_chg6", "ki_services",
]


def origin_date(o: pd.Period) -> pd.Timestamp:
    return (o + 2).to_timestamp() + pd.Timedelta(days=3)


def _last(s: pd.Series, k: int = 0) -> float:
    """k-th value from the end of a point-in-time series (0 = latest available)."""
    return float(s.iloc[-1 - k]) if len(s) > k else np.nan


def feature_row(o: pd.Period, table: pd.DataFrame) -> dict:
    d = origin_date(o)
    get = lambda name: obs.as_of(name, d, table)  # noqa: E731
    yy = get("kpif_yy").loc[:o]
    un = get("aku_unemp_nsa")
    kix, rate, brent = get("kix"), get("policy_rate"), get("brent_sek")
    return {
        "origin": o,
        "yy0": _last(yy),
        "gap": _last(yy) - TARGET,
        "yy_mom3": _last(yy) - _last(yy, 3),
        "unemp_chg12": un.iloc[-12:].mean() - un.iloc[-24:-12].mean() if len(un) >= 24 else np.nan,
        "unemp_level12": un.iloc[-12:].mean() if len(un) >= 12 else np.nan,
        "gdp_yy": get("gdp_ind_yy").iloc[-3:].mean(),
        "kix_chg12": np.log(_last(kix) / _last(kix, 12)) * 100,
        "rate": _last(rate),
        "rate_chg12": _last(rate) - _last(rate, 12),
        "brent_chg6": np.log(_last(brent) / _last(brent, 6)) * 100,
        "ki_services": get("ki_services").iloc[-3:].mean(),
    }


def build_dataset() -> pd.DataFrame:
    table = obs.load()
    yy_final = obs.as_of("kpif_yy", "2100-01-01", table)
    last = yy_final.index.max()
    rows = [feature_row(o, table) for o in pd.period_range(FIRST_ORIGIN, last, freq="M")]
    df = pd.DataFrame(rows).set_index("origin")
    for h in HORIZONS:
        df[f"y_{h}"] = yy_final.reindex(df.index + h).to_numpy()
    return df


def riksbank_for(forecasts: pd.DataFrame, when: pd.Timestamp, target: pd.Period) -> float:
    v = forecasts[["policy_round", "cutoff", "published"]].drop_duplicates()
    v = v[(v["published"] < when) & (v["cutoff"] < target)].sort_values("published")
    if v.empty:
        return np.nan
    hit = forecasts[(forecasts["policy_round"] == v["policy_round"].iloc[-1]) & (forecasts["month"] == target)]
    return float(hit["value"].iloc[0]) if len(hit) else np.nan


def backtest(df: pd.DataFrame) -> pd.DataFrame:
    rb = load_riksbank_forecasts()
    out = []
    for h in HORIZONS:
        y = df[f"y_{h}"]
        change = y - df["yy0"]
        for o in df.index:
            train_idx = df.index[df.index + h <= o]  # targets already published at origin o
            train = df.loc[train_idx].dropna(subset=FEATURES + [f"y_{h}"])
            row = {"h": h, "origin": o, "target": o + h, "actual": y.get(o), "yy0": df.at[o, "yy0"],
                   "naive": df.at[o, "yy0"], "target_2pct": TARGET,
                   "riksbank": riksbank_for(rb, origin_date(o), o + h)}
            x = df.loc[[o], FEATURES]
            if len(train) >= MIN_TRAIN and x.notna().all(axis=None):
                ch = change.loc[train.index]
                g = train["gap"].to_numpy()
                rho = float(((y.loc[train.index] - TARGET) * g).sum() / (g**2).sum())
                row["reversion"] = TARGET + rho * df.at[o, "gap"]
                ridge = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(train[FEATURES], ch)
                row["ridge"] = df.at[o, "yy0"] + float(ridge.predict(x)[0])
                gbm = HistGradientBoostingRegressor(
                    max_depth=2, learning_rate=0.05, max_iter=150, min_samples_leaf=15, random_state=0
                ).fit(train[FEATURES], ch)
                row["gbm"] = df.at[o, "yy0"] + float(gbm.predict(x)[0])
            out.append(row)
    return pd.DataFrame(out)


MODELS = ["naive", "target_2pct", "reversion", "ridge", "gbm", "riksbank"]


def summarize(res: pd.DataFrame, start: str, end: str | None = None) -> pd.DataFrame:
    r = res[(res["target"] >= pd.Period(start, "M"))]
    if end:
        r = r[r["target"] <= pd.Period(end, "M")]
    r = r.dropna(subset=["actual", *MODELS])
    tab = {}
    for h, g in r.groupby("h"):
        tab[f"h={h}"] = {m: (g[m] - g["actual"]).abs().mean() for m in MODELS} | {"n": len(g)}
    return pd.DataFrame(tab).round(2)


def main() -> None:
    warnings.filterwarnings("ignore")
    df = build_dataset()
    res = backtest(df)
    res.to_csv(OUT_DIR / "phase5_horizon_backtest.csv", index=False)

    report = []
    for label, (s, e) in {
        "Targets 2015-2026 (common sample with Riksbank)": ("2015-01", None),
        "Targets 2022-2023 (inflation shock)": ("2022-01", "2023-12"),
        "Targets 2024-2026": ("2024-01", None),
    }.items():
        t = summarize(res, s, e)
        report.append(f"## {label} – MAE, pp y/y\n\n{t.to_markdown()}\n")
        print(f"\n{label}\n{t}")

    # Which features matter for the linear model (latest fit, h=12), standardized coefficients
    h = 12
    train = df.dropna(subset=FEATURES + [f"y_{h}"])
    ridge = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(train[FEATURES], train[f"y_{h}"] - train["yy0"])
    coefs = pd.Series(ridge[-1].coef_, index=FEATURES).sort_values(key=abs, ascending=False).round(3)
    report.append(f"## Ridge coefficients, h=12, full sample (standardized)\n\n{coefs.to_frame('coef').to_markdown()}\n")
    print(f"\nRidge coefficients h=12:\n{coefs}")
    (OUT_DIR / "phase5_scores.md").write_text("\n".join(report), encoding="utf-8")

    fig, axes = plt.subplots(len(HORIZONS), 1, figsize=(11, 9), sharex=True)
    for ax, h in zip(axes, HORIZONS):
        g = res[(res["h"] == h) & (res["target"] >= pd.Period("2015-01", "M"))].set_index("target")
        t = g.index.to_timestamp()
        ax.plot(t, g["actual"], color="black", lw=2, label="outcome")
        for m in ["ridge", "gbm", "riksbank", "reversion"]:
            ax.plot(t, g[m], lw=1.1, label=m)
        ax.set_title(f"{h} months ahead")
        ax.grid(alpha=0.3)
    axes[0].legend(ncol=5, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "phase5_horizons.png", dpi=110)


if __name__ == "__main__":
    main()
