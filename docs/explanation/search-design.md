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

## Why there is no relevance ranking in the current search

The current `search` implementation returns results sorted alphabetically. Relevance ranking (weighted scoring by field, match position, or term frequency) is not implemented because:

- Without ranking, adding synonym expansion or vocabulary mixing creates noise with no way to bury irrelevant matches.
- Alphabetical ordering is deterministic and transparent — results are the same on every run.
- The match provenance (which tokens matched which fields) is already tracked internally; this is the foundation for future ranking.

Weighted ranking over `name`, `description`, `edam-operations`, and `edam-topics` — with different weights per field — is the intended next step.
