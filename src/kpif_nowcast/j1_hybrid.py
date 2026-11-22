"""J1: hybrid of rb_updated ("Riksbank + latest miss") and what happened after the Riksbank's cutoff.

Preregistered in docs/auto/j1/hypotes.md (variants C1-C4, H1-H4). "j2" is J2's V2 component
model (`j2_el_dev`). Everything estimated (weights, betas) uses an expanding window over months
< t whose outcome is known at t's deadline; before 24 such months a preregistered start value is used.

Run: python -m kpif_nowcast.j1_hybrid
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kpif_nowcast.baselines import seasonal_trend_additive
from kpif_nowcast.j2_el import build_j2_features, j2_forecast
from kpif_nowcast.riksbank_benchmark import deadline, riksbank_at_deadline

MIN_TRAIN = 24
MIN_PER_AGE = 12
EA_SERIES = "ea_flash_total"
VARIANTS = ["j1_comb_equal", "j1_comb_invmse", "j1_comb_ols", "j1_comb_ols_age",
            "j1_hyb_energy_fixed", "j1_hyb_energy", "j1_hyb_energy_core", "j1_hyb_energy_ea"]


def ea_news(obs: pd.DataFrame, months: pd.PeriodIndex) -> pd.Series:
    """Flash y/y for t minus flash for t-1, both as known at t's deadline; 0 when missing."""
    t_obs = obs[obs["series"] == EA_SERIES].copy()
    t_obs["period"] = pd.PeriodIndex(t_obs["period"], freq="M")
    out = {}
    for t in months:
        known = t_obs[t_obs["known_from"] <= deadline(t)].sort_values("known_from").groupby("period")["value"].last()
        out[t] = known.get(t, np.nan) - known.get(t - 1, np.nan)
    return pd.Series(out, dtype=float).fillna(0.0)


def build_panel(kpif, comps, feats, contracts, se3, rb_fc, obs) -> pd.DataFrame:
    """One row per target month t with everything known at t's deadline (plus the outcome, for scoring)."""
    index, actual = kpif["index"], kpif["yy_official"]
    j2f = build_j2_features(feats, contracts, se3)
    j2 = j2_forecast(index, comps, j2f, "j2_el_dev")
    effects = comps.pivot(index="month", columns="component", values="effect_month")
    effects = effects.reindex(pd.period_range(effects.index.min(), effects.index.max() + 1, freq="M"))
    base = effects.apply(seasonal_trend_additive)
    energy_news = (j2["fc_energy"] - base["energy"].reindex(j2.index)).rename("energy_news")
    core_dev = (effects.drop(columns="energy") - base.drop(columns="energy")).sum(axis=1, min_count=1).shift(1)
    rb = riksbank_at_deadline(rb_fc, j2.index, actual)
    panel = pd.DataFrame({"j2": j2["yy_hat"], "energy_news": energy_news}).join(rb[["rb_updated", "rb_months_ahead"]])
    panel["core_dev"] = core_dev.reindex(panel.index)
    panel["ea_news"] = ea_news(obs, panel.index)
    panel["actual"] = actual.reindex(panel.index)
    return panel.dropna(subset=["j2", "rb_updated"])


