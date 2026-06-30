# Shelley Bio

**A bioinformatics tool finder and module builder for CVMFS-hosted containers on [BioShell](https://github.com/Sydney-Informatics-Hub/bioimage)**

Shelley-bio helps researchers using [BioShell](https://github.com/AustralianBioCommons/BioShell) virtual machine images on Nectar research cloud platforms discover, query, and deploy bioinformatics software from CVMFS (CernVM File System) repositories. It provides both interactive and programmatic interfaces for finding tools, building Lmod modules, and managing containerised workflows.

## Features

- **Tool Discovery**: Find bioinformatics tools by name or search by description
- **Container Management**: Query available container versions from CVMFS
- **Module Building**: Automatically generate Lmod modules for tools, individually or in batch
- **Interactive CLI**: Guided REPL for exploring and installing tools

## Quick Start

### Installation

`shelley-bio` ships with [BioShell](https://github.com/AustralianBioCommons/BioShell).

To install or update shelley-bio manually:

| Goal | Guide |
|---|---|
| Install on a workstation or VM | [docs/how-to/install-locally.md](docs/how-to/install-locally.md) |
| Deploy via Ansible (BioShell) | [docs/how-to/install-ansible.md](docs/how-to/install-ansible.md) |
| Developer environment | [docs/how-to/developer-setup.md](docs/how-to/developer-setup.md) |

### Basic Usage

```bash
# Find a specific tool
shelley-bio find fastqc

# Search by function (in development)
shelley-bio search "quality control"

# List available versions
shelley-bio versions samtools

# Build an Lmod module
shelley-bio build samtools

# Build a specific version
shelley-bio build samtools/1.21

# Interactive mode
shelley-bio interactive
```

## Documentation

| Type | File | What it covers |
|---|---|---|
| Tutorial | [docs/tutorials/getting-started.md](docs/tutorials/getting-started.md) | First-time walkthrough |
| How-to | [docs/how-to/install-locally.md](docs/how-to/install-locally.md) | Install without a venv |
| How-to | [docs/how-to/install-ansible.md](docs/how-to/install-ansible.md) | Ansible deployment for BioShell VMs |
| How-to | [docs/how-to/find-and-search.md](docs/how-to/find-and-search.md) | find, search, versions |
| How-to | [docs/how-to/build-modules.md](docs/how-to/build-modules.md) | build and batch operations |
| How-to | [docs/how-to/maintain-corpus.md](docs/how-to/maintain-corpus.md) | Update data artifacts |
| How-to | [docs/how-to/developer-setup.md](docs/how-to/developer-setup.md) | Dev environment and tests |
| Reference | [docs/reference/cli.md](docs/reference/cli.md) | All CLI commands |
| Reference | [docs/reference/data-sources.md](docs/reference/data-sources.md) | Data artifacts and schemas |
| Explanation | [docs/explanation/search-design.md](docs/explanation/search-design.md) | Why the search is designed this way |
| Explanation | [docs/explanation/build-design.md](docs/explanation/build-design.md) | Why the build is designed this way |

## Architecture

Shelley Bio is organised as a modular Python package:

```
shelley_bio/
├── client/          # CLI entry point (thin routing)
├── commands/        # One module per user-facing command
├── builder/         # CVMFS module building functionality
├── script/          # Run-once to generate cached data
├── search/          # Tool metadata search sources
└── utils/           # Shared utilities, cache, rendering, style
```

## Requirements

- Python 3.10+
- Access to CVMFS repositories (typically `/cvmfs/singularity.galaxyproject.org/`)
- Lmod (for module management)
- Singularity/Apptainer (for container execution)
