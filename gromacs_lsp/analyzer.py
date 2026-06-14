from __future__ import annotations

import re
from pathlib import Path

from .diagnostics import Diagnostic
from .hover import _MDP_DOCS, get_valid_mdp_values
from .matmaster import MatMasterConfig, find_project_root, run_checks
from .rules import (
    RULE_MDP_INVALID_VALUE,
    RULE_MDP_UNKNOWN_PARAMETER,
    RULE_TOPOLOGY_MISSING_INCLUDE,
    RULE_TOPOLOGY_MOLECULE_COUNT_MISMATCH,
    rule_meta,
)

SUPPORTED_SUFFIXES = {".mdp", ".top", ".itp", ".gro"}
KNOWN_MDP_KEYS = set(_MDP_DOCS.keys())
SECTION_RE = re.compile(r"^\s*\[\s*([^\]]+)\s*\]")

# Manifest metadata for the unknown-MDP-parameter rule (severity / source /
# manual reference come from rules/diagnostics.yaml so they never drift).
_MDP_UNKNOWN_PARAMETER_META = rule_meta(RULE_MDP_UNKNOWN_PARAMETER) or {}
_MDP_UNKNOWN_PARAMETER_MANUAL = _MDP_UNKNOWN_PARAMETER_META.get(
    "manual_ref",
    "https://manual.gromacs.org/current/user-guide/mdp-options.html",
)
_MDP_UNKNOWN_PARAMETER_CONFIDENCE = float(
    _MDP_UNKNOWN_PARAMETER_META.get("confidence", 0.9)
)

# Manifest metadata for the invalid-MDP-value rule (severity / source /
# manual reference come from rules/diagnostics.yaml so they never drift).
_MDP_INVALID_VALUE_META = rule_meta(RULE_MDP_INVALID_VALUE) or {}
_MDP_INVALID_VALUE_MANUAL = _MDP_INVALID_VALUE_META.get(
    "manual_ref",
    "https://manual.gromacs.org/current/user-guide/mdp-options.html",
)
_MDP_INVALID_VALUE_CONFIDENCE = float(_MDP_INVALID_VALUE_META.get("confidence", 0.9))

# Manifest metadata for the missing-topology-include rule (severity / source /
# manual reference come from rules/diagnostics.yaml so they never drift).
_TOPOLOGY_MISSING_INCLUDE_META = rule_meta(RULE_TOPOLOGY_MISSING_INCLUDE) or {}
_TOPOLOGY_MISSING_INCLUDE_MANUAL = _TOPOLOGY_MISSING_INCLUDE_META.get(
    "manual_ref",
    "https://manual.gromacs.org/current/reference-manual/topologies/file-format.html",
)
_TOPOLOGY_MISSING_INCLUDE_CONFIDENCE = float(
    _TOPOLOGY_MISSING_INCLUDE_META.get("confidence", 0.9)
)

# Manifest metadata for the molecule-count-mismatch rule (severity / source /
# manual reference come from rules/diagnostics.yaml so they never drift).
_TOPOLOGY_MOLECULE_COUNT_MISMATCH_META = rule_meta(
    RULE_TOPOLOGY_MOLECULE_COUNT_MISMATCH
) or {}
_TOPOLOGY_MOLECULE_COUNT_MISMATCH_MANUAL = (
    _TOPOLOGY_MOLECULE_COUNT_MISMATCH_META.get(
        "manual_ref",
        "https://manual.gromacs.org/current/reference-manual/topologies/file-format.html",
    )
)
_TOPOLOGY_MOLECULE_COUNT_MISMATCH_CONFIDENCE = float(
    _TOPOLOGY_MOLECULE_COUNT_MISMATCH_META.get("confidence", 0.9)
)

# Pattern for a GROMACS topology `#include` directive. Captures the quoted or
# bracketed file path, e.g. `#include "foo.itp"` or `#include <bar.itp>`.
_INCLUDE_RE = re.compile(r'^\s*#include\s+[<"]([^>"]+)[>"]\s*$')
# Shared force-field includes (e.g. `amber99sb-ildn.ff/forcefield.itp`) are
# resolved by grompp against the GROMACS shared data directory, which the LSP
# editor cannot see. Only flag includes that look like local files.
_FORCEFIELD_INCLUDE_MARKER = ".ff/"

