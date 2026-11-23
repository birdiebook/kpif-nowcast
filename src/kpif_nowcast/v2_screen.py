"""V2 (run 3, wave 2): joint screening of run 3's new series as a correction on the two best bases.

Protocol preregistered in docs/auto3/v2/hypotes.md (commit c3f7670). Two bases, screened separately:

- R: `k2_avg_ridge_l` exactly as the shadow forecast (shadow.SHADOW_MODELS, frozen L set, K2b flash dates).
- A: `avg_5050` = `j1_comb_equal` (k0_screen.fifty_fifty_frame).

Each of the 10 hard-coded candidates is screened with j3_screen.correct (expanding OLS without intercept on
centred x, at least 24 rows) and j3_screen.score_table (one-sided DM on absolute errors, BH q = 0.10 per base).
x(t) is j3_screen.transform at the latest period p* known at deadline(t), plus two preregistered date rules:
x is missing when p* is older than the series' normal lag + 2 months (stale), and for el_contract_spot_share
when the transform spans the 2023-01 -> 2023-02 break. At most three series per base (one per source group)
are then tested together once (`v2_r_corr`, `v2_a_corr`, j3_screen.combined_h1), Holm over the variants run,
and the global test over every project variant reuses k12_global (SPA, StepM, MCS, selection bias).

Run: python -m kpif_nowcast.v2_screen [--B 9999] [--refresh]
"""

from __future__ import annotations

import argparse
import json
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kpif_nowcast import observations as obs
from kpif_nowcast.j3_screen import PRIMARY, combined_h1, correct, h1_usable, score_table, transform
from kpif_nowcast.riksbank_benchmark import deadline

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "auto3" / "v2"
CACHE = ROOT / "outputs" / "v2"

# key: (source group, months between the period known at deadline(t) and t) - hypotes.md section 1
CANDIDATES: dict[str, tuple[str, int]] = {
    "easter_window_days": ("resor", 0),
    "kpif_package_holidays_index": ("resor", 1),
    "kpif_air_transport_index": ("resor", 1),
    "kpif_accommodation_index": ("resor", 1),
    "guest_nights_domestic": ("resor", 3),
    "guest_nights_foreign": ("resor", 3),
    "kpi_rent_index": ("hyror", 1),
    "el_contract_spot_share": ("el", 1),
    "sek_eur": ("kronan", 0),
    "sek_usd": ("kronan", 0),
}
# Run 3 wave 1 series excluded before any test (hypotes.md section 1, "Uteslutna i förväg").
EXCLUDED = (
    "guest_nights_total", "guest_nights_hotel", "easter_sunday_in_month", "rent_negotiated",
    "prospera_mm_5y_mean", "prospera_mm_5y_p25", "prospera_mm_5y_p75", "el_contract_hourly_share",
    "el_contract_fixed_share", "el_contract_default_share", "el_grid_price_flat", "el_grid_price_house",
    "el_grid_price_house_heat", "el_grid_price_house_heat_unw", "ei_grid_fee_flat", "ei_grid_fee_house",
    "ei_grid_fee_house_heat", "ei_grid_fee_raise_share", "kpif_flash_yy", "kpif_flash_mm", "kpif_xe_flash_yy",
    "kpif_xe_flash_mm", "kpif_flash_err_yy", "kpif_flash_err_mm", "kpif_xe_flash_err_yy",
)
STALE_EXTRA = 2  # x missing if t - p* > normal lag + 2 months
BREAKS = {"el_contract_spot_share": pd.Period("2023-02", "M")}  # first period after the break
START = "2015-01"  # first target month; the correction is inactive before 2017-02 (24 rows)
MIN_ACTIVE = 100  # of the 117 primary target months
BH_Q = 0.10
MAX_SERIES = 3
PERIODS = {"primary 2017-02..2026-10": PRIMARY, "2015-01..2026-10": ("2015-01", "2026-10"),
           "2024-01..2026-10 (used, report only)": ("2024-01", "2026-10")}
PROJECT_VARIANTS_BEFORE = 51  # before run 3 (docs/auto3/v2/hypotes.md)
VARIANTS = {"v2_r_corr": "R", "v2_a_corr": "A"}  # in this order: project variants 52, 53
SHADOW_NAME = "k2_avg_ridge_l_shadow"  # K2b-corrected shadow version of k2_avg_ridge_l in the global universe
BASE_NAMES = {"R": SHADOW_NAME, "A": "avg_5050"}
# Base reproduction (hypotes.md section 6 point 7): MAE 2015-02..2026-10, n = 141
BASE_CHECK = {"R": 0.200, "A": 0.217}
GLOBAL_BLOCK, GLOBAL_B, SENS_BLOCKS = 3.0, 9999, (1, 6, 12)

