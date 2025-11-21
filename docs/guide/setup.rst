Setup Guide
===========

Required API Accounts
---------------------

Before starting, you need to set up the following API accounts:

.. list-table::
   :header-rows: 1
   :widths: 20 40 25 15

   * - Service
     - Purpose
     - Sign Up
     - Cost
   * - **OpenAI**
     - LLM processing and evaluation
     - `platform.openai.com <https://platform.openai.com>`_
     - Pay-per-use (~$1–5 per 10 papers)
   * - **LandingLens API**
     - PDF text extraction with vision AI
     - `landing.ai <https://landing.ai>`_
     - Contact for pricing

Setting Up API Keys
-------------------

Create a ``.env`` file in the project root:

.. code-block:: bash

   # Copy the example file
   cp env.example .env

   # Edit .env and add your keys:
   OPENAI_API_KEY=sk-proj-...your_key_here
   LANDING_AI_API_KEY=...your_key_here

Do not share your ``.env`` file or API keys publicly.
