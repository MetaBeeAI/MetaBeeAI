Contributing to MetaBeeAI
=========================

Thank you for your interest in contributing to MetaBeeAI! This guide will help you get started with development and understand our processes.

Getting Started
---------------

1. **Fork and Clone**:

   .. code-block:: bash

      git clone https://github.com/YOUR_USERNAME/MetaBeeAI.git
      cd MetaBeeAI

2. **Install for Development**:

   .. code-block:: bash

      pip install -e .[dev]

3. **Install Pre-commit Hooks**:

   .. code-block:: bash

      pre-commit install

Development Workflow
--------------------

1. **Create a Branch**:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. **Make Changes**: Write your code following our style guidelines

3. **Run Tests**:

   .. code-block:: bash

      pytest -q

4. **Run Pre-commit Checks**:

   .. code-block:: bash

      pre-commit run -a

5. **Commit and Push**:

   .. code-block:: bash

      git add .
      git commit -m "Description of changes"
      git push origin feature/your-feature-name

6. **Open a Pull Request** on GitHub

Code Style
----------

Code style is enforced automatically using pre-commit hooks. When you commit changes, pre-commit will:

- Format code and sort imports with Ruff
- Run linting checks with Ruff
- Ensure newlines at end of files
- Remove trailing whitespace
- Check YAML syntax
- Block large files

Install pre-commit hooks after cloning:

.. code-block:: bash

   pre-commit install

Run manually on all files:

.. code-block:: bash

   pre-commit run -a

**Style Guidelines**:

- Use descriptive variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and small
- Write tests for new functionality

Testing
-------

We use pytest for testing. Tests are located in the ``tests/`` directory.

**Run all tests**:

.. code-block:: bash

   pytest

**Run specific test file**:

.. code-block:: bash

   pytest tests/test_config.py

**Run with coverage**:

.. code-block:: bash

   pytest --cov=metabeeai

**Test Guidelines**:

- Write tests for all new features
- Test real behavior, not mocks (avoid mocking the functions you're testing)
- Use fixtures for setup/teardown
- Clear any caches or state between tests
- Use descriptive test names that explain what's being tested

Documentation
-------------

Documentation is built with Sphinx and hosted on Read the Docs.

**Quick Start**:

.. code-block:: bash

   # Install dependencies
   pip install -e .[docs]
   
   # Build documentation
   sphinx-build -b html docs/ docs/_build/html -q
   
   # Open in browser
   xdg-open docs/_build/html/index.html  # Linux/WSL

**Guidelines**:

- Update docs when adding features
- Include working code examples
- Keep language clear and concise
- No emojis in documentation
- Test builds before submitting PRs

For complete documentation on building docs, Sphinx usage, Read the Docs integration, and troubleshooting, see :doc:`documentation`

Developer Guides
----------------

.. toctree::
   :maxdepth: 1

   config_development
   documentation

Configuration System
~~~~~~~~~~~~~~~~~~~~

If you're adding new configuration parameters or working with the config system, see the :doc:`config_development` guide for detailed information on:

- Using ``get_config_value()`` for arbitrary parameters
- Adding parameters to ``COMMON_PARAMS``
- Naming conventions
- Integration with argparse
- Testing configuration

Pull Request Process
---------------------

1. **Ensure all tests pass**
2. **Update documentation** if needed
3. **Add tests** for new functionality
4. **Follow commit message conventions**:

   - Use present tense ("Add feature" not "Added feature")
   - Keep first line under 50 characters
   - Provide detailed description in commit body if needed

5. **Link related issues** in PR description
6. **Wait for review** - maintainers will review your PR

Common Development Tasks
------------------------

Adding a New Command
~~~~~~~~~~~~~~~~~~~~

1. Create module in ``src/metabeeai/``
2. Add CLI entrypoint in ``src/metabeeai/cli.py``
3. Add configuration parameters if needed (see :doc:`config_development`)
4. Write tests in ``tests/``
5. Update documentation

Adding Configuration Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See :doc:`config_development` for complete guide. Quick checklist:

- Add to ``COMMON_PARAMS`` if used by multiple commands
- Use ``get_config_value()`` for command-specific params
- Follow naming conventions (``snake_case``, ``METABEEAI_UPPER_CASE``)
- Document in ``config.example.yaml``
- Add tests for hierarchy

Questions?
----------

- Open an issue on GitHub
- Check existing documentation

Thank you for contributing!
