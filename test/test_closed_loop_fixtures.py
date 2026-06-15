"""Closed-loop fixture tests for gromacs-lsp.

These tests exercise the canonical fixture directories declared in
``lsp-capabilities.json`` (``test/fixtures/{valid,invalid,logs}`` and
``test/fixtures/preflight``) through the analyzer and the agent CLI surface.
They are the single-command gate that OpenQC's ``lsp:check-family``
coordinator consumes.

Issues addressed:
- #41 closed-loop fixtures, repair previews, output diagnostics, OpenQC smoke
- #40 DiagnosticEnvelope/v1 with rule IDs, severity, blocking, source
       provenance, and version scope
- #39 official-docs -> raw/assets -> wiki -> rules -> provenance -> fixtures
       pipeline
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "test" / "fixtures"
VALID_DIR = FIXTURES / "valid"
INVALID_DIR = FIXTURES / "invalid"
LOG_DIR = FIXTURES / "logs"
PREFLIGHT_VALID_DIR = FIXTURES / "preflight" / "valid"


def _run_tool(*args: str) -> dict:
    """Run ``gromacs-lsp-tool`` and return its parsed JSON payload."""
    cmd = [sys.executable, "-m", "gromacs_lsp.tool", *args]
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode in (0, 1), proc.stderr
    payload = json.loads(proc.stdout)
    return payload


def _run_check(*args: str) -> dict:
    """Run a check-style CLI operation and assert the envelope contract."""
    payload = _run_tool(*args)
    assert payload.get("diagnostic_envelope") == "v1", payload
    assert payload.get("software") == "gromacs", payload
    return payload


def test_canonical_fixture_directories_exist() -> None:
    """The canonical paths advertised in lsp-capabilities.json must exist."""
    for path in (VALID_DIR, INVALID_DIR, LOG_DIR):
        assert path.is_dir(), f"missing canonical fixture dir: {path}"
    assert any(VALID_DIR.glob("*.mdp"))
    assert any(INVALID_DIR.glob("*.mdp"))
    assert any(LOG_DIR.glob("*.log"))


@pytest.mark.parametrize(
    "fixture",
    sorted(p.name for p in VALID_DIR.glob("*.mdp"))
    + sorted(p.name for p in VALID_DIR.glob("*.top")),
)
def test_valid_fixtures_are_clean_via_analyze_file(fixture: str) -> None:
    """Valid fixtures produce no analyzer diagnostics (no false positives)."""
    from gromacs_lsp.analyzer import analyze_file

    diagnostics = analyze_file(VALID_DIR / fixture)
    assert diagnostics == [], [(d.code, d.message) for d in diagnostics]


def test_unknown_mdp_key_emits_blocking_error_with_provenance() -> None:
    """Invalid fixture: GMX002 blocking error with MDP options URL."""
    from gromacs_lsp.analyzer import analyze_file
    from gromacs_lsp.rich_diagnostics import diagnostic_to_dict

    diags = analyze_file(INVALID_DIR / "unknown_mdp_key.mdp")
    rich = [
        diagnostic_to_dict(d, software="gromacs", path=d.file, file_type="mdp")
        for d in diags
    ]
    errors = [d for d in rich if d["code"] == "GMX002"]
    assert len(errors) == 2, [d["code"] for d in rich]
    for diag in errors:
        assert diag["severity"] == "error"
        assert diag["blocking"] is True
        prov = diag.get("source_provenance") or {}
        assert prov.get("kind") == "official_docs"
        assert (
            prov.get("url")
            == "https://manual.gromacs.org/current/user-guide/mdp-options.html"
        )
        assert (
            diag.get("manual_ref")
            == "https://manual.gromacs.org/current/user-guide/mdp-options.html"
        )


def test_invalid_mdp_value_emits_blocking_error_with_provenance() -> None:
    """Invalid fixture: GMX004 blocking error with MDP options URL."""
    from gromacs_lsp.analyzer import analyze_file
    from gromacs_lsp.rich_diagnostics import diagnostic_to_dict

    diags = analyze_file(INVALID_DIR / "invalid_mdp_value.mdp")
    rich = [
        diagnostic_to_dict(d, software="gromacs", path=d.file, file_type="mdp")
        for d in diags
    ]
    errors = [d for d in rich if d["code"] == "GMX004"]
    assert len(errors) >= 2, [d["code"] for d in rich]
    for diag in errors:
        assert diag["severity"] == "error"
        assert diag["blocking"] is True
        prov = diag.get("source_provenance") or {}
        assert (
            prov.get("url")
            == "https://manual.gromacs.org/current/user-guide/mdp-options.html"
        )


def test_cutoff_pme_warning_is_non_blocking_warning() -> None:
    """Invalid fixture: GMX010 warning that does NOT block the gate."""
    from gromacs_lsp.analyzer import analyze_file
    from gromacs_lsp.rich_diagnostics import diagnostic_to_dict

    diags = analyze_file(INVALID_DIR / "cutoff_pme_warning.mdp")
    rich = [
        diagnostic_to_dict(d, software="gromacs", path=d.file, file_type="mdp")
        for d in diags
    ]
    warnings = [d for d in rich if d["code"] == "GMX010"]
    assert warnings, [d["code"] for d in rich]
    for diag in warnings:
        assert diag["severity"] == "warning"
        assert diag["blocking"] is False
        prov = diag.get("source_provenance") or {}
        assert (
            prov.get("url")
            == "https://manual.gromacs.org/current/user-guide/mdp-options.html"
        )


def test_missing_topology_include_emits_blocking_error_with_provenance() -> None:
    """Invalid fixture: GMX023 blocking cross-file error."""
    from gromacs_lsp.analyzer import analyze_file
    from gromacs_lsp.rich_diagnostics import diagnostic_to_dict

    diags = analyze_file(INVALID_DIR / "missing_topology_include.top")
    rich = [
        diagnostic_to_dict(d, software="gromacs", path=d.file, file_type="top")
        for d in diags
    ]
    errors = [d for d in rich if d["code"] == "GMX023"]
    assert errors, [d["code"] for d in rich]
    diag = errors[0]
    assert diag["severity"] == "error"
    assert diag["blocking"] is True
    prov = diag.get("source_provenance") or {}
    assert prov.get("url") == (
        "https://manual.gromacs.org/current/reference-manual/topologies/file-format.html"
    )


@pytest.mark.parametrize(
    "fixture,code",
    [
        ("fatal_error.log", "GMX401"),
        ("lincs_instability.log", "GMX402"),
        ("settle_shake_failure.log", "GMX403"),
    ],
)
def test_log_fixtures_emit_runtime_diagnostics(fixture: str, code: str) -> None:
    """Runtime log fixtures yield GMX40x diagnostics with run-time-errors URL."""
    from gromacs_lsp.log_parser import parse_log
    from gromacs_lsp.rich_diagnostics import diagnostic_to_dict

    diags = parse_log(LOG_DIR / fixture)
    matches = [d for d in diags if d.code == code]
    assert matches, f"{fixture}: expected {code}, got {[d.code for d in diags]}"
    rich = diagnostic_to_dict(
        matches[0], software="gromacs", path=str(LOG_DIR / fixture), file_type="log"
    )
    assert rich["severity"] == "error"
    assert rich["blocking"] is True
    prov = rich.get("source_provenance") or {}
    assert (
        prov.get("url")
        == "https://manual.gromacs.org/current/user-guide/run-time-errors.html"
    )


def test_valid_run_log_is_clean() -> None:
    """valid_run.log fixture yields no log-parser diagnostics."""
    from gromacs_lsp.log_parser import parse_log

    diags = parse_log(LOG_DIR / "valid_run.log")
    assert diags == [], [(d.code, d.message) for d in diags]


def test_preflight_valid_case_directory_passes_cli_check() -> None:
    """The preflight valid case directory must produce a clean check via CLI."""
    payload = _run_check("check", str(PREFLIGHT_VALID_DIR))
    # The preflight valid fixture is designed to produce no blocking diagnostics.
    assert payload["ok"] is True, payload["summary"]
    # The check should not surface any of the schema/type/cross-file rules.
    for diag in payload["diagnostics"]:
        assert diag.get("severity") != "error", diag


def test_capabilities_payload_advertises_canonical_fixture_paths() -> None:
    """lsp-capabilities.json must advertise the canonical fixture dirs."""
    capabilities = json.loads((REPO_ROOT / "lsp-capabilities.json").read_text())
    fixture_paths = capabilities["fixturePaths"]
    assert "test/fixtures/valid" in fixture_paths["valid"]
    assert "test/fixtures/invalid" in fixture_paths["invalid"]
    assert "test/fixtures/logs" in fixture_paths["logs"]


def test_rule_manifest_carries_provenance_for_every_rule() -> None:
    """Every rule in the manifest must trace to an official GROMACS URL."""
    from gromacs_lsp.rules import RULES, diagnostic_provenance

    assert RULES, "rule manifest must not be empty"
    for rule_id in RULES:
        prov = diagnostic_provenance(rule_id)
        assert prov, rule_id
        assert prov["kind"] == "official_docs", prov
        assert prov["url"].startswith("https://manual.gromacs.org/"), prov


def test_source_manifest_operation_returns_payload() -> None:
    """The source-manifest operation must return the canonical payload."""
    payload = _run_tool("source-manifest")
    assert payload["schema"] == "OpenQCSourceManifest", payload
    assert payload["id"] == "gromacs-lsp", payload
    assert "rules" in payload and payload["rules"]["rule_count"] > 0
    assert "sourceProvenance" in payload


def test_capabilities_operation_returns_payload() -> None:
    """The capabilities operation must return the canonical payload."""
    payload = _run_tool("capabilities")
    assert payload["schema"] == "OpenQCLspCapabilities", payload
    assert payload["id"] == "gromacs-lsp", payload
    assert "test/fixtures/valid" in payload["fixturePaths"]["valid"]


def test_openqc_compatibility_report_exists_and_references_fixtures() -> None:
    """The OpenQC compatibility report must be present and up-to-date."""
    report = REPO_ROOT / "diagnostics" / "openqc-compatibility.md"
    assert report.is_file(), "missing diagnostics/openqc-compatibility.md"
    text = report.read_text(encoding="utf-8")
    for fixture in (
        "test/fixtures/valid/minimal_em.mdp",
        "test/fixtures/invalid/unknown_mdp_key.mdp",
        "test/fixtures/logs/lincs_instability.log",
        "test/fixtures/preflight/valid/",
    ):
        assert fixture in text, f"openqc report missing reference: {fixture}"
    # Blocking policy table must list GMX002 as a blocker
    assert "GMX002" in text
