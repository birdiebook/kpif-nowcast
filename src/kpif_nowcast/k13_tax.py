"""K13: tax-cleaned base. Variants k13_j2_clean and k13_ens_clean.

Preregistered in docs/auto2/k13/hypotes.md; event sources in docs/skattekalender.md.

Idea: the component models forecast each component's contribution to KPIF m/m as seasonal pattern +
12-month trend. One-off tax changes (the food VAT cut 2026-04, the temporary fuel tax cuts 2026) then
leak into the trend for 12 months and into the same-month seasonal factor for 5 years. Here the known
effect of identified one-off events is removed from the history before season, trend and the energy
correction are estimated, and added back in the target month only if the event was decided before
the forecast deadline (day 4 of t+1).

Tax effect per month (SCB's mechanical calculation, full pass-through):
    tax_total = KPIF m/m - KPIF-KS m/m,  non-energy part ne = tax_xe_own * (1 - w_energy),
    energy part en = tax_total - ne.

Information set for target t:
- history cleaning uses the realised KS part of event months s < t (published with KPI for s, ~13th of s+1,
  i.e. before deadline(t) for every s <= t-1), only for events decided before deadline(s);
- add-back in t: "start" events use the calendar constant `pe` (SCB's mechanical number, see the doc for the
  caveat); "end" events use minus the realised KS part of their start month (< t, known).

Run: python -m kpif_nowcast.k13_tax          (backtest, both variants, writes docs/auto2/k13/results_raw.md)
     python -m kpif_nowcast.k13_tax current  (2026-11/12 forecasts with and without cleaning)
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, replace
from datetime import date

import numpy as np
import pandas as pd

from kpif_nowcast.baselines import seasonal_trend_additive, yy_from_mm
from kpif_nowcast.component_model import Correction, fit_correction
from kpif_nowcast.riksbank_benchmark import deadline

J2_ENERGY = Correction(["fuel_chg", "el_dev"], "2012-01")  # J2 V2 (j2_el_dev)


@dataclass(frozen=True)
class TaxEvent:
    month: str  # first month with the new tax
    component: str  # TAB6628 component that carries the effect
    part: str  # "en" (energy part of KS) or "ne" (non-energy part)
    kind: str  # "start" or "end"
    decided: date  # parliament decision, upper bound ("senast")
    label: str
    pe: float | None = None  # start events: mechanical effect on KPIF m/m (pp), SCB KS calculation
    start_of: str | None = None  # end events: the start month whose effect is reversed

    @property
    def period(self) -> pd.Period:
        return pd.Period(self.month, "M")


EVENTS: list[TaxEvent] = [
    TaxEvent("2022-05", "energy", "en", "start", date(2022, 4, 30),
             "Temporary energy tax cut petrol/diesel 1.05 SEK/l, prop. 2021/22:221", pe=-0.258),
    TaxEvent("2022-10", "energy", "en", "end", date(2022, 4, 30),
             "End of the 2022-05 cut (sunset 2022-09-30)", start_of="2022-05"),
    TaxEvent("2026-01", "energy", "en", "start", date(2025, 11, 30),
             "Lower energy tax on electricity, budget bill 2026", pe=-0.132),
    TaxEvent("2026-04", "food", "ne", "start", date(2025, 11, 30),
             "Food VAT 12% -> 6% 2026-04-01..2027-12-31, budget bill 2026", pe=-0.773),
    TaxEvent("2026-05", "energy", "en", "start", date(2026, 4, 30),
             "Temporary energy tax cut petrol/diesel to EU minimum 2026-05..09, prop. 2025/26:236", pe=-0.115),
    TaxEvent("2026-07", "energy", "en", "start", date(2026, 6, 30),
             "Temporary CO2 tax cut petrol/diesel 2.40 SEK/l 2026-07..11, prop. 2025/26:275", pe=-0.398),
    TaxEvent("2026-10", "energy", "en", "end", date(2026, 4, 30),
             "End of the 2026-05 energy tax cut (sunset 2026-09-30)", start_of="2026-05"),
    TaxEvent("2026-12", "energy", "en", "end", date(2026, 6, 30),
             "End of the 2026-07 CO2 tax cut (sunset 2026-11-30)", start_of="2026-07"),
]


def ks_parts(tax: pd.DataFrame, components: pd.DataFrame) -> pd.DataFrame:
    """Energy (en) and non-energy (ne) part of the monthly KS tax effect on KPIF m/m, pp."""
    w_e = components.pivot(index="month", columns="component", values="weight")["energy"] / 1000
    ne = tax["tax_xe_own"] * (1 - w_e.reindex(tax.index))
    return pd.DataFrame({"en": tax["tax_total"] - ne, "ne": ne})


def known(ev: TaxEvent, t: pd.Period) -> bool:
    """Is the event decided before the deadline of target month t?"""
    return pd.Timestamp(ev.decided) < deadline(t)


def cleaning(parts: pd.DataFrame, events: list[TaxEvent], columns) -> pd.DataFrame:
    """Realised KS amount to subtract, per (event month, component). Events decided after their own
    month's deadline are never cleaned (conservative; none in the calendar)."""
    out = pd.DataFrame(0.0, index=parts.index, columns=list(columns))
    for ev in events:
        if ev.period in parts.index and known(ev, ev.period):
            v = parts.at[ev.period, ev.part]
            if pd.notna(v):
                out.at[ev.period, ev.component] += v
    return out


