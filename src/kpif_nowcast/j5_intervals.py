"""J5: sequential prediction intervals for the one-month KPIF nowcast, methods U1-U6.

Preregistered in docs/auto/j5/hypotes.md. Point forecast: comp_fuel. The interval for t uses only
errors of months <= t-1 and features of t (el_chg, fuel_chg; known at the deadline).

`interval_for(...)` is the function a live forecast would call (proposal; forecast.py is not changed).

Run: python -m kpif_nowcast.j5_intervals
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

QUANTILES = [0.05, 0.10, 0.25, 0.75, 0.90, 0.95]
LEVELS = {50: (0.25, 0.75), 80: (0.10, 0.90), 90: (0.05, 0.95)}
METHODS = ["j5_abs_all", "j5_abs_36", "j5_signed_all", "j5_ewma", "j5_scaled_energy", "j5_qreg_energy"]
MIN_PAST = 36
EWMA_LAMBDA = 0.9
SIGMA_FLOOR = 0.05


def _conformal(scores: np.ndarray, q: float) -> float:
    """Finite-sample conformal quantile of past scores."""
    n = len(scores)
    k = min(n, int(np.ceil((n + 1) * q)))
    return float(np.sort(scores)[max(k, 1) - 1])


def interval_for(method: str, past_err: np.ndarray, past_x: np.ndarray, x_t: np.ndarray) -> dict[float, float]:
    """Quantiles of the error for the target month (add the point forecast to get the interval).

    past_err: errors (forecast - outcome... sign: outcome - forecast) of earlier months, oldest first;
    past_x / x_t: [|el_chg|, |fuel_chg|] for those months / the target month.
    """
    e = past_err
    out = {}
    if method in ("j5_abs_all", "j5_abs_36"):
        a = np.abs(e[-36:] if method == "j5_abs_36" else e)
        for lo, hi in LEVELS.values():
            w = _conformal(a, hi - lo)
            out[lo], out[hi] = -w, w
    elif method == "j5_signed_all":
        for q in QUANTILES:
            out[q] = float(np.quantile(e, q))
    elif method == "j5_ewma":
        # sigma_s for each past month s from errors before s; sigma_t from all past errors
        sig = np.empty(len(e))
        v = np.mean(e[:12] ** 2)
        for s in range(len(e)):
            sig[s] = np.sqrt(v)
            v = EWMA_LAMBDA * v + (1 - EWMA_LAMBDA) * e[s] ** 2
        z = e / np.maximum(sig, SIGMA_FLOOR)
        for q in QUANTILES:
            out[q] = float(np.quantile(z[12:], q)) * max(np.sqrt(v), SIGMA_FLOOR)
    elif method == "j5_scaled_energy":
        X = np.column_stack([np.ones(len(e)), past_x])
        b = np.linalg.lstsq(X, np.abs(e), rcond=None)[0]
        sig_past = np.maximum(X @ b, SIGMA_FLOOR)
        sig_t = max(float(np.r_[1.0, x_t] @ b), SIGMA_FLOOR)
        z = e / sig_past
        for q in QUANTILES:
            out[q] = float(np.quantile(z, q)) * sig_t
    elif method == "j5_qreg_energy":
        from sklearn.linear_model import QuantileRegressor

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for q in QUANTILES:
                m = QuantileRegressor(quantile=q, alpha=0.0, solver="highs").fit(past_x, e)
                out[q] = float(m.predict(x_t.reshape(1, -1))[0])
        vals = np.sort([out[q] for q in QUANTILES])
        out = dict(zip(QUANTILES, vals))
    else:
        raise ValueError(method)
    return out


def sequential(err: pd.Series, x: pd.DataFrame, method: str, start: str = "2015-01") -> pd.DataFrame:
    """For each t >= start: error quantiles from months < t. err = outcome - forecast."""
    err = err.dropna()
    rows = {}
    for t in err.index[err.index >= pd.Period(start, "M")]:
        past = err.loc[: t - 1]
        xp = x.reindex(past.index)
        ok = xp.notna().all(axis=1).to_numpy()
        if method in ("j5_scaled_energy", "j5_qreg_energy"):
            pe, px = past.to_numpy()[ok], xp.to_numpy()[ok]
        else:
            pe, px = past.to_numpy(), xp.to_numpy()
        if len(pe) < MIN_PAST or x.loc[t].isna().any():
            continue
        rows[t] = interval_for(method, pe, px, x.loc[t].to_numpy())
    return pd.DataFrame(rows).T


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    from scipy.stats import beta

    lo = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return float(lo), float(hi)


def pinball(e: np.ndarray, qhat: pd.DataFrame) -> float:
    loss = []
    for q in QUANTILES:
        u = e - qhat[q].to_numpy()
        loss.append(np.mean(np.maximum(q * u, (q - 1) * u)))
    return float(np.mean(loss))


def evaluate(err: pd.Series, qhat: pd.DataFrame, mask: pd.Series | None = None) -> dict:
    e = err.reindex(qhat.index)
    if mask is not None:
        qhat, e = qhat[mask.reindex(qhat.index).fillna(False)], e[mask.reindex(qhat.index).fillna(False)]
    res = {"n": len(e), "pinball": pinball(e.to_numpy(), qhat)}
    for lvl, (lo, hi) in LEVELS.items():
        hit = ((e >= qhat[lo]) & (e <= qhat[hi])).to_numpy()
        k = int(hit.sum())
        ci = clopper_pearson(k, len(hit))
        res[f"cov{lvl}"] = 100 * k / len(hit)
        res[f"cov{lvl}_ci"] = f"{100 * ci[0]:.0f}–{100 * ci[1]:.0f}"
        res[f"width{lvl}"] = float((qhat[hi] - qhat[lo]).mean())
    return res


def main() -> None:
    from pathlib import Path

    from kpif_nowcast.backtest import build_predictions
    from kpif_nowcast.evaluation import log_run
    from kpif_nowcast.features import load_features

    preds, actual, _ = build_predictions()
    err = (actual - preds["comp_fuel"]).loc[: pd.Period("2026-10", "M")].dropna()
    f = load_features()
    x = pd.DataFrame({"abs_el": f["el_chg"].abs(), "abs_fuel": f["fuel_chg"].abs()})
    qh = {m: sequential(err, x, m) for m in METHODS}
    common = sorted(set.intersection(*[set(q.index) for q in qh.values()]))
    common = pd.PeriodIndex(common, freq="M")
    common = common[common <= pd.Period("2026-10", "M")]
    absel = x["abs_el"].reindex(common)
    calm, turb = absel <= absel.quantile(1 / 3), absel >= absel.quantile(2 / 3)
    lines, log_rows = [f"Point forecast comp_fuel; evaluation months {common.min()}..{common.max()} (n={len(common)}).\n"], []
    for label, mask in [("all", None), ("turbulent (top third |el_chg|)", turb), ("calm (bottom third |el_chg|)", calm)]:
        tab = pd.DataFrame({m: evaluate(err, qh[m].reindex(common), mask) for m in METHODS}).T
        lines.append(f"## {label}\n\n{tab.round(3).to_markdown()}\n")
        print(f"\n{label}\n{tab.round(3)}")
        for m, row in tab.iterrows():
            log_rows.append({"variant": m, "period": f"2015-2026 {label}", "n": int(row["n"]),
                             "MAE": round(float(row["pinball"]), 4), "dm_p_vs_rb_updated": float("nan")})
    # coverage by year (50/80/90), method by method
    yrs = {}
    for m in METHODS:
        q = qh[m].reindex(common)
        e = err.reindex(common)
        for lvl, (lo, hi) in LEVELS.items():
            hit = (e >= q[lo]) & (e <= q[hi])
            yrs[(m, lvl)] = 100 * hit.groupby(common.year).mean()
    lines.append(f"## Coverage by year (%)\n\n{pd.DataFrame(yrs).round(0).to_markdown()}\n")
    path = log_run("j5_intervals", log_rows)
    lines.append(f"Run log: `{path.name}` (column MAE holds the pinball loss)\n")
    root = Path(__file__).resolve().parents[2]
    (root / "docs" / "auto" / "j5" / "results_raw.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
