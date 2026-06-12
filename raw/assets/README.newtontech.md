# newtontech/gromacs-lsp

This repository is a public fork of `janjoswig/MDParser`, preserving the MIT
licensed GROMACS topology parser as the parser/test foundation for a standalone
GROMACS language server.

## Public Interface

This fork adds an MVP `gromacs_lsp` package with the shared newtontech CLI shape:

```bash
gromacs-lsp --stdio
gromacs-lint ./case --json
gromacs-fmt -w md.mdp
gromacs-test static ./case --json
```

Roadmap issues track full `.mdp`, `.top/.itp`, and `.gro` parser-backed
diagnostics, OpenQC integration, golden fixtures, and formatter parity.
