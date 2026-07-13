# Run an nf-core RNA-seq pipeline on BioShell

This tutorial walks you through running a real RNA-seq analysis on a BioShell virtual machine, using `shelley` to supply the software containers the pipeline needs - without downloading a single one.

This is not a tutorial about RNA-seq or bioinformatics itself, and you do not need to be a biologist, bioinformatician, or programmer to follow along. The focus is the mechanics of running a pipeline on BioShell. A handful of terms come up along the way:

**Glossary**

- **RNA-seq** - a common experiment that measures which genes are switched on, or how gene activity differs across experimental conditions.
- **Pipeline** - a pre-built recipe that chains many analysis tools together in the right order. We use [nf-core](https://nf-co.re), a community collection of trusted [Nextflow](https://www.nextflow.io) pipelines.
- **Container** - a self-contained, reproducible package of one tool and everything it needs to run. A pipeline uses many. Normally Nextflow *downloads* ("pulls") each one, which is slow.
- **CVMFS** (the CernVM File System) - a read-only filesystem mounted on BioShell that already hosts thousands of containers. Instead of pulling, you point the pipeline at these, and `shelley` helps you find the right path.

For more on BioShell, CVMFS, and shelley, see the project [README](../../README.md).

## Learning objectives

By the end of this tutorial you will have:

1. Loaded the modules a pipeline needs (`nextflow`, `nf-core`, `singularity`).
2. Run a small pipeline and watched Nextflow pull containers.
3. Launched `nf-core/rnaseq` on a real dataset and hit a missing-container error.
4. Used `shelley find <tool> -vv` to locate that container's path on CVMFS.
5. Added the path to a Nextflow config and resumed the run.
6. Repeated this loop yourself to finish a full RNA-seq run **without pulling containers**.

## Prerequisites

You have logged into a BioShell virtual machine on Nectar. BioShell is preconfigured with the `shelley` utility and a mounted CVMFS which holds all the containers required.

<!-- PLACEHOLDER: how the learner obtains/accesses the example RNA-seq dataset (path on the
     VM, download command, or shared location). -->

## Step 1: Load the tools you need

Running an nf-core pipeline normally means setting up several tools by hand. BioShell has
them ready as loadable modules.

See what is available:

```bash
module avail
```

```
-------------------------------- /apps/Modules/modulefiles --------------------------------
   R/4.3.3           jupyter/2026.07     nf-core/4.0.2        snakemake/7.32.4
   ansible/2.16.3    nextflow/26.04.4    rstudio/2026.06.0

-------------------------------- /opt/Modules/modulefiles ---------------------------------
   shpc    singularity
```

Load the nextflow and nf-core modules required to run the pipelines.

```bash
module load nextflow nf-core
```

Run `module avail` again. An `(L)` now marks each loaded module:

```
   nf-core/4.0.2 (L)  nextflow/26.04.4 (L)
```

> **Note:** On a standard machine you would install and configure each of these yourself -
> see the [nf-core environment setup guide](https://nf-co.re/docs/get_started/environment_setup/overview).
> On BioShell it is a single `module load`.

## Step 2: Warm up with a tiny pipeline

Before the real analysis, run nf-core's tiny `demo` pipeline to see how a pipeline behaves.
The `test` profile uses a miniature built-in dataset, so this finishes quickly.

```bash
nextflow run nf-core/demo -profile test,singularity --outdir results
```

If you see this, the `singularity` module is not loaded:

```
bash: line 1: singularity: command not found
```

Load it and run the command again:

```bash
module load singularity
nextflow run nf-core/demo -profile test,singularity --outdir results
```

The pipeline now runs to completion.

> **Note:** Watch the output as it runs. Nextflow **pulls** (downloads) a container image
> for each step before it can start. Here the containers are tiny, so it is quick. In a
> real pipeline like `nf-core/rnaseq`, there are many larger tools, and pulling every one
> adds up. In the next steps you will skip pulling entirely by pointing the pipeline at
> containers already on CVMFS.

## Step 3: Preview the containers the pipeline needs

`nf-core/rnaseq` chains together many tools - quality checks, alignment, quantification,
and a summary report - and each runs in its own container. Before running anything, list
exactly which containers the pipeline will use with `nextflow inspect`.

<!-- PLACEHOLDER: describe the dataset briefly (organism, number of samples) so the learner
     knows what they are analysing. -->

You point the pipeline at your data with a **samplesheet** (a CSV listing your samples) and
tell it which genome to use. A config file (`-c`) is where you will record container paths
later in this tutorial.

```bash
nextflow inspect nf-core/rnaseq \
  -profile singularity \
  --input samplesheet.csv \
  --outdir results \
  -c custom_bioshell.config
```

<!-- PLACEHOLDER: the real command - samplesheet path, genome/reference params
     (e.g. --genome, --fasta, --gtf), and the config file name/path. -->

This prints the container each step will use. Keep this list handy - it is the set of
containers you may need to point at CVMFS in the steps that follow.

<!-- PLACEHOLDER: paste a short example of the nextflow inspect output. -->

## Step 4: Launch nf-core/rnaseq

Now start the real analysis on your dataset:

```bash
nextflow run nf-core/rnaseq \
  -profile singularity \
  --input samplesheet.csv \
  --outdir results \
  -c custom_bioshell.config
```

## Step 5: Read the missing-container error

The run stops with an error because one of the containers it needs is not available yet.
**This is expected** - you will fix it in the next step.

Read the error and note *which tool's* container is missing:

<!-- PLACEHOLDER: paste the actual error text, and highlight the tool name in it. -->

```
<!-- PLACEHOLDER: missing-container error output -->
```

The important part is the name of the tool (for example, `fastqc`). That is what you will
look up next.

## Step 6: Find the container with shelley

Ask shelley where that tool's container lives on CVMFS. The `-vv` flag lists every
individual build **and** its full container path:

```bash
shelley find <tool> -vv
```

<!-- PLACEHOLDER: replace <tool> with the missing tool from Step 4. -->

shelley prints a table like this:

```
 Versions              Buildable   Installed   Container Path
 0.12.1--hdfd78af_0    ✓           ✗           /cvmfs/singularity.galaxyproject.org/all/fastqc:0.12.1--hdfd78af_0
 ...
```

- **Buildable:** ✓ means the version is in the upstream registry; ✗ means it can still be
  used but may take longer to build.
- **Installed:** ✓ means it is already a loadable module on this system.
- **Container Path:** the exact `/cvmfs/...` image path. **This is the line you need.**

Copy the path for the version you want.

> **Note:** `find` is case-insensitive and handles hyphens and underscores -
> `shelley find STAR` and `shelley find star` return the same result.

## Step 7: Point your config at the CVMFS path

Open your config file and tell the pipeline to use that CVMFS image for the step that
failed. Add a `withName` block that matches the process and sets its `container`:

```groovy
process {
    withName: '<PROCESS_NAME>' {
        container = '/cvmfs/singularity.galaxyproject.org/all/<tool>:<tag>'
    }
}
```

<!-- PLACEHOLDER: the real process name (e.g. FASTQC) and the container path from Step 5,
     matching how the user's config is structured. -->

Save the file, then resume the run. The `-resume` flag reuses the steps that already
succeeded, so you only continue from where it stopped:

```bash
nextflow run nf-core/rnaseq \
  -profile singularity \
  --input samplesheet.csv \
  --outdir results \
  -c custom_bioshell.config \
  -resume
```

## Step 8: Repeat until the run completes

The run may stop again on the *next* tool whose container it needs. You now know the
pattern - repeat Steps 5-7 for each one:

1. Read the error to find the tool name.
2. `shelley find <tool> -vv` to get its CVMFS path.
3. Add a `withName` block to your config and `-resume`.

<!-- PLACEHOLDER: note roughly how many containers the learner will resolve, or confirm
     this is self-directed until the run finishes. -->

Each loop is faster than pulling would be, because CVMFS already hosts the image - shelley
just tells you where it is.

## Step 9: Check your results

When the run finishes, your outputs are in the `--outdir` folder (`results/` above).

<!-- PLACEHOLDER: point to the specific results the learner should look at. -->

Open the **MultiQC report** (`results/multiqc/`) in a browser - it is a single
human-readable page summarising quality and results across all your samples.

## What you did

You ran a complete RNA-seq pipeline on BioShell and resolved every container it needed by
locating it on CVMFS with `shelley find -vv` and pointing your Nextflow config at it. The
run finished **without pulling a single container**, because CVMFS already hosts them, you
just told the pipeline where to look.

The loop you learned: *run → read the missing-container error → `shelley find <tool> -vv` →
add the path to your config → resume* - works for any nextflow pipeline on BioShell.

## Next steps

- [docs/tutorials/getting-started.md](getting-started.md): finding and building tools with shelley
- [docs/how-to/find-and-search.md](../how-to/find-and-search.md): all options for `find` and `search`
- [docs/how-to/build-modules.md](../how-to/build-modules.md): installing tools as reusable modules
- [docs/reference/cli.md](../reference/cli.md): complete shelley command reference
- [nf-core/rnaseq documentation](https://nf-co.re/rnaseq): pipeline parameters and outputs
