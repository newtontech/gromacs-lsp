from __future__ import annotations

from pathlib import Path

from gromacs_lsp.analyzer import analyze_path, format_text


def test_mdp_fixture_has_no_errors(tmp_path: Path) -> None:
    (tmp_path / "md.mdp").write_text(
        "integrator = md\nnsteps = 1000\ndt = 0.002\n", encoding="utf-8"
    )

    diagnostics = analyze_path(tmp_path)

    assert not [item for item in diagnostics if item.severity == "error"]


def test_gro_atom_count_error(tmp_path: Path) -> None:
    (tmp_path / "bad.gro").write_text(
        "title\n2\n    1SOL     OW    1   0.0   0.0   0.0\n0.1 0.1 0.1\n",
        encoding="utf-8",
    )

    diagnostics = analyze_path(tmp_path)

    assert any(item.code == "GMX032" for item in diagnostics)


def test_formatter_is_idempotent() -> None:
    first = format_text("integrator=md\nnsteps=1000\n")

    assert format_text(first) == first
