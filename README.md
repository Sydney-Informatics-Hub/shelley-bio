# Shelley Bio

**A bioinformatics tool finder and module builder for CVMFS-hosted containers on [BioShell](https://github.com/Sydney-Informatics-Hub/bioimage)**

Shelley-bio helps researchers using [BioShell](https://github.com/AustralianBioCommons/BioShell) virtual machine images on Nectar research cloud platforms discover, query, and deploy bioinformatics software from CVMFS (CernVM File System) repositories. It provides both interactive and programmatic interfaces for finding tools, building Lmod modules, and managing containerised workflows.

## Features

- **Tool Discovery**: Find bioinformatics tools by name or browse the full catalog
- **Container Management**: Query available container versions from CVMFS
- **Module Building**: Automatically generate Lmod modules for tools
- **Interactive CLI**: User-friendly command-line interface
- **MCP Integration**: Model Context Protocol server for AI assistants

## Quick Start

### Installation

`shelley-bio` is installed as part of [BioShell](https://github.com/AustralianBioCommons/BioShell).

For development instructions, see [docs/how-to/developer-setup.md](docs/how-to/developer-setup.md).

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
| How-to | [docs/how-to/find-and-search.md](docs/how-to/find-and-search.md) | find, search, versions, list |
| How-to | [docs/how-to/build-modules.md](docs/how-to/build-modules.md) | build and batch operations |
| How-to | [docs/how-to/maintain-corpus.md](docs/how-to/maintain-corpus.md) | Update data artifacts |
| How-to | [docs/how-to/developer-setup.md](docs/how-to/developer-setup.md) | Dev environment and tests |
| Reference | [docs/reference/cli.md](docs/reference/cli.md) | All CLI commands |
| Reference | [docs/reference/mcp.md](docs/reference/mcp.md) | MCP tool schemas and resources |
| Reference | [docs/reference/data-sources.md](docs/reference/data-sources.md) | Data artifacts and schemas |
| Explanation | [docs/explanation/search-design.md](docs/explanation/search-design.md) | Why the search is designed this way |
| Explanation | [docs/explanation/build-design.md](docs/explanation/build-design.md) | Why the build is designed this way |

## Architecture

Shelley Bio is organised as a modular Python package:

```
shelley_bio/
├── client/          # CLI interface and client logic
├── server/          # MCP server for AI integration
├── builder/         # CVMFS module building functionality
├── scripts/         # Batch operations and utilities
└── utils/           # Shared utilities and constants
```

## Requirements

- Python 3.10+
- Access to CVMFS repositories (typically `/cvmfs/singularity.galaxyproject.org/`)
- Lmod (for module management)
- Singularity/Apptainer (for container execution)
