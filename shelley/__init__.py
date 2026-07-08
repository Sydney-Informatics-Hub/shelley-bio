"""
Shelley - A bioinformatics tool finder and module builder

This package provides tools for finding, querying, and building modules for
bioinformatics software from CVMFS repositories.
"""

__version__ = "0.2.0-dev"

from .client.cli import main as cli_main
from .builder.cvmfs_builder import CVMFSModuleBuilder

__all__ = ["cli_main", "CVMFSModuleBuilder"]