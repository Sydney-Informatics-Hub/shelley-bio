#!/usr/bin/env python3
"""Template pytest coverage for CVMFS version selection."""

import sys
from pathlib import Path

import pytest

# Add the project root to Python pat
# TODO: Wrap as a package to resolve
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shelley_bio.builder.cvmfs_builder import CVMFSModuleBuilder

# TODO: Create a mock available versions
@pytest.fixture
def builder() -> CVMFSModuleBuilder:
    """Create a builder instance for unit tests."""
    return CVMFSModuleBuilder()

@pytest.mark.parametrize(
    "tool_name,tool_version", 
    [('samtools', '1.21'), ('plink2', '2.00a5.12')]
) 
def test_search_tool_version_multiplebuilds(builder, tool_name, tool_version):
    # Both of these versions have multiple builds and will throw a ValueError
    with pytest.raises(ValueError, match=r"Multiple versions found"):
        builder.search_tool_version(tool_name, tool_version)

@pytest.mark.parametrize(
    "tool_name,tool_version", 
    [('samtools', '1.21--h96c455f_1'), ('plink2', '2.00a5.12--h4ac6f70_0')]
) 
def test_search_tool_version_singlebuild(builder, tool_name, tool_version):
    # Both of these versions have only a single build
    exp = (tool_name, tool_version)
    get = builder.search_tool_version(tool_name, tool_version)
    assert get == exp

@pytest.mark.parametrize(
    "tool_name,tool_version,latest_version", 
    [('samtools', None, '1.23--h96c455f_0'), ('plink2', None, '2.00a5.12--h4ac6f70_0')]
)
def test_search_tool_version_none(builder, tool_name, tool_version, latest_version):
    # When no version is provided, build the latest version
    exp = (tool_name, latest_version)
    get = builder.search_tool_version(tool_name, tool_version)
    assert get == exp