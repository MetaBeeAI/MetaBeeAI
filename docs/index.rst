.. MetaBeeAI documentation main index

MetaBeeAI
=========

MetaBeeAI is a literature-processing pipeline for extracting, reviewing, benchmarking,
and analyzing structured information from scientific PDFs using LLM and Vision AI
workflows.

If you are new to the project, start with installation and the quick start. If you are
already running the pipeline, jump directly to configuration, workflow, or the API
reference.

.. toctree::
   :hidden:

   installation
   quickstart
   api/index
   guide/index
   submodule/index

Start Here
----------

:doc:`Installation Guide <installation>`
   Install MetaBeeAI, set up your environment, and configure required API keys.

:doc:`Quick Start Guide <quickstart>`
   Run the shortest path from install to processing a set of PDFs.

:doc:`Setup Guide <guide/setup>`
   Prepare local directories, project structure, and expected inputs.

:doc:`Configuration Guide <guide/configuration>`
   Understand configuration files, environment variables, and parameter precedence.

Use The Pipeline
----------------

:doc:`Pipeline Overview <guide/pipeline_overview>`
   Understand the major stages of the MetaBeeAI workflow and how data moves through it.

:doc:`Complete Workflow <guide/workflow>`
   Follow the end-to-end process from raw PDFs to structured outputs.

:doc:`Benchmarking <guide/benchmarking>`
   Evaluate extraction quality and compare LLM behaviour across runs.

:doc:`Data Analysis <guide/analysis>`
   Work with processed outputs and downstream analysis steps.

:doc:`Troubleshooting Guide <guide/troubleshooting>`
   Diagnose common installation, configuration, and runtime issues.

Reference
---------

:doc:`API Reference <api/index>`
   Browse module, class, and function documentation for the Python package.

:doc:`Submodules <submodule/index>`
   Read higher-level descriptions of the major pipeline components and their roles.

Key module guides:

- :doc:`PDF Processing Pipeline <submodule/process_pdfs>`
- :doc:`LLM Pipeline <submodule/metabeeai_llm>`
- :doc:`LLM Review Software <submodule/llm_review_software>`
- :doc:`LLM Benchmarking <submodule/llm_benchmarking>`
- :doc:`Query Database - Data Extraction and Analysis <submodule/query_database>`

Development
-----------

:doc:`Contributing to MetaBeeAI <guide/contributing>`
   Set up a development environment, run checks, and follow the project workflow.

:doc:`Configuration System - Developer Guide <guide/config_development>`
   Extend the configuration layer safely and consistently.

:doc:`Building Documentation <guide/documentation>`
   Build, debug, and maintain the Sphinx documentation stack.

Common Paths
------------

If you want to...

- install the package and verify your environment, go to :doc:`Installation Guide <installation>`
- configure keys, paths, and runtime options, go to :doc:`Configuration Guide <guide/configuration>`
- understand the full processing sequence, go to :doc:`Complete Workflow <guide/workflow>`
- inspect code-level interfaces, go to :doc:`API Reference <api/index>`
- work on the codebase itself, go to :doc:`Contributing to MetaBeeAI <guide/contributing>`
