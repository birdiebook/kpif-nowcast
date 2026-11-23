"""K12: global test over every h=1 model variant tried on 2015-2026 (data snooping across tracks).

Every track ran Holm within its own family. The best variant overall (K2 `k2_avg_ridge_l`) is "best of N",
so its edge over the benchmark is inflated by the search. This module collects the monthly forecast
errors of all h=1 variants on one common sample and runs tests that account for the whole search:

- Hansen's SPA test (2005), studentized, with lower / consistent / upper recentring; the upper version
  without studentization is White's Reality Check (2000). H0: no model beats the benchmark (MAE loss).
- Romano-Wolf StepM (2005) with studentized max statistic: which models beat the benchmark with
  family-wise error control over the whole universe; plus single-step max-t adjusted p per model.
- Model Confidence Set (Hansen, Lunde, Nason 2011), T_max and T_R statistics, absolute-error loss.
- Selection bias: E[max_k mean improvement] when every model is as good as the benchmark, from the
  stationary bootstrap of the recentred loss differences (keeps their correlation).

The bootstrap is Politis-Romano's stationary bootstrap. The mean block length is the median of the
Politis-White (2004, corrected 2009) estimates over the loss differences, reported with sensitivities.

No model is changed. Forecasts are rebuilt by calling each track's own code (collectors below) and
cached under outputs/k12/. New tracks are picked up automatically if their module defines
`k12_forecasts() -> DataFrame` (monthly PeriodIndex, one column per h=1 KPIF y/y forecast), or if a
CSV with a `month` column and one column per variant is put in outputs/k12/extra/.

Run: python -m kpif_nowcast.k12_global [--refresh] [--B 9999]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import pkgutil
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "outputs" / "k12"
EXTRA = CACHE / "extra"
OUT = ROOT / "docs" / "auto2" / "k12"
PERIOD = ("2015-01", "2026-10")
USED = ("2024-01", "2026-10")
BENCHMARKS = ("rb_updated", "avg_5050")
ALPHA = 0.10
SEED = 20261123

# Feature set L of K2 as frozen at 415ba6f (copied from K2b's review, origin/auto2/k2b 866e1af). On a main
# that has K0 merged but not K2b, catalog.CATALOG has 72 monthly series and k2_ml would silently use them.
K2_CATALOG_KEYS = (
    "brent_sek", "aku_unemp_nsa", "aku_unemp_sa", "gdp_ind_yy", "kix", "policy_rate", "ki_services",
    "wage_private_nonmanual", "wage_private_manual_hourly", "wage_municipal_yy", "labour_cost_salaried_yy",
    "labour_cost_workers_yy", "aku_employed", "hh_consumption_yy", "retail_volume_yy", "hh_infl_exp_median",
    "hh_infl_perceived_median", "hh_price_exp_net", "ea_flash_total", "ea_flash_energy", "ea_flash_food",
    "ea_flash_goods", "ea_flash_services", "ea_hicp_total", "fao_food_idx", "fao_cereals", "fao_dairy",
    "gas_eu_usd", "wheat_usd", "gscpi", "freight_ppi_deepsea", "jobads_total", "mortgage_rate_new",
    "hh_lending_growth", "nfc_lending_growth", "nier_barometer", "nier_conf_services", "nier_conf_trade",
    "nier_conf_households", "bankruptcies", "ipi_yy", "service_prod_idx", "industry_orders_yy",
)
# Series the combination variants were built on, as chosen by each screen (results_raw.md of J3 and K0).
J3_COMBO_KEYS = ["ea_flash_goods", "ea_flash_food", "ki_services"]
K0_COMBO_KEYS = ["ppi_hmpi_food", "rapeseed_oil_usd", "swestr"]

# Which track each variant belongs to (for the report). Phase 2-4 models are "fas2-4".
TRACK_PREFIX = [("j1_", "J1"), ("j2_", "J2"), ("j3_", "J3"), ("j4_", "J4"), ("k0_", "K0"), ("k2_", "K2"),
                ("k7_", "K7"), ("k8_", "K8"), ("v2_", "V2")]
# K2b-corrected shadow version of k2_avg_ridge_l: the ribbon of run 3's V2 (not a new variant)
SHADOW_K2 = "k2_avg_ridge_l_shadow"
REFERENCES = {"rb_updated": "referens", "avg_5050": "referens (= j1_comb_equal)", "j2": "referens (= j2_el_dev)",
              SHADOW_K2: "referens (skugga, K2b-rättad)"}


# ====================================================================== statistics (numpy only)


def stationary_bootstrap_indices(n: int, B: int, block: float, rng: np.random.Generator) -> np.ndarray:
    """B x n index matrix of the stationary bootstrap (geometric blocks with mean length `block`, wrap-around)."""
    p = 1.0 / block
    idx = np.empty((B, n), dtype=np.int64)
    idx[:, 0] = rng.integers(0, n, B)
    new = rng.random((B, n)) < p
    starts = rng.integers(0, n, (B, n))
    for t in range(1, n):
        idx[:, t] = np.where(new[:, t], starts[:, t], (idx[:, t - 1] + 1) % n)
    return idx


def politis_white_block(x: np.ndarray) -> float:
    """Optimal mean block length for the stationary bootstrap (Politis-White 2004, Patton-Politis-White 2009)."""
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    n = len(x)
    kn = max(5, int(np.ceil(np.sqrt(np.log10(n)))))
    max_lag = min(n - 1, int(np.ceil(np.sqrt(n))) + kn)
    g0 = x @ x / n
    if g0 == 0:
        return 1.0
    acov = np.array([x[k:] @ x[: n - k] / n for k in range(max_lag + 1)])
    rho = acov / g0
    crit = 2.0 * np.sqrt(np.log10(n) / n)
    m_hat = max_lag
    for m in range(max_lag - kn + 1):
        if np.all(np.abs(rho[m + 1: m + kn + 1]) < crit):
            m_hat = m
            break
    M = min(2 * m_hat, max_lag)
    if M == 0:  # no significant autocorrelation: i.i.d. bootstrap
        return 1.0
    k = np.arange(-M, M + 1)
    lam = np.clip(2 * (1 - np.abs(k) / M), 0, 1)
    R = acov[np.abs(k)]
    G = np.sum(lam * np.abs(k) * R)
    g = np.sum(lam * R)
    if g <= 0:
        return 1.0
    b = (2 * G**2 / (2 * g**2)) ** (1 / 3) * n ** (1 / 3)
    return float(np.clip(b, 1.0, np.ceil(min(3 * np.sqrt(n), n / 3))))


def _boot_means(x: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """Bootstrap means of each column of x (n x K) -> B x K."""
    B = idx.shape[0]
    out = np.empty((B, x.shape[1]))
    for b in range(B):
        out[b] = x[idx[b]].mean(axis=0)
    return out


def spa_test(loss_bench: np.ndarray, loss_models: np.ndarray, idx: np.ndarray) -> dict:
    """Hansen's SPA and White's Reality Check. d_k = L_bench - L_k (positive = model k better).

    Returns p-values (lower, consistent, upper, white_rc), the statistic and per-model t-stats, plus
    StepM (Romano-Wolf) rejections at ALPHA and 0.05 and single-step max-t adjusted p-values.
    """
    d = loss_bench[:, None] - loss_models
    n, K = d.shape
    dbar = d.mean(axis=0)
    db = _boot_means(d, idx)  # B x K
    omega = np.sqrt(n) * db.std(axis=0)  # bootstrap se of sqrt(n) * dbar
    omega = np.where(omega > 0, omega, np.inf)
    t = np.sqrt(n) * dbar / omega
    stat = max(float(t.max()), 0.0)
    thresh = -np.sqrt(2 * np.log(np.log(n)))
    mus = {"lower": np.maximum(dbar, 0.0), "consistent": dbar * (t >= thresh), "upper": dbar}
    p = {}
    for k, mu in mus.items():
        tb = np.sqrt(n) * (db - mu) / omega
        p[k] = float(np.mean(np.maximum(tb.max(axis=1), 0.0) >= stat))
    # White's Reality Check: non-studentized, upper recentring
    rc_stat = max(float(np.sqrt(n) * dbar.max()), 0.0)
    p["white_rc"] = float(np.mean(np.maximum((np.sqrt(n) * (db - dbar)).max(axis=1), 0.0) >= rc_stat))
    # single-step max-t adjusted p (upper recentring, conservative) and StepM
    tb_c = np.sqrt(n) * (db - dbar) / omega
    max_all = tb_c.max(axis=1)
    adj_p = np.array([float(np.mean(max_all >= tk)) for tk in t])
    stepm = {a: _stepm(t, tb_c, a) for a in (ALPHA, 0.05)}
    return {"p": p, "stat": stat, "t": t, "dbar": dbar, "adj_p": adj_p, "stepm": stepm, "boot_dbar": db,
            "max_t_h0": max_all}


def _stepm(t: np.ndarray, tb_c: np.ndarray, alpha: float) -> np.ndarray:
    """Romano-Wolf step-down: boolean array of models that beat the benchmark at FWER alpha."""
    rejected = np.zeros(len(t), dtype=bool)
    while True:
        active = ~rejected
        if not active.any():
            break
        c = np.quantile(tb_c[:, active].max(axis=1), 1 - alpha)
        new = active & (t > c)
        if not new.any():
            break
        rejected |= new
    return rejected


def selection_bias(spa: dict) -> dict:
    """Best-of-K under H0 (every model exactly as good as the benchmark), raw and studentized.

    Raw: max_k mean improvement in pp MAE. Studentized: max_k t_k, the scale SPA uses; a model whose
    improvement is small but very stable (e.g. a small correction on top of the benchmark) has a large t.
    """
    boot_dbar, dbar, mt = spa["boot_dbar"], spa["dbar"], spa["max_t_h0"]
    mx = (boot_dbar - dbar).max(axis=1)
    return {"mean": float(mx.mean()), "q50": float(np.quantile(mx, 0.5)), "q90": float(np.quantile(mx, 0.9)),
            "q95": float(np.quantile(mx, 0.95)), "observed_max": float(dbar.max()),
            "p": float(np.mean(mx >= dbar.max())),
            "t_mean": float(mt.mean()), "t_q90": float(np.quantile(mt, 0.9)), "t_observed": float(spa["t"].max())}


def mcs(losses: np.ndarray, idx: np.ndarray, stat: str = "max") -> np.ndarray:
    """Model Confidence Set p-values (Hansen-Lunde-Nason 2011). losses: n x K. Returns MCS p per model.

    stat "max": T_max = max_i dbar_i. / se(dbar_i.), eliminate argmax. stat "R": T_R = max_ij |dbar_ij| / se,
    eliminate argmax_i max_j t_ij. The last surviving model has p = 1.
    """
    n, K = losses.shape
    lbar = losses.mean(axis=0)
    lb = _boot_means(losses, idx)  # B x K
    alive = list(range(K))
    pvals = np.zeros(K)
    running = 0.0
    while len(alive) > 1:
        a = np.array(alive)
        if stat == "max":
            di = lbar[a] - lbar[a].mean()
            dib = lb[:, a] - lb[:, a].mean(axis=1, keepdims=True)
            se = np.sqrt(np.mean((dib - di) ** 2, axis=0))
            se = np.where(se > 0, se, np.inf)
            ti = di / se
            T = ti.max()
            Tb = ((dib - di) / se).max(axis=1)
            worst = a[int(np.argmax(ti))]
        else:
            dij = lbar[a][:, None] - lbar[a][None, :]
            dijb = lb[:, a][:, :, None] - lb[:, a][:, None, :]
            se = np.sqrt(np.mean((dijb - dij) ** 2, axis=0))
            np.fill_diagonal(se, np.inf)
            se = np.where(se > 0, se, np.inf)
            tij = dij / se
            T = np.abs(tij).max()
            Tb = (np.abs(dijb - dij) / se).reshape(len(lb), -1).max(axis=1)
            worst = a[int(np.argmax(tij.max(axis=1)))]
        p = float(np.mean(Tb >= T))
        running = max(running, p)
        pvals[worst] = running
        alive.remove(worst)
    pvals[alive[0]] = 1.0
    return pvals


# ====================================================================== collectors (no model changes)


def _inputs() -> dict:
    from kpif_nowcast.data import load_components, load_el_contracts, load_kpif, load_riksbank_forecasts
    from kpif_nowcast.features import load_features
    from kpif_nowcast.j2_el import zone_monthly_spot
    from kpif_nowcast.observations import load as load_obs

    return dict(kpif=load_kpif(), comps=load_components(), feats=load_features(), contracts=load_el_contracts(),
                se3=zone_monthly_spot("SE3"), rb_fc=load_riksbank_forecasts(), obs=load_obs())


def _panel(inp: dict) -> pd.DataFrame:
    from kpif_nowcast.j1_hybrid import build_panel

    return build_panel(inp["kpif"], inp["comps"], inp["feats"], inp["contracts"], inp["se3"], inp["rb_fc"], inp["obs"])


def collect_refs(inp: dict) -> pd.DataFrame:
    p = _panel(inp)
    return pd.DataFrame({"actual": p["actual"], "rb_updated": p["rb_updated"], "j2": p["j2"],
                         "avg_5050": 0.5 * p["rb_updated"] + 0.5 * p["j2"]})


def collect_phase(inp: dict) -> pd.DataFrame:
    """Phase 2-4 models (baselines, raw Riksbank, component models) from backtest.build_predictions."""
    from kpif_nowcast.backtest import BENCHMARK, build_predictions

    preds, actual, _ = build_predictions()
    return preds.drop(columns=[BENCHMARK], errors="ignore")


def collect_j1(inp: dict) -> pd.DataFrame:
    from kpif_nowcast.j1_hybrid import VARIANTS, j1_forecast

    panel = _panel(inp)
    return pd.DataFrame({v: j1_forecast(panel, v) for v in VARIANTS})


def collect_j2(inp: dict) -> pd.DataFrame:
    from kpif_nowcast.j2_el import VARIANTS, build_j2_features, j2_forecast

    j2f = build_j2_features(inp["feats"], inp["contracts"], inp["se3"])
    return pd.DataFrame({v: j2_forecast(inp["kpif"]["index"], inp["comps"], j2f, v)["yy_hat"] for v in VARIANTS})


def collect_j4(inp: dict) -> pd.DataFrame:
    from kpif_nowcast.data import load_cpif_detail
    from kpif_nowcast.j4_detail import VARIANTS, j4_forecast, regressors

    detail, regs = load_cpif_detail(), regressors(inp["feats"])
    return pd.DataFrame({v: j4_forecast(inp["kpif"]["index"], detail, regs, v)["yy_hat"] for v in VARIANTS})


def _combo(inp: dict, keys: list[str], base_frame: pd.DataFrame | None = None) -> pd.Series:
    from kpif_nowcast import catalog_prices  # noqa: F401  (registers K0's specs where needed)
    from kpif_nowcast.catalog import by_key
    from kpif_nowcast.j3_screen import combined_h1, run_h1

    specs = by_key()
    f1, _, xs = run_h1(inp["kpif"], inp["rb_fc"], inp["obs"], [(k, specs[k].unit) for k in keys])
    return combined_h1(f1 if base_frame is None else base_frame, xs, keys)


def collect_j3(inp: dict) -> pd.DataFrame:
    return pd.DataFrame({"j3_combo": _combo(inp, J3_COMBO_KEYS)})


def collect_k0(inp: dict) -> pd.DataFrame:
    from kpif_nowcast.j1_hybrid import j1_forecast

    panel = _panel(inp)
    f2 = pd.DataFrame({"base": j1_forecast(panel, "j1_comb_equal"), "actual": panel["actual"]})
    return pd.DataFrame({"k0_c1": _combo(inp, K0_COMBO_KEYS), "k0_c2": _combo(inp, K0_COMBO_KEYS, f2)})


def _freeze_k2_catalog() -> str:
    from kpif_nowcast import k2_ml
    from kpif_nowcast.catalog import by_key

    if hasattr(k2_ml, "K2_CATALOG_KEYS"):
        return "k2_ml.K2_CATALOG_KEYS (on main)"

    def frozen() -> list[tuple[str, str, bool]]:
        specs = by_key()
        return [(k, specs[k].unit, specs[k].revised) for k in K2_CATALOG_KEYS]

    k2_ml.catalog_keys = frozen
    return "k12_global.K2_CATALOG_KEYS (copy of K2b's frozen list; k2_ml on this main is not frozen)"


def collect_k2(inp: dict) -> pd.DataFrame:
    from kpif_nowcast.k2_ml import ALL_VARIANTS, K2Runner, build_design

    _freeze_k2_catalog()
    d = build_design(inp["kpif"], inp["comps"], inp["feats"], inp["contracts"], inp["se3"], inp["rb_fc"], inp["obs"])
    run = K2Runner(d)
    out = {}
    for v in ALL_VARIANTS:
        out[v] = run.series(v)
        print("  k2", v, "done", flush=True)
    return pd.DataFrame(out)


def collect_k7(inp: dict, k2: pd.DataFrame) -> pd.DataFrame:
    from kpif_nowcast.k7_services import K2_NAME, VARIANTS, build_k7

    d = build_k7(inp["kpif"], inp["comps"], inp["feats"], inp["contracts"], inp["se3"], inp["rb_fc"], inp["obs"],
                 k2_rows=None)
    d[K2_NAME] = k2[K2_NAME].reindex(d.index)
    for name, (m, layer) in VARIANTS.items():
        if layer == "k2":
            d[name] = d[K2_NAME] + (d[f"j2s_{m}"] - d["j2"])
    return d[list(VARIANTS)]


def collect_k8(inp: dict, k2: pd.DataFrame) -> pd.DataFrame | None:
    """K8 food (not on main yet when K12 was written): built from k8_food's functions if the module exists."""
    try:
        k8 = importlib.import_module("kpif_nowcast.k8_food")
    except ImportError:
        return None
    if hasattr(k8, "k12_forecasts"):
        return k8.k12_forecasts()
    panel = _panel(inp)
    fx = k8.sekusd_daily()
    d = k8.build_food_design(inp["kpif"], inp["comps"], inp["obs"], fx, last=pd.Period(PERIOD[1], "M"))
    months = pd.period_range(*PERIOD, freq="M")
    corr = k8.corrections(d, months)
    avg = 0.5 * panel["rb_updated"] + 0.5 * panel["j2"]
    return k8.totals(avg, d["k"], corr, k2["k2_avg_ens_s"])


