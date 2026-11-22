"""Bottom-up model on KPIF components (phase 4 and 4b).

SCB publishes each analysis group's contribution ("effect") to KPIF's monthly
change, in percentage points; the five contributions sum to KPIF m/m (up to rounding).
We forecast each contribution separately and sum them.

Each component = seasonal pattern + 12-month trend (baseline), optionally plus an
expanding-window regression of the baseline's error on that component's drivers:

- energy: this month's electricity spot change and fuel proxy change (no intercept)
- services / food / goods: NIER price plans from the previous month's survey (with intercept)

The KPIF m/m forecast (pp) is then turned into y/y via the known index.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from kpif_nowcast.baselines import seasonal_trend_additive, yy_from_mm


@dataclass
class Correction:
    cols: list[str]
    train_start: str
    intercept: bool = False
    min_train: int = 24


def fit_correction(resid: pd.Series, features: pd.DataFrame, spec: Correction) -> pd.DataFrame:
    """Expanding-window OLS of the baseline error on drivers; coefficients for t use months < t only."""
    data = pd.concat([resid.rename("resid"), features[spec.cols]], axis=1)
    data = data.loc[pd.Period(spec.train_start, "M"):].dropna(subset=spec.cols)
    X_all = data[spec.cols].to_numpy()
    if spec.intercept:
        X_all = np.column_stack([np.ones(len(data)), X_all])
    names = (["const"] if spec.intercept else []) + spec.cols

    out = {}
    has_y = data["resid"].notna().to_numpy()
    for i, t in enumerate(data.index):
        mask = has_y[:i]
        if mask.sum() < spec.min_train:
            continue
        coef, *_ = np.linalg.lstsq(X_all[:i][mask], data["resid"].to_numpy()[:i][mask], rcond=None)
        out[t] = {"correction": float(X_all[i] @ coef), **{f"b_{n}": b for n, b in zip(names, coef)}}
    res = pd.DataFrame(out).T
    res.index = pd.PeriodIndex(res.index, freq="M")
    return res


def allocate_tax(components: pd.DataFrame, tax: pd.DataFrame) -> pd.DataFrame:
    """Split the monthly tax effect on KPIF (pp) across components.

    Energy gets tax_total minus the non-energy part (from KPIF-XE vs KPIF-XE-KS) when that
    split exists (~2020 onwards); the non-energy part (or the whole effect, earlier) is spread
    across components by weight. Rough, but the total is exact, which is what the forecast adds back.
    """
    w = components.pivot(index="month", columns="component", values="weight") / 1000
    total = tax["tax_total"].reindex(w.index).fillna(0)
    nonenergy = (tax["tax_xe_own"].reindex(w.index) * (1 - w["energy"])).fillna(total)
    energy_part = total - nonenergy
    others = w.drop(columns="energy")
    alloc = others.div(others.sum(axis=1), axis=0).mul(nonenergy, axis=0)
    alloc["energy"] = energy_part + 0.0
    has_split = tax["tax_xe_own"].reindex(w.index).notna()
    # before the split exists: spread everything by weight, energy included
    alloc.loc[~has_split] = w.loc[~has_split].mul(total[~has_split], axis=0)
    return alloc[w.columns]


def component_forecast(
    index: pd.Series,
    components: pd.DataFrame,
    features: pd.DataFrame,
    corrections: dict[str, Correction],
    tax: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """If `tax` is given: model tax-cleaned contributions, then add back month t's known tax effect."""
    effects = components.pivot(index="month", columns="component", values="effect_month")
    if tax is not None:
        effects = effects - allocate_tax(components, tax).reindex(effects.index).fillna(0)
    effects = effects.reindex(pd.period_range(effects.index.min(), effects.index.max() + 1, freq="M"))
    base = effects.apply(seasonal_trend_additive)  # includes next (unpublished) month

    fc = base.copy()
    coefs = []
    valid = base.index
    for comp, spec in corrections.items():
        corr = fit_correction(effects[comp] - base[comp], features, spec)
        fc[comp] = base[comp] + corr["correction"]
        valid = valid.intersection(corr.index)
        coefs.append(corr.drop(columns="correction").add_prefix(f"{comp}:"))

    fc = fc.reindex(valid)
    out = fc.add_prefix("fc_")
    out["mm_hat_pp"] = fc.sum(axis=1)
    if tax is not None:
        out["tax_effect"] = tax["tax_total"].reindex(out.index).fillna(0)
        out["mm_hat_pp"] += out["tax_effect"]
    # extend the index by one month so the unpublished target month gets a y/y forecast
    idx = index.reindex(pd.period_range(index.index.min(), index.index.max() + 1, freq="M"))
    out["yy_hat"] = yy_from_mm(idx, (out["mm_hat_pp"] / 100).reindex(idx.index)).reindex(out.index)
    return out.join(pd.concat(coefs, axis=1)) if coefs else out


ENERGY = Correction(["fuel_chg", "el_chg"], "2021-12")
ENERGY_FUEL_ONLY = Correction(["fuel_chg"], "2005-01")


def ki_corrections(kind: str) -> dict[str, Correction]:
    """kind: 'l1' (level of price plans) or 'dev' (deviation from 12-month average)."""
    return {
        "services": Correction([f"ki_services_{kind}"], "2005-01", intercept=True),
        "food": Correction([f"ki_grocery_{kind}"], "2005-01", intercept=True),
        "goods": Correction([f"ki_durables_{kind}"], "2005-01", intercept=True),
    }
