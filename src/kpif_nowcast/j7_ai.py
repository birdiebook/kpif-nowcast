"""J7: a Swedish AI indicator - job-ad demand for AI skills, firms' AI use, productivity by industry.

Method written before fetching: docs/auto/j7/hypotes.md. Descriptive only; no causal claims.
All fetched responses are cached per request under data/raw/j7/ (resumable; nothing is fetched twice).

Run: python -m kpif_nowcast.j7_ai [sample|build]
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "j7"
JOBTECH = "https://historical.api.jobtechdev.se/search"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
TERMS = ["AI", "artificiell intelligens", "maskininlärning", "machine learning", "generativ AI", "LLM",
         "språkmodell", "deep learning"]
YEARS = list(range(2016, 2026))
EXPOSED = {"J": "Information och kommunikation", "K": "Finans och försäkring", "M_N": "Företagstjänster"}
OTHER = {"B-E": "Industri", "F": "Bygg", "G-I": "Handel, transport, hotell och restaurang"}


def _cached_get(url: str, params: dict, tries: int = 3) -> dict:
    import requests

    key = hashlib.sha1((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:16]
    path = RAW / f"{url.rstrip('/').rsplit('/', 1)[-1]}_{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=90, headers={"User-Agent": "kpif-nowcast research script"})
            r.raise_for_status()
            break
        except Exception:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(2 ** (k + 1))
    RAW.mkdir(parents=True, exist_ok=True)
    data = r.json()
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    time.sleep(0.2)
    return data


def jobtech(year: int, term: str | None, limit: int = 0) -> dict:
    params = {"limit": limit, "historical-from": f"{year}-01-01T00:00:00", "historical-to": f"{year}-12-31T23:59:59",
              "stats": "occupation-field", "stats.limit": 30}
    if term:
        params["q"] = term
    return _cached_get(JOBTECH, params)


def snippet(text: str, term: str, width: int = 110) -> str:
    m = re.search(rf"(?<![\wåäö]){re.escape(term)}(?![\wåäö])", text, flags=re.IGNORECASE)
    if not m:
        return "(termen syns inte i texten)"
    s = text[max(0, m.start() - width): m.end() + width]
    return re.sub(r"\s+", " ", s)


def validation_sample(n: int = 10, year: int = 2025) -> pd.DataFrame:
    rows = []
    for term in TERMS:
        hits = jobtech(year, term, limit=n)["hits"]
        for h in hits:
            text = (h.get("description") or {}).get("text") or ""
            rows.append({"term": term, "id": h["id"], "headline": h["headline"],
                         "field": (h.get("occupation_field") or {}).get("label"),
                         "snippet": snippet(h["headline"] + " . " + text, term)})
    return pd.DataFrame(rows)


def ad_counts(terms: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Annual totals (rows: year, cols: 'all' + terms) and per occupation field counts (long)."""
    tot, fields = {}, []
    for y in YEARS:
        tot[y] = {}
        for term in [None, *terms]:
            j = jobtech(y, term)
            name = term or "all"
            tot[y][name] = j["total"]["value"]
            for st in j.get("stats", []):
                for v in st["values"]:
                    fields.append({"year": y, "term": name, "field": v["term"], "count": v["count"]})
    return pd.DataFrame(tot).T, pd.DataFrame(fields)


def productivity() -> pd.DataFrame:
    """Real labour productivity per hour (2015=100) by industry, SE and EU27, long."""
    out = []
    for geo in ["SE", "EU27_2020"]:
        j = _cached_get(f"{EUROSTAT}/nama_10_lp_a21",
                        {"format": "JSON", "geo": geo, "unit": "I15", "na_item": "RLPR_HW", "sinceTimePeriod": "2010"})
        dims = j["id"]
        sizes = j["size"]
        cats = {d: list(j["dimension"][d]["category"]["index"]) for d in dims}
        for flat, v in j["value"].items():
            idx, rest = {}, int(flat)
            for d, s in zip(reversed(dims), reversed(sizes)):
                idx[d] = cats[d][rest % s]
                rest //= s
            out.append({"geo": geo, "nace": idx["nace_r2"], "year": int(idx["time"]), "value": float(v)})
    return pd.DataFrame(out)


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


