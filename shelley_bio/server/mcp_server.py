#!/usr/bin/env python3
"""
Shelley Bio MCP Server

This MCP server provides bioinformatics container discovery for CVMFS-hosted
Singularity containers, helping users find and use containerized tools.
"""

import json
import gzip
import yaml
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import re
import logging
import sys
from difflib import get_close_matches

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shelley_bio.utils.constants import STOP_WORDS
from shelley_bio.utils.style import console, ShelleyStyle, print_error
from shelley_bio.builder.cvmfs_builder import get_registry_tags

# MCP SDK imports
# The MCP server exposes "tools" (callable functions) and "resources" (readable
# data) over a JSON-RPC protocol on stdio. The client (biofinder_client.py)
# spawns this process and talks to it over its stdin/stdout pipes.
from mcp.server import Server
from mcp.types import (Resource, Tool, TextContent)

import mcp.server.stdio

# Data paths
DATA_DIR = Path(__file__).resolve().parent.parent.parent
METADATA_FILE = DATA_DIR / "toolfinder_meta.yaml"
SINGULARITY_CACHE_FILE = DATA_DIR / "galaxy_singularity_cache.json.gz"


# Logging
# We log to stderr only. stdout is reserved exclusively for MCP JSON-RPC
# messages — a single stray print() to stdout will corrupt the protocol and
# break the client connection.
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [shelley-bio] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

log = logging.getLogger("shelley-bio")

