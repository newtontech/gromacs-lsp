"""MatMaster-domain execution rules for GROMACS input files.

These are newtontech-specific checks that complement the upstream
MDParser diagnostics.  They are enabled by placing a
``.gromacs-lsp/matmaster.json`` file at the project root.

Diagnostic codes
----------------

| Code   | Severity | Description                                      |
|--------|----------|--------------------------------------------------|
| GMX800 | error    | ``integrator`` must appear before ``nsteps``/``dt`` in MDP files |
| GMX801 | warning  | ``nsteps`` should be > 0 for dynamic integrators |
| GMX802 | warning  | ``#include`` path with ``..`` escapes project root |
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .diagnostics import Diagnostic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class MatMasterConfig:
    """MatMaster configuration loaded from ``.gromacs-lsp/matmaster.json``."""

    def __init__(self, enabled: bool = True, **kwargs: bool) -> None:
        self.enabled = enabled
        self.check_integrator_order: bool = kwargs.get("check_integrator_order", True)
        self.require_positive_nsteps: bool = kwargs.get("require_positive_nsteps", True)
        self.forbid_parent_paths: bool = kwargs.get("forbid_parent_paths", True)

    @classmethod
    def load(cls, project_root: Path) -> MatMasterConfig | None:
        """Load config from ``project_root/.gromacs-lsp/matmaster.json``.

        Returns ``None`` if the file does not exist, cannot be parsed, or
        has ``enabled: false``.
        """
        config_path = project_root / ".gromacs-lsp" / "matmaster.json"
        if not config_path.is_file():
            return None
        try:
            raw: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        enabled = raw.get("enabled", True)
        if not enabled:
            return None
        return cls(
            enabled=True,
            check_integrator_order=raw.get("check_integrator_order", True),
            require_positive_nsteps=raw.get("require_positive_nsteps", True),
            forbid_parent_paths=raw.get("forbid_parent_paths", True),
        )


# ---------------------------------------------------------------------------
# Project root discovery
# ---------------------------------------------------------------------------


def find_project_root(path: Path) -> Path | None:
    """Walk up from *path* looking for a ``.gromacs-lsp`` directory.

    Returns the first ancestor (or *path* itself) that contains such a
    directory, or ``None``.
    """
    path = path.resolve()
    for ancestor in [path, *path.parents]:
        if (ancestor / ".gromacs-lsp").is_dir():
            return ancestor
    return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

_INCLUDE_PARENT_RE = re.compile(r'#include\s+["<](\\.|[^"<>])*\.\.(\\.|[^"<>])*[">]')
_DYNAMIC_INTEGRATORS = {"md", "md-vv", "bd", "sd"}

# Known MDP keys that are integrator-dependent
_INTEGRATOR_DEPENDENT_KEYS = {"nsteps", "dt", "nstcomm", "nstxout", "nstvout"}

# Lines matching key = value
_MDP_LINE_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+?)\s*$", re.IGNORECASE)


def check_source(
    source: str, path: Path, config: MatMasterConfig, project_root: Path | None = None
) -> list[Diagnostic]:
    """Run all enabled MatMaster checks against a GROMACS file.

    Args:
        source:  Full text of the file.
        path:    ``Path`` to the file (for error location).
        config:  Loaded ``MatMasterConfig``.
        project_root:  Project root for parent-path checks.

    Returns:
        List of ``Diagnostic`` objects.
    """
    diagnostics: list[Diagnostic] = []

    suffix = path.suffix.lower()
    if suffix != ".mdp" and suffix not in (".top", ".itp"):
        return diagnostics  # GRO / other files – no MatMaster checks yet

    lines = source.splitlines()

    if config.check_integrator_order and suffix == ".mdp":
        diagnostics.extend(_check_integrator_order(lines, path))

    if config.require_positive_nsteps and suffix == ".mdp":
        diagnostics.extend(_check_nsteps_positive(lines, path))

    if config.forbid_parent_paths and project_root is not None:
        diagnostics.extend(_check_include_parent_path(lines, path, project_root))

    return diagnostics


def _check_integrator_order(lines: list[str], path: Path) -> list[Diagnostic]:
    """GMX800: ``integrator`` must appear before ``nsteps``/``dt``.

    This catches the common error of setting simulation parameters before
    choosing the integrator.
    """
    diagnostics: list[Diagnostic] = []
    integrator_line: int | None = None

    for line_no, raw in enumerate(lines, start=1):
        m = _MDP_LINE_RE.match(raw)
        if not m:
            continue
        key = m.group(1).lower()
        if key == "integrator":
            integrator_line = line_no
        elif key in _INTEGRATOR_DEPENDENT_KEYS and integrator_line is None:
            diagnostics.append(
                Diagnostic(
                    code="GMX800",
                    severity="error",
                    message=(
                        f"'{key}' used before integrator is set; "
                        "specify 'integrator' first"
                    ),
                    file=str(path),
                    line=line_no,
                    column=m.start(1) + 1,
                    evidence=[raw.strip()],
                    suggested_fix={
                        "kind": "reorder_keys",
                        "key": key,
                        "move_after": "integrator",
                    },
                    confidence=0.85,
                )
            )

    return diagnostics


def _check_nsteps_positive(lines: list[str], path: Path) -> list[Diagnostic]:
    """GMX801: ``nsteps`` should be > 0 for dynamic integrators."""
    diagnostics: list[Diagnostic] = []
    integrator: str | None = None
    nsteps: tuple[int | None, int] | None = None  # (value, line_no)

    for line_no, raw in enumerate(lines, start=1):
        m = _MDP_LINE_RE.match(raw)
        if not m:
            continue
        key = m.group(1).lower()
        value = m.group(2)
        if key == "integrator":
            integrator = value.strip().lower()
        elif key == "nsteps":
            try:
                nsteps_val = int(value.strip())
                nsteps = (nsteps_val, line_no)
            except ValueError:
                pass

    if integrator and nsteps:
        val, line_no = nsteps
        # Dynamic integrators should have nsteps > 0
        if integrator in _DYNAMIC_INTEGRATORS and val is not None and val <= 0:
            diagnostics.append(
                Diagnostic(
                    code="GMX801",
                    severity="warning",
                    message=(
                        f"nsteps should be > 0 for integrator '{integrator}', "
                        f"got {val}"
                    ),
                    file=str(path),
                    line=line_no,
                    confidence=0.85,
                )
            )

    return diagnostics


def _check_include_parent_path(
    lines: list[str], path: Path, project_root: Path
) -> list[Diagnostic]:
    """GMX802: ``#include`` paths that escape the project root."""
    diagnostics: list[Diagnostic] = []
    file_dir = path.resolve().parent

    for line_no, raw in enumerate(lines, start=1):
        # Find #include directives
        stripped = raw.split(";", 1)[0].strip()
        if not stripped.startswith("#include"):
            continue

        # Extract the path inside quotes or brackets
        m = re.search(r'#include\s+["<]([^">]+)[">]', stripped)
        if not m:
            continue

        include_target = m.group(1)
        # Check for '..' components
        if ".." in include_target:
            # Resolve the path to see if it escapes the project root
            resolved = (file_dir / include_target).resolve()
            try:
                resolved.relative_to(project_root.resolve())
            except ValueError:
                # Escaped!
                diagnostics.append(
                    Diagnostic(
                        code="GMX802",
                        severity="warning",
                        message=(
                            f"include path '{include_target}' " f"escapes project root"
                        ),
                        file=str(path),
                        line=line_no,
                        evidence=[raw.strip()],
                        suggested_fix={
                            "kind": "check_include_path",
                            "path": include_target,
                            "resolved_to": str(resolved),
                        },
                        confidence=0.8,
                    )
                )

    return diagnostics


# ---------------------------------------------------------------------------
# Wrapper used by analyzer / CLI
# ---------------------------------------------------------------------------


def run_checks(path: Path, config: MatMasterConfig) -> list[Diagnostic]:
    """Load a file and run all MatMaster checks against it.

    This is the main entry point used by ``analyze_file`` and the CLI.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    project_root = find_project_root(path)
    return check_source(source, path, config, project_root=project_root)
