# Installing nf-core/rnaseq on BioShell

This tutorial walks you through how to install an nf-core pipeline, and run an example RNA-seq analysis.

* Extremely brief, understandable-by-all, background on what nf-core/nextflow pipelines are, why it's powerful for running rnaseq analysis

## Learning objectives

* Understand the benefits of BioShell, CVMFS and shelley 
* Assess and compare thepros/cons of the setup steps using BioShell/CVMFS/shelley vs without (e.g. in a standard analysis environment)
    * CVMFS allows users to not have pull containers. In multi-step bioinformatics workflows, you would have to pull multiple, and waste time waiting for containers being pulled
* Process an example transcriptomics dataset through a multistep bioinformatics pipeline
* Familiarity navigating the bioshell and it's fit-for-purpose utility shelley
* Familiarity with CVMFS and how it helps with with bioinformatics analysis


## Preqrequisites

- Access to a BioShell with `shelley` installed

## Scratch

nf-core requires several steps to complete the environment setup. THe BioShell comes with these configured by default, and can be module loaded see https://nf-co.re/docs/get_started/environment_setup/overview

module avail

-------------------------------- /apps/Modules/modulefiles --------------------------------
   R/4.3.3           jupyter/2026.07     nf-core/4.0.2        snakemake/7.32.4
   ansible/2.16.3    nextflow/26.04.4    rstudio/2026.06.0

-------------------------------- /opt/Modules/modulefiles ---------------------------------
   shpc    singularity

If the avail list is too long consider trying:

"module --default avail" or "ml -d av" to just list the default modules.
"module overview" or "ml ov" to display the number of modules for each name.

Use "module spider" to find all possible modules and extensions.
Use "module keyword key1 key2 ..." to search for all possible modules matching any of the
"keys".

module load shpc singularity nextflow
ubuntu@shelley-dev-sa:~$ module avail

------------------------------ /apps/Modules/modulefiles ------------------------------
   R/4.3.3           jupyter/2026.07         nf-core/4.0.2        snakemake/7.32.4
   ansible/2.16.3    nextflow/26.04.4 (L)    rstudio/2026.06.0

------------------------------ /opt/Modules/modulefiles -------------------------------
   shpc (L)    singularity (L)

  Where:
   L:  Module is loaded

* Now should show the tools we need are avaialble

## TODO:

etc/skel/data
* samplesheet
* minimal fastq
* bioshell.config
