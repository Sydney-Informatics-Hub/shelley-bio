"""Tests for verbosity flag parsing and the -vv build/path helper."""

from unittest.mock import patch

from shelley.utils.args import parse_build_flags, parse_verbosity
from shelley.utils.cache import compute_build_entries


# ---------------------------------------------------------------------------
# parse_verbosity
# ---------------------------------------------------------------------------

def test_no_flags():
    assert parse_verbosity(["samtools"]) == (0, ["samtools"])


def test_single_short_flag():
    assert parse_verbosity(["samtools", "-v"]) == (1, ["samtools"])


def test_long_flag():
    assert parse_verbosity(["--verbose", "samtools"]) == (1, ["samtools"])


def test_double_short_flag():
    assert parse_verbosity(["-vv", "samtools"]) == (2, ["samtools"])


def test_stacked_short_flags():
    assert parse_verbosity(["-v", "samtools", "-v"]) == (2, ["samtools"])


# ---------------------------------------------------------------------------
# parse_build_flags
# ---------------------------------------------------------------------------

def test_build_flags_none():
    assert parse_build_flags(["samtools/1.21"]) == (False, ["samtools/1.21"])


def test_build_flags_edit_aliases():
    assert parse_build_flags(["samtools/1.21", "--edit-aliases"]) == (True, ["samtools/1.21"])


def test_build_flags_edit_aliases_before_positional():
    assert parse_build_flags(["--edit-aliases", "samtools/1.21"]) == (True, ["samtools/1.21"])


def test_stacked_long_flags():
    assert parse_verbosity(["--verbose", "--verbose", "x"]) == (2, ["x"])


# ---------------------------------------------------------------------------
# compute_build_entries — one row per build, keeps paths, no dedup
# ---------------------------------------------------------------------------

def test_build_entries_keep_every_build_and_path():
    pairs = [
        ("1.21--h50ea8bc_0", "/cvmfs/.../samtools:1.21--h50ea8bc_0"),
        ("1.21--h96c455f_1", "/cvmfs/.../samtools:1.21--h96c455f_1"),
        ("1.20--h50ea8bc_0", "/cvmfs/.../samtools:1.20--h50ea8bc_0"),
    ]
    with patch("shelley.utils.cache.get_registry_tags", return_value=["1.21--abc"]):
        entries = compute_build_entries("samtools", pairs)

    # No deduplication: every (tag, path) is preserved.
    assert [e["tag"] for e in entries] == [
        "1.21--h50ea8bc_0", "1.21--h96c455f_1", "1.20--h50ea8bc_0",
    ]
    assert [e["path"] for e in entries] == [p for _, p in pairs]
    # Buildable is keyed on the short tag: 1.21 is in the registry, 1.20 is not.
    assert [e["buildable"] for e in entries] == [True, True, False]


def test_build_entries_registry_failure_marks_unbuildable():
    pairs = [("1.21--h50ea8bc_0", "/cvmfs/.../samtools:1.21--h50ea8bc_0")]
    with patch("shelley.utils.cache.get_registry_tags", side_effect=RuntimeError):
        entries = compute_build_entries("samtools", pairs)
    assert entries[0]["buildable"] is False