# A GROMACS topology data record: whitespace-separated fields. Used to read
# the molecule name from `[ moleculetype ]` and `[ molecules ]` bodies, e.g.
# `SOL     3` -> first token is the molecule name.
_TOPOLOGY_RECORD_RE = re.compile(r"^(\S+)\s+\S+")

# Known topology section names (from _gmx_nodes)
KNOWN_TOPOLOGY_SECTIONS = {
    "defaults",
    "atomtypes",
    "bondtypes",
    "angletypes",
    "dihedraltypes",
    "constrainttypes",
    "pairtypes",
    "nonbond_params",
    "moleculetype",
    "atoms",
    "bonds",
    "pairs",
    "pairs_nb",
    "angles",
    "dihedrals",
    "exclusions",
    "constraints",
    "settles",
    "virtual_sites2",
    "virtual_sites3",
    "virtual_sites4",
    "virtual_sitesn",
    "position_restraints",
    "distance_restraints",
    "dihedral_restraints",
    "orientation_restraints",
    "angle_restraints",
    "angle_restraints_z",
    "system",
    "molecules",
    "implicit_genborn_params",
    "cmap",
    "frozen",
}


def analyze_path(path: Path) -> list[Diagnostic]:
    path = path.resolve()
    files = (
        [path]
        if path.is_file()
        else sorted(
            p for p in path.rglob("*") if p.suffix.lower() in SUPPORTED_SUFFIXES
        )
    )
    diagnostics: list[Diagnostic] = []
    if not files:
        return [
            Diagnostic(
                "GMX201", "error", "no supported GROMACS files found", str(path), 1
            )
        ]
    for file_path in files:
        diagnostics.extend(analyze_file(file_path))
    return sorted(diagnostics, key=lambda item: (item.file, item.line, item.code))


def analyze_file(path: Path) -> list[Diagnostic]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [
            Diagnostic("GMX202", "error", "file is not valid UTF-8 text", str(path), 1)
        ]
    suffix = path.suffix.lower()
    if suffix == ".mdp":
        diagnostics = _analyze_mdp(path, content)
    elif suffix in {".top", ".itp"}:
        diagnostics = _analyze_topology(path, content)
    elif suffix == ".gro":
        diagnostics = _analyze_gro(path, content)
    else:
        diagnostics = []

    project_root = find_project_root(path)
    if project_root is not None:
        config = MatMasterConfig.load(project_root)
        if config is not None:
            diagnostics.extend(run_checks(path, config))

    return diagnostics


