"""Contract tests for the OpenQC code-actions capability (issue #23).

These pin the ``code-actions`` capability surface:

* the exported ``code_action_kinds`` list must include one kind per
  diagnostic code with a concrete fix;
* the rename action for an unknown MDP key (GMX002) must produce a real
  ``WorkspaceEdit`` and be flagged ``safe_to_auto_apply`` when the typo is
  within the edit-distance threshold;
* the missing-include action (GMX023) must surface the path the caller
  needs to create;
* the log-instability actions (GMX402/GMX403) must surface the standard
  stability playbook without claiming to be auto-applicable;
* the agent CLI ``fix`` operation must wire the concrete actions through.
"""

from __future__ import annotations

import json
from pathlib import Path

from gromacs_lsp.code_actions import (
    HANDLED_CODES,
    _levenshtein,
    actions_for_diagnostic,
    code_action_kinds,
)


def _mdp_typo_diagnostic(*, typo: str, line: int = 1) -> dict:
    return {
        "code": "GMX002",
        "severity": "error",
        "message": f"unknown or currently unsupported MDP key: {typo}",
        "range": {
            "start": {"line": line, "character": 0},
            "end": {"line": line, "character": 1},
        },
        "fix_hints": [{"kind": "check_mdp_keyword", "keyword": typo}],
        "blocking": True,
        "source": "gromacs-lsp",
        "path": "/tmp/sample.mdp",
    }


def _missing_include_diagnostic(*, path: str, line: int = 0) -> dict:
    return {
        "code": "GMX023",
        "severity": "error",
        "message": (
            f"topology #include references a file that could not be resolved: '{path}'"
        ),
        "range": {
            "start": {"line": line, "character": 0},
            "end": {"line": line, "character": 1},
        },
        "fix_hints": [{"kind": "check_include_path", "include": path}],
        "blocking": True,
        "source": "gromacs-lsp",
        "path": "/tmp/sample.top",
    }


def _log_instability_diagnostic(*, code: str, line: int = 0) -> dict:
    return {
        "code": code,
        "severity": "error",
        "message": "constraint solver failed to converge",
        "range": {
            "start": {"line": line, "character": 0},
            "end": {"line": line, "character": 1},
        },
        "fix_hints": [],
        "blocking": True,
        "source": "gromacs-lsp",
        "path": "/tmp/sample.log",
    }


# --- exported surface ------------------------------------------------------


def test_code_action_kinds_cover_all_handled_codes() -> None:
    kinds = code_action_kinds()
    evidence_codes = {code for kind in kinds for code in kind["evidence_codes"]}
    assert evidence_codes == set(HANDLED_CODES)
    kind_names = {kind["kind"] for kind in kinds}
    assert kind_names == {
        "rename_mdp_keyword",
        "create_include",
        "lincs_playbook",
        "settle_shake_playbook",
    }


def test_rename_action_is_the_only_safe_to_auto_apply_kind() -> None:
    kinds = code_action_kinds()
    auto = [k for k in kinds if k["safe_to_auto_apply"]]
    not_auto = [k for k in kinds if not k["safe_to_auto_apply"]]
    assert {k["kind"] for k in auto} == {"rename_mdp_keyword"}
    assert {k["kind"] for k in not_auto} == {
        "create_include",
        "lincs_playbook",
        "settle_shake_playbook",
    }


# --- levenshtein primitive -------------------------------------------------


def test_levenshtein_basic_distances() -> None:
    assert _levenshtein("nsteps", "nsteps") == 0
    assert _levenshtein("nstesp", "nsteps") == 2  # adjacent-letter swap
    assert _levenshtein("coulombtyp", "coulombtype") == 1
    assert _levenshtein("integrator", "integrator") == 0


# --- GMX002 typo rename ----------------------------------------------------


def test_gmx002_typo_action_renames_to_closest_known_key(tmp_path: Path) -> None:
    """A 1-edit typo must produce a rename action with a real WorkspaceEdit."""
    from gromacs_lsp.analyzer import KNOWN_MDP_KEYS

    diag = _mdp_typo_diagnostic(typo="coulombtyp", line=2)
    source_text = "integrator = md\ncoulombtyp = PME\nnsteps = 100\n"
    actions = actions_for_diagnostic(
        diag, known_mdp_keys=KNOWN_MDP_KEYS, source_text=source_text
    )
    assert len(actions) == 1
    action = actions[0]
    assert action["data"]["kind"] == "rename_mdp_keyword"
    assert action["data"]["from"] == "coulombtyp"
    assert action["data"]["to"] == "coulombtype"
    assert action["data"]["edit_distance"] == 1
    assert action["safe_to_auto_apply"] is True
    edit = action["edit"]
    assert edit is not None
    text_edit = edit["changes"][diag["path"]][0]
    assert text_edit["newText"] == "coulombtype"
    # Edit is anchored to the diagnostic line.
    assert text_edit["range"]["start"]["line"] == 2
    assert text_edit["range"]["end"]["line"] == 2


