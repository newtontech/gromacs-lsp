"""OpenQC rule manifest for gromacs-lsp.

Loads ``rules/diagnostics.yaml`` once and exposes the rule surface to the
analyzer, the agent CLI (``gromacs-lsp-tool explain``), and OpenQC consumers.

The manifest is the single source of truth for stable ``rule_id`` values, their
planned severity, source classification, and manual references. Diagnostic
emitters reference these constants so the rule id never drifts from the
manifest.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml  # type: ignore[import-untyped]

# Stable rule identifiers exported by gromacs-lsp.
RULE_MDP_UNKNOWN_PARAMETER = "gromacs.mdp.unknown_parameter"
RULE_MDP_INVALID_VALUE = "gromacs.mdp.invalid_value"
RULE_TOPOLOGY_MISSING_INCLUDE = "gromacs.topology.missing_include"
RULE_TOPOLOGY_MOLECULE_COUNT_MISMATCH = "gromacs.topology.molecule_count_mismatch"
RULE_LOG_FATAL_ERROR = "gromacs.log.fatal_error"
RULE_LOG_LINCS_INSTABILITY = "gromacs.log.lincs_instability"
RULE_LOG_SETTLE_SHAKE_FAILURE = "gromacs.log.settle_shake_failure"
RULE_CUTOFF_PME_WARNING = "gromacs.cutoff.pme_warning"
RULE_LOG_MISSING_TOPOLOGY = "gromacs.log.missing_topology"
RULE_LOG_ATOM_COUNT_MISMATCH = "gromacs.log.atom_count_mismatch"
RULE_LOG_BOX_DIMENSION_ERROR = "gromacs.log.box_dimension_error"
RULE_LOG_CUDA_ERROR = "gromacs.log.cuda_error"
RULE_LOG_MEMORY_ERROR = "gromacs.log.memory_error"
RULE_LOG_IO_ERROR = "gromacs.log.io_error"

MANIFEST_RELPATH = Path("rules") / "diagnostics.yaml"


def _find_repo_root() -> Optional[Path]:
    """Walk up from this file to locate the rules manifest."""
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / MANIFEST_RELPATH).exists():
            return parent
    return None


@lru_cache(maxsize=1)
def _manifest() -> dict[str, Any]:
    """Load and cache the diagnostics manifest.

    Returns an empty rule set if the manifest is absent so that consumers
    degrade gracefully in stripped-down test environments.
    """
    root = _find_repo_root()
    if root is None:
        return {"rules": []}
    path = root / MANIFEST_RELPATH
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data.setdefault("rules", [])
    return data


def load_manifest() -> dict[str, Any]:
    """Public accessor for the cached diagnostics manifest."""
    return _manifest()


# Immutable set of rule_ids exported by this LSP, derived from the manifest.
RULES: frozenset[str] = frozenset(entry["rule_id"] for entry in _manifest()["rules"])


def rule_meta(rule_id: str) -> Optional[dict[str, Any]]:
    """Return the manifest entry for ``rule_id`` or ``None`` if unknown."""
    for entry in load_manifest()["rules"]:
        if entry.get("rule_id") == rule_id:
            return dict(entry)
    return None


def diagnostic_provenance(rule_id: str) -> Optional[dict[str, Any]]:
    """Build a ``source_provenance`` payload for ``rule_id`` from the manifest.

    Returns ``None`` when the rule is not in the manifest. The payload shape
    matches the official-spec entries OpenQC consumers expect so the
    DiagnosticEnvelope/v1 ``source_provenance`` field stays consistent across
    analyzer, log-parser, and preflight emitters.
    """
    meta = rule_meta(rule_id)
    if meta is None:
        return None
    file_type = meta.get("file_type")
    if file_type == "mdp":
        source_label = "GROMACS MDP options"
    elif file_type == "top":
        source_label = "GROMACS topology file format"
    elif file_type == "log":
        source_label = "GROMACS run-time errors"
    else:
        source_label = "GROMACS manual"
    return {
        "kind": "official_docs",
        "label": source_label,
        "url": meta.get("manual_ref") or "https://manual.gromacs.org/current/",
        "rule_id": rule_id,
        "file_type": file_type,
        "category": meta.get("category"),
    }
