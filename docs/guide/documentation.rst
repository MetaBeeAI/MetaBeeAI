Building Documentation
======================

MetaBeeAI's documentation is built with Sphinx and hosted on Read the Docs. This guide covers how to build documentation locally and how the automated deployment works.

Documentation Structure
-----------------------

The documentation is organized as follows:

.. code-block:: text

   docs/
   ├── index.rst              # Main documentation landing page
   ├── installation.rst       # Installation guide
   ├── quickstart.rst         # Quick start guide
   ├── guide/                 # User and developer guides
   │   ├── configuration.rst  # Configuration system guide
   │   ├── contributing.rst   # Contribution guidelines
   │   ├── config_development.rst  # Config developer guide
   │   └── ...
   ├── api/                   # API reference documentation
   ├── generated/             # Auto-generated API docs
   ├── _static/               # Static files (CSS, images)
   ├── _build/                # Build output (not in git)
   └── conf.py                # Sphinx configuration

Building Locally
----------------

Prerequisites
~~~~~~~~~~~~~

Install documentation dependencies:

.. code-block:: bash

   pip install -e .[docs]

This installs:

- ``sphinx`` - Documentation builder
- ``sphinx-automodapi`` - API documentation generator
- ``sphinx_rtd_theme`` - Read the Docs theme
- Other documentation-related packages

Build Commands
~~~~~~~~~~~~~~

**Standard build**:

.. code-block:: bash

   sphinx-build -b html docs/ docs/_build/html

**Quiet build** (shows only warnings and errors):

.. code-block:: bash

   sphinx-build -b html docs/ docs/_build/html -q

**Clean build** (remove old build artifacts first):

.. code-block:: bash

   rm -rf docs/_build
   sphinx-build -b html docs/ docs/_build/html

Viewing Built Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After building, open the HTML files in your browser:

.. code-block:: bash

   # Linux/WSL
   xdg-open docs/_build/html/index.html

   # macOS
   open docs/_build/html/index.html

   # Windows (PowerShell)
   start docs/_build/html/index.html

Or navigate directly to ``docs/_build/html/index.html`` in your file browser.

Writing Documentation
---------------------

Format
~~~~~~

Documentation uses reStructuredText (reST) format. Key syntax:

**Headings**:

.. code-block:: rst

   Page Title
   ==========

   Section
   -------

   Subsection
   ~~~~~~~~~~

**Code blocks**:

.. code-block:: rst

   .. code-block:: python

      def example():
          return "hello"

**Links**:

.. code-block:: rst

   :doc:`other_page`           # Link to another doc page
   :doc:`../api/config`        # Relative path
   ``code_reference``          # Inline code

**Lists**:

.. code-block:: rst

   - Bullet item
   - Another item

   1. Numbered item
   2. Another item

Documentation Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~

**DO**:

- Update documentation when adding features
- Include working code examples
- Use clear, concise language
- Add docstrings to all public functions
- Test code examples actually work
- Build docs locally before submitting PRs

**DON'T**:

- Use emojis in documentation
- Leave broken links or references
- Include outdated information
- Write overly technical language without explanation

Docstrings
~~~~~~~~~~

Use Google-style docstrings for Python code:

.. code-block:: python

   def example_function(param1, param2):
       """
       Brief one-line description.

       More detailed description if needed. Can span
       multiple lines.

       Args:
           param1: Description of first parameter
           param2: Description of second parameter

       Returns:
           Description of return value

       Raises:
           ValueError: When something goes wrong

       Example:
           >>> result = example_function("a", "b")
           >>> print(result)
           'ab'
       """
       return param1 + param2

Read the Docs Integration
--------------------------

How It Works
~~~~~~~~~~~~

MetaBeeAI documentation is automatically built and deployed to Read the Docs (RTD):

1. **On every commit**: RTD monitors the GitHub repository
2. **Automatic builds**: When changes are pushed, RTD triggers a build
3. **Branch builds**: Each branch gets its own documentation version
4. **Deployment**: Successful builds are deployed to https://metabeeai.readthedocs.io