class BioFinderIndex:
    """Index of container metadata and singularity images."""
    
    def __init__(self):
        self.metadata: List[Dict[str, Any]] = []
        self.singularity_entries: List[Dict[str, Any]] = []
        self.tool_to_containers: Dict[str, List[Dict]] = defaultdict(list)
        self.container_index: Dict[str, List[Dict]] = defaultdict(list)
        self.cache_info: Dict[str, Any] = {}
        
    def load_data(self):
        """Load metadata and singularity cache."""
        # Load metadata YAML
        log.info(f"Loading metadata from {METADATA_FILE}...")
        with open(METADATA_FILE, 'r') as f:
            self.metadata = yaml.safe_load(f)
        log.info(f"Loaded {len(self.metadata)} tool metadata entries")
        
        # Load singularity cache
        log.info(f"Loading singularity cache from {SINGULARITY_CACHE_FILE}...")
        with gzip.open(SINGULARITY_CACHE_FILE, 'rt') as f:
            cache_data = json.load(f)
            self.cache_info = {
                'generated_at': cache_data['generated_at'],
                'cvmfs_root': cache_data['cvmfs_root'],
                'entry_count': cache_data['entry_count']
            }
            self.singularity_entries = cache_data['entries']
        log.info(f"Loaded {len(self.singularity_entries)} singularity entries")
        
        # Build indexes
        self._build_indexes()
        
    def _build_indexes(self):
        """Build search indexes."""
        # Index containers by tool name
        for entry in self.singularity_entries:
            tool_name = entry['tool_name'].lower()
            self.container_index[tool_name].append(entry)
            
    def _parse_version(self, tag: str) -> Tuple[List[int], str]:
        """Parse version from tag for sorting."""
        # Extract version number (e.g., "0.12.1" from "0.12.1--hdfd78af_1")
        match = re.match(r'^(\d+(?:\.\d+)*)', tag)
        if match:
            version_str = match.group(1)
            version_parts = [int(x) for x in version_str.split('.')]
            return (version_parts, tag)
        return ([0], tag)
        
    def search_tool(self, query: str) -> Dict[str, Any]:
        """
        Search for a tool and return metadata + available containers.
        
        Returns structured data about the tool including:
        - Tool metadata (description, homepage, publications)
        - Available containers with versions
        - Most recent version
        - Usage examples
        """
        query_lower = query.lower()
        
        # Find in metadata
        tool_meta = None
        for entry in self.metadata:
            entry_id = entry.get('id', '') or ''
            entry_name = entry.get('name', '') or ''
            entry_biotools = entry.get('biotools', '') or ''
            entry_biocontainers = entry.get('biocontainers', '') or ''
            
            if (entry_id.lower() == query_lower or 
                entry_name.lower() == query_lower or
                entry_biotools.lower() == query_lower or
                entry_biocontainers.lower() == query_lower):
                tool_meta = entry
                break
        
        # Fuzzy-match against all known IDs when no exact match was found
        suggestions: List[str] = []
        if not tool_meta:
            id_map = {e['id'].lower(): e['id'] for e in self.metadata if e.get('id')}
            suggestions = [id_map[m] for m in get_close_matches(query_lower, id_map.keys(), n=8, cutoff=0.6)]
        
        # Get containers - try exact match first, then variations
        containers = []
        search_variations = [
            query_lower,
            query_lower.replace('-', '_'),
            query_lower.replace('_', '-'),
        ]
        
        # Add name if available
        if tool_meta and tool_meta.get('id'):
            search_variations.append(tool_meta['id'].lower())
        
        for variation in search_variations:
            if variation in self.container_index:
                containers = self.container_index[variation]
                break
        
        # Sort containers by version (newest first)
        if containers:
            containers_sorted = sorted(
                containers,
                key=lambda x: self._parse_version(x['tag']),
                reverse=True
            )
        else:
            containers_sorted = []
        
        return {
            'query': query,
            'metadata': tool_meta,
            'containers': containers_sorted,
            'container_count': len(containers_sorted),
            'suggestions': suggestions if not tool_meta else [],
        }

    def _normalise(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r"[^\w\s\-]", " ", text)
        return text.split()

    def _flatten_edam(self, value):
        """Flatten EDAM fields safely."""
        results = []
        if not value:
            return results

        if isinstance(value, list):
            for v in value:
                if isinstance(v, dict):
                    if "term" in v and v["term"]:
                        results.append(str(v["term"]))
                    if "formats" in v and v["formats"]:
                        if isinstance(v["formats"], list):
                            results.extend(map(str, v["formats"]))
                        else:
                            results.append(str(v["formats"]))
                else:
                    results.append(str(v))
        else:
            results.append(str(value))

        return list(set(results))  # Remove duplicates

    def _search_metadata(self, query: str) -> List[str]:
        """
        Search tool metadata using token-based OR matching.

        HOW IT WORKS
        ------------
        1. The query is normalised (lowercased, cleaned with _normalise(), split into tokens).
        2. Tokens are expanded to improve matching:
             - Keep original token
             - Remove hyphens (rna-seq → rnaseq)
             - Split hyphenated terms (rna-seq → rna, seq)
            
        3. Each tools searchable text is built from:
             - id, name, description
             - edam-operations, edam-topics, edam-inputs, edam-outputs
           (EDAM fields are flattened to plain strings.)
        4. A tool matches if ANY expanded query token overlaps with
           ANY expanded metadata token.
        
        EXAMPLE
        -------
        "RNA-seq alignment" -> tokens: ["rna-seq", "alignment"] + expansions ["rnaseq", "rna", "seq", "alignment"]

        NOTES
        -----
        - Matching is case-insensitive.
        - OR-based (at least one token match returns the tool).
        - No ranking or fuzzy matching.
        - Partial substrings (e.g. "align") do not match "alignment".

        Returns a list of unique matching tool names.
        """
        class SearchResults(list):
            def __contains__(self, item):
                if isinstance(item, list):
                    return all(list.__contains__(self, token) for token in item)
                return list.__contains__(self, item)

        def expand_tokens(tokens):
            expanded = set()
            for token in tokens:
                if not token:
                    continue
                expanded.add(token)
                compact = token.replace("-", "")
                expanded.add(compact)
                if "-" in token:
                    expanded.update(part for part in token.split("-") if part)
            return expanded

        query_tokens = expand_tokens(self._normalise(query))
        results = SearchResults()
        seen = set()

        for entry in self.metadata:
            entry_id = str(entry.get("id") or "")
            entry_name = str(entry.get("name") or "")
            entry_description = str(entry.get("description") or "")

            text_parts = [entry_id, entry_name, entry_description]

            for field in (
                "edam-operations",
                "edam-topics",
                "edam-inputs",
                "edam-outputs",
            ):
                text_parts.extend(self._flatten_edam(entry.get(field)))

            searchable_tokens = expand_tokens(self._normalise(" ".join(text_parts)))

            if not searchable_tokens:
                continue

            # Token intersection instead of substring matching
            overlap = query_tokens.intersection(searchable_tokens)

            if overlap:
                tool_name = entry_name or entry_id
                if tool_name and tool_name not in seen:
                    results.append(tool_name)
                    seen.add(tool_name)

        return results
 
    def search_by_description(self, query: str) -> List[str]:
        """
        Search tools by description or functionality.
        Useful for queries like "What can I use to generate count data?"
        """
        log.info(query)
        return self._search_metadata(query)
    
    def list_all_tools(self, limit: int = 10) -> List[str]:
        """List all available tool names."""
        tools = set()
        
        # From metadata
        for entry in self.metadata:
            if entry.get('id'):
                tools.add(entry['id'])
        
        # From containers
        for tool_name in self.container_index.keys():
            tools.add(tool_name)
        
        return sorted(list(tools))[:limit]


# Initialize the index
index = BioFinderIndex()