def addback(t: pd.Period, parts: pd.DataFrame, events: list[TaxEvent], columns) -> pd.Series:
    """Known tax effect added to target month t, per component. Uses parts only for months < t."""
    out = pd.Series(0.0, index=list(columns))
    for ev in events:
        if ev.period != t or not known(ev, t):
            continue
        if ev.kind == "start":
            out[ev.component] += ev.pe
        else:
            s = pd.Period(ev.start_of, "M")
            assert s < t
            v = parts[ev.part].get(s, np.nan)
            out[ev.component] += -v if pd.notna(v) else -next(e.pe for e in events if e.month == ev.start_of)
    return out


def clean_component_forecast(index: pd.Series, components: pd.DataFrame, features: pd.DataFrame,
                             corrections: dict[str, Correction], tax: pd.DataFrame | None,
                             events: list[TaxEvent]) -> pd.DataFrame:
    """Component model (seasonal + 12m trend + corrections) on tax-cleaned contributions, plus the known
    add-back in the target month. With events=[] this equals component_forecast(...) without tax.

    Row t uses contributions and KS up to t-1 (the backtest is one vectorised pass: the cleaned value at
    s only enters forecasts for months > s)."""
    effects = components.pivot(index="month", columns="component", values="effect_month")
    cols = effects.columns
    if events:
        parts = ks_parts(tax, components)
        effects = effects - cleaning(parts, events, cols).reindex(effects.index).fillna(0.0)
    else:
        parts = pd.DataFrame(columns=["en", "ne"], dtype=float)
    effects = effects.reindex(pd.period_range(effects.index.min(), effects.index.max() + 1, freq="M"))
    base = effects.apply(seasonal_trend_additive)
    fc = base.copy()
    valid = base.index
    for comp, spec in corrections.items():
        corr = fit_correction(effects[comp] - base[comp], features, spec)
        fc[comp] = base[comp] + corr["correction"]
        valid = valid.intersection(corr.index)
    fc = fc.reindex(valid)
    add = pd.DataFrame([addback(t, parts, events, cols) for t in fc.index], index=fc.index) if events \
        else pd.DataFrame(0.0, index=fc.index, columns=cols)
    out = fc.add_prefix("fc_")
    out["base_energy"] = base["energy"].reindex(fc.index)
    out["tax_addback"] = add.sum(axis=1)
    out["mm_hat_pp"] = fc.sum(axis=1) + out["tax_addback"]
    idx = index.reindex(pd.period_range(index.index.min(), index.index.max() + 1, freq="M"))
    out["yy_hat"] = yy_from_mm(idx, (out["mm_hat_pp"] / 100).reindex(idx.index)).reindex(out.index)
    out["cleaned_core_dev"] = (effects.drop(columns="energy") - base.drop(columns="energy")).sum(
        axis=1, min_count=1).shift(1).reindex(out.index)
    return out


