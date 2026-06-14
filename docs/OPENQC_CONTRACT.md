# OpenQC Integration Contract

This document describes how `gromacs-lsp` participates in the OpenQC fleet
contract maintained by `newtontech/bohrium_skills`.

## Agent CLI Operations

The `gromacs-lsp-tool` binary exposes the following operations via
`DiagnosticEnvelope/v1` JSON:

| Operation    | Description                                         |
|------------- |---------------------------------------------------- |
| `capabilities` | Emit the capabilities manifest (`lsp-capabilities.json`) |
| `check`       | Analyze a file and return diagnostics                |
| `log`         | Parse a GROMACS runtime log for error patterns       |
| `explain`     | Emit the manifest entry for a single rule id         |
| `rules`       | Dump the full exported rule manifest                 |
| `context`     | Emit editor context (line, token, nearby diagnostics)|
| `complete`    | Emit completion items for the cursor position        |
| `hover`       | Emit hover documentation for the token at cursor     |
| `symbols`     | Emit document symbols for the file                   |
| `fix`         | Emit quick-fix actions for diagnostics (incl. code actions) |
| `source-manifest` | Emit the OpenQC source manifest aggregating capabilities, rules, and features |
| `features`    | Emit the generated LSP feature manifest (coverage by data source) |
| `code-actions`| Emit the exported code-action surface                |

### Usage

```bash
# Static analysis of an MDP file
gromacs-lsp-tool check path/to/file.mdp --json

# Log file analysis
gromacs-lsp-tool log path/to/simulation.log --json

# Rule explanation
gromacs-lsp-tool explain gromacs.mdp.unknown_parameter --json

# Full rule manifest
gromacs-lsp-tool rules --json

# Source manifest aggregating capabilities, rules, and generated features
gromacs-lsp-tool source-manifest --json

# Generated LSP feature coverage (completion/hover/diagnostics/etc.)
gromacs-lsp-tool features --json

# Exported code-action surface
gromacs-lsp-tool code-actions --json

# Code actions for diagnostics at a position
gromacs-lsp-tool fix path/to/file.mdp --line 1 --character 0 --json
```

## Rule Manifest

Rules are declared in `rules/diagnostics.yaml` and loaded by
`gromacs_lsp/rules.py`. Each rule carries:

- `rule_id` — stable identifier (e.g. `gromacs.mdp.unknown_parameter`)
- `code` — legacy diagnostic code (e.g. `GMX002`)
- `severity` — `error` or `warning`
- `category` — one of the Diagnostic Engine v1 categories
- `source` — `official` or `community`
- `confidence` — 0.0–1.0
- `blocking` — whether the diagnostic blocks run-gate
- `manual_ref` — URL to the official documentation
- `fix_hint` — structured hint for the agent CLI

### Current Rule Surface

| Rule ID                               | Code   | Severity | Category               | File Type |
|-------------------------------------- |--------|---------- |----------------------- |---------- |
| `gromacs.mdp.unknown_parameter`       | GMX002 | error     | schema                  | mdp       |
| `gromacs.mdp.invalid_value`           | GMX004 | error     | type/value              | mdp       |
| `gromacs.topology.missing_include`    | GMX023 | error     | cross-file reference    | top       |
| `gromacs.topology.molecule_count_mismatch` | GMX024 | error | type/value             | top       |
| `gromacs.log.fatal_error`             | GMX401 | error     | preflight/runtime-risk  | log       |
| `gromacs.log.lincs_instability`       | GMX402 | error     | preflight/runtime-risk  | log       |
| `gromacs.log.settle_shake_failure`    | GMX403 | error     | preflight/runtime-risk  | log       |
| `gromacs.cutoff.pme_warning`          | GMX102 | warning   | preflight/runtime-risk  | mdp       |

## Code Actions

Concrete code actions live in `gromacs_lsp/code_actions.py` and are surfaced
through the `fix` CLI operation. Each action carries an LSP-style
`WorkspaceEdit` when the fix can be applied mechanically, and a
`safe_to_auto_apply` flag so consumers can decide whether to skip the
confirmation prompt.

