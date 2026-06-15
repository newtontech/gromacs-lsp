# GROMACS Runtime Log Fixtures

Canonical GROMACS runtime log fixtures used by the agent CLI smoke tests and
the OpenQC `lsp:check-family` gate.

## Fixtures

| File | Expected code | Severity | Blocking | Provenance |
|------|---------------|----------|----------|------------|
| `fatal_error.log` | `GMX401` (`gromacs.log.fatal_error`) | error | yes | https://manual.gromacs.org/current/user-guide/run-time-errors.html |
| `lincs_instability.log` | `GMX402` (`gromacs.log.lincs_instability`) | error | yes | https://manual.gromacs.org/current/user-guide/run-time-errors.html |
| `settle_shake_failure.log` | `GMX403` (`gromacs.log.settle_shake_failure`) | error | yes | https://manual.gromacs.org/current/user-guide/run-time-errors.html |
| `valid_run.log` | (none) | — | — | — |

## Closed-loop contract

`gromacs-lsp-tool log <path>` parses each log file via
`gromacs_lsp.log_parser.parse_log` and returns `DiagnosticEnvelope/v1` JSON.
Log parsing is intentionally separate from MDP/topology analysis: a clean
input can still produce a runtime log diagnostic, and a log diagnostic never
edits the input file.

## Source

- Runtime error anchor: https://manual.gromacs.org/current/user-guide/run-time-errors.html
- Artifacts are minimal synthetic reproductions of real GROMACS 2023 runtime failures.
