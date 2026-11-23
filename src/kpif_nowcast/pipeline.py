"""The steps the GitHub Actions workflows run, as one command per job so they run the same locally.

    python -m kpif_nowcast.pipeline weekly   [--offline]   # Sunday: fetch everything + data tests
    python -m kpif_nowcast.pipeline monthly  [--offline]   # day 1-4: fetch forecast inputs (+ K2 series), shadows, scorecard, explain, letter
    python -m kpif_nowcast.pipeline manadsbrev [--month YYYY-MM]  # K5: docs/manadsbrev/<month>.md
    python -m kpif_nowcast.pipeline explain  [--offline]   # K3: explanations to outputs/explain/ (not committed)
    python -m kpif_nowcast.pipeline fetch    [--offline] [--no-observations]
    python -m kpif_nowcast.pipeline shadow   [--offline] [--as-of YYYY-MM-DD] [--force]
    python -m kpif_nowcast.pipeline check                  # data tests (pytest, DuckDB)
    python -m kpif_nowcast.pipeline scorecard
    python -m kpif_nowcast.pipeline prune --keep 4         # CI cache: drop older raw responses
    python -m kpif_nowcast.pipeline site     [--offline]   # K10: Sverigeläget as a static site in site/ (GitHub Pages)

--offline (or KPIF_OFFLINE=1): every source reads its latest saved raw response in data/raw/ and any
other network call fails. Used to rebuild everything from a raw cache and to run the workflow
steps locally without touching the APIs.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def go_offline() -> None:
    from kpif_nowcast.sources import rawcache

    os.environ[rawcache.ENV] = "1"
    rawcache.block_network()


def fetch(observations: bool = True) -> None:
    """Refresh processed data and features (fatal on failure), then the observation table (per-series)."""
    from kpif_nowcast import data, features
    from kpif_nowcast.sources import elpris, energinet, rawcache

    print("== processed KPIF, components, tax effects, Riksbank forecasts", flush=True)
    data.refresh()
    print("== electricity: Energinet history (cached chunks kept) and elprisetjustnu.se days", flush=True)
    energinet.fetch_all(fetch_missing=not rawcache.offline())
    for zone in features.ZONE_WEIGHTS:
        s = elpris.daily_prices(zone)
        print(f"   {zone}: {s.index.min().date()}..{s.index.max().date()} ({len(s)} days)")
    print("== features", flush=True)
    features.refresh()
    if observations:
        from kpif_nowcast import observations as obs

        if rawcache.offline() and obs.PATH.exists():
            # replaying old raw files into an existing vintage table would only add fake revisions
            print("== observation table: offline, existing table kept as is", flush=True)
            return
        print("== observation table (one failing series does not stop the rest)", flush=True)

        status = obs.refresh()
        failed = [k for k, v in status.items() if v.startswith("FAILED")]
        print(f"   {len(status) - len(failed)} ok, {len(failed)} failed: {failed}")


def fetch_shadow_observations() -> None:
    """Monthly: refresh the observation-table series the K2 shadow models read (euro-area flash and
    K2's 43 catalog series), so that releases since Sunday's weekly fetch (the flash comes at the end
    of the month or on days 1-3) are in the table. Offline: the existing table is kept as is."""
    from kpif_nowcast import observations as obs
    from kpif_nowcast.k2_ml import K2_CATALOG_KEYS
    from kpif_nowcast.k2b_review import FLASH
    from kpif_nowcast.sources import rawcache

    if rawcache.offline() and obs.PATH.exists():
        print("== K2 observation series: offline, existing table kept as is", flush=True)
        return
    print("== K2 observation series (flash + 43 catalog series)", flush=True)
    status = obs.refresh(sorted(set(K2_CATALOG_KEYS) | set(FLASH)))
    failed = [k for k, v in status.items() if v.startswith("FAILED")]
    print(f"   {len(status) - len(failed)} ok, {len(failed)} failed: {failed}")


def check() -> None:
    """Data tests on observations.parquet (DuckDB) and the processed files."""
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_data_quality.py"], cwd=REPO, env=env)
    if r.returncode:
        raise SystemExit(f"data tests failed (exit {r.returncode})")


def shadow(as_of: str | None = None, force: bool = False) -> None:
    from kpif_nowcast import shadow as shadow_mod

    shadow_mod.run(as_of, force)


def explain(strict: bool = True) -> None:
    """K3 explanations of the live forecast (last 24 months + target) to outputs/explain/. Writes no committed file.

    In `monthly` it is not fatal: a failure here must not stop the shadow forecasts from being committed.
    """
    from kpif_nowcast import explain as explain_mod

    try:
        explain_mod.run(months=24)
    except Exception as exc:
        if strict:
            raise
        print(f"WARNING: explanation failed, shadows and scorecard unaffected: {exc!r}", flush=True)


def manadsbrev(month: str | None = None, strict: bool = True) -> None:
    """K5 monthly letter docs/manadsbrev/<month>.md (default: the next unpublished month).

    In `monthly` it is not fatal: the shadow forecasts and the scorecard are committed regardless.
    """
    from kpif_nowcast import manadsbrev as mb

    try:
        mb.write(month or str(mb.default_month()))
    except Exception as exc:
        if strict:
            raise
        print(f"WARNING: monthly letter failed, shadows and scorecard unaffected: {exc!r}", flush=True)


def scorecard() -> None:
    from kpif_nowcast import scorecard as sc

    sc.main()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["weekly", "monthly", "fetch", "shadow", "check", "scorecard", "explain", "manadsbrev", "prune", "site"])
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--no-observations", action="store_true", help="fetch: skip the observation table")
    parser.add_argument("--as-of", help="shadow: date for FINAL/PRELIMINARY/LATE (default today)")
    parser.add_argument("--force", action="store_true", help="shadow: overwrite FINAL files")
    parser.add_argument("--month", help="manadsbrev: target month YYYY-MM (default: next unpublished month)")
    parser.add_argument("--keep", type=int, default=4, help="prune: dated versions to keep per raw response")
    args = parser.parse_args(argv)
    if args.offline or os.environ.get("KPIF_OFFLINE", "") not in ("", "0"):
        go_offline()

    if args.command == "weekly":
        fetch(observations=True)
        check()
    elif args.command == "monthly":
        fetch(observations=False)
        fetch_shadow_observations()
        shadow(args.as_of, args.force)
        scorecard()
        explain(strict=False)
        manadsbrev(strict=False)
    elif args.command == "manadsbrev":
        manadsbrev(args.month)
    elif args.command == "explain":
        explain()
    elif args.command == "fetch":
        fetch(observations=not args.no_observations)
    elif args.command == "shadow":
        shadow(args.as_of, args.force)
    elif args.command == "check":
        check()
    elif args.command == "scorecard":
        scorecard()
    elif args.command == "site":
        from kpif_nowcast import pages

        record = pages.main()
        if not record["datasets"]:
            raise SystemExit("site: no dataset written")
    elif args.command == "prune":
        from kpif_nowcast.sources import rawcache
        from kpif_nowcast.sources.scb import RAW_DIR

        removed = rawcache.prune(RAW_DIR, max(args.keep, 1))
        print(f"pruned {len(removed)} old raw files")


if __name__ == "__main__":
    main()
