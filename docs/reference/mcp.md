# MCP reference

Complete reference for the [Model Context Protocol](https://modelcontextprotocol.io/) server exposed by shelley-bio. MCP-compatible clients (AI assistants, workflow tools) use these tools and resources.

---

## MCP tools

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

**Returns:** Formatted text containing tool metadata, latest container path, copy-pastable Singularity commands, and a summary of other available versions.

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

**Returns:** Formatted text with an alphabetical list of matching tools, each with description, operations, latest container tag, and a quick-start command.

> Results are sorted alphabetically, not by relevance score.

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

**Returns:** Formatted text listing every container version for the tool, sorted newest-first. Each entry shows version tag, CVMFS path, size (MB), and last-modified date.

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
| `shelley-bio://cvmfs-galaxy-containers` | `application/json` | `generated_at`, `cvmfs_root`, `entry_count` |
| `shelley-bio://metadata` | `text/plain` | Newline-separated list of tool names |

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

When multiple containers exist for the same version (different build strings), shelley-bio sorts by the full tag string as a tiebreaker. Use `versions` to inspect all options.

---

## CVMFS path format

All container paths follow this pattern:

```
/cvmfs/singularity.galaxyproject.org/all/<tool_name>:<tag>
```

Paths are valid when the CVMFS filesystem is mounted at `/cvmfs/singularity.galaxyproject.org`. shelley-bio does not validate path existence at query time.

---

## `build` as an MCP tool

`shelley-bio build` is currently CLI-only. Exposing it as an MCP tool is under consideration. The main open questions are privilege (build requires sudo and modifies system state) and safety (it is not easily reversible). Decision deferred until the MCP permission model is clearer.
