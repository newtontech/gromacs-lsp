"""Document symbol extraction for GROMACS file formats."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .analyzer import SUPPORTED_SUFFIXES, SECTION_RE


def document_symbols(path: Path) -> list[dict[str, Any]]:
    """Extract document symbols from a GROMACS file.

    For MDP files, returns key=value pairs.
    For topology files, returns section headers.
    """
    content = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".mdp":
        return _mdp_symbols(content)
    if suffix in {".top", ".itp"}:
        return _topology_symbols(content)
    if suffix == ".gro":
        return _gro_symbols(content)
    return []


def _mdp_symbols(content: str) -> list[dict[str, Any]]:
    """Extract symbols from an MDP file (key=value settings)."""
    symbols: list[dict[str, Any]] = []
    for line_no, raw in enumerate(content.splitlines(), start=1):
        stripped = raw.split(";", 1)[0].strip()
        if not stripped or "=" not in stripped:
            continue
        key, _ = (part.strip() for part in stripped.split("=", 1))
        symbols.append({
            "name": key,
            "kind": 6,  # Property
            "line": line_no,
            "column": 1,
        })
    return symbols


def _topology_symbols(content: str) -> list[dict[str, Any]]:
    """Extract symbols from a topology file (section headers)."""
    symbols: list[dict[str, Any]] = []
    for line_no, raw in enumerate(content.splitlines(), start=1):
        match = SECTION_RE.match(raw)
        if match:
            section_name = match.group(1).strip()
            symbols.append({
                "name": section_name,
                "kind": 7,  # Class
                "line": line_no,
                "column": raw.index("[") + 1,
            })
    return symbols


def _gro_symbols(content: str) -> list[dict[str, Any]]:
    """Extract symbols from a GRO file (minimal: title + atoms)."""
    lines = content.splitlines()
    symbols: list[dict[str, Any]] = []
    if lines:
        symbols.append({
            "name": lines[0].strip() or "GRO title",
            "kind": 19,  # File
            "line": 1,
            "column": 1,
        })
    if len(lines) >= 2:
        symbols.append({
            "name": "atoms",
            "kind": 6,  # Property
            "line": 2,
            "column": 1,
        })
    return symbols