# Create MCP server
app = Server("shelley-bio")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources (the data sources)."""
    return [
        Resource(
            uri="shelley-bio://cvmfs-galaxy-containers",
            name="CVMFS Cache Information (Galaxy containers)",
            mimeType="application/json",
            description="Information about the Singularity container cache from the CVMFS"
        ),
        Resource(
            uri="shelley-bio://metadata",
            name="Tool metadata",
            mimeType="text/plain",
            description="Bio.tools metadata from https://github.com/AustralianBioCommons/finder-service-metadata/blob/main/data/data.yaml"
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    if uri == "shelley-bio://cvmfs-galaxy-containers":
        return json.dumps(index.cache_info, indent=2)
    elif uri == "shelley-bio://metadata":
        tools = index.list_all_tools(limit=999999)
        return "\n".join(tools)
    else:
        raise ValueError(f"Unknown resource: {uri}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="find_tool",
            description=(
                "Find a bioinformatics tool by name and get container information. "
                "Use this when the user asks 'Where can I find X?' or 'How do I use X?'. "
                "Returns the tool's metadata, available container versions, and usage examples."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to search for (e.g., 'fastqc', 'iqtree', 'samtools')"
                    }
                },
                "required": ["tool_name"]
            }
        ),
        Tool(
            name="search_by_function",
            description=(
                "Search for tools by their function or description. "
                "Use this when the user asks 'What can I use to do X?' or describes a task. "
                "Examples: 'count data', 'quality control', 'alignment', 'assembly'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of what the user wants to do"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["description"]
            }
        ),
        Tool(
            name="get_container_versions",
            description=(
                "Get all available versions of a specific container. "
                "Returns a sorted list of versions with their CVMFS paths."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool"
                    }
                },
                "required": ["tool_name"]
            }
        ),
        Tool(
            name="list_available_tools",
            description=(
                "Search for tools by their function or description. "
                "Use this when the user asks 'What tools are available?'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of tools to list",
                        "default": 10
                    }
                },
                "required": []
            }
        )
    ]


def _handle_find_tool(tool_name: str) -> str:
    # Remove version suffixes
    clean_name = re.sub(r'[:/].*$', '', tool_name).strip()
    result = index.search_tool(clean_name)

    meta = result['metadata']
    containers = result['containers']

    tool_payload: Optional[Dict] = None
    if meta:
        tool_payload = {
            "id": meta.get("id", clean_name),
            "name": meta.get("name", clean_name),
            "description": meta.get("description") or "",
            "homepage": meta.get("homepage") or "",
            "operations": index._flatten_edam(meta.get("edam-operations")),
            "inputs": index._flatten_edam(meta.get("edam-inputs")),
            "outputs": index._flatten_edam(meta.get("edam-outputs")),
        }

    containers_payload: Optional[Dict] = None
    if containers:
        seen: set = set()
        unique_versions: List[Dict] = []
        tool_id = tool_payload["id"] if tool_payload else clean_name
        registry_tags = get_registry_tags(tool_id)
        for c in containers:
            short = c["tag"].split("--")[0]
            if short not in seen:
                seen.add(short)
                buildable = c["tag"] in registry_tags
                unique_versions.append({"version": short, "buildable": buildable})

        containers_payload = {
            "available": True,
            "recent_versions": unique_versions[:5],
            "total_versions": len(unique_versions),
            "install_command": f"shelley-bio build {tool_id}",
        }

    return json.dumps({
        "query": clean_name,
        "found": meta is not None or bool(containers),
        "suggestions": result.get("suggestions", []),
        "tool": tool_payload,
        "containers": containers_payload,
    })


def _handle_search_by_function(description: str, limit: int) -> str:
    results = index.search_by_description(description)[:limit]

    if not results:
        return f"No tools found matching '{description}'. Try different keywords or browse available tools."

    parts = [
        f"\n{'='*70}\n",
        f"🔎 TOOLS MATCHING: {description}\n",
        f"{'='*70}\n\n",
        f"Found {len(results)} matching tools.\n",
    ]
    for i, tool_name in enumerate(results, 1):
        parts.append(f"{i:2}. {tool_name}\n")
    return "".join(parts)


def _handle_get_container_versions(tool_name: str) -> str:
    result = index.search_tool(tool_name)

    if not result['containers']:
        return f"No containers found for '{tool_name}'"

    parts = [f"# Container Versions for {tool_name}\n\nTotal versions: {len(result['containers'])}\n\n"]
    for container in result['containers']:
        parts.append(f"## Version {container['tag']}\n")
        parts.append(f"- Path: `{container['path']}`\n")
        parts.append(f"- Size: {container['size_bytes'] / (1024**2):.1f} MB\n")
        parts.append(f"- Modified: {datetime.fromtimestamp(container['mtime']).strftime('%Y-%m-%d')}\n\n")
    return "".join(parts)


def _handle_list_available_tools(limit: int) -> str:
    tools = index.list_all_tools(limit)
    return f"# Available Bioinformatics Tools ({len(tools)} shown)\n\n" + "\n".join(f"- {tool}" for tool in tools)


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Dispatch tool calls to focused handler functions."""
    if name == "find_tool":
        text = _handle_find_tool(arguments["tool_name"])
    elif name == "search_by_function":
        text = _handle_search_by_function(arguments["description"], arguments.get("limit", 10))
    elif name == "get_container_versions":
        text = _handle_get_container_versions(arguments["tool_name"])
    elif name == "list_available_tools":
        text = _handle_list_available_tools(arguments.get("limit", 50))
    else:
        raise ValueError(f"Unknown tool: {name}")

    return [TextContent(type="text", text=text)]


async def main():
    """Run the MCP server."""
    # Load data
    #print("Initializing Shelley Bio MCP Server...")
    index.load_data()
    #print("Ready to serve requests!")
    
    # Run server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())