Configuration System - Developer Guide
========================================

This guide explains how to use and extend MetaBeeAI's configuration system when developing new features.

Overview
--------

The configuration system (``metabeeai.config``) provides:

1. **Hierarchical config resolution**: CLI args > config file > env vars > defaults
2. **Two APIs**:

   - ``get_config_param(name)``: For common parameters (registered in ``COMMON_PARAMS``)
   - ``get_config_value(key, ...)``: For arbitrary/custom parameters

3. **Centralized config loading**: Single source of truth for all configuration

Config Hierarchy
----------------

The full hierarchy (from highest to lowest priority):

.. code-block:: text

    1. CLI argument (handled by argparse in your entrypoint)
    2. Config file from CLI --config flag
    3. Config file from METABEEAI_CONFIG_FILE env var
    4. Config file from default location (./config.yaml)
    5. Environment variable (METABEEAI_PAPERS_DIR, etc.)
    6. Hardcoded default value

**Implementation Note**: Steps 1-4 result in a config file path that's passed to ``get_config_value``. The config file is loaded and checked first, then the env var, then the default.

Using get_config_value() for Arbitrary Parameters
--------------------------------------------------

Use ``get_config_value()`` when you need to read a custom parameter that isn't in ``COMMON_PARAMS``.

Function Signature
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def get_config_value(key, config_path=None, env_var=None, default=None):
        """
        Get a config parameter value using the hierarchy:
        1. YAML config file (explicit config_path or METABEEAI_CONFIG_FILE)
        2. Environment variable (if env_var provided)
        3. Default value

        Args:
            key: Config key (use dots for nested: 'llm.model')
            config_path: Path to config file (optional)
            env_var: Environment variable name (optional)
            default: Default value (optional)

        Returns:
            The config value from highest priority source
        """

Basic Usage
~~~~~~~~~~~

.. code-block:: python

    from metabeeai.config import get_config_value

    # Simple parameter with default
    batch_size = get_config_value(
        'batch_size',
        env_var='MY_BATCH_SIZE',
        default=10
    )

    # Nested parameter (uses dot notation)
    llm_model = get_config_value(
        'llm.relevance_model',
        env_var='MY_LLM_MODEL',
        default='gpt-4o-mini'
    )

    # With explicit config file
    api_key = get_config_value(
        'my_api_key',
        config_path='/path/to/config.yaml',
        env_var='MY_API_KEY',
        default=None
    )

Integration with Argparse
~~~~~~~~~~~~~~~~~~~~~~~~~~

In your CLI entrypoint, check CLI args first, then fall back to config:

.. code-block:: python

    import argparse
    from metabeeai.config import get_config_value

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', help='Config file path')
        parser.add_argument('--batch-size', type=int, help='Batch size')
        parser.add_argument('--model', help='Model name')
        args = parser.parse_args()

        # Hierarchy: CLI arg > config file > env var > default
        batch_size = (
            args.batch_size  # CLI arg wins
            if args.batch_size is not None
            else get_config_value(
                'batch_size',
                config_path=args.config,  # From --config flag
                env_var='MY_BATCH_SIZE',
                default=10
            )
        )

        model = (
            args.model
            if args.model is not None
            else get_config_value(
                'llm.model',
                config_path=args.config,
                env_var='MY_MODEL',
                default='gpt-4o-mini'
            )
        )

        print(f"Batch size: {batch_size}, Model: {model}")

Config File Format
~~~~~~~~~~~~~~~~~~

For ``get_config_value()`` to work, users need to structure their YAML:

.. code-block:: yaml

    # Top-level keys
    batch_size: 25
    my_api_key: "key-123"

    # Nested keys (accessed with dot notation)
    llm:
      model: "gpt-4o"
      temperature: 0.7

    custom_settings:
      threshold: 0.95
      max_iterations: 100

Then access with:

.. code-block:: python

    # Top-level: get_config_value('batch_size')
    # Nested: get_config_value('llm.model')
    # Nested: get_config_value('custom_settings.threshold')

Adding Common Parameters to COMMON_PARAMS
------------------------------------------

For parameters used across multiple commands/modules, add them to ``COMMON_PARAMS`` in ``src/metabeeai/config.py``.

When to Add a Common Parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add to ``COMMON_PARAMS`` when:

- Parameter is used by 2+ commands/modules
- Parameter should have consistent naming across codebase
- You want centralized documentation

Keep custom parameters local when:

- Used by only one command
- Highly specialized/experimental
- Not user-facing

How to Add a Common Parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Add to COMMON_PARAMS dict**:

.. code-block:: python

    # src/metabeeai/config.py

    COMMON_PARAMS = {
        # ... existing params ...

        "my_new_param": {
            "env_var": "METABEEAI_MY_NEW_PARAM",  # Environment variable name
            "yaml_key": "my_new_param",            # YAML config key
            "default": "default_value",            # Default value
        },
    }

2. **Use via get_config_param()**:

.. code-block:: python

    from metabeeai.config import get_config_param

    def my_function():
        # Simple one-liner
        my_value = get_config_param("my_new_param")

        # Or with CLI arg support
        my_value = (
            args.my_param
            if args.my_param is not None
            else get_config_param("my_new_param", config_path=args.config)
        )

3. **Document in config.example.yaml**:

.. code-block:: yaml

    # My new parameter description
    # What it does, valid values, etc.
    # Default: default_value
    # Env var: METABEEAI_MY_NEW_PARAM
    my_new_param: default_value

4. **Add to docs/guide/configuration.rst** in the Common Parameters table.

