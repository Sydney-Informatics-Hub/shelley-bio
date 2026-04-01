#!/usr/bin/env python3
"""Template pytest coverage for CVMFS version selection."""

import sys
from pathlib import Path
from unittest.mock import patch

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
    # Both of these versions have multiple builds; interactive selection should be triggered.
    # Mock questionary so the test runs headlessly.
    with patch("shelley_bio.builder.cvmfs_builder.questionary") as mock_q:
        available = builder._get_available_tools(tool_name)
        matches = [
            (t, v) for t, v in available
            if v == tool_version or v.split("--", 1)[0] == tool_version
        ]
        assert len(matches) > 1, "Precondition: test requires multiple builds"
        first_match = matches[0]
        mock_q.select.return_value.ask.return_value = first_match

        result = builder.search_tool_version(tool_name, tool_version)

        mock_q.select.assert_called_once()
        assert result[0] == tool_name
        assert result[1].split("--", 1)[0] == tool_version

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
    [('samtools', None, '1.23.1--ha83d96e_0'), ('plink2', None, '2.00a5.12--h4ac6f70_0')]
)
def test_search_tool_version_none(builder, tool_name, tool_version, latest_version):
    # When no version is provided, build the latest version
    exp = (tool_name, latest_version)
    get = builder.search_tool_version(tool_name, tool_version)
    assert get == exp