Complete Workflow
=================

The MetaBeeAI pipeline can be run end-to-end or executed in stages.
Each stage corresponds to one of the core submodules introduced in the :doc:`Pipeline Overview <pipeline_overview>` section.

.. note::
   Before running the workflow, ensure you have configured your API keys and environment variables as described in the :doc:`Setup Guide <setup>`.

Step 1 — Process PDFs to JSON
-----------------------------

.. code-block:: bash

   metabeeai process-pdfs

**Purpose:** Convert PDFs into structured JSON chunks using the `process_pdfs <api/process_pdfs>`_ submodule.
**Output:** ``data/papers/{paper_id}/pages/merged_v2.json``

Step 2 — Extract Information with LLM
-------------------------------------

.. code-block:: bash

   # Process all papers (default configuration)
   metabeeai llm

   # Predefined configurations (you can choose any ofthe following three to preset the answer quality level you expect)
   metabeeai llm --preset balanced   # Fast relevance + high-quality answers
   metabeeai llm --preset fast       # Fast & cheap
   metabeeai llm --preset quality    # High quality for critical analysis

   # Process specific papers
   metabeeai llm --papers 4YD2Y4J8 76DQP2DC

   # Custom model selection
   metabeeai llm --relevance-model "openai/gpt-4o-mini" --answer-model "openai/gpt-4o"

**Purpose:** Run LLM-based extraction using the `metabeeai_llm <api/metabeeai_llm>`_ submodule.
**Input:** JSON chunks from Stage 1
**Output:** ``data/papers/{paper_id}/answers.json``

Questions are defined in ``metabeeai_llm/questions.yml``.

Step 3 — Human Review (Optional)
--------------------------------

.. code-block:: bash

   metabeeai review

**Purpose:** Launch the graphical review interface provided by the `llm_review_software <api/llm_review_software>`_ submodule.
**Output:** ``data/papers/{paper_id}/answers_extended.json``

Features include PDF viewing, answer editing, and quality ratings.

Step 4 — Benchmarking and Evaluation
------------------------------------

4a. **Prepare Reviewer Data**

If you have CSV golden answers:

.. code-block:: bash

   metabeeai prep-benchmark --papers-dir /path/to/papers --output data/benchmark_data_gui.json
   # If you already ran the review GUI, reviewer data is read automatically from ``answers_extended.json``.

4b. **Create Benchmark Dataset**

.. code-block:: bash

   metabeeai prep-benchmark

**Purpose:** Generate benchmarking datasets using the `llm_benchmarking <api/llm_benchmarking>`_ submodule.
**Output:** ``data/benchmark_data.json`` or ``data/benchmark_data_gui.json``

4c. **Run Evaluation**

.. code-block:: bash

   metabeeai benchmark --question design
   metabeeai benchmark --question population
   metabeeai benchmark --question welfare

   # Evaluate all at once
   metabeeai benchmark

**Output:** ``deepeval_results/combined_results_{question}_{timestamp}.json``

4d. **Visualize Results**

.. code-block:: bash

   metabeeai plot-metrics

**Output:** ``deepeval_results/plots/metrics_comparison.png``

4e. **Identify Problem Papers (Optional)**

.. code-block:: bash

   metabeeai edge-cases --num-cases 3

**Output:** ``edge_cases/edge-case-report.md``

Step 5 — Data Analysis
----------------------

.. code-block:: bash

   # Data analysis scripts (run as modules)
   python -m metabeeai.query_database.trend_analysis
   python -m metabeeai.query_database.network_analysis
   python -m metabeeai.query_database.investigate_bee_species
   python -m metabeeai.query_database.investigate_pesticides

**Purpose:** Perform large-scale data aggregation and analysis using the `query_database <api/query_database>`_ submodule.
**Output:** Analytical reports, plots, and datasets in ``query_database/output/``.