def collect_v2(inp: dict) -> pd.DataFrame:
    """Run 3 wave 2 (V2): the joint corrections with the frozen selection, plus the shadow k2_avg_ridge_l."""
    from kpif_nowcast.v2_screen import k12_forecasts

    return k12_forecasts(inp)


def _source_hash(modules: list[str]) -> str:
    h = hashlib.sha256()
    for m in modules:
        f = ROOT / "src" / "kpif_nowcast" / f"{m}.py"
        if f.exists():
            h.update(f.read_bytes())
    for f in sorted((ROOT / "data" / "processed").glob("*.csv")) + [ROOT / "data" / "observations.parquet"]:
        if f.exists():
            st = f.stat()
            h.update(f"{f.name}{st.st_size}{int(st.st_mtime)}".encode())
    return h.hexdigest()[:16]


FAMILIES = {
    # name: (modules whose source defines the forecasts, collector, needs k2)
    "refs": (["j1_hybrid", "j2_el", "riksbank_benchmark"], collect_refs, False),
    "phase": (["backtest", "baselines", "component_model", "riksbank_benchmark"], collect_phase, False),
    "j1": (["j1_hybrid", "j2_el"], collect_j1, False),
    "j2": (["j2_el"], collect_j2, False),
    "j3": (["j3_screen"], collect_j3, False),
    "j4": (["j4_detail"], collect_j4, False),
    "k0": (["j3_screen", "k0_screen", "catalog_prices", "j1_hybrid"], collect_k0, False),
    "k2": (["k2_ml", "j1_hybrid", "j2_el", "j3_screen"], collect_k2, False),
    "k7": (["k7_services", "j2_el", "j1_hybrid"], collect_k7, True),
    "k8": (["k8_food"], collect_k8, True),
    "v2": (["v2_screen", "shadow", "k2_ml", "k2b_review", "j1_hybrid", "j2_el", "j3_screen", "publication"],
           collect_v2, False),
}
COMMON_MODULES = ["data", "features", "observations", "catalog"]