# Mechanical outcome of the selection rule on the primary screen (frozen after the one run, like
# k12_global.J3_COMBO_KEYS), so k12_global can rebuild the variants without rerunning the screen.
# test_v2_screen checks that choose() on the screen still gives these.
V2_CHOSEN: dict[str, list[str]] | None = {"R": ["kpif_air_transport_index"], "A": ["kpif_air_transport_index"]}


# ====================================================================== features


def latest_period(s: pd.Series, t: pd.Period) -> pd.Period | None:
    s = s.loc[:t].dropna()
    return None if s.empty else s.index.max()


def x_value(key: str, unit: str, known: pd.Series, t: pd.Period) -> float:
    """x(t) from the values known at deadline(t): J3's transform plus the stale and break rules."""
    p = latest_period(known, t)
    if p is None:
        return np.nan
    if (t - p).n > CANDIDATES[key][1] + STALE_EXTRA:
        return np.nan
    b = BREAKS.get(key)
    if b is not None and (p == b or p - 12 == b):
        return np.nan
    return transform(known, key, unit, t)


def features(table: pd.DataFrame, months: pd.PeriodIndex, keys: list[str] | None = None) -> tuple[dict, pd.DataFrame]:
    """x per candidate and target month (NaN before START), plus p*(t) per candidate for the leakage check."""
    from kpif_nowcast.catalog import by_key

    specs = by_key()
    xs, ps = {}, {}
    start = pd.Period(START, "M")
    for key in keys or list(CANDIDATES):
        sub = table[table["series"] == key]
        xv, pv = {}, {}
        for t in months:
            if t < start:
                xv[t], pv[t] = np.nan, None
                continue
            known = obs.as_of(key, deadline(t), sub)
            xv[t] = x_value(key, specs[key].unit, known, t)
            pv[t] = latest_period(known, t)
        xs[key] = pd.Series(xv, dtype=float)
        ps[key] = pd.Series(pv, dtype=object)
    return xs, pd.DataFrame(ps)


# ====================================================================== bases


def _inputs() -> dict:
    from kpif_nowcast.k12_global import _inputs as k12_inputs

    return k12_inputs()


def base_a(inp: dict | None = None) -> pd.DataFrame:
    """avg_5050 = j1_comb_equal, as in k0_screen.fifty_fifty_frame (same panel, inputs passed in)."""
    from kpif_nowcast.j1_hybrid import j1_forecast
    from kpif_nowcast.k12_global import _panel

    if inp is None:
        from kpif_nowcast.k0_screen import fifty_fifty_frame

        return fifty_fifty_frame()
    panel = _panel(inp)
    return pd.DataFrame({"base": j1_forecast(panel, "j1_comb_equal"), "actual": panel["actual"]})


def base_r(inp: dict) -> pd.DataFrame:
    """k2_avg_ridge_l exactly as the shadow forecast computes it (shadow.SHADOW_MODELS, K2b flash dates)."""
    from kpif_nowcast.shadow import SHADOW_MODELS, Inputs

    fc = SHADOW_MODELS["k2_avg_ridge_l"].fn(Inputs(inp["kpif"], inp["comps"], inp["feats"], inp["rb_fc"], inp["obs"]))
    actual = inp["kpif"]["yy_official"]
    return pd.DataFrame({"base": fc["yy_hat"], "actual": actual.reindex(fc.index)})


def _cached_base_r(inp: dict, refresh: bool) -> pd.DataFrame:
    from kpif_nowcast.k12_global import COMMON_MODULES, _read_cache, _source_hash

    key = _source_hash(["shadow", "k2_ml", "k2b_review", "j1_hybrid", "j2_el", "j3_screen", "publication",
                        *COMMON_MODULES])
    path, meta = CACHE / "base_r.csv", CACHE / "base_r.json"
    if not refresh and path.exists() and meta.exists() and json.loads(meta.read_text())["key"] == key:
        return _read_cache(path)
    f = base_r(inp)
    CACHE.mkdir(parents=True, exist_ok=True)
    f.to_csv(path)
    meta.write_text(json.dumps({"key": key}), encoding="utf-8")
    return f


def restrict(f: pd.DataFrame) -> pd.DataFrame:
    """Target months from START on (training rows start at 2015-01)."""
    f = f.loc[pd.Period(START, "M"):].copy()
    f.index = pd.PeriodIndex(f.index, freq="M")
    return f


# ====================================================================== screen and selection


def screen(f: pd.DataFrame, xs: dict, revised: dict) -> tuple[dict, dict]:
    """Per candidate: corrected forecast, and score tables per period."""
    preds = {k: correct(f["base"], f["actual"], xs[k].reindex(f.index), h1_usable(f.index)) for k in xs}
    tabs = {lab: score_table(f, preds, s, e, 1, revised) for lab, (s, e) in PERIODS.items()}
    return preds, tabs


