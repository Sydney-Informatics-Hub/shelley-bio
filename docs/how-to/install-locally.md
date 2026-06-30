# How to install shelley-bio locally

This guide covers installing shelley-bio as a command-line tool on a Linux workstation or BioShell VM. No virtual environment activation is required.

## Prerequisites

- Linux (Ubuntu 22.04+ or compatible)
- `uv` 0.4 or later

Install `uv` if it is not already present:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env   # adds ~/.local/bin to PATH for the current shell
```

Verify:

```bash
uv --version
```

`uv` manages its own Python interpreter — it does not modify your system Python.

## Recommended method — `uv tool install`

`uv tool install` installs shelley-bio into a uv-managed isolated environment and places the `shelley-bio` executable on your PATH. No venv creation or activation is needed.

```bash
uv tool install "shelley-bio @ git+https://github.com/Sydney-Informatics-Hub/shelley-bio.git"
```

Verify:

```bash
shelley-bio --help
```

If `shelley-bio` is not found, run:

```bash
uv tool update-shell   # modifies ~/.bashrc / ~/.zshrc automatically
```

Then reopen your terminal or run `source ~/.bashrc`.

## Upgrade

```bash
uv tool upgrade shelley-bio
```

## Uninstall

```bash
uv tool uninstall shelley-bio
```

## Method comparison

| Method | No explicit venv | System Python safe | Resolves git deps | Notes |
|---|---|---|---|---|
| `uv tool install` (recommended) | Yes | Yes | Yes | Best for end users and BioShell VMs |
| `uv sync` + `uv run` | No (managed, hidden) | Yes | Yes | For developers — see [developer-setup.md](developer-setup.md) |
| `pipx install` | Yes | Yes | No | Cannot resolve `[tool.uv.sources]` git entries |
| `pip install` (system) | Yes | **No** | No | Pollutes system Python; not supported |
| conda | No (conda env) | Yes | No | Not packaged for conda-forge |

### Why not pipx?

`pipx` is the conventional venv-free installer for Python CLIs. It works for pure-PyPI packages, but shelley-bio depends on a specific branch of `container-guts` (from the [SIH guts fork](https://github.com/Sydney-Informatics-Hub/guts.git)) that is not available on PyPI. `pipx` has no equivalent of uv's `[tool.uv.sources]` override, so it cannot inject the correct git source at install time.

### Why not conda?

shelley-bio is not packaged for conda-forge or bioconda. A conda environment still requires activation, so it does not meet the no-venv goal.

## Python version

`uv tool install` creates a sandboxed Python environment that does not affect your system Python. shelley-bio requires Python 3.10 or later; uv selects the highest compatible version it can find or downloads one automatically if none is present.

To pin a specific interpreter:

```bash
uv tool install "shelley-bio @ git+..." --python 3.11
```
