# OpenQC Agent Context (OpenQC 智能体上下文)

OpenQC consumes `gromacs-lsp-tool` and `lsp-capabilities.json` to assemble diagnostics, hover, completion, symbols, examples, next-token guidance, and repair-plan hints for `gromacs` documents.

## LSP Capability Surface

| Capability | Operation | Source Evidence |
|------------|-----------|-----------------|
| Completion | `complete` | MDP keys from [completion.py](../../raw/assets/gromacs_lsp/completion.py); topology sections |
| Hover | `hover` | MDP/topology docs from [hover.py](../../raw/assets/gromacs_lsp/hover.py); see [LSP Features](./lsp-features.md) |
| Diagnostics | `check` | Value validation from [diagnostics.py](../../raw/assets/gromacs_lsp/diagnostics.py); [rich_diagnostics.py](../../gromacs_lsp/rich_diagnostics.py) |
| Symbols | `symbols` | Topology/document outline from [symbols.py](../../raw/assets/gromacs_lsp/symbols.py) |
| Fix Preview | `fix` | Repair suggestions from validation rules |
| Blocking Gate | `check` | Error diagnostics block submission (see `blockingPolicy` in `lsp-capabilities.json`) |

## Source Provenance

The LSP draws domain knowledge from these upstream sources (recorded in `lsp-capabilities.json` → `sourceProvenance`):

- **GROMACS manual**: https://manual.gromacs.org/current/
- **MDP options reference**: https://manual.gromacs.org/current/user-guide/mdp-options.html
- **Topology file formats**: https://manual.gromacs.org/current/reference-manual/topologies/topology-file-formats.html
- **Official tutorials**: https://tutorials.gromacs.org/
- **Upstream manifest**: [raw/assets/upstream-gromacs-reference.md](../../raw/assets/upstream-gromacs-reference.md)

## Diagnostic Engine

Diagnostics follow `DiagnosticEnvelope/v1` (see `diagnostics/diagnostic-engine-v1.schema.json`). Blocking policy is `blocking` — error diagnostics block agent submission until resolved.

## Example Inputs

- **Energy minimization MDP**: [raw/assets/example-em-steep.mdp](../../raw/assets/example-em-steep.mdp) — steepest descent minimization
- **NPT equilibration MDP**: [raw/assets/example-npt-equil.mdp](../../raw/assets/example-npt-equil.mdp) — V-rescale + Parrinello-Rahman