def test_gmx002_typo_action_handles_adjacent_swap(tmp_path: Path) -> None:
    """A 2-edit adjacent-letter swap (nstesp -> nsteps) still gets a rename."""
    from gromacs_lsp.analyzer import KNOWN_MDP_KEYS

    diag = _mdp_typo_diagnostic(typo="nstesp", line=1)
    source_text = "integrator = md\nnstesp = 100\ndt = 0.002\n"
    actions = actions_for_diagnostic(
        diag, known_mdp_keys=KNOWN_MDP_KEYS, source_text=source_text
    )
    assert len(actions) == 1
    action = actions[0]
    assert action["data"]["from"] == "nstesp"
    assert action["data"]["to"] == "nsteps"
    assert action["safe_to_auto_apply"] is True


def test_gmx002_typo_action_returns_none_when_distance_too_large() -> None:
    """A typo with no close neighbour must not surface a rename action."""
    from gromacs_lsp.analyzer import KNOWN_MDP_KEYS

    diag = _mdp_typo_diagnostic(typo="quantum_atoms")
    actions = actions_for_diagnostic(diag, known_mdp_keys=KNOWN_MDP_KEYS)
    # quantum_atoms is not close to any known key, so no rename action.
    assert actions == []


def test_gmx002_typo_action_without_source_text_still_emits_action() -> None:
    """Without source_text the action still surfaces but edit is None."""
    from gromacs_lsp.analyzer import KNOWN_MDP_KEYS

    diag = _mdp_typo_diagnostic(typo="coulombtyp")
    actions = actions_for_diagnostic(diag, known_mdp_keys=KNOWN_MDP_KEYS)
    assert len(actions) == 1
    action = actions[0]
    assert action["safe_to_auto_apply"] is True
    # The action still advertises the rename, the caller just has to build
    # the edit itself because we did not give it the source text.
    assert action["edit"] is None
    assert action["data"]["to"] == "coulombtype"


# --- GMX023 missing include ------------------------------------------------


def test_gmx023_missing_include_action_surfaces_path() -> None:
    diag = _missing_include_diagnostic(path="missing.itp")
    actions = actions_for_diagnostic(diag)
    assert len(actions) == 1
    action = actions[0]
    assert action["data"]["kind"] == "create_include"
    assert action["data"]["path"] == "missing.itp"
    # Creating an empty file is a workspace policy decision; not auto-applied.
    assert action["safe_to_auto_apply"] is False
    assert action["edit"] is None
    assert "missing.itp" in action["title"]


def test_gmx023_action_recovers_path_from_message_when_hint_missing() -> None:
    diag = _missing_include_diagnostic(path="recovered.itp")
    diag["fix_hints"] = []
    actions = actions_for_diagnostic(diag)
    assert len(actions) == 1
    assert actions[0]["data"]["path"] == "recovered.itp"


# --- GMX402 / GMX403 log instability ---------------------------------------


def test_gmx402_lincs_action_emits_playbook() -> None:
    diag = _log_instability_diagnostic(code="GMX402")
    actions = actions_for_diagnostic(diag)
    assert len(actions) == 1
    action = actions[0]
    assert action["data"]["kind"] == "lincs_playbook"
    assert "Halve the integration time step" in action["data"]["steps"][0]
    assert action["safe_to_auto_apply"] is False


def test_gmx403_settle_shake_action_emits_playbook() -> None:
    diag = _log_instability_diagnostic(code="GMX403")
    actions = actions_for_diagnostic(diag)
    assert len(actions) == 1
    action = actions[0]
    assert action["data"]["kind"] == "settle_shake_playbook"
    assert "Halve the integration time step" in action["data"]["steps"][0]
    assert action["safe_to_auto_apply"] is False


# --- integration through the fix CLI operation -----------------------------


