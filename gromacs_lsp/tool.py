"""Agent-facing CLI for Diagnostic Engine v1 operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .rich_diagnostics import agent_check_payload
from .agent_operations import operation_path, with_capabilities

SOFTWARE = "gromacs"


def _capabilities_payload() -> dict[str, Any]:
    for parent in Path(__file__).resolve().parents:
        manifest_path = parent / "lsp-capabilities.json"
        if manifest_path.exists():
            return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "schema": "OpenQCLspCapabilities",
        "version": 1,
        "software": SOFTWARE,
        "capabilities": [
            "diagnostics",
            "rich-diagnostics",
            "completion",
            "hover",
            "symbols",
            "fix-preview",
            "llm-wiki",
            "openqc-context",
        ],
        "agentCli": {
            "operations": ["capabilities", "check", "context", "complete", "hover", "symbols", "fix"],
            "jsonFormat": True,
            "failOnBlocking": True,
        },
    }


_GMX_UPPER_NAMES = frozenset()


def _file_type(path: Path) -> str:
    name = path.name.upper()
    if name in _GMX_UPPER_NAMES:
        return name
    if "." in path.name:
        return path.suffix.lstrip(".").lower()
    return name.lower()


def _collect_diagnostics(path: Path) -> list[Any]:
    from .analyzer import analyze_path

    return list(analyze_path(path))


def check_path(path: Path) -> dict[str, Any]:
    uri = path.resolve().as_uri()
    diagnostics = _collect_diagnostics(path)
    return agent_check_payload(
        software=SOFTWARE,
        uri=uri,
        operation="check",
        diagnostics=diagnostics,
        path=str(path),
        file_type=_file_type(path),
    )


def _rule_payload(rule_id: str) -> dict[str, Any] | None:
    """Return the OpenQC rule manifest entry for ``rule_id``."""
    from .rules import load_manifest, rule_meta

    manifest = load_manifest()
    meta = rule_meta(rule_id)
    if meta is None:
        return None
    return {
        "operation": "explain",
        "software": SOFTWARE,
        "diagnostic_engine": manifest.get("version", 1),
        "manifest_schema": manifest.get("schema"),
        **meta,
    }


def explain_main(argv: list[str] | None = None) -> str:
    """Entry point used by tests; returns the JSON document for a rule id."""
    parser = argparse.ArgumentParser(prog="gromacs-lsp-tool explain")
    parser.add_argument("rule_id")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args(argv)
    payload = _rule_payload(args.rule_id)
    if payload is None:
        payload = {
            "operation": "explain",
            "software": SOFTWARE,
            "rule_id": args.rule_id,
            "known": False,
        }
    return json.dumps(payload, indent=2, sort_keys=True)


def rules_main(argv: list[str] | None = None) -> str:
    """Entry point that dumps the full exported rule manifest."""
    from .rules import RULES, load_manifest

    _ = argv
    manifest = load_manifest()
    payload = {
        "operation": "rules",
        "software": SOFTWARE,
        "diagnostic_engine": manifest.get("version", 1),
        "manifest_schema": manifest.get("schema"),
        "rule_ids": sorted(RULES),
        "rules": manifest["rules"],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _operation_payload(path: Path, operation: str, line: int = 0, character: int = 0) -> dict[str, Any]:
    return operation_path(
        path,
        operation,
        software=SOFTWARE,
        file_type_func=_file_type,
        collect_diagnostics=_collect_diagnostics,
        line=line,
        character=character,
    )

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gromacs-lsp-tool")
    subparsers = parser.add_subparsers(dest="operation", required=True)
    capabilities = subparsers.add_parser("capabilities")
    capabilities.add_argument("--format", choices=["json"], default="json")
    explain = subparsers.add_parser(
        "explain", help="emit the manifest entry for a single rule id"
    )
    explain.add_argument("rule_id")
    explain.add_argument("--format", choices=["json"], default="json")
    rules = subparsers.add_parser(
        "rules", help="dump the full exported rule manifest"
    )
    rules.add_argument("--format", choices=["json"], default="json")
    for operation in ("check", "context", "complete", "hover", "symbols", "fix"):
        sub = subparsers.add_parser(operation)
        sub.add_argument("path", type=Path)
        sub.add_argument("--format", choices=["json"], default="json")
        sub.add_argument("--line", type=int, default=0, help="0-based line for position-aware operations.")
        sub.add_argument("--character", type=int, default=0, help="0-based character for position-aware operations.")
        if operation == "check":
            sub.add_argument("--fail-on-blocking", action="store_true")
    args = parser.parse_args(argv)

    if args.operation == "capabilities":
        print(json.dumps(_capabilities_payload(), indent=2, sort_keys=True))
        return 0
    if args.operation == "explain":
        print(explain_main([args.rule_id, "--format", args.format]))
        return 0
    if args.operation == "rules":
        print(rules_main(["--format", args.format]))
        return 0
    if args.operation == "check":
        payload = with_capabilities(check_path(args.path), "check")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if getattr(args, "fail_on_blocking", False) and not payload["ok"] else 0
    payload = _operation_payload(args.path, args.operation, args.line, args.character)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