def coverage(xs: dict) -> pd.DataFrame:
    """Minimum-observation rule: x defined from target 2015-01 and in >= MIN_ACTIVE primary months."""
    prim = pd.period_range(*PRIMARY, freq="M")
    rows = {}
    for k, x in xs.items():
        first = x.dropna().index.min() if x.notna().any() else None
        n = int(x.reindex(prim).notna().sum())
        rows[k] = {"first": str(first), "n_primary": n,
                   "ok": first is not None and first <= pd.Period(START, "M") and n >= MIN_ACTIVE}
    return pd.DataFrame(rows).T


def choose(prim: pd.DataFrame, eligible: set[str] | None = None, k: int = MAX_SERIES,
           q: float = BH_Q) -> tuple[list[str], str]:
    """Preregistered rule (hypotes.md section 3): BH survivors by raw p, then the rest by raw p; only negative
    MAE difference (raw one-sided p < 0.5); at most one per source group; at most three."""
    prim = prim if eligible is None else prim.loc[[i for i in prim.index if i in eligible]]
    surv = prim["bh_q"].astype(float) < q
    order = list(prim[surv].sort_values("p1").index) + list(prim[~surv].sort_values("p1").index)
    chosen, groups = [], set()
    for key in order:
        if not (float(prim.loc[key, "diff"]) < 0 and float(prim.loc[key, "p1"]) < 0.5):
            continue
        g = CANDIDATES[key][0]
        if g in groups:
            continue
        chosen.append(key)
        groups.add(g)
        if len(chosen) == k:
            break
    if not chosen:
        return [], "ingen kandidat"
    n_surv = int((prim.loc[chosen, "bh_q"].astype(float) < q).sum())
    if n_surv == len(chosen):
        tag = "alla överlevde BH"
    elif n_surv == 0:
        tag = "ingen överlevde BH"
    else:
        tag = f"{n_surv} av {len(chosen)} överlevde BH"
    return chosen, tag


def variant_numbers(run: list[str]) -> dict[str, int]:
    """Project variant number of each variant actually run (52, 53 in preregistered order)."""
    return {v: PROJECT_VARIANTS_BEFORE + i + 1 for i, v in enumerate([v for v in VARIANTS if v in run])}


# ====================================================================== leakage checks


def check_known_at_deadline(ps: pd.DataFrame, table: pd.DataFrame) -> pd.DataFrame:
    """Check 1-2: p*(t) = t - lag for every candidate and target month 2015-01..2026-10, and the used period's
    known_from <= deadline(t). Deviations are listed; a deviation not explained by a documented late release
    (publication.LATE_RELEASES) is 'unknown' and stops the test."""
    from kpif_nowcast.publication import release_dates

    rows = []
    months = pd.period_range(START, PRIMARY[1], freq="M")
    for key, (_, lag) in CANDIDATES.items():
        sub = table[table["series"] == key].copy()
        sub["period"] = pd.PeriodIndex(sub["period"], freq="M")
        kf = sub.groupby("period")["known_from"].min()
        late = release_dates(key)
        for t in months:
            p = ps.loc[t, key]
            d = deadline(t)
            if p is None or (isinstance(p, float) and np.isnan(p)):
                rows.append({"series": key, "target": str(t), "p_star": None, "expected": str(t - lag),
                             "kind": "unknown", "why": "no value known"})
                continue
            if kf.get(p, pd.Timestamp.max) > d:
                rows.append({"series": key, "target": str(t), "p_star": str(p), "expected": str(t - lag),
                             "kind": "unknown", "why": "used period known after the deadline"})
            if p != t - lag:
                exp = t - lag
                kind = "late release" if exp in late and late[exp] > d else "unknown"
                rows.append({"series": key, "target": str(t), "p_star": str(p), "expected": str(exp),
                             "kind": kind, "why": f"documented release {late[exp].date()}" if exp in late else ""})
    return pd.DataFrame(rows, columns=["series", "target", "p_star", "expected", "kind", "why"])


def deadline_margin(ps: pd.DataFrame, table: pd.DataFrame) -> pd.DataFrame:
    """Check 3: smallest margin in days between known_from of p* and deadline(t), and of the next period
    (which must not be known yet), per candidate, over target months 2015-01..2026-10."""
    months = pd.period_range(START, PRIMARY[1], freq="M")
    out = {}
    for key, (_, lag) in CANDIDATES.items():
        sub = table[table["series"] == key].copy()
        sub["period"] = pd.PeriodIndex(sub["period"], freq="M")
        kf = sub.groupby("period")["known_from"].min()
        m_used, m_next = [], []
        for t in months:
            p = ps.loc[t, key]
            if p is None:
                continue
            d = deadline(t)
            m_used.append((d - kf[p]).days)
            nxt = p + 1
            if nxt <= t and nxt in kf.index:
                m_next.append((kf[nxt] - d).days)
        out[key] = {"min_days_used_before_deadline": min(m_used),
                    "min_days_next_after_deadline": min(m_next) if m_next else np.nan}
    return pd.DataFrame(out).T


