Quick Start Guide
=================

This guide will help you get started with MetaBeeAI quickly.

Installation
------------

MetaBeeAI can be installed using pip. Open your terminal and run:

.. code-block:: bash        

   pip install metabeeai

For further options, including development installation, please refer to the :doc:`Installation Guide <installation>`

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

For a detailed breakdown of the usage and options, please refer to the  :doc:`User Guide <user_guide/index>`.

For the full API reference, please refer to the :doc:`API Reference <api/index>`.