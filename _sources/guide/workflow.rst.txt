Complete Workflow
=================

The MetaBeeAI pipeline can be run end-to-end or executed in stages.  
Each stage corresponds to one of the core submodules introduced in the :doc:`Pipeline Overview <pipeline_overview>` section.

.. note::
   Before running the workflow, ensure you have configured your API keys and environment variables as described in the :doc:`Setup Guide <setup>`.

Step 1 — Process PDFs to JSON
-----------------------------

.. code-block:: bash

   cd process_pdfs
   python process_all.py

**Purpose:** Convert PDFs into structured JSON chunks using the `process_pdfs <api/process_pdfs>`_ submodule.  
**Output:** ``data/papers/{paper_id}/pages/merged_v2.json``

Step 2 — Extract Information with LLM
-------------------------------------

.. code-block:: bash

   cd metabeeai_llm

   # Process all papers (default configuration)
   python llm_pipeline.py

   # Predefined configurations
   python llm_pipeline.py --config balanced   # Fast relevance + high-quality answers
   python llm_pipeline.py --config fast       # Fast & cheap
   python llm_pipeline.py --config quality    # High quality for critical analysis

   # Process specific papers
   python llm_pipeline.py --folders 4YD2Y4J8 76DQP2DC

   # Custom model selection
   python llm_pipeline.py --relevance-model "openai/gpt-4o-mini" --answer-model "openai/gpt-4o"

**Purpose:** Run LLM-based extraction using the `metabeeai_llm <api/metabeeai_llm>`_ submodule.  
**Input:** JSON chunks from Stage 1  
**Output:** ``data/papers/{paper_id}/answers.json``

Questions are defined in ``metabeeai_llm/questions.yml``.

Step 3 — Human Review (Optional)
--------------------------------

.. code-block:: bash

   cd llm_review_software
   python beegui.py

**Purpose:** Launch the graphical review interface provided by the `llm_review_software <api/llm_review_software>`_ submodule.  
**Output:** ``data/papers/{paper_id}/answers_extended.json``

Features include PDF viewing, answer editing, and quality ratings.

Step 4 — Benchmarking and Evaluation
------------------------------------

4a. **Prepare Reviewer Data**

If you have CSV golden answers:

.. code-block:: bash

   cd metabeeai_llm
   python convert_goldens.py

**Output:** ``data/papers/{paper_id}/rev1_answers.json``

If you used the GUI review tool, reviewer data is already available in ``answers_extended.json``.

4b. **Create Benchmark Dataset**

.. code-block:: bash

   cd llm_benchmarking
   python prep_benchmark_data.py

   # For GUI reviewer answers
   python prep_benchmark_data_from_GUI_answers.py

**Purpose:** Generate benchmarking datasets using the `llm_benchmarking <api/llm_benchmarking>`_ submodule.  
**Output:** ``data/benchmark_data.json`` or ``data/benchmark_data_gui.json``

4c. **Run Evaluation**

.. code-block:: bash

   python deepeval_benchmarking.py --question design
   python deepeval_benchmarking.py --question population
   python deepeval_benchmarking.py --question welfare

   # Evaluate all at once
   python deepeval_benchmarking.py

**Output:** ``deepeval_results/combined_results_{question}_{timestamp}.json``

4d. **Visualize Results**

.. code-block:: bash

   python plot_metrics_comparison.py

**Output:** ``deepeval_results/plots/metrics_comparison.png``

4e. **Identify Problem Papers (Optional)**

.. code-block:: bash

   python edge_cases.py --num-cases 3

**Output:** ``edge_cases/edge-case-report.md``

Step 5 — Data Analysis
----------------------

.. code-block:: bash

   cd query_database

   python trend_analysis.py

   python network_analysis.py

   python investigate_bee_species.py

   python investigate_pesticides.py

**Purpose:** Perform large-scale data aggregation and analysis using the `query_database <api/query_database>`_ submodule.  
**Output:** Analytical reports, plots, and datasets in ``query_database/output/``.
