#!/usr/bin/env python3
"""Verify source and optional wheel metadata for a GROMACS LSP release."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from email.parser import Parser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "gromacs-lsp"


def _setup_version() -> str:
    text = (ROOT / "setup.py").read_text(encoding="utf-8")
    match = re.search(r'version=["\']([^"\']+)["\']', text)
    if match is None:
        raise ValueError("package version is missing from setup.py")
    return match.group(1)


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def verify_source(tag: str) -> tuple[str, list[str]]:
    version = _setup_version()
    errors: list[str] = []
    manifest = json.loads((ROOT / "lsp-capabilities.json").read_text(encoding="utf-8"))
    init_text = (ROOT / "gromacs_lsp" / "__init__.py").read_text(encoding="utf-8")

    _require(
        tag == f"v{version}", f"tag {tag!r} does not match version {version!r}", errors
    )
    _require(
        (ROOT / "VERSION").read_text(encoding="utf-8").strip() == version,
        "VERSION does not match setup.py",
        errors,
    )
    _require(
        f'__version__ = "{version}"' in init_text,
        "package version is inconsistent",
        errors,
    )
    _require(
        manifest.get("releaseVersion") == version,
        "manifest releaseVersion is inconsistent",
        errors,
    )
    _require(
        manifest.get("releaseTag") == tag, "manifest releaseTag is inconsistent", errors
    )
    _require(
        manifest.get("repository") == "newtontech/gromacs-lsp",
        "manifest repository is inconsistent",
        errors,
    )
    _require(
        manifest.get("traceabilityReportPath")
        == "reports/docstring-wiki-raw-traceability.json",
        "manifest traceability report path is inconsistent",
        errors,
    )
    for relative_path in (
        "CHANGELOG.md",
        "docs/RELEASE.md",
        "raw/assets/manifest.json",
        "reports/docstring-wiki-raw-traceability.json",
    ):
        _require(
            (ROOT / relative_path).is_file(),
            f"required release evidence is missing: {relative_path}",
            errors,
        )
    return version, errors


def verify_wheel(wheel: Path, version: str) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_name = next(
            (name for name in names if name.endswith(".dist-info/METADATA")), None
        )
        entry_points_name = next(
            (name for name in names if name.endswith(".dist-info/entry_points.txt")),
            None,
        )
        _require(metadata_name is not None, "wheel METADATA is missing", errors)
        _require(
            entry_points_name is not None, "wheel entry_points.txt is missing", errors
        )
        _require(
            any(name.endswith(".data/data/lsp-capabilities.json") for name in names),
            "wheel capability manifest is missing",
            errors,
        )
        _require(
            any(name.endswith(".data/data/rules/diagnostics.yaml") for name in names),
            "wheel diagnostic rules are missing",
            errors,
        )
        _require(
            not any(name.startswith(("test/", "tests/")) for name in names),
            "wheel contains repository test packages",
            errors,
        )
        if metadata_name is not None:
            metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
            _require(
                metadata.get("Name") == PACKAGE,
                "wheel package name is inconsistent",
                errors,
            )
            _require(
                metadata.get("Version") == version,
                "wheel version is inconsistent",
                errors,
            )
            _require(
                any(
                    value.startswith("PyYAML")
                    for value in metadata.get_all("Requires-Dist", [])
                ),
                "wheel PyYAML runtime dependency is missing",
                errors,
            )
        if entry_points_name is not None:
            entry_points = archive.read(entry_points_name).decode("utf-8")
            for command in ("gromacs-lsp", "gromacs-lsp-tool"):
                _require(
                    f"{command} =" in entry_points,
                    f"wheel entry point {command} is missing",
                    errors,
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Release tag, for example v0.0.4")
    parser.add_argument("--wheel", type=Path, help="Optional built wheel to inspect")
    args = parser.parse_args()

    try:
        version, errors = verify_source(args.tag)
        if args.wheel is not None:
            errors.extend(verify_wheel(args.wheel, version))
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        zipfile.BadZipFile,
    ) as exc:
        errors = [str(exc)]

    if errors:
        for error in errors:
            print(f"release verification failed: {error}", file=sys.stderr)
        return 1
    print(f"release verification passed: {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
