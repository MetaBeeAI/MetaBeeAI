Pipeline Overview
=================

The MetaBeeAI pipeline is composed of five core **submodules**, each responsible for a distinct stage of the literature review and analysis process.

.. code-block::

   PDFs → Vision AI Processing → LLM Analysis → Human Review → Benchmarking → Analysis

For a detailed overview of the various stages see their respective sections in the :doc:`submodule documentation <../submodule/index>`.

Stages
------

1. **PDF Processing → Structured JSON**
   - **Submodule:** :doc:`process_pdfs <../submodule/process_pdfs>`
   - **Purpose:** Convert PDFs into structured JSON text with layout and coordinate data
   - **Input:** PDF files
   - **Output:** JSON chunks representing extracted text and layout elements
   - **API Reference:** :doc:`Process PDFs <../api/process_pdfs>`

1. **LLM Question Answering → Extracted Information**
   - **Submodule:** :doc:`metabeeai_llm <../submodule/metabeeai_llm>`
   - **Purpose:** Use large language models to extract structured answers and citations from processed text
   - **Input:** JSON chunks
   - **Output:** Structured question–answer pairs with traceable sources
   - **API Reference:** :doc:`MetaBeeAI LLM <../api/metabeeai_llm>`
  
1. **Human Review & Annotation → Validated Answers**
   - **Submodule:** :doc:`llm_review_software <../submodule/llm_review_software>`
   - **Purpose:** Provide a graphical interface for human review and validation of LLM answers
   - **Input:** LLM-generated answers
   - **Output:** Human-verified and annotated answers
   - **API Reference:** :doc:`LLM Review Software <../api/llm_review_software>`

1. **Benchmarking → Performance Metrics**
   - **Submodule:** :doc:`llm_benchmarking <../submodule/llm_benchmarking>`
   - **Purpose:** Evaluate model performance against human-reviewed ground truth
   - **Input:** LLM and reviewer answers
   - **Output:** Quantitative metrics, comparisons, and performance plots
   - **API Reference:** :doc:`LLM Benchmarking <../api/llm_benchmarking>`

1. **Data Analysis → Insights**
   - **Submodule:** :doc:`query_database <../submodule/query_database>`
   - **Purpose:** Aggregate validated data across studies and perform trend and network analyses
   - **Input:** Structured and benchmarked results
   - **Output:** Analytical summaries, visualizations, and derived datasets
   - **API Reference:** :doc:`Query Database <../api/query_database>`

