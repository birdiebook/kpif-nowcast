"""Compare logged live forecasts with SCB's outcomes -> forecasts/SCORECARD.md.

Also appends the champion/challenger table for the shadow models (champion.py), and (L9) SCB's flash
estimate (Snabb-KPI) as a reference: for each live month with a flash, the flash's own error against the outcome
and our forecast against the flash. Descriptive, no tests.

Run after each SCB release: python -m kpif_nowcast.scorecard
"""

from __future__ import annotations

import json

import pandas as pd

from kpif_nowcast.data import load_kpif
from kpif_nowcast.forecast import FORECAST_DIR


def flash_live_lines(live: pd.DataFrame, flash: pd.Series, flash_err: pd.Series | None = None) -> list[str]:
    """Live forecasts against Snabb-KPI. `live`: columns month (Period), forecast_yy, outcome (NaN if not out)."""
    lines = ["## Snabb-KPI som referens", "",
             "SCB:s snabb-KPI (KPIF årstakt, en decimal) kommer cirka en vecka före utfallet. Beskrivande: hur nära "
             "SCB:s egen tidiga siffra prognosen kommer, och hur nära utfallet snabb-KPI kommer.", ""]
    rows = []
    for r in live.itertuples():
        f = flash.get(r.month)
        if f is None or pd.isna(f):
            continue
        out = None if r.outcome is None or pd.isna(r.outcome) else float(r.outcome)
        e = None if flash_err is None else flash_err.get(r.month)
        if (e is None or pd.isna(e)) and out is not None:
            e = round(float(f) - out, 2)
        rows.append({"Månad": str(r.month), "Prognos": round(float(r.forecast_yy), 2), "Snabb-KPI": float(f),
                     "Prognos − snabb": round(float(r.forecast_yy) - float(f), 2), "Utfall": out,
                     "Snabb − utfall": None if e is None or pd.isna(e) else round(float(e), 2),
                     "Prognos − utfall": None if out is None else round(float(r.forecast_yy) - out, 2)})
    if rows:
        lines.append(pd.DataFrame(rows).to_markdown(index=False))
    else:
        lines.append("_Snabb-KPI finns ännu inte för någon månad med skarp prognos._")
    return lines + [""]


def main() -> None:
    kpif = load_kpif()
    rows, live = [], []
    for path in sorted(FORECAST_DIR.glob("*.json")):
        f = json.loads(path.read_text(encoding="utf-8"))
        month = pd.Period(f["target_month"], "M")
        outcome = kpif["yy_official"].get(month)
        rb = f["riksbank"]["forecast_yy"]
        live.append({"month": month, "forecast_yy": f["forecast_yy"], "outcome": outcome})
        rows.append(
            {
                "Månad": f["target_month"],
                "Status": f["status"],
                "Prognos": f["forecast_yy_rounded"],
                "80%-intervall": f"{f['range_80'][0]}–{f['range_80'][1]}",
                "Riksbanken": rb,
                "Utfall": outcome,
                "Fel": None if outcome is None else round(f["forecast_yy"] - outcome, 2),
                "Fel Riksbanken": None if outcome is None or rb is None else round(rb - outcome, 2),
                "Manuell just.": f["manual_adjustment_pp"] or "",
            }
        )
    df = pd.DataFrame(rows)
    done = df.dropna(subset=["Utfall"])
    lines = [
        "# Scorecard – skarpa prognoser",
        "",
        "Varje prognos committas före SCB:s snabb-KPI. Årstakt KPIF, procent.",
        "",
        df.to_markdown(index=False) if len(df) else "_Inga prognoser än._",
        "",
    ]
    if len(done):
        lines += [
            f"**Genomsnittligt absolut fel:** modellen {done['Fel'].abs().mean():.2f} pe, "
            f"Riksbanken {done['Fel Riksbanken'].abs().mean():.2f} pe ({len(done)} månader).",
        ]
    try:  # the flash reference must never stop the live scorecard from being written
        from kpif_nowcast.champion import load_flash

        lines += [""] + flash_live_lines(pd.DataFrame(live, columns=["month", "forecast_yy", "outcome"]), *load_flash())
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: flash reference skipped: {type(exc).__name__}: {exc}")
    try:  # the shadow table must never stop the live scorecard from being written
        from kpif_nowcast.champion import section

        lines += section()
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: champion/challenger table skipped: {type(exc).__name__}: {exc}")
    (FORECAST_DIR / "SCORECARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
