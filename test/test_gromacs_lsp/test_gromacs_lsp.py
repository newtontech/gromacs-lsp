from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from gromacs_lsp.analyzer import (
    KNOWN_MDP_KEYS,
    analyze_file,
    analyze_path,
    format_text,
)
from gromacs_lsp.completion import mdp_completions, topology_completions
from gromacs_lsp.diagnostics import Diagnostic
from gromacs_lsp.hover import mdp_hover, topology_hover
from gromacs_lsp.symbols import document_symbols


# ---------------------------------------------------------------------------
# MDP: valid fixtures
# ---------------------------------------------------------------------------


def test_mdp_fixture_has_no_errors(tmp_path: Path) -> None:
    (tmp_path / "md.mdp").write_text(
        "integrator = md\nnsteps = 1000\ndt = 0.002\n", encoding="utf-8"
    )

    diagnostics = analyze_path(tmp_path)

    assert not [item for item in diagnostics if item.severity == "error"]


def test_mdp_complete_valid_file(tmp_path: Path) -> None:
    """A well-formed MDP with all required keys should produce zero diagnostics."""
    content = textwrap.dedent("""\
        integrator  = md
        nsteps      = 50000
        dt          = 0.002
        coulombtype = PME
        rcoulomb    = 1.0
        rvdw        = 1.0
        pbc         = xyz
        constraints = all-bonds
    """)
    p = tmp_path / "min.mdp"
    p.write_text(content, encoding="utf-8")

    diags = analyze_file(p)

    assert diags == []


def test_mdp_missing_required_key(tmp_path: Path) -> None:
    """Missing required MDP keys should produce GMX101 diagnostics."""
    content = "coulombtype = PME\n"
    p = tmp_path / "bad.mdp"
    p.write_text(content, encoding="utf-8")

    diags = analyze_file(p)

    codes = {d.code for d in diags}
    assert "GMX101" in codes
    missing_keys = {d.message.split("'")[1] for d in diags if d.code == "GMX101"}
    assert "integrator" in missing_keys
    assert "nsteps" in missing_keys
    assert "dt" in missing_keys


def test_mdp_unknown_key(tmp_path: Path) -> None:
    """Unknown MDP key should produce GMX002."""
    p = tmp_path / "unk.mdp"
    p.write_text("integrator = md\nnsteps = 100\ndt = 0.002\nfoobar = yes\n", encoding="utf-8")

    diags = analyze_file(p)
    codes = [d.code for d in diags]
    assert "GMX002" in codes


def test_mdp_line_without_equals(tmp_path: Path) -> None:
    """Non-comment, non-blank line without = should produce GMX001."""
    p = tmp_path / "weird.mdp"
    p.write_text("integrator = md\nnsteps = 100\ndt = 0.002\nthis is not a setting\n", encoding="utf-8")

    diags = analyze_file(p)
    assert any(d.code == "GMX001" for d in diags)


def test_mdp_duplicate_key(tmp_path: Path) -> None:
    """Duplicate MDP key should produce GMX003."""
    p = tmp_path / "dup.mdp"
    p.write_text("integrator = md\nnsteps = 100\ndt = 0.002\nnsteps = 200\n", encoding="utf-8")

    diags = analyze_file(p)
    assert any(d.code == "GMX003" for d in diags)


def test_mdp_value_validation_error(tmp_path: Path) -> None:
    """Invalid value for a validated MDP key should produce GMX004."""
    p = tmp_path / "badval.mdp"
    p.write_text("integrator = blah\nnsteps = 100\ndt = 0.002\n", encoding="utf-8")

    diags = analyze_file(p)
    assert any(d.code == "GMX004" for d in diags)


def test_mdp_nsteps_negative(tmp_path: Path) -> None:
    """Negative nsteps should produce GMX004."""
    p = tmp_path / "neg.mdp"
    p.write_text("integrator = md\nnsteps = -1\ndt = 0.002\n", encoding="utf-8")

    diags = analyze_file(p)
    assert any(d.code == "GMX004" for d in diags)


def test_mdp_comments_and_blank_lines_ignored(tmp_path: Path) -> None:
    """Comments and blank lines should not produce diagnostics."""
    content = textwrap.dedent("""\
        ; This is a comment
        # This is a preprocessor directive

        integrator = md
        nsteps = 1000
        dt = 0.002
    """)
    p = tmp_path / "comments.mdp"
    p.write_text(content, encoding="utf-8")

    diags = analyze_file(p)
    assert diags == []


