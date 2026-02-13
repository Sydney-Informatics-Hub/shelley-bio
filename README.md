# Shelley Bio

**A powerful bioinformatics tool finder and module builder for CVMFS-hosted containers**

Shelley Bio helps researchers discover, query, and deploy bioinformatics software from CVMFS (CernVM File System) repositories. It provides both interactive and programmatic interfaces for finding tools, building Lmod modules, and managing containerized workflows.

## ✨ Features

- 🔍 **Tool Discovery**: Search for bioinformatics tools by name or function
- 📦 **Container Management**: Query available container versions from CVMFS
- 🧩 **Module Building**: Automatically generate Lmod modules for tools
- 🖥️ **Interactive CLI**: User-friendly command-line interface
- 🚀 **Batch Operations**: Build multiple modules simultaneously
- 🔌 **MCP Integration**: Model Context Protocol server for AI assistants

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/shelley-bio/shelley-bio.git
cd shelley-bio

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Basic Usage

```bash
# Find a specific tool
shelley-bio find fastqc

# Search by function
shelley-bio search "quality control"

# List available tools
shelley-bio list 20

# Build an Lmod module
shelley-bio build samtools

# Build a specific version
shelley-bio build samtools/1.21

# Interactive mode
shelley-bio interactive
```

### Batch Operations

```bash
# Build multiple modules at once
shelley-bio-batch samtools fastqc bowtie2

# Build specific versions
shelley-bio-batch samtools/1.21 fastqc/0.12.1
```

## 📖 Documentation

- [Command Reference](docs/COMMAND_REFERENCE.md) - Complete CLI documentation
- [Developer Reference](docs/DEVELOPER_REFERENCE.md) - API and development guide
- [Query Guide](docs/HOW_TO_QUERY.md) - Advanced search techniques

## 🏗️ Architecture

Shelley Bio is organized as a modular Python package:

```
shelley_bio/
├── client/          # CLI interface and client logic
├── server/          # MCP server for AI integration
├── builder/         # CVMFS module building functionality
├── scripts/         # Batch operations and utilities
└── utils.py         # Shared utilities and constants
```

## 🔧 Requirements

- Python 3.8+
- Access to CVMFS repositories (typically `/cvmfs/singularity.galaxyproject.org/`)
- Lmod (for module management)
- Singularity/Apptainer (for container execution)

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🚨 Migration from bio-finder

If you're migrating from the original bio-finder project, the core functionality remains the same with these improvements:

### What's New
- **Professional packaging**: Installable via pip
- **Improved CLI**: Better user experience and error handling  
- **Modular design**: Clean separation of concerns
- **Enhanced documentation**: Comprehensive guides and references
- **Batch operations**: Efficient multi-tool module building

### Command Changes
| bio-finder | shelley-bio |
|------------|-------------|
| `./biofinder find fastqc` | `shelley-bio find fastqc` |
| `./biofinder build samtools` | `shelley-bio build samtools` |
| `./build-modules.sh tool1 tool2` | `shelley-bio-batch tool1 tool2` |

All functionality from bio-finder is preserved and enhanced in Shelley Bio.

---

**Made with ❤️ for the bioinformatics community**