"""
Tests for RsecSource.

RSEC entries use plain string lists for EDAM fields (already flattened during
ingestion), so sample entries mirror that format.

load() tests write a minimal gzipped JSON to tmp_path — no mocking needed.
All other tests inject entries directly via source.entries = [...].
"""

import gzip
import json
from pathlib import Path

import pytest

from shelley_bio.search.rsec import RsecSource, RSEC_DATA_PATH


# Plain string list format — matches what rsec_meta.json.gz actually contains
ENTRIES = [
    {
        "id": "fastqc",
        "name": "FastQC",
        "description": "Quality control for sequencing data",
        "edam-operations": ["Sequencing quality control"],
        "edam-topics": ["Sequencing"],
        "edam-inputs": [],
        "edam-outputs": [],
    },
    {
        "id": "bwa",
        "name": "BWA",
        "description": "Burrows-Wheeler Aligner for read mapping",
        "edam-operations": ["Read mapping", "Sequence alignment"],
        "edam-topics": ["Mapping"],
        "edam-inputs": [],
        "edam-outputs": [],
    },
]


@pytest.fixture
def tiny_artifact(tmp_path) -> Path:
    """Write a minimal rsec_meta.json.gz to tmp_path and return its path."""
    doc = {"entries": ENTRIES, "entry_count": len(ENTRIES)}
    path = tmp_path / "rsec_meta.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(doc, f)
    return path


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def test_name():
    assert RsecSource.name == "rsec"


def test_default_data_path():
    assert RsecSource().data_path == RSEC_DATA_PATH


def test_custom_data_path(tmp_path):
    p = tmp_path / "custom.json.gz"
    assert RsecSource(data_path=p).data_path == p


# ---------------------------------------------------------------------------
# load()
# ---------------------------------------------------------------------------

def test_load_populates_entries(tiny_artifact):
    source = RsecSource(data_path=tiny_artifact).load()
    assert len(source) == len(ENTRIES)


def test_load_returns_self(tiny_artifact):
    source = RsecSource(data_path=tiny_artifact)
    assert source.load() is source


def test_load_entries_have_expected_keys(tiny_artifact):
    source = RsecSource(data_path=tiny_artifact).load()
    assert source.entries[0]["id"] == "fastqc"
    assert source.entries[0]["name"] == "FastQC"


# ---------------------------------------------------------------------------
# __len__ with injected entries
# ---------------------------------------------------------------------------

def test_len_after_injection():
    source = RsecSource()
    source.entries = ENTRIES
    assert len(source) == 2


def test_len_empty():
    assert len(RsecSource()) == 0


# ---------------------------------------------------------------------------
# search() — stub
# ---------------------------------------------------------------------------

def test_search_is_stub():
    source = RsecSource()
    source.entries = ENTRIES
    # search() is a placeholder; the body is pass, so it returns None
    assert source.search("quality") is None


def test_search_stub_does_not_raise():
    source = RsecSource()
    source.entries = ENTRIES
    source.search("variant calling", limit=5)  # must not raise
