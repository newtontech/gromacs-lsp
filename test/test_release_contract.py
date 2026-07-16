from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import gromacs_lsp


ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "0.0.4"


def _setup_version() -> str:
    match = re.search(
        r'version=["\']([^"\']+)["\']',
        (ROOT / "setup.py").read_text(encoding="utf-8"),
    )
    assert match is not None
    return match.group(1)


def test_release_version_and_provenance_are_consistent() -> None:
    manifest = json.loads((ROOT / "lsp-capabilities.json").read_text(encoding="utf-8"))

    assert _setup_version() == RELEASE_VERSION
    assert gromacs_lsp.__version__ == RELEASE_VERSION
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == RELEASE_VERSION
    assert manifest["repository"] == "newtontech/gromacs-lsp"
    assert manifest["releaseVersion"] == RELEASE_VERSION
    assert manifest["releaseTag"] == f"v{RELEASE_VERSION}"
    assert manifest["sourceProvenanceVersion"] == 1
    assert (
        manifest["traceabilityReportPath"]
        == "reports/docstring-wiki-raw-traceability.json"
    )
    assert manifest["releaseChecklistPath"] == "docs/RELEASE.md"


def test_release_workflow_is_tag_only_and_uses_scoped_oidc() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )

    assert re.search(r"push:\s*\n\s+tags:\s*\[?\"v\*\"\]?", workflow)
    assert "workflow_dispatch:" not in workflow
    assert "environment: pypi" in workflow
    assert "id-token: write" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "gh release create" in workflow
    assert "scripts/verify_release.py" in workflow
    assert "scripts/smoke_wheel.sh" in workflow


def test_release_docs_and_smoke_cover_acceptance_surface() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs" / "RELEASE.md").read_text(encoding="utf-8")
    smoke = (ROOT / "scripts" / "smoke_wheel.sh").read_text(encoding="utf-8")

    assert f"Current release: `{RELEASE_VERSION}`" in readme
    assert "Trusted Publishing" in readme
    assert f"## [{RELEASE_VERSION}] - 2026-07-16" in changelog
    for required in (
        "raw/assets/manifest.json",
        "wiki/",
        "reports/docstring-wiki-raw-traceability.json",
        "lsp:check-latest -- --fail-on-drift",
        f"v{RELEASE_VERSION}",
    ):
        assert required in checklist
    for required in (
        "gromacs-lsp",
        "gromacs-lsp-tool",
        "--help",
        " check ",
        " log ",
        "test/fixtures/valid/minimal_em.mdp",
        "test/fixtures/invalid/invalid_mdp_value.mdp",
        "test/fixtures/logs/fatal_error.log",
    ):
        assert required in smoke


def test_source_release_verifier_accepts_matching_tag() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/verify_release.py", "--tag", f"v{RELEASE_VERSION}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
