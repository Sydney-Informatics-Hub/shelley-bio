# Build design

Why the module builder is designed the way it is.

## Why local registry aliases are generated fresh from each SIF

`shelley build` has two paths depending on whether the requested version is in the upstream [shpc-registry](https://github.com/singularityhub/shpc-registry):

- **Version in upstream registry** — `shpc install` is called directly; the upstream registry's `aliases` field is used as-is.
- **Version absent from upstream** — shelley creates a local `container.yaml` under `/apps/local/`. As part of building that entry, it calls `extract_aliases` to diff the exact CVMFS SIF and generate the `aliases` field fresh. The local entry is never copied or inherited from another version of the same tool.

The reason for the no-inheritance rule is correctness. A concrete failure mode: if `star-fusion 1.0.0` inherited the local registry entry from `star-fusion 1.10.1`, the module would expose `salmon` as an alias — because `salmon` was present in the `1.10.1` container but absent from `1.0.0`. Any user running `module load star-fusion/1.0.0` and calling `salmon` would get a command-not-found error, or silently pick up a wrong binary from elsewhere on PATH.

The regression test `test_extract_aliases_star_fusion_1_0_0` explicitly asserts that `salmon` does not appear in the `1.0.0` alias list. `star-fusion 1.0.0` uses the local fallback path (`newly_created=True` in the regression matrix), so this test exercises the alias generation directly.

## Why guts_db exists — the conda subtraction problem

`shelley build` discovers tool aliases by diffing the tool's container against a database of base OS images (the [shpc-guts](https://github.com/singularityhub/shpc-guts) database). The diff returns files that are unique to the tool container — in theory, the tool's own executables.

In practice, BioContainers conda packages install the tool _and_ a full conda stack (`python`, `pip`, `conda`, `mamba`, ~90 conda-infrastructure binaries) into `/opt/conda/bin/` or `/usr/local/bin/`. The base OS images in shpc-guts contain neither conda nor these executables, so the diff returns all ~90 conda binaries as "unique" — inflating the alias list with entries like `mamba`, `pip3`, `activate`, and so on that are not tool-specific.

`shelley/data/guts_db/` is a supplementary manifest database in the same JSON format as shpc-guts. At runtime, `extract_aliases` merges `guts_db/` into the sparse-cloned shpc-guts working directory before running the diff. This adds conda-layer manifests (`anaconda/miniconda`, `continuumio/miniconda3`) to the subtraction set, removing ~90–100 spurious entries from every BioContainers alias list.

The two current manifests cover slightly different conda installations:

| Image | Covers |
|---|---|
| `anaconda/miniconda:latest` | `/opt/miniconda3/bin` |
| `continuumio/miniconda3:latest` | `/opt/conda/bin` — the standard BioContainers layer |

Without `continuumio/miniconda3`, roughly 100 extra conda-infrastructure executables appear as tool aliases.

## Local registry fallback — when and why it triggers

The upstream [shpc-registry](https://github.com/singularityhub/shpc-registry) does not carry every version of every tool. Older patch releases and some tools are present in CVMFS but absent from the registry.

When `shelley build` requests a version that has no upstream registry entry, it:

1. Creates a minimal `container.yaml` under `/apps/local/<uri>/` (the local shpc registry path).
2. Retries `shpc install` pointing at the local registry.

This is transparent to the user — it adds a few minutes to the build and is logged. The `newly_created` flag in the regression matrix (see [docs/reference/data-sources.md](../reference/data-sources.md)) records which tools consistently require a local entry.
