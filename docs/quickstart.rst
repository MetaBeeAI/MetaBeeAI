Quick Start Guide
=================

This guide will help you get started with MetaBeeAI quickly.

Installation
------------

MetaBeeAI can be installed using pip. Open your terminal and run:

.. code-block:: bash

   pip install metabeeai

For further options, including development installation, please refer to the :doc:`Installation Guide <installation>`

Configuration
-------------

MetaBeeAI uses a flexible configuration system. Before running commands, set up your configuration:

1. **Copy the example config**:

   .. code-block:: bash

      cp config.example.yaml config.yaml

2. **Add your API keys** (required for most operations):

   .. code-block:: bash

      # Set as environment variables
      export OPENAI_API_KEY=sk-your-key-here
      export LANDING_API_KEY=your-landing-key

   Or add them to ``config.yaml`` (but don't commit this file!):

   .. code-block:: yaml

      openai_api_key: "sk-your-key-here"
      landing_api_key: "your-landing-key"

3. **Customize paths** (optional):

   .. code-block:: yaml

      data_dir: ./data
      papers_dir: ./data/papers
      log_level: INFO

For detailed configuration options and hierarchy, see the :doc:`Configuration Guide <guide/configuration>`.

Basic Usage
-----------

Prepare Your PDFs
~~~~~~~~~~~~~~~~~

Organize papers in ``data/papers/``:

.. code-block::

   data/papers/
   ├── 4YD2Y4J8/
   │   └── 4YD2Y4J8_main.pdf
   ├── 76DQP2DC/
   │   └── 76DQP2DC_main.pdf
   └── ...

Each paper should be in its own folder with a unique alphanumeric ID.

Run the Pipeline
~~~~~~~~~~~~~~~~

The full pipeline can be ran, using the CLI command:

.. code-block:: bash

   metabeeai run

For a detailed breakdown of the usage and options, please refer to the  :doc:`User Guide <guide/index>`.

For the full API reference, please refer to the :doc:`API Reference <api/index>`.
