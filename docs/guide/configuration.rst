Configuration Guide
===================

MetaBeeAI uses a flexible configuration system that allows you to set parameters through multiple sources, with a clear hierarchy of precedence.

Configuration Hierarchy
-----------------------

When MetaBeeAI looks for a configuration parameter, it checks sources in this order (highest priority first):

1. **CLI Arguments**: Command-line flags like ``--papers-dir`` or ``--data-dir``
2. **Config File (CLI)**: YAML file specified via ``--config /path/to/config.yaml``
3. **Config File (Environment)**: YAML file specified via ``METABEEAI_CONFIG_FILE`` env var
4. **Config File (Default)**: ``./config.yaml`` in current directory
5. **Environment Variables**: ``METABEEAI_PAPERS_DIR``, ``OPENAI_API_KEY``, etc.
6. **Hardcoded Defaults**: Built-in default values

**Key Point**: Values in config files **override** environment variables. Use env vars for temporary overrides or secrets that shouldn't be in config files.

Quick Start
-----------

1. Copy the example config::

    cp config.example.yaml config.yaml

2. Edit ``config.yaml`` to customize your settings::

    # config.yaml
    data_dir: ./data
    papers_dir: ./data/papers
    log_level: DEBUG

3. Run any command - it will automatically load ``./config.yaml``::

    metabeeai llm
    metabeeai process_pdfs --start 1 --end 10

Configuration File Format
-------------------------

MetaBeeAI uses YAML format for configuration files:

.. code-block:: yaml

    # Common parameters
    data_dir: ./data
    papers_dir: ./data/papers
    results_dir: ./data/results
    log_level: INFO

    # API keys (better to use env vars for these!)
    openai_api_key: "sk-..."
    landing_api_key: "..."

    # Nested settings for specific commands
    llm:
      relevance_model: "gpt-4o-mini"
      answer_model: "gpt-4o"
      preset: "balanced"

    process_pdfs:
      batch_size: 10

    benchmark:
      model: "gpt-4o"
      batch_size: 25
      max_retries: 5

Common Parameters
-----------------

These parameters are available across all MetaBeeAI commands:

.. list-table::
   :header-rows: 1
   :widths: 20 30 30 20

   * - Parameter
     - YAML Key
     - Environment Variable
     - Default
   * - Data directory
     - ``data_dir``
     - ``METABEEAI_DATA_DIR``
     - ``./data``
   * - Papers directory
     - ``papers_dir``
     - ``METABEEAI_PAPERS_DIR``
     - ``./data/papers``
   * - Results directory
     - ``results_dir``
     - ``METABEEAI_RESULTS_DIR``
     - ``./data/results``
   * - Output directory
     - ``output_dir``
     - ``METABEEAI_OUTPUT_DIR``
     - ``./data/output``
   * - Logs directory
     - ``logs_dir``
     - ``METABEEAI_LOGS_DIR``
     - ``{data_dir}/logs``
   * - Log level
     - ``log_level``
     - ``METABEEAI_LOG_LEVEL``
     - ``INFO``
   * - OpenAI API key
     - ``openai_api_key``
     - ``OPENAI_API_KEY``
     - None
   * - Landing AI API key
     - ``landing_api_key``
     - ``LANDING_AI_API_KEY``
     - None

Using Environment Variables
----------------------------

Environment variables are useful for:

- Temporary overrides during development
- Secrets that shouldn't be committed to version control
- CI/CD environments

Set environment variables in your shell::

    export METABEEAI_PAPERS_DIR=/tmp/papers
    export OPENAI_API_KEY=sk-your-key-here
    export METABEEAI_LOG_LEVEL=DEBUG

Or use a ``.env`` file::

    # .env
    METABEEAI_PAPERS_DIR=/tmp/papers
    OPENAI_API_KEY=sk-your-key-here
    METABEEAI_LOG_LEVEL=DEBUG

**Important**: If a parameter is set in both a config file and an environment variable, **the config file wins**. This ensures config files provide stable, explicit configuration.

Using Config Files
------------------

Specifying Config File Location
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Three ways to specify which config file to use:

1. **Automatic**: Place ``config.yaml`` in your current directory::

    # MetaBeeAI will automatically find and load it
    metabeeai llm