def j2_clean(index, components, j2feats, tax, events) -> pd.DataFrame:
    return clean_component_forecast(index, components, j2feats, {"energy": J2_ENERGY}, tax, events)


def clean_design(design: pd.DataFrame, j2c: pd.DataFrame) -> pd.DataFrame:
    """K2 design with the J2 part swapped for the tax-cleaned J2 (J2-derived features recomputed)."""
    d = design.copy()
    d["j2"] = j2c["yy_hat"].reindex(d.index)
    d["avg"] = 0.5 * d["rb"] + 0.5 * d["j2"]
    d["gap"] = d["j2"] - d["rb"]
    d["energy_news"] = (j2c["fc_energy"] - j2c["base_energy"]).reindex(d.index)
    d["core_dev"] = j2c["cleaned_core_dev"].reindex(d.index)
    d["last_resid_j2"] = (d["actual"] - d["j2"]).reindex(d.index - 1).to_numpy()
    age = d["rb_months_ahead"].clip(upper=3)
    d["gap_x_age"] = d["gap"] * age
    d["energy_x_age"] = d["energy_news"] * age
    return d


def scale_starts(events: list[TaxEvent], f: float) -> list[TaxEvent]:
    return [replace(e, pe=e.pe * f) if e.kind == "start" else e for e in events]


# ------------------------------------------------------------------ evaluation

PERIOD = ("2015-02", "2026-10")


def _inputs(partial_last_month: bool = False):
    from kpif_nowcast.data import (load_components, load_el_contracts, load_kpif, load_riksbank_forecasts,
                                   load_tax_effects)
    from kpif_nowcast.features import load_features
    from kpif_nowcast.j2_el import zone_monthly_spot
    from kpif_nowcast.observations import load as load_obs

    if partial_last_month:  # live-style features: partial electricity month allowed (forecast.py does the same)
        from kpif_nowcast.features import build_features, electricity_monthly, fuel_proxy_daily
        feats = build_features(electricity_monthly(min_days=1), fuel_proxy_daily())
    else:
        feats = load_features()
    return dict(kpif=load_kpif(), comps=load_components(), feats=feats, contracts=load_el_contracts(),
                se3=zone_monthly_spot("SE3"), rb_fc=load_riksbank_forecasts(), obs=load_obs(),
                tax=load_tax_effects())


def build_all(inp: dict, events: list[TaxEvent] = EVENTS):
    from kpif_nowcast.j2_el import build_j2_features
    from kpif_nowcast.k2_ml import build_design

    j2f = build_j2_features(inp["feats"], inp["contracts"], inp["se3"])
    index = inp["kpif"]["index"]
    j2_raw = j2_clean(index, inp["comps"], j2f, None, [])
    j2_c = j2_clean(index, inp["comps"], j2f, inp["tax"], events)
    design = build_design(inp["kpif"], inp["comps"], inp["feats"], inp["contracts"], inp["se3"], inp["rb_fc"],
                          inp["obs"], with_catalog=False)
    return j2_raw, j2_c, design, clean_design(design, j2_c)


