# How to set up your development environment

## First-time setup

The project uses [uv](https://github.com/astral-sh/uv) for dependency management.

Development is generally done on BioShell, so install `uv` system-wide into `/opt/uv` if it
is not already present. See [Install `uv`](install.md#install-uv-system-wide) in
the install guide.

```bash
# 1. Clone the repository
git clone https://github.com/Sydney-Informatics-Hub/shelley.git
cd shelley

# 2. Install shelley and dev dependencies
uv sync --extra dev

# 3. Load required modules
module load singularity shpc

# 4. Verify
uv run shelley --help
uv run pytest --collect-only   # confirm pytest is installed; do not run yet
```

> **No venv activation needed.** `uv sync` creates a managed `.venv` automatically. Run all commands through `uv run` — you never need to activate the environment manually.

> **Why `uv` and not plain `pip`?** See [../explanation/install-design.md](../explanation/install-design.md).

## Keeping the environment up to date

After pulling changes that modify `pyproject.toml`:

```bash
uv sync --extra dev
```

## Running tests

The test suite has two groups:

| Group | What it tests | Mark | Runs in CI? |
|---|---|---|---|
| General unit tests | Registry lookups, shpc install logic, CLI rendering, interactive mode | *(none)* | Yes |
| CVMFS tests | Version resolution against real container files | `cvmfs` | No (skipped) |

### CI (GitHub Actions)

Every push to a pull request runs general unit tests automatically using `uv run pytest`. CVMFS tests are skipped — the CVMFS filesystem is not available in GitHub Actions.

### Running locally (BioShell)

Run from inside a BioShell session where `/cvmfs/singularity.galaxyproject.org/all` is mounted — `cvmfs`-marked tests enable automatically when the path exists:

```bash
uv run pytest                              # all tests
uv run pytest -v --tb=short               # verbose with short tracebacks
uv run pytest tests/test_cvmfs_builder.py # single file
uv run pytest -m "not network"            # exclude network tests when offline
```
