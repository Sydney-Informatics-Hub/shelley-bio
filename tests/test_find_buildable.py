#!/usr/bin/env python3
"""
Tests for _handle_find_tool() — the MCP layer that adds buildable status.

Four categories:
  1. Smoke: all 21 user-specified args return valid JSON (no network needed).
  2. Buildable cross-check: for full-tag inputs, find's buildable field must
     match get_registry_tags() called independently (network required).
  3. Version presence: version-only args must resolve to a known container.
  4. R/Bioconductor: these packages have no Singularity containers.
"""

import json
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import shelley_bio.server.mcp_server as _mcp
from shelley_bio.server.mcp_server import BioFinderIndex, _handle_find_tool
from shelley_bio.builder.cvmfs_builder import get_registry_tags


@pytest.fixture(scope="module", autouse=True)
def _load_mcp_index():
    """Load the module-level index used by _handle_find_tool."""
    _mcp.index.load_data()


@pytest.fixture(scope="module")
def index() -> BioFinderIndex:
    """Separate index instance for tests that call search_tool() directly."""
    idx = BioFinderIndex()
    idx.load_data()
    return idx


# ---------------------------------------------------------------------------
# Category 1 — Smoke test: all inputs, no network/CVMFS required
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("arg", [
    "fastqc:0.12.1--hdfd78af_0",
    "multiqc:1.19--pyhdfd78af_0",
    "salmon:1.10.1--h7e5ed60_0",
    "bcftools",
    "bwa-mem2/2.2.1",
    "fastp/0.20.0",
    "parabricks",
    "sambamba/0.8.1",
    "samblaster/0.1.24",
    "samtools/1.19",
    "blast:2.5.0--hc0b0e79_3",
    "star/2.7.11a--h0033a41_0",
    "star-fusion:1.0.0",
    "seurat",
    "tidyverse",
    "limma",
    "edger",
    "SpatialExperiment",
    "scuttle",
    "scater",
    "R",
])
def test_find_with_versioned_arg_returns_valid_json(arg):
    """_handle_find_tool must return valid JSON with expected keys for any input."""
    payload = json.loads(_handle_find_tool(arg))
    assert "found" in payload
    assert "containers" in payload
    assert "suggestions" in payload


# ---------------------------------------------------------------------------
# Category 2 — Buildable cross-check: full-tag inputs (network required)
# ---------------------------------------------------------------------------

FULL_TAG_CASES = [
    ("fastqc:0.12.1--hdfd78af_0",  "fastqc",  "0.12.1--hdfd78af_0"),
    ("multiqc:1.19--pyhdfd78af_0", "multiqc", "1.19--pyhdfd78af_0"),
    ("salmon:1.10.1--h7e5ed60_0",  "salmon",  "1.10.1--h7e5ed60_0"),
    ("blast:2.5.0--hc0b0e79_3",    "blast",   "2.5.0--hc0b0e79_3"),
    ("star/2.7.11a--h0033a41_0",   "star",    "2.7.11a--h0033a41_0"),
]


@pytest.mark.network
@pytest.mark.parametrize("arg,tool_id,full_tag", FULL_TAG_CASES)
def test_find_buildable_matches_registry(arg, tool_id, full_tag):
    """buildable in find output must equal (full_tag in get_registry_tags())."""
    registry_tags = get_registry_tags(tool_id)
    expected_buildable = full_tag in registry_tags

    payload = json.loads(_handle_find_tool(arg))
    short_version = full_tag.split("--")[0]
    versions = (payload.get("containers") or {}).get("recent_versions", [])
    match = next((v for v in versions if v["version"] == short_version), None)

    if match is None:
        pytest.skip(f"{short_version} not in top-5 recent versions for {tool_id}")

    assert match["buildable"] == expected_buildable, (
        f"{tool_id} {full_tag}: find says buildable={match['buildable']}, "
        f"registry says {expected_buildable} "
        f"(registry_tags sample: {sorted(registry_tags)[:3]})"
    )


# ---------------------------------------------------------------------------
# Category 3 — Version presence: version-only inputs resolve to known container
# ---------------------------------------------------------------------------

VERSION_CASES = [
    ("bwa-mem2/2.2.1",    "bwa-mem2",   "2.2.1"),
    ("fastp/0.20.0",      "fastp",      "0.20.0"),
    ("sambamba/0.8.1",    "sambamba",   "0.8.1"),
    ("samblaster/0.1.24", "samblaster", "0.1.24"),
    ("samtools/1.19",     "samtools",   "1.19"),
    ("star-fusion:1.0.0", "star-fusion","1.0.0"),
]


@pytest.mark.parametrize("arg,tool_id,short_version", VERSION_CASES)
def test_find_version_present_in_containers(index, arg, tool_id, short_version):
    """Requested version must appear somewhere in the full container list."""
    result = index.search_tool(tool_id)
    all_shorts = [c["tag"].split("--")[0] for c in result["containers"]]
    assert short_version in all_shorts, (
        f"{tool_id}: version {short_version!r} not found. "
        f"Available (sample): {all_shorts[:10]}"
    )


# ---------------------------------------------------------------------------
# Category 4 — R/Bioconductor: no Singularity containers expected
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tool", [
    "seurat",
    "tidyverse",
    "limma",
    "edger",
    "SpatialExperiment",
    "scuttle",
    "scater",
])
def test_r_packages_no_containers_no_crash(tool):
    """R/Bioconductor packages are not in the Galaxy Singularity cache."""
    payload = json.loads(_handle_find_tool(tool))
    assert payload["containers"] is None or not payload["containers"].get("available"), (
        f"{tool}: unexpectedly found containers — update Category F if this is intentional"
    )
