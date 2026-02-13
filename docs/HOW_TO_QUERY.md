# 🔍 How to Query BioFinder

This guide covers the four query types BioFinder supports, with real examples and
tips for getting good results.

All examples below are shown in **interactive mode** (the `biofinder>` prompt).
BioFinder also supports a **non-interactive command-line interface** for scripting
and one-shot commands. See [`COMMAND_REFERENCE.md`](COMMAND_REFERENCE.md).

## Available Tools

1. **find_tool** - Find a specific tool by name
   - Returns: metadata, container versions, usage examples
   - Example: `find fastqc`

2. **search_by_function** - Search by description or operation
   - Returns: ranked list of matching tools
   - Example: `search quality control`

3. **get_container_versions** - List all versions of a tool
   - Returns: complete version history with CVMFS paths
   - Example: `versions samtools`

4. **list_available_tools** - Browse available tools
   - Returns: alphabetical list of tool names
   - Example: `list 10`

## 1 — Find a specific tool  `find`

Use `find` when you know the tool's name. The search is case-insensitive and handles
common variations (hyphens vs underscores).

```bash
biofinder> find fastqc
biofinder> find IQTree    # case doesn't matter
biofinder> find bwa-mem2
```

**Returns:**
- Tool description, homepage, and operations
- Most recent container version + CVMFS path
- Copy-pastable `singularity exec` and `singularity shell` commands
- The three next-most-recent versions, with a count of how many more exist

## 2 — Search by function  `search`

Use `search` when you know what you want to *do* but not which tool to use.
BioFinder scores tools by how closely their description, operations, and topics
match your keywords.

```bash
biofinder> search "quality control"
biofinder> search "variant calling"
biofinder> search "genome assembly"
biofinder> search "adapter trimming"
```

**Returns:** A ranked list of matching tools, each with a description, operations,
latest container version, and a quick-start command.

### Tips for better search results

Shorter, technical terms work better than full sentences:

| ❌ Less effective | ✅ More effective |
|---|---|
| `"check if my fastq data is good"` | `"fastq quality control"` |
| `"find where mutations are"` | `"variant calling"` |
| `"build a genome from scratch"` | `"de novo assembly"` |
| `"line up reads to a reference"` | `"read mapping"` |

You can also combine terms to narrow results:

```bash
biofinder> search "splice-aware alignment"
biofinder> search "single cell clustering"
```

### ⚠️ Known `search` limitations

- **Search is keyword-based**, not semantic. The query `"how do I QC my reads?"`
  will not match a tool described as *"quality control for sequencing data"* — use
  `"quality control"` instead.
- **Metadata is incomplete for many tools.** If `find` returns no description,
  check the tool's homepage directly or try `search` with related terms.
- **Container availability ≠ tool availability.** A tool can appear in the metadata
  without having a container on CVMFS (it will show a warning). The tool may still
  be usable via a module system or conda.
- **The `search` score is a rough heuristic.** Results near the top of a list are
  usually relevant, but the ranking isn't perfect — scan a few entries before
  concluding a tool doesn't exist.

## 3 — List all versions  `versions`

Use `versions` when you need to pin an exact container version — for example,
to reproduce results from a paper, or to test whether a bug is version-specific.

```bash
biofinder> versions samtools
biofinder> versions bwa
biofinder> versions gatk
```

**Returns:** Every available version sorted newest-first, with the CVMFS path,
file size, and last-modified date for each.

## 4 — Browse available tools  `list`

Use `list` to explore what's available, or to confirm a tool is in the catalog
before running `find`.

```bash
./biofinder_client.py list           # first 50 tools
./biofinder_client.py list 200       # first 200 tools
```

**Returns:** An alphabetical, columnar list of tool names.
