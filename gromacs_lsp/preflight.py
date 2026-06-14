"""Universal generated-input preflight capabilities.

This module implements the four fleet-wide preflight capabilities called out in
``newtontech/gromacs-lsp#29`` against a *generic artifact-role model*, so the
checks generalize across the scientific LSP fleet instead of being wired to
MatMaster submission policy:

* ``version-aware-keywords``  - explicit runtime/version assumption metadata
  (GROMACS release / runtime image) surfaced at the envelope top level and as a
  ``GMXPREF109`` information diagnostic when the exact version is unknown, plus
  unknown/typo'd ``.mdp`` parameter detection (``GMXPREF110``) reusing the
  analyzer's keyword set.
* ``cross-artifact-graph``   - resolves the case as a graph of artifacts with
  stable roles (primary-input ``.mdp``, topology ``.top``/``.itp``, coordinate
  ``.gro``/``.pdb``, index ``.ndx``). Cross-file checks operate on the graph
  rather than ad-hoc file names: missing primary input (``GMXPREF101``),
  unreadable/empty input (``GMXPREF102``), unresolved topology ``#include``
  (``GMXPREF103``), molecule defined in ``[ moleculetype ]`` but absent from
  ``[ molecules ]`` or vice-versa (``GMXPREF104``), referenced coordinate file
  missing (``GMXPREF105``), referenced index file missing (``GMXPREF106``).
* ``code-actions``           - normalizes repair hints/actions on every
  diagnostic and exposes a blocking gate the agent CLI can run as
  ``check --fail-on-blocking`` and ``preflight --fail-on-blocking``.
* ``fleet-regression-fixtures`` - ``fleet_manifest`` returns a machine-readable
  description of the preflight surface (codes, capabilities, roles) and merges
  per-case fixture expectations so the parent ``bohrium_skills`` probe/report
  workflow can consume regression evidence without re-deriving it.

The diagnostics emitted here are plain dictionaries (not the legacy
``Diagnostic`` dataclass) so they can carry the richer ``DiagnosticEnvelope/v1``
fields (``source_provenance``, ``domain_tags``, ``facts``, ``artifact_roles``,
``version_assumption``, ``actions``) directly.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .analyzer import SECTION_RE, _INCLUDE_RE
from .hover import _MDP_DOCS

# --- Artifact-role model ---------------------------------------------------

# Generic roles. These are intentionally software-agnostic: every fleet backend
# can map its native files onto this same small role set, which is what lets the
# parent router consume cross-file checks without learning MatMaster specifics.
ROLE_PRIMARY_INPUT = "primary-input"
ROLE_TOPOLOGY = "topology"
ROLE_COORDINATE = "coordinate"
ROLE_INDEX = "index"

ALL_ROLES = (
    ROLE_PRIMARY_INPUT,
    ROLE_TOPOLOGY,
    ROLE_COORDINATE,
    ROLE_INDEX,
)

# Molecule name captured from the first whitespace-separated token of a
# ``[ moleculetype ]`` or ``[ molecules ]`` body record.
_TOPOLOGY_RECORD_RE = re.compile(r"^(\S+)\s+\S+")
# Shared force-field includes (``amber99sb-ildn.ff/forcefield.itp``) are
# resolved by grompp against the GROMACS shared data directory, which the LSP
# editor cannot see. Only flag includes that look like local files.
_FORCEFIELD_INCLUDE_MARKER = ".ff/"

# Codes reserved for the universal preflight surface. They use the ``GMXPREF1xx``
# band so they sort after the existing GMX rule codes and stay identifiable as
# cross-fleet preflight findings.
CODE_MISSING_PRIMARY_INPUT = "GMXPREF101"
CODE_UNREADABLE_INPUT = "GMXPREF102"
CODE_UNRESOLVED_TOPOLOGY_INCLUDE = "GMXPREF103"
CODE_MOLECULE_DECLARATION_MISMATCH = "GMXPREF104"
CODE_MISSING_COORDINATE = "GMXPREF105"
CODE_MISSING_INDEX = "GMXPREF106"
CODE_EMPTY_MDP = "GMXPREF107"
CODE_MISSING_REQUIRED_MDP_KEY = "GMXPREF108"
CODE_VERSION_ASSUMPTION = "GMXPREF109"
CODE_UNKNOWN_MDP_PARAMETER = "GMXPREF110"

# ``.mdp`` keys the analyzer treats as required for a runnable integration.
REQUIRED_MDP_KEYS = ("integrator", "nsteps", "dt")

# Known ``.mdp`` parameter set, reused from the analyzer's hover docs so the
# preflight never duplicates the keyword list. A ``.mdp`` parameter not in this
# set is flagged as a likely typo (GROMACS silently ignores unknown mdp options,
# which masks misspelled settings).
KNOWN_MDP_KEYS = set(_MDP_DOCS.keys())


@dataclass(frozen=True)
class ArtifactNode:
    """A node in the cross-artifact graph.

    ``role`` is one of the fleet-generic roles above; ``path`` is the resolved
    filesystem path (may be a non-existent reference, which is itself a
    finding); ``source`` records where the reference originated so consumers
    can trace provenance.
    """

    role: str
    path: Path
    exists: bool
    source: str
    referenced_from: tuple[str, int] | None = None
    detail: dict[str, Any] | None = None


@dataclass
class ArtifactGraph:
    """Generic cross-artifact graph built from a parsed case directory."""

    case_dir: Path
    nodes: list[ArtifactNode] = field(default_factory=list)

    def by_role(self, role: str) -> list[ArtifactNode]:
        return [node for node in self.nodes if node.role == role]

    def to_json(self) -> list[dict[str, Any]]:
        """Serialize the graph for the parent probe/report workflow."""

        def _node_json(node: ArtifactNode) -> dict[str, Any]:
            payload: dict[str, Any] = {
                "role": node.role,
                "path": str(node.path),
                "exists": node.exists,
                "source": node.source,
            }
            if node.referenced_from is not None:
                payload["referenced_from"] = {
                    "path": node.referenced_from[0],
                    "line": node.referenced_from[1],
                }
            if node.detail:
                payload["detail"] = node.detail
            return payload

        return sorted(
            (_node_json(node) for node in self.nodes),
            key=lambda item: (item["role"], item["path"]),
        )


def _read_mdp_settings(mdp_path: Path) -> tuple[dict[str, str], dict[str, int]]:
    """Parse ``key = value`` settings from a ``.mdp`` file.

    Returns ``(parameters, parameter_lines)``. Comments (``;``) and
    preprocessor directives (``#``) are skipped, matching the analyzer's
    ``_analyze_mdp`` reading rules. Reused here instead of re-implementing the
    analyzer's parser so the keyword set stays in one place.
    """
    parameters: dict[str, str] = {}
    parameter_lines: dict[str, int] = {}
    try:
        content = mdp_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return parameters, parameter_lines
    for line_no, raw in enumerate(content.splitlines(), start=1):
        line = raw.split(";", 1)[0].strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        parameters[key.lower()] = value
        parameter_lines[key.lower()] = line_no
    return parameters, parameter_lines


def _parse_topology_molecules(
    top_path: Path,
) -> tuple[set[str], list[tuple[str, int]], list[tuple[str, int]]]:
    """Return ``(moleculetype_names, molecules_entries, local_includes)``.

    Reuses the same ``SECTION_RE`` / ``_INCLUDE_RE`` / record pattern as the
    analyzer so molecule-name capture never drifts from the analyzer's own
    ``[ molecules ]`` cross-reference logic.
    """
    moleculetype_names: set[str] = set()
    molecules_entries: list[tuple[str, int]] = []
    local_includes: list[tuple[str, int]] = []
    current_section: str | None = None
    try:
        content = top_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return moleculetype_names, molecules_entries, local_includes
    for line_no, raw in enumerate(content.splitlines(), start=1):
        section_match = SECTION_RE.match(raw)
        if section_match:
            current_section = section_match.group(1).strip().lower()
            continue
        stripped = raw.split(";", 1)[0].strip()
        if current_section in {"moleculetype", "molecules"}:
            record_match = _TOPOLOGY_RECORD_RE.match(stripped)
            if record_match:
                record_name = record_match.group(1)
                if current_section == "moleculetype":
                    moleculetype_names.add(record_name)
                else:
                    molecules_entries.append((record_name, line_no))
        include_match = _INCLUDE_RE.match(stripped)
        if include_match:
            include_target = include_match.group(1).strip()
            if _FORCEFIELD_INCLUDE_MARKER in include_target:
                continue
            local_includes.append((include_target, line_no))
    return moleculetype_names, molecules_entries, local_includes


def build_artifact_graph(case_dir: Path, mdp_path: Path) -> ArtifactGraph:
    """Build the cross-artifact graph from a parsed GROMACS case directory.

    The model is generic: it records roles + resolved paths + provenance. The
    same shape generalizes to other fleet backends because it never bakes in
    MatMaster/Bohrium runtime concepts (no input_dir, no image, no session).
    """
    case_dir = case_dir.resolve()
    graph = ArtifactGraph(case_dir=case_dir)

    graph.nodes.append(
        ArtifactNode(
            role=ROLE_PRIMARY_INPUT,
            path=mdp_path,
            exists=mdp_path.exists(),
            source="case-root",
        )
    )

    parameters, _ = _read_mdp_settings(mdp_path)

    # Coordinate file: ``cutoff-scheme`` runs reference a structure file via the
    # ``structure`` mdp option, or conventionally a sibling ``.gro``/``.pdb``.
    coordinate_target = parameters.get("structure") or ""
    coordinate_path: Path | None = None
    coordinate_source = ""
    coordinate_line: tuple[str, int] | None = None
    if coordinate_target:
        coordinate_path = (case_dir / coordinate_target).resolve()
        coordinate_source = f"MDP:structure={coordinate_target}"
        coordinate_line = (
            str(mdp_path),
            _read_mdp_settings(mdp_path)[1].get("structure", 1),
        )
    else:
        for name in ("conf.gro", "input.gro", "system.gro", "pos.gro"):
            candidate = case_dir / name
            if candidate.exists():
                coordinate_path = candidate.resolve()
                coordinate_source = "case-root:convention"
                break
        if coordinate_path is None:
            for candidate in sorted(case_dir.glob("*.gro")):
                coordinate_path = candidate.resolve()
                coordinate_source = "case-root:glob"
                break
    if coordinate_path is not None:
        graph.nodes.append(
            ArtifactNode(
                role=ROLE_COORDINATE,
                path=coordinate_path,
                exists=coordinate_path.exists(),
                source=coordinate_source,
                referenced_from=coordinate_line,
                detail={"declared_name": coordinate_target or None},
            )
        )

    # Index file: ``index`` mdp option, or conventionally ``index.ndx``.
    index_target = parameters.get("index") or ""
    index_path: Path | None = None
    index_source = ""
    index_line: tuple[str, int] | None = None
    if index_target:
        index_path = (case_dir / index_target).resolve()
        index_source = f"MDP:index={index_target}"
        index_line = (
            str(mdp_path),
            _read_mdp_settings(mdp_path)[1].get("index", 1),
        )
        graph.nodes.append(
            ArtifactNode(
                role=ROLE_INDEX,
                path=index_path,
                exists=index_path.exists(),
                source=index_source,
                referenced_from=index_line,
                detail={"declared_name": index_target},
            )
        )

    # Topology: a sibling ``.top`` (the entry point that ``#include``s ``.itp``
    # fragments). The first ``.top`` in the case dir is treated as primary.
    top_path: Path | None = None
    for candidate in sorted(case_dir.glob("*.top")):
        top_path = candidate.resolve()
        break
    if top_path is not None:
        graph.nodes.append(
            ArtifactNode(
                role=ROLE_TOPOLOGY,
                path=top_path,
                exists=top_path.exists(),
                source="case-root:*.top",
                detail={"includes": []},
            )
        )

    return graph


# --- Preflight diagnostics -------------------------------------------------


def preflight_diagnostics(
    case_dir: Path,
    *,
    intent: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], ArtifactGraph]:
    """Run universal generated-input preflight checks.

    Returns a tuple of ``(diagnostics, artifact_graph)``. Diagnostics are
    envelope dicts carrying the full ``DiagnosticEnvelope/v1`` field set so the
    agent CLI can emit them directly without re-shaping.
    """
    case_dir = case_dir.resolve()
    mdp_path = _locate_primary_input(case_dir)
    graph = build_artifact_graph(case_dir, mdp_path) if mdp_path else ArtifactGraph(case_dir=case_dir)
    version_assumption = resolve_version_assumption(intent)
    diagnostics: list[dict[str, Any]] = []

    if mdp_path is None:
        diagnostics.extend(_missing_primary_input_diagnostics(case_dir))
    else:
        diagnostics.extend(_unreadable_input_diagnostics(mdp_path))
        diagnostics.extend(_empty_mdp_diagnostics(mdp_path))
        diagnostics.extend(_missing_required_mdp_key_diagnostics(mdp_path))
        diagnostics.extend(_unknown_mdp_parameter_diagnostics(mdp_path, version_assumption))
        diagnostics.extend(_missing_coordinate_diagnostics(graph))
        diagnostics.extend(_missing_index_diagnostics(graph))
        diagnostics.extend(_unresolved_topology_include_diagnostics(graph))
        diagnostics.extend(_molecule_declaration_mismatch_diagnostics(graph))

    diagnostics.extend(_version_assumption_diagnostic(version_assumption, intent))

    return sorted(
        diagnostics,
        key=lambda item: (
            item.get("range", {}).get("start", {}).get("line", 0),
            item.get("range", {}).get("start", {}).get("character", 0),
            item["code"],
        ),
    ), graph


def _locate_primary_input(case_dir: Path) -> Path | None:
    """Find the primary ``.mdp`` input in a case directory.

    Prefers ``grompp.mdp`` / ``run.mdp`` / ``md.mdp`` then falls back to the
    first ``.mdp`` sibling. Returns ``None`` when no ``.mdp`` exists.
    """
    for name in ("grompp.mdp", "run.mdp", "md.mdp", "minim.mdp", "em.mdp"):
        candidate = case_dir / name
        if candidate.exists():
            return candidate
    for candidate in sorted(case_dir.glob("*.mdp")):
        return candidate
    return None


def _diag(
    *,
    code: str,
    severity: str,
    message: str,
    path: Path,
    line: int = 1,
    column: int = 1,
    category: str,
    confidence: float,
    blocking: bool,
    source_provenance: dict[str, Any],
    fix_hints: list[str],
    actions: list[dict[str, Any]] | None = None,
    facts: dict[str, Any] | None = None,
    artifact_roles: list[str] | None = None,
    domain_tags: list[str] | None = None,
    version_assumption: dict[str, Any] | None = None,
    manual_ref: str | None = None,
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a single normalized preflight diagnostic.

    Carries every field the issue acceptance criteria require (``code``,
    ``severity``, ``path``/``range``, ``blocking``, ``category``,
    ``source_provenance``, ``fix_hints``/``actions``) plus the richer envelope
    fields (``facts``, ``artifact_roles``, ``domain_tags``,
    ``version_assumption``) used by the parent fleet probe.
    """
    line0 = max(line - 1, 0)
    col0 = max(column - 1, 0)
    payload: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
        "file": str(path),
        "line": line,
        "column": column,
        "category": category,
        "confidence": confidence,
        "source": "gromacs-preflight",
        "range": {
            "start": {"line": line0, "character": col0},
            "end": {"line": line0, "character": col0 + 1},
        },
        "blocking": blocking,
        "fix_hints": fix_hints,
        "source_provenance": source_provenance,
    }
    if actions:
        payload["actions"] = actions
    if facts:
        payload["facts"] = facts
    if artifact_roles:
        payload["artifact_roles"] = artifact_roles
    if domain_tags:
        payload["domain_tags"] = domain_tags
    if version_assumption:
        payload["version_assumption"] = version_assumption
    if manual_ref:
        payload["manual_ref"] = manual_ref
    if intent:
        payload["intent"] = intent
    return payload


