Installation Guide
==================

MetaBeeAI can be installed using pip, simply run:

.. code-block:: bash

   pip install metabeeai

Development Installation
------------------------

To install MetaBeeAI for development, clone the repository and install the package in editable mode:

.. code-block:: bash

   git clone https://github.com/MetaBeeAI/MetaBeeAI
   cd MetaBeeAI
   pip install -e .[dev]

Documentation Build
-------------------

To build the documentation locally, first make sure the `docs` optional dependencies are installed:

.. code-block:: bash

   pip install -e .[docs]

Then run sphinx build on the /docs directory:

.. code-block:: bash

   sphinx-build -b html docs/ docs/_build/html

Open the generated HTML files in your web browser to view the documentation.