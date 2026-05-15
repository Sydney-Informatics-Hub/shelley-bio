import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from container_guts.main import ManifestGenerator

_SUPPLEMENTARY_DB = Path(__file__).parent.parent / "data" / "guts_db"


def _merge_supplementary_db(tmpdir: str) -> None:
    """Copy bundled extra manifests (e.g. miniconda3) into the guts tmpdir."""
    if _SUPPLEMENTARY_DB.exists():
        shutil.copytree(str(_SUPPLEMENTARY_DB), tmpdir, dirs_exist_ok=True)


def _sparse_clone_base_manifests(db_url: str, namespaces: list[str]) -> str:
    """
    Shallow sparse-clone only the base OS image directories from db_url.
    Returns the tmpdir path; caller is responsible for cleanup.

    dbs = shpc guts have general json manifests to diff against
    """
    tmpdir = tempfile.mkdtemp(prefix="shelley-guts-")
    subprocess.run(
        ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", db_url, tmpdir],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", tmpdir, "sparse-checkout", "set"] + namespaces,
        check=True, capture_output=True,
    )
    return tmpdir


SHPC_GUTS_DB_URL = "https://github.com/singularityhub/shpc-guts"
BASE_IMAGE_NAMESPACES = [
    "docker.io/library/ubuntu",
    "docker.io/library/alpine",
    "docker.io/library/busybox",
    "docker.io/library/rockylinux",
]


def extract_aliases(cvmfs_path: str) -> list[dict]:
    """
    Use guts to find executables unique to this container vs base OS images.

    Sparse-clones only ubuntu/alpine/busybox/rockylinux manifests from the
    shpc-guts database (no image pulling; CVMFS SIF must already be on disk).
    Returns shpc alias dicts: [{"name": "bwa", "command": "bwa"}, ...].
    Returns [] silently if guts is unavailable or analysis fails.

    Replicates https://github.com/singularityhub/guts/blob/main/.github/workflows/generate.yaml#L64 
    """
    tmpdir = None
    try:
        tmpdir = _sparse_clone_base_manifests(SHPC_GUTS_DB_URL, BASE_IMAGE_NAMESPACES)
        _merge_supplementary_db(tmpdir)
        # Use the Sydney-Informatics-Hub/guts implementation for singularity support
        gen = ManifestGenerator(tech="singularity")
        result = gen.diff(cvmfs_path, database=tmpdir)
        if not result:
            return []
        diff_data = next(iter(result.values()), {}).get("diff", {})
        unique_paths = sorted(diff_data.get("unique_paths", []))
        bin_re = re.compile(r"/(s?bin)/")
        return [
            {"name": os.path.basename(p), "command": os.path.basename(p)}
            for p in unique_paths
            if bin_re.search(p) and os.path.basename(p)
        ]
    except (Exception, SystemExit):
        return []
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
