"""Agent-facing CLI for Diagnostic Engine v1 operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .skill_export import export_skill, skill_spec_text

from .rich_diagnostics import agent_check_payload
from .agent_operations import operation_path, with_capabilities

SOFTWARE = "gromacs"


def _capabilities_payload() -> dict[str, Any]:
    for parent in Path(__file__).resolve().parents:
        manifest_path = parent / "lsp-capabilities.json"
        if manifest_path.exists():
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            # The shipped capabilities file is the canonical source of truth.
            # Augment the agent CLI operation list with the source-manifest,
            # features, and code-actions operations added in #12/#13/#23 so
            # OpenQC consumers that read this payload first still discover
            # them without waiting for a follow-up capabilities file bump.
            agent_cli = dict(data.get("agentCli") or {})
            operations = list(agent_cli.get("operations") or [])
            for op in (
                "source-manifest",
                "features",
                "code-actions",
            ):
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
            "code-actions",
            "generated-features",
            "source-manifest",
            "llm-wiki",
            "openqc-context",
        ],
        "agentCli": {
            "operations": [
                "capabilities",
                "check",
                "log",
                "context",
                "complete",
                "hover",
                "symbols",
                "fix",
                "source-manifest",
                "features",
                "code-actions",
            ],
            "jsonFormat": True,
            "failOnBlocking": True,
        },
    }


_GMX_UPPER_NAMES: frozenset[str] = frozenset()


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


def _load_intent(path: Path) -> dict[str, Any] | None:
    """Load the optional preflight intent contract for a case directory.

    The intent contract is the only place preflight policy overrides live
    (e.g. ``software_version``, ``runtime_image``). It is a workspace-local
    artifact, never a MatMaster/Bohrium runtime concept.
    """
    case_dir = path if path.is_dir() else path.parent
    intent_path = case_dir / ".gromacs-lsp" / "intent.json"
    if not intent_path.exists():
        return None
    try:
        data = json.loads(intent_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _looks_like_workspace(case_dir: Path) -> bool:
    """True when a directory is a real generated-input workspace.

    Preflight needs at least a ``.mdp`` primary input plus a topology or
    coordinate file to build a meaningful cross-artifact graph; a directory
    with only an ``.mdp`` still runs preflight (it can flag missing primary
    keys), but a directory with no ``.mdp`` at all falls back to the legacy
    directory lint path so callers that progressively build inputs are not
    flooded with blocking missing-artifact errors before the workspace exists.
    """
    if not case_dir.is_dir():
        return False
    return any(case_dir.glob("*.mdp"))


def _collect_preflight(
    path: Path, intent: dict[str, Any] | None
) -> tuple[list[Any], list[dict[str, Any]], dict[str, Any]]:
    """Return ``(preflight_diagnostics, artifact_graph, version_assumption)``.

    Imported lazily so callers that never touch preflight (e.g. single-file
    LSP hover) pay no import cost.
    """
    from .preflight import preflight_diagnostics, resolve_version_assumption

    case_dir = path if path.is_dir() else path.parent
    diagnostics, graph = preflight_diagnostics(case_dir, intent=intent)
    version_assumption = resolve_version_assumption(intent)
    return diagnostics, graph.to_json(), version_assumption


# Codes already emitted by the legacy analyzer that overlap with the universal
# preflight surface. We keep the legacy emission (it carries the existing test
# contract) and drop the duplicate preflight variant to avoid noisy double
# reports. The preflight shape is still proven by every other fixture.
_OVERLAP_CODES_BY_LEGACY = {
    "GMX002": {"GMXPREF110"},  # legacy unknown MDP parameter
    "GMX023": {"GMXPREF103"},  # legacy unresolved topology #include
    "GMX024": {"GMXPREF104"},  # legacy [ molecules ] without [ moleculetype ]
}


def _dedupe_preflight(legacy: list[Any], preflight: list[Any]) -> list[Any]:
    """Drop preflight diagnostics whose finding the legacy analyzer already emitted."""
    emitted_legacy = {
        getattr(item, "code", None)
        or (item.get("code") if isinstance(item, dict) else None)
        for item in legacy
    }
    suppressed_preflight: set[str] = set()
    for legacy_code, preflight_codes in _OVERLAP_CODES_BY_LEGACY.items():
        if legacy_code in emitted_legacy:
            suppressed_preflight |= preflight_codes
    return [
        item
        for item in preflight
        if (item.get("code") if isinstance(item, dict) else None)
        not in suppressed_preflight
    ]


def _collect_log_diagnostics(path: Path) -> list[Any]:
    from .log_parser import parse_log

    return list(parse_log(path))


def check_path(path: Path) -> dict[str, Any]:
    uri = path.resolve().as_uri()
    intent = _load_intent(path)
    diagnostics = _collect_diagnostics(path)
    # Universal preflight diagnostics augment the legacy analyzer output, but
    # only for a real generated-input workspace (a directory). A bare single
    # file path keeps the legacy single-file behavior so existing consumers
    # that lint one file at a time are unaffected.
    case_dir = (
        path
        if path.is_dir()
        else (path.parent if path.suffix.lower() == ".mdp" else None)
    )
    artifacts: list[dict[str, Any]] = []
    version_assumption: dict[str, Any] | None = None
    # Preflight only runs against a real generated-input workspace: a directory
    # that has at least one .mdp file. This keeps the single-file lint path
    # unchanged (it has no cross-artifact graph to build).
    if case_dir is not None and _looks_like_workspace(case_dir):
        preflight, artifacts, version_assumption = _collect_preflight(path, intent)
        diagnostics.extend(_dedupe_preflight(diagnostics, preflight))
    return agent_check_payload(
        software=SOFTWARE,
        uri=uri,
        operation="check",
        diagnostics=diagnostics,
        path=str(path),
        file_type=_file_type(path),
        intent=intent,
        version_assumption=version_assumption,
        artifacts=artifacts,
    )


def preflight_path(path: Path) -> dict[str, Any]:
    """Return a preflight-only payload (universal checks, no legacy analyzer)."""
    from .preflight import preflight_diagnostics, resolve_version_assumption

    intent = _load_intent(path)
    case_dir = path if path.is_dir() else path.parent
    diagnostics, graph = preflight_diagnostics(case_dir, intent=intent)
    version_assumption = resolve_version_assumption(intent)
    payload = agent_check_payload(
        software=SOFTWARE,
        uri=case_dir.resolve().as_uri(),
        operation="preflight",
        diagnostics=diagnostics,
        path=str(case_dir),
        file_type="case-dir",
        intent=intent,
        version_assumption=version_assumption,
        artifacts=graph.to_json(),
    )
    return with_capabilities(payload, "preflight")


def manifest_path(path: Path | None = None) -> dict[str, Any]:
    """Return the fleet preflight manifest.

    When ``path`` is given, fixture expectations declared in
    ``.gromacs-lsp/fixtures.json`` are merged in so the parent probe can confirm
    a case directory exercises the documented codes.
    """
    from .preflight import fleet_manifest

    fixtures: list[dict[str, Any]] = []
    if path is not None:
        case_dir = path if path.is_dir() else path.parent
        fixtures_path = case_dir / ".gromacs-lsp" / "fixtures.json"
        if fixtures_path.exists():
            try:
                data = json.loads(fixtures_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = None
            if isinstance(data, list):
                fixtures = [item for item in data if isinstance(item, dict)]
            elif isinstance(data, dict) and isinstance(data.get("fixtures"), list):
                fixtures = [item for item in data["fixtures"] if isinstance(item, dict)]
    return fleet_manifest(fixtures=fixtures)


def log_check_path(path: Path) -> dict[str, Any]:
    uri = path.resolve().as_uri()
    diagnostics = _collect_log_diagnostics(path)
    return agent_check_payload(
        software=SOFTWARE,
        uri=uri,
        operation="check",
        diagnostics=diagnostics,
        path=str(path),
        file_type="log",
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


def source_manifest_main(argv: list[str] | None = None) -> str:
    """Entry point that emits the OpenQC source manifest (issue #12)."""
    from .source_manifest import source_manifest

    _ = argv
    payload = {
        "operation": "source-manifest",
        "software": SOFTWARE,
        **source_manifest(),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def features_main(argv: list[str] | None = None) -> str:
    """Entry point that emits the generated LSP feature manifest (issue #13)."""
    from .generated_features import generated_features_manifest

    _ = argv
    payload = {
        "operation": "features",
        "software": SOFTWARE,
        **generated_features_manifest(),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def code_actions_main(argv: list[str] | None = None) -> str:
    """Entry point that emits the exported code-action surface (issue #23)."""
    from .code_actions import code_action_kinds

    _ = argv
    payload = {
        "operation": "code-actions",
        "software": SOFTWARE,
        "kinds": code_action_kinds(),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _operation_payload(
    path: Path, operation: str, line: int = 0, character: int = 0
) -> dict[str, Any]:
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
    skill_spec = subparsers.add_parser("skill-spec")
    skill_spec.add_argument("--format", choices=["json", "yaml"], default="json")
    skill_export = subparsers.add_parser("skill-export")
    skill_export.add_argument("--output", type=Path, required=True)
    capabilities = subparsers.add_parser("capabilities")
    capabilities.add_argument("--format", choices=["json"], default="json")
    explain = subparsers.add_parser(
        "explain", help="emit the manifest entry for a single rule id"
    )
    explain.add_argument("rule_id")
    explain.add_argument("--format", choices=["json"], default="json")
    rules = subparsers.add_parser("rules", help="dump the full exported rule manifest")
    rules.add_argument("--format", choices=["json"], default="json")
    source_manifest_cmd = subparsers.add_parser(
        "source-manifest",
        help="emit the OpenQC source manifest aggregating capabilities, rules, and features",
    )
    source_manifest_cmd.add_argument("--format", choices=["json"], default="json")
    features_cmd = subparsers.add_parser(
        "features",
        help="emit the generated LSP feature manifest (coverage by data source)",
    )
    features_cmd.add_argument("--format", choices=["json"], default="json")
    code_actions_cmd = subparsers.add_parser(
        "code-actions",
        help="emit the exported code-action surface",
    )
    code_actions_cmd.add_argument("--format", choices=["json"], default="json")
    preflight = subparsers.add_parser(
        "preflight", help="universal generated-input preflight checks"
    )
    preflight.add_argument("path", type=Path)
    preflight.add_argument("--format", choices=["json"], default="json")
    preflight.add_argument("--fail-on-blocking", action="store_true")
    manifest = subparsers.add_parser(
        "manifest", help="emit the fleet preflight manifest"
    )
    manifest.add_argument(
        "path",
        type=Path,
        nargs="?",
        help="Optional case directory to merge fixture expectations from.",
    )
    manifest.add_argument("--format", choices=["json"], default="json")
    for operation in ("check", "context", "complete", "hover", "symbols", "fix"):
        sub = subparsers.add_parser(operation)
        sub.add_argument("path", type=Path)
        sub.add_argument("--format", choices=["json"], default="json")
        sub.add_argument(
            "--line",
            type=int,
            default=0,
            help="0-based line for position-aware operations.",
        )
        sub.add_argument(
            "--character",
            type=int,
            default=0,
            help="0-based character for position-aware operations.",
        )
        if operation == "check":
            sub.add_argument("--fail-on-blocking", action="store_true")
    log_parser = subparsers.add_parser(
        "log", help="parse a GROMACS log file for runtime errors"
    )
    log_parser.add_argument("path", type=Path)
    log_parser.add_argument("--format", choices=["json"], default="json")
    log_parser.add_argument("--fail-on-blocking", action="store_true")
    args = parser.parse_args(argv)

    if args.operation == "skill-spec":
        print(skill_spec_text(args.format))
        return 0
    if args.operation == "skill-export":
        print(json.dumps(export_skill(args.output), indent=2, sort_keys=True))
        return 0

    if args.operation == "capabilities":
        print(json.dumps(_capabilities_payload(), indent=2, sort_keys=True))
        return 0
    if args.operation == "explain":
        print(explain_main([args.rule_id, "--format", args.format]))
        return 0
    if args.operation == "rules":
        print(rules_main(["--format", args.format]))
        return 0
    if args.operation == "source-manifest":
        print(source_manifest_main(["--format", args.format]))
        return 0
    if args.operation == "features":
        print(features_main(["--format", args.format]))
        return 0
    if args.operation == "code-actions":
        print(code_actions_main(["--format", args.format]))
        return 0
    if args.operation == "manifest":
        payload = manifest_path(getattr(args, "path", None))
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.operation == "preflight":
        payload = preflight_path(args.path)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return (
            1 if getattr(args, "fail_on_blocking", False) and not payload["ok"] else 0
        )
    if args.operation == "check":
        payload = with_capabilities(check_path(args.path), "check")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return (
            1 if getattr(args, "fail_on_blocking", False) and not payload["ok"] else 0
        )
    if args.operation == "log":
        payload = with_capabilities(log_check_path(args.path), "log")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return (
            1 if getattr(args, "fail_on_blocking", False) and not payload["ok"] else 0
        )
    if args.operation == "fix" and args.path.suffix.lower() == ".log":
        # Log files do not flow through the analyzer; route the fix operation
        # through the log parser so the code-actions capability (issue #23)
        # can surface stability playbooks for LINCS/SHAKE diagnostics.
        from .agent_operations import OPERATIONS, _fix_actions

        payload = with_capabilities(log_check_path(args.path), "fix")
        payload["actions"] = _fix_actions(
            payload["diagnostics"],
            line=args.line,
            character=args.character,
        )
        payload["position"] = {"line": args.line, "character": args.character}
        status = "available" if payload["actions"] else "unavailable"
        payload["capabilities"] = {
            "operations": list(OPERATIONS),
            "operation": "fix",
            "status": status,
            "source": "agent_operations",
        }
        if not payload["actions"]:
            payload.setdefault("summary", {})["note"] = (
                "No safe quick-fix hints are available for current diagnostics."
            )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    payload = _operation_payload(args.path, args.operation, args.line, args.character)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