# ---------------------------------------------------------------------------
# Topology (.top/.itp) diagnostics
# ---------------------------------------------------------------------------


def test_topology_valid(tmp_path: Path) -> None:
    """A valid minimal topology should produce no diagnostics."""
    content = textwrap.dedent("""\
        [ moleculetype ]
        ; name  nrexcl
        Urea         3

        [ atoms ]
           1  C  1  URE      C      1     0.880  12.01
    """)
    p = tmp_path / "urea.top"
    p.write_text(content, encoding="utf-8")

    diags = analyze_file(p)
    assert diags == []


def test_topology_missing_moleculetype(tmp_path: Path) -> None:
    """Topology without [ moleculetype ] should produce GMX110."""
    content = textwrap.dedent("""\
        [ atoms ]
           1  C  1  URE      C      1     0.880  12.01
    """)
    p = tmp_path / "bad.top"
    p.write_text(content, encoding="utf-8")

    diags = analyze_file(p)
    assert any(d.code == "GMX110" for d in diags)


def test_topology_missing_atoms(tmp_path: Path) -> None:
    """Topology without [ atoms ] should produce GMX110."""
    content = textwrap.dedent("""\
        [ moleculetype ]
        Urea  3
    """)
    p = tmp_path / "noatoms.top"
    p.write_text(content, encoding="utf-8")

    diags = analyze_file(p)
    assert any(d.code == "GMX110" for d in diags)


def test_topology_include_no_quotes(tmp_path: Path) -> None:
    """#include without quotes or brackets should produce GMX020."""
    content = textwrap.dedent("""\
        #include forcefield.itp
        [ moleculetype ]
        Urea  3
        [ atoms ]
           1  C  1  URE      C      1     0.880  12.01
    """)
    p = tmp_path / "inc.top"
    p.write_text(content, encoding="utf-8")

    diags = analyze_file(p)
    assert any(d.code == "GMX020" for d in diags)


def test_topology_include_with_quotes_ok(tmp_path: Path) -> None:
    """#include with quotes should not produce GMX020."""
    content = textwrap.dedent("""\
        #include "forcefield.itp"
        [ moleculetype ]
        Urea  3
        [ atoms ]
           1  C  1  URE      C      1     0.880  12.01
    """)
    p = tmp_path / "incok.top"
    p.write_text(content, encoding="utf-8")

    diags = analyze_file(p)
    assert not any(d.code == "GMX020" for d in diags)


def test_topology_unknown_section(tmp_path: Path) -> None:
    """Unknown section name should produce GMX021."""
    content = textwrap.dedent("""\
        [ moleculetype ]
        Urea  3
        [ atoms ]
           1  C  1  URE      C      1     0.880  12.01
        [ bogus_section ]
           foo bar
    """)
    p = tmp_path / "unk.top"
    p.write_text(content, encoding="utf-8")

    diags = analyze_file(p)
    assert any(d.code == "GMX021" for d in diags)


def test_topology_itp_treated_same_as_top(tmp_path: Path) -> None:
    """ITP files should be analyzed with the same topology logic."""
    content = textwrap.dedent("""\
        [ moleculetype ]
        SOL  2
        [ atoms ]
           1  OW  1  SOL  OW  1  -0.834  16.0
    """)
    p = tmp_path / "water.itp"
    p.write_text(content, encoding="utf-8")

    diags = analyze_file(p)
    assert diags == []


# ---------------------------------------------------------------------------
# GRO diagnostics
# ---------------------------------------------------------------------------


def test_gro_atom_count_error(tmp_path: Path) -> None:
    (tmp_path / "bad.gro").write_text(
        "title\n2\n    1SOL     OW    1   0.0   0.0   0.0\n0.1 0.1 0.1\n",
        encoding="utf-8",
    )

    diagnostics = analyze_path(tmp_path)

    assert any(item.code == "GMX032" for item in diagnostics)


def test_gro_valid(tmp_path: Path) -> None:
    """Valid minimal GRO file should produce no diagnostics."""
    content = textwrap.dedent("""\
        water
        1
            1SOL     OW    1   0.000   0.000   0.000
        0.0 0.0 0.0
    """)
    p = tmp_path / "water.gro"
    p.write_text(content, encoding="utf-8")

    diags = analyze_file(p)
    assert diags == []


