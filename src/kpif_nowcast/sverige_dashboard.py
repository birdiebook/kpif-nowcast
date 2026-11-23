"""Export the datasets behind the "Sverigeläget" dashboard (Claude Data).

Run: python -m kpif_nowcast.sverige_dashboard

Reads the versioned observation table (latest vintage of every catalog series) and writes
outputs/sverige/<name>.json as {"rows": [...], "meta": [...]}; meta carries this script's code.

How each series is shown ("display value"):
- levels that trend (prices, indices, wages, counts) -> change vs 12 months earlier, %
- rates, balances, shares and survey indicators -> as published
- AI job ads -> per 10 000 published ads

Inflation pressure: each series gets a sign (+1 = higher value means more inflation pressure,
-1 = less, 0 = not part of the pressure picture). Its z-score over 2005..now times the sign is
its "pressure". An area's pressure is the mean over its series. These are descriptive, not a model.

Link to inflation: correlation between the display value lagged L = 0..12 months and KPIF y/y,
2005..now, monthly (quarterly series on their quarter months). Correlation is not prediction;
the forecast test is a separate step.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from kpif_nowcast import observations as obs
from kpif_nowcast.catalog import AREAS, CATALOG

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "sverige"
START = pd.Period("2005-01", "M")
SERIES_START = pd.Period("2010-01", "M")
MAX_LAG = 12

YOY = {
    "brent_sek", "kix", "wage_private_nonmanual", "wage_private_manual_hourly", "vacancies", "aku_employed",
    "house_price_idx", "housing_starts", "bankruptcies", "service_prod_idx", "fao_food_idx", "fao_cereals",
    "fao_dairy", "gas_eu_usd", "wheat_usd", "freight_ppi_deepsea", "gdp_real_q", "hours_worked_q",
    "software_investment_q", "jobads_total", "af_varsel", "af_inskrivna_arbetslosa", "af_oppet_arbetslosa",
}
PER_10K_ADS = {"jobads_ml", "jobads_ai"}
SKIP = {"kpif_index", "kpif_yy", "aku_unemp_sa", "nier_firm_infl_exp_new"}  # target / duplicates / 1 obs

SIGN = {
    "aku_unemp_nsa": -1, "bankruptcies": -1, "hh_saving_rate": -1, "mortgage_rate_new": -1, "policy_rate": -1,
    "lp_hour_yy_se": -1, "lp_hour_yy_ea": 0, "ai_use_firms_se": 0, "ai_use_firms_eu": 0, "jobads_ml": 0,
    "jobads_ai": 0, "software_investment_q": 0, "gdp_real_q": 0, "hours_worked_q": 0,
    "af_varsel": -1, "af_inskrivna_arbetslosa": -1, "af_oppet_arbetslosa": -1,
}  # every other series: +1


def display_value(key: str, s: pd.Series, table: pd.DataFrame) -> pd.Series:
    if key in YOY:
        return (s / s.shift(12) - 1) * 100 if s.index.freqstr == "M" else _yoy_sparse(s)
    if key in PER_10K_ADS:
        total = obs.as_of("jobads_total", "2100-01-01", table)
        return (s / total * 10_000).dropna()
    return s


def _yoy_sparse(s: pd.Series) -> pd.Series:
    """y/y for series stored on quarter/year months: compare with the same month a year earlier."""
    prev = s.reindex(s.index - 12)
    prev.index = s.index
    return ((s / prev - 1) * 100).dropna()


def _clean(v):
    if v is None:
        return None
    if isinstance(v, pd.Period):
        return str(v)
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float):
        return None if not math.isfinite(v) else round(v, 4)
    return v


def _write(name: str, df: pd.DataFrame, note: str) -> None:
    code = Path(__file__).read_text(encoding="utf-8")
    payload = {
        "rows": [{k: _clean(v) for k, v in r.items()} for r in df.to_dict(orient="records")],
        "meta": [
            {"label": "sverige_dashboard.py", "value": code, "type": "code", "lang": "python"},
            {"label": "Input", "value": "data/observations.parquet (latest vintage per series), " + note},
            {"label": "Exported", "value": datetime.now().isoformat(timespec="seconds")},
            {"label": "Repository", "value": "https://github.com/birdiebook/kpif-nowcast"},
        ],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"  {path.relative_to(ROOT)}: {len(df)} rows, {path.stat().st_size // 1024} KB")


def best_lead(x: pd.Series, kpif: pd.Series) -> tuple[float, int, int]:
    """Correlation with KPIF y/y at the lag (0..12 months) with the largest |r|; returns (r, lag, n)."""
    best = (np.nan, 0, 0)
    for lag in range(MAX_LAG + 1):
        shifted = x.copy()
        shifted.index = shifted.index + lag
        pair = pd.concat([shifted, kpif], axis=1, join="inner").dropna()
        pair = pair[pair.index >= START]
        if len(pair) < 24:
            continue
        r = float(pair.iloc[:, 0].corr(pair.iloc[:, 1]))
        if np.isnan(best[0]) or abs(r) > abs(best[0]):
            best = (r, lag, len(pair))
    return best


def main() -> None:
    table = obs.load()
    kpif = obs.as_of("kpif_yy", "2100-01-01", table)
    overview, long_rows, pressure_cols = [], [], {}

    for spec in CATALOG:
        if spec.key in SKIP:
            continue
        raw = obs.as_of(spec.key, "2100-01-01", table)
        if raw.empty:
            continue
        dv = display_value(spec.key, raw, table).dropna()
        if dv.empty:
            continue
        hist = dv[dv.index >= START]
        mu, sd = hist.mean(), hist.std()
        z = (dv - mu) / sd if sd and sd > 0 else dv * np.nan
        sign = SIGN.get(spec.key, 1)
        r, lag, n = best_lead(dv, kpif) if spec.freq != "A" else (np.nan, 0, 0)
        last_p = dv.index.max()
        prev = dv[dv.index <= last_p - 12]
        overview.append({
            "key": spec.key, "area": spec.area, "area_label": AREAS[spec.area], "label": spec.label,
            "display": "årsförändring %" if spec.key in YOY else ("per 10 000 annonser" if spec.key in PER_10K_ADS else spec.unit),
            "freq": spec.freq, "source": spec.source, "link": spec.link,
            "period": str(last_p), "value": float(dv.iloc[-1]),
            "value_12m_ago": float(prev.iloc[-1]) if len(prev) else None,
            "z": float(z.iloc[-1]), "pressure": float(z.iloc[-1] * sign) if sign else None, "sign": sign,
            "corr_kpif": r, "corr_lead_months": lag, "corr_n": n,
            "revised": spec.revised,
        })
        for p, v in dv[dv.index >= SERIES_START].items():
            long_rows.append({"key": spec.key, "period": str(p), "value": float(v),
                              "z": float(z.get(p)) if pd.notna(z.get(p)) else None})
        if sign and spec.freq in ("M", "Q"):
            zz = (z * sign)
            if spec.freq == "Q":  # spread a quarter over its three months for the area average
                zz = zz.reindex(pd.period_range(zz.index.min() - 2, zz.index.max(), freq="M")).bfill(limit=2)
            pressure_cols.setdefault(spec.area, []).append(zz.rename(spec.key))

    ov = pd.DataFrame(overview)
    _write("overview", ov, "one row per series: latest value, z-score, pressure sign, correlation with KPIF")
    _write("series", pd.DataFrame(long_rows), f"display values from {SERIES_START}, long format")

    area_rows = []
    for area, cols in pressure_cols.items():
        m = pd.concat(cols, axis=1)
        avg = m.mean(axis=1).where(m.notna().sum(axis=1) >= max(1, len(cols) // 3))
        for p, v in avg[avg.index >= SERIES_START].items():
            if pd.notna(v):
                area_rows.append({"area": area, "area_label": AREAS[area], "period": str(p), "pressure": float(v),
                                  "n_series": int(m.loc[p].notna().sum())})
    for p, v in kpif[kpif.index >= SERIES_START].items():
        area_rows.append({"area": "kpif", "area_label": "KPIF, årstakt", "period": str(p), "pressure": float(v),
                          "n_series": 1})
    _write("pressure", pd.DataFrame(area_rows), "area pressure = mean of signed z-scores; plus KPIF y/y")

    # AI and productivity story, one tidy table
    ai_keys = ["lp_hour_yy_se", "lp_hour_yy_ea", "ai_use_firms_se", "ai_use_firms_eu", "jobads_ml", "jobads_ai",
               "software_investment_q"]
    ai = [r for r in long_rows if r["key"] in ai_keys]
    for k in ["ai_use_firms_se", "ai_use_firms_eu"]:  # annual: whole history
        s = obs.as_of(k, "2100-01-01", table)
        ai = [r for r in ai if r["key"] != k] + [{"key": k, "period": str(p), "value": float(v), "z": None}
                                                 for p, v in s.items()]
    _write("ai", pd.DataFrame(ai), "AI and productivity series")

    # Swedish AI indicator (J7): job ads per occupation field, firms' AI use, productivity by industry
    try:
        import json as _json

        from kpif_nowcast import j7_ai

        approved = _json.loads((ROOT / "docs" / "auto" / "j7" / "approved_terms.json").read_text(encoding="utf-8"))
        _write("ai_indicator", j7_ai.tidy_rows(j7_ai.build(approved)), "AI indicator, method in docs/ai-indikator.md")
    except Exception as exc:  # noqa: BLE001 - the rest of the dashboard must not depend on it
        print(f"  ai_indicator skipped: {type(exc).__name__}: {exc}")

    print("\nTop pressure now:")
    print(ov.dropna(subset=["pressure"]).sort_values("pressure", ascending=False)[["key", "period", "value", "pressure"]]
          .head(8).round(2).to_string(index=False))
    print("\nStrongest link to KPIF:")
    print(ov.reindex(ov["corr_kpif"].abs().sort_values(ascending=False).index)[["key", "corr_kpif", "corr_lead_months"]]
          .head(10).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