def build(approved: list[str]) -> dict:
    from kpif_nowcast import observations as obs

    tot, fields = ad_counts(TERMS)
    share = tot[TERMS].div(tot["all"], axis=0) * 1e4  # ads per 10 000
    main_term = approved[0]
    f_all = fields[fields["term"] == "all"].pivot(index="year", columns="field", values="count")
    f_ai = fields[fields["term"] == main_term].pivot(index="year", columns="field", values="count")
    f_share = (f_ai / f_all * 1e4).round(1)
    prod = productivity()
    table = obs.load()
    use = {g: obs.as_of(k, "2100-01-01", table) for g, k in [("SE", "ai_use_firms_se"), ("EU27", "ai_use_firms_eu")]}
    use = pd.DataFrame({g: pd.Series(s.to_numpy(), index=s.index.year) for g, s in use.items()})
    ind = pd.DataFrame({"ad_share": share[main_term], "firm_use_se": use["SE"].reindex(share.index)})
    zs = ind.loc[2017:].apply(zscore)
    ind["indicator"] = zs.mean(axis=1, skipna=True)
    return {"totals": tot, "share": share, "field_share": f_share, "productivity": prod, "firm_use": use,
            "indicator": ind, "main_term": main_term}


def tidy_rows(res: dict) -> pd.DataFrame:
    """One long table for the dashboard: series, group, year, value."""
    rows = []
    for term in res["share"]:
        for y, v in res["share"][term].items():
            rows.append({"series": "ad_share_per_10k", "group": term, "year": int(y), "value": float(v)})
    for f in res["field_share"]:
        for y, v in res["field_share"][f].items():
            if pd.notna(v):
                rows.append({"series": f"ad_share_by_field_per_10k ({res['main_term']})", "group": f, "year": int(y),
                             "value": float(v)})
    for g in res["firm_use"]:
        for y, v in res["firm_use"][g].dropna().items():
            rows.append({"series": "firm_ai_use_pct", "group": g, "year": int(y), "value": float(v)})
    prod = res["productivity"]
    keep = prod[prod["nace"].isin(list(EXPOSED) + list(OTHER))]
    for r in keep.itertuples():
        rows.append({"series": "productivity_per_hour_2015_100", "group": f"{r.geo} {r.nace}", "year": r.year,
                     "value": r.value})
    for y, v in res["indicator"]["indicator"].dropna().items():
        rows.append({"series": "ai_diffusion_indicator_z", "group": "SE", "year": int(y), "value": float(v)})
    return pd.DataFrame(rows)


def main(mode: str) -> None:
    if mode == "sample":
        df = validation_sample()
        out = ROOT / "outputs" / "j7_validation_sample.csv"
        out.parent.mkdir(exist_ok=True)
        df.to_csv(out, index=False, encoding="utf-8")
        for term, g in df.groupby("term", sort=False):
            print(f"\n=== {term}")
            for _, r in g.iterrows():
                print(f"- [{r['field']}] {r['headline'][:70]} :: {r['snippet'][:230]}")
    elif mode == "build":
        approved = json.loads((ROOT / "docs" / "auto" / "j7" / "approved_terms.json").read_text(encoding="utf-8"))
        res = build(approved)
        write_outputs(res, approved)


def write_outputs(res: dict, approved: list[str]) -> None:
    out = ROOT / "outputs" / "sverige"
    out.mkdir(parents=True, exist_ok=True)
    prod = res["productivity"]
    payload = {
        "method": "docs/ai-indikator.md",
        "main_term": res["main_term"],
        "approved_terms": approved,
        "ad_share_per_10k": {t: {str(y): round(float(v), 2) for y, v in res["share"][t].items()} for t in res["share"]},
        "ad_share_by_field_per_10k": {f: {str(y): (None if pd.isna(v) else float(v)) for y, v in res["field_share"][f].items()}
                                      for f in res["field_share"]},
        "firm_ai_use_pct": {g: {str(y): (None if pd.isna(v) else float(v)) for y, v in res["firm_use"][g].items()}
                            for g in res["firm_use"]},
        "productivity_2015_100": {f"{r.geo}:{r.nace}:{r.year}": r.value for r in prod.itertuples()},
        "indicator_z": {str(y): (None if pd.isna(v) else round(float(v), 3)) for y, v in res["indicator"]["indicator"].items()},
    }
    (out / "ai_indicator_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ["main_term", "indicator_z"]}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build")
