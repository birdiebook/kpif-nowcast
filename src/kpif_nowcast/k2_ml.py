"""K2: can a regularised or boosted model improve the 50/50 average of rb_updated and J2 V2?

Preregistered in docs/auto2/k2/hypotes.md (8 variants). Target = residual of a base forecast
(rb_updated, j2 = J2 V2 `j2_el_dev`, or avg = 0.5*rb_updated + 0.5*j2); forecast = base + predicted residual.

Nested validation: for each target month t the model is fitted on rows s < t with a published outcome
(KPIF for t-1 is out mid-month t, before t's deadline). Hyperparameters are chosen inside that window by
TimeSeriesSplit(4) on MAE, then the model is refitted on the whole window. Imputation and scaling are
fitted on training rows only (a Pipeline). Before MIN_TRAIN rows the forecast is the 50/50 average.

Features for row s are computed from what was known at s's own deadline (catalog series via
observations.as_of), so training rows are pseudo-real-time too.

Run: python -m kpif_nowcast.k2_ml
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

from kpif_nowcast.j1_hybrid import build_panel
from kpif_nowcast.j2_el import build_j2_features
from kpif_nowcast.riksbank_benchmark import deadline

MIN_TRAIN = 36
N_SPLITS = 4
EXCLUDE_CATALOG = {"kpif_index", "kpif_yy", "jobads_ai", "jobads_ml"}
SMALL = ["gap", "energy_news", "fuel_chg", "el_dev", "core_dev", "last_resid_rb", "last_resid_j2",
         "ki_services_dev", "ki_grocery_dev", "ki_durables_dev", "ea_news", "rb_months_ahead",
         "gap_x_age", "energy_x_age"]

RIDGE_GRID = [{"alpha": a} for a in (0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000)]
LASSO_GRID = [{"alpha": a} for a in (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2)]
HGB_GRID = [{"learning_rate": lr, "max_depth": d, "max_iter": it}
            for lr in (0.03, 0.1) for d in (2, 3) for it in (50, 150)]


@dataclass(frozen=True)
class Variant:
    base: str  # "avg", "rb", "j2"
    model: str  # "ridge", "lasso", "hgb", "ens"
    fset: str  # "S" or "L"


VARIANTS = {
    "k2_avg_ridge_s": Variant("avg", "ridge", "S"),
    "k2_avg_lasso_s": Variant("avg", "lasso", "S"),
    "k2_avg_hgb_s": Variant("avg", "hgb", "S"),
    "k2_avg_ens_s": Variant("avg", "ens", "S"),
    "k2_avg_ridge_l": Variant("avg", "ridge", "L"),
    "k2_rb_ridge_s": Variant("rb", "ridge", "S"),
    "k2_j2_ridge_s": Variant("j2", "ridge", "S"),
    "k2_rb_hgb_s": Variant("rb", "hgb", "S"),
}
# Added after the results (marked as such in docs/auto2/k2/resultat.md, counts against the cap, not in the
# Holm family): k2_avg_ridge_l without the revised=True catalog series, to check the revision-leak flag.
POSTHOC = {"k2_avg_ridge_lnr": Variant("avg", "ridge", "LNR")}
ALL_VARIANTS = {**VARIANTS, **POSTHOC}


def catalog_keys() -> list[tuple[str, str, bool]]:
    """(key, unit, revised) for the monthly catalog series in feature set L."""
    from kpif_nowcast.catalog import CATALOG

    return [(s.key, s.unit, s.revised) for s in CATALOG
            if s.freq == "M" and s.key not in EXCLUDE_CATALOG and not s.key.startswith("af_")]


def build_design(kpif, comps, feats, contracts, se3, rb_fc, obs, with_catalog: bool = True) -> pd.DataFrame:
    """Panel (bases, outcome) plus all features; row t uses only data known at deadline(t)."""
    from kpif_nowcast.j3_screen import feature

    panel = build_panel(kpif, comps, feats, contracts, se3, rb_fc, obs)
    j2f = build_j2_features(feats, contracts, se3)
    d = pd.DataFrame(index=panel.index)
    d["actual"] = panel["actual"]
    d["rb"] = panel["rb_updated"]
    d["j2"] = panel["j2"]
    d["avg"] = 0.5 * d["rb"] + 0.5 * d["j2"]
    d["gap"] = d["j2"] - d["rb"]
    d["energy_news"] = panel["energy_news"]
    d["fuel_chg"] = j2f["fuel_chg"].reindex(d.index)
    d["el_dev"] = j2f["el_dev"].reindex(d.index)
    d["core_dev"] = panel["core_dev"]
    prev = d.index - 1
    d["last_resid_rb"] = (d["actual"] - d["rb"]).reindex(prev).to_numpy()
    d["last_resid_j2"] = (d["actual"] - d["j2"]).reindex(prev).to_numpy()
    for k in ("ki_services_dev", "ki_grocery_dev", "ki_durables_dev"):
        d[k] = feats[k].reindex(d.index)
    d["ea_news"] = panel["ea_news"]
    d["rb_months_ahead"] = panel["rb_months_ahead"].astype(float)
    age = d["rb_months_ahead"].clip(upper=3)
    d["gap_x_age"] = d["gap"] * age
    d["energy_x_age"] = d["energy_news"] * age
    if with_catalog:
        dates = {t: deadline(t) for t in d.index}
        lasts = {t: t for t in d.index}
        for key, unit, _ in catalog_keys():
            d[f"cat_{key}"] = feature(key, unit, obs, dates, lasts).reindex(d.index)
    return d


def feature_cols(d: pd.DataFrame, fset: str) -> list[str]:
    if fset == "S":
        return SMALL
    revised = {f"cat_{k}" for k, _, r in catalog_keys() if r} if fset == "LNR" else set()
    return SMALL + [c for c in d.columns if c.startswith("cat_") and c not in revised]


def _make(model: str, params: dict):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import Lasso, Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if model == "hgb":
        return HistGradientBoostingRegressor(loss="squared_error", min_samples_leaf=8, early_stopping=False,
                                             random_state=0, **params)
    est = Ridge(**params) if model == "ridge" else Lasso(max_iter=20000, **params)
    return make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(), est)


GRIDS = {"ridge": RIDGE_GRID, "lasso": LASSO_GRID, "hgb": HGB_GRID}


def fit_nested(model: str, X: np.ndarray, y: np.ndarray):
    """Choose hyperparameters by inner TimeSeriesSplit (MAE), refit on all rows. Returns (fitted, params)."""
    from sklearn.model_selection import TimeSeriesSplit

    splits = list(TimeSeriesSplit(n_splits=N_SPLITS).split(X))
    best, best_mae = None, np.inf
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for params in GRIDS[model]:
            errs = []
            for tr, va in splits:
                m = _make(model, params).fit(X[tr], y[tr])
                errs.append(np.abs(m.predict(X[va]) - y[va]))
            mae = float(np.mean(np.concatenate(errs)))
            if mae < best_mae:
                best, best_mae = params, mae
        return _make(model, best).fit(X, y), best


class K2Runner:
    """Fits per (base, model, fset, row) once and caches, so the ensemble reuses its members."""

    def __init__(self, design: pd.DataFrame):
        self.d = design
        self.cache: dict = {}

    def start_resid(self, base: str, i: int) -> float:
        r = self.d.iloc[i]
        return float(r["avg"] - r[base])

    def member(self, base: str, model: str, fset: str, i: int):
        key = (base, model, fset, i)
        if key not in self.cache:
            d = self.d
            cols = feature_cols(d, fset)
            y_all = (d["actual"] - d[base]).to_numpy()
            train = np.arange(i)[~np.isnan(y_all[:i])]
            if len(train) < MIN_TRAIN:
                self.cache[key] = None
            else:
                X = d[cols].to_numpy(dtype=float)
                self.cache[key] = fit_nested(model, X[train], y_all[train])
        return self.cache[key]

    def resid(self, name: str, i: int, X_row: np.ndarray | None = None) -> float:
        v = ALL_VARIANTS[name]
        members = ["ridge", "hgb"] if v.model == "ens" else [v.model]
        preds = []
        for m in members:
            fit = self.member(v.base, m, v.fset, i)
            if fit is None:
                return self.start_resid(v.base, i)
            x = self.d[feature_cols(self.d, v.fset)].iloc[[i]].to_numpy(dtype=float) if X_row is None else X_row
            preds.append(float(fit[0].predict(x)[0]))
        return float(np.mean(preds))

    def forecast(self, name: str, i: int) -> float:
        return float(self.d[ALL_VARIANTS[name].base].iat[i]) + self.resid(name, i)

    def series(self, name: str) -> pd.Series:
        return pd.Series([self.forecast(name, i) for i in range(len(self.d))], index=self.d.index, name=name)


def forecast_at(design: pd.DataFrame, t: pd.Period, name: str) -> float:
    return K2Runner(design).forecast(name, design.index.get_loc(t))


# ------------------------------------------------------------------ explanation


def ridge_path(run: K2Runner, name: str) -> pd.DataFrame:
    """Standardised coefficients and alpha in the last window of each year."""
    v = VARIANTS[name]
    cols = feature_cols(run.d, v.fset)
    rows = {}
    for i, t in enumerate(run.d.index):
        fit = run.member(v.base, v.model, v.fset, i)
        if fit is None or not (t.month == 12 or i == len(run.d) - 1):
            continue
        est = fit[0][-1]
        rows[str(t)] = {"alpha": fit[1]["alpha"], "intercept": est.intercept_, **dict(zip(cols, est.coef_))}
    return pd.DataFrame(rows)


def lasso_selection(run: K2Runner, name: str) -> pd.Series:
    v = VARIANTS[name]
    cols = feature_cols(run.d, v.fset)
    nz = [np.abs(f[0][-1].coef_) > 1e-12 for i in range(len(run.d))
          if (f := run.member(v.base, v.model, v.fset, i)) is not None]
    return pd.Series(np.mean(nz, axis=0), index=cols).sort_values(ascending=False)


def oos_permutation(run: K2Runner, name: str, reps: int = 20, seed: int = 0) -> pd.DataFrame:
    """MAE increase on active out-of-sample months when one feature is permuted (each month's own model)."""
    v = VARIANTS[name]
    cols = feature_cols(run.d, v.fset)
    X = run.d[cols].to_numpy(dtype=float)
    act = [i for i in range(len(run.d)) if run.member(v.base, "ridge" if v.model == "ens" else v.model, v.fset, i)
           is not None and not np.isnan(run.d["actual"].iat[i])]
    base = run.d[v.base].to_numpy()[act]
    y = run.d["actual"].to_numpy()[act]

    def mae(Xa):
        return np.mean(np.abs(base + np.array([run.resid(name, i, Xa[k:k + 1]) for k, i in enumerate(act)]) - y))

    ref = mae(X[act])
    rng = np.random.default_rng(seed)
    out = {}
    for j, c in enumerate(cols):
        inc = []
        for _ in range(reps):
            Xp = X[act].copy()
            Xp[:, j] = rng.permutation(Xp[:, j])
            inc.append(mae(Xp) - ref)
        out[c] = {"mae_increase": float(np.mean(inc)), "sd": float(np.std(inc))}
    return pd.DataFrame(out).T.sort_values("mae_increase", ascending=False).assign(ref_mae=ref, n=len(act))


# ------------------------------------------------------------------ evaluation


def main() -> None:
    from pathlib import Path

    from kpif_nowcast.data import load_components, load_el_contracts, load_kpif, load_riksbank_forecasts
    from kpif_nowcast.evaluation import log_run
    from kpif_nowcast.features import load_features
    from kpif_nowcast.j1_hybrid import dm_one_sided
    from kpif_nowcast.j2_el import holm, zone_monthly_spot
    from kpif_nowcast.observations import load as load_obs

    warnings.filterwarnings("ignore")
    d = build_design(load_kpif(), load_components(), load_features(), load_el_contracts(),
                     zone_monthly_spot("SE3"), load_riksbank_forecasts(), load_obs())
    run = K2Runner(d)
    preds = d[["rb", "j2", "avg"]].rename(columns={"rb": "rb_updated", "avg": "avg_5050"})
    for name in VARIANTS:
        preds[name] = run.series(name)
        print("done", name, flush=True)
    actual = d["actual"]
    refs = {"avg_5050": "50/50", "rb_updated": "rb_updated", "j2": "J2 V2"}
    lines, log_rows = [], []
    for label, start in [("2015-02..2026-10 (primary)", "2015-02"), ("2018-02..2026-10 (ML active)", "2018-02"),
                         ("2024-01..2026-10 (used, report only)", "2024-01")]:
        p = preds.loc[pd.Period(start, "M"): pd.Period("2026-10", "M")]
        p = p[actual.reindex(p.index).notna()].dropna()
        err = p.sub(actual.reindex(p.index), axis=0)
        tab = pd.DataFrame({"MAE": err.abs().mean(), "RMSE": np.sqrt((err ** 2).mean()), "bias": err.mean(),
                            "n": err.count()})
        for ref in refs:
            raw = {m: dm_one_sided(err[m].to_numpy(), err[ref].to_numpy())[1] for m in VARIANTS}
            h = holm(raw)
            for m in VARIANTS:
                tab.loc[m, f"diff_{ref}"] = tab.loc[m, "MAE"] - tab.loc[ref, "MAE"]
                tab.loc[m, f"p1_{ref}"] = raw[m]
                tab.loc[m, f"holm_{ref}"] = h[m]
        for m, row in tab.iterrows():
            log_rows.append({"variant": m, "period": label, "n": int(row["n"]), "MAE": round(row["MAE"], 4),
                             "dm_p_vs_rb_updated": round(row.get("p1_rb_updated", float("nan")), 4)})
        lines.append(f"## {label} (n={len(p)}; DM one-sided, H1: variant lower MAE; Holm over 8 per reference)\n\n"
                     f"{tab.round(3).to_markdown()}\n")
        print(f"\n{label}\n{tab.round(3)}", flush=True)

    # explanation
    for name in ("k2_avg_ridge_s", "k2_rb_ridge_s", "k2_j2_ridge_s"):
        lines.append(f"## Ridge path {name} (standardised coefficients, last window each year)\n\n"
                     f"{ridge_path(run, name).round(3).to_markdown()}\n")
    rl = ridge_path(run, "k2_avg_ridge_l")
    top = rl.drop(index=["alpha", "intercept"]).iloc[:, -1].abs().sort_values(ascending=False).index[:15]
    lines.append(f"## Ridge path k2_avg_ridge_l (alpha + top 15 by |coef| in last window)\n\n"
                 f"{rl.loc[['alpha', 'intercept', *top]].round(4).to_markdown()}\n")
    lines.append(f"## Lasso k2_avg_lasso_s: share of windows with nonzero weight\n\n"
                 f"{lasso_selection(run, 'k2_avg_lasso_s').round(2).to_frame('share').to_markdown()}\n")
    for name in ("k2_avg_hgb_s", "k2_rb_hgb_s", "k2_avg_ridge_s"):
        pi = oos_permutation(run, name)
        lines.append(f"## Out-of-sample permutation importance {name} (MAE increase, 20 reps)\n\n"
                     f"{pi.round(4).to_markdown()}\n")
        print(name, pi.head(6).round(4), sep="\n", flush=True)
    hp = {}
    for name in ("k2_avg_hgb_s", "k2_rb_hgb_s"):
        v = VARIANTS[name]
        ch = [str(f[1]) for i in range(len(d)) if (f := run.member(v.base, v.model, v.fset, i)) is not None]
        hp[name] = pd.Series(ch).value_counts()
    lines.append(f"## Chosen boosting hyperparameters (count of windows)\n\n{pd.DataFrame(hp).fillna(0).astype(int).to_markdown()}\n")
    revised = {f"cat_{k}": r for k, _, r in catalog_keys()}
    lines.append(f"Feature set L: {len(feature_cols(d, 'L'))} features, of which revised=True: "
                 f"{', '.join(k for k, r in revised.items() if r)}\n")
    path = log_run("k2_ml", log_rows)
    lines.append(f"Run log: `{path.name}`\n")
    root = Path(__file__).resolve().parents[2]
    out = root / "docs" / "auto2" / "k2"
    out.mkdir(parents=True, exist_ok=True)
    (out / "results_raw.md").write_text("\n".join(lines), encoding="utf-8")
    (root / "outputs").mkdir(exist_ok=True)
    preds.join(actual).to_csv(root / "outputs" / "k2_preds.csv")


def posthoc() -> None:
    """Post-hoc diagnostic (not in the Holm family): k2_avg_ridge_lnr vs 50/50 and k2_avg_ridge_l."""
    from kpif_nowcast.data import load_components, load_el_contracts, load_kpif, load_riksbank_forecasts
    from kpif_nowcast.evaluation import log_run
    from kpif_nowcast.features import load_features
    from kpif_nowcast.j1_hybrid import dm_one_sided
    from kpif_nowcast.j2_el import zone_monthly_spot
    from kpif_nowcast.observations import load as load_obs

    warnings.filterwarnings("ignore")
    d = build_design(load_kpif(), load_components(), load_features(), load_el_contracts(),
                     zone_monthly_spot("SE3"), load_riksbank_forecasts(), load_obs())
    run = K2Runner(d)
    preds = pd.DataFrame({"avg_5050": d["avg"], "rb_updated": d["rb"],
                          "k2_avg_ridge_l": run.series("k2_avg_ridge_l"),
                          "k2_avg_ridge_lnr": run.series("k2_avg_ridge_lnr")})
    rows, log_rows = [], []
    for label, start in [("2015-02..2026-10", "2015-02"), ("2024-01..2026-10 (used)", "2024-01")]:
        p = preds.loc[pd.Period(start, "M"): pd.Period("2026-10", "M")]
        p = p[d["actual"].reindex(p.index).notna()]
        err = p.sub(d["actual"].reindex(p.index), axis=0)
        r = {"period": label, "n": len(p), **{f"MAE {c}": err[c].abs().mean() for c in err}}
        r["p1 lnr vs 50/50"] = dm_one_sided(err["k2_avg_ridge_lnr"].to_numpy(), err["avg_5050"].to_numpy())[1]
        r["p two-sided lnr vs ridge_l"] = __import__("kpif_nowcast.evaluation", fromlist=["dm_test"]).dm_test(
            err["k2_avg_ridge_lnr"].to_numpy(), err["k2_avg_ridge_l"].to_numpy()).p
        rows.append(r)
        log_rows.append({"variant": "k2_avg_ridge_lnr (posthoc)", "period": label, "n": len(p),
                         "MAE": round(r["MAE k2_avg_ridge_lnr"], 4),
                         "dm_p_vs_rb_updated": round(dm_one_sided(err["k2_avg_ridge_lnr"].to_numpy(),
                                                                  err["rb_updated"].to_numpy())[1], 4)})
    tab = pd.DataFrame(rows).set_index("period").T
    print(tab)
    path = log_run("k2_ml_posthoc", log_rows)
    from pathlib import Path

    out = Path(__file__).resolve().parents[2] / "docs" / "auto2" / "k2" / "results_raw.md"
    out.write_text(out.read_text(encoding="utf-8") + f"
## Post-hoc (added after results): k2_avg_ridge_lnr = "
                   f"k2_avg_ridge_l without revised series

{tab.to_markdown(floatfmt='.3f')}

Run log: `{path.name}`
",
                   encoding="utf-8")


if __name__ == "__main__":
    import sys

    posthoc() if sys.argv[1:] == ["posthoc"] else main()
