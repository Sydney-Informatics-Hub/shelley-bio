from pathlib import Path

CVMFS_GALAXY_SINGULARITY_PATH='/cvmfs/singularity.galaxyproject.org/all'
LMOD_MODULES_PATH="/apps/Modules/modulefiles"
LOCAL_REGISTRY="/apps/local"
SHPC_BASE="/apps/shpc"

# Path to the bundled data directory (shelley_bio/data/)
DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
