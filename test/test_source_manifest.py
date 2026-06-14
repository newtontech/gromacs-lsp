"""Contract tests for the OpenQC source manifest (issue #12).

These pin the ``agent-json`` capability surface:

* the source manifest must aggregate the LSP capabilities block, the
  diagnostic rule manifest, and the generated feature manifest into a single
  deterministic JSON document;
* the agent CLI operations list must include ``source-manifest`` (and the
  other new operations) so OpenQC consumers can discover the surface from
  the manifest alone;
* ``gromacs-lsp-tool source-manifest`` must produce valid JSON with the
  expected schema fields.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from gromacs_lsp.source_manifest import (
    MANIFEST_SCHEMA,
    MANIFEST_VERSION,
    source_manifest,
)


def test_source_manifest_has_stable_schema_header() -> None:
    manifest = source_manifest()
    assert manifest["schema"] == MANIFEST_SCHEMA
    assert manifest["schema_version"] == MANIFEST_VERSION


def test_source_manifest_identifies_the_lsp() -> None:
    manifest = source_manifest()
    assert manifest["id"] == "gromacs-lsp"
    assert manifest["software"] == "gromacs"
    assert manifest["languageId"] == "gromacs"
    assert manifest["executable"] == "gromacs-lsp"
    assert "*.mdp" in manifest["filePatterns"]
    assert "*.top" in manifest["filePatterns"]


def test_source_manifest_carries_blocking_policy() -> None:
    manifest = source_manifest()
    policy = manifest["blockingPolicy"]
    assert policy["mode"] == "blocking"


def test_source_manifest_advertises_new_agent_cli_operations() -> None:
    """The manifest must surface the source-manifest/features/code-actions ops."""
    manifest = source_manifest()
    operations = manifest["agentCli"]["operations"]
    for op in ("source-manifest", "features", "code-actions"):
        assert op in operations, f"missing agent CLI operation: {op}"


def test_source_manifest_advertises_capability_strings() -> None:
    manifest = source_manifest()
    caps = manifest["capabilities"]
    for cap in ("diagnostics", "completion", "hover", "source-manifest"):
        assert cap in caps, f"missing capability: {cap}"


def test_source_manifest_summarizes_rule_surface() -> None:
    """The rule summary must match the rules/diagnostics.yaml source of truth."""
    manifest = source_manifest()
    rules_section = manifest["rules"]
    repo_root = Path(__file__).resolve().parents[1]
    yaml_rules = yaml.safe_load(
        (repo_root / "rules" / "diagnostics.yaml").read_text(encoding="utf-8")
    )
    expected_ids = {entry["rule_id"] for entry in yaml_rules["rules"]}
    assert set(rules_section["rule_ids"]) == expected_ids
    assert rules_section["rule_count"] == len(expected_ids)
    # The rule surface is grouped by file type so OpenQC dashboards can branch.
    assert "mdp" in rules_section["by_file_type"]
    assert "top" in rules_section["by_file_type"]
    assert "log" in rules_section["by_file_type"]


def test_source_manifest_embeds_generated_features() -> None:
    manifest = source_manifest()
    features = manifest["generated_features"]
    assert features["schema"] == "OpenQCLspFeatureManifest"
    assert "completion" in features["features"]
    assert "code_actions" in features["features"]
    # Every advertised feature must report its status.
    for name, entry in features["features"].items():
        assert entry["status"] == "available", f"{name} not available"


def test_source_manifest_carries_source_provenance() -> None:
    manifest = source_manifest()
    provenance = manifest["sourceProvenance"]
    assert provenance, "source provenance must not be empty"
    # Every entry classifies the upstream source kind.
    for entry in provenance:
        assert "kind" in entry
        assert "label" in entry


def test_source_manifest_is_json_serializable() -> None:
    """The manifest must round-trip through JSON for OpenQC consumers."""
    manifest = source_manifest()
    serialized = json.dumps(manifest, sort_keys=True)
    assert json.loads(serialized) == manifest


def test_source_manifest_cli_payload() -> None:
    """``gromacs-lsp-tool source-manifest`` must emit the manifest unchanged."""
    from gromacs_lsp.tool import source_manifest_main

    payload = json.loads(source_manifest_main([]))
    assert payload["operation"] == "source-manifest"
    assert payload["schema"] == MANIFEST_SCHEMA
    assert payload["id"] == "gromacs-lsp"
    # The CLI payload must round-trip back to the in-process manifest (modulo
    # the ``operation`` key the CLI adds at the top level).
    expected = source_manifest()
    for key in expected:
        assert payload[key] == expected[key]
