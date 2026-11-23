"""Champion/challenger table for forecasts/SCORECARD.md.

Two kinds of evidence, kept apart:
- Backtest 2015-2026: the models were selected on this period, so it is selection evidence only.
  2024-2026 has been used for many variants and is reported, never used for choosing.
- Live: FINAL shadow forecasts (forecasts/shadow/<model>/<month>.json) for months whose outcome
  is now published. Only months where every registered model has a FINAL file count, so all
  models are compared on the same months.

Benchmarks rb_updated and the Riksbank forecast are computed from data with the same deadline rule.
"""

from __future__ import annotations

import json

import pandas as pd

from kpif_nowcast.shadow import CHAMPION, SHADOW_DIR, SHADOW_MODELS, Inputs, rb_updated

BENCHMARKS = ["rb_updated", "riksbank"]


def histories(inp: Inputs) -> pd.DataFrame:
    """Backtest forecast per model and benchmark, one column each."""
    from kpif_nowcast.riksbank_benchmark import riksbank_at_deadline

    out = pd.DataFrame({name: m.fn(inp)["yy_hat"] for name, m in SHADOW_MODELS.items()})
    rb = riksbank_at_deadline(inp.rb_fc, inp.kpif.index.append(pd.PeriodIndex([inp.kpif.index.max() + 1])),
                              inp.kpif["yy_official"])
    out["rb_updated"] = rb["rb_updated"]
    out["riksbank"] = rb["riksbank"]
    return out


def live_forecasts() -> pd.DataFrame:
    """FINAL shadow forecasts, months x models (NaN where a model has no FINAL file)."""
    rows = {}
    for name in SHADOW_MODELS:
        for path in sorted((SHADOW_DIR / name).glob("*.json")):
            f = json.loads(path.read_text(encoding="utf-8"))
            if f.get("status") == "FINAL":
                rows.setdefault(pd.Period(f["target_month"], "M"), {})[name] = f["forecast_yy"]
    return pd.DataFrame.from_dict(rows, orient="index").reindex(columns=list(SHADOW_MODELS))


def _mae(pred: pd.DataFrame, actual: pd.Series) -> tuple[pd.Series, int]:
    p = pred[actual.reindex(pred.index).notna()].dropna()
    return p.sub(actual.reindex(p.index), axis=0).abs().mean(), len(p)


def table(inp: Inputs, live: pd.DataFrame | None = None) -> tuple[pd.DataFrame, dict]:
    actual = inp.kpif["yy_official"]
    last = actual.dropna().index.max()
    hist = histories(inp).loc[: last]
    cols = list(hist)
    # models with a forecast from early 2015 (rb_updated starts 2015-02: first Riksbank vintage 2015:1)
    long_cols = [c for c in cols if (fv := hist[c].first_valid_index()) is not None and fv <= pd.Period("2015-03", "M")]
    mae_long, n_long = _mae(hist.loc["2015-01":, long_cols], actual)
    first_long = hist.loc["2015-01":, long_cols].dropna().index.min()
    mae_used, n_used = _mae(hist.loc["2024-01":, cols], actual)
    first_used = hist.loc["2024-01":, cols].dropna().index.min()

    live = live_forecasts() if live is None else live
    live = live[actual.reindex(live.index).notna()].dropna()  # same months for every model
    if len(live):
        live = live.join(hist.loc[live.index, BENCHMARKS])
    mae_live, n_live = _mae(live, actual) if len(live) else (pd.Series(dtype=float), 0)

    roles = {CHAMPION: "champion (live model)", "rb_updated": "benchmark", "riksbank": "benchmark"}
    df = pd.DataFrame(index=cols)
    df["Roll"] = [roles.get(c, "challenger") for c in cols]
    df["MAE 2015–26 (urval)"] = mae_long.reindex(cols)
    df["MAE 2024–26 (använd)"] = mae_used.reindex(cols)
    df["MAE live"] = mae_live.reindex(cols) if n_live else float("nan")
    df["Första backtestmånad"] = [str(hist[c].first_valid_index()) for c in cols]
    meta = {"first_long": str(first_long), "n_long": n_long, "n_used": n_used, "first_used": str(first_used), "last": str(last), "n_live": n_live}
    return df, meta


def section(inp: Inputs | None = None) -> list[str]:
    if inp is None:
        from kpif_nowcast.data import load_components, load_kpif, load_riksbank_forecasts
        from kpif_nowcast.features import load_features

        inp = Inputs(load_kpif(), load_components(), load_features(), load_riksbank_forecasts())
    df, m = table(inp)
    shown = df.copy()
    for c in ["MAE 2015–26 (urval)", "MAE 2024–26 (använd)", "MAE live"]:
        shown[c] = shown[c].map(lambda v: "–" if pd.isna(v) else f"{v:.3f}")
    return [
        "",
        "## Champion/challenger",
        "",
        "Skuggprognoser loggas i `forecasts/shadow/<modell>/<månad>.json` (genereras av "
        "`python -m kpif_nowcast.pipeline monthly`). Årstakt KPIF, absolut fel i procentenheter.",
        "",
        shown.reset_index(names="Modell").to_markdown(index=False),
        "",
        f"- **MAE 2015–26 är urvalsevidens**: modellerna valdes på den perioden. Gemensamt urval "
        f"{m['first_long']}..{m['last']}, n = {m['n_long']}, bara modeller som finns från 2015 "
        f"(`{CHAMPION}` har energikorrektion först från 2023-12 och saknas där).",
        f"- **MAE 2024–26** är en redan använd period, samma månader för alla modeller "
        f"({m['first_used']}..{m['last']}, n = {m['n_used']}). Rapporteras, väljs inte på.",
        f"- **Live**: FINAL-skuggprognoser med publicerat utfall, samma månader för alla modeller: "
        f"**{m['n_live']} månader**." + (" Än så länge finns ingen riktig evidens." if m["n_live"] == 0 else ""),
    ]
