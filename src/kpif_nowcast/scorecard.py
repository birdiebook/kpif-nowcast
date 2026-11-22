"""Compare logged live forecasts with SCB's outcomes -> forecasts/SCORECARD.md.

Run after each SCB release: python -m kpif_nowcast.scorecard
"""

from __future__ import annotations

import json

import pandas as pd

from kpif_nowcast.data import load_kpif
from kpif_nowcast.forecast import FORECAST_DIR


def main() -> None:
    kpif = load_kpif()
    rows = []
    for path in sorted(FORECAST_DIR.glob("*.json")):
        f = json.loads(path.read_text(encoding="utf-8"))
        month = pd.Period(f["target_month"], "M")
        outcome = kpif["yy_official"].get(month)
        rb = f["riksbank"]["forecast_yy"]
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
    (FORECAST_DIR / "SCORECARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