def base_reproduction(fr: pd.DataFrame, fa: pd.DataFrame) -> dict:
    """Check 7: MAE 2015-02..2026-10 (n = 141) of both bases."""
    out = {}
    for b, f in (("R", fr), ("A", fa)):
        s = f.loc[pd.Period("2015-02", "M"): pd.Period("2026-10", "M")].dropna()
        mae = float((s["base"] - s["actual"]).abs().mean())
        out[b] = {"MAE": mae, "n": len(s), "expected": BASE_CHECK[b], "ok": round(mae, 3) == BASE_CHECK[b] and len(s) == 141}
    return out


def k12_table() -> dict[str, str]:
    """K12's per-model MAE (3 decimals, Swedish comma) from docs/auto2/k12/resultat.md."""
    txt = (ROOT / "docs" / "auto2" / "k12" / "resultat.md").read_text(encoding="utf-8")
    sec = txt.split("## Per modell")[1].split("\n## ")[0]
    return {m: v for m, v in re.findall(r"^\| `([^`]+)` \| [^|]+ \| ([0-9,]+) \|", sec, flags=re.M)}


# ====================================================================== global test (K12 machinery)


def k12_universe(preds: pd.DataFrame, extra_cols: list[str]) -> tuple[pd.DataFrame, list[str], dict, list[str]]:
    """K12's U1 on its common sample plus the given extra columns. Returns (errors, old U1, alias, dropped)."""
    from kpif_nowcast.k12_global import BENCHMARKS, common_sample, dedupe

    family_of = preds.attrs.get("family_of", {})
    candidates = [c for c in preds.columns if c != "actual"]
    err, _, dropped = common_sample(preds, candidates)
    err, alias = dedupe(err, prefer=(*BENCHMARKS, SHADOW_NAME))
    phase = {c for c in err.columns if family_of.get(c) == "phase"}
    old = [c for c in err.columns if c not in phase and c not in extra_cols]
    return err, old, alias, dropped


def analyse_one(err: pd.DataFrame, cols: list[str], bench: str, B: int) -> dict:
    from kpif_nowcast.k12_global import SEED, analyse

    return analyse(err[cols], bench, GLOBAL_BLOCK, B, SEED)


def global_tests(err: pd.DataFrame, cols: list[str], benches: list[str], B: int) -> dict:
    from kpif_nowcast.k12_global import SEED, analyse

    res = {(b, GLOBAL_BLOCK): analyse(err[cols], b, GLOBAL_BLOCK, B, SEED) for b in benches}
    for bl in SENS_BLOCKS:
        for b in benches:
            res[(b, float(bl))] = analyse(err[cols], b, float(bl), min(B, 4999), SEED + bl)
    return res


# ====================================================================== report helpers


def _f(x, d: int = 3) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    return f"{x:.{d}f}".replace(".", ",")


