from __future__ import annotations

import re
from pathlib import Path

from .diagnostics import Diagnostic

SUPPORTED_SUFFIXES = {".mdp", ".top", ".itp", ".gro"}
KNOWN_MDP_KEYS = {
    "integrator",
    "nsteps",
    "dt",
    "nstxout",
    "nstvout",
    "nstenergy",
    "nstlog",
    "cutoff-scheme",
    "coulombtype",
    "rcoulomb",
    "rvdw",
    "constraints",
    "constraint-algorithm",
    "tcoupl",
    "pcoupl",
    "ref-t",
    "ref-p",
    "gen-vel",
    "pbc",
}
SECTION_RE = re.compile(r"^\s*\[\s*([^\]]+)\s*\]")


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
        return _analyze_mdp(path, content)
    if suffix in {".top", ".itp"}:
        return _analyze_topology(path, content)
    if suffix == ".gro":
        return _analyze_gro(path, content)
    return []


def _analyze_mdp(path: Path, content: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    params: dict[str, tuple[str, int]] = {}
    for line_no, raw in enumerate(content.splitlines(), start=1):
        line = raw.split(";", 1)[0].strip()
        if not line:
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
            sections.add(match.group(1).strip().lower())
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
