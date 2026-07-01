# How to install shelley-bio via Ansible

This guide describes recommendations for deploying shelley-bio onto BioShell VMs via Ansible. The actual role implementation lives in the [BioShell repository](https://github.com/Sydney-Informatics-Hub/BioShell).

## Overview

BioShell VM images are built using [Packer](https://www.packer.io/) with Ansible as the provisioner. `shelley` is one of several tools installed during the image build. The BioShell repository contains the canonical Ansible role and validation tasks.

## Installation approach

The recommended approach is to install `uv` on the target VM and then use `uv tool install` to deploy `shelley`. This avoids virtual environments while keeping `shelley` isolated from the system Python.

### High-level steps

1. **Install system prerequisites:** `python3`, `curl`, and `git` via the system package manager.

2. **Install `uv`:** create `/opt/uv` first (the installer will not create it), then run the official installer script with `UV_INSTALL_DIR` pointing there:
   ```bash
   mkdir -p /opt/uv
   curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/opt/uv sh
   ```
   This places `uv` and `uvx` directly under `/opt/uv/`. In a Packer/Ansible context the provisioner runs as root so no `sudo` is needed.

3. **Add `/opt/uv` to the system PATH:** prepend it to the `PATH` line in `/etc/environment` so all users can invoke `uv`:
   ```
   PATH="/opt/uv:/usr/local/sbin:/usr/local/bin:..."
   ```

4. **Install `shelley`:** set `UV_TOOL_DIR=/opt` so uv places the tool environment at `/opt/shelley-bio/` (uv appends the package name), and `UV_TOOL_BIN_DIR=/usr/local/bin` to place the executable alias where users can invoke it:
   ```bash
   UV_TOOL_DIR=/opt UV_TOOL_BIN_DIR=/usr/local/bin \
     uv tool install git+https://github.com/Sydney-Informatics-Hub/shelley-bio
   ```
   The tool environment goes to `/opt/shelley-bio/`. uv links the executable into `/usr/local/bin/shelley-bio`.

5. **Validate:** confirm the binary runs correctly:
   ```bash
   /usr/local/bin/shelley-bio --help
   ```
   Let stderr through — if the install failed, you want to see the error output, not suppress it.

## Key considerations

**Python version**: uv selects or downloads a compatible Python 3.10+ interpreter without touching the system Python. The system `python3` is unaffected.

**Multi-user VMs**: Setting `UV_TOOL_DIR=/opt` and `UV_TOOL_BIN_DIR=/usr/local/bin` makes shelley available to all users on the VM without any per-user setup.

## References

- [uv tool documentation](https://docs.astral.sh/uv/concepts/tools/)
- [BioShell repository](https://github.com/Sydney-Informatics-Hub/BioShell) contains the Ansible role and validation tasks
- [install-locally.md](install-locally.md) for single-user installations without Ansible
