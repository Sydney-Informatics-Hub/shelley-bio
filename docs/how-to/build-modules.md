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

## Build multiple modules — batch operations

> **Placeholder:** Full batch how-to coming once `shelley-bio-batch` implementation is stable.

The `shelley-bio-batch` command accepts multiple tool specs and builds them in sequence:

```bash
shelley-bio-batch samtools fastqc bowtie2
shelley-bio-batch samtools/1.21 fastqc/0.12.1
```

## Requirements

- `shpc` must be on PATH (`module load shpc`)
- CVMFS must be mounted at `/cvmfs/singularity.galaxyproject.org/`
- Write access to `/apps/Modules/modulefiles/` — shelley-bio will prompt for sudo if needed