def _read_cache(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0)
    df.index = pd.PeriodIndex(df.index, freq="M")
    return df


def collect_all(refresh: bool = False, only: list[str] | None = None) -> tuple[pd.DataFrame, dict]:
    """All forecasts (one column per model) plus `actual`. Returns (frame, info per family)."""
    warnings.filterwarnings("ignore")
    CACHE.mkdir(parents=True, exist_ok=True)
    inp = None
    frames, info = {}, {}
    for fam, (mods, fn, needs_k2) in FAMILIES.items():
        if only and fam not in only and fam not in ("refs", "k2"):
            continue
        key = _source_hash(mods + COMMON_MODULES)
        path, meta = CACHE / f"{fam}.csv", CACHE / f"{fam}.json"
        if not refresh and path.exists() and meta.exists() and json.loads(meta.read_text())["key"] == key:
            frames[fam] = _read_cache(path)
            info[fam] = "cache"
            continue
        inp = inp or _inputs()
        print("collecting", fam, flush=True)
        try:
            df = fn(inp, frames["k2"]) if needs_k2 else fn(inp)
        except Exception as e:  # a track whose code cannot be run is reported, not hidden
            info[fam] = f"FEL: {type(e).__name__}: {e}"
            print(info[fam], flush=True)
            continue
        if df is None:
            info[fam] = "modul saknas"
            continue
        df.index = pd.PeriodIndex(df.index, freq="M")
        df.to_csv(path)
        meta.write_text(json.dumps({"key": key}), encoding="utf-8")
        frames[fam] = df
        info[fam] = "beräknad"
    # discovery: other modules with k12_forecasts(), and CSVs in outputs/k12/extra/
    known = {"k8_food"}
    import kpif_nowcast

    for m in pkgutil.iter_modules(kpif_nowcast.__path__):
        if m.name in known or m.name == "k12_global" or not m.name[:1] in "jk" or not m.name[1:2].isdigit():
            continue
        try:
            mod = importlib.import_module(f"kpif_nowcast.{m.name}")
        except Exception:
            continue
        if hasattr(mod, "k12_forecasts"):
            df = mod.k12_forecasts()
            df.index = pd.PeriodIndex(df.index, freq="M")
            frames[m.name] = df
            info[m.name] = "k12_forecasts()"
    for f in sorted(EXTRA.glob("*.csv")) if EXTRA.exists() else []:
        df = pd.read_csv(f).set_index("month")
        df.index = pd.PeriodIndex(df.index, freq="M")
        frames[f"extra:{f.stem}"] = df
        info[f"extra:{f.stem}"] = f"CSV {f.name}"
    family_of = {}
    cols = {}
    for fam, df in frames.items():
        for c in df.columns:
            if c not in cols:
                cols[c] = df[c]
                family_of[c] = fam
    out = pd.DataFrame(cols)
    out.attrs["family_of"] = family_of
    return out, info


