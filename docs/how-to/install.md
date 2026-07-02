# How to install shelley

`shelley` ships preinstalled on [BioShell](https://github.com/AustralianBioCommons/BioShell)
VM images. This guide covers installing or updating it yourself.

There is a single install mechanism — `uv tool install` — which places `shelley`
on the system PATH. No virtual environment activation is ever required. For the
reasoning behind using `uv` (and not `pip`, `pipx`, or conda), see
[../explanation/install-design.md](../explanation/install-design.md).

## Which path is for you?

| You are… | Do this |
|---|---|
| On a BioShell VM with shelley already baked in | Nothing — just run `shelley …` (see the [tutorial](../tutorials/getting-started.md)) |
| Installing/updating on a workstation or VM manually | [Prerequisites](#prerequisites-install-uv) → [Install shelley](#install-shelley) (with `sudo`) |
| Baking shelley into a BioShell image (Ansible/Packer) | Same steps, run as root — see the `sudo` asides below |
| Wanting the latest shelley quickly on a VM not yet baked | [Install shelley](#install-shelley), appending `@branch` |
| A developer working on shelley | [developer-setup.md](developer-setup.md) |
| Running once, outside BioShell | [Run without installing (uvx)](#run-without-installing-uvx-experimental) |

The install is **path-dependent by design**: `uv` lives at `/opt/uv`, the tool
environment at `/opt/shelley`, and the `shelley` executable at
`/usr/local/bin/shelley`. This makes shelley available to every user on the VM.

## Prerequisites

- Linux (Ubuntu 22.04+ or compatible)
- `python3`, `curl`, and `git` (via the system package manager)

### Install `uv` (system-wide)

Install `uv` into `/opt/uv` so all users can invoke it. The installer will not
create the directory, so make it first:

```bash
sudo mkdir -p /opt/uv
curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/opt/uv sh
```

This places `uv` and `uvx` directly under `/opt/uv/`. Add that directory to the
system PATH by prepending it to the `PATH` line in `/etc/environment` so every
user can find it:

```
PATH="/opt/uv:/usr/local/sbin:/usr/local/bin:..."
```

Verify:

```bash
uv --version
```

> **Ansible/Packer:** the provisioner runs as root, so drop every `sudo` above.

`uv` manages its own Python interpreter and does not modify your system Python.

## Install shelley

Install shelley into the system tool location and link its executable onto the
PATH:

```bash
sudo env UV_TOOL_DIR=/opt UV_TOOL_BIN_DIR=/usr/local/bin \
  uv tool install git+https://github.com/Sydney-Informatics-Hub/shelley
```

`UV_TOOL_DIR=/opt` places the isolated tool environment at `/opt/shelley/` (uv
appends the package name); `UV_TOOL_BIN_DIR=/usr/local/bin` links the executable
to `/usr/local/bin/shelley`, where all users can invoke it.

Verify:

```bash
shelley --help
```

> **Ansible/Packer:** run the exact same command without `sudo` (the provisioner
> is already root). The canonical Ansible role and validation tasks live in the
> [BioShell repository](https://github.com/Sydney-Informatics-Hub/BioShell).

### Install a specific branch

To get the latest development version or a specific branch, append `@branch_name`:

```bash
sudo env UV_TOOL_DIR=/opt UV_TOOL_BIN_DIR=/usr/local/bin \
  uv tool install git+https://github.com/Sydney-Informatics-Hub/shelley@branch_name
```

### Upgrade

```bash
sudo env UV_TOOL_DIR=/opt UV_TOOL_BIN_DIR=/usr/local/bin uv tool upgrade shelley
```

### Uninstall

```bash
sudo env UV_TOOL_DIR=/opt UV_TOOL_BIN_DIR=/usr/local/bin uv tool uninstall shelley
```

## Run without installing (uvx, experimental)

If you are outside BioShell and only need shelley briefly, `uvx` runs it from a
cached, path-independent environment under `~/.local` without a persistent
install:

```bash
uvx --from git+https://github.com/Sydney-Informatics-Hub/shelley shelley find fastqc
```

> **Experimental — read-only commands only.** This path supports `find`,
> `versions`, and `search`. It does **not** support `build`, which needs the
> system `shpc`/Singularity layout that only a full VM install provides.

## Python version

`uv` creates a sandboxed Python environment that does not affect your system
Python. shelley requires Python 3.10 or later; uv selects the highest compatible
version it finds, or downloads one automatically. To pin a specific version, add
`--python`:

```bash
sudo env UV_TOOL_DIR=/opt UV_TOOL_BIN_DIR=/usr/local/bin \
  uv tool install "git+https://github.com/Sydney-Informatics-Hub/shelley" --python 3.11
```
