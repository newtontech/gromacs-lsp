"""Golden/fixture contract for the gromacs.log.settle_shake_failure rule (issue #21).

These tests pin the OpenQC rule surface for SETTLE/SHAKE failure detection:

* the invalid fixture must emit exactly the ``gromacs.log.settle_shake_failure``
  diagnostic at ``error`` severity, with a stable range and fix hint;
* the valid fixture must emit no ``gromacs.log.settle_shake_failure`` diagnostic;
* the rule manifest under ``rules/diagnostics.yaml`` must export the rule with
  the expected severity and source metadata;
* ``gromacs-lsp-tool log --json <path>`` must surface the same rule id.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from gromacs_lsp.diagnostics import Diagnostic
from gromacs_lsp.log_parser import parse_log
from gromacs_lsp.rich_diagnostics import diagnostic_to_dict
from gromacs_lsp.rules import RULES, rule_meta

LOG_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "logs"
RULE_ID = "gromacs.log.settle_shake_failure"


def _rich_items(diagnostics: list[Diagnostic]) -> list[dict]:
    return [
        diagnostic_to_dict(d, software="gromacs", path=d.file, file_type="log")
        for d in diagnostics
    ]


def test_rule_id_is_exported_constant() -> None:
    assert RULE_ID in RULES
    meta = rule_meta(RULE_ID)
    assert meta is not None
    assert meta["severity"] == "error"
    assert meta["code"] == "GMX403"
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
    fixture = LOG_FIXTURES / "settle_shake_failure.log"
    golden_path = Path(__file__).resolve().parents[1] / "fixtures" / "rules" / "log_settle_shake_failure.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))

    diagnostics = [d for d in parse_log(fixture) if d.rule_id == RULE_ID]
    items = _rich_items(diagnostics)

    assert len(items) == len(golden["diagnostics"])

    for actual, expected in zip(items, golden["diagnostics"]):
        assert actual["rule_id"] == RULE_ID
        assert actual["severity"] == "error"
        assert actual["category"] == "preflight/runtime-risk"
        assert actual["range"] == expected["range"]
        assert actual["fix_hints"] == expected["fix_hints"]


def test_valid_fixture_does_not_trigger() -> None:
    fixture = LOG_FIXTURES / "valid_run.log"
    diagnostics = [d for d in parse_log(fixture) if d.rule_id == RULE_ID]
    assert diagnostics == []


def test_explain_json_surfaces_rule() -> None:
    from gromacs_lsp.tool import explain_main

    payload = json.loads(explain_main([RULE_ID]))
    assert payload["rule_id"] == RULE_ID
    assert payload["severity"] == "error"
    assert payload["source"] == "official"


def test_log_tool_operation(tmp_path: Path) -> None:
    """The gromacs-lsp-tool log operation must surface SETTLE/SHAKE failures."""
    log_file = tmp_path / "test.log"
    log_file.write_text("SHAKE error on molecules SOL 1\n", encoding="utf-8")
    from gromacs_lsp.tool import log_check_path
    payload = log_check_path(log_file)
    assert payload["ok"] is False
    assert any(d["rule_id"] == RULE_ID for d in payload["diagnostics"])
