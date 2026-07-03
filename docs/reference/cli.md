# CLI reference

Complete reference for all `shelley` commands.

```
shelley <command> [args]
```

---

## `find`

```bash
shelley find <tool_name> [-v | --verbose]
```

| Argument | Type | Required | Description |
|---|---|---|---|
| `tool_name` | string | Yes | Tool to look up |
| `-v`, `--verbose` | flag | No | Show every available container version, paginated, instead of the recent-versions preview |

Looks up a tool by name. Case-insensitive; handles hyphen/underscore variants. Matches against the `id` and `name` fields in the RSEC corpus; falls back to fuzzy matching when no exact match is found.

**Returns:** Tool description, homepage, and EDAM operations; a table of container versions with buildable status and install state; an install prompt. By default only the five most recent versions are shown; `-v` expands this to the full paginated list, sorted newest-first (✓ = in the upstream shpc-registry, ✗ = requires local registry fallback).

---

## `search`

```bash
shelley search <query>
```

| Argument | Type | Required |
|---|---|---|
| `query` | string | Yes |

Keyword search across tool metadata. Matches on name, description, EDAM operations, and EDAM topics. Results returned in alphabetical order.

**Returns:** List of matching tools with descriptions and latest container versions.

> Relevance ranking is under development.

---

## `build`

```bash
shelley build <tool_spec>
```

| Argument | Type | Required | Format |
|---|---|---|---|
| `tool_spec` | string | Yes | `<tool>`, `<tool>/<version>`, `<tool>:<version>--<hash>`, or a path to a text file of tool specs |

When `tool_spec` is an existing file, each non-blank non-comment line is treated as a tool spec and built in sequence. See [Build multiple modules](../how-to/build-modules.md).

Installs an Lmod module for a tool from CVMFS via `shpc`. Creates a local registry entry if the version is absent from the upstream shpc-registry. Prompts for sudo if the module directory is not writable.

**Returns:** Build status output.

Requires `shpc` on PATH and CVMFS mounted.

---

## `interactive`

```bash
shelley interactive
```

Starts a REPL session. Available commands inside the REPL:

```
find <tool_name> [-v]
search <description>
build <tool_spec>
help
quit / exit
```
