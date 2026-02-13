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
        
        # Search for partial matches if exact match not found
        if not tool_meta:
            for entry in self.metadata:
                entry_id = entry.get('id', '').lower()
                if query_lower in entry_id or entry_id in query_lower:
                    tool_meta = entry
                    break
        
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
            'container_count': len(containers_sorted)
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

        return results

    def _search_metadata(self, query: str) -> List[str]:
        """
        Search metadata and return matching tool names.
        OR-based matching with token-level accuracy.
        """

        query_tokens = set(self._normalise(query))
        results = []

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

            searchable_tokens = set(self._normalise(" ".join(text_parts)))

            if not searchable_tokens:
                continue

            # Token intersection instead of substring matching
            overlap = query_tokens.intersection(searchable_tokens)

            if overlap:
                tool_name = entry_name or entry_id
                if tool_name:
                    results.append(tool_name)

        return sorted(set(results))
 
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


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Handle tool calls based on the tool name and arguments. 

    Piece together responses based on available metadata and container information, formatted for user readability.
    """
    
    if name == "find_tool":
        tool_name = arguments["tool_name"]
        result = index.search_tool(tool_name)
        
        # Format response
        response_parts = []
        
        # Tool information
        if result['metadata']:
            meta = result['metadata']
            response_parts.append(f"\n{'='*70}\n")
            response_parts.append(f"🧬 {meta.get('name', tool_name.upper())}\n")
            response_parts.append(f"{'='*70}\n\n")

            if meta.get('description'):
                response_parts.append(f"📝 Description:\n")
                response_parts.append(f"   {meta['description']}\n\n")  
            
            if meta.get('homepage'):
                response_parts.append(f"🌐 Homepage: {meta['homepage']}\n")
            
            # Operations
            if meta.get('edam-operations'):
                response_parts.append(f"⚙️  Operations: {', '.join(meta['edam-operations'])}\n")
        else:
            response_parts.append(f"\n{'='*70}\n")
            response_parts.append(f"🧬 {tool_name.upper()}\n")
            response_parts.append(f"{'='*70}\n\n")
            response_parts.append("ℹ️  No metadata available for this tool\n")
        
        # Container information
        if result['containers']:
            response_parts.append(f"\n{'─'*70}\n")
            response_parts.append(f"📦 AVAILABLE CONTAINERS ({result['container_count']} versions)\n")
            response_parts.append(f"{'─'*70}\n\n")
            
            # Most recent version
            latest = result['containers'][0]
            response_parts.append(f"✨ Most Recent Version: {latest['tag']}\n\n")
            response_parts.append(f"   Path: {latest['path']}\n")
            response_parts.append(f"   Size: {latest['size_bytes'] / (1024**2):.1f} MB\n\n")
            
            # Usage example
            response_parts.append(f"{'─'*70}\n")
            response_parts.append(f"💡 USAGE EXAMPLES\n")
            response_parts.append(f"{'─'*70}\n\n")
            response_parts.append(f"# Execute a command in the container\n")
            response_parts.append(f"singularity exec {latest['path']} \\\n")
            response_parts.append(f"  {tool_name} --help\n\n")
            response_parts.append(f"# Run interactively\n")
            response_parts.append(f"singularity shell {latest['path']}\n")
            
            # Show all versions
            if len(result['containers']) > 1:
                response_parts.append(f"\n{'─'*70}\n")
                response_parts.append(f"📚 OTHER VERSIONS\n")
                response_parts.append(f"{'─'*70}\n\n")
                for i, container in enumerate(result['containers'][:3], 1):  # Show top 3
                    response_parts.append(
                        f"  {i:2}. {container['tag']}\n"
                        f"      {container['path']}\n"
                    )
                if len(result['containers']) > 3:
                    response_parts.append(f"   ... and {len(result['containers']) - 3} more versions\n")
        else:
            response_parts.append(f"\n⚠️  WARNING: No containers found in CVMFS for this tool\n")
            response_parts.append(f"   The tool may be available through other means or under a different name.\n")
        
        response_parts.append(f"\n{'='*70}\n")
        return [TextContent(type="text", text="".join(response_parts))]
    
    elif name == "search_by_function":
        description = arguments["description"]
        limit = arguments.get("limit", 10)
        
        results = index.search_by_description(description)
        
        if not results:
            return [TextContent(
                type="text",
                text=f"No tools found matching '{description}'. Try different keywords or browse available tools."
            )]
        
        response_parts = []
        response_parts.append(f"\n{'='*70}\n")
        response_parts.append(f"🔎 TOOLS MATCHING: {description}\n")
        response_parts.append(f"{'='*70}\n\n")
        response_parts.append(f"Found {len(results)} matching tools.\n")
        
        for i, tool_name in enumerate(results, 1):
            response_parts.append(f"{i:2}. {tool_name}\n")
        
        return [TextContent(type="text", text="".join(response_parts))]
    
    elif name == "get_container_versions":
        tool_name = arguments["tool_name"]
        result = index.search_tool(tool_name)
        
        if not result['containers']:
            return [TextContent(
                type="text",
                text=f"No containers found for '{tool_name}'"
            )]
        
        response_parts = [f"# Container Versions for {tool_name}\n\n"]
        response_parts.append(f"Total versions: {len(result['containers'])}\n\n")
        
        for container in result['containers']:
            response_parts.append(f"## Version {container['tag']}\n")
            response_parts.append(f"- Path: `{container['path']}`\n")
            response_parts.append(f"- Size: {container['size_bytes'] / (10242):.1f} MB\n")
            response_parts.append(f"- Modified: {datetime.fromtimestamp(container['mtime']).strftime('%Y-%m-%d')}\n\n")
        
        return [TextContent(type="text", text="".join(response_parts))]
    
    elif name == "list_available_tools":
        limit = arguments.get("limit", 50)
        tools = index.list_all_tools(limit)
        
        response = f"# Available Bioinformatics Tools ({len(tools)} shown)\n\n"
        response += "\n".join(f"- {tool}" for tool in tools)
        
        return [TextContent(type="text", text=response)]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


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