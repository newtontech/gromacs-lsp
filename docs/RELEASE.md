# Release and provenance checklist

The release version must agree across `setup.py`, `gromacs_lsp/__init__.py`,
`VERSION`, `CHANGELOG.md`, and `lsp-capabilities.json`.

Before approving a release tag:

- Run `make format`, `make lint`, `make typecheck`, `make test`, and `make check`.
- Run `make smoke-wheel`; this checks both distributions and installs the wheel
  into a fresh virtual environment.
- Confirm `raw/assets/manifest.json` still validates the captured upstream
  evidence used by the rule and documentation pipeline.
- Confirm the `wiki/` corpus passes its link/provenance gate.
- Regenerate and check `reports/docstring-wiki-raw-traceability.json`.
- From a managed latest OpenQC checkout, run
  `npm run lsp:check-latest -- --fail-on-drift` and record any real drift.

After the metadata PR is merged and a human approves its merge commit, create
and push `v0.0.4`. The tag-only workflow verifies the tag and artifacts, then
uses the protected `pypi` environment for Trusted Publishing and creates a
GitHub Release. Pull requests and ordinary branch pushes cannot publish.
