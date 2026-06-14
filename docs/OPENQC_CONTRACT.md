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
| `fix`         | Emit quick-fix actions for diagnostics               |

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
