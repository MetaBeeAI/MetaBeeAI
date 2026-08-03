.. MetaBeeAI documentation main index

MetaBeeAI
=========

.. toctree::
   :hidden:

   installation
   quickstart
   guide/index
   reference/index
   developer/index
   citations

.. card::
   :class-card: landing-hero

   MetaBeeAI is an open-source, modular pipeline for extracting structured information
   from scientific papers for systematic review and meta-analysis in biology.

   Use these docs to install MetaBeeAI, configure reproducible processing runs,
   understand the major modules, and navigate the full workflow from raw papers to
   structured outputs.

   Start with :doc:`Installation <installation>` and :doc:`Quick Start <quickstart>`.
   If you already have the package running, jump straight to
   :doc:`Configuration <guide/configuration>`, :doc:`Workflow <guide/workflow>`, or
   :doc:`Reference <reference/index>`.

If you use MetaBeeAI in your research, please cite:

   Parkinson, R. H., Cerbone, H., Mieskolainen, M., Cao, S., Wilson, A. D., Albacete, S., et al. (2026).
   MetaBeeAI: An AI pipeline for structured evidence extraction from biological literature.
   *Ecological Informatics*, *96*, Article 103813.
   https://doi.org/10.1016/j.ecoinf.2026.103813

See :doc:`Citations <citations>` for the full author list and BibTeX.

Explore The Docs
----------------

.. grid:: 1 1 2 3
   :gutter: 3

   .. grid-item-card:: Install MetaBeeAI
      :link: installation
      :link-type: doc
      :class-card: landing-card landing-card--warm

      Set up the package, configure required keys, and verify that the CLI is available.

   .. grid-item-card:: Quick Start
      :link: quickstart
      :link-type: doc
      :class-card: landing-card landing-card--warm

      Follow the shortest path from installation to processing a set of PDFs.

   .. grid-item-card:: User Guide
      :link: guide/index
      :link-type: doc
      :class-card: landing-card

      Read the end-to-end guides for setup, configuration, workflow, benchmarking, and troubleshooting.

   .. grid-item-card:: Reference
      :link: reference/index
      :link-type: doc
      :class-card: landing-card

      Find API docs, submodule overviews, and lower-level reference material in one place.

   .. grid-item-card:: Developer Guide
      :link: developer/index
      :link-type: doc
      :class-card: landing-card

      Find contribution, configuration-development, and documentation-maintenance guides for working on MetaBeeAI itself.

   .. grid-item-card:: Citations
      :link: citations
      :link-type: doc
      :class-card: landing-card landing-card--warm

      Find the preferred citation, full author list, and BibTeX entry for MetaBeeAI.

Pipeline Guides
---------------

.. grid:: 1 1 2 3
   :gutter: 3

   .. grid-item-card:: Setup
      :link: guide/setup
      :link-type: doc
      :class-card: landing-card

      Prepare local directories, expected file layout, and the project structure used by the pipeline.

   .. grid-item-card:: Configuration
      :link: guide/configuration
      :link-type: doc
      :class-card: landing-card

      Understand configuration files, environment variables, defaults, and precedence.

   .. grid-item-card:: Workflow
      :link: guide/workflow
      :link-type: doc
      :class-card: landing-card

      Follow the end-to-end processing flow from raw PDFs to structured outputs.

   .. grid-item-card:: Benchmarking
      :link: guide/benchmarking
      :link-type: doc
      :class-card: landing-card

      Compare model behaviour and evaluate extraction quality across runs.

   .. grid-item-card:: Data Analysis
      :link: guide/analysis
      :link-type: doc
      :class-card: landing-card

      Work with processed outputs and downstream analysis steps after extraction is complete.

   .. grid-item-card:: Troubleshooting
      :link: guide/troubleshooting
      :link-type: doc
      :class-card: landing-card

      Diagnose installation issues, pipeline failures, and common runtime problems.

Reference And Internals
-----------------------

.. grid:: 1 1 2 2
   :gutter: 3

   .. grid-item-card:: Submodules
      :link: submodule/index
      :link-type: doc
      :class-card: landing-card

      Read higher-level descriptions of the major pipeline components and what each one is responsible for.

   .. grid-item-card:: PDF Processing Pipeline
      :link: submodule/process_pdfs
      :link-type: doc
      :class-card: landing-card

      Understand how PDFs are split, merged, deduplicated, and prepared for downstream extraction.

   .. grid-item-card:: LLM Pipeline
      :link: submodule/metabeeai_llm
      :link-type: doc
      :class-card: landing-card

      Review the prompts, extraction flow, and higher-level orchestration behind the LLM stage.

   .. grid-item-card:: Query And Analysis Tools
      :link: submodule/query_database
      :link-type: doc
      :class-card: landing-card

      Find the query and analysis layer used for working with processed outputs.

Development
-----------

.. grid:: 1 1 2 3
   :gutter: 3

   .. grid-item-card:: Developer Guide
      :link: developer/index
      :link-type: doc
      :class-card: landing-card landing-card--warm

      Set up a development environment, run checks, and navigate the project’s developer documentation.

   .. grid-item-card:: Config Development
      :link: guide/config_development
      :link-type: doc
      :class-card: landing-card

      Extend the configuration layer safely and consistently.

   .. grid-item-card:: Documentation
      :link: guide/documentation
      :link-type: doc
      :class-card: landing-card

      Build, debug, and maintain the Sphinx documentation stack.
