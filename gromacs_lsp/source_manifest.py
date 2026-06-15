"""Source manifest: agent-facing JSON contract for gromacs-lsp exports.

The OpenQC ``agent-json`` capability contract
(``newtontech/gromacs-lsp#12``) requires a single, deterministic, source
manifest that OpenQC consumers can read to discover:

* the LSP identity and editor launch contract (``lsp-capabilities.json``),
* the diagnostic rule surface (``rules/diagnostics.yaml``),
* the generated LSP feature coverage (``gromacs_lsp.generated_features``),
* the source provenance classification (official/upstream/community).

This module is the only place that aggregates those four sources into a single
JSON document. Each piece is loaded lazily from its existing source so the
manifest cannot drift from the in-repo data.

See also: wiki/synthesis/openqc-agent-context.md
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .rules import load_manifest

MANIFEST_SCHEMA = "OpenQCSourceManifest"
MANIFEST_VERSION = 1
_CAPABILITIES_RELPATH = Path("lsp-capabilities.json")


def _find_repo_root() -> Path | None:
    """Walk up from this file to locate the repo root (rules/ lives there)."""
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "rules" / "diagnostics.yaml").exists():
            return parent
    return None


@lru_cache(maxsize=1)
def _capabilities() -> dict[str, Any]:
    """Load and cache ``lsp-capabilities.json``.

    The shipped file is the canonical source of truth, but the source manifest
    must reflect the operations the agent CLI actually answers to. We augment
    the operations list and capabilities list with the source-manifest,
    features, and code-actions operations added in #12/#13/#23 so OpenQC
    consumers that read the source manifest first still discover them.
    """
    root = _find_repo_root()
    if root is None or not (root / _CAPABILITIES_RELPATH).exists():
        return {}
    try:
        data = json.loads((root / _CAPABILITIES_RELPATH).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    agent_cli = dict(data.get("agentCli") or {})
    operations = list(agent_cli.get("operations") or [])
    for op in ("source-manifest", "features", "code-actions"):
        if op not in operations:
            operations.append(op)
    agent_cli["operations"] = operations
    data["agentCli"] = agent_cli
    caps = list(data.get("capabilities") or [])
    for cap in ("code-actions", "generated-features", "source-manifest"):
        if cap not in caps:
            caps.append(cap)
    data["capabilities"] = caps
    return data


def _rule_surface() -> dict[str, Any]:
    """Summarize the diagnostic rule manifest for the source manifest.

    The full per-rule metadata already lives in ``rules/diagnostics.yaml`` and
    is exported verbatim by ``gromacs-lsp-tool rules``; the source manifest
    carries only the summary fields an OpenQC consumer needs to discover the
    surface without re-parsing every rule body.
    """
    manifest = load_manifest()
    rules = manifest.get("rules", [])
    by_file_type: dict[str, list[str]] = {}
    for entry in rules:
        file_type = entry.get("file_type") or "unknown"
        by_file_type.setdefault(file_type, []).append(entry.get("rule_id", ""))
    return {
        "rule_count": len(rules),
        "rule_ids": sorted(entry.get("rule_id", "") for entry in rules),
        "by_file_type": {
            file_type: sorted(values) for file_type, values in by_file_type.items()
        },
        "manifest_schema": manifest.get("schema"),
        "manifest_version": manifest.get("version"),
    }


def _generated_features() -> dict[str, Any]:
    """Pull the generated LSP feature coverage from ``generated_features``.

    Imported lazily so source_manifest can be imported in stripped-down
    environments where generated_features has additional (optional)
    dependencies.
    """
    try:
        from .generated_features import generated_features_manifest

        return generated_features_manifest()
    except Exception:
        return {}


def source_manifest() -> dict[str, Any]:
    """Build the canonical source manifest for gromacs-lsp.

    The returned document is the single JSON an OpenQC consumer reads to
    discover what gromacs-lsp exports. Each section is sourced from its
    existing in-repo artifact so this module is a pure aggregator.
    """
    capabilities = _capabilities()
    rules = _rule_surface()
    features = _generated_features()
    payload: dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "schema_version": MANIFEST_VERSION,
        "id": capabilities.get("id", "gromacs-lsp"),
        "software": capabilities.get("software", "gromacs"),
        "displayName": capabilities.get("displayName", "GROMACS"),
        "languageId": capabilities.get("languageId", "gromacs"),
        "executable": capabilities.get("executable", "gromacs-lsp"),
        "defaultBranch": capabilities.get("defaultBranch", "main"),
        "maturity": capabilities.get("maturity", "stable"),
        "filePatterns": list(capabilities.get("filePatterns", [])),
        "capabilities": list(capabilities.get("capabilities", [])),
        "agentCli": capabilities.get("agentCli", {}),
        "blockingPolicy": capabilities.get(
            "blockingPolicy",
            {
                "mode": "blocking",
                "description": "Error diagnostics block run-gate until resolved.",
            },
        ),
        "diagnosticSchema": capabilities.get(
            "diagnosticSchema", "diagnostics/diagnostic-engine-v1.schema.json"
        ),
        "rules": rules,
        "generated_features": features,
        "sourceProvenance": list(capabilities.get("sourceProvenance", [])),
        "fixturePaths": capabilities.get("fixturePaths", {}),
        "openqc": capabilities.get(
            "openqc",
            {
                "registryId": "gromacs-lsp",
                "repoName": "gromacs-lsp",
                "contextContract": "DSLAuthoringContext",
                "diagnosticEnvelope": "DiagnosticEnvelope/v1",
            },
        ),
    }
    return payload