# ====================================================================== analysis


def track_of(name: str, family: str) -> str:
    if name in REFERENCES:
        return "ref"
    if family == "phase":
        return "fas2-4"
    for p, t in TRACK_PREFIX:
        if name.startswith(p):
            return t
    return family


def common_sample(preds: pd.DataFrame, models: list[str]) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Errors on PERIOD for the models that cover the longest common sample. Drops models with gaps."""
    p = preds.loc[pd.Period(PERIOD[0], "M"): pd.Period(PERIOD[1], "M")]
    p = p[p["actual"].notna()]
    cover = p[models].notna().sum()
    full = cover.max()
    keep = [m for m in models if cover[m] >= full - 1]  # allow one missing first month (K2 starts 2015-02)
    dropped = [m for m in models if m not in keep]
    p = p[keep + ["actual"]].dropna()
    return p[keep].sub(p["actual"], axis=0), keep, dropped


def dedupe(err: pd.DataFrame, prefer: tuple[str, ...]) -> tuple[pd.DataFrame, dict]:
    """Drop exact duplicate series (e.g. avg_5050 = j1_comb_equal). Keeps names in `prefer`, else the first."""
    groups: dict[tuple, list[str]] = {}
    for c in err.columns:
        groups.setdefault(tuple(np.round(err[c].to_numpy(), 9)), []).append(c)
    drop, alias = [], {}
    for names in groups.values():
        keep = next((n for n in names if n in prefer), names[0])
        for n in names:
            if n != keep:
                drop.append(n)
                alias[n] = keep
    return err.drop(columns=drop), alias


def analyse(err: pd.DataFrame, bench: str, block: float, B: int, seed: int) -> dict:
    n = len(err)
    rng = np.random.default_rng(seed)
    idx = stationary_bootstrap_indices(n, B, block, rng)
    loss = err.abs()
    models = [c for c in loss.columns if c != bench]
    spa = spa_test(loss[bench].to_numpy(), loss[models].to_numpy(), idx)
    sb = selection_bias(spa)
    all_names = [bench, *models]
    L = loss[all_names].to_numpy()
    mcs_max = mcs(L, idx, "max")
    mcs_r = mcs(L, idx, "R")
    return {"n": n, "block": block, "models": models, "spa": spa, "sb": sb,
            "mcs_max": dict(zip(all_names, mcs_max)), "mcs_r": dict(zip(all_names, mcs_r))}


def _f(x: float, d: int = 3) -> str:
    return "–" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}".replace(".", ",")


def logged_mae() -> pd.DataFrame:
    """Latest logged MAE per variant on the primary 2015 period, for the reproduction check."""
    rows = []
    for f in sorted((ROOT / "experiments" / "runs").glob("*.csv")):
        if "k12_global" in f.name:
            continue
        df = pd.read_csv(f)
        prim = df[df["period"].astype(str).str.contains("2015") & ~df["period"].astype(str).str.contains("used")]
        for _, r in prim.iterrows():
            rows.append({"variant": str(r["variant"]).replace(" (posthoc)", ""), "MAE_log": r["MAE"], "n_log": r["n"],
                         "run": f.stem, "period": r["period"]})
    return pd.DataFrame(rows).drop_duplicates("variant", keep="last").set_index("variant") if rows else pd.DataFrame()


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="recompute all forecast families (ignore cache)")
    ap.add_argument("--B", type=int, default=9999, help="bootstrap replications")
    ap.add_argument("--no-log", action="store_true")
    a = ap.parse_args(argv)

    import kpif_nowcast
    from kpif_nowcast.evaluation import dm_test, git_sha, log_run

    preds, info = collect_all(a.refresh)
    family_of = preds.attrs["family_of"]
    candidates = [c for c in preds.columns if c != "actual"]
    err_all, kept, dropped = common_sample(preds, candidates)
    err_all, alias = dedupe(err_all, prefer=BENCHMARKS)
    phase = [c for c in err_all.columns if family_of.get(c) == "phase"]
    variants = [c for c in err_all.columns if c not in phase and c not in BENCHMARKS and c not in REFERENCES]
    n = len(err_all)

    # block length: Politis-White on the loss differences vs each benchmark
    pw = {b: np.median([politis_white_block(err_all[b].abs() - err_all[c].abs())
                        for c in err_all.columns if c != b]) for b in BENCHMARKS}
    block = float(np.clip(np.round(np.median(list(pw.values()))), 3, 6))

    mae = err_all.abs().mean()
    universes = {
        "U1 registrerade varianter + referenser": [*BENCHMARKS, *[r for r in REFERENCES if r in err_all.columns
                                                                  and r not in BENCHMARKS], *variants],
        "U2 U1 + fas 2–4-modeller": list(err_all.columns),
    }
    res = {}
    for uname, cols in universes.items():
        for bench in BENCHMARKS:
            res[(uname, bench, block)] = analyse(err_all[cols], bench, block, a.B, SEED)
    sens = {}
    for bl in (1, 3, 6, 12):
        if bl == block:
            continue
        for bench in BENCHMARKS:
            sens[(bl, bench)] = analyse(err_all[universes["U1 registrerade varianter + referenser"]], bench, bl,
                                        min(a.B, 4999), SEED + bl)
    best = mae[variants].idxmin()

    # ------------------------------------------------------------- report
    U1 = "U1 registrerade varianter + referenser"
    r_rb, r_50 = res[(U1, "rb_updated", block)], res[(U1, "avg_5050", block)]
    in_mcs = [m for m, p in r_rb["mcs_max"].items() if p >= ALPHA]
    i_best_rb = r_rb["models"].index(best)
    i_best_50 = r_50["models"].index(best)
    best_rb_adj = r_rb["spa"]["adj_p"][i_best_rb]
    best_50_adj = r_50["spa"]["adj_p"][i_best_50]
    stepm_rb = [m for m, rj in zip(r_rb["models"], r_rb["spa"]["stepm"][ALPHA]) if rj]
    stepm_50 = [m for m, rj in zip(r_50["models"], r_50["spa"]["stepm"][ALPHA]) if rj]
    sb_rb, sb_50 = r_rb["sb"], r_50["sb"]
    spa_rb, spa_50 = r_rb["spa"]["p"]["consistent"], r_50["spa"]["p"]["consistent"]
    mcs_excl_rb = r_rb["mcs_max"]["rb_updated"] < ALPHA
    mcs_excl_50 = r_rb["mcs_max"]["avg_5050"] < ALPHA

    def spa_at(bench: str, bl: float) -> float:
        r = res[(U1, bench, bl)] if bl == block else sens.get((bl, bench))
        return r["spa"]["p"]["consistent"] if r else float("nan")

    robust = {bn: max(spa_at(bn, 3), spa_at(bn, 6)) for bn in BENCHMARKS}  # worst case over blocks 3-6
    holds_rb = robust["rb_updated"] < ALPHA and best in stepm_rb
    holds_50 = robust["avg_5050"] < ALPHA and best in stepm_50
    n_active = int((err_all[best] != err_all["avg_5050"]).sum())
    if holds_rb and holds_50:
        verdict = (f"**Den bästa håller även globalt, men marginalen mot 50/50 är liten.** `{best}` är bättre än både "
                   f"rb_updated och 50/50 även när alla {len(variants)} varianter räknas: SPA p = {_f(spa_rb)} mot "
                   f"rb_updated och {_f(spa_50)} mot 50/50 (högst {_f(robust['rb_updated'])} resp. "
                   f"{_f(robust['avg_5050'])} för blocklängd 3–6), och Romano–Wolf StepM (10 %) pekar ut den mot båda "
                   f"ribborna (justerat p {_f(best_rb_adj)} resp. {_f(best_50_adj)}).")
    elif holds_rb:
        verdict = (f"**Håller globalt mot rb_updated, men inte mot 50/50.** Efter att alla {len(variants)} varianter "
                   f"räknats slår `{best}` rb_updated (SPA p = {_f(spa_rb)}, StepM väljer den). Fördelen över 50/50 går "
                   f"däremot inte att skilja från urvalsbias (SPA p = {_f(spa_50)}, högst {_f(robust['avg_5050'])} "
                   f"för block 3–6; justerat p för `{best}` = {_f(best_50_adj)}).")
    elif robust["rb_updated"] < ALPHA:
        verdict = (f"**Håller inte globalt för den enskilda modellen, men** något i universum slår rb_updated "
                   f"(SPA p = {_f(spa_rb)}); `{best}` utpekas inte av StepM.")
    else:
        verdict = (f"**Håller inte globalt.** När alla {len(variants)} varianter räknas går ingen förbättring mot "
                   f"rb_updated att skilja från urvalsbias (SPA p = {_f(spa_rb)}, högst {_f(robust['rb_updated'])} "
                   f"för block 3–6).")

    L = []
    L.append("# K12 Globalt test över alla modellvarianter: resultat\n")
    L.append(f"Genererad av `python -m kpif_nowcast.k12_global` (kod @ {git_sha()}). Inga nya varianter "
             f"(0 förbrukade). Bootstrap B = {a.B}, stationär bootstrap, medelblocklängd {block:g} månader, seed {SEED}. "
             f"Förlust = absolutfel (MAE). Allt är urvalsevidens på samma urval som modellerna valdes på.\n")
    L.append("## Dom\n")
    L.append(verdict + "\n")
    L.append(f"- Urval: {PERIOD[0]}..{PERIOD[1]}, gemensamt för alla serier, **n = {n}**. {len(variants)} registrerade "
             f"h=1-varianter + referenserna rb_updated, 50/50 och J2 V2 (U1), plus {len(phase)} fas 2–4-modeller (U2).")
    L.append(f"- Bästa variant: `{best}`, MAE {_f(mae[best])} mot rb_updated {_f(mae['rb_updated'])} och 50/50 "
             f"{_f(mae['avg_5050'])}. Den skiljer sig från 50/50 i {n_active} av {n} månader (K2 = 50/50 före 2018-02).")
    L.append(f"- **Urvalsbias i pe MAE.** Om alla {len(r_rb['models'])} modeller vore exakt lika bra som ribban skulle den "
             f"bästa ändå se ut att vinna med i snitt {_f(sb_rb['mean'])} pe mot rb_updated (90 %-kvantil "
             f"{_f(sb_rb['q90'])}) och {_f(sb_50['mean'])} pe mot 50/50 (90 % {_f(sb_50['q90'])}). Observerat bästa: "
             f"{_f(sb_rb['observed_max'])} resp. {_f(sb_50['observed_max'])}. Grovt biasjusterat: "
             f"≈ {_f(sb_rb['observed_max'] - sb_rb['mean'])} pe mot rb_updated, "
             f"≈ {_f(sb_50['observed_max'] - sb_50['mean'])} pe mot 50/50.")
    L.append(f"- **Varför SPA ändå kan godkänna mot 50/50 när den råa vinsten ligger inom brusbandet:** maximum av råa "
             f"vinster domineras av modeller som skiljer sig mycket från ribban och därför har stort brus (White RC p = "
             f"{_f(r_50['spa']['p']['white_rc'])}). SPA studentiserar: `{best}` är 50/50 plus en liten, stabil "
             f"korrektion, så dess vinst är liten men ovanligt säker. Studentiserat är bästa t under H0 i snitt "
             f"{_f(sb_50['t_mean'], 2)} (90 % {_f(sb_50['t_q90'], 2)}), observerat {_f(sb_50['t_observed'], 2)}. "
             f"Mot rb_updated: {_f(sb_rb['t_mean'], 2)} (90 % {_f(sb_rb['t_q90'], 2)}), observerat "
             f"{_f(sb_rb['t_observed'], 2)}.")
    L.append(f"- **Model Confidence Set (90 %, T_max)** innehåller {len(in_mcs)} av {len(r_rb['mcs_max'])} modeller; "
             f"rb_updated {'är utesluten' if mcs_excl_rb else 'ingår'}, 50/50 "
             f"{'är utesluten' if mcs_excl_50 else 'ingår'}. Utanför: "
             f"{', '.join(f'`{m}`' for m, p in r_rb['mcs_max'].items() if p < ALPHA) or 'ingen'}. MCS jämför varje "
             f"modell med *snittet* av mängden och har låg styrka med n = {n} och så här korrelerade modeller. Den "
             f"säger att datan inte räcker för att rangordna de flesta, inte att de är lika bra. StepM besvarar den "
             f"skarpare frågan \"vilka slår ribban\".")
    L.append(f"- Förbehåll: K2b fann att ea_news läckte i tre månader (flashdatum); med K2b:s rättelse är `{best}` "
             f"0,200. Rättelsen är inte med här (koden på main används). Allt gäller samma urval som modellerna valdes "
             f"på; det ersätter inte ett utfall utanför urvalet. Skuggprognoserna från 2026-12 är det riktiga testet.\n")

    L.append("## Globala test (U1, primär blocklängd)\n")
    L.append("| Ribba | n modeller | SPA lower | SPA consistent | SPA upper | White RC | E[max förbättring] H0 | 90 % | observerat max | StepM 10 % väljer |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for bench in BENCHMARKS:
        r = res[(U1, bench, block)]
        p = r["spa"]["p"]
        sm = [m for m, rj in zip(r["models"], r["spa"]["stepm"][ALPHA]) if rj]
        L.append(f"| {bench} | {len(r['models'])} | {_f(p['lower'])} | {_f(p['consistent'])} | {_f(p['upper'])} | "
                 f"{_f(p['white_rc'])} | {_f(r['sb']['mean'])} | {_f(r['sb']['q90'])} | {_f(r['sb']['observed_max'])} | "
                 f"{', '.join(f'`{m}`' for m in sm) or 'ingen'} |")
    L.append("\nSPA: H0 = ingen modell har lägre förväntad MAE än ribban. *consistent* är Hansens rekommenderade p; "
             "*lower*/*upper* ger gränser. White RC = ostudentiserad, övre recentrering. StepM = Romano–Wolf "
             "steg-ned, familjevis felrisk 10 % över hela universum.\n")

    L.append("## Känslighet\n")
    L.append("| Universum / blocklängd | Ribba | SPA consistent | White RC | E[max] H0 | `" + best + "` justerat p | 90 %-MCS (antal) |")
    L.append("|---|---|---|---|---|---|---|")
    rows_sens = [(k[0] + f", block {block:g}", k[1], v) for k, v in res.items()]
    rows_sens += [(f"U1, block {k[0]:g}", k[1], v) for k, v in sens.items()]
    for lab, bench, r in rows_sens:
        ib = r["models"].index(best)
        nm = sum(p >= ALPHA for p in r["mcs_max"].values())
        L.append(f"| {lab} | {bench} | {_f(r['spa']['p']['consistent'])} | {_f(r['spa']['p']['white_rc'])} | "
                 f"{_f(r['sb']['mean'])} | {_f(r['spa']['adj_p'][ib])} | {nm} |")
    L.append(f"\nBlocklängd: Politis–White-skattning (median över förlustdifferenserna) = "
             f"{_f(pw['rb_updated'], 1)} mot rb_updated, {_f(pw['avg_5050'], 1)} mot 50/50; avrundad och begränsad "
             f"till 3–6 månader (Riksbankens prognosomgång lever 2–4 månader, så felen är korrelerade inom en omgång). "
             f"1 och 12 visas som ytterlägen.\n")

    L.append("## Per modell (U1, primär blocklängd)\n")
    L.append("| Modell | Spår | MAE | diff mot rb_updated | DM p ensidig (rå) | max-t justerat p mot rb_updated | "
             "justerat p mot 50/50 | MCS p (T_max) | MCS p (T_R) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    order = mae[universes[U1]].sort_values().index
    for m in order:
        dm = dm_test(err_all[m].to_numpy(), err_all["rb_updated"].to_numpy()) if m != "rb_updated" else None
        p1 = (dm.p / 2 if dm.mean_diff < 0 else 1 - dm.p / 2) if dm else float("nan")
        a_rb = r_rb["spa"]["adj_p"][r_rb["models"].index(m)] if m in r_rb["models"] else float("nan")
        a_50 = r_50["spa"]["adj_p"][r_50["models"].index(m)] if m in r_50["models"] else float("nan")
        L.append(f"| `{m}` | {track_of(m, family_of.get(m, ''))} | {_f(mae[m])} | {_f(mae[m] - mae['rb_updated'])} | "
                 f"{_f(p1)} | {_f(a_rb)} | {_f(a_50)} | {_f(r_rb['mcs_max'][m])} | {_f(r_rb['mcs_r'][m])} |")
    L.append("\nJusterat p = andel bootstrapdragningar där den största studentiserade förbättringen bland *alla* "
             "modeller (under H0) är minst modellens egen (enstegs max-t, konservativ). MCS p ≥ 0,10 = i 90 %-MCS.\n")

    # inventory
    L.append("## Inventering\n")
    L.append("| Familj | Status |")
    L.append("|---|---|")
    for fam, s in info.items():
        L.append(f"| {fam} | {s} |")
    L.append("")
    if alias:
        L.append("Identiska serier (räknas en gång): " + ", ".join(f"`{k}` = `{v}`" for k, v in alias.items()) + ".\n")
    if dropped:
        L.append("Utan full täckning på urvalet (inte med): " + ", ".join(f"`{m}`" for m in dropped) + ".\n")
    L.append("Inte med, med orsak:\n")
    L.append("- J5 (U1–U6): intervallmetoder runt comp_fuel, ingen egen punktprognos.")
    L.append("- K6 (N1, N2): prognoser för Finlands och Danmarks HIKP, inte KPIF.")
    L.append("- K9 (4 varianter): horisont 3–12 månader, annat mål och överlappande fel.")
    L.append("- J3/K0-screeningarna (45 + 29 serier): räknades inte mot taket och ingår inte; kombinationerna "
             "(`j3_combo`, `k0_c1`, `k0_c2`) ingår. Om screeningarna räknades skulle urvalsbiasen bli större, inte mindre.")
    L.append("- K1, K3, K4: inga modellvarianter.")
    L.append("- K2b: inga nya varianter. K2b:s rättelse av flashdatumen (ea_news) ändrar K2-varianterna marginellt "
             "(0,199 → 0,200); här används koden på main.")
    L.append("- K8 tas med automatiskt när `k8_food` finns på main (samma kod som K8:s main).\n")

    lm = logged_mae()
    if not lm.empty:
        L.append("## Reproduktionskontroll (MAE här mot körloggen)\n")
        L.append("Egen MAE räknas på det gemensamma urvalet; loggens på spårets eget urval (kan skilja en månad).\n")
        L.append("| Modell | MAE här | MAE logg | n logg | körning |")
        L.append("|---|---|---|---|---|")
        for m in order:
            key = alias.get(m, m)
            if m in lm.index:
                r = lm.loc[m]
                L.append(f"| `{m}` | {_f(mae[key])} | {_f(float(r['MAE_log']))} | {int(r['n_log'])} | {r['run']} |")
        L.append("")
    L.append(f"`kpif_nowcast.__file__` = `{kpif_nowcast.__file__}`. K2:s L-mängd: {_freeze_k2_catalog()}.\n")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "resultat.md").write_text("\n".join(L), encoding="utf-8")
    err_all.to_csv(CACHE / "errors_common.csv")
    print("\n".join(L[:12]))
    if not a.no_log:
        rows = [{"variant": m, "period": f"{PERIOD[0]}..{PERIOD[1]} common", "n": n, "MAE": round(float(mae[m]), 4),
                 "dm_p_vs_rb_updated": round(float(r_rb["spa"]["adj_p"][r_rb["models"].index(m)]), 4)
                 if m in r_rb["models"] else float("nan")} for m in order]
        log_run("k12_global", rows)


if __name__ == "__main__":
    main()
