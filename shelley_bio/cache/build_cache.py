from __future__ import annotations

import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, TypedDict
from shelley_bio.utils.globals import CVMFS_GALAXY_SINGULARITY_PATH

# Schema for cache entries, for consistency
class CacheEntry(TypedDict):
    entry_name: str
    tool_name: str
    tag: Optional[str]
    path: str
    size_bytes: int
    mtime: float

class CacheDocument(TypedDict):
    generated_at: str
    cvmfs_root: str
    entry_count: int
    entries: List[CacheEntry]
    tool_names: List[str]

def build_cache(
    cvmfs_path: Path,
    output_path: Path,
) -> None:
    entries = scan_executable_entries(cvmfs_path)
    tool_names = sorted({e.get("tool_name") for e in entries})

    cache: CacheDocument = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cvmfs_root": str(cvmfs_path),
        "entry_count": len(entries),
        "entries": [
            {
                "entry_name": e.get("entry_name"),
                "tool_name": e.get("tool_name"),
                "tag": e.get("tag"),
                "path": e.get("path"),
                "size_bytes": e.get("size_bytes"),
                "mtime": e.get("mtime"),
            }
            for e in entries
        ],
        "tool_names": tool_names,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def scan_executable_entries(cvmfs_path: Path) -> list[CacheEntry]:
    """
    Scan a CVMFS 'all' directory and store as class
    """
    entries: list[CacheEntry] = []

    for entry in cvmfs_path.iterdir():
        if ":" in entry.name:
            tool_name, tag = entry.name.split(":", 1)
        else:
            tool_name, tag = entry.name, None

        st = entry.stat()

        entries.append(
            CacheEntry(
                entry_name=entry.name,
                tool_name=tool_name,
                tag=tag,
                path=str(entry),
                size_bytes=st.st_size,
                mtime=st.st_mtime,
            )
        )
    return entries

if __name__ == "__main__":
    build_cache(
        cvmfs_path=Path(CVMFS_GALAXY_SINGULARITY_PATH),
        output_path=Path("galaxy_singularity_cache.json.gz")
    )