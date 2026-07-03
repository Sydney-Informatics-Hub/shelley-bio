# Why shelley installs with uv

This explains why shelley is installed with `uv` rather than `pip`, `pipx`, or
conda, and not distributed as a container. For the actual install steps, see
[../how-to/install.md](../how-to/install.md).

## The core constraint: a git-sourced dependency

shelley depends on `container-guts`, but not the version on PyPI - it needs a
specific branch of the [SIH guts fork](https://github.com/Sydney-Informatics-Hub/guts.git)
that carries the Singularity support shelley requires. `pyproject.toml` declares
this with a `[tool.uv.sources]` override:

```toml
[tool.uv.sources]
container-guts = { git = "https://github.com/Sydney-Informatics-Hub/guts.git", branch = "singularity" }
```

Any installer that does not understand `[tool.uv.sources]` ignores this table and
tries to pull `container-guts` from PyPI, which lacks the Singularity and CVMFS support.
This single fact rules out most conventional installers.

Because `uv` resolves the git source directly from `pyproject.toml`, there is no
separate step to install `container-guts` first. A single `uv tool install` handles
it. This keeps the Ansible role that bakes shelley into BioShell images simpler.

## The second constraint: don't break system Python

Recent Ubuntu/Debian mark the system Python as externally managed (PEP 668), so
`pip install` into it is blocked or actively breaks the OS's own packages. The
usual workaround (a virtual environment) has to be created and activated before
every use, which is awkward on VMs where conflicting python versions must be used in parallel. `uv` avoids both: `uv tool install`
puts shelley in an isolated, uv-managed environment and links its executable onto
the PATH, so it is always available without activation and never touches the
system Python.

## Method comparison

| Method | No explicit venv | System Python safe | Resolves git deps | Notes |
|---|---|---|---|---|
| `uv tool install` (recommended) | Yes | Yes | Yes | Best for end users and BioShell VMs |
| `uv sync` + `uv run` | No (managed, hidden) | Yes | Yes | For developers — see [../how-to/developer-setup.md](../how-to/developer-setup.md) |
| `pipx install` | Yes | Yes | **No** | Cannot resolve `[tool.uv.sources]` git entries |
| `pip install` (system) | Yes | **No** | **No** | Pollutes system Python; not supported |
| conda | No (conda env) | Yes | **No** | Not packaged for conda-forge |

## Why not pipx?

`pipx` is the conventional venv-free installer for Python CLIs, and it works for
pure-PyPI packages. But it has no equivalent of uv's `[tool.uv.sources]` override,
so it cannot inject the correct `container-guts` git source at install time.

## Why not conda?

shelley is not packaged for conda-forge or bioconda. A conda environment also
still requires activation, so it does not meet the goal of a no-venv,
always-on-PATH install.

## Why not a container?

Distributing shelley as a container was considered and would work, but it was
rejected: it forces users to run shelley from inside a container, and adds
maintenance burden and an extra layer to debug through. A uv-managed install on
the host is lighter and simpler for the BioShell use case.

## Why uv tool install specifically

`uv tool install` installs shelley into a uv-managed isolated environment and
places the `shelley` executable on the PATH — no venv creation or activation, and
the system Python is left untouched. On a multi-user BioShell VM the same command,
pointed at `/opt` via `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR`, makes shelley available to
every user with no per-user setup.


