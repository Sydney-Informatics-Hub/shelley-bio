# CLI reference

Complete reference for all `shelley-bio` commands.

```
shelley-bio <command> [args]
```

---

## `find`

```bash
shelley-bio find <tool_name>
```

| Argument | Type | Required |
|---|---|---|
| `tool_name` | string | Yes |

Looks up a tool by name. Case-insensitive; handles hyphen/underscore variants. Tries `id`, `name`, `biotools`, and `biocontainers` fields from metadata; falls back to fuzzy matching when no exact match is found.

**Returns:** Tool metadata, latest container path and copy-pastable Singularity commands, a table of recent versions with buildable status and install state.

---

## `search`

```bash
shelley-bio search <query>
```

| Argument | Type | Required |
|---|---|---|
| `query` | string | Yes |

Keyword search across tool metadata. Matches on name, description, EDAM operations, and EDAM topics. Results returned in alphabetical order.

**Returns:** List of matching tools with descriptions and latest container versions.

> Relevance ranking is under development.

---

## `versions`

```bash
shelley-bio versions <tool_name>
```

| Argument | Type | Required |
|---|---|---|
| `tool_name` | string | Yes |

Lists every available container version for a tool, sorted newest-first.

**Returns:** Version tag, CVMFS path, size in MB, and last-modified date for each entry.

---

## `list`

```bash
shelley-bio list [limit]
```

| Argument | Type | Default |
|---|---|---|
| `limit` | integer | 50 |

Alphabetical browse of available tool names. Draws from both the metadata catalog and the container index, so includes tools that have containers but no metadata record.

**Returns:** Columnar alphabetical list of tool names.

---

## `build`

```bash
shelley-bio build <tool_spec>
```

| Argument | Type | Required | Format |
|---|---|---|---|
| `tool_spec` | string | Yes | `<tool>`, `<tool>/<version>`, or `<tool>:<version>--<hash>` |

Installs an Lmod module for a tool from CVMFS via `shpc`. Creates a local registry entry if the version is absent from the upstream shpc-registry. Prompts for sudo if the module directory is not writable.

**Returns:** Build status output.

Requires `shpc` on PATH and CVMFS mounted.

---

## `interactive`

```bash
shelley-bio interactive
```

Starts a REPL session. Available commands inside the REPL:

```
find <tool_name>
search <description>
versions <tool_name>
list [limit]
build <tool_spec>
help
quit / exit
```
