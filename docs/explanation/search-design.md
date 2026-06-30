# Search design

Why search is designed the way it is. For field schemas and coverage numbers, see [docs/reference/data-sources.md](../reference/data-sources.md).

## Why RSEC over toolfinder as the default search source

shelley-bio has two metadata corpora: `toolfinder_meta.yaml` (AustralianBioCommons) and `rsec_meta.json.gz` (Research Software Ecosystem). RSEC is the default for `search` because its EDAM coverage is substantially higher:

| Field | toolfinder | RSEC bio.tools |
|---|---|---|
| entries | 714 | 34,130 |
| description | 72.5 % | 100 % |
| edam-operations | 69.7 % | 91.6 % |
| edam-topics | 69.7 % | 95.0 % |

Before searching, the 34,130 RSEC entries are filtered to only those with a matching container in the CVMFS cache (`galaxy_singularity_cache.json.gz`). This means every result returned by `search` can be installed immediately with `shelley-bio build`. The effective search corpus is the intersection of bio.tools metadata and CVMFS-hosted containers.

The CVMFS filter runs at search time rather than being pre-computed. The two artifacts (`rsec_meta.json.gz` and `galaxy_singularity_cache.json.gz`) update independently — a pre-filtered artifact would require coordinating both rebuild steps. Runtime cost is low (a list comprehension over ~34K entries), so runtime filtering is preferable for now.

## Why bio.tools only within the RSEC corpus

The RSEC content repository aggregates multiple upstream sources. Each tool directory can contain several JSON/YAML files — one per source. Only `*.biotools.json` files are ingested:

| Source | Files | Description | EDAM | Additive entries |
|---|---|---|---|---|
| `*.biotools.json` | 34,130 | 100 % | ops 92 %, topics 95 % | — (primary) |
| `*.galaxy.json` | 503 | 98 % | ops 94 %, topics 93 % | ~0 — subset of bio.tools |
| `*.bioconductor.json` | 2,402 | 100 % | — (uses `biocViews`) | ~815 not in bio.tools |
| `*.oeb.metrics.json` | 40,968 | — | — | performance metrics only |

**Galaxy** wrappers carry EDAM because they pull from bio.tools, but they represent only 503 of the same tools already in the 34,130-entry bio.tools set.

**Bioconductor** is the only source with meaningful additive coverage: ~815 R packages (34 % of 2,402) are absent from bio.tools. They have 100 % description coverage and the `biocViews` vocabulary (`RNASeq`, `SingleCell`, `DifferentialExpression`, …). The blocker is that `biocViews` is not EDAM — mixing the two vocabularies without relevance ranking would produce noisy results. Adding Bioconductor is a concrete future-work item.

**OEB metrics** are benchmarking measurements, not tool metadata.

## Why edam-inputs and edam-outputs are excluded from search

`edam-inputs` and `edam-outputs` are stored in the artifact but not matched against queries. Two reasons:

**Coverage is too sparse.** Across 34,130 bio.tools entries, inputs are populated for only 11.7 % and outputs for only 9.7 %. Matching against a field that is absent for 88–90 % of the corpus produces unpredictable results.

**Low coverage is not a non-popular tool artefact.** Among the 13 tools from the build regression matrix that are in RSEC, inputs are annotated for 54 % and outputs for 46 % — better than the corpus average, but still absent for widely-used tools like fastp, sambamba, samblaster, star-fusion, seurat, and MultiQC inputs. I/O is therefore unreliable even for high-profile tools.

When relevance ranking exists, matched I/O tokens could be weighted lower than operations or topics to limit noise. Until then, they are excluded.

## Why broad queries return many results

The search algorithm is OR-based token matching: a tool matches if *any* expanded query token appears in *any* of its searchable fields (name, description, edam-operations, edam-topics). OR means *any token can match, not all* — the opposite of how a web search works.

The scale of this effect (measured against the full unfiltered RSEC corpus of 34,130 entries):

| Query | Tokens after expansion | Results |
|---|---|---|
| `"variant calling"` | variant, calling | 2,213 |
| `"splice site prediction"` | splice, site, prediction | 7,260 |
| `"nanopore"` | nanopore | 198 |
| `"chip-seq"` | chip-seq, chipseq, chip, seq | 4,068 |
| `"chipseq"` | chipseq | 660 |

Two patterns stand out:

**Fewer tokens → fewer results.** `"nanopore"` (one token, 198 results) is far more specific than `"variant calling"` (two tokens, 2,213). `"splice site prediction"` expands to three tokens and returns more results than `"variant calling"`, not fewer.

**Hyphens multiply tokens.** `"chip-seq"` produces four tokens after hyphen expansion (chip-seq, chipseq, chip, seq), which is why it returns 6× more results than `"chipseq"` (one token). Omitting the hyphen is more specific.

## Why there is no relevance ranking in the current search

Results are sorted alphabetically. Relevance ranking (weighted scoring by field, match position, or term frequency) is not implemented because:

- Without ranking, adding synonym expansion or vocabulary mixing creates noise with no way to bury irrelevant matches.
- Alphabetical ordering is deterministic and transparent - results are the same on every run.
- The match provenance (which tokens matched which fields) is already tracked internally; this is the foundation for future ranking.

Weighted ranking over `name`, `description`, `edam-operations`, and `edam-topics` with different weights per field, is a possible next step. Ranking would also make the OR-match breadth useful rather than noisy: many weak matches would rank below a few strong ones.

## Future improvements

**Relevance ranking.** Weighted scoring by field (name match > EDAM match > description match) and match position is the highest-leverage improvement. It would turn the current broad OR-match into a usable ranked list without requiring a vocabulary change.

**bio.tools popularity signals.** bio.tools exposes citation count and usage metrics per tool. Incorporating these as a ranking signal would surface widely-used tools above obscure ones with the same keyword match.

**Semantic and NLP-based search.** Natural language queries (`"how do I QC my reads?"`) require semantic understanding beyond keyword matching. Options include embedding-based retrieval (RAG) or an MCP-connected language model that reformulates queries into technical terms before matching.