| Kind                    | Diagnostic Codes | Safe to Auto-Apply | Behavior                                                                 |
|-------------------------|------------------|--------------------|--------------------------------------------------------------------------|
| `rename_mdp_keyword`    | GMX002           | yes                | Rename a typo'd MDP key to the closest valid neighbour (≤2 edit distance)|
| `create_include`        | GMX023           | no                 | Surface the path of a missing `#include` so the caller can create it    |
| `lincs_playbook`        | GMX402           | no                 | Stability remediation playbook for a LINCS instability (reduce `dt`, etc.)|
| `settle_shake_playbook` | GMX403           | no                 | Stability remediation playbook for a SETTLE/SHAKE solver failure        |

The exported kind surface is also reachable through
`gromacs-lsp-tool code-actions --json` for OpenQC discovery.

## Source Manifest and Generated Features

`gromacs-lsp-tool source-manifest --json` aggregates the LSP capabilities
block (`lsp-capabilities.json`), the diagnostic rule manifest
(`rules/diagnostics.yaml`), the generated LSP feature manifest, and the
source provenance into a single OpenQC-facing JSON document. Consumers read
this single document to discover what `gromacs-lsp` exports without
re-deriving the surface from individual files.

`gromacs-lsp-tool features --json` emits the generated LSP feature manifest.
Each feature (completion, hover, diagnostics, formatting, code actions,
symbols) is generated from the in-repo data dictionaries
(`_MDP_DOCS`, `_MDP_VALID_VALUES`, `_TOPOLOGY_DOCS`, `KNOWN_TOPOLOGY_SECTIONS`,
and `rules/diagnostics.yaml`), so the manifest cannot drift from the actual
feature surface.

## DiagnosticEnvelope/v1

All agent-facing JSON payloads follow the DiagnosticEnvelope/v1 contract
defined in `diagnostics/diagnostic-engine-v1.schema.json`. The envelope
includes:

- `uri` — file URI
- `operation` — the operation that produced the payload
- `ok` — `true` when no blocking diagnostics exist
- `version` — envelope version (`1.0`)
- `software` — `gromacs`
- `diagnostics` — array of rich diagnostic objects
- `summary` — counts of total, blocking, errors, and warnings

Each rich diagnostic includes:

- `diagnostic_engine` — `1.0`
- `rule_id` — stable rule identifier (or `null` for legacy diagnostics)
- `code`, `severity`, `category`, `confidence`, `source`
- `range` — LSP-style `{start, end}` with 0-based line/character
- `file_type`, `path`
- `fix_hints` — array of structured fix hints
- `blocking` — whether this diagnostic blocks run-gate
- `message` — human-readable description

## Fixtures and Golden Assertions

Each rule must have:

1. An **invalid fixture** that triggers the rule (e.g. `test/fixtures/logs/fatal_error.log`)
2. A **valid fixture** that does not trigger the rule (e.g. `test/fixtures/logs/valid_run.log`)
3. A **golden JSON** file with expected diagnostics (e.g. `test/fixtures/rules/log_fatal_error.json`)

Tests follow the pattern in `test/test_rules/test_gromacs_*.py`:

- `test_rule_id_is_exported_constant` — rule is in `RULES` frozenset
- `test_manifest_exports_rule` — rule appears in `rules/diagnostics.yaml`
- `test_invalid_fixture_matches_golden` — invalid fixture produces expected diagnostics
- `test_valid_fixture_does_not_trigger` — valid fixture produces no diagnostics
- `test_explain_json_surfaces_rule` — `explain` CLI surfaces the rule

## OpenQC Smoke

OpenQC consumers can:

1. Read `lsp-capabilities.json` to discover the rule surface
2. Run `gromacs-lsp-tool rules --json` to get the full manifest
3. Run `gromacs-lsp-tool check <file> --json` to get diagnostics
4. Run `gromacs-lsp-tool log <file> --json` to parse runtime logs
5. Run `gromacs-lsp-tool explain <rule_id> --json` to get rule details
6. Run `gromacs-lsp-tool source-manifest --json` to get the aggregated source manifest
7. Run `gromacs-lsp-tool features --json` to inspect generated LSP feature coverage
8. Run `gromacs-lsp-tool code-actions --json` to list the exported code-action kinds
9. Run `gromacs-lsp-tool fix <file> --line N --character C --json` to get concrete actions
