from __future__ import annotations

import re
from pathlib import Path

from .diagnostics import Diagnostic
from .hover import _MDP_DOCS, get_valid_mdp_values
from .matmaster import MatMasterConfig, find_project_root, run_checks

SUPPORTED_SUFFIXES = {".mdp", ".top", ".itp", ".gro"}
KNOWN_MDP_KEYS = set(_MDP_DOCS.keys())
SECTION_RE = re.compile(r"^\s*\[\s*([^\]]+)\s*\]")

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
                    "warning",
                    f"unknown or currently unsupported MDP key: {key}",
                    str(path),
                    line_no,
                    suggested_fix={"kind": "check_mdp_keyword", "keyword": key},
                    confidence=0.55,
                )
            )
        else:
            # GMX004: value validation for known keys
            valid_vals = get_valid_mdp_values(lower)
            if valid_vals is not None:
                if value not in valid_vals:
                    diagnostics.append(
                        Diagnostic(
                            "GMX004",
                            "warning",
                            f"invalid value '{value}' for MDP key '{key}'",
                            str(path),
                            line_no,
                            suggested_fix={
                                "kind": "valid_values",
                                "keyword": key,
                                "valid": sorted(valid_vals),
                            },
                            confidence=0.7,
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
                                "warning",
                                f"nsteps should be non-negative, got {value}",
                                str(path),
                                line_no,
                                confidence=0.8,
                            )
                        )
                except ValueError:
                    diagnostics.append(
                        Diagnostic(
                            "GMX004",
                            "warning",
                            f"nsteps should be an integer, got '{value}'",
                            str(path),
                            line_no,
                            confidence=0.8,
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
    for line_no, raw in enumerate(content.splitlines(), start=1):
        match = SECTION_RE.match(raw)
        if match:
            section = match.group(1).strip().lower()
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
