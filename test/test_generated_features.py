"""Contract tests for the generated LSP feature manifest (issue #13).

These pin the ``generated-lsp-features`` capability surface:

* the manifest must list each generated LSP feature (completion, hover,
  diagnostics, formatting, code actions, symbols) with a status and at least
  one data source;
* the completion/hover coverage counts must match the in-repo data
  dictionaries (``_MDP_DOCS`` and ``_TOPOLOGY_DOCS``) so a regression in the
  data dictionary surfaces as a regression in this manifest;
* the diagnostics coverage must match the rule manifest rule ids;
* ``gromacs-lsp-tool features`` must produce valid JSON with the expected
  schema fields.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from gromacs_lsp.generated_features import (
    FEATURE_SCHEMA,
    FEATURE_VERSION,
    generated_features_manifest,
)


def test_features_manifest_has_stable_schema_header() -> None:
    manifest = generated_features_manifest()
    assert manifest["schema"] == FEATURE_SCHEMA
    assert manifest["schema_version"] == FEATURE_VERSION
    assert manifest["software"] == "gromacs"


def test_features_manifest_lists_every_generated_feature() -> None:
    manifest = generated_features_manifest()
    features = manifest["features"]
    for name in (
        "completion",
        "hover",
        "diagnostics",
        "formatting",
        "code_actions",
        "symbols",
    ):
        assert name in features, f"missing feature: {name}"
        assert features[name]["status"] == "available"
        assert features[name]["data_sources"], (
            f"{name} must declare at least one data source"
        )


def test_completion_coverage_matches_mdp_docs() -> None:
    """Completion coverage is generated from _MDP_DOCS / _TOPOLOGY_DOCS."""
    from gromacs_lsp.hover import _MDP_DOCS, _TOPOLOGY_DOCS

    manifest = generated_features_manifest()
    completion = manifest["features"]["completion"]
    assert completion["coverage"]["mdp_keys"] == sorted(_MDP_DOCS.keys())
    assert completion["coverage"]["topology_sections"] == sorted(_TOPOLOGY_DOCS.keys())
    assert completion["counts"]["mdp_keys"] == len(_MDP_DOCS)
    assert completion["counts"]["topology_sections"] == len(_TOPOLOGY_DOCS)


def test_hover_coverage_matches_mdp_docs() -> None:
    """Hover coverage is generated from the same source as completion."""
    from gromacs_lsp.hover import _MDP_DOCS

    manifest = generated_features_manifest()
    hover = manifest["features"]["hover"]
    assert hover["coverage"]["mdp_keys"] == sorted(_MDP_DOCS.keys())


def test_diagnostics_coverage_matches_rule_manifest() -> None:
    """Diagnostics coverage is generated from rules/diagnostics.yaml."""
    repo_root = Path(__file__).resolve().parents[1]
    yaml_rules = yaml.safe_load(
        (repo_root / "rules" / "diagnostics.yaml").read_text(encoding="utf-8")
    )
    expected_ids = {entry["rule_id"] for entry in yaml_rules["rules"]}

    manifest = generated_features_manifest()
    diagnostics = manifest["features"]["diagnostics"]
    assert set(diagnostics["coverage"]["rule_ids"]) == expected_ids
    assert diagnostics["counts"]["rules"] == len(expected_ids)


def test_code_actions_coverage_lists_handled_codes() -> None:
    from gromacs_lsp.code_actions import HANDLED_CODES

    manifest = generated_features_manifest()
    code_actions = manifest["features"]["code_actions"]
    assert code_actions["status"] == "available"
    assert set(code_actions["coverage"]["handled_codes"]) == set(HANDLED_CODES)
    kinds = {entry["kind"] for entry in code_actions["coverage"]["kinds"]}
    assert "rename_mdp_keyword" in kinds
    assert "create_include" in kinds


def test_feature_status_rollup_lists_all_features() -> None:
    manifest = generated_features_manifest()
    rollup = manifest["feature_status"]
    for name in ("completion", "hover", "diagnostics", "formatting", "code_actions"):
        assert rollup[name] == "available"


def test_features_manifest_is_json_serializable() -> None:
    manifest = generated_features_manifest()
    serialized = json.dumps(manifest, sort_keys=True)
    assert json.loads(serialized) == manifest


def test_features_cli_payload() -> None:
    """``gromacs-lsp-tool features`` emits the manifest unchanged."""
    from gromacs_lsp.tool import features_main

    payload = json.loads(features_main([]))
    assert payload["operation"] == "features"
    assert payload["schema"] == FEATURE_SCHEMA
    # The CLI payload must round-trip back to the in-process manifest.
    expected = generated_features_manifest()
    for key in expected:
        assert payload[key] == expected[key]
