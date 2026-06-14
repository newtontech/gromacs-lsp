"""Golden/fixture contract for the gromacs.topology.missing_include rule (issue #17).

These tests pin the OpenQC rule surface for unresolvable topology #include
directives:

* the invalid fixture must emit exactly the ``gromacs.topology.missing_include``
  diagnostic at ``error`` severity, with a stable range and fix hint;
* the valid fixture (every #include resolves) must emit no
  ``gromacs.topology.missing_include`` diagnostic;
* the rule manifest under ``rules/diagnostics.yaml`` must export the rule with
  the expected severity and source metadata;
* ``gromacs-lsp-tool explain --json gromacs.topology.missing_include`` must
  surface the same rule id for OpenQC consumers.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from gromacs_lsp.analyzer import analyze_file
from gromacs_lsp.diagnostics import Diagnostic
from gromacs_lsp.rich_diagnostics import diagnostic_to_dict
from gromacs_lsp.rules import RULES, rule_meta

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "rules"
RULE_ID = "gromacs.topology.missing_include"


def _rich_items(diagnostics: list[Diagnostic]) -> list[dict]:
    return [
        diagnostic_to_dict(d, software="gromacs", path=d.file, file_type="top")
        for d in diagnostics
    ]


def test_rule_id_is_exported_constant() -> None:
    assert RULE_ID in RULES
    meta = rule_meta(RULE_ID)
    assert meta is not None
    assert meta["severity"] == "error"
    assert meta["code"] == "GMX023"
    assert meta["source"] == "official"


def test_manifest_exports_rule() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = repo_root / "rules" / "diagnostics.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    rule_ids = {entry["rule_id"] for entry in manifest["rules"]}
    assert RULE_ID in rule_ids
    entry = next(r for r in manifest["rules"] if r["rule_id"] == RULE_ID)
    assert entry["severity"] == "error"
    assert entry["source"] == "official"
    assert entry["manual_ref"].startswith("https://manual.gromacs.org/")


def test_invalid_fixture_matches_golden() -> None:
    fixture = FIXTURES / "missing_include.top"
    golden_path = FIXTURES / "missing_include.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))

    diagnostics = [d for d in analyze_file(fixture) if d.rule_id == RULE_ID]
    items = _rich_items(diagnostics)

    # Exactly the golden diagnostics must fire, on the expected lines.
    assert [d["range"]["start"]["line"] for d in items] == [
        d["range"]["start"]["line"] for d in golden["diagnostics"]
    ]
    assert len(items) == len(golden["diagnostics"]) == 1

    for actual, expected in zip(items, golden["diagnostics"]):
        assert actual["rule_id"] == RULE_ID
        assert actual["severity"] == "error"
        assert actual["category"] == "cross-file reference"
        assert actual["message"] == expected["message"]
        assert actual["range"] == expected["range"]
        assert actual["fix_hints"] == expected["fix_hints"]


def test_valid_fixture_does_not_trigger() -> None:
    fixture = FIXTURES / "valid_topology_includes.top"
    diagnostics = [d for d in analyze_file(fixture) if d.rule_id == RULE_ID]
    assert diagnostics == []


def test_explain_json_surfaces_rule() -> None:
    from gromacs_lsp.tool import explain_main

    payload = json.loads(explain_main([RULE_ID]))
    assert payload["rule_id"] == RULE_ID
    assert payload["severity"] == "error"
    assert payload["source"] == "official"


def test_missing_include_severity_is_error(tmp_path: Path) -> None:
    """Promotion check: missing includes must be blocking errors, not warnings."""
    fixture = tmp_path / "missing.top"
    fixture.write_text(
        '#include "absent.itp"\n', encoding="utf-8"
    )
    diagnostics = [d for d in analyze_file(fixture) if d.rule_id == RULE_ID]
    assert diagnostics
    assert all(d.severity == "error" for d in diagnostics)
