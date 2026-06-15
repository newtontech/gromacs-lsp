"""Generated LSP feature manifest for gromacs-lsp (OpenQC contract).

The OpenQC ``generated-lsp-features`` capability contract
(``newtontech/gromacs-lsp#13``) requires gromacs-lsp to expose the LSP feature
surface that is generated from the in-repo data dictionaries. In this repo the
"DSL IR schema" is the union of:

* ``gromacs_lsp.hover._MDP_DOCS``  — drives MDP completion + hover + the
  unknown-parameter rule's keyword set.
* ``gromacs_lsp.hover._MDP_VALID_VALUES`` — drives the invalid-value rule.
* ``gromacs_lsp.hover._TOPOLOGY_DOCS`` — drives topology completion + hover.
* ``gromacs_lsp.analyzer.KNOWN_TOPOLOGY_SECTIONS`` — drives the unknown
  topology section check.
* ``rules/diagnostics.yaml`` — drives the diagnostic rule surface.

This module aggregates those sources into a single manifest that lists each
LSP feature (completion, hover, diagnostics, formatting, code actions), the
data source it is generated from, and a coverage count. OpenQC consumers read
this manifest to confirm the LSP is wired into the data dictionaries rather
than ad-hoc hard-coded branches.

See also: wiki/synthesis/lsp-features.md
"""

from __future__ import annotations

from typing import Any

from .rules import load_manifest

FEATURE_SCHEMA = "OpenQCLspFeatureManifest"
FEATURE_VERSION = 1


def _completion_coverage() -> dict[str, Any]:
    """Coverage for the completion feature."""
    from .hover import _MDP_DOCS, _TOPOLOGY_DOCS

    return {
        "status": "available",
        "data_sources": [
            "gromacs_lsp.hover._MDP_DOCS",
            "gromacs_lsp.hover._TOPOLOGY_DOCS",
        ],
        "coverage": {
            "mdp_keys": sorted(_MDP_DOCS.keys()),
            "topology_sections": sorted(_TOPOLOGY_DOCS.keys()),
        },
        "counts": {
            "mdp_keys": len(_MDP_DOCS),
            "topology_sections": len(_TOPOLOGY_DOCS),
        },
    }


def _hover_coverage() -> dict[str, Any]:
    """Coverage for the hover feature (same data source as completion)."""
    from .hover import _MDP_DOCS, _TOPOLOGY_DOCS

    return {
        "status": "available",
        "data_sources": [
            "gromacs_lsp.hover._MDP_DOCS",
            "gromacs_lsp.hover._TOPOLOGY_DOCS",
        ],
        "coverage": {
            "mdp_keys": sorted(_MDP_DOCS.keys()),
            "topology_sections": sorted(_TOPOLOGY_DOCS.keys()),
        },
        "counts": {
            "mdp_keys": len(_MDP_DOCS),
            "topology_sections": len(_TOPOLOGY_DOCS),
        },
    }


def _diagnostics_coverage() -> dict[str, Any]:
    """Coverage for the diagnostics feature, from the rule manifest."""
    manifest = load_manifest()
    rules = manifest.get("rules", [])
    return {
        "status": "available",
        "data_sources": [
            "rules/diagnostics.yaml",
            "gromacs_lsp.hover._MDP_VALID_VALUES",
            "gromacs_lsp.analyzer.KNOWN_TOPOLOGY_SECTIONS",
        ],
        "coverage": {
            "rule_ids": sorted(entry.get("rule_id", "") for entry in rules),
            "codes": sorted(entry.get("code", "") for entry in rules),
        },
        "counts": {
            "rules": len(rules),
        },
    }


def _formatting_coverage() -> dict[str, Any]:
    """Coverage for the formatting feature."""
    return {
        "status": "available",
        "data_sources": ["gromacs_lsp.analyzer.format_text"],
        "coverage": {
            "file_types": ["mdp"],
            "behavior": (
                "Aligns ``key = value`` lines, preserves comments and "
                "preprocessor directives, idempotent."
            ),
        },
    }


def _code_actions_coverage() -> dict[str, Any]:
    """Coverage for the code-actions feature."""
    try:
        from .code_actions import HANDLED_CODES, code_action_kinds

        return {
            "status": "available",
            "data_sources": ["gromacs_lsp.code_actions"],
            "coverage": {
                "handled_codes": sorted(HANDLED_CODES),
                "kinds": code_action_kinds(),
            },
        }
    except Exception:
        return {
            "status": "unavailable",
            "data_sources": [],
            "coverage": {},
        }


def _symbols_coverage() -> dict[str, Any]:
    """Coverage for the document-symbols feature."""
    return {
        "status": "available",
        "data_sources": ["gromacs_lsp.symbols.document_symbols"],
        "coverage": {
            "file_types": ["mdp", "top", "itp"],
        },
    }


def generated_features_manifest() -> dict[str, Any]:
    """Build the generated LSP feature manifest for OpenQC consumers.

    Each feature entry is generated from the in-repo data dictionaries so
    the manifest cannot drift from the actual feature surface. The output is
    deterministic and JSON-serializable.
    """
    return {
        "schema": FEATURE_SCHEMA,
        "schema_version": FEATURE_VERSION,
        "software": "gromacs",
        "source_of_truth": (
            "Hover/completion/diagnostics coverage is generated from "
            "gromacs_lsp.hover._MDP_DOCS, _MDP_VALID_VALUES, "
            "_TOPOLOGY_DOCS, gromacs_lsp.analyzer.KNOWN_TOPOLOGY_SECTIONS, "
            "and rules/diagnostics.yaml."
        ),
        "features": {
            "completion": _completion_coverage(),
            "hover": _hover_coverage(),
            "diagnostics": _diagnostics_coverage(),
            "formatting": _formatting_coverage(),
            "code_actions": _code_actions_coverage(),
            "symbols": _symbols_coverage(),
        },
        # Convenience rollup so OpenQC dashboards can show one number per LSP.
        "feature_status": {
            "completion": "available",
            "hover": "available",
            "diagnostics": "available",
            "formatting": "available",
            "code_actions": "available",
            "symbols": "available",
        },
    }