def main() -> None:
    from pathlib import Path

    from kpif_nowcast.evaluation import log_run
    from kpif_nowcast.j1_hybrid import dm_one_sided
    from kpif_nowcast.j2_el import holm
    from kpif_nowcast.k2_ml import K2Runner

    warnings.filterwarnings("ignore")
    inp = _inputs()
    j2_raw, j2_c, design, design_c = build_all(inp)
    assert np.allclose(j2_raw["yy_hat"].reindex(design.index), design["j2"], atol=1e-10), "J2 V2 mismatch"
    preds = pd.DataFrame({"rb_updated": design["rb"], "avg_5050": design["avg"], "j2": design["j2"],
                          "k13_j2_clean": design_c["j2"]})
    preds["k2_avg_ens_s"] = K2Runner(design).series("k2_avg_ens_s")
    print("done k2_avg_ens_s", flush=True)
    preds["k13_ens_clean"] = K2Runner(design_c).series("k2_avg_ens_s")
    print("done k13_ens_clean", flush=True)
    actual = design["actual"]
    pairs = {"k13_j2_clean": "j2", "k13_ens_clean": "k2_avg_ens_s"}
    event_months = {e.period for e in EVENTS}

    lines, log_rows = [], []

    def table(p: pd.DataFrame, label: str, holm_family: bool):
        p = p[actual.reindex(p.index).notna()].dropna()
        err = p.sub(actual.reindex(p.index), axis=0)
        tab = pd.DataFrame({"MAE": err.abs().mean(), "RMSE": np.sqrt((err ** 2).mean()), "bias": err.mean(),
                            "n": err.count()})
        raw = {m: dm_one_sided(err[m].to_numpy(), err[r].to_numpy())[1] for m, r in pairs.items()}
        h = holm(raw)
        for m, r in pairs.items():
            tab.loc[m, "ref"] = r
            tab.loc[m, "diff_vs_ref"] = tab.loc[m, "MAE"] - tab.loc[r, "MAE"]
            tab.loc[m, "p1_raw"] = raw[m]
            tab.loc[m, "holm_p" if holm_family else "holm_p (report only)"] = h[m]
        for m in p:
            tab.loc[m, "p1_vs_rb_updated"] = dm_one_sided(err[m].to_numpy(), err["rb_updated"].to_numpy())[1] \
                if m != "rb_updated" else np.nan
        lines.append(f"## {label} (n={len(p)}; DM one-sided, H1: variant lower MAE than its reference)\n\n"
                     f"{tab.round(4).to_markdown()}\n")
        print(f"\n{label}\n{tab.round(4)}", flush=True)
        for m, row in tab.iterrows():
            log_rows.append({"variant": m, "period": label, "n": int(row["n"]), "MAE": round(row["MAE"], 4),
                             "dm_p_vs_rb_updated": round(row.get("p1_vs_rb_updated", float("nan")), 4)})
        return err

    s, e = (pd.Period(x, "M") for x in PERIOD)
    err = table(preds.loc[s:e], f"{PERIOD[0]}..{PERIOD[1]} (primary, Holm over 2)", True)
    table(preds.loc[s:e][[t not in event_months for t in preds.loc[s:e].index]],
          "2015-02..2026-10 without event months (base effect only)", False)
    table(preds.loc[pd.Period("2024-01", "M"):e], "2024-01..2026-10 (used, report only)", False)
    table(preds.loc[pd.Period("2026-04", "M"):e], "2026-04..2026-10 (after the VAT cut, report only)", False)

    yr = err.abs().groupby(err.index.year).mean()
    diff = pd.DataFrame({m: yr[m] - yr[r] for m, r in pairs.items()}).assign(n=err.groupby(err.index.year).size())
    lines.append(f"## Diff in MAE vs reference by year\n\n{diff.round(4).to_markdown()}\n")

    ev = preds.loc[[t for t in sorted(event_months) if t in preds.index]].join(actual.rename("actual"))
    ev["addback_pp_mm"] = j2_c["tax_addback"].reindex(ev.index)
    lines.append(f"## Event months: forecasts and outcome (y/y)\n\n{ev.round(3).to_markdown()}\n")

    # sensitivity: start-event add-back scaled +-20% (J2 variant only, cheap)
    from kpif_nowcast.j2_el import build_j2_features
    j2f = build_j2_features(inp["feats"], inp["contracts"], inp["se3"])
    sens = {}
    for f in (0.8, 1.0, 1.2):
        y = j2_clean(inp["kpif"]["index"], inp["comps"], j2f, inp["tax"], scale_starts(EVENTS, f))["yy_hat"]
        ee = (y - actual).loc[err.index]
        sens[f"pe x {f}"] = {"MAE": ee.abs().mean(), "diff_vs_j2": ee.abs().mean() - err["j2"].abs().mean()}
    lines.append(f"## Sensitivity: start-event add-back scaled (k13_j2_clean, primary period)\n\n"
                 f"{pd.DataFrame(sens).T.round(4).to_markdown()}\n")

    path = log_run("k13_tax", log_rows)
    lines.append(f"Run log: `{path.name}`\n")
    root = Path(__file__).resolve().parents[2]
    out = root / "docs" / "auto2" / "k13"
    out.mkdir(parents=True, exist_ok=True)
    (out / "results_raw.md").write_text("\n".join(lines), encoding="utf-8")
    (root / "outputs").mkdir(exist_ok=True)
    preds.join(actual.rename("actual")).to_csv(root / "outputs" / "k13_preds.csv")


