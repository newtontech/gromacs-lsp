"""Golden/fixture contract for the gromacs.cutoff.pme_warning rule (issue #19).

These tests pin the OpenQC rule surface for suspicious cutoff/PME settings:

* the invalid fixture must emit exactly the ``gromacs.cutoff.pme_warning``
  diagnostic at ``warning`` severity, with a stable range and fix hint;
* the valid fixture must emit no ``gromacs.cutoff.pme_warning`` diagnostic;
* the rule manifest under ``rules/diagnostics.yaml`` must export the rule with
  the expected severity and source metadata;
* ``gromacs-lsp-tool explain --json gromacs.cutoff.pme_warning`` must surface
  the same rule id for OpenQC consumers.
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
RULE_ID = "gromacs.cutoff.pme_warning"


def _rich_items(diagnostics: list[Diagnostic]) -> list[dict]:
    return [
        diagnostic_to_dict(d, software="gromacs", path=d.file, file_type="mdp")
        for d in diagnostics
    ]


def test_rule_id_is_exported_constant() -> None:
    assert RULE_ID in RULES
    meta = rule_meta(RULE_ID)
    assert meta is not None
    assert meta["severity"] == "warning"
    assert meta["code"] == "GMX010"
    assert meta["source"] == "official"


def test_manifest_exports_rule() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = repo_root / "rules" / "diagnostics.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    rule_ids = {entry["rule_id"] for entry in manifest["rules"]}
    assert RULE_ID in rule_ids
    entry = next(r for r in manifest["rules"] if r["rule_id"] == RULE_ID)
    assert entry["severity"] == "warning"
    assert entry["source"] == "official"
    assert entry["manual_ref"].startswith("https://manual.gromacs.org/")


def test_invalid_fixture_matches_golden() -> None:
    fixture = FIXTURES / "cutoff_pme_warning.mdp"
    golden_path = FIXTURES / "cutoff_pme_warning.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))

    diagnostics = [d for d in analyze_file(fixture) if d.rule_id == RULE_ID]
    items = _rich_items(diagnostics)

    assert [d["range"]["start"]["line"] for d in items] == [
        d["range"]["start"]["line"] for d in golden["diagnostics"]
    ]
    assert len(items) == len(golden["diagnostics"]) == 1

    actual, expected = items[0], golden["diagnostics"][0]
    assert actual["rule_id"] == RULE_ID
    assert actual["severity"] == "warning"
    assert actual["category"] == "preflight/runtime-risk"
    assert actual["message"] == expected["message"]
    assert actual["range"] == expected["range"]
    assert actual["fix_hints"] == expected["fix_hints"]


def test_valid_fixture_does_not_trigger() -> None:
    fixture = FIXTURES / "valid_cutoff_pme.mdp"
    diagnostics = [d for d in analyze_file(fixture) if d.rule_id == RULE_ID]
    assert diagnostics == []


def test_explain_json_surfaces_rule() -> None:
    from gromacs_lsp.tool import explain_main

    payload = json.loads(explain_main([RULE_ID]))
    assert payload["rule_id"] == RULE_ID
    assert payload["severity"] == "warning"
    assert payload["source"] == "official"


def test_pme_warning_severity_is_warning(tmp_path: Path) -> None:
    """Promotion check: suspicious cutoff/PME settings are non-blocking warnings."""
    fixture = tmp_path / "badpme.mdp"
    fixture.write_text(
        "integrator = md\nnsteps = 1\ndt = 0.002\n"
        "coulombtype = PME\nrcoulomb = 0.6\nrvdw = 1.0\n",
        encoding="utf-8",
    )
    diagnostics = [d for d in analyze_file(fixture) if d.rule_id == RULE_ID]
    assert diagnostics
    assert all(d.severity == "warning" for d in diagnostics)
