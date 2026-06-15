"""LSP code actions for common gromacs-lsp diagnostics.

The agent operations layer (``agent_operations._fix_actions``) emits generic
"review this diagnostic" quick-fix hints for every diagnostic. That keeps the
fallback path safe, but the OpenQC ``code-actions`` capability contract
(``newtontech/gromacs-lsp#23``) requires concrete, evidence-backed code actions
for the diagnostic codes where a safe fix already exists:

* ``gromacs.mdp.unknown_parameter`` (``GMX002``) — offer to rename a typo'd
  MDP key to its closest valid neighbour when the Levenshtein distance is
  small enough to be an obvious typo. The action carries a real
  ``WorkspaceEdit`` and is flagged ``safe_to_auto_apply`` so editor/agent
  consumers can apply it without re-confirming.
* ``gromacs.topology.missing_include`` (``GMX023``) — offer to create the
  referenced ``#include`` file (the editor/agent still owns the file creation
  step) and to open the parent directory. The action is *not* auto-applied
  because creating an empty file is a policy decision the caller must make.
* ``gromacs.log.lincs_instability`` / ``gromacs.log.settle_shake_failure``
  (``GMX402``/``GMX403``) — surface the standard stability remediation
  playbook (reduce ``dt`` / revisit ``constraints`` / re-equilibrate) as a
  hint action anchored on the offending log line.

Code actions stay inside the LSP repo per the issue implementation boundary;
OpenQC only consumes the serialized JSON.

See also: wiki/synthesis/lsp-features.md
"""

from __future__ import annotations

from typing import Any, Iterable

# Maximum edit distance at which we still classify an unknown MDP key as an
# obvious typo of a known key. Tuned so:
#   * "nstesp" -> "nsteps" (distance 1) qualifies
#   * "coulombtyp" -> "coulombtype" (distance 1) qualifies
#   * "quantum_atoms" -> any known key is well above the threshold (no fix)
_TYPO_MAX_DISTANCE = 2

# Diagnostic codes that this module produces concrete actions for. Used by
# ``code_action_kinds`` so consumers can discover the action surface without
# scanning every diagnostic in a payload.
HANDLED_CODES: frozenset[str] = frozenset({"GMX002", "GMX023", "GMX402", "GMX403"})