Example: Adding a Timeout Parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Step 1: Add to ``COMMON_PARAMS``:

.. code-block:: python

    COMMON_PARAMS = {
        # ... existing ...
        "timeout": {
            "env_var": "METABEEAI_TIMEOUT",
            "yaml_key": "timeout",
            "default": 30,  # seconds
        },
    }

Step 2: Use in your code:

.. code-block:: python

    from metabeeai.config import get_config_param

    def process_with_timeout():
        timeout = get_config_param("timeout")
        # Use timeout...

Step 3: Document in ``config.example.yaml``:

.. code-block:: yaml

    # Timeout for API requests (seconds)
    # Default: 30
    # Env var: METABEEAI_TIMEOUT
    timeout: 30

Naming Conventions
~~~~~~~~~~~~~~~~~~

Follow these conventions when adding parameters:

- **Python name**: ``snake_case`` (e.g., ``my_param``)
- **YAML key**: Same as Python name (e.g., ``my_param``)
- **Env var**: ``METABEEAI_`` prefix + ``UPPER_CASE`` (e.g., ``METABEEAI_MY_PARAM``)
- **Exception**: External APIs don't need prefix (e.g., ``OPENAI_API_KEY``, not ``METABEEAI_OPENAI_API_KEY``)

Using get_config_param() for Common Parameters
-----------------------------------------------

Once a parameter is in ``COMMON_PARAMS``, use ``get_config_param()`` instead of ``get_config_value()``.

Function Signature
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def get_config_param(name, config_path=None):
        """
        Get a common config parameter by name.

        Convenience wrapper around get_config_value() for parameters
        registered in COMMON_PARAMS.

        Args:
            name: Parameter name (must be in COMMON_PARAMS)
            config_path: Optional path to config file

        Returns:
            The config value

        Raises:
            ValueError: If parameter name not in COMMON_PARAMS
        """

Examples
~~~~~~~~

.. code-block:: python

    from metabeeai.config import get_config_param

    # Get data directory
    data_dir = get_config_param("data_dir")

    # Get papers directory with custom config
    papers_dir = get_config_param("papers_dir", config_path="/path/to/config.yaml")

    # Get API key
    api_key = get_config_param("openai_api_key")
    if not api_key:
        raise ValueError("OpenAI API key not configured")

    # With CLI arg support
    papers_dir = (
        args.papers_dir
        if args.papers_dir is not None
        else get_config_param("papers_dir", config_path=args.config)
    )

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

    from metabeeai.config import get_config_param

    try:
        value = get_config_param("typo_param")
    except ValueError as e:
        # Raised if "typo_param" not in COMMON_PARAMS
        print(f"Invalid parameter: {e}")

Config Caching
--------------

The config system caches loaded YAML files to avoid re-reading:

.. code-block:: python

    # src/metabeeai/config.py
    _config_cache = {}

    def load_config(config_path=None):
        # Checks cache first
        if path and path in _config_cache:
            return _config_cache[path]

        # Loads and caches
        with open(path) as f:
            config = yaml.safe_load(f)
            _config_cache[path] = config
            return config

**Implication**: Changes to config files during runtime won't be reflected unless you clear the cache.

Clearing Cache in Tests
~~~~~~~~~~~~~~~~~~~~~~~~

In tests, clear the cache between test cases:

.. code-block:: python

    import pytest
    from metabeeai import config

    @pytest.fixture(autouse=True)
    def clear_config_cache():
        """Clear config cache before each test."""
        config._config_cache.clear()
        yield
        config._config_cache.clear()

Best Practices
--------------

For Library Developers
~~~~~~~~~~~~~~~~~~~~~~

**DO**:

- Use ``get_config_param()`` for common parameters
- Use ``get_config_value()`` for command-specific parameters
- Add widely-used parameters to ``COMMON_PARAMS``
- Check CLI args before calling config functions
- Provide sensible defaults
- Document all parameters in ``config.example.yaml``

**DON'T**:

- Don't read env vars directly (use config system)
- Don't hardcode config values in multiple places
- Don't add rarely-used parameters to ``COMMON_PARAMS``
- Don't modify ``_config_cache`` directly

For Command Developers
~~~~~~~~~~~~~~~~~~~~~~

Pattern for CLI entrypoints:

.. code-block:: python

    import argparse
    from metabeeai.config import get_config_param, get_config_value

    def main():
        parser = argparse.ArgumentParser()

        # Global config flag
        parser.add_argument('--config', help='Config file')

        # Common parameters (optional CLI overrides)
        parser.add_argument('--papers-dir', help='Papers directory')
        parser.add_argument('--data-dir', help='Data directory')

        # Command-specific parameters
        parser.add_argument('--batch-size', type=int, help='Batch size')

        args = parser.parse_args()

        # Resolve common parameters (CLI > config > env > default)
        papers_dir = (
            args.papers_dir
            if args.papers_dir is not None
            else get_config_param("papers_dir", config_path=args.config)
        )

        data_dir = (
            args.data_dir
            if args.data_dir is not None
            else get_config_param("data_dir", config_path=args.config)
        )

        # Resolve custom parameters
        batch_size = (
            args.batch_size
            if args.batch_size is not None
            else get_config_value(
                "process.batch_size",
                config_path=args.config,
                env_var="MY_BATCH_SIZE",
                default=10
            )
        )

        # Use the resolved values
        run_command(papers_dir, data_dir, batch_size)

See Also
--------

- :doc:`configuration` - User guide for configuration
- ``src/metabeeai/config.py`` - Source code
- ``tests/test_config.py`` - Test examples
- ``config.example.yaml`` - Example config with all parameters
