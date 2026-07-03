"""CVMFS cache loading utilities."""

import gzip
import json
import re

from shelley.utils.globals import DATA_DIR
from shelley.builder.cvmfs_builder import get_registry_tags


def load_cvmfs_tool_ids() -> set[str] | None:
    """Return normalised tool IDs from the CVMFS container cache, or None if unavailable."""
    cache_path = DATA_DIR / "galaxy_singularity_cache.json.gz"
    if not cache_path.exists():
        return None
    with gzip.open(cache_path, "rt", encoding="utf-8") as f:
        data = json.load(f)
    return {entry["tool_name"].lower().replace("-", "_") for entry in data["entries"]}


def load_versions_from_cache(tool_name: str) -> list[tuple[str, str]] | None:
    """Return (tag, path) pairs for tool_name from the CVMFS cache, sorted newest-first.

    Returns None if the cache file is missing; returns [] if the tool has no entries.
    """
    cache_path = DATA_DIR / "galaxy_singularity_cache.json.gz"
    if not cache_path.exists():
        return None
    with gzip.open(cache_path, "rt", encoding="utf-8") as f:
        data = json.load(f)

    tool_lower = tool_name.lower()
    variations = {tool_lower, tool_lower.replace("-", "_"), tool_lower.replace("_", "-")}
    entries = [e for e in data["entries"] if e["tool_name"].lower() in variations]

    def _ver_key(e: dict) -> tuple:
        m = re.match(r"^(\d+(?:\.\d+)*)", e["tag"])
        if m:
            return tuple(int(x) for x in m.group(1).split("."))
        return (0,)

    entries.sort(key=_ver_key, reverse=True)
    return [(e["tag"], e["path"]) for e in entries]


def compute_version_entries(tool_id: str, pairs: list[tuple[str, str]]) -> list[dict]:
    """Deduplicate (tag, path) pairs and annotate each with buildable status."""
    try:
        registry_tags = get_registry_tags(tool_id)
        buildable_shorts = {tag.split("--")[0] for tag in registry_tags}
    except Exception:
        buildable_shorts = set()
    seen: set = set()
    result = []
    for tag, _path in pairs:
        short = tag.split("--")[0]
        if short not in seen:
            seen.add(short)
            result.append({"version": short, "buildable": short in buildable_shorts})
    return result


def compute_build_entries(tool_id: str, pairs: list[tuple[str, str]]) -> list[dict]:
    """Annotate every (tag, path) build with buildable status, without deduplicating.

    Unlike ``compute_version_entries``, this keeps every individual container build
    (a single short version may have several ``--hash`` builds) and carries the full
    CVMFS container path — used by the ``-vv`` view.
    """
    try:
        registry_tags = get_registry_tags(tool_id)
        buildable_shorts = {tag.split("--")[0] for tag in registry_tags}
    except Exception:
        buildable_shorts = set()
    return [
        {"tag": tag, "path": path, "buildable": tag.split("--")[0] in buildable_shorts}
        for tag, path in pairs
    ]
