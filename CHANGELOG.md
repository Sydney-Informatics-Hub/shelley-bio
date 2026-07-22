# Changelog

All notable changes to shelley are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-22

Pinned version for BioShell launch.

### Added

- `shelley find <tool> -v` — lists every individual container build (one row per
  `--hash`) with the date modified, install status and the full CVMFS container path.
- [EXPERIMENTAL] `shelley build <tool> -i` (`--interactive`) — opens an interactive session to
  curate the aliases a module exposes (deselect, rename, and add) for both
  upstream and local builds.
- Update check — on startup shelley compares its version against the `main`
  branch and prints upgrade instructions when a newer release is available. The
  result is cached for a day and fails silently on any network error.
- `shelley update` — upgrades shelley in place. It detects whether the install is
  system-wide (`/opt/uv/tools`) or per-user and runs the matching
  `uv tool upgrade shelley` for you.

### Changed

- Merged the `versions` command into `find`. Run `shelley find <tool> -v`
  (or `--verbose`) to see the full, paginated list of container versions.

### Removed

- `versions` command. Use `shelley find <tool> -v` instead.

### Fixed

- `shpc` and `singularity` are now loaded when required i.e. during `shelley build`.

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

[0.2.0]: https://github.com/Sydney-Informatics-Hub/shelley/releases/tag/v0.2.0
[0.1.0]: https://github.com/Sydney-Informatics-Hub/shelley/releases/tag/v0.1.0