Configuration
~~~~~~~~~~~~~

RTD configuration is in ``.readthedocs.yaml`` at the repository root:

.. code-block:: yaml

   version: 2

   build:
     os: ubuntu-22.04
     tools:
       python: "3.11"

   sphinx:
     configuration: docs/conf.py

   python:
     install:
       - method: pip
         path: .
         extra_requirements:
           - docs

This tells RTD:

- Use Ubuntu 22.04 with Python 3.11
- Build with Sphinx using ``docs/conf.py``
- Install package with ``[docs]`` extras

Build Process
~~~~~~~~~~~~~

When RTD builds documentation:

1. Clones the repository
2. Installs dependencies: ``pip install .[docs]``
3. Runs: ``sphinx-build -b html docs/ _build/html``
4. Deploys HTML to RTD servers
5. Makes it available at https://metabeeai.readthedocs.io

Viewing Build Status
~~~~~~~~~~~~~~~~~~~~

- **Build dashboard**: https://readthedocs.org/projects/metabeeai/builds/
- **Latest version**: https://metabeeai.readthedocs.io/en/latest/
- **Stable version**: https://metabeeai.readthedocs.io/en/stable/

Versioning
~~~~~~~~~~

RTD automatically creates documentation for:

- **latest**: Documentation from the ``main`` branch
- **stable**: Documentation from the latest release tag
- **Branch versions**: Each branch gets a version (e.g., ``config-changes``)
- **Tag versions**: Each git tag gets a version (e.g., ``v1.0.0``)

Troubleshooting
---------------

Build Warnings
~~~~~~~~~~~~~~

Common warnings and how to fix them:

**"document isn't included in any toctree"**:

Add the document to a ``toctree`` directive or delete it if unused.

**"unknown document"**:

Check that the referenced document exists and the path is correct.

**"Enumerated list ends without a blank line"**:

Add a blank line after numbered lists before continuing text.

**"WARNING: Failed to get a function signature"**:

The documented function/module doesn't exist or has import errors. Check imports.

Build Failures
~~~~~~~~~~~~~~

If docs fail to build:

1. **Check build logs** on Read the Docs dashboard
2. **Build locally** to reproduce the error:

   .. code-block:: bash

      sphinx-build -b html docs/ docs/_build/html

3. **Common issues**:

   - Missing dependencies in ``[docs]`` extras
   - Import errors in documented modules
   - Syntax errors in reST files
   - Broken internal references

4. **Fix and test** locally before pushing

Import Errors
~~~~~~~~~~~~~

If Sphinx can't import modules:

- Ensure package installs correctly: ``pip install -e .[docs]``
- Check for circular imports
- Verify all dependencies are in ``pyproject.toml``
- Test in a clean environment

Links Not Working
~~~~~~~~~~~~~~~~~

- Use ``:doc:`` for internal documentation links
- Use relative paths from current file location
- Don't include ``.rst`` extension in ``:doc:`` links
- Check paths are correct (case-sensitive on Linux)

Continuous Integration
----------------------

Documentation is checked in CI/CD:

**Pre-commit** (local):

.. code-block:: bash

   pre-commit run -a

**GitHub Actions** (on push):

- Runs tests
- Checks code formatting
- Validates documentation builds

**Read the Docs** (on push):

- Builds documentation
- Deploys to RTD hosting

Testing Documentation Changes
------------------------------

Before submitting a PR with documentation changes:

1. **Build locally**:

   .. code-block:: bash

      sphinx-build -b html docs/ docs/_build/html -q

2. **Check for warnings** in the build output

3. **View in browser** to verify formatting

4. **Test all links** work correctly

5. **Run pre-commit**:

   .. code-block:: bash

      pre-commit run -a

6. **Push to branch** and check RTD build status

Resources
---------

- `Sphinx Documentation <https://www.sphinx-doc.org/>`_
- `reStructuredText Primer <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_
- `Read the Docs Documentation <https://docs.readthedocs.io/>`_
- `Google Python Style Guide <https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`_
