"""
RsecSource — loads and searches the RSEC bio.tools corpus.

The RSEC artifact (rsec_meta.json.gz) stores EDAM fields as plain string lists,
already flattened during ingestion by build_rsec_meta.py. This means
_flatten_edam() passes them through unchanged, unlike toolfinder entries which
use nested dicts.
"""

import gzip
import json
from pathlib import Path
from typing import Optional

from shelley_bio.utils.globals import DATA_DIR
from shelley_bio.search.base import MetadataSource

RSEC_DATA_PATH = DATA_DIR / "rsec_meta.json.gz"


class RsecSource(MetadataSource):
    """
    Metadata source backed by the RSEC bio.tools corpus (rsec_meta.json.gz).

    Usage:
        source = RsecSource().load()
        results = source.search("variant calling")

    For testing, inject entries directly instead of loading from disk:
        source = RsecSource()
        source.entries = [{"id": "bwa", "name": "BWA", ...}]
    """

    name = "rsec"

    def __init__(self, data_path: Path = RSEC_DATA_PATH):
        super().__init__()
        self.data_path = Path(data_path)

    def load(self) -> "RsecSource":
        """
        Load rsec_meta.json.gz into self.entries.

        The artifact is a gzipped JSON file produced by shelley-bio-build-rsec.
        Top-level keys: generated_at, source, source_commit, entry_count,
        field_coverage, entries. Only entries is loaded here.
        """
        with gzip.open(self.data_path, "rt", encoding="utf-8") as f:
            doc = json.load(f)
        self.entries = doc["entries"]
        return self

    def search(self, query: str, limit: Optional[int] = None) -> list[str]:
        """
        Keyword OR-match across name, description, edam-operations, edam-topics.
        Returns tool names sorted alphabetically, truncated to limit.

        RSEC entries store EDAM fields as plain string lists (already flattened
        during build_rsec_meta.py ingestion), so _flatten_edam() passes them
        through unchanged.

        Algorithm:
        # 1. self._normalise(query) → raw token list
        # 2. drop stopwords via self._load_stopwords(); fall back to raw tokens
        #    if all tokens are stopwords (to avoid returning an empty set)
        # 3. self._expand_tokens(tokens) → query token set (adds hyphen variants)
        # 4. for each entry in self.entries:
        #      a. collect searchable text from: name, description,
        #         edam-operations, edam-topics
        #         (edam-inputs/outputs excluded — see explanation/search-design.md)
        #      b. self._flatten_edam() each EDAM field → plain strings
        #      c. self._expand_tokens(self._normalise(joined_text)) → entry token set
        #      d. if query_tokens ∩ entry_tokens is non-empty → entry matches
        # 5. collect matched tool names (deduplicated, preserving first occurrence)
        # 6. sort alphabetically, then return names[:limit]
        pass
        """
