"""K10: build Sverigeläget as a static site for GitHub Pages.

Run: python -m kpif_nowcast.pipeline site [--offline]

The same page as in Claude Data (templates/sverige_index.html) is wrapped in a standalone HTML shell
(templates/site_shell.html: design tokens for light and dark mode, d3 from cdnjs, dash-shim.js). The shim
implements the parts of the Claude Data `dash` API the page uses and reads data/<id>.json with fetch.

site/                    (gitignored, built in CI by .github/workflows/pages.yml)
  index.html             shell + page
  dash-shim.js
  data/<id>.json         {"rows": [...], "meta": [...]} as written by sverige_dashboard, without the embedded
                         source code (the meta links to the repository instead)
  data/build.json        build time and which datasets were written / missing
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "site"
TEMPLATES = Path(__file__).with_name("templates")
PAGE = TEMPLATES / "sverige_index.html"
SHELL = TEMPLATES / "site_shell.html"
SHIM = TEMPLATES / "dash-shim.js"

D3_URL = "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"
D3_SRI = "sha512-vc58qvvBdrDR4etbxMdlTt4GBQk1qjvyORR2nrsPsFPyrs+/u5c3+1Ct6upOgdZoIl7eq6k3a1UPDSNAQi/32A=="


def page_datasets(html: str | None = None) -> tuple[set[str], set[str]]:
    """(file datasets, calcs) the page reads. File datasets are what the build must write.

    Collected from every way the page names a dataset: dash.data("x"), its helper rows("x"), failed(el, [..]),
    mini(..., {src: "x"}) (default "ai"), calc inputs, and data-source attributes; minus the dash.calc ids.
    """
    html = PAGE.read_text(encoding="utf-8") if html is None else html
    calcs = set(re.findall(r'dash\.calc\(\s*"([\w-]+)"', html))
    ids = set(re.findall(r'dash\.data\(\s*"([\w-]+)"\s*\)', html))
    ids |= set(re.findall(r'\brows\(\s*"([\w-]+)"\s*\)', html))
    ids |= set(re.findall(r'\bsrc:\s*"([\w-]+)"', html))
    ids |= set(re.findall(r'opts\.src\s*\|\|\s*"([\w-]+)"', html))
    for group in re.findall(r'(?:inputs:|failed\(\s*el,)\s*\[([^\]]*)\]', html):
        ids |= set(re.findall(r'"([\w-]+)"', group))
    for attr in re.findall(r'data-source="([^"]+)"', html):
        ids |= set(attr.split())
    return ids - calcs, calcs


def shell_html(built_at: str) -> str:
    page = PAGE.read_text(encoding="utf-8")
    page = page.replace('<meta name="dash-one-writer">', "", 1)  # Claude Data hint, meaningless here
    out = SHELL.read_text(encoding="utf-8")
    for k, v in {"__D3_URL__": D3_URL, "__D3_SRI__": D3_SRI, "__BUILT_AT__": built_at}.items():
        out = out.replace(k, v)
    return out.replace("__PAGE__", page.strip())


def build_site(src_dir: Path, site_dir: Path = SITE_DIR) -> dict:
    """Write site_dir from the dashboard JSON files in src_dir. Returns the build record (also data/build.json).

    Only datasets the page reads are published. Missing ones are listed (the page then shows "kunde inte
    laddas" for that section) instead of failing the whole site.
    """
    need, _ = page_datasets()
    if site_dir.exists():  # empty it but keep the folder (on Windows it may be a running server's cwd)
        for p in site_dir.iterdir():
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    (site_dir / "data").mkdir(parents=True)
    written, missing = [], []
    for name in sorted(need):
        src = src_dir / f"{name}.json"
        if not src.exists():
            missing.append(name)
            continue
        payload = json.loads(src.read_text(encoding="utf-8"))
        payload["meta"] = [m for m in payload.get("meta", []) if m.get("type") != "code"]
        (site_dir / "data" / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                                                        encoding="utf-8")
        written.append(name)
    now = datetime.now(timezone.utc)
    built_at = now.astimezone().strftime("%Y-%m-%d %H:%M") + " (" + now.strftime("%H:%M UTC") + ")"
    (site_dir / "index.html").write_text(shell_html(built_at), encoding="utf-8")
    shutil.copyfile(SHIM, site_dir / "dash-shim.js")
    (site_dir / ".nojekyll").write_text("", encoding="utf-8")
    record = {"built_at": now.isoformat(timespec="seconds"), "datasets": written, "missing": missing}
    (site_dir / "data" / "build.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  site: {site_dir} ({len(written)} datasets" + (f", MISSING {missing}" if missing else "") + ")")
    return record


def main(site_dir: Path = SITE_DIR, out_dir: Path | None = None, with_k2: bool = True) -> dict:
    """Regenerate the dashboard datasets (sverige_dashboard) and build the site from them."""
    from kpif_nowcast import sverige_dashboard as sd

    out_dir = sd.OUT_DIR if out_dir is None else out_dir
    failed = sd.main(out_dir=out_dir, with_k2=with_k2)
    record = build_site(out_dir, site_dir)
    record["failed_sections"] = failed
    return record


if __name__ == "__main__":
    main()