def _missing_primary_input_diagnostics(case_dir: Path) -> list[dict[str, Any]]:
    return [
        _diag(
            code=CODE_MISSING_PRIMARY_INPUT,
            severity="error",
            message=(
                "no primary GROMACS input (.mdp) found in the case directory"
            ),
            path=case_dir / "grompp.mdp",
            line=1,
            category="cross-file reference",
            confidence=0.97,
            blocking=True,
            source_provenance={
                "role": ROLE_PRIMARY_INPUT,
                "reason": "no .mdp file found in case directory",
            },
            fix_hints=[
                "Add a .mdp run-parameter file (e.g. grompp.mdp)",
                "Or point gromacs-lsp at the directory containing it",
            ],
            actions=[
                {
                    "kind": "create_artifact",
                    "role": ROLE_PRIMARY_INPUT,
                    "target": str(case_dir / "grompp.mdp"),
                    "safe_to_auto_apply": False,
                }
            ],
            facts={"case_dir": str(case_dir)},
            artifact_roles=[ROLE_PRIMARY_INPUT],
            domain_tags=["cross-file", "blocking"],
        )
    ]


def _unreadable_input_diagnostics(mdp_path: Path) -> list[dict[str, Any]]:
    if not mdp_path.exists():
        return []
    try:
        mdp_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [
            _diag(
                code=CODE_UNREADABLE_INPUT,
                severity="error",
                message=f"primary input {mdp_path.name} could not be read as UTF-8 text",
                path=mdp_path,
                line=1,
                category="syntax",
                confidence=0.95,
                blocking=True,
                source_provenance={
                    "role": ROLE_PRIMARY_INPUT,
                    "reason": "read_text raised OSError/UnicodeDecodeError",
                },
                fix_hints=[
                    f"Restore or re-encode {mdp_path.name} as UTF-8 text",
                ],
                actions=[
                    {
                        "kind": "review_artifact",
                        "role": ROLE_PRIMARY_INPUT,
                        "target": str(mdp_path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"path": str(mdp_path)},
                artifact_roles=[ROLE_PRIMARY_INPUT],
                domain_tags=["syntax", "blocking"],
            )
        ]
    return []


def _empty_mdp_diagnostics(mdp_path: Path) -> list[dict[str, Any]]:
    parameters, _ = _read_mdp_settings(mdp_path)
    if parameters:
        return []
    return [
        _diag(
            code=CODE_EMPTY_MDP,
            severity="error",
            message=(
                f"primary input {mdp_path.name} declares no key = value settings"
            ),
            path=mdp_path,
            line=1,
            category="semantic consistency",
            confidence=0.9,
            blocking=True,
            source_provenance={
                "role": ROLE_PRIMARY_INPUT,
                "reason": "no parseable key=value lines found",
            },
            fix_hints=[
                "Populate the .mdp with integrator/nsteps/dt at minimum",
            ],
            actions=[
                {
                    "kind": "review_artifact",
                    "role": ROLE_PRIMARY_INPUT,
                    "target": str(mdp_path),
                    "safe_to_auto_apply": False,
                }
            ],
            facts={"parameter_count": 0},
            artifact_roles=[ROLE_PRIMARY_INPUT],
            domain_tags=["semantic", "blocking"],
        )
    ]


def _missing_required_mdp_key_diagnostics(mdp_path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    parameters, parameter_lines = _read_mdp_settings(mdp_path)
    for required in REQUIRED_MDP_KEYS:
        if required in parameters:
            continue
        out.append(
            _diag(
                code=CODE_MISSING_REQUIRED_MDP_KEY,
                severity="error",
                message=(
                    f"required .mdp key '{required}' is missing from {mdp_path.name}"
                ),
                path=mdp_path,
                line=1,
                category="schema",
                confidence=0.92,
                blocking=True,
                source_provenance={
                    "role": ROLE_PRIMARY_INPUT,
                    "keyword": required,
                    "reason": "key absent from .mdp",
                },
                fix_hints=[
                    f"Add '{required} = <value>' to {mdp_path.name}",
                ],
                actions=[
                    {
                        "kind": "set_keyword",
                        "keyword": required,
                        "target": str(mdp_path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"missing_key": required, "present_keys": sorted(parameters)},
                artifact_roles=[ROLE_PRIMARY_INPUT],
                domain_tags=["schema", "blocking"],
            )
        )
    return out


def _unknown_mdp_parameter_diagnostics(
    mdp_path: Path, version_assumption: dict[str, Any]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    parameters, parameter_lines = _read_mdp_settings(mdp_path)
    for key, value in parameters.items():
        if key in KNOWN_MDP_KEYS:
            continue
        line = parameter_lines.get(key, 1)
        out.append(
            _diag(
                code=CODE_UNKNOWN_MDP_PARAMETER,
                severity="error",
                message=(
                    f"unknown or currently unsupported .mdp key '{key}'; "
                    "GROMACS silently ignores unknown mdp options"
                ),
                path=mdp_path,
                line=line,
                category="schema",
                confidence=0.9,
                blocking=True,
                source_provenance={
                    "role": ROLE_PRIMARY_INPUT,
                    "keyword": key,
                    "schema_source": "gromacs-lsp builtin mdp docs",
                },
                fix_hints=[
                    f"Correct the likely typo '{key}'",
                    f"Or remove {key} if it is not a real GROMACS mdp option",
                ],
                actions=[
                    {
                        "kind": "check_mdp_keyword",
                        "keyword": key,
                        "target": str(mdp_path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={
                    "keyword": key,
                    "value": value,
                    "known_keys_sample": sorted(list(KNOWN_MDP_KEYS)[:10]),
                },
                artifact_roles=[ROLE_PRIMARY_INPUT],
                domain_tags=["schema", "version-aware", "blocking"],
                version_assumption=version_assumption,
                manual_ref=(
                    "https://manual.gromacs.org/current/user-guide/mdp-options.html"
                ),
            )
        )
    return out


def _missing_coordinate_diagnostics(graph: ArtifactGraph) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in graph.by_role(ROLE_COORDINATE):
        if node.exists:
            continue
        # Only block when the coordinate is explicitly declared via the .mdp
        # structure option; a missing conventional sibling .gro is a soft note.
        declared = (node.detail or {}).get("declared_name")
        severity = "error" if declared else "warning"
        blocking = bool(declared)
        ref = node.referenced_from or (str(node.path), 1)
        out.append(
            _diag(
                code=CODE_MISSING_COORDINATE,
                severity=severity,
                message=(
                    f"coordinate artifact referenced from .mdp is missing: "
                    f"{node.path.name}"
                )
                if declared
                else (
                    f"no coordinate (.gro/.pdb) found in the case directory "
                    f"(expected near {node.path.name})"
                ),
                path=node.path,
                line=ref[1],
                category="cross-file reference",
                confidence=0.9 if declared else 0.7,
                blocking=blocking,
                source_provenance={
                    "role": ROLE_COORDINATE,
                    "referenced_from": {"path": ref[0], "line": ref[1]},
                    "declared_in": node.source,
                    "declared_name": declared,
                },
                fix_hints=[
                    f"Create {node.path.name} in the case directory",
                    "Or update the structure = reference in the .mdp",
                ],
                actions=[
                    {
                        "kind": "create_artifact",
                        "role": ROLE_COORDINATE,
                        "target": str(node.path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"missing_path": str(node.path), "declared_name": declared},
                artifact_roles=[ROLE_COORDINATE],
                domain_tags=["cross-file", "blocking" if blocking else "non-blocking"],
            )
        )
    return out


def _missing_index_diagnostics(graph: ArtifactGraph) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in graph.by_role(ROLE_INDEX):
        if node.exists:
            continue
        ref = node.referenced_from or (str(node.path), 1)
        out.append(
            _diag(
                code=CODE_MISSING_INDEX,
                severity="error",
                message=(
                    f"index artifact referenced from .mdp is missing: {node.path.name}"
                ),
                path=node.path,
                line=ref[1],
                category="cross-file reference",
                confidence=0.9,
                blocking=True,
                source_provenance={
                    "role": ROLE_INDEX,
                    "referenced_from": {"path": ref[0], "line": ref[1]},
                    "declared_in": node.source,
                },
                fix_hints=[
                    f"Create {node.path.name} in the case directory",
                    "Or remove the index = reference from the .mdp",
                ],
                actions=[
                    {
                        "kind": "create_artifact",
                        "role": ROLE_INDEX,
                        "target": str(node.path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"missing_path": str(node.path)},
                artifact_roles=[ROLE_INDEX],
                domain_tags=["cross-file", "blocking"],
            )
        )
    return out


def _unresolved_topology_include_diagnostics(
    graph: ArtifactGraph
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in graph.by_role(ROLE_TOPOLOGY):
        if not node.exists:
            continue
        _, _, local_includes = _parse_topology_molecules(node.path)
        for include_target, line_no in local_includes:
            resolved = (node.path.parent / include_target).resolve()
            if resolved.is_file():
                continue
            out.append(
                _diag(
                    code=CODE_UNRESOLVED_TOPOLOGY_INCLUDE,
                    severity="error",
                    message=(
                        "topology #include references a file that could not be "
                        f"resolved: '{include_target}'"
                    ),
                    path=node.path,
                    line=line_no,
                    category="cross-file reference",
                    confidence=0.9,
                    blocking=True,
                    source_provenance={
                        "role": ROLE_TOPOLOGY,
                        "include": include_target,
                        "referenced_from": {
                            "path": str(node.path),
                            "line": line_no,
                        },
                    },
                    fix_hints=[
                        f"Place '{include_target}' next to {node.path.name}",
                        f"Or correct the #include path in {node.path.name}",
                    ],
                    actions=[
                        {
                            "kind": "resolve_artifact",
                            "role": ROLE_TOPOLOGY,
                            "target": str(resolved),
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={"unresolved_path": str(resolved), "include": include_target},
                    artifact_roles=[ROLE_TOPOLOGY],
                    domain_tags=["cross-file", "blocking"],
                    manual_ref=(
                        "https://manual.gromacs.org/current/reference-manual/"
                        "topologies/file-format.html"
                    ),
                )
            )
    return out


def _molecule_declaration_mismatch_diagnostics(
    graph: ArtifactGraph
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in graph.by_role(ROLE_TOPOLOGY):
        if not node.exists:
            continue
        moleculetype_names, molecules_entries, _ = _parse_topology_molecules(node.path)
        molecules_names = {name for name, _ in molecules_entries}
        # Molecules referenced under [ molecules ] but never defined by any
        # [ moleculetype ] block: grompp cannot satisfy the declared count.
        for molecule_name, entry_line in molecules_entries:
            if molecule_name in moleculetype_names:
                continue
            out.append(
                _diag(
                    code=CODE_MOLECULE_DECLARATION_MISMATCH,
                    severity="error",
                    message=(
                        "[ molecules ] references molecule type "
                        f"'{molecule_name}' which is not defined by any "
                        "[ moleculetype ] block in this topology"
                    ),
                    path=node.path,
                    line=entry_line,
                    category="semantic consistency",
                    confidence=0.9,
                    blocking=True,
                    source_provenance={
                        "role": ROLE_TOPOLOGY,
                        "molecule": molecule_name,
                        "moleculetype_names": sorted(moleculetype_names),
                    },
                    fix_hints=[
                        f"Add a [ moleculetype ] block for '{molecule_name}'",
                        f"Or remove the [ molecules ] entry for '{molecule_name}'",
                    ],
                    actions=[
                        {
                            "kind": "review_section",
                            "section": "molecules",
                            "target": str(node.path),
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={
                        "molecule": molecule_name,
                        "defined_types": sorted(moleculetype_names),
                    },
                    artifact_roles=[ROLE_TOPOLOGY],
                    domain_tags=["semantic", "blocking"],
                    manual_ref=(
                        "https://manual.gromacs.org/current/reference-manual/"
                        "topologies/file-format.html"
                    ),
                )
            )
        # Molecules defined via [ moleculetype ] but never instantiated under
        # [ molecules ]: a likely incomplete system definition.
        defined_but_unused = moleculetype_names - molecules_names
        for molecule_name in sorted(defined_but_unused):
            out.append(
                _diag(
                    code=CODE_MOLECULE_DECLARATION_MISMATCH,
                    severity="warning",
                    message=(
                        f"molecule type '{molecule_name}' is defined in "
                        "[ moleculetype ] but never instantiated under [ molecules ]"
                    ),
                    path=node.path,
                    line=1,
                    category="semantic consistency",
                    confidence=0.75,
                    blocking=False,
                    source_provenance={
                        "role": ROLE_TOPOLOGY,
                        "molecule": molecule_name,
                        "molecules_names": sorted(molecules_names),
                    },
                    fix_hints=[
                        f"Add a [ molecules ] entry for '{molecule_name}'",
                        "Or remove the unused [ moleculetype ] block",
                    ],
                    actions=[
                        {
                            "kind": "review_section",
                            "section": "molecules",
                            "target": str(node.path),
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={
                        "molecule": molecule_name,
                        "instantiated": sorted(molecules_names),
                    },
                    artifact_roles=[ROLE_TOPOLOGY],
                    domain_tags=["semantic", "non-blocking"],
                )
            )
    return out


# --- version-aware-keywords ------------------------------------------------


def resolve_version_assumption(intent: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve the explicit runtime/version assumption for this preflight run.

    When the exact runtime/image version is unknown we record that fact
    explicitly rather than guessing, per the issue's version-assumptions
    acceptance criterion. The intent contract can override ``software_version``
    (e.g. ``gromacs >=2024``); otherwise we fall back to the schema version the
    builtin keyword set was authored against.
    """
    intent = intent or {}
    software_version = intent.get("software_version")
    runtime_image = intent.get("runtime_image")
    assumption: dict[str, Any] = {
        "software": "gromacs",
        "software_version": software_version or "unknown",
        "runtime_image": runtime_image or "unknown",
        "schema_source": intent.get("schema_source", "gromacs-lsp builtin mdp docs"),
        # The fallback is intentional and explicit so consumers never have to
        # guess whether ``unknown`` means "not checked" or "could not determine".
        "exact_runtime_known": bool(software_version or runtime_image),
    }
    if software_version or runtime_image:
        assumption["declared_by"] = "intent"
    else:
        assumption["declared_by"] = "fallback"
    return assumption


def _version_assumption_diagnostic(
    version_assumption: dict[str, Any], intent: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Emit an explicit information diagnostic when the runtime version is unknown.

    This makes the version assumption machine-readable in the diagnostic stream
    itself (not just metadata) so the parent probe can surface it without
    parsing the envelope top-level.
    """
    if version_assumption["exact_runtime_known"]:
        return []
    return [
        _diag(
            code=CODE_VERSION_ASSUMPTION,
            severity="information",
            message=(
                "Exact GROMACS runtime/image version is unknown; preflight "
                "validated against the builtin mdp keyword set"
            ),
            path=Path(version_assumption.get("schema_source", "gromacs-lsp builtin mdp docs")),
            line=1,
            category="preflight/runtime-risk",
            confidence=1.0,
            blocking=False,
            source_provenance={
                "role": ROLE_PRIMARY_INPUT,
                "reason": "software_version and runtime_image not declared in intent",
            },
            fix_hints=[
                "Declare software_version/runtime_image in the intent contract",
            ],
            actions=[],
            facts={
                "software_version": version_assumption["software_version"],
                "runtime_image": version_assumption["runtime_image"],
                "schema_source": version_assumption["schema_source"],
            },
            artifact_roles=[ROLE_PRIMARY_INPUT],
            domain_tags=["version-aware", "assumption"],
            version_assumption=version_assumption,
            intent=dict(intent) if intent else None,
        )
    ]


# --- fleet-regression-fixtures --------------------------------------------


def fleet_manifest(
    *,
    fixtures: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a machine-readable preflight manifest for the parent fleet.

    The parent ``bohrium_skills`` probe/report workflow consumes this to know
    which preflight codes exist, which capabilities are implemented, and which
    fixtures exercise them. Keeping it as data (not README prose) means the
    fleet regression evidence stays in sync with the implementation.
    """
    codes = {
        CODE_MISSING_PRIMARY_INPUT: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "no primary .mdp input found in the case directory",
        },
        CODE_UNREADABLE_INPUT: {
            "severity": "error",
            "category": "syntax",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "primary .mdp input could not be read as UTF-8 text",
        },
        CODE_EMPTY_MDP: {
            "severity": "error",
            "category": "semantic consistency",
            "blocking": True,
            "capability": "version-aware-keywords",
            "summary": "primary .mdp declares no key = value settings",
        },
        CODE_MISSING_REQUIRED_MDP_KEY: {
            "severity": "error",
            "category": "schema",
            "blocking": True,
            "capability": "version-aware-keywords",
            "summary": "required .mdp key (integrator/nsteps/dt) is missing",
        },
        CODE_UNRESOLVED_TOPOLOGY_INCLUDE: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "topology #include references a file that cannot be resolved",
        },
        CODE_MOLECULE_DECLARATION_MISMATCH: {
            "severity": "error",
            "category": "semantic consistency",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": (
                "[ molecules ] entry without a matching [ moleculetype ] block "
                "(or vice-versa)"
            ),
        },
        CODE_MISSING_COORDINATE: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "coordinate (.gro/.pdb) referenced from .mdp is missing",
        },
        CODE_MISSING_INDEX: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "index (.ndx) referenced from .mdp is missing",
        },
        CODE_VERSION_ASSUMPTION: {
            "severity": "information",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "exact runtime version unknown; fallback schema used",
        },
        CODE_UNKNOWN_MDP_PARAMETER: {
            "severity": "error",
            "category": "schema",
            "blocking": True,
            "capability": "version-aware-keywords",
            "summary": "unknown/typo'd .mdp parameter GROMACS would silently ignore",
        },
    }
    capabilities = {
        "version-aware-keywords": {
            "status": "available",
            "evidence_codes": [
                CODE_UNKNOWN_MDP_PARAMETER,
                CODE_MISSING_REQUIRED_MDP_KEY,
                CODE_EMPTY_MDP,
                CODE_VERSION_ASSUMPTION,
            ],
        },
        "cross-artifact-graph": {
            "status": "available",
            "roles": list(ALL_ROLES),
            "evidence_codes": [
                CODE_MISSING_PRIMARY_INPUT,
                CODE_UNREADABLE_INPUT,
                CODE_UNRESOLVED_TOPOLOGY_INCLUDE,
                CODE_MOLECULE_DECLARATION_MISMATCH,
                CODE_MISSING_COORDINATE,
                CODE_MISSING_INDEX,
            ],
        },
        "code-actions": {
            "status": "available",
            "blocking_gate": "gromacs-lsp-tool check --fail-on-blocking",
            "evidence_codes": list(codes.keys()),
        },
        "fleet-regression-fixtures": {
            "status": "available",
            "fixtures": list(fixtures) if fixtures else [],
        },
    }
    return {
        "software": "gromacs",
        "preflight_envelope": "DiagnosticEnvelope/v1",
        "artifact_roles": list(ALL_ROLES),
        "capabilities": capabilities,
        "codes": codes,
    }