def test_fix_operation_emits_rename_action_for_typo(tmp_path: Path) -> None:
    """The ``fix`` operation must surface the rename action end-to-end."""
    from gromacs_lsp.tool import main

    p = tmp_path / "typo.mdp"
    p.write_text("integrator = md\nnstesp = 100\ndt = 0.002\n", encoding="utf-8")

    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    try:
        rc = main(["fix", str(p), "--line", "1", "--character", "0"])
    finally:
        sys.stdout = old_stdout
    assert rc == 0
    payload = json.loads(buf.getvalue())
    actions = payload["actions"]
    rename_actions = [
        a for a in actions if a["data"].get("kind") == "rename_mdp_keyword"
    ]
    assert len(rename_actions) == 1
    action = rename_actions[0]
    assert action["data"]["from"] == "nstesp"
    assert action["data"]["to"] == "nsteps"
    assert action["safe_to_auto_apply"] is True
    # The action carries a real WorkspaceEdit because the source text is
    # available through the fix operation path.
    edit = action["edit"]
    assert edit is not None
    text_edit = edit["changes"][str(p)][0]
    assert text_edit["newText"] == "nsteps"


def test_fix_operation_emits_create_action_for_missing_include(
    tmp_path: Path,
) -> None:
    """The ``fix`` operation must surface the create-include action."""
    from gromacs_lsp.tool import main

    p = tmp_path / "missing.top"
    p.write_text(
        '#include "absent.itp"\n'
        "[ moleculetype ]\nSOL 3\n[ atoms ]\n"
        "1 P1 1 SOL O 1 0.000 16.00\n"
        "[ system ]\nOne\n[ molecules ]\nSOL 1\n",
        encoding="utf-8",
    )

    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    try:
        rc = main(["fix", str(p), "--line", "0", "--character", "0"])
    finally:
        sys.stdout = old_stdout
    assert rc == 0
    payload = json.loads(buf.getvalue())
    actions = payload["actions"]
    create_actions = [a for a in actions if a["data"].get("kind") == "create_include"]
    assert len(create_actions) == 1
    assert create_actions[0]["data"]["path"] == "absent.itp"


def test_code_actions_cli_emits_exported_kinds() -> None:
    """``gromacs-lsp-tool code-actions`` emits the kind surface for OpenQC."""
    from gromacs_lsp.tool import code_actions_main

    payload = json.loads(code_actions_main([]))
    assert payload["operation"] == "code-actions"
    assert payload["software"] == "gromacs"
    kinds = payload["kinds"]
    assert {k["kind"] for k in kinds} == {
        "rename_mdp_keyword",
        "create_include",
        "lincs_playbook",
        "settle_shake_playbook",
    }


def test_fix_operation_emits_playbook_for_lincs_log(tmp_path: Path) -> None:
    """The ``fix`` operation on a log file must surface the LINCS playbook."""
    from gromacs_lsp.tool import main

    log = tmp_path / "md.log"
    log.write_text(
        "step 100: warning: LINCS warnings. Wrote pdb.\n"
        "Back Off! step 100\n"
        "Back Off! step 101\n",
        encoding="utf-8",
    )

    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    try:
        rc = main(["fix", str(log), "--line", "0", "--character", "0"])
    finally:
        sys.stdout = old_stdout
    assert rc == 0
    payload = json.loads(buf.getvalue())
    actions = payload["actions"]
    playbook = [a for a in actions if a["data"].get("kind") == "lincs_playbook"]
    assert len(playbook) == 1
    assert playbook[0]["safe_to_auto_apply"] is False
    assert "Halve the integration time step" in playbook[0]["data"]["steps"][0]


def test_fix_operation_emits_playbook_for_settle_shake_log(tmp_path: Path) -> None:
    """The ``fix`` operation on a log file must surface the SETTLE/SHAKE playbook."""
    from gromacs_lsp.tool import main

    log = tmp_path / "md.log"
    log.write_text(
        "Step 50, time 0.1 (ps)\nSHAKE error on molecules SOL 1234\n",
        encoding="utf-8",
    )

    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    try:
        rc = main(["fix", str(log), "--line", "0", "--character", "0"])
    finally:
        sys.stdout = old_stdout
    assert rc == 0
    payload = json.loads(buf.getvalue())
    actions = payload["actions"]
    playbook = [a for a in actions if a["data"].get("kind") == "settle_shake_playbook"]
    assert len(playbook) == 1
    assert playbook[0]["safe_to_auto_apply"] is False


# --- golden fixtures -------------------------------------------------------

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "code_actions"


