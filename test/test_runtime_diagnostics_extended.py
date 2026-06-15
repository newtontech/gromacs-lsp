"""Extended runtime diagnostics tests for GROMACS (issue #45).

Validates that:
1. Additional runtime error patterns are detected
2. New diagnostic codes are emitted with proper provenance
3. Fix operation provides deterministic repair previews
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "test" / "fixtures"


def _run_tool(*args: str) -> dict:
    """Run ``gromacs-lsp-tool`` and return its parsed JSON payload."""
    cmd = [sys.executable, "-m", "gromacs_lsp.tool", *args]
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode in (0, 1), proc.stderr
    payload = json.loads(proc.stdout)
    return payload


# ===================================================================
# Additional runtime error pattern tests
# ===================================================================


class TestAdditionalRuntimePatterns:
    def test_missing_topology_pattern(self) -> None:
        from gromacs_lsp.log_parser import parse_log

        log_content = "Could not find topology file topol.top\n"
        log_path = FIXTURES / "logs" / "test_missing_topology.log"
        log_path.write_text(log_content)
        
        diags = parse_log(log_path)
        matches = [d for d in diags if d.code == "GMX404"]
        assert matches, f"Expected GMX404, got {[d.code for d in diags]}"
        assert "missing topology" in matches[0].message.lower()
        
        log_path.unlink()

    def test_atom_count_mismatch_pattern(self) -> None:
        from gromacs_lsp.log_parser import parse_log

        log_content = "Number of atoms in topology (100) does not match structure (99)\n"
        log_path = FIXTURES / "logs" / "test_atom_count.log"
        log_path.write_text(log_content)
        
        diags = parse_log(log_path)
        matches = [d for d in diags if d.code == "GMX405"]
        assert matches, f"Expected GMX405, got {[d.code for d in diags]}"
        assert "atom count mismatch" in matches[0].message.lower()
        
        log_path.unlink()

    def test_box_dimension_error_pattern(self) -> None:
        from gromacs_lsp.log_parser import parse_log

        log_content = "Illegal box dimension\n"
        log_path = FIXTURES / "logs" / "test_box_dimension.log"
        log_path.write_text(log_content)
        
        diags = parse_log(log_path)
        matches = [d for d in diags if d.code == "GMX406"]
        assert matches, f"Expected GMX406, got {[d.code for d in diags]}"
        assert "box dimension" in matches[0].message.lower()
        
        log_path.unlink()

    def test_cuda_error_pattern(self) -> None:
        from gromacs_lsp.log_parser import parse_log

        log_content = "CUDA error: out of memory\n"
        log_path = FIXTURES / "logs" / "test_cuda_error.log"
        log_path.write_text(log_content)
        
        diags = parse_log(log_path)
        matches = [d for d in diags if d.code == "GMX407"]
        assert matches, f"Expected GMX407, got {[d.code for d in diags]}"
        assert "cuda error" in matches[0].message.lower()
        
        log_path.unlink()

    def test_memory_error_pattern(self) -> None:
        from gromacs_lsp.log_parser import parse_log

        log_content = "Memory allocation failed\n"
        log_path = FIXTURES / "logs" / "test_memory_error.log"
        log_path.write_text(log_content)
        
        diags = parse_log(log_path)
        matches = [d for d in diags if d.code == "GMX408"]
        assert matches, f"Expected GMX408, got {[d.code for d in diags]}"
        assert "memory error" in matches[0].message.lower()
        
        log_path.unlink()

    def test_io_error_pattern(self) -> None:
        from gromacs_lsp.log_parser import parse_log

        log_content = "I/O error: cannot open file\n"
        log_path = FIXTURES / "logs" / "test_io_error.log"
        log_path.write_text(log_content)
        
        diags = parse_log(log_path)
        matches = [d for d in diags if d.code == "GMX409"]
        assert matches, f"Expected GMX409, got {[d.code for d in diags]}"
        assert "i/o error" in matches[0].message.lower()
        
        log_path.unlink()


# ===================================================================
# Fix operation tests for log files
# ===================================================================


class TestFixOperationForLogs:
    def test_fix_returns_actions_for_fatal_error(self) -> None:
        log_path = FIXTURES / "logs" / "fatal_error.log"
        payload = _run_tool("fix", str(log_path))
        assert "actions" in payload
        assert isinstance(payload["actions"], list)
        assert len(payload["actions"]) > 0

    def test_fix_returns_actions_for_lincs_instability(self) -> None:
        log_path = FIXTURES / "logs" / "lincs_instability.log"
        payload = _run_tool("fix", str(log_path))
        assert "actions" in payload
        assert isinstance(payload["actions"], list)
        assert len(payload["actions"]) > 0

    def test_fix_has_capabilities(self) -> None:
        log_path = FIXTURES / "logs" / "fatal_error.log"
        payload = _run_tool("fix", str(log_path))
        assert "capabilities" in payload
        assert payload["capabilities"]["operation"] == "fix"


# ===================================================================
# Provenance tests for new rules
# ===================================================================


class TestNewRuleProvenance:
    def test_new_rules_have_provenance(self) -> None:
        from gromacs_lsp.rules import RULES, diagnostic_provenance

        new_rules = [
            "gromacs.log.missing_topology",
            "gromacs.log.atom_count_mismatch",
            "gromacs.log.box_dimension_error",
            "gromacs.log.cuda_error",
            "gromacs.log.memory_error",
            "gromacs.log.io_error",
        ]
        
        for rule_id in new_rules:
            assert rule_id in RULES, f"Rule {rule_id} not in RULES"
            prov = diagnostic_provenance(rule_id)
            assert prov, f"No provenance for {rule_id}"
            assert prov["kind"] == "official_docs", prov
            assert prov["url"].startswith("https://manual.gromacs.org/"), prov