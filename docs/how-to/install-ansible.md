# How to install shelley-bio via Ansible

This guide describes the approach for deploying shelley-bio onto BioShell VMs via Ansible. The actual role implementation lives in the [BioShell repository](https://github.com/Sydney-Informatics-Hub/BioShell). This document contains a high-level overview and recommendations of steps to include when building the BioShell image.

## Overview

BioShell VM images are built using [Packer](https://www.packer.io/) with Ansible as the provisioner. `shelley` is one of several tools installed during the image build. The BioShell repository contains the canonical Ansible role and validation tasks.

## Installation approach

The recommended approach is to install `uv` on the target VM and then use `uv tool install` to deploy `shelley`. This avoids virtual environments while keeping `shelley` isolated from the system Python.

### High-level steps

1. **Install system prerequisites:** `python3`, `curl`, and `git` via the system package manager.

2. **Install `uv`:** use the official installer script:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   Place the `uv` binary in a system-wide location (e.g. `/usr/local/bin/uv`) so all users can invoke it.

3. **Install `shelley`:** use `uv tool install` with a `--tool-dir` pointing to a stable system location such as `/opt/shelley`. This keeps the managed environment out of any user's home directory:
   ```
   uv tool install \
     "shelley @ git+https://github.com/Sydney-Informatics-Hub/shelley.git" \
     --tool-dir /opt/shelley
   ```
   The `shelley` executable will be at `/opt/shelley/bin/shelley`.

4. **Create a system-wide launcher:** place a minimal wrapper at `/usr/local/bin/shelley-bio` that delegates to the uv-managed binary. This makes the command available to all users regardless of their PATH. TODO: Provide an example. `uv run shelley` as `shelley`?

5. **Validate:** confirm `/usr/local/bin/shelley --help` exits 0. TODO: what about 2&> dev/null?

## Key considerations

**Python version**: uv selects or downloads a compatible Python 3.10+ interpreter without touching the system Python. The system `python3` is unaffected.

**Multi-user VMs**: The installation under `/opt/shelley/` and the launcher at `/usr/local/bin/shelley` make shelley available to all users on the VM without any per-user setup.

## References

- [uv tool documentation](https://docs.astral.sh/uv/concepts/tools/)
- [BioShell repository](https://github.com/Sydney-Informatics-Hub/BioShell) contains the Ansible role and validation tasks
- [install-locally.md](install-locally.md) for single-user installations without Ansible
