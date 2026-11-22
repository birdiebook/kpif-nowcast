"""Build the processed datasets used by models and backtests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from kpif_nowcast.sources import riksbank, scb

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

KPIF_CODES = {"000007ZN": "index", "000007ZO": "mm_official", "000007ZM": "yy_official"}


def build_kpif() -> pd.DataFrame:
    """Monthly KPIF: index (2020=100) plus SCB's official m/m and y/y (one decimal)."""
    long = scb.fetch_table("TAB6590")
    long["series"] = long["ContentsCode"].map(KPIF_CODES)
    wide = long.pivot(index="Tid", columns="series", values="value")
    wide.index = scb.month_to_period(wide.index.to_series())
    wide = wide.sort_index().astype(float)
    wide.index.name = "month"
    return wide[["index", "mm_official", "yy_official"]]


COMPONENTS = {
    "TXKS": "services",
    "KS": "capital_stock",
    "LIVS": "food",
    "NRG": "energy",
    "VXLIVSNRG": "goods",
}
COMPONENT_CODES = {
    "0000084S": "index",
    "0000084V": "mm_official",
    "0000084W": "weight",  # year-to-month weight (per mille), fixed within a calendar year
    "0000084R": "effect_month",  # contribution to KPIF's monthly change, pp
}


def build_components() -> pd.DataFrame:
    """KPIF analysis groups (TAB6628), long format: month, component, index, mm, weight, effect."""
    long = scb.fetch_table(
        "TAB6628",
        {"VaruTjanstegrupp": ",".join(COMPONENTS), "ContentsCode": ",".join(COMPONENT_CODES), "Tid": "*"},
    )
    long["component"] = long["VaruTjanstegrupp"].map(COMPONENTS)
    long["series"] = long["ContentsCode"].map(COMPONENT_CODES)
    wide = long.pivot_table(index=["Tid", "component"], columns="series", values="value").reset_index()
    wide["month"] = scb.month_to_period(wide["Tid"])
    return wide.drop(columns="Tid").sort_values(["component", "month"])[
        ["month", "component", "index", "mm_official", "weight", "effect_month"]
    ]


def build_tax_effects() -> pd.DataFrame:
    """Mechanical effect of tax/subsidy changes on KPIF's monthly change, in pp.

    tax_total  = KPIF m/m - KPIF-KS m/m (KPIF at constant taxes, TAB6592)
    tax_xe     = KPIF-XE m/m - KPIF-XE-KS m/m (excl. energy; TAB6593 vs TAB6746)
    Tax changes are decided in advance (budget), so the mechanical effect for month t
    is treated as known at the forecast deadline. ASSUMPTION: full pass-through, as in SCB's KS method.
    """
    ks = scb.fetch_table("TAB6592", {"ContentsCode": "000007ZT", "Tid": "*"})
    xe = scb.fetch_table("TAB6593", {"ContentsCode": "*", "Tid": "*"})
    xe_ks = scb.fetch_table("TAB6746", {"Analysmatt": "KPIF-XE-KS", "ContentsCode": "000008F6", "Tid": "*"})

    def series(df: pd.DataFrame, code_col: str | None = None, code: str | None = None) -> pd.Series:
        if code_col:
            df = df[df[code_col] == code]
        s = pd.Series(df["value"].to_numpy(dtype=float), index=scb.month_to_period(df["Tid"]))
        return s.sort_index()

    kpif = load_kpif()["index"]
    xe_index_code = xe["ContentsCode"].iloc[0]  # first content code is the index
    out = pd.DataFrame(
        {
            "kpif": kpif,
            "kpif_ks": series(ks),
            "kpif_xe": series(xe, "ContentsCode", xe_index_code),
            "kpif_xe_ks": series(xe_ks),
        }
    )
    mm = lambda s: (s / s.shift(1) - 1) * 100  # noqa: E731
    out["tax_total"] = mm(out["kpif"]) - mm(out["kpif_ks"])
    out["tax_xe_own"] = mm(out["kpif_xe"]) - mm(out["kpif_xe_ks"])
    out.index.name = "month"
    return out


def load_tax_effects() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "tax_effects.csv")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    return df.set_index("month")


def load_components() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "components.csv")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    return df


def build_riksbank_forecasts() -> pd.DataFrame:
    return riksbank.fetch_forecasts("SEMCPIFNAYNA")


def refresh() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    kpif = build_kpif()
    kpif.to_csv(PROCESSED_DIR / "kpif.csv")
    comp = build_components()
    comp.to_csv(PROCESSED_DIR / "components.csv", index=False)
    print(f"Components: {sorted(comp['component'].unique())}, {comp['month'].min()}..{comp['month'].max()}")
    build_tax_effects().to_csv(PROCESSED_DIR / "tax_effects.csv")
    rb = build_riksbank_forecasts()
    rb.to_csv(PROCESSED_DIR / "riksbank_kpif_forecasts.csv", index=False)
    print(f"KPIF: {kpif.index.min()}..{kpif.index.max()} ({len(kpif)} months)")
    print(f"Riksbank: {rb['policy_round'].nunique()} vintages, {rb['policy_round'].min()}..{rb['policy_round'].max()}")


