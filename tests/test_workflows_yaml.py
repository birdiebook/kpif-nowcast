"""Every GitHub Actions workflow file must be valid YAML.

GitHub rejects an invalid workflow file at push time and never runs it (K10's pages.yml had an unquoted
": " in a `run:` line, so Pages never deployed). This guards all workflow files."""
from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOWS = sorted((Path(__file__).resolve().parents[1] / ".github" / "workflows").glob("*.yml"))


@pytest.mark.parametrize("path", WORKFLOWS, ids=[p.name for p in WORKFLOWS])
def test_workflow_is_valid_yaml(path):
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict) and "jobs" in doc
    assert True in doc or "on" in doc  # YAML 1.1 reads the bare key `on` as True
    for name, job in doc["jobs"].items():
        assert "runs-on" in job, name
        for step in job.get("steps", []):
            assert isinstance(step, dict) and ("run" in step or "uses" in step), (name, step)


def test_found_workflows():
    assert {p.name for p in WORKFLOWS} >= {"pages.yml", "weekly-fetch.yml", "monthly-shadow.yml"}
