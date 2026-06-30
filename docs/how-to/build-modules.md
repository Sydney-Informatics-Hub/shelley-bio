# How to build Lmod modules

## Build a single module

```bash
shelley-bio build <tool>
```

shelley-bio resolves the most recent available version from CVMFS, runs `shpc install`, and creates a symlink under `/apps/Modules/modulefiles/<tool>/`. After a successful build:

```bash
module load <tool>
```

### Specify a version

```bash
shelley-bio build samtools/1.19
shelley-bio build star/2.7.11a
```

Version strings follow the Bioconda convention — see `shelley-bio versions <tool>` for exact tags available on CVMFS.

### What happens when a tool is absent from the upstream shpc-registry

If the requested version has no entry in the [shpc-registry](https://github.com/singularityhub/shpc-registry), shelley-bio creates a local `container.yaml` under `/apps/local/<uri>/` and retries the install. This typically adds a few extra minutes to the build. For the reasoning behind this design, see [docs/explanation/build-design.md](../explanation/build-design.md).

## Build multiple modules — file input

Pass a plain-text file of tool specs (one per line) to `shelley-bio build`:

```bash
shelley-bio build tools.txt
```

**File format** — each line is a tool spec in the same format accepted by the
single-build command. Blank lines and `#` comments are ignored:

```
# Core alignment tools
samtools/1.21
bwa
bowtie2/2.5.1  # pinned for reproducibility

fastqc
```

shelley-bio detects that the argument is a file, parses it, and runs the batch
builder — showing a progress table and results summary for each tool.

## Requirements

- `shpc` must be on PATH (`module load shpc`)
- CVMFS must be mounted at `/cvmfs/singularity.galaxyproject.org/`
- Write access to `/apps/Modules/modulefiles/` — shelley-bio will prompt for sudo if needed