def current() -> None:
    """2026-11 (and 2026-12 add-back) with and without cleaning: live main model, J2 V2, K2 ensemble.

    Uses live-style features (partial electricity month, as forecast.py), local caches only."""
    import os
    from pathlib import Path

    from kpif_nowcast.component_model import ENERGY
    from kpif_nowcast.k2_ml import K2Runner

    os.environ.setdefault("KPIF_OFFLINE", "1")
    warnings.filterwarnings("ignore")
    inp = _inputs(partial_last_month=True)
    index, comps, tax = inp["kpif"]["index"], inp["comps"], inp["tax"]
    target = index.index.max() + 1
    rows = {}
    main_raw = clean_component_forecast(index, comps, inp["feats"], {"energy": ENERGY}, None, [])
    main_c = clean_component_forecast(index, comps, inp["feats"], {"energy": ENERGY}, tax, EVENTS)
    rows["component_fuel_el_v1 (live main model)"] = (main_raw, main_c)
    j2_raw, j2_c, design, design_c = build_all(inp)
    rows["J2 V2"] = (j2_raw, j2_c)
    lines = [f"# K13: {target} with and without tax cleaning (made {date.today()}, live-style "
             f"features, partial electricity month as in forecast.py)\n"]
    tab = {}
    for name, (r, c) in rows.items():
        tab[name] = {"raw_yy": r.at[target, "yy_hat"], "clean_yy": c.at[target, "yy_hat"],
                     "diff_yy": c.at[target, "yy_hat"] - r.at[target, "yy_hat"],
                     "raw_mm": r.at[target, "mm_hat_pp"], "clean_mm": c.at[target, "mm_hat_pp"],
                     "addback_mm": c.at[target, "tax_addback"],
                     **{f"d_{k[3:]}": c.at[target, k] - r.at[target, k] for k in r.columns if k.startswith("fc_")}}
    if target in design.index:
        i = design.index.get_loc(target)
        r_ens = K2Runner(design).forecast("k2_avg_ens_s", i)
        c_ens = K2Runner(design_c).forecast("k2_avg_ens_s", i)
        tab["k2_avg_ens_s"] = {"raw_yy": r_ens, "clean_yy": c_ens, "diff_yy": c_ens - r_ens}
        tab["rb_updated"] = {"raw_yy": design.at[target, "rb"], "clean_yy": design.at[target, "rb"], "diff_yy": 0.0}
    t = pd.DataFrame(tab).T
    print(t.round(3))
    lines.append(t.round(3).to_markdown() + "\n")
    # December: the add-back alone (the CO2 cut ends 2026-11-30); y/y effect ~ k * add-back
    dec = target + 1
    parts = ks_parts(tax, comps)
    add_dec = addback(dec, parts, EVENTS, comps["component"].unique())
    k = float(index.iloc[-1] / index.iloc[-12]) if len(index) > 12 else 1.0
    lines.append(f"{dec}: known tax add-back {add_dec.sum():+.3f} pp m/m (energy), about {k * add_dec.sum():+.2f} pp "
                 f"y/y relative to a forecast without it; on top of the cleaned base.\n")
    print(lines[-1])
    out = Path(__file__).resolve().parents[2] / "docs" / "auto2" / "k13" / "current_raw.md"
    out.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    import sys

    current() if sys.argv[1:] == ["current"] else main()
