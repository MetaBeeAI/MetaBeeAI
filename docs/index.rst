.. MetaBeeAI documentation main index

MetaBeeAI
=========

.. toctree::
   :hidden:

   installation
   quickstart
   api/index
   guide/index
   submodule/index

.. card::
   :class-card: landing-hero

   MetaBeeAI is an open-source, modular pipeline for extracting structured information
   from scientific papers for systematic review and meta-analysis in biology.

   Use these docs to install MetaBeeAI, configure reproducible processing runs,
   understand the major modules, and navigate the full workflow from raw papers to
   structured outputs.

   Start with :doc:`Installation <installation>` and :doc:`Quick Start <quickstart>`.
   If you already have the package running, jump straight to
   :doc:`Configuration <guide/configuration>`, :doc:`Workflow <guide/workflow>`, or the
   :doc:`API Reference <api/index>`.

Explore The Docs
----------------

.. grid:: 1 1 2 2
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

   .. grid-item-card:: App Pipeline
      :link: guide/index
      :link-type: doc
      :class-card: landing-card

      Read the end-to-end guides for setup, configuration, workflow, benchmarking, and troubleshooting.

   .. grid-item-card:: API Reference
      :link: api/index
      :link-type: doc
      :class-card: landing-card

      Browse the Python package interfaces, generated function docs, and module-level reference.

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

   .. grid-item-card:: Contributing
      :link: guide/contributing
      :link-type: doc
      :class-card: landing-card landing-card--warm

      Set up a development environment, run checks, and follow the project workflow.

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
