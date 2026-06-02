# How to find and search for tools

This guide covers the four read-only commands: `find`, `search`, `versions`, and `list`.

For the MCP tool schemas used by AI assistants, see [docs/reference/mcp.md](../reference/mcp.md).

## Find a tool by name — `find`

Use `find` when you know the tool's name.

```bash
shelley-bio find fastqc
shelley-bio find STAR          # case-insensitive
shelley-bio find bwa-mem2      # hyphens and underscores handled automatically
```

**Returns:**
- Tool description, homepage, and EDAM operations
- Most recent container version and CVMFS path
- Copy-pastable `singularity exec` and `singularity shell` commands
- A table of the next most-recent versions with buildable status and install state

If no exact match is found, shelley-bio suggests close alternatives.

## Search by function — `search`

Use `search` when you know what you want to do but not which tool does it.

```bash
shelley-bio search "quality control"
shelley-bio search "variant calling"
shelley-bio search "genome assembly"
shelley-bio search "adapter trimming"
```

**Returns:** A list of matching tools sorted alphabetically, each with a description and latest container version.

> **Note:** Search is under active development — corpus and ranking improvements are coming.

### Tips for better results

Shorter technical terms work better than full sentences:

| Less effective | More effective |
|---|---|
| `"check if my fastq data is good"` | `"fastq quality control"` |
| `"find where mutations are"` | `"variant calling"` |
| `"build a genome from scratch"` | `"de novo assembly"` |
| `"line up reads to a reference"` | `"read mapping"` |

Combine terms to narrow results:

```bash
shelley-bio search "splice-aware alignment"
shelley-bio search "single cell clustering"
```

### Known limitations

- **Keyword-based, not semantic.** The query `"how do I QC my reads?"` will not match a tool described as _"quality control for sequencing data"_ — use `"quality control"` instead.
- **Metadata is incomplete for some tools.** If `find` returns no description, check the tool's homepage directly or try `search` with related terms.
- **Container availability does not equal tool availability.** A tool can appear in the metadata without a container on CVMFS (it will show a warning). The tool may still be usable via a module system or conda.

## List all versions — `versions`

Use `versions` to see every available container for a tool, sorted newest-first.

```bash
shelley-bio versions samtools
shelley-bio versions bwa
shelley-bio versions gatk
```

**Returns:** Every available version with CVMFS path, file size, and last-modified date.

Use this when you need to pin an exact version — for reproducibility or to test a specific release.

> **Note:** Versions is under active development — corpus and ranking improvements are coming.
