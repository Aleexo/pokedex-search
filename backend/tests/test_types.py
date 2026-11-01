"""Runs mypy as part of the test suite, so type errors fail `uv run pytest`.

Main reason: `EntityRef(kind, id, name)` must receive a `Kind`, never a plain string.
"""

from pathlib import Path

from mypy import api

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_mypy_passes(monkeypatch):
    """The whole backend type-checks, e.g. no plain string passed where a Kind is expected."""
    monkeypatch.chdir(BACKEND_DIR)  # mypy reads [tool.mypy] from pyproject.toml here
    stdout, stderr, status = api.run([])
    assert status == 0, stdout + stderr
