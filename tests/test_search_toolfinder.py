"""
Tests for ToolfinderSource.

Toolfinder entries use nested dicts for EDAM fields — e.g.
[{"term": "Read mapping", "formats": ["SAM"]}] — unlike RSEC which uses
plain string lists. Sample entries here mirror that actual format to ensure
the data contract is correct for this source.

load() tests write a minimal YAML to tmp_path — no mocking needed.
All other tests inject entries directly via source.entries = [...].
"""

from pathlib import Path

import pytest
import yaml

from shelley_bio.search.toolfinder import ToolfinderSource, TOOLFINDER_DATA_PATH


# Nested dict format — matches what toolfinder_meta.yaml actually contains
ENTRIES = [
    {
        "id": "fastqc",
        "name": "FastQC",
        "description": "Quality control for sequencing data",
        "edam-operations": [{"term": "Sequencing quality control", "formats": []}],
        "edam-topics": [{"term": "Sequencing"}],
    },
    {
        "id": "samtools",
        "name": "SAMtools",
        "description": "Tools for manipulating SAM/BAM alignment files",
        "edam-operations": [
            {"term": "Sequence alignment", "formats": ["SAM", "BAM"]}
        ],
        "edam-topics": [{"term": "Mapping"}],
    },
]


@pytest.fixture
def tiny_yaml(tmp_path) -> Path:
    """Write a minimal toolfinder_meta.yaml to tmp_path and return its path."""
    path = tmp_path / "toolfinder_meta.yaml"
    path.write_text(yaml.dump(ENTRIES), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def test_name():
    assert ToolfinderSource.name == "toolfinder"


def test_default_data_path():
    assert ToolfinderSource().data_path == TOOLFINDER_DATA_PATH


def test_custom_data_path(tmp_path):
    p = tmp_path / "custom.yaml"
    assert ToolfinderSource(data_path=p).data_path == p


# ---------------------------------------------------------------------------
# load()
# ---------------------------------------------------------------------------

def test_load_populates_entries(tiny_yaml):
    source = ToolfinderSource(data_path=tiny_yaml).load()
    assert len(source) == len(ENTRIES)


def test_load_returns_self(tiny_yaml):
    source = ToolfinderSource(data_path=tiny_yaml)
    assert source.load() is source


def test_load_entries_have_expected_keys(tiny_yaml):
    source = ToolfinderSource(data_path=tiny_yaml).load()
    assert source.entries[0]["id"] == "fastqc"
    assert source.entries[0]["name"] == "FastQC"


# ---------------------------------------------------------------------------
# __len__ with injected entries
# ---------------------------------------------------------------------------

def test_len_after_injection():
    source = ToolfinderSource()
    source.entries = ENTRIES
    assert len(source) == 2


def test_len_empty():
    assert len(ToolfinderSource()) == 0


# ---------------------------------------------------------------------------
# search() — stub
# ---------------------------------------------------------------------------

def test_search_is_stub():
    source = ToolfinderSource()
    source.entries = ENTRIES
    # search() is a placeholder; the body is pass, so it returns None
    assert source.search("quality") is None


def test_search_stub_does_not_raise():
    source = ToolfinderSource()
    source.entries = ENTRIES
    source.search("alignment", limit=3)  # must not raise
