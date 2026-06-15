"""GROMACS runtime log parser for Diagnostic Engine v1.

Parses GROMACS ``.log`` files and emits diagnostics for known runtime error
and warning patterns.  The parser is intentionally conservative — it matches
well-documented GROMACS runtime error signatures and avoids heuristic noise.
"""

from __future__ import annotations

import re
from pathlib import Path

from .diagnostics import Diagnostic
from .rules import (
    RULE_LOG_FATAL_ERROR,
    RULE_LOG_LINCS_INSTABILITY,
    RULE_LOG_SETTLE_SHAKE_FAILURE,
    rule_meta,
)

# ---------------------------------------------------------------------------
# Rule metadata (severity / source / manual_ref from the manifest)
# ---------------------------------------------------------------------------
_FATAL_ERROR_META = rule_meta(RULE_LOG_FATAL_ERROR) or {}
_FATAL_ERROR_MANUAL = _FATAL_ERROR_META.get(
    "manual_ref",
    "https://manual.gromacs.org/current/user-guide/run-time-errors.html",
)
_FATAL_ERROR_CONFIDENCE = float(_FATAL_ERROR_META.get("confidence", 0.95))

_LINCS_INSTABILITY_META = rule_meta(RULE_LOG_LINCS_INSTABILITY) or {}
_LINCS_INSTABILITY_MANUAL = _LINCS_INSTABILITY_META.get(
    "manual_ref",
    "https://manual.gromacs.org/current/user-guide/run-time-errors.html",
)
_LINCS_INSTABILITY_CONFIDENCE = float(
    _LINCS_INSTABILITY_META.get("confidence", 0.95)
)

_SETTLE_SHAKE_META = rule_meta(RULE_LOG_SETTLE_SHAKE_FAILURE) or {}
_SETTLE_SHAKE_MANUAL = _SETTLE_SHAKE_META.get(
    "manual_ref",
    "https://manual.gromacs.org/current/user-guide/run-time-errors.html",
)
_SETTLE_SHAKE_CONFIDENCE = float(_SETTLE_SHAKE_META.get("confidence", 0.95))

# ---------------------------------------------------------------------------
# Log patterns
# ---------------------------------------------------------------------------

# GROMACS fatal error line: "Fatal error:" followed by an error description.
# "GROMACS reminds you:" is a citation reminder, NOT a fatal error.
_FATAL_ERROR_RE = re.compile(
    r"^\s*Fatal\s+error\s*:", re.IGNORECASE
)

# LINCS warning: "LINCS warning" or step-related LINCS instability messages.
# GROMACS emits messages like:
#   "Step 12345, time 24.69 (ps)  LINCS warning"
#   "relative constraint deviation after restraining:"
_LINCS_INSTABILITY_RE = re.compile(
    r"^\s*(?:Step\s+\d+.*LINCS\s+warning|LINCS\s+warning)", re.IGNORECASE
)

# SETTLE/SHAKE failure: "SETTLE error" or "SHAKE error" or
#   "The shake constraint in molecule with atom X Y is not converged"
_SETTLE_SHAKE_RE = re.compile(
    r"^\s*(?:SETTLE\s+error|SHAKE\s+error|.*shake\s+constraint.*not\s+converged)",
    re.IGNORECASE,
)

# Section header for context: GROMACS logs use "Back Off!" lines for restart
# info and blank lines as section separators.  We look for time-step markers
# to associate diagnostics with approximate log locations.
_STEP_RE = re.compile(r"^\s*Step\s+(\d+)")

# Maximum number of diagnostics per rule type to avoid log spam.
_MAX_PER_RULE = 20


def parse_log(path: Path) -> list[Diagnostic]:
    """Parse a GROMACS ``.log`` file and return diagnostics for known errors."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [
            Diagnostic(
                code="GMX400",
                severity="error",
                message="could not read log file",
                file=str(path),
                line=1,
                rule_id=None,
                confidence=1.0,
            )
        ]

    diagnostics: list[Diagnostic] = []
    fatal_count = 0
    lincs_count = 0
    settle_shake_count = 0

    for line_no, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        if _FATAL_ERROR_RE.search(line) and fatal_count < _MAX_PER_RULE:
            diagnostics.append(
                Diagnostic(
                    code="GMX401",
                    severity="error",
                    message=f"GROMACS fatal error: {line.strip()[:120]}",
                    file=str(path),
                    line=line_no,
                    suggested_fix={"kind": "review_log", "hint": "check_gromacs_fatal_error"},
                    confidence=_FATAL_ERROR_CONFIDENCE,
                    rule_id=RULE_LOG_FATAL_ERROR,
                    manual_ref=_FATAL_ERROR_MANUAL,
                    category="preflight/runtime-risk",
                )
            )
            fatal_count += 1

        if _LINCS_INSTABILITY_RE.search(line) and lincs_count < _MAX_PER_RULE:
            diagnostics.append(
                Diagnostic(
                    code="GMX402",
                    severity="error",
                    message=f"LINCS instability detected: {line.strip()[:120]}",
                    file=str(path),
                    line=line_no,
                    suggested_fix={
                        "kind": "check_lincs",
                        "hint": "reduce_timestep_or_check_constraints",
                    },
                    confidence=_LINCS_INSTABILITY_CONFIDENCE,
                    rule_id=RULE_LOG_LINCS_INSTABILITY,
                    manual_ref=_LINCS_INSTABILITY_MANUAL,
                    category="preflight/runtime-risk",
                )
            )
            lincs_count += 1

        if _SETTLE_SHAKE_RE.search(line) and settle_shake_count < _MAX_PER_RULE:
            diagnostics.append(
                Diagnostic(
                    code="GMX403",
                    severity="error",
                    message=f"SETTLE/SHAKE constraint failure: {line.strip()[:120]}",
                    file=str(path),
                    line=line_no,
                    suggested_fix={
                        "kind": "check_shake",
                        "hint": "check_constraint_settings_or_reduce_timestep",
                    },
                    confidence=_SETTLE_SHAKE_CONFIDENCE,
                    rule_id=RULE_LOG_SETTLE_SHAKE_FAILURE,
                    manual_ref=_SETTLE_SHAKE_MANUAL,
                    category="preflight/runtime-risk",
                )
            )
            settle_shake_count += 1

    return [_enrich_log_provenance(diag) for diag in diagnostics]


def _enrich_log_provenance(diag: Diagnostic) -> Diagnostic:
    """Attach manifest-backed source_provenance to log diagnostics."""
    if diag.source_provenance is not None or not diag.rule_id:
        return diag
    # Imported here to avoid a circular import at module load time.
    from .rules import diagnostic_provenance

    prov = diagnostic_provenance(diag.rule_id)
    if prov is None:
        return diag
    return Diagnostic(
        code=diag.code,
        severity=diag.severity,
        message=diag.message,
        file=diag.file,
        line=diag.line,
        column=diag.column,
        evidence=diag.evidence,
        suggested_fix=diag.suggested_fix,
        confidence=diag.confidence,
        rule_id=diag.rule_id,
        manual_ref=diag.manual_ref,
        category=diag.category,
        source_provenance=prov,
    )