def _ols_no_const(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.linalg.lstsq(X, y, rcond=None)[0]


def j1_forecast(panel: pd.DataFrame, variant: str) -> pd.Series:
    """Forecast per month; estimation for t uses only rows s < t with a known outcome."""
    p = panel
    rbu, j2 = p["rb_updated"].to_numpy(), p["j2"].to_numpy()
    y = p["actual"].to_numpy()
    out = np.full(len(p), np.nan)
    for i in range(len(p)):
        past = np.arange(i)[~np.isnan(y[:i])]
        n = len(past)
        if variant == "j1_comb_equal":
            out[i] = 0.5 * rbu[i] + 0.5 * j2[i]
        elif variant == "j1_comb_invmse":
            if n < MIN_TRAIN:
                w = 0.5
            else:
                m_rb, m_j2 = np.mean((rbu[past] - y[past]) ** 2), np.mean((j2[past] - y[past]) ** 2)
                w = (1 / m_j2) / (1 / m_j2 + 1 / m_rb)
            out[i] = (1 - w) * rbu[i] + w * j2[i]
        elif variant in ("j1_comb_ols", "j1_comb_ols_age"):
            def beta(idx):
                d = (j2 - rbu)[idx]
                return float(np.clip(_ols_no_const(d[:, None], (y - rbu)[idx])[0], 0, 1))
            b = 0.5 if n < MIN_TRAIN else beta(past)
            if variant == "j1_comb_ols_age" and n >= MIN_TRAIN:
                age = np.minimum(p["rb_months_ahead"].to_numpy(), 3)
                same = past[age[past] == age[i]]
                if len(same) >= MIN_PER_AGE:
                    b = beta(same)
            out[i] = rbu[i] + b * (j2[i] - rbu[i])
        elif variant == "j1_hyb_energy_fixed":
            out[i] = rbu[i] + p["energy_news"].iat[i]
        else:
            cols = {"j1_hyb_energy": ["energy_news"], "j1_hyb_energy_core": ["energy_news", "core_dev"],
                    "j1_hyb_energy_ea": ["energy_news", "ea_news"]}[variant]
            X = p[cols].to_numpy()
            start = np.array([1.0] + [0.0] * (len(cols) - 1))
            ok = past[~np.isnan(X[past]).any(axis=1)]
            coef = start if len(ok) < MIN_TRAIN else _ols_no_const(X[ok], (y - rbu)[ok])
            xi = np.nan_to_num(X[i])
            out[i] = rbu[i] + xi @ coef
    return pd.Series(out, index=p.index, name=variant)


def dm_one_sided(ea, eb):
    """One-sided DM p for H1: variant a has lower mean absolute error than b."""
    from kpif_nowcast.evaluation import dm_test

    r = dm_test(ea, eb)
    p_two = r.p
    return r, (p_two / 2 if r.mean_diff < 0 else 1 - p_two / 2)


def main() -> None:
    from pathlib import Path

    from kpif_nowcast.backtest import score
    from kpif_nowcast.data import load_components, load_el_contracts, load_kpif, load_riksbank_forecasts
    from kpif_nowcast.evaluation import log_run
    from kpif_nowcast.features import load_features
    from kpif_nowcast.j2_el import holm, zone_monthly_spot
    from kpif_nowcast.observations import load as load_obs

    panel = build_panel(load_kpif(), load_components(), load_features(), load_el_contracts(),
                        zone_monthly_spot("SE3"), load_riksbank_forecasts(), load_obs())
    preds = panel[["rb_updated", "j2"]].copy()
    for v in VARIANTS:
        preds[v] = j1_forecast(panel, v)
    actual = panel["actual"]
    lines, log_rows = [], []
    for label, start in [("2015-2026", "2015-01"), ("2017-02..2026-10 (all estimates >=24 obs)", "2017-02"),
                         ("2024-2026 (used)", "2024-01")]:
        p = preds.loc[pd.Period(start, "M"): pd.Period("2026-10", "M")]
        p = p[actual.reindex(p.index).notna()].dropna()
        err = p.sub(actual.reindex(p.index), axis=0)
        table = score(actual, p)
        raw = {}
        for m in [*VARIANTS, "j2"]:
            r, p1 = dm_one_sided(err[m].to_numpy(), err["rb_updated"].to_numpy())
            raw[m] = p1
            table.loc[m, "diff_vs_rb_updated"] = r.mean_diff
            table.loc[m, "dm_p1_vs_rb_updated"] = p1
        h = holm({m: raw[m] for m in VARIANTS})
        for m in VARIANTS:
            table.loc[m, "holm_p1"] = h[m]
        for m, row in table.iterrows():
            log_rows.append({"variant": m, "period": label, "n": int(row["n"]), "MAE": round(row["MAE"], 4),
                             "dm_p_vs_rb_updated": round(row.get("dm_p1_vs_rb_updated", float("nan")), 4)})
        lines.append(f"## {label} (n={len(p)}; DM one-sided, H1: lower MAE than rb_updated)\n\n{table.round(3).to_markdown()}\n")
        print(f"\n{label} n={len(p)}\n{table[['MAE', 'diff_vs_rb_updated', 'dm_p1_vs_rb_updated', 'holm_p1']].round(3)}")

    p = preds.loc["2015-01":"2026-10"].dropna()
    p = p[actual.reindex(p.index).notna()]
    age = panel["rb_months_ahead"].reindex(p.index).clip(upper=3)
    by_age = p.sub(actual.reindex(p.index), axis=0).abs().groupby(age).mean().assign(n=age.value_counts())
    lines.append(f"## MAE by months since Riksbank cutoff (3 = 3+), 2015-2026\n\n{by_age.round(3).T.to_markdown()}\n")
    print(by_age.round(3).T)
    path = log_run("j1_hybrid", log_rows)
    lines.append(f"Run log: `{path.name}`\n")
    root = Path(__file__).resolve().parents[2]
    (root / "docs" / "auto" / "j1").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "auto" / "j1" / "results_raw.md").write_text("\n".join(lines), encoding="utf-8")
    (root / "outputs").mkdir(exist_ok=True)
    preds.join(panel[["actual", "rb_months_ahead", "energy_news", "core_dev", "ea_news"]]).to_csv(root / "outputs" / "j1_preds.csv")


if __name__ == "__main__":
    main()
