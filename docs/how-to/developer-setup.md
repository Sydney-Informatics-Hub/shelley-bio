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

## Preparing a release

### Branch model

- **`main`** is the **default branch** and holds **released** code. It is updated
  from `dev` at release time and each release is tagged `vX.Y.Z`. The install
  guide points end users at `@main` (latest release) or a specific tag
  (reproducible).
- **`dev`** carries **active development** — feature work merges here first, then
  into `main` at release time. Installing from `@dev` gets the latest, possibly
  unstable code.

### Version is single-sourced

The version lives in **one** place — `__version__` in
[`shelley/__init__.py`](../../shelley/__init__.py). `pyproject.toml` reads it
dynamically (`[tool.hatch.version]`), and `shelley --version` reports it. Never
edit a version string anywhere else.

### Update check

`shelley --version`, `shelley help`, and bare `shelley` tell the user when a
newer version is available and how to upgrade. The check
([`shelley/utils/update_check.py`](../../shelley/utils/update_check.py)) fetches
`__version__` from `shelley/__init__.py` on the **`main`** branch (raw GitHub),
compares it to the running version. If `main` is ahead, prompt to the user to
run `shelley update`. 

The update check is cached for a day (`~/.cache/shelley/update_check.json`),
times out fast, and fails silently, so it never slows or breaks a command.
Users can silence it by running `export SHELLEY_NO_UPDATE_CHECK=1` in the shell.

Because the signal is the released version string, bumping `__version__` on
`main` at release time (below) is what triggers the alert for existing installs.
The repo/branch it reads are the clearly marked constants at the top of
`update_check.py`.

`shelley update` ([`shelley/commands/update.py`](../../shelley/commands/update.py))
performs the upgrade: it detects whether the running shelley is a system-wide
(`/opt/uv/tools`) or per-user install and runs the matching `uv tool upgrade
shelley`. The system-install path constants there must stay in sync with the
`### Upgrade` section of [`install.md`](install.md#upgrade).

### Release checklist

On `dev`:

1. Bump the version (follow [SemVer](https://semver.org/)): `__version__` in
   `shelley/__init__.py` (the source `pyproject.toml` reads), plus the `version`
   and `date-released` fields in `CITATION.cff`.
2. Update `CHANGELOG.md`: rename the `Unreleased` section to the new version with
   today's date, and add the release link at the bottom.
3. Confirm the build and version resolve:
   ```bash
   uv build                     # builds shelley-<version>.{whl,tar.gz}
   uv run shelley --version     # should print the new version
   uv run pytest -m "not cvmfs" # tests green
   ```
4. Commit and open a PR into `main`; merge once CI passes.

On `main`, after merge:

5. Tag and push:
   ```bash
   git checkout main && git pull
   git tag v0.1.0
   git push origin v0.1.0
   ```
6. Create the GitHub release from the tag, pasting the CHANGELOG entry as notes.