def _md_screen(t: pd.DataFrame, cov: pd.DataFrame) -> str:
    lines = ["| Serie | Grupp | MAE | diff mot bas | rå p (ensidig) | BH-q | n | aktiva | revised | täckning ok |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in t.iterrows():
        lines.append(f"| `{k}` | {CANDIDATES[k][0]} | {_f(float(r['MAE']))} | {_f(float(r['diff']), 4)} | "
                     f"{_f(float(r['p1']))} | {_f(float(r['bh_q']))} | {int(r['n'])} | {int(r['n_active'])} | "
                     f"{'ja' if r['revised'] else 'nej'} | {'ja' if cov.loc[k, 'ok'] else 'NEJ'} |")
    return "\n".join(lines)


def evaluate(f: pd.DataFrame, pred: pd.Series, start: str, end: str) -> dict:
    from kpif_nowcast.k0_screen import evaluate as k0_evaluate

    return k0_evaluate(f, pred, start, end)


# ====================================================================== main


def load_pre_run3(d: Path | None) -> dict | None:
    """Reference forecasts from a checkout of main before run 3 (129bbb0) on the same data: the shadow
    k2_avg_ridge_l (shadow_ridge_l.csv) and k12_global.collect_all() (k12_all.csv)."""
    if d is None:
        return None
    from kpif_nowcast.k12_global import _read_cache

    return {"shadow": _read_cache(Path(d) / "shadow_ridge_l.csv")["yy_hat"], "k12": _read_cache(Path(d) / "k12_all.csv")}


def max_abs_diff(a: pd.Series, b: pd.Series) -> float:
    a, b = a.align(b, join="outer")
    both = a.notna() & b.notna()
    if (a.notna() != b.notna()).any():
        return float("inf")
    return float((a[both] - b[both]).abs().max()) if both.any() else 0.0


def run(B: int = GLOBAL_B, refresh: bool = False, log: bool = True, pre_run3: Path | None = None,
        checks_only: bool = False) -> dict:
    warnings.filterwarnings("ignore")
    from kpif_nowcast.catalog import by_key
    from kpif_nowcast.evaluation import git_sha, log_run
    from kpif_nowcast.j2_el import holm
    from kpif_nowcast.k12_global import FAMILIES, collect_all

    specs = by_key()
    revised = {k: specs[k].revised for k in CANDIDATES}
    inp = _inputs()
    table = inp["obs"]
    pre = load_pre_run3(pre_run3)
    L: list[str] = [f"# V2 rådata (genererad av `python -m kpif_nowcast.v2_screen`, kod @ {git_sha()})", ""]

    # --- bases and reproduction checks (7)
    fa = restrict(base_a(inp))
    fr = restrict(_cached_base_r(inp, refresh))
    rep = base_reproduction(fr, fa)
    L.append("## Kontroll 7: baserna reproduceras (MAE 2015-02..2026-10)\n")
    for b, r in rep.items():
        L.append(f"- Bas {b} (`{BASE_NAMES[b]}`): MAE {r['MAE']:.4f}, n = {r['n']}, förregistrerat {r['expected']:.3f} → "
                 f"{'OK' if r['ok'] else 'AVVIKER'}")
    if pre is not None:
        d_r = max_abs_diff(fr["base"], pre["shadow"].loc[fr.index.min():])
        rep["R"]["pre_run3_maxdiff"] = d_r
        L.append(f"- Bas R mot skuggan på main före körning 3 (129bbb0, samma data): största absoluta skillnad "
                 f"{d_r:.2e} → {'identisk' if d_r < 1e-10 else 'AVVIKER'}")
        if not rep["R"]["ok"] and d_r < 1e-10:
            rep["R"]["ok"] = True
            L.append("  - Avvikelsen från det förregistrerade 0,200 kommer inte från körning 3: skuggan är identisk med "
                     "main före körning 3. Den kommer från ändringar på main efter K2b:s 0,200 (K11:s publiceringskalender "
                     "och laggar) och möjligen dagens dataårgång.")
    L.append("")
    if not all(r["ok"] for r in rep.values()):
        raise SystemExit("Base reproduction failed (check 7): " + json.dumps(rep))

    # --- check 8: registered variants unchanged (before any screening)
    old_fams = [f for f in FAMILIES if f != "v2"]
    preds_old, info = collect_all(refresh=False, only=old_fams)
    err_old, old_cols0, alias0, _ = k12_universe(preds_old, [])
    mae0 = err_old.abs().mean()
    ref = k12_table()
    missing = [m for m in ref if alias0.get(m, m) not in err_old.columns]
    mism = {m: (ref[m], _f(float(mae0[alias0.get(m, m)]))) for m in ref
            if m not in missing and _f(float(mae0[alias0.get(m, m)])) != ref[m]}
    L.append("## Kontroll 8: redan registrerade varianter oförändrade\n")
    L.append(f"- Mot K12:s per-modelltabell (docs/auto2/k12/resultat.md, {len(ref)} modeller): "
             f"{len(ref) - len(mism) - len(missing)} identiska på 3 decimaler. Avvikelser (K12 → nu): "
             + (", ".join(f"`{m}` {a} → {b}" for m, (a, b) in mism.items()) or "inga")
             + f". Saknas: {missing or 'inga'}. n = {len(err_old)}.")
    L.append(f"- Familjer: {info}.")
    pre_ok = None
    if pre is not None:
        old = [c for c in pre["k12"].columns if c in preds_old.columns]
        diffs = {c: max_abs_diff(preds_old[c], pre["k12"][c]) for c in old}
        bad = {c: d for c, d in diffs.items() if not d < 1e-10}
        gone = [c for c in pre["k12"].columns if c not in preds_old.columns]
        pre_ok = not bad and not gone
        L.append(f"- Mot main före körning 3 (129bbb0, samma data, alla {len(old)} kolumner i k12_global.collect_all, "
                 f"hela tidsserien): största absoluta skillnad {max(diffs.values()):.2e}; avvikande: {bad or 'inga'}; "
                 f"saknas: {gone or 'inga'} → {'identiska' if pre_ok else 'AVVIKER'}.")
        if mism and pre_ok:
            L.append("  - Avvikelserna mot K12:s tabell kommer alltså inte från körning 3. De kommer från main efter K12:s "
                     "körning (K11:s publiceringskalender och laggar, mergad efter K12; K11 rapporterade +0,001 för K2) "
                     "och kan delvis vara dagens dataårgång. Vilket av de två som ger vad har inte separerats.")
    old_res = {b: analyse_one(err_old, old_cols0, b, B) for b in ("rb_updated", "avg_5050")}
    L.append("- K12:s U1 utan körning 3 (block 3, B och seed som K12): SPA consistent "
             + ", ".join(f"{b} {_f(r['spa']['p']['consistent'])}" for b, r in old_res.items())
             + f" (K12:s fil: rb_updated 0,035, avg_5050 0,025); {len(old_cols0)} serier.\n")
    if missing or (mism and not pre_ok):
        raise SystemExit(f"K12 reproduction failed (check 8): {mism} {missing}")

    # --- features and leakage checks (1-3)
    months = pd.period_range(START, max(fr.index.max(), fa.index.max()), freq="M")
    xs, ps = features(table, months)
    dev = check_known_at_deadline(ps, table)
    unknown = dev[dev["kind"] == "unknown"]
    L.append("## Kontroll 1–2: period känd vid deadline\n")
    L.append(f"Avvikelser från tabellen i avsnitt 1: {len(dev)} (varav okända: {len(unknown)}).\n")
    if len(dev):
        L.append(dev.to_markdown(index=False) + "\n")
    p2 = ps.loc[pd.Period("2024-01", "M"), "el_contract_spot_share"]
    L.append(f"- Kontroll 2: p* för `el_contract_spot_share` vid deadline 2024-01 = {p2} (väntat 2023-04).\n")
    if len(unknown) or str(p2) != "2023-04":
        raise SystemExit("Leakage check 1/2 failed:\n" + unknown.to_string())
    marg = deadline_margin(ps, table)
    L.append("## Kontroll 3: marginal till deadline (dagar)\n")
    L.append(marg.to_markdown() + "\n")
    cov = coverage(xs)
    el = xs["el_contract_spot_share"]
    stale = [str(t) for t in pd.period_range("2023-08", "2024-07", freq="M") if np.isnan(el.get(t, np.nan))]
    L.append("## Täckning (minsta antal observationer)\n")
    L.append(cov.to_markdown() + "\n")
    L.append(f"- Inaktuella-regeln: x saknas för elavtal i {len(stale)} av 12 målmånader 2023-08..2024-07; "
             f"brottregeln: x(2023-03) = {el.get(pd.Period('2023-03', 'M'))}.\n")
    missing_el = [str(t) for t in pd.period_range(*PRIMARY, freq="M") if np.isnan(el.get(t, np.nan))]
    L.append(f"- Elavtal, målmånader utan x i primärperioden: {', '.join(missing_el)}.\n")

    if checks_only:  # protocol order: checks 1-3 and 7-8, then pytest, then the screen
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "checks_raw.md").write_text("\n".join(L), encoding="utf-8")
        print("\n".join(L))
        return {"checks": True}

    # --- screening, both bases
    frames = {"R": fr, "A": fa}
    screens, chosen = {}, {}
    for b, f in frames.items():
        _, tabs = screen(f, xs, revised)
        screens[b] = tabs
        eligible = set(cov.index[cov["ok"].astype(bool)])
        chosen[b] = choose(tabs[list(PERIODS)[0]], eligible)
        for lab, t in tabs.items():
            L.append(f"## Screening bas {b} (`{BASE_NAMES[b]}`), {lab} (bas-MAE {t.attrs['base_mae']:.4f}, "
                     f"n = {t.attrs['n']})\n")
            L.append(_md_screen(t, cov) + "\n")
        L.append(f"**Valda för bas {b} ({chosen[b][1]}):** {', '.join(chosen[b][0]) or 'inga'}\n")
    if V2_CHOSEN is not None:
        assert {b: c for b, (c, _) in chosen.items()} == V2_CHOSEN, "selection differs from the frozen V2_CHOSEN"

    # --- the joint test, once
    run_v = [v for v, b in VARIANTS.items() if chosen[b][0]]
    nums = variant_numbers(run_v)
    total = PROJECT_VARIANTS_BEFORE + len(run_v)
    preds_v = {v: combined_h1(frames[VARIANTS[v]], xs, chosen[VARIANTS[v]][0]) for v in run_v}
    res = {v: {lab: evaluate(frames[VARIANTS[v]], preds_v[v], *per) for lab, per in PERIODS.items()} for v in run_v}
    holm_p = holm({v: res[v][list(PERIODS)[0]]["p1"] for v in run_v}) if run_v else {}
    rb = collect_refs_rb(inp)
    vs_rb = {}
    for v in run_v:
        f_rb = pd.DataFrame({"base": rb.reindex(frames[VARIANTS[v]].index), "actual": frames[VARIANTS[v]]["actual"]})
        vs_rb[v] = {lab: evaluate(f_rb, preds_v[v], *per) for lab, per in PERIODS.items()}
    L.append(f"## Gemensamt test (projektet totalt {total} varianter)\n")
    L.append("| Variant | Bas | Serier | Period | MAE | bas-MAE | diff | rå p | Holm p | n | aktiva | "
             "MAE rb_updated | p mot rb_updated |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    log_rows = []
    for v in run_v:
        for lab, r in res[v].items():
            hp = holm_p[v] if lab == list(PERIODS)[0] else np.nan
            L.append(f"| `{v}` (nr {nums[v]}) | {BASE_NAMES[VARIANTS[v]]} | {', '.join(chosen[VARIANTS[v]][0])} | {lab} | "
                     f"{_f(r['MAE'], 4)} | {_f(r['base_MAE'], 4)} | {_f(r['diff'], 4)} | {_f(r['p1'])} | {_f(hp)} | "
                     f"{r['n']} | {r['n_active']} | {_f(vs_rb[v][lab]['base_MAE'], 4)} | {_f(vs_rb[v][lab]['p1'])} |")
            log_rows.append({"variant": v, "period": lab, "n": r["n"], "MAE": round(r["MAE"], 4),
                             "dm_p_vs_rb_updated": round(vs_rb[v][lab]["p1"], 4)})
    L.append("")
    for b in VARIANTS.values():
        if not chosen[b][0]:
            L.append(f"- Bas {b}: ingen kandidat, ingen variant körd.\n")

    # --- global test: K12's U1 + run 3's variants + the shadow ribbon
    preds = preds_old.copy()
    for v in run_v:
        preds[v] = preds_v[v].reindex(preds.index)
    preds[SHADOW_NAME] = fr["base"].reindex(preds.index)
    preds.attrs["family_of"] = {**preds_old.attrs.get("family_of", {}), **{v: "v2" for v in run_v}, SHADOW_NAME: "v2"}
    extra = [*run_v, SHADOW_NAME]
    err, old_cols, alias, dropped = k12_universe(preds, extra)
    assert err.index.equals(err_old.index) and old_cols == old_cols0, "run 3 columns changed K12's common sample"
    mae = err.abs().mean()
    cols = [*old_cols, *extra]
    benches = ["rb_updated", "avg_5050", SHADOW_NAME]
    gres = global_tests(err, cols, benches, B)
    L.append(f"## Globalt test: U1 + körning 3 ({len(cols)} serier, n = {len(err)})\n")
    L.append("| Ribba | block | n modeller | SPA lower | SPA consistent | SPA upper | White RC | E[max förb.] H0 | 90 % | "
             "observerat max | StepM 10 % väljer |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for (b, bl), r in gres.items():
        p = r["spa"]["p"]
        sm = [m for m, rj in zip(r["models"], r["spa"]["stepm"][0.10]) if rj]
        L.append(f"| {b} | {bl:g} | {len(r['models'])} | {_f(p['lower'])} | {_f(p['consistent'])} | {_f(p['upper'])} | "
                 f"{_f(p['white_rc'])} | {_f(r['sb']['mean'])} | {_f(r['sb']['q90'])} | {_f(r['sb']['observed_max'])} | "
                 f"{', '.join(f'`{m}`' for m in sm) or 'ingen'} |")
    L.append("")
    adj = {}
    for v in run_v:
        own = BASE_NAMES[VARIANTS[v]]
        adj[v] = {bl: float(gres[(own, bl)]["spa"]["adj_p"][gres[(own, bl)]["models"].index(v)])
                  for bl in (GLOBAL_BLOCK, *map(float, SENS_BLOCKS))}
    L.append("## Per variant: kriterierna (avsnitt 5)\n")
    L.append("| Variant | Holm p | justerat p mot egen bas (block 3) | block 1 | block 6 | block 12 | MAE 2024–26 | "
             "bas-MAE 2024–26 | MCS p T_max | MCS p T_R | klarade urvalsskärmen |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    verdict = {}
    for v in run_v:
        own = BASE_NAMES[VARIANTS[v]]
        used = res[v][list(PERIODS)[2]]
        c1, c2, c3 = holm_p[v] < 0.10, adj[v][GLOBAL_BLOCK] < 0.10, used["MAE"] <= used["base_MAE"]
        verdict[v] = {"holm": c1, "global": c2, "used": c3, "passed": bool(c1 and c2 and c3)}
        r3 = gres[(own, GLOBAL_BLOCK)]
        L.append(f"| `{v}` | {_f(holm_p[v])} | {_f(adj[v][GLOBAL_BLOCK])} | {_f(adj[v][1.0])} | {_f(adj[v][6.0])} | "
                 f"{_f(adj[v][12.0])} | {_f(used['MAE'], 4)} | {_f(used['base_MAE'], 4)} | {_f(r3['mcs_max'][v])} | "
                 f"{_f(r3['mcs_r'][v])} | {'ja' if verdict[v]['passed'] else 'nej'} |")
    L.append("")
    L.append("## Per modell (U1 + körning 3, block 3)\n")
    L.append("| Modell | MAE | justerat p mot rb_updated | mot 50/50 | mot skugga | MCS p (T_max) | MCS p (T_R) |")
    L.append("|---|---|---|---|---|---|---|")
    r_rb, r_50, r_sh = (gres[(b, GLOBAL_BLOCK)] for b in benches)

    def adjp(r, m):
        return float(r["spa"]["adj_p"][r["models"].index(m)]) if m in r["models"] else float("nan")

    for m in mae[cols].sort_values().index:
        L.append(f"| `{m}` | {_f(float(mae[m]))} | {_f(adjp(r_rb, m))} | {_f(adjp(r_50, m))} | {_f(adjp(r_sh, m))} | "
                 f"{_f(r_rb['mcs_max'][m])} | {_f(r_rb['mcs_r'][m])} |")
    L.append("")
    if alias:
        L.append("Identiska serier (räknas en gång): " + ", ".join(f"`{k}` = `{v}`" for k, v in alias.items()) + ".\n")
    if dropped:
        L.append("Utan full täckning (inte med): " + ", ".join(f"`{m}`" for m in dropped) + ".\n")

    if log:
        for b, tabs in screens.items():
            for lab, t in tabs.items():
                for k, row in t.iterrows():
                    log_rows.append({"variant": f"v2s_{b}_{k}", "period": lab, "n": int(row["n"]),
                                     "MAE": round(float(row["MAE"]), 4), "dm_p_vs_rb_updated": round(float(row["p1"]), 4)})
        path = log_run("v2_screen", log_rows)
        L.append(f"Körlogg: `{path.name}` (p för screeningraderna är mot den egna basen).\n")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results_raw.md").write_text("\n".join(L), encoding="utf-8")
    CACHE.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(preds_v).to_csv(CACHE / "variants.csv")
    for b, tabs in screens.items():
        tabs[list(PERIODS)[0]].to_csv(CACHE / f"screen_{b}.csv")
    print("\n".join(L))
    return {"chosen": chosen, "res": res, "holm": holm_p, "adj": adj, "verdict": verdict, "gres": gres,
            "screens": screens, "total": total, "nums": nums}


def collect_refs_rb(inp: dict) -> pd.Series:
    from kpif_nowcast.k12_global import _panel

    return _panel(inp)["rb_updated"]


def k12_forecasts(inp: dict | None = None) -> pd.DataFrame:
    """Run 3's h=1 variants (frozen selection V2_CHOSEN) plus the K2b-corrected shadow k2_avg_ridge_l, for
    k12_global's universe."""
    if V2_CHOSEN is None:
        raise RuntimeError("V2_CHOSEN not frozen yet: run python -m kpif_nowcast.v2_screen first")
    inp = inp or _inputs()
    fa = restrict(base_a(inp))
    fr = restrict(_cached_base_r(inp, False))
    frames = {"R": fr, "A": fa}
    xs, _ = features(inp["obs"], pd.period_range(START, max(fr.index.max(), fa.index.max()), freq="M"), sorted({k for v in V2_CHOSEN.values() for k in v}))
    out = {v: combined_h1(frames[b], xs, V2_CHOSEN[b]) for v, b in VARIANTS.items() if V2_CHOSEN.get(b)}
    out[SHADOW_NAME] = fr["base"]
    return pd.DataFrame(out)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=GLOBAL_B)
    ap.add_argument("--refresh", action="store_true", help="recompute the cached shadow base R")
    ap.add_argument("--no-log", action="store_true")
    ap.add_argument("--pre-run3", type=Path, default=None,
                    help="dir with shadow_ridge_l.csv and k12_all.csv from a checkout of main before run 3")
    ap.add_argument("--checks-only", action="store_true", help="run the leakage/reproduction checks, no screen")
    a = ap.parse_args(argv)
    run(a.B, a.refresh, not a.no_log, a.pre_run3, a.checks_only)


if __name__ == "__main__":
    main()
