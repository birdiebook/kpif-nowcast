"""Shared evaluation: error metrics, one Diebold-Mariano test, and a run log.

Deliberately small. No bootstrap, no reality check. Statistics use numpy only.

Diebold-Mariano (DM) asks: is the average loss difference between two forecasts
on the same months different from zero, given that the monthly differences are
noisy and autocorrelated? Choices, fixed once so they cannot be tuned per result:

- loss = absolute error (MAE is our main metric)
- long-run variance by Newey-West (Bartlett weights), lag = floor(4 * (n/100)^(2/9)).
  Nowcast misses are persistent (a missed energy shock lingers), so lag 0 would
  overstate precision. n=34 gives lag 3, n=141 gives lag 4.
- Harvey-Leybourne-Newbold small-sample correction for horizon h=1, p-value from
  Student's t with n-1 degrees of freedom.

Minimum detectable difference (MDE): the MAE gap a two-sided test at 5 % would
find 80 % of the time with this sample's noise, approx. (1.96 + 0.84) * SE.
"""

from __future__ import annotations

import csv
import math
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO / "experiments" / "runs"
RUN_COLUMNS = ["utc", "git_sha", "variant", "period", "n", "MAE", "dm_p_vs_rb_updated"]
MDE_FACTOR = 1.96 + 0.84  # 5 % two-sided, 80 % power, normal approximation


def metrics(errors) -> dict[str, float]:
    e = np.asarray(errors, dtype=float)
    e = e[~np.isnan(e)]
    return {
        "MAE": float(np.mean(np.abs(e))),
        "RMSE": float(np.sqrt(np.mean(e**2))),
        "bias": float(np.mean(e)),
        "n": len(e),
    }


def newey_west_lag(n: int) -> int:
    return int(math.floor(4 * (n / 100) ** (2 / 9)))


def long_run_variance(d: np.ndarray, lag: int) -> float:
    """Newey-West variance of the mean's numerator: gamma_0 + 2 * sum_k w_k * gamma_k, w_k = 1 - k/(lag+1)."""
    d = d - d.mean()
    n = len(d)
    lrv = d @ d / n
    for k in range(1, lag + 1):
        lrv += 2 * (1 - k / (lag + 1)) * (d[k:] @ d[:-k]) / n
    return float(lrv)


@dataclass
class DMResult:
    n: int
    lag: int
    mean_diff: float  # MAE(a) - MAE(b); negative = a is better
    se: float  # standard error of mean_diff, HLN-corrected
    stat: float
    p: float
    mde: float  # minimum detectable |mean_diff|

    def sentence(self, a: str, b: str) -> str:
        better = a if self.mean_diff < 0 else b
        return (
            f"{a} vs {b}: MAE diff {self.mean_diff:+.3f} pp ({better} better), DM p={self.p:.2f}, n={self.n}. "
            f"With this noise only differences of about {self.mde:.2f} pp or more are detectable."
        )


def dm_test(errors_a, errors_b, h: int = 1) -> DMResult:
    """DM test on absolute-error loss. Months where either error is missing are dropped."""
    ea, eb = np.asarray(errors_a, dtype=float), np.asarray(errors_b, dtype=float)
    ok = ~(np.isnan(ea) | np.isnan(eb))
    d = np.abs(ea[ok]) - np.abs(eb[ok])
    n = len(d)
    lag = newey_west_lag(n)
    hln = math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    se = math.sqrt(max(long_run_variance(d, lag), 0.0) / n) / hln
    mean = float(d.mean())
    if se == 0:
        return DMResult(n, lag, mean, 0.0, float("nan"), float("nan"), 0.0)
    stat = mean / se
    return DMResult(n, lag, mean, se, stat, t_two_sided_p(stat, n - 1), MDE_FACTOR * se)


def t_two_sided_p(t: float, df: int) -> float:
    """P(|T| > |t|) for Student's t: the regularized incomplete beta I_x(df/2, 1/2), x = df/(df+t^2)."""
    return _betainc(df / 2, 0.5, df / (df + t * t))


def _betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function (continued fraction, Numerical Recipes 6.4)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    if x > (a + 1) / (a + b + 2):  # the continued fraction converges fast only below this point
        return 1.0 - _betainc(b, a, 1 - x)
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    tiny = 1e-300
    c, d = 1.0, 1.0 - (a + b) * x / (a + 1)
    d = 1.0 / (d if abs(d) > tiny else tiny)
    f = d
    for m in range(1, 300):
        for num in (m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m)),
                    -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))):
            d = 1.0 + num * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + num / c
            c = c if abs(c) > tiny else tiny
            f *= c * d
        if abs(c * d - 1.0) < 1e-14:
            break
    return front * f / a


def git_sha() -> str:
    """Short commit hash, with '+dirty' if tracked files have uncommitted changes."""
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "-uno"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        return sha + ("+dirty" if dirty else "")
    except OSError:
        return "unknown"


def log_run(name: str, rows: list[dict]) -> Path:
    """Write one CSV per run: experiments/runs/<utc>_<name>.csv. One file per run, so parallel tracks never collide."""
    now = datetime.now(timezone.utc)
    utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    sha = git_sha()
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{now.strftime('%Y%m%dT%H%M%SZ')}_{name}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RUN_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({"utc": utc, "git_sha": sha, **r})
    return path
