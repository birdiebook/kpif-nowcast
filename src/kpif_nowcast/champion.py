"""Champion/challenger table for forecasts/SCORECARD.md.

Two kinds of evidence, kept apart:
- Backtest 2015-2026: the models were selected on this period, so it is selection evidence only.
  2024-2026 has been used for many variants and is reported, never used for choosing.
- Live: FINAL shadow forecasts (forecasts/shadow/<model>/<month>.json) for months whose outcome
  is now published. Only months where every registered model has a FINAL file count, so all
  models are compared on the same months.

Benchmarks rb_updated and the Riksbank forecast are computed from data with the same deadline rule.

L9: SCB's flash estimate (Snabb-KPI, catalog_flash: kpif_flash_yy, kpif_flash_err_yy) as a reference. For the
months with a flash (from 2024-09), descriptive only: the flash's own error against the first-published outcome,
and each model's backtest forecast against the flash and against the outcome, on the same months for all.
No tests, no p-values: it shows how close the models come to SCB's own early figure.
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


def table(inp: Inputs, live: pd.DataFrame | None = None, hist: pd.DataFrame | None = None) -> tuple[pd.DataFrame, dict]:
    actual = inp.kpif["yy_official"]
    last = actual.dropna().index.max()
    hist = (histories(inp) if hist is None else hist).loc[: last]
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


FLASH_YY, FLASH_ERR_YY = "kpif_flash_yy", "kpif_flash_err_yy"


def load_flash(table: pd.DataFrame | None = None) -> tuple[pd.Series, pd.Series]:
    """Snabb-KPI KPIF y/y and its error against the first-published outcome (latest vintage; ex post use)."""
    from kpif_nowcast import observations as obs

    table = obs.load() if table is None else table
    latest = "2100-01-01"
    return obs.as_of(FLASH_YY, latest, table), obs.as_of(FLASH_ERR_YY, latest, table)


def flash_reference(pred: pd.DataFrame, actual: pd.Series, flash: pd.Series,
                    flash_err: pd.Series | None = None) -> tuple[pd.DataFrame, dict]:
    """Per model (columns of `pred`): MAE against the outcome and against the flash, mean signed difference to
    the flash and share within 0.1 pp of it, on the months where the flash, the outcome and every model exist.
    The row "snabb_kpi" is the flash itself, measured against the same `actual` as the models. Its error against
    the first-published outcome (`flash_err`, if given) is reported separately in `meta` ("first_pub_*")."""
    flash, actual = flash.dropna(), actual.dropna()
    months = flash.index.intersection(actual.index)
    p = pred.reindex(months).dropna()
    m = p.index
    if not len(m):
        return pd.DataFrame(), {"n": 0}
    d_flash = p.sub(flash.reindex(m), axis=0)
    d_out = p.sub(actual.reindex(m), axis=0)
    df = pd.DataFrame({
        "MAE mot utfall": d_out.abs().mean(),
        "MAE mot snabb-KPI": d_flash.abs().mean(),
        "Medel prognos − snabb": d_flash.mean(),
        "Andel inom ±0,1 av snabb": (d_flash.abs() <= 0.1 + 1e-9).mean(),
    })
    err = (flash - actual).reindex(m)
    df.loc["snabb_kpi"] = [err.abs().mean(), 0.0, 0.0, 1.0]
    meta = {"n": len(m), "first": str(m.min()), "last": str(m.max()), "flash_mean_err": float(err.mean()),
            "flash_n_nonzero": int((err.abs() > 1e-9).sum()), "flash_max_abs": float(err.abs().max())}
    if flash_err is not None:
        fe = flash_err.reindex(m).dropna()
        if len(fe):
            meta.update({"first_pub_n": len(fe), "first_pub_mae": float(fe.abs().mean()),
                         "first_pub_n_nonzero": int((fe.abs() > 1e-9).sum()),
                         "first_pub_max_abs": float(fe.abs().max())})
    return df, meta


def flash_lines(df: pd.DataFrame, meta: dict) -> list[str]:
    if not meta.get("n"):
        return ["", "### Snabb-KPI som referens", "", "Ingen månad med både snabb-KPI, utfall och backtestprognos."]
    shown = df.copy()
    for c in ["MAE mot utfall", "MAE mot snabb-KPI", "Medel prognos − snabb"]:
        shown[c] = shown[c].map(lambda v: f"{v:+.3f}" if c.startswith("Medel") else f"{v:.3f}")
    shown["Andel inom ±0,1 av snabb"] = shown["Andel inom ±0,1 av snabb"].map(lambda v: f"{v:.0%}")
    return [
        "",
        "### Snabb-KPI som referens",
        "",
        f"SCB:s snabb-KPI (KPIF årstakt, en decimal) mot backtestprognoserna, samma månader för alla "
        f"({meta['first']}..{meta['last']}, n = {meta['n']}). Beskrivande, inga tester. Alla rader, snabb-KPI "
        f"inräknad, mäts mot samma utfall (yy_official). Snabb-KPI:s fel mot det: {meta['flash_n_nonzero']} av "
        f"{meta['n']} månader ≠ 0, högst {meta['flash_max_abs']:.1f} pe, medel {meta['flash_mean_err']:+.3f} pe."
        + (f" Mot först publicerat utfall (1987=100 före 2026-01): {meta['first_pub_n_nonzero']} av "
           f"{meta['first_pub_n']} månader ≠ 0, MAE {meta['first_pub_mae']:.3f}, högst "
           f"{meta['first_pub_max_abs']:.1f} pe." if meta.get("first_pub_n") else ""),
        "",
        shown.reset_index(names="Modell").to_markdown(index=False),
        "",
        "- Perioden ingår i 2024–26, som redan är använd: urvalsevidens, väljs inte på. Prognoserna har två decimaler, "
        "snabb-KPI en.",
    ]


def section(inp: Inputs | None = None, flash: tuple[pd.Series, pd.Series] | None = None) -> list[str]:
    if inp is None:
        from kpif_nowcast.data import load_components, load_kpif, load_riksbank_forecasts
        from kpif_nowcast.features import load_features

        inp = Inputs(load_kpif(), load_components(), load_features(), load_riksbank_forecasts())
    hist = histories(inp)
    df, m = table(inp, hist=hist)
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
    ] + _flash_part(hist, inp, flash)


def _flash_part(hist: pd.DataFrame, inp: Inputs, flash: tuple[pd.Series, pd.Series] | None) -> list[str]:
    try:  # the flash reference must never stop the champion table
        fl, err = load_flash() if flash is None else flash
        return flash_lines(*flash_reference(hist, inp.kpif["yy_official"], fl, err))
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: flash reference skipped: {type(exc).__name__}: {exc}")
        return []