def _analyze_mdp(path: Path, content: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    params: dict[str, tuple[str, int]] = {}
    for line_no, raw in enumerate(content.splitlines(), start=1):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        # Skip preprocessor directives (#include, #ifdef, etc.)
        if line.startswith("#"):
            continue
        if "=" not in line:
            diagnostics.append(
                Diagnostic(
                    "GMX001",
                    "warning",
                    "MDP setting should use key = value",
                    str(path),
                    line_no,
                    confidence=0.65,
                )
            )
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        lower = key.lower()
        # GMX003: duplicate key
        if lower in params:
            diagnostics.append(
                Diagnostic(
                    "GMX003",
                    "warning",
                    f"duplicate MDP key: {key} (first set on line {params[lower][1]})",
                    str(path),
                    line_no,
                    confidence=0.75,
                )
            )
        params[lower] = (value, line_no)
        if lower not in KNOWN_MDP_KEYS:
            diagnostics.append(
                Diagnostic(
                    "GMX002",
                    "error",
                    f"unknown or currently unsupported MDP key: {key}",
                    str(path),
                    line_no,
                    suggested_fix={"kind": "check_mdp_keyword", "keyword": key},
                    confidence=_MDP_UNKNOWN_PARAMETER_CONFIDENCE,
                    rule_id=RULE_MDP_UNKNOWN_PARAMETER,
                    manual_ref=_MDP_UNKNOWN_PARAMETER_MANUAL,
                )
            )
        else:
            # GMX004: value validation for known keys (gromacs.mdp.invalid_value)
            valid_vals = get_valid_mdp_values(lower)
            if valid_vals is not None:
                if value not in valid_vals:
                    diagnostics.append(
                        Diagnostic(
                            "GMX004",
                            "error",
                            f"invalid value '{value}' for MDP key '{key}'",
                            str(path),
                            line_no,
                            suggested_fix={
                                "kind": "valid_values",
                                "keyword": key,
                                "valid": sorted(valid_vals),
                            },
                            confidence=_MDP_INVALID_VALUE_CONFIDENCE,
                            rule_id=RULE_MDP_INVALID_VALUE,
                            manual_ref=_MDP_INVALID_VALUE_MANUAL,
                        )
                    )
            # Validate nsteps is a non-negative integer
            if lower == "nsteps":
                try:
                    nsteps_val = int(value)
                    if nsteps_val < 0:
                        diagnostics.append(
                            Diagnostic(
                                "GMX004",
                                "error",
                                f"nsteps should be non-negative, got {value}",
                                str(path),
                                line_no,
                                confidence=_MDP_INVALID_VALUE_CONFIDENCE,
                                rule_id=RULE_MDP_INVALID_VALUE,
                                manual_ref=_MDP_INVALID_VALUE_MANUAL,
                            )
                        )
                except ValueError:
                    diagnostics.append(
                        Diagnostic(
                            "GMX004",
                            "error",
                            f"nsteps should be an integer, got '{value}'",
                            str(path),
                            line_no,
                            confidence=_MDP_INVALID_VALUE_CONFIDENCE,
                            rule_id=RULE_MDP_INVALID_VALUE,
                            manual_ref=_MDP_INVALID_VALUE_MANUAL,
                        )
                    )
    for required in ("integrator", "nsteps", "dt"):
        if required not in params:
            diagnostics.append(
                Diagnostic(
                    "GMX101",
                    "warning",
                    f"required MDP key '{required}' was not found",
                    str(path),
                    1,
                    confidence=0.75,
                )
            )
    return diagnostics


def _analyze_topology(path: Path, content: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    sections: set[str] = set()
    # Active section header (lower-cased) so body lines can be parsed in
    # context. Reset to None outside any known section.
    current_section: str | None = None
    # Molecule types defined via [ moleculetype ] blocks in this topology. The
    # [ molecules ] section must reference only names in this set, otherwise
    # grompp cannot satisfy the declared molecule count.
    moleculetype_names: set[str] = set()
    # Pending [ molecules ] entries collected as (name, line_no) so they can be
    # validated against the full moleculetype set once the file is fully read.
    molecules_entries: list[tuple[str, int]] = []
    for line_no, raw in enumerate(content.splitlines(), start=1):
        match = SECTION_RE.match(raw)
        if match:
            section = match.group(1).strip().lower()
            current_section = section
            sections.add(section)
            if section not in KNOWN_TOPOLOGY_SECTIONS:
                diagnostics.append(
                    Diagnostic(
                        "GMX021",
                        "warning",
                        f"unknown or currently unsupported topology section [{section}]",
                        str(path),
                        line_no,
                        suggested_fix={
                            "kind": "check_topology_section",
                            "section": section,
                        },
                        confidence=0.6,
                    )
                )
            continue
        stripped = raw.split(";", 1)[0].strip()
        # Capture the molecule name from [ moleculetype ] and [ molecules ]
        # body records so the [ molecules ] entries can be validated against
        # the set of defined molecule types once the file is fully read.
        if current_section in {"moleculetype", "molecules"}:
            record_match = _TOPOLOGY_RECORD_RE.match(stripped)
            if record_match:
                record_name = record_match.group(1)
                if current_section == "moleculetype":
                    moleculetype_names.add(record_name)
                else:
                    molecules_entries.append((record_name, line_no))
        if (
            stripped.startswith("#include")
            and '"' not in stripped
            and "<" not in stripped
        ):
            diagnostics.append(
                Diagnostic(
                    "GMX020",
                    "warning",
                    "#include should quote or bracket the included topology path",
                    str(path),
                    line_no,
                    confidence=0.7,
                )
            )
            continue
        # GMX023: a quoted/bracketed #include that does not resolve to a local
        # file next to this topology. Shared force-field includes (e.g.
        # `amber99sb-ildn.ff/forcefield.itp`) are resolved by grompp against the
        # GROMACS shared data directory, which the LSP editor cannot see, so
        # those are intentionally left to the runtime rather than flagged here.
        include_match = _INCLUDE_RE.match(stripped)
        if include_match:
            include_target = include_match.group(1).strip()
            if _FORCEFIELD_INCLUDE_MARKER in include_target:
                continue
            resolved = (path.parent / include_target).resolve()
            if not resolved.is_file():
                diagnostics.append(
                    Diagnostic(
                        "GMX023",
                        "error",
                        (
                            "topology #include references a file that could not "
                            f"be resolved: '{include_target}'"
                        ),
                        str(path),
                        line_no,
                        suggested_fix={
                            "kind": "check_include_path",
                            "include": include_target,
                        },
                        confidence=_TOPOLOGY_MISSING_INCLUDE_CONFIDENCE,
                        rule_id=RULE_TOPOLOGY_MISSING_INCLUDE,
                        manual_ref=_TOPOLOGY_MISSING_INCLUDE_MANUAL,
                    )
                )
    # GMX024: a [ molecules ] entry whose molecule type is not defined by any
    # [ moleculetype ] block in this topology. grompp cross-references the
    # molecule names under [ molecules ] against the defined molecule types and
    # aborts when a referenced type has no definition, so the declared molecule
    # count cannot be satisfied.
    for molecule_name, entry_line in molecules_entries:
        if molecule_name in moleculetype_names:
            continue
        diagnostics.append(
            Diagnostic(
                "GMX024",
                "error",
                (
                    "[ molecules ] references molecule type "
                    f"'{molecule_name}' which is not defined by any "
                    "[ moleculetype ] block in this topology"
                ),
                str(path),
                entry_line,
                suggested_fix={
                    "kind": "check_molecule_type",
                    "molecule": molecule_name,
                },
                confidence=_TOPOLOGY_MOLECULE_COUNT_MISMATCH_CONFIDENCE,
                rule_id=RULE_TOPOLOGY_MOLECULE_COUNT_MISMATCH,
                manual_ref=_TOPOLOGY_MOLECULE_COUNT_MISMATCH_MANUAL,
            )
        )
    for required in ("moleculetype", "atoms"):
        if required not in sections:
            diagnostics.append(
                Diagnostic(
                    "GMX110",
                    "warning",
                    f"topology section [{required}] was not found",
                    str(path),
                    1,
                    confidence=0.7,
                )
            )
    return diagnostics


def _analyze_gro(path: Path, content: str) -> list[Diagnostic]:
    lines = content.splitlines()
    if len(lines) < 3:
        return [Diagnostic("GMX030", "error", "GRO file is too short", str(path), 1)]
    try:
        atom_count = int(lines[1].strip())
    except ValueError:
        return [
            Diagnostic(
                "GMX031", "error", "GRO atom-count line is not an integer", str(path), 2
            )
        ]
    actual = max(0, len(lines) - 3)
    if atom_count != actual:
        return [
            Diagnostic(
                "GMX032",
                "error",
                f"GRO atom count is {atom_count}, but {actual} atom lines were found",
                str(path),
                2,
            )
        ]
    return []


def format_text(content: str) -> str:
    lines: list[str] = []
    for raw in content.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith((";", "#")) or "=" not in stripped:
            lines.append(raw.rstrip())
            continue
        key, value = stripped.split("=", 1)
        lines.append(f"{key.strip():<26} = {value.strip()}")
    return "\n".join(lines).rstrip() + "\n"
