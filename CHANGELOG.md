# Changelog

All notable changes to shelley are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-03

First tagged release.

### Added

- `find` — look up a bioinformatics tool by name and show its description and
  recent buildable container versions.
- `search` — find tools by function/description across the RSEC and toolfinder
  corpora.
- `versions` — list available container versions for a tool, newest first.
- `build` — generate Lmod modules for CVMFS-hosted containers, individually or
  in batch from a file.
- `interactive` — guided REPL for exploring and installing tools.
- `--version` flag on the CLI.
- Installation guide covering system-wide (`uv tool install` into `/opt`),
  per-user, and `uvx` (experimental) paths.

[0.1.0]: https://github.com/Sydney-Informatics-Hub/shelley/releases/tag/v0.1.0
