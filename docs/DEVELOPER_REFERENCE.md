# Developer reference

## Key paths

Paths involved in a `shelley-bio build` run, in the order they are touched:

| Path | Written by | Why it matters |
|------|-----------|----------------|
| `/cvmfs/singularity.galaxyproject.org/all/` | Galaxy Project (read-only) | Source SIF files; `shelley-bio build` reads from here, never writes |
| `/apps/local/` | `shelley-bio build` | Local shpc registry: `container.yaml` files for tool versions **absent** from the upstream shpc-registry; only created for the local path |
| `/apps/shpc/` | shpc | shpc install base; contains `modules/` (generated `module.lua` + wrapper scripts) and `containers/` |
| `/apps/Modules/modulefiles/<tool>/<version>.lua` | `shelley-bio build` | Symlink into `/apps/shpc/modules/`; this is what `module avail` and `module load <tool>/<version>` resolves |

## Data sources

### `toolfinder_meta.yaml`

Sourced from [AustralianBioCommons/finder-service-metadata](https://github.com/AustralianBioCommons/finder-service-metadata/blob/main/data/data.yaml).

Each record is a YAML object. Key fields used by shelley-bio:

| Field | Type | Notes |
|---|---|---|
| `id` | string | Primary tool identifier, used as lookup key |
| `name` | string | Human-readable display name |
| `biotools` | string | bio.tools identifier (may differ from `id`) |
| `biocontainers` | string | BioContainers name (used for container lookup) |
| `description` | string \| null | Free-text description; used in `search_by_description` |
| `edam-operations` | list \| null | Controlled vocab for what the tool does |
| `edam-topics` | list \| null | Controlled vocab for scientific domain |
| `homepage` | string \| null | Project homepage URL |
| `license` | string \| null | SPDX identifier |

Field coverage across 714 entries (measured 2026-06-02):

| Field | Coverage | Notes |
|---|---|---|
| `id` | 100 % | Always present |
| `name` | 100 % | Always present |
| `description` | 72.5 % | ~27 % of tools lack descriptions |
| `biotools` | 72.5 % | bio.tools cross-reference |
| `edam-operations` | 69.7 % | Lower than RSEC bio.tools (91.6 %) |
| `edam-topics` | 69.7 % | Lower than RSEC bio.tools (95.0 %) |
| `homepage` | 78.7 % | |
| `license` | 48.2 % | |
| `biocontainers` | 16.9 % | Used for container lookup, not search |
| `edam-inputs` | 22.5 % | |
| `edam-outputs` | 19.6 % | |

The search logic guards against `null` values throughout. EDAM coverage at
~70 % is notably lower than the RSEC bio.tools corpus (~92–95 %), which is a
key reason RSEC is the default search source.

**Reproduce these numbers** (reads the committed file, no network required):

```bash
python3 shelley_bio/scripts/assess_coverage.py toolfinder
```

### Research Software Ecosystem (RSEc)

The [research-software-ecosystem/content](https://github.com/research-software-ecosystem/content)
repository aggregates bio.tools, BioContainers, Bioconda, Galaxy wrappers, Bioconductor,
and other sources under one repo. Each tool gets its own directory under `data/` containing
one JSON/YAML file per upstream source.

#### Why bio.tools only?

The corpus is restricted to `*.biotools.json` (the bio.tools schema). The table below
summarises what each source type offers for *search* (numbers from the current master commit):

| Source | Files | Entries | Description | EDAM ops / topics | Additive entries |
|---|---|---|---|---|---|
| `*.biotools.json` | 34,130 | 34,130 | 100 % | 92 % / 95 % | — (primary) |
| `*.galaxy.json` | 503 | 503 | 98 % | 94 % / 93 % | ~0 (subset of bio.tools) |
| `*.bioconductor.json` | 2,402 | 2,402 | 100 % | — (uses `biocViews`) | ~815 not in bio.tools |
| `*.oeb.metrics.json` | 40,968 | 40,968 | — | — | performance metrics only |

**Galaxy** wrappers are a strict subset of bio.tools in practice — they carry EDAM
annotations because they pull from bio.tools, but there are only 503 of them and they
add no new tools.

**Bioconductor** is the only source that could meaningfully extend the corpus: ~815
packages (34 % of 2,402) are not in bio.tools. They have 100 % description coverage and
the `biocViews` controlled vocabulary (`RNASeq`, `SingleCell`, `DifferentialExpression`,
etc.), but `biocViews` is not EDAM — it would need separate normalisation to search
alongside EDAM fields without adding noise. This is tracked as future work.

**OEB metrics** files contain benchmarking/performance measurements (not metadata), so
they are not useful for search.

The bio.tools-only decision keeps the MVP field schema uniform (EDAM everywhere) and
avoids vocabulary-mixing noise. The 815 Bioconductor-only packages are the concrete gap
to close in a future iteration.

#### `rsec_meta.json.gz` — the search corpus

Field coverage measured over 34,130 bio.tools entries (RSEC commit `7ac28185`):

| Field | Searched? | Coverage | Notes |
|---|---|---|---|
| `name` | Yes | 100 % | Verbatim tool name |
| `description` | Yes | 100 % | Free-text description |
| `edam-operations` | Yes | 91.6 % | Flattened from `function[].operation[].term` |
| `edam-topics` | Yes | 95.0 % | Flattened from `topic[].term` |
| `license` | No | 45.1 % | SPDX identifier |
| `edam-inputs` | No | 11.7 % | Too sparse and noisy without ranking |
| `edam-outputs` | No | 9.7 % | Too sparse and noisy without ranking |
| `homepage` | No | 100 % | Stored for display |

`edam-inputs` and `edam-outputs` are stored in the artifact for future use but excluded
from matching. Their coverage (10–12 %) is far lower than the plan's 47–53 % estimate —
the actual numbers make the exclusion even more clearly correct.

**Reproduce these numbers** (reads the committed artifact, no network required):

```bash
python3 shelley_bio/scripts/assess_coverage.py rsec
```

To re-assess against the latest upstream data (re-fetches the RSEC repo, ~90 s):

```bash
shelley-bio-build-rsec --assess
```

#### Per-tool field coverage — regression tool matrix

The 15 tools from the `shelley-bio build` regression matrix were checked against
both corpora to test whether low I/O coverage is a non-popular tool artefact:

| Tool | In RSEC? | In TF? | ops | topics | inputs | outputs |
|---|---|---|---|---|---|---|
| fastqc | ✓ | ✓ | 3 | 3 | 5 | 2 |
| multiqc | ✓ | ✓ | 2 | 4 | — | 7 |
| salmon | ✓ | ✓ | 3 | 3 | 4 | 2 |
| bcftools | ✓ | ✓ | 2 | 4 | 3 | 3 |
| bwa-mem2 | ✓ | ✓ | 1 | 1 | 2 | — |
| fastp | ✓ | ✓ | 2 | 2 | — | — |
| sambamba | ✓ | ✓ | 2 | 3 | — | — |
| samblaster | ✓ | — | 1 | 3 | — | — |
| samtools | ✓ | ✓ | 7 | 4 | 4 | 4 |
| blast | ✓ | ✓ | 2 | 2 | 2 | 9 |
| star | ✓ | ✓ | 1 | 2 | 2 | 4 |
| star-fusion | ✓ | ✓ | 1 | 2 | — | — |
| seurat | ✓ | ✓ | — | 2 | — | — |
| parabricks | — | — | — | — | — | — |
| tidyverse | — | — | — | — | — | — |

`—` in **In RSEC / In TF** = not in that corpus. `—` in field columns = field is empty
for an entry that is present.

**Finding: low I/O coverage is not a non-popular tool artefact.**

Among the 13 tools found in RSEC, 7/13 (54 %) have some input annotation and 6/13
(46 %) have some output annotation — noticeably higher than the full-corpus average
(11.7 % / 9.7 %), confirming that well-known tools do get preferential curation.
However, 6–7 of these 13 widely-used tools still lack I/O annotations entirely
(fastp, sambamba, samblaster, star-fusion, seurat, and multiqc inputs). I/O coverage
is therefore unreliable even for high-profile tools, and the decision to exclude I/O
from search matching stands.

Notable absences and gaps:

- **parabricks** — NVIDIA proprietary GPU toolkit. Not in bio.tools or toolfinder;
  search will never surface it. Users must `find`/`build` by exact name.
- **tidyverse** — general-purpose R framework, not bioinformatics-specific. Absent
  from both corpora under any key (`tidyverse`, `r-tidyverse`). The `r-` prefix is
  a Bioconda package-name convention that bio.tools does not use.
- **samblaster** — in RSEC but not toolfinder.
- **seurat** — present in both corpora as `seurat` (not `r-seurat`; bio.tools uses
  the tool name, not the Bioconda package name). Has no operations and no I/O; only
  topics (`RNA-Seq`, `Transcriptomics`) are populated. Matches queries like "single
  cell" only if the description carries the tokens.
- **bwa-mem2** — inputs annotated (2 terms) but outputs absent in bio.tools.
- **multiqc** — outputs well-annotated (7 terms) but inputs deliberately absent,
  since MultiQC aggregates arbitrary tool output files.
- **star-fusion** — present in toolfinder as `star_fusion` (underscore). The
  reproduce script handles this variant automatically.

**Reproduce the per-tool lookup** (reads committed artifacts, no network required):

```bash
python3 shelley_bio/scripts/assess_regression_tools.py
```

Top-level artifact structure:

```json
{
  "generated_at": "2026-06-02T...",
  "source": "https://github.com/research-software-ecosystem/content",
  "source_ref": "master",
  "source_commit": "7ac28185...",
  "entry_count": 34130,
  "field_coverage": {
    "name": 100.0, "description": 100.0, "homepage": 100.0,
    "license": 45.1, "edam-operations": 91.6, "edam-topics": 95.0,
    "edam-inputs": 11.7, "edam-outputs": 9.7
  },
  "entries": [
    {
      "id": "bwa", "name": "BWA", "biotools_id": "bwa",
      "description": "...", "homepage": "...", "license": "GPL-3.0",
      "edam-operations": ["Read mapping", "Sequence alignment"],
      "edam-topics": ["Genomics", "Mapping"],
      "edam-inputs": ["Nucleic acid sequence", "FASTQ"],
      "edam-outputs": ["Sequence alignment map", "SAM"]
    }
  ]
}
```

#### Generating the artifact

The artifact is built by a committed, re-runnable script. Run from the repo root with
the virtual environment active:

```bash
# Preferred: shallow sparse-clone of data/ only (~1.2 GB on disk, ~90 s)
shelley-bio-build-rsec

# Or equivalently via python -m:
python -m shelley_bio.scripts.build_rsec_meta
```

The script sparse-clones `data/` from the RSEC content repo (falling back to a full
tarball download if git partial-clone is unavailable), parses every `*.biotools.json`
file, deduplicates by `biotoolsID`, and writes `shelley_bio/data/rsec_meta.json.gz`.

**Assessment mode** — print field-coverage statistics without writing anything:

```bash
shelley-bio-build-rsec --assess
```

**All options:**

| Option | Default | Purpose |
|---|---|---|
| `--assess` | off | Print field-coverage report and exit |
| `--method` | `sparse-clone` | `sparse-clone` or `tarball` |
| `--ref` | `master` | Branch/tag to fetch |
| `--out` | `shelley_bio/data/rsec_meta.json.gz` | Output path |
| `--workdir` | auto (temp) | Persistent work directory for debugging |
| `-v` | off | Debug logging |

**Regenerate and commit after upstream updates:**

```bash
shelley-bio-build-rsec
git add shelley_bio/data/rsec_meta.json.gz
git commit -m "DEV: Regenerate rsec_meta.json.gz from RSEC content"
```

### `galaxy_singularity_cache.json.gz`

A cache is used to enable fast look ups for `shelley-bio` read-only functions (`find`, `search`, `versions`). To generate the cache, run:

```bash
python3 shelley_bio/cache/build_cache.py
```

A gzipped JSON snapshot of the CVMFS Singularity image cache, generated by scanning
`/cvmfs/singularity.galaxyproject.org/all`. Top-level structure:

```json
{
  "generated_at": "2026-01-28T03:40:51.706534+00:00",
  "cvmfs_root": "/cvmfs/singularity.galaxyproject.org/all",
  "entry_count": 118594,
  "entries": [
    {
      "entry_name": "fastqc:0.12.1--hdfd78af_0",
      "tool_name": "fastqc",
      "tag": "0.12.1--hdfd78af_0",
      "path": "/cvmfs/singularity.galaxyproject.org/all/fastqc:0.12.1--hdfd78af_0",
      "size_bytes": 293400576,
      "mtime": 1697123456.0
    },
    ...
  ]
}
```

The `tool_name` field is the index key used to join with metadata. Tags follow
the Bioconda convention: `<version>--<build_string>`.

This should be regenerated periodically.

### Local registry behaviour

When a tool/version is absent from the upstream shpc-registry, `shelley-bio build`
creates a local `container.yaml` under `/apps/local/<uri>/` and retries.

**Aliases are always version-specific.** Each build call regenerates the `aliases` field
from the exact CVMFS SIF being installed via `guts diff`. Aliases are never inherited
from a previously-installed version of the same tool — doing so would produce wrapper
scripts for binaries absent in the older container (e.g. `salmon` appearing in a
`star-fusion 1.0.0` module because it was extracted from `1.10.1`).

### `shelley_bio/data/guts_db/` — supplementary guts manifest database

When `extract_aliases` diffs a CVMFS SIF to discover a tool's executables, it compares
the container against the [shpc-guts](https://github.com/singularityhub/shpc-guts) database
of base OS images (ubuntu, alpine, busybox, rockylinux). That database contains only plain
OS images — it has no conda layer.

BioContainers conda packages install everything (python, pip, conda, mamba, and the actual
tool) into `/opt/conda/bin/` or `/usr/local/bin/`. Without subtracting conda's own
executables, the diff returns every conda-infrastructure binary as a "unique alias",
inflating the alias list with ~90 entries that are not tool-specific.

**The fix:** `shelley_bio/data/guts_db/` is a supplementary manifest database in the same
JSON format as shpc-guts. At runtime, `extract_aliases` merges this directory into the
sparse-cloned shpc-guts tmpdir before running the diff, so conda plumbing is subtracted
automatically.

#### Generating a new base image manifest

To add a new base image (or refresh an existing one), run `guts manifest` on a system
with Singularity:

```bash
# -c singularity  — use Singularity to pull and inspect the image
# -i fs           — include the full filesystem listing (required for set-subtraction)
# -i paths        — include executables found on $PATH (required for unique_paths output)
# -o              — write JSON to this file
guts manifest -c singularity -i fs -i paths -o miniconda.json anaconda/miniconda
```

Move the output into the correct namespace path under `guts_db/`:

```
shelley_bio/data/guts_db/
└── docker.io/
    └── anaconda/
        └── miniconda/
            └── latest.json    ← the file generated above
```

Commit the JSON. It is bundled with the package (hatchling includes `shelley_bio/**`
by default) and loaded automatically — no code changes required for new base images.

#### Current manifests

| Image | Install path | Purpose |
|-------|-------------|---------|
| `anaconda/miniconda:latest` | `/opt/miniconda3/bin` | Base conda tooling |
| `continuumio/miniconda3:latest` | `/opt/conda/bin` | Python-3 conda layer used by BioContainers |

Both are kept because they cover slightly different conda installations.
BioContainers packages install into `/opt/conda/bin`; without the `continuumio/miniconda3`
manifest, ~100 extra conda-infrastructure executables appear as tool aliases.

To refresh or add a new manifest (Singularity must be on PATH):

```bash
# anaconda/miniconda
uv run guts manifest -c singularity -i fs -i paths \
    -o shelley_bio/data/guts_db/docker.io/anaconda/miniconda/latest.json \
    anaconda/miniconda

# continuumio/miniconda3
uv run guts manifest -c singularity -i fs -i paths \
    -o shelley_bio/data/guts_db/docker.io/continuumio/miniconda3/latest.json \
    continuumio/miniconda3
```

**When to refresh:** when a base image's conda version makes a major jump (e.g.
Python 3.10 → 3.12) and tool manifests suddenly gain or lose many entries.

## Regression tool matrix

The 14 tools below are the canonical regression set for `shelley-bio build`.
Each row captures the exact CVMFS version, whether a local registry entry must be created
(`newly_created=True` means the upstream shpc-registry does not carry this build), and
the expected key aliases that the Lmod module should expose.

The `newly_created` flag is verified by `test_ensure_local_registry_entry_newly_created`
and `test_ensure_local_registry_entry_upstream_known` in `tests/test_cvmfs_builder.py`.

| Tool | Canonical version (CVMFS) | In upstream registry | newly_created | Key aliases |
|------|---------------------------|---------------------|---------------|-------------|
| fastqc | `0.12.1--hdfd78af_0` | ✓ | False | `fastqc` |
| multiqc | `1.19--pyhdfd78af_0` | ✓ | False | `multiqc` |
| salmon | `1.10.1--h7e5ed60_0` | ✓ | False | `salmon` |
| bcftools | `1.23.1--hb2cee57_0` | ✓ | False | `bcftools` |
| bwa-mem2 | `2.2.1--he70b90d_8` | ✓ | False | `bwa-mem2` |
| fastp | `0.20.0--hdbcaa40_0` | ✗ (only ≥0.23.x) | True | `fastp` |
| sambamba | `0.8.1--hadffe2f_1` | ✗ (only ≥1.0.x) | True | `sambamba` |
| samblaster | `0.1.24--hc9558a2_3` | ✗ (only ≥0.1.25) | True | `samblaster` |
| samtools | `1.19--h50ea8bc_0` | ✗ (only `0.1.19`) | True | `samtools` |
| blast | `2.5.0--hc0b0e79_3` | ✗ | True | `blastn`, `blastp`, `blastx` |
| star | `2.7.11a--h0033a41_0` | ✓ | False | `STAR` |
| star-fusion | `1.0.0--pl5.22.0_0` | ✗ (only ≥1.9.1) | True | `STAR` (not `salmon`) |
| parabricks | n/a | ✗ | n/a | not in CVMFS — raises `ValueError` |
| seurat | n/a | ✗ | n/a | not in CVMFS — raises `ValueError` |

> **star-fusion 1.0.0 regression note:** `salmon` must NOT appear as an alias. It was
> incorrectly present when aliases were inherited from a newer build of the same tool.
> The fix (always regenerate aliases from the specific SIF) is tested by
> `test_extract_aliases_star_fusion_1_0_0` (requires Singularity on PATH to run).

## Known issues

### `shpc` must be on PATH

All `shelley-bio build` operations and the CVMFS integration tests call `shpc` as a
subprocess. `shpc` is installed at `/opt/shpc/bin/shpc` and is not on the default PATH —
it must be loaded before use:

```bash
module load shpc
```

In environments without the module system (e.g. GitHub Actions CI), the test
`test_run_shpc_install_missing_cvmfs_path` will fail with `FileNotFoundError` rather than
being skipped. This is a tracked known issue; the test is intentionally left as a
documented failure until shpc path discovery is added to the builder.

## Developer setup

### First-time environment setup

The project uses [uv](https://github.com/astral-sh/uv) for dependency management and requires the local `guts` library (singularity branch) to be checked out as a sibling directory.

Install `uv` if not already present:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# 1. Clone both repos
git clone https://github.com/Sydney-Informatics-Hub/shelley-bio.git
git clone https://github.com/Sydney-Informatics-Hub/guts.git

# Change to the SIH dev branch that supports singularity
cd guts && git checkout singularity && cd ..

# 2. Create and activate the virtual environment
cd shelley-bio
uv venv .venv
source .venv/bin/activate

# 3. Install shelley-bio in editable mode with dev extras
#    uv resolves the local ../guts path from pyproject.toml automatically
uv pip install -e ".[dev]"

# 4. Load required modules
module load singularity shpc

# 5. Verify
shelley-bio
pytest --collect-only # check pytest is installed correctly, but do not run
```

> **Why `uv` and not plain `pip`?** `pyproject.toml` declares `container-guts` as a local path
> dependency (`[tool.uv.sources]`). Plain `pip install -e .` ignores this table and will
> try to pull `container-guts` from PyPI instead.

### Keeping the environment up to date

After pulling changes that modify `pyproject.toml` or `guts/`:

```bash
uv pip install -e ".[dev]"   # re-sync dependencies
```

No need to recreate the venv unless Python itself changes.

## Running tests

The test suite is split into three groups:

| Group | What it tests | Mark | Runs in CI? |
|---|---|---|---|
| General unit tests | Registry lookups, shpc install logic, CLI rendering | *(none)* | Yes |
| CVMFS tests | Version resolution against real container files | `cvmfs` | No (skipped) |
| Network tests | `find` buildable cross-check against GitHub shpc-registry | `network` | Yes (requires outbound curl) |

### Automated CI (GitHub Actions)

Every push to a pull request runs the general unit tests and network tests automatically. The CVMFS tests are **skipped** in CI because the CVMFS filesystem is not available in the GitHub Actions environment. You will see them marked as `s` (skipped) in the test output — this is expected.

### Running tests locally (BioShell)

Run the full suite from inside a BioShell session where `/cvmfs/singularity.galaxyproject.org/all` is mounted — `cvmfs`-marked tests auto-enable when the path exists:

```bash
source .venv/bin/activate
pytest                              # all tests
pytest -v --tb=short                # verbose with short tracebacks
pytest tests/test_cvmfs_builder.py  # single file
```

To exclude network tests when offline:

```bash
pytest -m "not network"
```

Tests marked `@pytest.mark.cvmfs` will run automatically when the CVMFS path is detected, and be skipped when it is not. Tests marked `@pytest.mark.network` always run unless explicitly excluded — they make outbound curl requests to the [shpc-registry](https://github.com/singularityhub/shpc-registry) on GitHub. Both markers are defined in `conftest.py`.

### `find` buildable tests (`tests/test_find_buildable.py`)

Exercises `_handle_find_tool()` with 21 real-world tool arguments covering all supported input formats (`tool:version--hash`, `tool/version`, bare name, R/Bioconductor packages). Four categories:

- **Smoke** — all 21 inputs return valid JSON (offline, always runs)
- **Buildable cross-check** (`network`) — for full-tag inputs (e.g. `fastqc:0.12.1--hdfd78af_0`), asserts that the `buildable` field in `find` output matches `full_tag in get_registry_tags()` called independently
- **Version presence** — version-only inputs (e.g. `samtools/1.19`) resolve to a known container in the local index (offline)
- **R packages** — confirms R/Bioconductor tools return no Singularity containers (offline)

Cross-check tests skip automatically when the requested version is not in the top-5 most recent results (expected for older tags like `blast:2.5.0`).
