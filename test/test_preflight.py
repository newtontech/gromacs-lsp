"""Universal generated-input preflight contract (issue #29).

These tests pin the four fleet-wide preflight capabilities for gromacs-lsp
against a generic artifact-role model (primary-input ``.mdp``, topology
``.top``, coordinate ``.gro``, index ``.ndx``):

* the valid fixture must emit no blocking diagnostics (and none of the
  preflight error codes);
* the several_failing fixture must emit the expected ``GMXPREF1xx`` codes;
* every blocking diagnostic must carry the ``DiagnosticEnvelope/v1`` required
  fields (``source_provenance``, ``actions``, ``fix_hints``, ``facts``,
  ``artifact_roles``);
* the ``--fail-on-blocking`` gate must exit non-zero on a failing case;
* the ``manifest`` subcommand must list all codes/roles/capabilities and merge
  the per-case fixture expectations declared in ``.gromacs-lsp/fixtures.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

from gromacs_lsp import tool
from gromacs_lsp.preflight import (
    ALL_ROLES,
    CODE_EMPTY_MDP,
    CODE_MOLECULE_DECLARATION_MISMATCH,
    CODE_MISSING_COORDINATE,
    CODE_MISSING_INDEX,
    CODE_MISSING_PRIMARY_INPUT,
    CODE_MISSING_REQUIRED_MDP_KEY,
    CODE_UNKNOWN_MDP_PARAMETER,
    CODE_UNREADABLE_INPUT,
    CODE_UNRESOLVED_TOPOLOGY_INCLUDE,
    CODE_VERSION_ASSUMPTION,
    ArtifactGraph,
    build_artifact_graph,
    fleet_manifest,
    resolve_version_assumption,
)
from gromacs_lsp.tool import (
    _dedupe_preflight,
    _looks_like_workspace,
    check_path,
    manifest_path,
    preflight_path,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "preflight"

# Envelope fields the issue acceptance criteria require on failing fixtures.
REQUIRED_FAILING_FIELDS = {
    "code",
    "severity",
    "path",
    "range",
    "blocking",
    "category",
    "source_provenance",
}

FAILING_CODES = {
    CODE_UNRESOLVED_TOPOLOGY_INCLUDE,
    CODE_MOLECULE_DECLARATION_MISMATCH,
    CODE_MISSING_COORDINATE,
    CODE_MISSING_INDEX,
    CODE_MISSING_REQUIRED_MDP_KEY,
    CODE_UNKNOWN_MDP_PARAMETER,
}


def _envelope_codes(payload: dict) -> set[str]:
    return {item["code"] for item in payload["diagnostics"]}


# --- Envelope shape --------------------------------------------------------


def test_agent_check_payload_carries_diagnostic_envelope_v1(capsys) -> None:
    rc = tool.main(["check", str(FIXTURES / "valid")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["diagnostic_envelope"] == "v1"
    assert payload["diagnostic_engine"] == "1.0"
    assert payload["software"] == "gromacs"
    # capabilities block is attached by the CLI wrapper
    assert payload["capabilities"]["operation"] == "check"
    # version assumption is surfaced at top level so the parent probe can branch
    assert "version_assumption" in payload
    assert payload["version_assumption"]["software"] == "gromacs"
    # cross-artifact graph is serialized for the fleet report workflow
    assert isinstance(payload.get("artifacts"), list)
    assert payload["artifacts"]


def test_failing_diagnostics_carry_required_envelope_fields() -> None:
    payload = preflight_path(FIXTURES / "several_failing")
    failing = [
        item
        for item in payload["diagnostics"]
        if item["code"] == CODE_MOLECULE_DECLARATION_MISMATCH
    ]
    assert failing, "failing fixture must emit a molecule-declaration mismatch"
    item = failing[0]
    for field in REQUIRED_FAILING_FIELDS:
        assert field in item, f"missing required envelope field: {field}"
    # Richer envelope fields used by the parent fleet probe
    assert item["confidence"] >= 0.0
    assert "actions" in item and item["actions"]
    assert "fix_hints" in item and item["fix_hints"]
    assert "facts" in item
    assert item["facts"]["molecule"] == "Undefined"
    assert "artifact_roles" in item
    # range is a proper LSP-style start/end object
    assert item["range"]["start"]["line"] >= 0
    assert "character" in item["range"]["start"]


# --- Fixture behavior ------------------------------------------------------


def test_valid_fixture_has_no_blocking_or_error_diagnostics() -> None:
    payload = preflight_path(FIXTURES / "valid")
    assert payload["summary"]["errors"] == 0
    assert payload["summary"]["blocking"] == 0
    # valid fixture must not carry any preflight error code
    assert not (_envelope_codes(payload) & FAILING_CODES)


def test_several_failing_fixture_emits_expected_blocking_codes() -> None:
    payload = preflight_path(FIXTURES / "several_failing")
    codes = _envelope_codes(payload)
    assert payload["ok"] is False, f"expected failing, got codes={sorted(codes)}"
    assert FAILING_CODES <= codes, (
        f"expected codes {sorted(FAILING_CODES)}, got {sorted(codes)}"
    )


def test_unknown_mdp_parameter_carries_version_assumption() -> None:
    payload = preflight_path(FIXTURES / "several_failing")
    item = next(
        d for d in payload["diagnostics"] if d["code"] == CODE_UNKNOWN_MDP_PARAMETER
    )
    assert item["facts"]["keyword"] == "nstepps"
    assert "version-aware" in item["domain_tags"]
    assert "version_assumption" in item


def test_missing_required_mdp_key_reports_dt() -> None:
    payload = preflight_path(FIXTURES / "several_failing")
    items = [
        d
        for d in payload["diagnostics"]
        if d["code"] == CODE_MISSING_REQUIRED_MDP_KEY
    ]
    assert items
    missing = {item["facts"]["missing_key"] for item in items}
    assert "dt" in missing


def test_unresolved_topology_include_records_provenance() -> None:
    payload = preflight_path(FIXTURES / "several_failing")
    item = next(
        d for d in payload["diagnostics"] if d["code"] == CODE_UNRESOLVED_TOPOLOGY_INCLUDE
    )
    prov = item["source_provenance"]
    assert prov["role"] == "topology"
    assert prov["include"] == "does_not_exist.itp"
    assert "referenced_from" in prov
    assert prov["referenced_from"]["path"].endswith("topol.top")


def test_missing_coordinate_is_blocking_with_provenance() -> None:
    payload = preflight_path(FIXTURES / "several_failing")
    item = next(
        d for d in payload["diagnostics"] if d["code"] == CODE_MISSING_COORDINATE
    )
    assert item["severity"] == "error"
    assert item["blocking"] is True
    assert item["source_provenance"]["role"] == "coordinate"
    assert item["source_provenance"]["declared_name"] == "missing_coord.gro"


def test_missing_index_is_blocking_with_provenance() -> None:
    payload = preflight_path(FIXTURES / "several_failing")
    item = next(
        d for d in payload["diagnostics"] if d["code"] == CODE_MISSING_INDEX
    )
    assert item["severity"] == "error"
    assert item["blocking"] is True
    assert item["source_provenance"]["role"] == "index"


# --- version-aware-keywords ------------------------------------------------


def test_version_assumption_unknown_when_intent_absent() -> None:
    assumption = resolve_version_assumption(None)
    assert assumption["exact_runtime_known"] is False
    assert assumption["declared_by"] == "fallback"
    assert assumption["software_version"] == "unknown"
    assert assumption["software"] == "gromacs"


def test_version_assumption_known_when_intent_declares_version() -> None:
    assumption = resolve_version_assumption(
        {"software_version": "gromacs >=2024", "runtime_image": "gmx:2024"}
    )
    assert assumption["exact_runtime_known"] is True
    assert assumption["declared_by"] == "intent"
    assert assumption["software_version"] == "gromacs >=2024"


def test_version_assumption_information_diagnostic_when_unknown() -> None:
    payload = preflight_path(FIXTURES / "valid")
    item = next(
        (d for d in payload["diagnostics"] if d["code"] == CODE_VERSION_ASSUMPTION),
        None,
    )
    assert item is not None
    assert item["severity"] == "information"
    assert item["blocking"] is False
    assert item["version_assumption"]["exact_runtime_known"] is False


def test_version_assumption_silent_when_intent_declares_version(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "grompp.mdp").write_text(
        "integrator = md\nnsteps = 100\ndt = 0.002\n", encoding="utf-8"
    )
    cfg = case / ".gromacs-lsp"
    cfg.mkdir()
    (cfg / "intent.json").write_text(
        json.dumps({"software_version": "gromacs >=2024"}), encoding="utf-8"
    )
    payload = preflight_path(case)
    assert CODE_VERSION_ASSUMPTION not in _envelope_codes(payload)
    assert payload["version_assumption"]["exact_runtime_known"] is True


# --- cross-artifact-graph --------------------------------------------------


def test_artifact_graph_uses_generic_roles() -> None:
    case_dir = (FIXTURES / "valid").resolve()
    mdp_path = case_dir / "grompp.mdp"
    graph = build_artifact_graph(case_dir, mdp_path)
    roles = {node.role for node in graph.nodes}
    assert roles <= set(ALL_ROLES)
    # primary-input + coordinate + topology are always present for the valid case
    for required in ("primary-input", "coordinate", "topology"):
        assert graph.by_role(required), f"missing required role: {required}"
    # serialized graph is JSON-friendly and stable
    serialized = graph.to_json()
    assert isinstance(serialized, list)
    assert all(
        "role" in node and "path" in node and "exists" in node for node in serialized
    )


def test_missing_primary_input_emits_blocking(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    # directory with no .mdp at all
    payload = preflight_path(case)
    assert CODE_MISSING_PRIMARY_INPUT in _envelope_codes(payload)
    item = next(
        d for d in payload["diagnostics"] if d["code"] == CODE_MISSING_PRIMARY_INPUT
    )
    assert item["blocking"] is True


def test_empty_mdp_emits_blocking(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "grompp.mdp").write_text("; only a comment\n", encoding="utf-8")
    payload = preflight_path(case)
    assert CODE_EMPTY_MDP in _envelope_codes(payload)


def test_unreadable_mdp_emits_blocking(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    mdp = case / "grompp.mdp"
    mdp.write_bytes(b"\xff\xfe\x00invalid binary")
    payload = preflight_path(case)
    assert CODE_UNREADABLE_INPUT in _envelope_codes(payload)


# --- code-actions / blocking gate -----------------------------------------


def test_check_fail_on_blocking_exits_nonzero_on_failing_fixture() -> None:
    rc = tool.main(
        ["check", str(FIXTURES / "several_failing"), "--fail-on-blocking"]
    )
    assert rc == 1


def test_check_fail_on_blocking_exits_zero_on_valid_fixture(capsys) -> None:
    rc = tool.main(["check", str(FIXTURES / "valid"), "--fail-on-blocking"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_preflight_fail_on_blocking_exits_nonzero_on_failing_fixture() -> None:
    rc = tool.main(
        ["preflight", str(FIXTURES / "several_failing"), "--fail-on-blocking"]
    )
    assert rc == 1


def test_preflight_subcommand_emits_envelope(capsys) -> None:
    rc = tool.main(["preflight", str(FIXTURES / "several_failing")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operation"] == "preflight"
    assert payload["diagnostic_envelope"] == "v1"
    assert payload["capabilities"]["operation"] == "preflight"


def test_actions_present_on_blocking_diagnostics() -> None:
    payload = preflight_path(FIXTURES / "several_failing")
    blocking = [d for d in payload["diagnostics"] if d["blocking"]]
    assert blocking
    for item in blocking:
        assert item.get("actions"), (
            f"blocking diagnostic {item['code']} must carry actions"
        )
        assert all("kind" in action for action in item["actions"])


# --- fleet-regression-fixtures / manifest ---------------------------------


def test_manifest_lists_all_four_capabilities() -> None:
    manifest = manifest_path(FIXTURES / "valid")
    capabilities = manifest["capabilities"]
    for cap in (
        "version-aware-keywords",
        "cross-artifact-graph",
        "code-actions",
        "fleet-regression-fixtures",
    ):
        assert cap in capabilities, f"missing capability: {cap}"
        assert capabilities[cap]["status"] == "available"
    # artifact roles are the generic fleet model, not MatMaster policy
    assert set(manifest["artifact_roles"]) == set(ALL_ROLES)
    assert manifest["preflight_envelope"] == "DiagnosticEnvelope/v1"


def test_manifest_without_path_still_describes_surface() -> None:
    manifest = manifest_path(None)
    assert set(manifest["codes"])
    assert manifest["capabilities"]["code-actions"]["blocking_gate"]


def test_manifest_merges_fixture_expectations() -> None:
    manifest = manifest_path(FIXTURES / "valid")
    fixtures = manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"]
    names = {item["name"] for item in fixtures}
    assert {"valid", "several_failing"} <= names


def test_fleet_manifest_helper_pure_data() -> None:
    manifest = fleet_manifest(fixtures=[{"name": "x", "expect_ok": True}])
    assert manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"] == [
        {"name": "x", "expect_ok": True}
    ]
    # every code entry is self-describing for the parent probe
    for body in manifest["codes"].values():
        assert body["severity"] in {"error", "warning", "information", "hint"}
        assert "capability" in body
        assert "summary" in body


def test_manifest_codes_cover_all_preflight_constants() -> None:
    manifest = manifest_path(None)
    declared = set(manifest["codes"])
    constants = {
        CODE_MISSING_PRIMARY_INPUT,
        CODE_UNREADABLE_INPUT,
        CODE_EMPTY_MDP,
        CODE_MISSING_REQUIRED_MDP_KEY,
        CODE_UNRESOLVED_TOPOLOGY_INCLUDE,
        CODE_MOLECULE_DECLARATION_MISMATCH,
        CODE_MISSING_COORDINATE,
        CODE_MISSING_INDEX,
        CODE_VERSION_ASSUMPTION,
        CODE_UNKNOWN_MDP_PARAMETER,
    }
    assert constants <= declared


# --- dedupe + workspace detection -----------------------------------------


def test_dedupe_preflight_drops_overlap_with_legacy() -> None:
    legacy = [{"code": "GMX002", "severity": "error", "line": 1, "message": "unknown"}]
    preflight = [
        {"code": CODE_UNKNOWN_MDP_PARAMETER, "severity": "error", "message": "unknown"},
        {"code": CODE_MISSING_REQUIRED_MDP_KEY, "severity": "error", "message": "dt"},
    ]
    result = _dedupe_preflight(legacy, preflight)
    codes = {item["code"] for item in result}
    assert CODE_UNKNOWN_MDP_PARAMETER not in codes  # suppressed (overlap with GMX002)
    assert CODE_MISSING_REQUIRED_MDP_KEY in codes


def test_looks_like_workspace_requires_mdp(tmp_path: Path) -> None:
    assert _looks_like_workspace(tmp_path) is False
    (tmp_path / "grompp.mdp").write_text("integrator = md\n", encoding="utf-8")
    assert _looks_like_workspace(tmp_path) is True


def test_check_on_single_mdp_file_merges_preflight(tmp_path: Path) -> None:
    # A bare .mdp with a missing required key must surface the preflight finding
    # alongside the legacy single-file lint.
    mdp = tmp_path / "grompp.mdp"
    mdp.write_text("integrator = md\n", encoding="utf-8")
    payload = check_path(mdp)
    assert CODE_MISSING_REQUIRED_MDP_KEY in _envelope_codes(payload)
    assert payload["diagnostic_envelope"] == "v1"


def test_check_on_full_workspace_merges_preflight() -> None:
    payload = check_path(FIXTURES / "several_failing")
    codes = _envelope_codes(payload)
    # GMXPREF104 overlaps with legacy GMX024 and is deduped, but the missing
    # coordinate/index/required-key findings survive.
    assert CODE_MISSING_COORDINATE in codes
    assert CODE_MISSING_INDEX in codes
    assert payload["diagnostic_envelope"] == "v1"


# --- smoke / dataclass -----------------------------------------------------


def test_artifact_graph_is_json_serializable_for_fleet_report() -> None:
    payload = preflight_path(FIXTURES / "valid")
    serialized = json.dumps(payload["artifacts"], sort_keys=True)
    assert "primary-input" in serialized


def test_artifact_graph_class_smoke() -> None:
    graph = ArtifactGraph(case_dir=Path("/tmp"))
    assert graph.nodes == []
    assert graph.by_role("topology") == []
    assert graph.to_json() == []
