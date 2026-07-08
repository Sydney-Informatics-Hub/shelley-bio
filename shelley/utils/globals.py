from pathlib import Path

CVMFS_GALAXY_SINGULARITY_PATH='/cvmfs/singularity.galaxyproject.org/all'
LMOD_MODULES_PATH="/apps/Modules/modulefiles"
LOCAL_REGISTRY="/apps/local"
SHPC_BASE="/apps/shpc"

# Environment (Lmod) modules loaded before a build so shpc and singularity are on
# PATH. Loaded only on the build path (see shelley.utils.modules.load_build_modules).
BUILD_MODULES=("shpc", "singularity")

# Path to the bundled data directory (shelley/data/)
DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
