"""
ToolfinderSource — loads and searches the toolfinder corpus.

The toolfinder artifact (toolfinder_meta.yaml) stores EDAM fields as nested
dicts: [{"term": "Read mapping", "formats": ["SAM"]}]. The inherited
_flatten_edam() method handles this format alongside RSEC's plain string lists,
so the search algorithm is the same — _flatten_edam() does the format bridging.
"""

from pathlib import Path
from typing import Optional

import yaml

from shelley_bio.utils.globals import DATA_DIR
from shelley_bio.search.base import MetadataSource

TOOLFINDER_DATA_PATH = DATA_DIR / "toolfinder_meta.yaml"


class ToolfinderSource(MetadataSource):
    """
    Metadata source backed by the toolfinder corpus (toolfinder_meta.yaml).

    Usage:
        source = ToolfinderSource().load()
        results = source.search("variant calling")

    For testing, inject entries directly instead of loading from disk:
        source = ToolfinderSource()
        source.entries = [{"id": "fastqc", "name": "FastQC", ...}]
    """

    name = "toolfinder"

    def __init__(self, data_path: Path = TOOLFINDER_DATA_PATH):
        super().__init__()
        self.data_path = Path(data_path)

    def load(self) -> "ToolfinderSource":
        """Load toolfinder_meta.yaml into self.entries."""
        with open(self.data_path, encoding="utf-8") as f:
            self.entries = yaml.safe_load(f)
        return self

    def search(self, query: str, limit: Optional[int] = None) -> list[str]:
        """
        Same algorithm as RsecSource.search() — see that docstring for the steps.

        Why not inherit the implementation from MetadataSource (polymorphism)?
        The algorithm is identical, but toolfinder entries use a nested EDAM dict
        format that must go through _flatten_edam() before tokenisation.
        Keeping the full algorithm description here — rather than delegating to a
        shared parent method — means a maintainer can read this file without
        following the inheritance chain to understand what search() does.

        # 1–6 same as RsecSource.search()
        pass
        """
