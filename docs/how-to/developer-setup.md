# How to setup your development environment

## First-time environment setup

The project uses [uv](https://github.com/astral-sh/uv) for dependency management and requires the local `guts` library (singularity branch) checked out as a sibling directory.

Install `uv` if not already present:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# 1. Clone both repos
git clone https://github.com/Sydney-Informatics-Hub/shelley-bio.git
git clone https://github.com/Sydney-Informatics-Hub/guts.git

# Switch to the SIH dev branch that supports Singularity
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
shelley-bio --help
pytest --collect-only   # confirm pytest is installed; do not run yet
```

> **Why `uv` and not plain `pip`?** `pyproject.toml` declares `container-guts` as a local path dependency (`[tool.uv.sources]`). Plain `pip install -e .` ignores this table and tries to pull `container-guts` from PyPI instead.

## Keeping the environment up to date

After pulling changes that modify `pyproject.toml` or `guts/`:

```bash
uv pip install -e ".[dev]"
```

No need to recreate the venv unless Python itself changes.

## Running tests

The test suite has three groups:

| Group | What it tests | Mark | Runs in CI? |
|---|---|---|---|
| General unit tests | Registry lookups, shpc install logic, CLI rendering | *(none)* | Yes |
| CVMFS tests | Version resolution against real container files | `cvmfs` | No (skipped) |
| Network tests | `find` buildable cross-check against GitHub shpc-registry | `network` | Yes |

### CI (GitHub Actions)

Every push to a pull request runs general unit tests and network tests automatically. CVMFS tests are skipped — the CVMFS filesystem is not available in GitHub Actions. Skipped tests appear as `s` in the output.

### Running locally (BioShell)

Run from inside a BioShell session where `/cvmfs/singularity.galaxyproject.org/all` is mounted — `cvmfs`-marked tests enable automatically when the path exists:

```bash
source .venv/bin/activate
pytest                              # all tests
pytest -v --tb=short                # verbose with short tracebacks
pytest tests/test_cvmfs_builder.py  # single file
pytest -m "not network"             # exclude network tests when offline
```

### `find` buildable tests (`tests/test_find_buildable.py`)

Exercises `_handle_find_tool()` with 21 real-world tool arguments covering all supported input formats (`tool:version--hash`, `tool/version`, bare name, R/Bioconductor packages). Four categories:

- **Smoke** — all 21 inputs return valid JSON (offline, always runs)
- **Buildable cross-check** (`network`) — for full-tag inputs, asserts the `buildable` field matches `full_tag in get_registry_tags()` called independently
- **Version presence** — version-only inputs resolve to a known container in the local index (offline)
- **R packages** — confirms R/Bioconductor tools return no Singularity containers (offline)

Cross-check tests skip automatically when the requested version is not in the top-5 most recent results (expected for older tags like `blast:2.5.0`).