def load_kpif() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "kpif.csv")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    return df.set_index("month")


def load_riksbank_forecasts() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "riksbank_kpif_forecasts.csv")
    df["cutoff"] = pd.PeriodIndex(df["cutoff"], freq="M")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    df["published"] = pd.to_datetime(df["published"])
    return df


# --- Detail tables (not used by the models yet; collected for later phases) -------------------

DETAIL_CODES = {
    "0000083S": "index",
    "0000083V": "mm_official",
    "0000080M": "yy_official",
    "0000083W": "weight",  # year-to-month weight, per mille
    "0000080W": "effect_month",  # contribution to KPIF's monthly change, pp
}


def build_cpif_detail() -> pd.DataFrame:
    """KPIF per COICOP 2018 code, all levels (TAB6613), long format.

    ~400 codes x 5 measures x ~480 months, fetched 15 codes per call. NOTE: values before 2026
    are SCB's back-calculation to COICOP 2018 (partly model estimated) - they were not what
    was published at the time. See docs/datakallor.md.
    """
    long = scb.fetch_table_chunked(
        "TAB6613", "VaruTjanstegrupp", {"ContentsCode": ",".join(DETAIL_CODES), "Tid": "*"}, chunk_size=15
    )
    labels = scb.fetch_metadata("TAB6613")["dimension"]["VaruTjanstegrupp"]["category"]["label"]
    long["series"] = long["ContentsCode"].map(DETAIL_CODES)
    wide = long.pivot_table(index=["Tid", "VaruTjanstegrupp"], columns="series", values="value").reset_index()
    wide["month"] = scb.month_to_period(wide["Tid"])
    wide = wide.rename(columns={"VaruTjanstegrupp": "coicop"})
    wide["label"] = wide["coicop"].map(labels)
    wide["level"] = wide["coicop"].map(lambda c: 0 if c == "00" else c.count(".") + 1)
    cols = ["month", "coicop", "level", "label", *DETAIL_CODES.values()]
    return wide.sort_values(["coicop", "month"])[cols]


def build_el_contracts() -> pd.DataFrame:
    """Share of electricity contract types per bidding zone, % (TAB3571), long format.

    Month m is published around the 23rd of m+1. At the deadline for target t (day 4 of t+1)
    the latest known month is therefore t-1 (out ~the 23rd of t); month t itself is not known.
    """
    long = scb.fetch_table("TAB3571", {"Elomrade": "*", "Avtalstyp": "*", "ContentsCode": "*", "Tid": "*"})
    long["month"] = scb.month_to_period(long["Tid"])
    out = long.rename(columns={"Elomrade": "zone", "Avtalstyp": "contract", "value": "share"})
    return out.sort_values(["zone", "contract", "month"])[["month", "zone", "contract", "share"]]


def build_el_grid_prices() -> pd.DataFrame:
    """Electricity grid prices as of 1 January, ore/kWh excl. taxes (TAB3950).

    Customer categories: 1 flat, 2 house without electric heating, 3 house with electric
    heating, 4 large house. 'viktat' (weighted by connection points) only from 2015.
    """
    long = scb.fetch_table("TAB3950", {"Kundkategori": "*", "Viktat": "*", "ContentsCode": "*", "Tid": "*"})
    out = long.rename(
        columns={"Tid": "year", "Kundkategori": "customer", "Viktat": "weighting", "value": "ore_per_kwh"}
    )
    out["year"] = out["year"].astype(int)
    return out.sort_values(["customer", "weighting", "year"])[["year", "customer", "weighting", "ore_per_kwh"]]


def refresh_detail() -> None:
    """Fetch the detail tables. Separate from refresh() so the live forecast stays fast."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    detail = build_cpif_detail()
    detail.to_csv(PROCESSED_DIR / "cpif_detail.csv", index=False)
    print(f"CPIF detail: {detail['coicop'].nunique()} codes, {detail['month'].min()}..{detail['month'].max()}")
    contracts = build_el_contracts()
    contracts.to_csv(PROCESSED_DIR / "el_contracts.csv", index=False)
    print(f"El contracts: {contracts['month'].min()}..{contracts['month'].max()}")
    grid = build_el_grid_prices()
    grid.to_csv(PROCESSED_DIR / "el_grid_prices.csv", index=False)
    print(f"El grid prices: {grid['year'].min()}..{grid['year'].max()}")


def load_cpif_detail() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "cpif_detail.csv", dtype={"coicop": str})
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    return df


def load_el_contracts() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "el_contracts.csv")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    return df


def load_el_grid_prices() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "el_grid_prices.csv", dtype={"customer": str})


if __name__ == "__main__":
    refresh()
    refresh_detail()
