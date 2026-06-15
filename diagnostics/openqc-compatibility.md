# OpenQC Compatibility Report — gromacs-lsp

> Generated: 2026-06-15
> Capability manifest: `lsp-capabilities.json`
> Coordinator gate: `lsp:check-family`

This document records the executable evidence that `gromacs-lsp` is wired into
the OpenQC scientific LSP fleet. It is intentionally machine-readable in
structure so the coordinator can verify each claim from the repo without
running the LSP server.

## 1. Language and file detection

| Field | Value | Evidence |
|-------|-------|----------|
| `languageId` | `gromacs` | `lsp-capabilities.json` |
| `filePatterns` | `*.top`, `*.itp`, `*.mdp`, `*.gro` | `lsp-capabilities.json` |
| `displayName` | GROMACS | `lsp-capabilities.json` |

## 2. Configured executable

| Field | Value |
|-------|-------|
| `executable` | `gromacs-lsp` (editor server entrypoint: `gromacs_lsp.cli:lsp_main`) |
| `agentCli.command` | `gromacs-lsp-tool` |
| `agentCli.jsonFormat` | true |
| `agentCli.failOnBlocking` | true |

## 3. Agent CLI availability

`gromacs-lsp-tool` answers the fleet-standard operations:

```bash
gromacs-lsp-tool capabilities
gromacs-lsp-tool check <path> [--fail-on-blocking]
gromacs-lsp-tool log <path>
gromacs-lsp-tool context <path> [--line N --character N]
gromacs-lsp-tool complete <path> [--line N --character N]
gromacs-lsp-tool hover <path> [--line N --character N]
gromacs-lsp-tool symbols <path>
gromacs-lsp-tool fix <path> [--line N --character N]
gromacs-lsp-tool source-manifest
gromacs-lsp-tool features
gromacs-lsp-tool code-actions <path>
```

Every operation returns stable `DiagnosticEnvelope/v1` JSON.

## 4. Closed-loop fixture evidence

| Fixture | Expected outcome | Verified by |
|---------|------------------|-------------|
| `test/fixtures/valid/minimal_em.mdp` | clean (`analyze_file` returns no diagnostics) | `test/test_closed_loop_fixtures.py` |
| `test/fixtures/valid/valid_topology.top` | clean | `test/test_closed_loop_fixtures.py` |
| `test/fixtures/invalid/unknown_mdp_key.mdp` | `GMX002` blocking errors (2×) | `test/test_closed_loop_fixtures.py` |
| `test/fixtures/invalid/invalid_mdp_value.mdp` | `GMX004` blocking errors (2×) | `test/test_closed_loop_fixtures.py` |
| `test/fixtures/invalid/cutoff_pme_warning.mdp` | `GMX010` non-blocking warning | `test/test_closed_loop_fixtures.py` |
| `test/fixtures/invalid/missing_topology_include.top` | `GMX023` blocking error | `test/test_closed_loop_fixtures.py` |
| `test/fixtures/logs/fatal_error.log` | `GMX401` runtime log error | `test/test_closed_loop_fixtures.py` |
| `test/fixtures/logs/lincs_instability.log` | `GMX402` runtime log error | `test/test_closed_loop_fixtures.py` |
| `test/fixtures/logs/settle_shake_failure.log` | `GMX403` runtime log error | `test/test_closed_loop_fixtures.py` |
| `test/fixtures/logs/valid_run.log` | no diagnostics | `test/test_closed_loop_fixtures.py` |
| `test/fixtures/preflight/valid/` | clean preflight case directory | `test/test_closed_loop_fixtures.py` |

## 5. Source provenance summary

Every analyzer and log-parser diagnostic now carries
`source_provenance.kind=official_docs` and a URL pinned to
https://manual.gromacs.org/current/. The provenance is derived from
`rules/diagnostics.yaml` via `gromacs_lsp.rules.diagnostic_provenance`, so
adding a new rule with provenance is a single YAML entry.

## 6. Blocking policy

| Code | Severity | Blocks run-gate? |
|------|----------|------------------|
| GMX002 (unknown MDP key) | error | yes |
| GMX004 (invalid MDP value) | error | yes |
| GMX010 (PME cutoff warning) | warning | no |
| GMX023 (missing topology include) | error | yes |
| GMX024 (molecule count mismatch) | error | yes |
| GMX401 (fatal error log) | error | yes (runtime log) |
| GMX402 (LINCS instability log) | error | yes (runtime log) |
| GMX403 (SETTLE/SHAKE failure log) | error | yes (runtime log) |
| GMXPREF1xx–GMXPREF6xx (preflight) | mixed | per preflight intent |

## 7. Output/log diagnostic support

| Layer | Status |
|-------|--------|
| Input-file analyzer rules | implemented (8 rules across MDP/topology) |
| Preflight cross-file checks | implemented (GMXPREF1xx–GMXPREF6xx) |
| Runtime log parser | implemented for fatal errors, LINCS, SETTLE/SHAKE |
| Version-aware keyword scope | partial — rule manifest carries `manual_ref` per rule; runtime-version gating lives in preflight |

## 8. Verification commands

```bash
# Closed-loop fixture gate
PYTHONPATH=. python3 -m pytest test/test_closed_loop_fixtures.py -v

# Full test suite
PYTHONPATH=. python3 -m pytest test/

# One-shot agent CLI smoke
PYTHONPATH=. python3 -m gromacs_lsp.tool capabilities
PYTHONPATH=. python3 -m gromacs_lsp.tool source-manifest
PYTHONPATH=. python3 -m gromacs_lsp.tool check test/fixtures/preflight/valid --fail-on-blocking
PYTHONPATH=. python3 -m gromacs_lsp.tool log test/fixtures/logs/lincs_instability.log
```
