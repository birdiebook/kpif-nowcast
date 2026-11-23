"""K2b: independent, adversarial review of K2 (docs/auto2/k2b/granskning.md).

No new model variants: every run re-uses K2's frozen variants (k2_ml.VARIANTS) on perturbed inputs.

Scenarios (observation table perturbed, everything else unchanged):
- base:    as K2 (reproduction).
- fwd:     sabotage. Every K2 catalog series and the euro-area flash (feeds ea_news in S) gets the value
           of the NEXT period under the same known_from, i.e. the model is handed future data.
- back:    every such series gets the value of the PREVIOUS period (one month more publication delay).
- decfix:  correction. The backfill sets known_from = period end + 2 days for the Eurostat flash, but the
           December flash is released 4-7 January (after our deadline, day 4), and the January 2026 flash
           on 4 February. Those periods get their real release date, so they are not usable at the deadline.
- no2223:  base inputs, but rows 2022-01..2023-12 are dropped from training and from evaluation.

Run: python -m kpif_nowcast.k2b_review [scenario ...]
"""

from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

from kpif_nowcast.k2_ml import ALL_VARIANTS, MIN_TRAIN, VARIANTS, K2Runner, build_design, catalog_keys, fit_nested

FLASH = ["ea_flash_total", "ea_flash_energy", "ea_flash_food", "ea_flash_goods", "ea_flash_services"]
# Eurostat flash releases that fall after day 4 of the following month (euro indicators release calendar;
# 2019-01-04, 2022-01-07, 2023-01-06, 2024-01-05, 2025-01-07, 2026-01-07, 2026-02-04 confirmed by the
# release codes 2-DDMMYYYY-AP; the other Decembers are also in the first working week of January).
LATE_FLASH = {
    "2017-12": "2018-01-05", "2018-12": "2019-01-04", "2019-12": "2020-01-07", "2020-12": "2021-01-07",
    "2021-12": "2022-01-07", "2022-12": "2023-01-06", "2023-12": "2024-01-05", "2024-12": "2025-01-07",
    "2025-12": "2026-01-07", "2026-01": "2026-02-04",
}
CORE3 = ["k2_avg_ridge_s", "k2_avg_ens_s", "k2_avg_ridge_l"]
START, END = pd.Period("2015-02", "M"), pd.Period("2026-10", "M")


def shifted_obs(obs: pd.DataFrame, keys: list[str], k: int) -> pd.DataFrame:
    """Value of period p := latest-vintage value of p+k, known_from of p unchanged (k=+1 future data)."""
    out = [obs[~obs["series"].isin(keys)]]
    for key in keys:
        sub = obs[obs["series"] == key].sort_values("known_from").groupby("period").last().reset_index()
        per = pd.PeriodIndex(sub["period"], freq="M")
        vals = pd.Series(sub["value"].to_numpy(), index=per)
        sub["value"] = vals.reindex(per + k).to_numpy()
        out.append(sub.dropna(subset=["value"]))
    return pd.concat(out, ignore_index=True)


def decfix_obs(obs: pd.DataFrame) -> pd.DataFrame:
    o = obs.copy()
    for p, rel in LATE_FLASH.items():
        m = o["series"].isin(FLASH) & (o["period"].astype(str) == p)
        o.loc[m, "known_from"] = np.maximum(o.loc[m, "known_from"], pd.Timestamp(rel))
    return o


class MaskedRunner(K2Runner):
    """K2Runner whose training rows exclude a set of months (the no2223 scenario)."""

    def __init__(self, design: pd.DataFrame, drop: pd.PeriodIndex):
        super().__init__(design)
        self.drop = np.asarray(design.index.isin(drop))

    def member(self, base, model, fset, i):
        key = (base, model, fset, i)
        if key not in self.cache:
            from kpif_nowcast.k2_ml import feature_cols

            d = self.d
            y_all = (d["actual"] - d[base]).to_numpy()
            ok = ~np.isnan(y_all[:i]) & ~self.drop[:i]
            train = np.arange(i)[ok]
            if len(train) < MIN_TRAIN:
                self.cache[key] = None
            else:
                X = d[feature_cols(d, fset)].to_numpy(dtype=float)
                self.cache[key] = fit_nested(model, X[train], y_all[train])
        return self.cache[key]


def load_all():
    from kpif_nowcast.data import load_components, load_el_contracts, load_kpif, load_riksbank_forecasts
    from kpif_nowcast.features import load_features
    from kpif_nowcast.j2_el import zone_monthly_spot
    from kpif_nowcast.observations import load as load_obs

    return (load_kpif(), load_components(), load_features(), load_el_contracts(), zone_monthly_spot("SE3"),
            load_riksbank_forecasts(), load_obs())


