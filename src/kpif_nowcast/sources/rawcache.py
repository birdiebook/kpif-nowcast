"""Offline mode: replay saved raw responses instead of calling the APIs.

Every source client saves its raw response under data/raw/ as `<name>_<YYYYMMDD>.<ext>`.
With the environment variable KPIF_OFFLINE=1 the clients read the latest saved file for the
same request instead of calling the API, and `block_network()` makes any other HTTP call fail
loudly. This lets the whole chain (processed data, features, shadow forecasts) be rebuilt
from a copy of data/raw/ alone, so a run can be reproduced exactly.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import requests

ENV = "KPIF_OFFLINE"


class OfflineError(RuntimeError):
    """Raised when offline mode needs a raw file that is not in the cache, or code tries the network."""


def offline() -> bool:
    return os.environ.get(ENV, "") not in ("", "0", "false", "False")


def latest(raw_dir: Path, name: str, ext: str) -> Path | None:
    """Newest `<name>_<YYYYMMDD><ext>` in raw_dir (exact name match, not a prefix match)."""
    pattern = re.compile(re.escape(name) + r"_(\d{8})" + re.escape(ext) + "$")
    hits = sorted((m.group(1), p) for p in raw_dir.glob(f"{name}_*{ext}") if (m := pattern.match(p.name)))
    return hits[-1][1] if hits else None


def require(raw_dir: Path, *names: str, ext: str = ".json") -> Path:
    """First name (in order of preference) that has a cached file; OfflineError if none."""
    for name in names:
        path = latest(raw_dir, name, ext)
        if path is not None:
            return path
    raise OfflineError(f"offline: no cached raw file for {names[0]}{ext} in {raw_dir}")


_original_request = requests.Session.request


def block_network() -> None:
    """Make every requests call raise OfflineError (sources with a cache never get here)."""

    def _blocked(self, method, url, *args, **kwargs):  # noqa: ANN001
        raise OfflineError(f"offline: network call blocked ({method} {url})")

    requests.Session.request = _blocked


def unblock_network() -> None:
    requests.Session.request = _original_request