def test_gro_too_short(tmp_path: Path) -> None:
    """GRO file with < 3 lines should produce GMX030."""
    p = tmp_path / "short.gro"
    p.write_text("title\n1\n", encoding="utf-8")

    diags = analyze_file(p)
    assert any(d.code == "GMX030" for d in diags)


def test_gro_bad_atom_count(tmp_path: Path) -> None:
    """GRO file with non-integer atom count line should produce GMX031."""
    p = tmp_path / "badcnt.gro"
    p.write_text("title\nabc\n   1SOL OW 1 0 0 0\n0 0 0\n", encoding="utf-8")

    diags = analyze_file(p)
    assert any(d.code == "GMX031" for d in diags)


def test_gro_unicode_error(tmp_path: Path) -> None:
    """Non-UTF-8 file should produce GMX202."""
    p = tmp_path / "bad.gro"
    p.write_bytes(b"\xff\xfe\x00\x00")

    diags = analyze_file(p)
    assert any(d.code == "GMX202" for d in diags)


# ---------------------------------------------------------------------------
# analyze_path (directory-level)
# ---------------------------------------------------------------------------


def test_analyze_path_no_files(tmp_path: Path) -> None:
    """Directory with no supported files should produce GMX201."""
    diags = analyze_path(tmp_path)
    assert any(d.code == "GMX201" for d in diags)


def test_analyze_path_multiple_files(tmp_path: Path) -> None:
    """analyze_path should find diagnostics across multiple files."""
    (tmp_path / "a.mdp").write_text("foobar = yes\n", encoding="utf-8")
    (tmp_path / "b.top").write_text("; empty\n", encoding="utf-8")

    diags = analyze_path(tmp_path)
    files = {d.file for d in diags}
    assert len(files) >= 2


def test_analyze_path_single_file(tmp_path: Path) -> None:
    """analyze_path with a single file should analyze that file only."""
    p = tmp_path / "ok.mdp"
    p.write_text("integrator = md\nnsteps = 100\ndt = 0.002\n", encoding="utf-8")

    diags = analyze_path(p)
    assert diags == []


# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------


def test_formatter_is_idempotent() -> None:
    first = format_text("integrator=md\nnsteps=1000\n")

    assert format_text(first) == first


def test_formatter_aligns_equals() -> None:
    """Formatter should left-align keys and align = signs."""
    result = format_text("integrator=md\nnsteps=1000\n")
    lines = result.strip().splitlines()
    for line in lines:
        assert "= " in line  # space after =


def test_formatter_preserves_comments() -> None:
    """Comment lines should be preserved as-is (just rstripped)."""
    result = format_text("; This is a comment\nintegrator = md\nnsteps = 1000\ndt = 0.002\n")
    assert "; This is a comment" in result


def test_formatter_preserves_preprocessor() -> None:
    """Preprocessor lines should be preserved as-is."""
    result = format_text("#include \"something.itp\"\nintegrator = md\nnsteps = 1000\ndt = 0.002\n")
    assert '#include "something.itp"' in result


