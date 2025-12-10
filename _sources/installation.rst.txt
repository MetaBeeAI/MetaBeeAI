Installation Guide
==================

MetaBeeAI can be installed using pip, simply run:

.. code-block:: bash

   pip install metabeeai

Post-Installation Setup
-----------------------

After installation, set up your configuration:

1. **Create a configuration file**:

   .. code-block:: bash

      # Copy the example config to get started
      cp config.example.yaml config.yaml

2. **Set up API keys** (required for most operations):

   You can set API keys via environment variables:

   .. code-block:: bash

      export OPENAI_API_KEY=sk-your-openai-key
      export LANDING_AI_API_KEY=your-landing-ai-key

   Or add them to a ``.env`` file in your project directory:

   .. code-block:: bash

      # .env
      OPENAI_API_KEY=sk-your-openai-key
      LANDING_AI_API_KEY=your-landing-ai-key

   **Note**: The configuration file takes precedence over environment variables. See the :doc:`Configuration Guide <guide/configuration>` for details on the hierarchy.

3. **Verify installation**:

   .. code-block:: bash

      metabeeai --help

For complete configuration options, see the :doc:`Configuration Guide <guide/configuration>`.

Development Installation
------------------------

To install MetaBeeAI for development, clone the repository and install the package in editable mode:

.. code-block:: bash

   git clone https://github.com/MetaBeeAI/MetaBeeAI
   cd MetaBeeAI
   pip install -e .[dev]
