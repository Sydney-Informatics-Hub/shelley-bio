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

> **Note:** `find` is case-sensitive. `shelley-bio find Arriba` and `shelley-bio find arriba` may return different results — use the tool's canonical casing (usually lowercase) if you don't get a match.

## Search by function — `search`

Use `search` when you know what you want to do but not which tool does it.

```bash
shelley-bio search "quality control"
shelley-bio search "variant calling"
shelley-bio search "genome assembly"
shelley-bio search "adapter trimming"
```

**Returns:** A list of matching tool names sorted alphabetically, each with a `shelley-bio find <name>` command to get full details. Results are filtered to tools that have a container available on CVMFS, so every result can be installed directly with `shelley-bio build`.

### Tips for better results

The search is OR-based: **more words → more results, not fewer.** Each additional word is another independent match condition. Use the fewest, most domain-specific terms you know:

| Avoid | Better |
|---|---|
| `"check if my fastq data is good"` | `"quality control"` |
| `"tool that finds where mutations are"` | `"variant calling"` |
| `"assembling a genome from scratch"` | `"de novo assembly"` |
| `"RNA-seq analysis"` | `"RNA-seq"` |

If you get too many results, **remove words rather than adding them.** A single specific technical term (e.g., `"nanopore"`) returns far fewer results than a phrase (`"nanopore sequencing analysis"`).

Note that hyphens are expanded during tokenisation — `"chip-seq"` matches any tool containing *chip*, *seq*, or *chipseq*, while `"chipseq"` matches only the compound form.

### Known limitations

- **Returns many results for broad queries.** "OR-based" means any token can match, not all — the opposite of how a Google search works. `"quality control"` matches every tool that mentions either *quality* or *control* anywhere in its metadata, not only tools where both appear together. The current result set is large and unsorted by relevance.
- **No relevance ranking.** Results are sorted alphabetically, not by how well they match. The best tool for your task may be anywhere in the list.
- **Keyword-based, not semantic.** `"how do I QC my reads?"` will not match a tool described as _"quality control for sequencing data"_ — exact technical terms are required.
- **Metadata is incomplete for some tools.** If `find` returns no description, check the tool's homepage directly or try `search` with related terms.

For the design rationale behind these limitations, see [docs/explanation/search-design.md](../explanation/search-design.md).

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
