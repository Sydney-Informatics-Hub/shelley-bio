# How to maintain data artifacts

Steps for keeping the bundled data files up to date. For the rationale behind what each artifact contains and why, see [docs/reference/data-sources.md](../reference/data-sources.md) and [docs/explanation/search-design.md](../explanation/search-design.md).

## Regenerate `rsec_meta.json.gz`

The RSEC search corpus is built from the [research-software-ecosystem/content](https://github.com/research-software-ecosystem/content) repository. Regenerate after upstream updates:

```bash
# From the repo root, with uv venv active:
shelley-build-rsec
```

This sparse-clones `data/` from the RSEC repo (~90 s), parses every `*.biotools.json` file, and writes `shelley/data/rsec_meta.json.gz`.

```bash
# Force tarball download instead of sparse clone:
shelley-build-rsec --method tarball

# Check field-coverage statistics without writing anything:
shelley-build-rsec --assess

# Fetch a specific branch/tag:
shelley-build-rsec --ref main
```

After regenerating:

```bash
git add shelley/data/rsec_meta.json.gz
git commit -m "DEV: Regenerate rsec_meta.json.gz from RSEC content"
```

## Run field-coverage assessment

Check how well-populated each metadata field is across both corpora (reads committed artifacts, no network required):

```bash
uv run python shelley/scripts/assess_coverage.py           # both sources
uv run python shelley/scripts/assess_coverage.py rsec
uv run python shelley/scripts/assess_coverage.py toolfinder
```

## Check per-tool field coverage for regression tools

Cross-reference the 15-tool regression matrix against both corpora:

```bash
uv run python shelley/scripts/assess_regression_tools.py
```

## Refresh a guts base-image manifest

The `shelley/data/guts_db/` directory holds Singularity manifests used to subtract conda infrastructure from tool containers. Refresh when a base image's conda version makes a major jump.

Requires Singularity on PATH e.g. `module load singularity`:

```bash
# anaconda/miniconda
uv run guts manifest -c singularity -i fs -i paths \
    -o shelley/data/guts_db/docker.io/anaconda/miniconda/latest.json \
    anaconda/miniconda

# continuumio/miniconda3
uv run guts manifest -c singularity -i fs -i paths \
    -o shelley/data/guts_db/docker.io/continuumio/miniconda3/latest.json \
    continuumio/miniconda3
```

Move new manifests under the correct namespace path (`docker.io/<org>/<image>/<tag>.json`) then commit.

## Regenerate `galaxy_singularity_cache.json.gz`

The CVMFS container index is built by scanning the Galaxy Singularity CVMFS mount directly. Run on a system where CVMFS is mounted:

```bash
uv run python shelley/cache/build_cache.py
```

Then commit the updated file.
