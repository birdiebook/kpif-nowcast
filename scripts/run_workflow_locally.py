"""Run the steps of the GitHub Actions workflows locally, in order (a small stand-in for `act`).

    python scripts/run_workflow_locally.py [weekly-fetch|monthly-shadow ...] [--online] [--as-of YYYY-MM-DD]

Reads .github/workflows/<name>.yml (or ci/workflows/), and runs every single-line `run:` step that is
a `python -m kpif_nowcast...` command, with this interpreter and PYTHONPATH=src. Skipped, and listed:
`uses:` steps (checkout, setup-python, cache, artifacts: the local data/ plays the cache), the pip
install (the local venv is used) and steps named "(CI only)" (git commit/push).

Default is offline (KPIF_OFFLINE=1): sources replay data/raw/ and the network is blocked, so a local
run never calls the APIs. --online fetches for real. --as-of is passed to the shadow step's status rule.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIRS = [REPO / ".github" / "workflows", REPO / "ci" / "workflows"]


def find(name: str) -> Path:
    for d in DIRS:
        if (d / f"{name}.yml").exists():
            return d / f"{name}.yml"
    raise SystemExit(f"workflow {name}.yml not found in {[str(d) for d in DIRS]}")


def steps(path: Path) -> list[tuple[str, str | None, str]]:
    """(step name, command or None, reason if skipped) in file order. Minimal parser for our own files."""
    out, name = [], None
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if m := re.match(r"\s*- (name|uses): (.*)", line):
            if m.group(1) == "uses":
                out.append((m.group(2), None, "uses: (CI action)"))
                name = None
            else:
                name = m.group(2)
                nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if nxt.startswith("uses:"):
                    out.append((name, None, "uses: (CI action)"))
                    name = None
        elif name and (m := re.match(r"\s*run: (.*)", line)):
            cmd = m.group(1).strip()
            if "(CI only)" in name:
                out.append((name, None, "CI only"))
            elif cmd == "|" or not cmd.startswith("python -m kpif_nowcast"):
                out.append((name, None, "not a pipeline command (local venv is used)"))
            else:
                out.append((name, cmd, ""))
            name = None
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("workflows", nargs="*", default=["weekly-fetch", "monthly-shadow"])
    ap.add_argument("--online", action="store_true", help="really fetch from the sources")
    ap.add_argument("--as-of", help="date for the shadow status rule (default today)")
    args = ap.parse_args()
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONIOENCODING": "utf-8"}
    if not args.online:
        env["KPIF_OFFLINE"] = "1"
    failed = False
    for wf in args.workflows:
        path = find(wf)
        print(f"\n######## {path.relative_to(REPO)} ({'online' if args.online else 'offline'})", flush=True)
        for name, cmd, skip in steps(path):
            if cmd is None:
                print(f"-- skip  {name}  [{skip}]")
                continue
            argv = [sys.executable, *cmd.split()[1:]]
            if args.as_of and (" monthly" in cmd or " shadow" in cmd):
                argv += ["--as-of", args.as_of]
            print(f"-- run   {name}: {' '.join(argv[1:])}", flush=True)
            t0 = time.time()
            r = subprocess.run(argv, cwd=REPO, env=env)
            print(f"-- {'ok' if r.returncode == 0 else f'FAILED ({r.returncode})'}  {time.time() - t0:.0f}s", flush=True)
            if r.returncode:
                failed = True
                break
    print("\nRESULT:", "FAILED" if failed else "GREEN")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
