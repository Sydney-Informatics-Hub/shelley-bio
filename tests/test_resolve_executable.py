"""Tests for locating the `shelley` launcher when re-invoking under sudo.

Regression guard for the bug where the launcher path was derived from
__file__ (assuming a `bin/shelley` sibling of the package). That assumption
is false under a `uv tool install` layout, where the launcher lives in
.../uv/tools/shelley/bin/ while the package lives in .../site-packages/shelley/.
The fix resolves the launcher via PATH instead.
"""

import os

from shelley.commands.build import resolve_shelley_executable


def _make_executable(path):
    path.write_text("#!/bin/sh\nexit 0\n")
    path.chmod(0o755)


def test_finds_launcher_on_path(tmp_path, monkeypatch):
    """When a `shelley` executable is on PATH, it is returned as-is."""
    launcher = tmp_path / "shelley"
    _make_executable(launcher)
    monkeypatch.setenv("PATH", str(tmp_path))

    assert resolve_shelley_executable() == str(launcher)


def test_returns_none_when_absent(tmp_path, monkeypatch):
    """With no `shelley` anywhere on PATH, resolution fails cleanly (None)."""
    empty = tmp_path / "empty_bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))

    assert resolve_shelley_executable() is None


def test_path_independent_of_package_location(tmp_path, monkeypatch):
    """The launcher is found via PATH even though it is nowhere near the package.

    This mirrors the uv-tool layout that broke the old __file__-derived logic:
    the launcher sits in an isolated bin/ dir unrelated to site-packages.
    """
    tool_bin = tmp_path / "uv" / "tools" / "shelley" / "bin"
    tool_bin.mkdir(parents=True)
    launcher = tool_bin / "shelley"
    _make_executable(launcher)
    monkeypatch.setenv("PATH", os.pathsep.join([str(tool_bin), "/usr/bin"]))

    assert resolve_shelley_executable() == str(launcher)