def _levenshtein(a: str, b: str) -> int:
    """Standard iterative Levenshtein distance, case-sensitive."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            substitute = previous[j - 1] + (ca != cb)
            current.append(min(insert, delete, substitute))
        previous = current
    return previous[-1]


def _closest_known_mdp_key(
    typo: str, known_keys: Iterable[str]
) -> tuple[str | None, int]:
    """Return ``(closest_key, distance)`` for ``typo`` against ``known_keys``.

    Distance is the Levenshtein distance, case-sensitive. Returns
    ``(None, ...)`` when ``known_keys`` is empty.
    """
    best: tuple[str | None, int] = (None, max(len(typo), 1) + _TYPO_MAX_DISTANCE + 1)
    for key in known_keys:
        # Lower-bound prune: a key whose length differs by more than the
        # threshold cannot be within the threshold, so skip the O(n*m) loop.
        if abs(len(key) - len(typo)) > _TYPO_MAX_DISTANCE:
            continue
        distance = _levenshtein(typo, key)
        if distance < best[1] or (distance == best[1] and best[0] is None):
            best = (key, distance)
    return best


def _text_edit_for_key_rename(
    line_text: str, old_key: str, new_key: str
) -> dict[str, Any]:
    """Build a single-line LSP ``TextEdit`` replacing ``old_key`` with ``new_key``.

    The edit replaces only the key token, preserving the surrounding
    whitespace and the ``= value`` portion of the line so the editor applies
    the smallest possible change.
    """
    start_char = line_text.find(old_key)
    if start_char < 0:
        # Fall back to the start of the line; the caller still gets a useful
        # action that renames the entire line if the key cannot be located.
        start_char = 0
        end_char = len(line_text)
    else:
        end_char = start_char + len(old_key)
    return {
        "range": {
            "start": {"line": 0, "character": start_char},
            "end": {"line": 0, "character": end_char},
        },
        "newText": new_key,
    }


def _mdp_typo_action(
    diagnostic: dict[str, Any],
    known_keys: Iterable[str],
    *,
    source_text: str | None = None,
) -> dict[str, Any] | None:
    """Build a rename action for an unknown-MDP-parameter diagnostic.

    Returns ``None`` when no known key is within ``_TYPO_MAX_DISTANCE`` of the
    typo'd keyword, so consumers only see actionable suggestions.
    """
    hint = _first_fix_hint(diagnostic)
    typo = (
        hint.get("keyword")
        if isinstance(hint, dict)
        else _extract_keyword_from_message(diagnostic.get("message", ""))
    )
    if not typo:
        return None
    closest, distance = _closest_known_mdp_key(str(typo), known_keys)
    if closest is None or distance > _TYPO_MAX_DISTANCE or closest == str(typo):
        return None
    range_ = diagnostic.get("range") or {}
    start = (range_.get("start") or {}).get("line", 0)
    edit = None
    if source_text is not None:
        lines = source_text.splitlines()
        if 0 <= start < len(lines):
            line_text = lines[start]
            text_edit = _text_edit_for_key_rename(line_text, str(typo), closest)
            # Re-anchor the text edit to the actual line number so the
            # WorkspaceEdit applies at the right place in the document.
            text_edit["range"]["start"]["line"] = start
            text_edit["range"]["end"]["line"] = start
            edit = {"changes": {diagnostic.get("path") or "": [text_edit]}}
    title = f"Rename '{typo}' to '{closest}'"
    return {
        "title": title,
        "kind": "quickfix",
        "diagnostic_code": diagnostic.get("code"),
        "diagnostic_range": range_,
        "confidence": _confidence_for_distance(distance),
        "blocking": bool(diagnostic.get("blocking", False)),
        "safe_to_auto_apply": True,
        "edit": edit,
        "data": {
            "kind": "rename_mdp_keyword",
            "from": typo,
            "to": closest,
            "edit_distance": distance,
            "source": diagnostic.get("source"),
        },
    }


def _confidence_for_distance(distance: int) -> float:
    """Confidence falls off as the edit distance grows from 1 to the cutoff."""
    if distance <= 1:
        return 0.95
    if distance == 2:
        return 0.8
    return 0.6


def _missing_include_action(diagnostic: dict[str, Any]) -> dict[str, Any] | None:
    """Build a "create the missing #include file" hint action."""
    hint = _first_fix_hint(diagnostic)
    include = (
        hint.get("include")
        if isinstance(hint, dict)
        else _extract_include_from_message(diagnostic.get("message", ""))
    )
    if not include:
        return None
    title = f"Create missing include '{include}'"
    return {
        "title": title,
        "kind": "quickfix",
        "diagnostic_code": diagnostic.get("code"),
        "diagnostic_range": diagnostic.get("range"),
        "confidence": 0.7,
        "blocking": bool(diagnostic.get("blocking", False)),
        # Creating an empty file is a workspace policy decision; the action
        # carries the path so the caller can apply it, but we do not flag it
        # safe for blind auto-application.
        "safe_to_auto_apply": False,
        "edit": None,
        "data": {
            "kind": "create_include",
            "path": include,
            "source": diagnostic.get("source"),
        },
    }


def _log_instability_action(diagnostic: dict[str, Any], *, kind: str) -> dict[str, Any]:
    """Build the standard stability remediation playbook action.

    ``kind`` is ``"lincs"`` or ``"settle_shake"`` so consumers can branch on
    the underlying constraint family.
    """
    if kind == "lincs":
        title = "Reduce dt / relax constraints (LINCS instability)"
        playbook = [
            "Halve the integration time step (dt) and re-equilibrate.",
            "Switch constraints=h-bonds if currently all-bonds to loosen the network.",
            "Run grompp with -maxwarn only after diagnosing the source of instability.",
        ]
    else:  # settle_shake
        title = "Reduce dt / revisit water topology (SETTLE/SHAKE failure)"
        playbook = [
            "Halve the integration time step (dt) and re-equilibrate.",
            "Verify the solvent topology matches the .gro coordinate file.",
            "If using SHAKE on heavy-atom hydrogens, switch to SETTLE for water.",
        ]
    return {
        "title": title,
        "kind": "quickfix",
        "diagnostic_code": diagnostic.get("code"),
        "diagnostic_range": diagnostic.get("range"),
        "confidence": 0.85,
        "blocking": bool(diagnostic.get("blocking", False)),
        # Playbook actions touch MDP / topology files the diagnostic does not
        # own, so they are surfaced as hints rather than blind edits.
        "safe_to_auto_apply": False,
        "edit": None,
        "data": {
            "kind": f"{kind}_playbook",
            "steps": playbook,
            "source": diagnostic.get("source"),
        },
    }


def _first_fix_hint(diagnostic: dict[str, Any]) -> Any:
    hints = diagnostic.get("fix_hints") or []
    if hints and isinstance(hints, list):
        return hints[0]
    return None


def _extract_keyword_from_message(message: str) -> str | None:
    """Recover the offending MDP key from the analyzer's GMX002 message.

    The analyzer emits ``"unknown or currently unsupported MDP key: <key>"``,
    so we split on the colon and strip whitespace. Used only when the
    structured fix hint is missing.
    """
    if ":" not in message:
        return None
    tail = message.split(":", 1)[1].strip()
    return tail or None


def _extract_include_from_message(message: str) -> str | None:
    """Recover the missing include path from a GMX023 message.

    The analyzer wraps the path in single quotes, e.g.
    ``"... could not be resolved: 'foo.itp'"``.
    """
    if "'" not in message:
        return None
    parts = message.split("'")
    if len(parts) < 3:
        return None
    candidate = parts[1].strip()
    return candidate or None


def code_action_kinds() -> list[dict[str, Any]]:
    """Return the exported code-action surface for OpenQC discovery.

    Each entry is a stable kind identifier plus a short description, so an
    OpenQC consumer can branch on ``data.kind`` without parsing the title.
    """
    return [
        {
            "kind": "rename_mdp_keyword",
            "description": (
                "Rename a typo'd MDP key to the closest valid neighbour "
                "when the edit distance is small enough to be an obvious typo."
            ),
            "safe_to_auto_apply": True,
            "evidence_codes": ["GMX002"],
        },
        {
            "kind": "create_include",
            "description": (
                "Surface the path of a missing topology #include so the "
                "caller can create it next to the parent topology."
            ),
            "safe_to_auto_apply": False,
            "evidence_codes": ["GMX023"],
        },
        {
            "kind": "lincs_playbook",
            "description": (
                "Stability remediation playbook for a LINCS instability "
                "reported in a runtime log file."
            ),
            "safe_to_auto_apply": False,
            "evidence_codes": ["GMX402"],
        },
        {
            "kind": "settle_shake_playbook",
            "description": (
                "Stability remediation playbook for a SETTLE/SHAKE constraint "
                "solver failure reported in a runtime log file."
            ),
            "safe_to_auto_apply": False,
            "evidence_codes": ["GMX403"],
        },
    ]


def actions_for_diagnostic(
    diagnostic: dict[str, Any],
    *,
    known_mdp_keys: Iterable[str] | None = None,
    source_text: str | None = None,
) -> list[dict[str, Any]]:
    """Return concrete code actions for ``diagnostic`` (may be empty).

    Parameters
    ----------
    diagnostic:
        A serialized ``DiagnosticEnvelope/v1`` diagnostic.
    known_mdp_keys:
        Known valid MDP keys. Required for ``GMX002`` typo actions; ignored
        otherwise. Typically the analyzer's ``KNOWN_MDP_KEYS`` set.
    source_text:
        Full source text of the document the diagnostic is anchored to.
        Required to produce a ``WorkspaceEdit`` for key-rename actions;
        without it the action still surfaces but carries ``edit=None``.
    """
    code = diagnostic.get("code")
    actions: list[dict[str, Any]] = []
    if code == "GMX002" and known_mdp_keys is not None:
        action = _mdp_typo_action(diagnostic, known_mdp_keys, source_text=source_text)
        if action is not None:
            actions.append(action)
    elif code == "GMX023":
        action = _missing_include_action(diagnostic)
        if action is not None:
            actions.append(action)
    elif code == "GMX402":
        actions.append(_log_instability_action(diagnostic, kind="lincs"))
    elif code == "GMX403":
        actions.append(_log_instability_action(diagnostic, kind="settle_shake"))
    return actions
