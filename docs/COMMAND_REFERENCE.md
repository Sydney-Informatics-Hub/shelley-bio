# 📖 BioFinder MCP — Reference

Complete reference for the CLI commands, MCP tools, and MCP resources.

---

## CLI commands

```
biofinder_client.py <command> [args]
```

| Command | Arguments | Description |
|---|---|---|
| `find <name>` | Tool name (string) | Look up a tool by name |
| `search <query>` | Query string | Search by function or description |
| `versions <name>` | Tool name (string) | List all container versions for a tool |
| `list [n]` | Optional integer (default 50) | Browse available tools |
| `interactive` | — | Start interactive REPL |

### `find`

```bash
./biofinder_client.py find fastqc
./biofinder_client.py find "bwa-mem2"
```

- Case-insensitive.
- Tries `id`, `name`, `biotools`, and `biocontainers` fields from metadata.
- Falls back to substring matching if no exact match.
- Handles hyphen/underscore variants automatically.

### `search`

```bash
./biofinder_client.py search "quality control"
./biofinder_client.py search variant calling       # quotes optional for multi-word
```

- Scores all metadata records against your query.
- Returns results ranked by relevance score (highest first).

### `versions`

```bash
./biofinder_client.py versions samtools
```

- Returns all versions sorted newest-first.
- Each entry includes CVMFS path, size in MB, and last-modified date.

### `list`

```bash
./biofinder_client.py list
./biofinder_client.py list 200
```

- Alphabetical, columnar output.
- Draws from both the metadata catalog and the container index, so includes tools that have containers but no metadata.

### `interactive`

```bash
./biofinder_client.py interactive
```

Starts a REPL. Available commands inside interactive mode:

```
find <tool_name>
search <description>
versions <tool_name>
list [limit]
help
quit / exit
```

## MCP tool schema

The server implements the
[Model Context Protocol](https://modelcontextprotocol.io/) and can be used by any
MCP-compatible client (LLMs, workflow tools, etc.).

### `find_tool`

```json
{
  "name": "find_tool",
  "inputSchema": {
    "type": "object",
    "properties": {
      "tool_name": { "type": "string" }
    },
    "required": ["tool_name"]
  }
}
```

**Returns:** Formatted text containing tool metadata, latest container path,
copy-pastable usage examples, and a summary of other available versions.

---

### `search_by_function`

```json
{
  "name": "search_by_function",
  "inputSchema": {
    "type": "object",
    "properties": {
      "description": { "type": "string" },
      "limit":       { "type": "integer", "default": 3 }
    },
    "required": ["description"]
  }
}
```

**Returns:** Formatted text with a ranked list of matching tools, each with
description, operations, latest container tag, and a quick-start command.

---

### `get_container_versions`

```json
{
  "name": "get_container_versions",
  "inputSchema": {
    "type": "object",
    "properties": {
      "tool_name": { "type": "string" }
    },
    "required": ["tool_name"]
  }
}
```

**Returns:** Formatted text listing every container version for the tool, sorted
newest-first. Each entry shows version tag, CVMFS path, size (MB), and
last-modified date.

---

### `list_available_tools`

```json
{
  "name": "list_available_tools",
  "inputSchema": {
    "type": "object",
    "properties": {
      "limit": { "type": "integer", "default": 50 }
    },
    "required": []
  }
}
```

**Returns:** Formatted text with an alphabetical list of tool names.

---

## MCP resources

Resources are read via `read_resource(uri)`.

| URI | MIME type | Content |
|---|---|---|
| `biocontainer://cache-info` | `application/json` | `generated_at`, `cvmfs_root`, `entry_count` |
| `biocontainer://tool-list` | `text/plain` | Newline-separated list of tool names (up to 1000) |

---

## Container tag format

Tags follow the Bioconda build convention:

```
<version>--<build_string>

Examples:
  0.12.1--hdfd78af_0      # version 0.12.1, build hash hdfd78af, build number 0
  1.17--h00cdaf9_0        # version 1.17
  3.0.1--h503566f_0       # version 3.0.1
```

When multiple containers exist for the same version (different build strings),
BioFinder sorts by the full tag string as a tiebreaker, so the "latest" shown may
not always be the numerically last build. Use `versions` to inspect all options.

## CVMFS path format

All container paths follow this pattern:

```
/cvmfs/singularity.galaxyproject.org/all/<tool_name>:<tag>
```

Paths are valid when the CVMFS filesystem is mounted at
`/cvmfs/singularity.galaxyproject.org`. On systems without CVMFS, the paths will
not resolve — BioFinder does not validate path existence at query time.