def test_formatter_trailing_newline() -> None:
    """Formatted output should end with exactly one newline."""
    result = format_text("integrator = md\nnsteps = 1000\ndt = 0.002")
    assert result.endswith("\n")
    assert not result.endswith("\n\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_lint_mdp(tmp_path: Path) -> None:
    """gromacs-lint should return 0 on clean files."""
    from gromacs_lsp.cli import lint_main

    p = tmp_path / "ok.mdp"
    p.write_text("integrator = md\nnsteps = 100\ndt = 0.002\n", encoding="utf-8")

    rc = lint_main([str(p)])
    assert rc == 0


def test_cli_lint_error_returns_1(tmp_path: Path) -> None:
    """gromacs-lint should return 1 on files with errors."""
    from gromacs_lsp.cli import lint_main

    p = tmp_path / "bad.gro"
    p.write_text("title\n2\n   1SOL OW 1 0 0 0\n0 0 0\n", encoding="utf-8")

    rc = lint_main([str(p)])
    assert rc == 1


def test_cli_lint_json(tmp_path: Path) -> None:
    """gromacs-lint --json should produce valid JSON."""
    from gromacs_lsp.cli import lint_main
    import io
    import sys

    p = tmp_path / "bad.mdp"
    p.write_text("foobar = yes\n", encoding="utf-8")

    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    try:
        lint_main([str(p), "--json"])
    finally:
        sys.stdout = old_stdout

    output = buf.getvalue()
    data = json.loads(output)
    assert isinstance(data, list)


def test_cli_fmt_write(tmp_path: Path) -> None:
    """gromacs-fmt -w should write formatted content back to file."""
    from gromacs_lsp.cli import fmt_main

    p = tmp_path / "fmt.mdp"
    p.write_text("integrator=md\nnsteps=1000\n", encoding="utf-8")

    fmt_main(["-w", str(p)])

    result = p.read_text(encoding="utf-8")
    assert "= md" in result


def test_cli_lsp_main() -> None:
    """gromacs-lsp --stdio should return 0."""
    from gromacs_lsp.cli import lsp_main

    rc = lsp_main(["--stdio"])
    assert rc == 0


# ---------------------------------------------------------------------------
# Hover
# ---------------------------------------------------------------------------


def test_mdp_hover_known_key() -> None:
    """Hover on a known MDP key should return documentation."""
    info = mdp_hover("integrator")
    assert info is not None
    assert "md" in info or "integrator" in info.lower()


def test_mdp_hover_unknown_key() -> None:
    """Hover on unknown key should return None or a helpful message."""
    info = mdp_hover("foobar_baz")
    assert info is None or "unknown" in info.lower()


def test_mdp_hover_case_insensitive() -> None:
    """Hover should be case-insensitive."""
    info = mdp_hover("Integrator")
    assert info is not None


def test_topology_hover_section() -> None:
    """Hover on a known topology section should return docs."""
    info = topology_hover("atoms")
    assert info is not None
    assert "atom" in info.lower()


def test_topology_hover_subsection() -> None:
    """Hover on a subsection should return docs."""
    info = topology_hover("bonds")
    assert info is not None


def test_topology_hover_unknown() -> None:
    """Hover on unknown topology section should return None."""
    info = topology_hover("foobar")
    assert info is None


# ---------------------------------------------------------------------------
# Completion
# ---------------------------------------------------------------------------


def test_mdp_completions_include_known_keys() -> None:
    """MDP completions should include known keys."""
    items = mdp_completions()
    labels = {item["label"] for item in items}
    assert "integrator" in labels
    assert "nsteps" in labels
    assert "dt" in labels


def test_mdp_completions_have_detail() -> None:
    """Each completion item should have a detail string."""
    items = mdp_completions()
    for item in items:
        assert "label" in item
        assert "detail" in item


def test_topology_completions_include_sections() -> None:
    """Topology completions should include common sections."""
    items = topology_completions()
    labels = {item["label"] for item in items}
    assert "moleculetype" in labels
    assert "atoms" in labels
    assert "bonds" in labels


def test_topology_completions_have_detail() -> None:
    """Each topology completion item should have detail."""
    items = topology_completions()
    for item in items:
        assert "label" in item
        assert "detail" in item


# ---------------------------------------------------------------------------
# Document symbols
# ---------------------------------------------------------------------------


def test_mdp_document_symbols(tmp_path: Path) -> None:
    """MDP document symbols should list all key=value pairs."""
    content = "integrator = md\nnsteps = 1000\ndt = 0.002\n"
    p = tmp_path / "sym.mdp"
    p.write_text(content, encoding="utf-8")

    symbols = document_symbols(p)
    names = {s["name"] for s in symbols}
    assert "integrator" in names
    assert "nsteps" in names
    assert "dt" in names


def test_topology_document_symbols(tmp_path: Path) -> None:
    """Topology document symbols should list sections."""
    content = textwrap.dedent("""\
        [ moleculetype ]
        Urea  3
        [ atoms ]
           1  C  1  URE  C  1  0.880  12.01
        [ bonds ]
           1   2
    """)
    p = tmp_path / "sym.top"
    p.write_text(content, encoding="utf-8")

    symbols = document_symbols(p)
    names = {s["name"] for s in symbols}
    assert "moleculetype" in names
    assert "atoms" in names
    assert "bonds" in names


# ---------------------------------------------------------------------------
# Diagnostic dataclass
# ---------------------------------------------------------------------------


def test_diagnostic_to_json() -> None:
    """Diagnostic.to_json should produce a serializable dict."""
    d = Diagnostic("GMX001", "warning", "test message", "f.txt", 1)
    j = d.to_json()
    assert j["code"] == "GMX001"
    assert j["severity"] == "warning"
    assert j["line"] == 1


def test_diagnostic_frozen() -> None:
    """Diagnostic should be immutable."""
    d = Diagnostic("GMX001", "warning", "test", "f.txt", 1)
    with pytest.raises(AttributeError):
        d.code = "CHANGED"  # type: ignore[misc]
