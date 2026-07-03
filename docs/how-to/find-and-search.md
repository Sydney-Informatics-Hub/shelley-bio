# How to find and search for tools

This guide covers the three read-only commands: `find`, `search`, and `versions`.

## Find a tool by name — `find`

Use `find` when you know the tool's name.

```bash
shelley find fastqc
shelley find STAR          # case-insensitive
shelley find bwa-mem2      # hyphens and underscores handled automatically
```

**Returns:**
- Tool description, homepage, and EDAM operations
- A table of recent container versions with buildable status and install state
- An install prompt with the `shelley build` command

If no exact match is found, shelley suggests close alternatives.

> **Note:** `find` is case-insensitive. `shelley find Arriba` and `shelley find arriba` return the same result.

## Search by function — `search`

Use `search` when you know what you want to do but not which tool does it.

```bash
shelley search "quality control"
shelley search "variant calling"
shelley search "genome assembly"
shelley search "adapter trimming"
```

**Returns:** A list of matching tool names sorted alphabetically, each with a `shelley find <name>` command to get full details. Results are filtered to tools that have a container available on CVMFS, so every result can be installed directly with `shelley build`.

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
shelley versions samtools
shelley versions bwa
shelley versions gatk
```

**Returns:** Every available version with buildable status (✓ = in the upstream shpc-registry, ✗ = requires local registry fallback); an install prompt.

Use this when you need to pin an exact version for reproducibility or to test a specific release.