2. **CLI flag**: Use ``--config`` before the command name::

    metabeeai --config /path/to/custom-config.yaml llm

3. **Environment variable**: Set ``METABEEAI_CONFIG_FILE``::

    export METABEEAI_CONFIG_FILE=/path/to/config.yaml
    metabeeai llm

Config File Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**DO**:

- Keep ``config.yaml`` in your project directory for project-specific settings
- Use ``--config`` or ``METABEEAI_CONFIG_FILE`` to specify alternate config locations
- Commit ``config.example.yaml`` to version control as a template
- Use environment variables for API keys and secrets

**DON'T**:

- Don't commit ``config.yaml`` with real API keys to version control
- Don't rely on environment variables for persistent settings (use config files)
- Don't mix personal settings into project config files

Examples
--------

Example 1: Development Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use config file for stable settings, env vars for secrets::

    # config.yaml (committed to git)
    data_dir: ./data
    papers_dir: ./data/papers
    log_level: DEBUG

    llm:
      relevance_model: "gpt-4o-mini"
      answer_model: "gpt-4o"

::

    # .env (NOT committed to git)
    OPENAI_API_KEY=sk-your-actual-key
    LANDING_AI_API_KEY=your-landing-key

Example 2: Production Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Override specific settings for production::

    # config.production.yaml
    data_dir: /data/metabeeai
    papers_dir: /data/metabeeai/papers
    log_level: WARNING

    llm:
      config: "quality"

Run with::

    metabeeai --config config.production.yaml llm

Example 3: Temporary Override
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use CLI args for one-off changes::

    # Override papers directory just for this run
    metabeeai process_pdfs --papers-dir /tmp/test-papers --start 1 --end 5

Example 4: CI/CD Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use environment variables in CI::

    # .github/workflows/test.yml
    env:
      METABEEAI_DATA_DIR: /tmp/ci-data
      METABEEAI_LOG_LEVEL: DEBUG
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

Command-Specific Settings
--------------------------

LLM Pipeline
~~~~~~~~~~~~

.. code-block:: yaml

    llm:
      relevance_model: "gpt-4o-mini"  # Model for chunk selection
      answer_model: "gpt-4o"          # Model for answer generation
      preset: "balanced"              # fast/balanced/quality
      temperature: 0.7                # LLM temperature (optional)
      max_tokens: 2000                # Max response tokens (optional)

PDF Processing
~~~~~~~~~~~~~~

.. code-block:: yaml

    process_pdfs:
      batch_size: 10        # Parallel processing batch size
      skip_split: false     # Skip PDF splitting
      skip_api: false       # Skip API processing
      skip_merge: false     # Skip JSON merging
      skip_deduplicate: false  # Skip deduplication

Benchmarking
~~~~~~~~~~~~

.. code-block:: yaml

    benchmark:
      model: "gpt-4o"       # Evaluation model
      batch_size: 25        # Test cases per batch
      max_retries: 5        # Max retries per batch
      timeout: 120          # Timeout per test (seconds)

Troubleshooting
---------------

Config Not Loading
~~~~~~~~~~~~~~~~~~

Check these in order:

1. Verify file exists: ``ls -la config.yaml``
2. Check YAML syntax: ``python -c "import yaml; yaml.safe_load(open('config.yaml'))``
3. Check you're in the correct directory (config.yaml must be in current directory)
4. Use ``--config`` to explicitly specify the path

Environment Variable Not Working
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Remember: **Config files override environment variables**

If you have ``papers_dir: ./data/papers`` in your config file, setting ``METABEEAI_PAPERS_DIR=/tmp/papers`` won't work. Either:

1. Remove the parameter from the config file, OR
2. Use a CLI argument: ``--papers-dir /tmp/papers``

Checking Current Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``--verbose`` or ``--debug`` to see which config values are being used::

    metabeeai --verbose llm

Or programmatically check from Python::

    from metabeeai.config import get_config_param, load_config

    # Check what config file is loaded
    config = load_config()
    print(config)

    # Check specific parameter
    papers_dir = get_config_param("papers_dir")
    print(f"Papers directory: {papers_dir}")

See Also
--------

- :doc:`../quickstart` - Getting started with MetaBeeAI
- :doc:`./troubleshooting` - Common issues and solutions
- :doc:`./config_development` - Developer guide for config system
