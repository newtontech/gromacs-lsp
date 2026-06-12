"""Completion items for GROMACS file formats."""
from __future__ import annotations

from typing import Any

from .hover import _MDP_DOCS, _TOPOLOGY_DOCS


def mdp_completions() -> list[dict[str, Any]]:
    """Return completion items for MDP keys.

    Each item is a dict with keys ``label``, ``detail``, and ``kind``.
    """
    items: list[dict[str, Any]] = []
    for key in sorted(_MDP_DOCS):
        # Use first line of docs as detail
        first_line = _MDP_DOCS[key].split("\n")[0]
        items.append({
            "label": key,
            "detail": first_line,
            "kind": 6,  # LSP CompletionItemKind.Property
        })
    return items


def topology_completions() -> list[dict[str, Any]]:
    """Return completion items for topology section headers.

    Each item is a dict with keys ``label``, ``detail``, and ``kind``.
    """
    items: list[dict[str, Any]] = []
    for name in sorted(_TOPOLOGY_DOCS):
        items.append({
            "label": name,
            "detail": _TOPOLOGY_DOCS[name],
            "kind": 7,  # LSP CompletionItemKind.Class
        })
    return items
