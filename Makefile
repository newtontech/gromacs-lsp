.PHONY: install format lint typecheck test wiki-check verify-release build smoke-wheel check cleanup-merged

PYTHON ?= python3

install:
	bash scripts/install.sh

format:
	bash scripts/format.sh
	$(PYTHON) -m ruff check --fix scripts/verify_release.py test/test_release_contract.py
	$(PYTHON) -m ruff format scripts/verify_release.py test/test_release_contract.py

lint:
	bash scripts/lint.sh
	$(PYTHON) -m ruff check scripts/verify_release.py test/test_release_contract.py

typecheck:
	bash scripts/typecheck.sh
	$(PYTHON) -m mypy scripts/verify_release.py

test:
	bash scripts/test.sh

wiki-check:
	bash scripts/wiki-lint.sh

verify-release:
	$(PYTHON) scripts/verify_release.py --tag v$$(cat VERSION)

build:
	rm -rf build dist
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*

smoke-wheel: build
	bash scripts/smoke_wheel.sh dist/*.whl

check: lint typecheck test wiki-check verify-release

cleanup-merged:
	bash scripts/cleanup_merged_worktrees.sh
