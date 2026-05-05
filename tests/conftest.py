from pathlib import Path
import pytest

CVMFS_PATH = Path("/cvmfs/singularity.galaxyproject.org/all")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "cvmfs: requires a live CVMFS mount"
    )


@pytest.fixture(autouse=True)
def _skip_without_cvmfs(request):
    if request.node.get_closest_marker("cvmfs") and not CVMFS_PATH.exists():
        pytest.skip("CVMFS not mounted")
