"""K10: the GitHub Pages build writes every dataset the Sverigeläget page reads, and the shell wires up the shim."""

from __future__ import annotations

import json
import re

import pytest

from kpif_nowcast import observations as obs
from kpif_nowcast import pages
from kpif_nowcast import sverige_dashboard as sd
from kpif_nowcast.data import PROCESSED_DIR

needs_data = pytest.mark.skipif(not obs.PATH.exists() or not (PROCESSED_DIR / "features.csv").exists(),
                                reason="data/observations.parquet or data/processed missing")


def test_page_datasets_are_dashboard_datasets():
    need, calcs = pages.page_datasets()
    assert calcs == {"area_now", "prisled_now", "af_now"}
    assert need == set(sd.DATASETS), need ^ set(sd.DATASETS)


def test_page_datasets_parser_sees_every_access_pattern():
    html = ('dash.calc("c", {inputs: ["a"], fn: () => []}); dash.data("b"); rows("d"); failed(el, ["e", "f"], "x");'
            ' mini(el, [], { src: "g" }); const d = dash.data(opts.src || "h"); <div data-source="i c">')
    need, calcs = pages.page_datasets(html)
    assert need == set("abdefghi") and calcs == {"c"}


def test_build_site_from_fake_datasets(tmp_path):
    src, site = tmp_path / "src", tmp_path / "site"
    src.mkdir()
    code = {"label": "sverige_dashboard.py", "value": "print(1)", "type": "code"}
    for name in sd.DATASETS:
        (src / f"{name}.json").write_text(json.dumps({"rows": [{"x": 1}], "meta": [code, {"label": "Input", "value": "v"}]}),
                                          encoding="utf-8")
    rec = pages.build_site(src, site)
    assert rec["missing"] == [] and set(rec["datasets"]) == set(sd.DATASETS)
    for name in sd.DATASETS:
        payload = json.loads((site / "data" / f"{name}.json").read_text(encoding="utf-8"))
        assert payload["rows"] == [{"x": 1}]
        assert all(m.get("type") != "code" for m in payload["meta"])  # no embedded source in the public files
    html = (site / "index.html").read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>") and '<meta name="viewport"' in html
    assert pages.D3_URL in html and re.search(r"/d3/\d+\.\d+\.\d+/d3\.min\.js", pages.D3_URL)
    assert html.index(pages.D3_URL) < html.index('src="dash-shim.js"') < html.index("dash.calc(")
    assert not any(p in html for p in ["__PAGE__", "__D3_URL__", "__D3_SRI__", "__BUILT_AT__"])
    assert "prefers-color-scheme: dark" in html and "dash-one-writer" not in html
    assert (site / "dash-shim.js").read_text(encoding="utf-8") == pages.SHIM.read_text(encoding="utf-8")
    # rebuilding with a dataset missing lists it instead of failing
    (src / "region.json").unlink()
    assert pages.build_site(src, site)["missing"] == ["region"]
    assert not (site / "data" / "region.json").exists()


def test_shim_implements_what_the_page_uses():
    html = pages.PAGE.read_text(encoding="utf-8")
    used = set(re.findall(r"\bdash\.(\w+)", html))
    shim = pages.SHIM.read_text(encoding="utf-8")
    exported = set(re.search(r"window\.dash = \{([^}]*)\}", shim).group(1).replace(" ", "").split(","))
    assert used <= exported, used - exported


@needs_data
def test_site_build_writes_every_dataset_the_page_reads(tmp_path):
    rec = pages.main(site_dir=tmp_path / "site", out_dir=tmp_path / "out", with_k2=False)
    need, _ = pages.page_datasets()
    assert rec["missing"] == [] and rec["failed_sections"] == []
    for name in need:
        rows = json.loads((tmp_path / "site" / "data" / f"{name}.json").read_text(encoding="utf-8"))["rows"]
        assert len(rows) > 0, name