def test_typo_mdp_key_fixture_matches_golden() -> None:
    """The fixture MDP must produce a rename action that matches the golden."""
    from gromacs_lsp.analyzer import KNOWN_MDP_KEYS, analyze_file
    from gromacs_lsp.code_actions import actions_for_diagnostic
    from gromacs_lsp.rich_diagnostics import diagnostic_to_dict

    fixture = FIXTURES / "typo_mdp_key.mdp"
    golden = json.loads((FIXTURES / "typo_mdp_key.json").read_text(encoding="utf-8"))

    # Only the GMX002 diagnostic on the typo line is in scope. Diagnostic.line
    # is 1-based; the golden JSON carries that line number explicitly so the
    # fixture can grow without breaking the test.
    diags = [
        d
        for d in analyze_file(fixture)
        if d.code == "GMX002" and d.line == golden["diagnostic_line_1based"]
    ]
    assert diags, "fixture must emit at least one GMX002 on the typo line"
    rich = diagnostic_to_dict(diags[0], software="gromacs", file_type="mdp")
    source_text = fixture.read_text(encoding="utf-8")
    actions = actions_for_diagnostic(
        rich, known_mdp_keys=KNOWN_MDP_KEYS, source_text=source_text
    )
    assert len(actions) == 1
    action = actions[0]
    assert action["data"]["kind"] == golden["kind"]
    assert action["diagnostic_code"] == golden["diagnostic_code"]
    assert action["safe_to_auto_apply"] == golden["safe_to_auto_apply"]
    assert action["data"]["from"] == golden["rename"]["from"]
    assert action["data"]["to"] == golden["rename"]["to"]
    assert action["data"]["edit_distance"] == golden["rename"]["edit_distance"]
    edit = action["edit"]
    assert edit is not None
    text_edit = edit["changes"][str(fixture)][0]
    assert text_edit["newText"] == golden["new_text"]
    assert text_edit["range"]["start"] == golden["edit_range"]["start"]
    assert text_edit["range"]["end"] == golden["edit_range"]["end"]


def test_missing_include_fixture_matches_golden() -> None:
    """The fixture topology must produce a create-include action."""
    from gromacs_lsp.analyzer import analyze_file
    from gromacs_lsp.code_actions import actions_for_diagnostic
    from gromacs_lsp.rich_diagnostics import diagnostic_to_dict

    fixture = FIXTURES / "missing_include.top"
    golden = json.loads((FIXTURES / "missing_include.json").read_text(encoding="utf-8"))

    diags = [d for d in analyze_file(fixture) if d.code == "GMX023"]
    assert diags, "fixture must emit at least one GMX023"
    rich = diagnostic_to_dict(diags[0], software="gromacs", file_type="top")
    actions = actions_for_diagnostic(rich)
    assert len(actions) == 1
    action = actions[0]
    assert action["data"]["kind"] == golden["kind"]
    assert action["diagnostic_code"] == golden["diagnostic_code"]
    assert action["safe_to_auto_apply"] == golden["safe_to_auto_apply"]
    assert action["data"]["path"] == golden["include_path"]
    assert golden["title_contains"] in action["title"]


def test_valid_mdp_fixture_emits_no_typo_actions() -> None:
    """The valid MDP fixture must not produce any rename actions."""
    from gromacs_lsp.analyzer import KNOWN_MDP_KEYS, analyze_file
    from gromacs_lsp.code_actions import actions_for_diagnostic
    from gromacs_lsp.rich_diagnostics import diagnostic_to_dict

    fixture = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "rules"
        / "valid_mdp_parameters.mdp"
    )
    diags = [d for d in analyze_file(fixture) if d.code == "GMX002"]
    assert diags == []
    # Sanity: even if a GMX002 were present, no action would fire.
    for d in analyze_file(fixture):
        rich = diagnostic_to_dict(d, software="gromacs", file_type="mdp")
        actions = actions_for_diagnostic(rich, known_mdp_keys=KNOWN_MDP_KEYS)
        assert not any(a["data"].get("kind") == "rename_mdp_keyword" for a in actions)


def test_valid_topology_includes_fixture_emits_no_create_actions() -> None:
    """The valid topology fixture must not produce any create-include actions."""
    from gromacs_lsp.analyzer import analyze_file
    from gromacs_lsp.code_actions import actions_for_diagnostic
    from gromacs_lsp.rich_diagnostics import diagnostic_to_dict

    fixture = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "rules"
        / "valid_topology_includes.top"
    )
    diags = [d for d in analyze_file(fixture) if d.code == "GMX023"]
    assert diags == []
    for d in analyze_file(fixture):
        rich = diagnostic_to_dict(d, software="gromacs", file_type="top")
        actions = actions_for_diagnostic(rich)
        assert not any(a["data"].get("kind") == "create_include" for a in actions)