def predictions(scenario: str, data, names: list[str]) -> pd.DataFrame:
    kpif, comps, feats, contracts, se3, rb_fc, obs = data
    keys = sorted({k for k, _, _ in catalog_keys()} | set(FLASH))
    if scenario == "fwd":
        obs = shifted_obs(obs, keys, +1)
    elif scenario == "back":
        obs = shifted_obs(obs, keys, -1)
    elif scenario == "decfix":
        obs = decfix_obs(obs)
    d = build_design(kpif, comps, feats, contracts, se3, rb_fc, obs)
    drop = pd.period_range("2022-01", "2023-12", freq="M")
    run = MaskedRunner(d, drop) if scenario == "no2223" else K2Runner(d)
    p = pd.DataFrame({"avg_5050": d["avg"], "rb_updated": d["rb"], "j2": d["j2"], "actual": d["actual"]})
    for n in names:
        p[n] = run.series(n)
        print(scenario, "done", n, flush=True)
    if scenario == "no2223":
        p = p[~p.index.isin(drop)]
    return p


def score(p: pd.DataFrame, names: list[str], start=START, end=END) -> pd.DataFrame:
    from kpif_nowcast.j1_hybrid import dm_one_sided
    from kpif_nowcast.j2_el import holm

    q = p.loc[start:end]
    q = q[q["actual"].notna()]
    err = q.drop(columns="actual").sub(q["actual"], axis=0)
    rows = {}
    raw = {n: dm_one_sided(err[n].to_numpy(), err["avg_5050"].to_numpy())[1] for n in names}
    h = holm(raw) if len(names) == len(VARIANTS) else {n: np.nan for n in names}
    for n in [*names, "avg_5050", "j2", "rb_updated"]:
        rows[n] = {"n": int(err[n].notna().sum()), "MAE": err[n].abs().mean(),
                   "diff_5050": err[n].abs().mean() - err["avg_5050"].abs().mean(),
                   "p1_vs_5050": raw.get(n, np.nan), "holm8_vs_5050": h.get(n, np.nan)}
    return pd.DataFrame(rows).T


def per_year(p: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    q = p.loc[START:END]
    q = q[q["actual"].notna()]
    ae = q.drop(columns="actual").sub(q["actual"], axis=0).abs()
    g = ae.groupby(ae.index.year)
    out = pd.DataFrame({n: g[n].mean() - g["avg_5050"].mean() for n in names})
    out["MAE_5050"] = g["avg_5050"].mean()
    out["n"] = g.size()
    return out


def main(scenarios: list[str]) -> None:
    from pathlib import Path

    from kpif_nowcast.evaluation import log_run

    warnings.filterwarnings("ignore")
    root = Path(__file__).resolve().parents[2]
    outdir = root / "outputs" / "k2b"
    outdir.mkdir(parents=True, exist_ok=True)
    data = load_all()
    lines, log_rows = [], []
    for sc in scenarios:
        names = list(VARIANTS) if sc in ("base", "decfix") else CORE3
        p = predictions(sc, data, names)
        p.to_csv(outdir / f"preds_{sc}.csv")
        tab = score(p, names)
        lines.append(f"## {sc}: 2015-02..2026-10 (DM one-sided vs 50/50; Holm over K2's 8 where all 8 run)\n\n"
                     f"{tab.round(4).to_markdown()}\n")
        for lab, s0 in [("2018-02..2026-10", "2018-02"), ("2024-01..2026-10", "2024-01")]:
            lines.append(f"### {sc}: {lab}\n\n{score(p, names, pd.Period(s0, 'M')).round(4).to_markdown()}\n")
        if sc in ("base", "decfix"):
            lines.append(f"### {sc}: per year, MAE difference vs 50/50 (negative = better)\n\n"
                         f"{per_year(p, CORE3).round(3).to_markdown()}\n")
            for excl in [("excl. 2022-23", ["2022", "2023"])]:
                q = p[~p.index.year.isin([int(y) for y in excl[1]])]
                lines.append(f"### {sc}: evaluated {excl[0]} (models trained as usual)\n\n"
                             f"{score(q, names).round(4).to_markdown()}\n")
        print(tab.round(4), flush=True)
        for n, r in tab.iterrows():
            log_rows.append({"variant": f"{n} [{sc}]", "period": "2015-02..2026-10", "n": int(r["n"]),
                             "MAE": round(float(r["MAE"]), 4), "dm_p_vs_rb_updated": np.nan})
    path = log_run("k2b_review_" + "_".join(scenarios), log_rows)
    lines.append(f"Run log: `{path.name}`\n")
    (outdir / f"review_{'_'.join(scenarios)}.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:] or ["base", "decfix", "fwd", "back", "no2223"])
