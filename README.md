# MetaBeeAI Literature Review Pipeline

A comprehensive pipeline for extracting, analyzing, and benchmarking structured information from scientific literature using Large Language Models and Vision AI.

---

## Required API Accounts

Before starting, you need to set up the following API accounts:

| Service | Purpose | Sign Up | Cost |
|---------|---------|---------|------|
| **OpenAI** | LLM processing and evaluation | [platform.openai.com](https://platform.openai.com) | Pay-per-use (model dependent) |
| **LandingLens API** | PDF text extraction with vision AI | [landing.ai](https://landing.ai) | US $0.03 per page |

### Setting Up API Keys

Create a `.env` file in the project root:

```bash
# Copy the example file
cp env.example .env

# Edit .env and add your keys:
OPENAI_API_KEY=sk-proj-...your_key_here
LANDING_AI_API_KEY=...your_key_here
```

The `.env` file is automatically excluded from git for security.

---

## Quick Start

### 1. Install Dependencies

Choose the option that best fits your workflow.

**Option A – Install from PyPI (recommended for using the CLI/package directly):**

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Mac/Linux
# Or: venv\Scripts\activate     # Windows

# Install the published package
pip install metabeeai

# Verify the CLI is available
metabeeai --help
```

**Option B – Install for development (editable install from the repo):**

```bash
# Clone the repository if you have not already
git clone https://github.com/MetaBeeAI/MetaBeeAI.git
cd MetaBeeAI

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# Or: venv\Scripts\activate     # Windows

# Install in editable mode with project dependencies
pip install -e .
# (Alternatively, pip install -r requirements.txt if you prefer)
```

### 2. Prepare Your PDFs

Organize papers in a folder with a subfolder called "papers" (best to do this in a location outside the repo folder) `YOURDATABASE/papers/`:

```
YOURDATABASE/papers/
├── 4YD2Y4J8/
│   └── 4YD2Y4J8_main.pdf
├── 76DQP2DC/
│   └── 76DQP2DC_main.pdf
└── ...
```

Each paper should be in its own folder with a unique alphanumeric ID.

### 3. Run the Pipeline

See the **Complete Workflow** section below for the full step-by-step process.

---

## Pipeline Overview

The repository is now published as the `metabeeai` Python package. Every stage can be run directly from the command line via the `metabeeai` CLI (installed automatically with the package). The end-to-end flow is:

```
PDFs → Document Processing → LLM Extraction → Human Review → Benchmarking → Analysis
```

| Stage | Purpose | CLI command(s) | Python entry point |
|-------|---------|----------------|--------------------|
| 1. Document processing | Convert PDFs into structured JSON chunks using Vision AI + merging + deduplication | `metabeeai process-pdfs` | `metabeeai.process_pdfs.process_all` |
| 2. LLM question answering | Ask the configured questions over the processed chunks and store answers | `metabeeai llm` | `metabeeai.metabeeai_llm.llm_pipeline` |
| 3. Human review | Launch the BeeGUI application to validate and rate answers | `metabeeai review` | `metabeeai.llm_review_software.beegui` |
| 4. Benchmarking & QA | Prepare benchmark data, run DeepEval, plot metrics, inspect edge cases | `metabeeai prep-benchmark`, `metabeeai benchmark`, `metabeeai plot-metrics`, `metabeeai edge-cases` or `metabeeai benchmark-all` for the whole sequence | `metabeeai.llm_benchmarking.*` |
| 5. Downstream analysis | Run domain-specific analyses (trends, networks, investigations) | Python scripts in `metabeeai.query_database` (see docs) | `metabeeai.query_database.*` |

Each command accepts additional flags (see `metabeeai --help`). You can also run the underlying Python modules directly if you prefer to script the workflow, but the CLI provides the recommended interface for both production use and local experimentation.

For more detailed walkthroughs, refer to the documentation in `docs/guide/` (particularly `pipeline_overview.rst`, `workflow.rst`, and `benchmarking.rst`).

---

## Complete Workflow (CLI-first)

The `metabeeai` CLI exposes every stage. All commands automatically load configuration from `config.py` / environment variables unless you override them with flags.

### 1. Process PDFs to JSON

```bash
# Basic usage – processes every folder under your data directory
metabeeai process-pdfs

# Only merge/deduplicate previously processed chunks (skip expensive steps)
metabeeai process-pdfs --merge-only

# Process a subset of folders (alphabetical range) and skip API calls
metabeeai process-pdfs --start af20101 --end b2050e6 --skip-api

# Change root directory
metabeeai process-pdfs --dir /path/to/YOURDATABASE/papers
```

**Purpose**: Split PDFs, send pages to Vision AI, merge/deduplicate chunks
**Output**: `YOURDATABASE/papers/{paper_id}/pages/merged_v2.json`
**Key options**: `--dir`, `--start/--end`, `--merge-only`, `--skip-split`, `--skip-api`, `--skip-merge`, `--skip-deduplicate`, `--filter-chunk-type`, `--pages`

---

### 2. Extract Information with the LLM

```bash
# Default run (balanced settings from pipeline_config.py)
metabeeai llm

# Process specific paper folders
metabeeai llm --folders 4YD2Y4J8 76DQP2DC

# Override model choices
metabeeai llm --relevance-model openai/gpt-4o-mini --answer-model openai/gpt-4o

# Point to a different data directory
metabeeai llm --dir /path/to/YOURDATABASE/papers
```

**Purpose**: Run `questions.yml` against processed chunks and store answers
**Output**: `YOURDATABASE/papers/{paper_id}/answers.json`
**Key options**: `--dir`, `--folders`, `--overwrite`, `--relevance-model`, `--answer-model`, `--config`

---

### 3. Human Review

```bash
# Launch BeeGUI (requires desktop/Qt)
metabeeai review
```

**Purpose**: Inspect LLM answers alongside PDFs, capture reviewer edits/ratings
**Output**: `YOURDATABASE/papers/{paper_id}/answers_extended.json`
**Notes**: GUI allows filtering, editing, rating, adding reviewer notes

---

### 4. Benchmarking & Evaluation

This stage has individual commands plus a “run everything” helper.

#### 4.1 Prepare benchmarking data

```bash
# Generate benchmark_data_gui.json (default paths)
metabeeai prep-benchmark

# Custom locations
metabeeai prep-benchmark --papers-dir /path/to/YOURDATABASE/papers \
                         --questions-yml /path/to/questions.yml \
                         --output /path/to/benchmark_data_gui.json
```

**Purpose**: Collate GUI-reviewed answers + LLM answers + retrieval context
**Output**: `YOURDATABASE/benchmark_data_gui.json` (nested structure)
**Key options**: `--papers-dir`, `--questions-yml`, `--output`

#### 4.2 Run DeepEval benchmarking

```bash
# Basic run over all questions
metabeeai benchmark

# Filter by question and sample size, list available keys
metabeeai benchmark --list-questions
metabeeai benchmark --question bee_species --limit 5

# Adjust runtime/cost knobs
metabeeai benchmark --batch-size 10 --max-retries 3
metabeeai benchmark --use-retrieval-only
metabeeai benchmark --model gpt-4o-mini --max-context-length 150000
```

**Purpose**: Evaluate LLM answers vs reviewer answers using 5 metrics
**Output**: `YOURDATABASE/deepeval_results/combined_results_{question}_{timestamp}.json(.jsonl)`
**Key options**: `--question`, `--input`, `--limit`, `--batch-size`, `--max-retries`, `--model`, `--max-context-length`, `--use-retrieval-only`, `--list-questions`

#### 4.3 Visualize metrics

```bash
# Create per-metric plots + summary plot
metabeeai plot-metrics

# Alternate locations
metabeeai plot-metrics --results-dir /custom/results --output-dir /custom/results
```

**Purpose**: Generate bar charts (mean ± standard error) per metric and a summary plot
**Output**: `YOURDATABASE/deepeval_results/plots/{metric}.png` and `summary_metrics.png`
**Key options**: `--results-dir`, `--output-dir`

#### 4.4 Identify edge cases

```bash
# Default: bottom 3 per question
metabeeai edge-cases --num-cases 3

# Contextual-only run with custom directories and OpenAI key override
metabeeai edge-cases --contextual-only \
    --results-dir /custom/deepeval_results \
    --output-dir /custom/edge_cases \
    --openai-api-key sk-... \
    --model gpt-4o-mini
```

**Purpose**: Surface lowest-scoring papers, generate reports and optional LLM summaries
**Output**: `YOURDATABASE/edge_cases/` (combined JSON, markdown report, summaries)
**Key options**: `--num-cases`, `--results-dir`, `--output-dir`, `--openai-api-key`, `--model`, `--generate-summaries-only`, `--contextual-only`, `--generate-contextual-summaries-only`

#### 4.5 Run the entire benchmarking pipeline

```bash
# Prep + benchmark + plot + edge cases (default settings)
metabeeai benchmark-all

# Skip certain stages or pass through flags
metabeeai benchmark-all --skip-prep --skip-edge-cases --question bee_species --limit 5
```

This wrapper simply forwards the relevant options to the commands above. Use it when you want the full workflow in one go; use the individual commands for finer control.

---

### Step 5: Data Analysis

```bash
cd query_database

# Analyze trends
python trend_analysis.py

# Network analysis
python network_analysis.py

# Investigate specific topics
python investigate_bee_species.py
python investigate_pesticides.py
```

**Output**: `query_database/output/` (plots, reports, JSON data)

---

## Project Structure

The repository is packaged under `src/metabeeai`. Key directories:

```
metabeeai/
├── pyproject.toml              # Packaging, dependencies, CLI entrypoints
├── README.md                   # This file
├── docs/                       # Sphinx documentation (see docs/guide/*)
├── examples/                   # Sample configs / usage snippets
├── tests/                      # CLI and unit tests
├── src/
│   └── metabeeai/
│       ├── __init__.py
│       ├── cli.py              # `metabeeai` console entrypoint
│       ├── config.py           # Shared helpers for locating data dirs
│       ├── process_pdfs/       # Stage 1 modules (process_all, split_pdf, etc.)
│       ├── metabeeai_llm/      # Stage 2 modules (llm_pipeline, questions.yml, …)
│       ├── llm_review_software/# Stage 3 GUI (beegui, annotator)
│       ├── llm_benchmarking/   # Stage 4 tools (prep_benchmark_data, deepeval, plots, edge cases, run_benchmarking)
│       └── query_database/     # Stage 5 analysis scripts (trend_analysis, network_analysis, investigations)
└── data/ (optional)            # Local data tree (see below)
```

### Where to store your data

We recommend keeping paper data outside the repo checkout, e.g.:

```
YOURDATABASE/
└── papers/
    ├── 4YD2Y4J8/
    │   ├── 4YD2Y4J8_main.pdf
    │   ├── pages/merged_v2.json
    │   ├── answers.json
    │   └── answers_extended.json
    └── ...
```

Point the CLI at this directory via `config.py`, environment variables, or per-command `--dir/--papers-dir` flags.

---

## Common Use Cases

### Use Case 1: Process New Papers

```bash
# 1. Add PDFs to YOURDATABASE/papers/{paper_id}/
# 2. Run the document pipeline
metabeeai process-pdfs --dir /path/to/YOURDATABASE/papers

# 3. Extract answers with the balanced preset
metabeeai llm --dir /path/to/YOURDATABASE/papers --config balanced
```

**Result**: Each paper folder now contains an `answers.json` file with structured outputs

---

### Use Case 2: Review LLM Answers

```bash
metabeeai review
```

**Features**:
- View PDF alongside LLM answers
- Edit and validate answers
- Rate answer quality
- Navigate between papers
- Saves reviewer responses side-by-side with the original LLM output in `YOURDATABASE/papers/{paper_id}/answers_extended.json`

---

### Use Case 3: Benchmark LLM Performance

```bash
# 1. Ensure reviewer confirmations exist (answers_extended.json per paper from BeeGUI)

# 2. Create benchmark dataset from GUI reviewer answers
metabeeai prep-benchmark \
  --papers-dir /path/to/YOURDATABASE/papers \
  --output /path/to/YOURDATABASE/benchmark_data_gui.json

# 3. Run evaluation (all questions or filtered)
metabeeai benchmark \
  --input /path/to/YOURDATABASE/benchmark_data_gui.json \
  --question species

# 4. Visualize metrics
metabeeai plot-metrics \
  --results-dir /path/to/YOURDATABASE/deepeval_results

# 5. Find problem papers (edge cases - can specify how many to include)
metabeeai edge-cases --num-cases 5 \
  --results-dir /path/to/YOURDATABASE/deepeval_results \
  --output-dir /path/to/YOURDATABASE/edge_cases
```

**Result**:
- Performance metrics across 5 dimensions
- Comparison plots
- Edge case analysis

---

### Use Case 4: Analyze Extracted Data

```bash
cd query_database

# Analyze trends
python trend_analysis.py

# Analyze relationships between variables
python network_analysis.py
```

**Result**: Plots and reports in `query_database/output/`

---

## Question Definitions (`questions.yml`)

All question logic lives in `src/metabeeai/metabeeai_llm/questions.yml`. Each entry under the top-level `QUESTIONS:` key defines how the LLM should extract a specific piece of information. A typical block looks like this:

```yaml
QUESTIONS:
  some_question_id:
    question: "Natural language prompt to send to the model"
    instructions:
      - "Step-by-step guidance on what to include/exclude"
      - "Each bullet is enforced before the answer."
    output_format: "Human-readable description of the expected formatting"
    example_output:
      - "Example answer 1"
      - "Example answer 2"
    bad_example_output:
      - "Examples of what NOT to return"
    no_info_response: "Fallback text when nothing is found"
    max_chunks: 5                 # (optional) throttle retrieval depth per question
    description: "Short note about retrieval threshold/purpose"
```

### Field descriptions

| Field | Purpose |
|-------|---------|
| `question` | The actual prompt sent to the LLM. Treats retrieved chunks as context. |
| `instructions` | Ordered list of constraints/checklists. The LLM sees these before answering. |
| `output_format` | Plain-language description of the formatting you expect (e.g., numbered list, JSON-like bullets). |
| `example_output` | One or more positive examples showing ideal answers. |
| `bad_example_output` | (Optional) Counter-examples to discourage common mistakes. |
| `no_info_response` | Exact string returned when the pipeline cannot find relevant information. |
| `max_chunks` | (Optional) The maximum number of retrieval chunks passed to the LLM for this question. |
| `description` | (Optional) Human-readable comment about retrieval strictness, priority, etc. |

You can add, remove, or edit question blocks to suit new projects (e.g., different species, stressors, experimental outputs). The LLM pipeline will automatically pick up any `question_key` listed under `QUESTIONS` as long as it has the required fields above. After editing `questions.yml`, rerun `metabeeai llm` (and downstream benchmarking if needed) to populate the new fields in each `answers.json`.

---

## Model Selection

The LLM pipeline exposes model selection through the `metabeeai llm` CLI. Choose from presets or override models directly.

### Preset configurations (recommended)

```bash
metabeeai llm --config fast      # gpt-4o-mini for relevance + answers
metabeeai llm --config balanced  # gpt-4o-mini for relevance, gpt-4o for answers
metabeeai llm --config quality   # gpt-4o for relevance + answers
```

### Custom model override

```bash
metabeeai llm \
  --relevance-model openai/gpt-4o-mini \
  --answer-model openai/gpt-4o
```

| Configuration | Relevance model | Answer model | Primary goal |
|---------------|-----------------|--------------|--------------|
| `fast`        | `openai/gpt-4o-mini` | `openai/gpt-4o-mini` | High throughput / low cost |
| `balanced`    | `openai/gpt-4o-mini` | `openai/gpt-4o`      | Default mix of speed + accuracy |
| `quality`     | `openai/gpt-4o`      | `openai/gpt-4o`      | Maximum fidelity, slower |

## Configuration

### Global Configuration (`config.py`)

Centralized configuration for all pipeline components:

```python
from config import get_papers_dir, get_data_dir

# Get configured directories
papers_dir = get_papers_dir()  # Default: data/papers
data_dir = get_data_dir()      # Default: data
```

**Environment Variables** (set in `.env`):
- `METABEEAI_DATA_DIR` - Base data directory (default: `data`)
- `OPENAI_API_KEY` - OpenAI API key
- `LANDING_AI_API_KEY` - LandingLens API key

### Question Configuration (`metabeeai_llm/questions.yml`)

Define questions with:
- Question text
- Instructions for LLM
- Expected output format
- Examples (good and bad)
- Retrieval parameters (max_chunks, min_score)

---

## Benchmarking Metrics

The pipeline evaluates LLM performance using 5 metrics:

### Standard DeepEval Metrics (3)

1. **Faithfulness** (0-1, higher is better)
   - Measures if LLM answer contradicts source text
   - Perfect score: No hallucinations or contradictions

2. **Contextual Precision** (0-1, higher is better)
   - Evaluates if relevant chunks are ranked highly
   - Perfect score: Most relevant chunks retrieved first

3. **Contextual Recall** (0-1, higher is better)
   - Checks if expected answer is supported by retrieval
   - Perfect score: All key points have source support

### G-Eval Metrics (2)

4. **Completeness** (0-1, threshold: 0.5)
   - Assesses if answer covers all key points
   - Uses GPT-4o to evaluate against reviewer answer

5. **Accuracy** (0-1, threshold: 0.5)
   - Evaluates information accuracy
   - Uses GPT-4o to compare LLM vs reviewer answers

**Typical Performance** (based on 10 primate welfare papers):
- Standard metrics: 0.7-1.0 (good)
- G-Eval metrics: 0.4-0.5 (moderate)

---

## Cost Estimates

Based on typical usage with GPT-4o:

| Task | Papers | Questions | Cost |
|------|--------|-----------|------|
| **LLM Extraction** | 10 | 3 per paper | ~$2-3 |
| **Benchmarking** | 10 | 3 questions | ~$0.95 |
| **Edge Case Analysis** | 3 bottom papers | All questions | ~$0.05 |
| **TOTAL** | 10 papers | Full pipeline | **~$3-4** |

**Cost Reduction Options**:
- Use `--config fast` instead of `--config quality` (3-5x cheaper)
- Use `--config balanced` for optimal cost/quality trade-off
- Process fewer papers initially for testing

---

## Detailed Documentation

Each component has detailed documentation:

| Component | Documentation |
|-----------|---------------|
| **PDF Processing** | `process_pdfs/README.md` |
| **LLM Pipeline** | `metabeeai_llm/README.md` |
| **Benchmarking** | `llm_benchmarking/README.md` |
| **Data Analysis** | `query_database/README.md` |

---

## Tutorial: Process Your First 3 Papers

### Complete Example

```bash
# 1. Set up environment (one-time)
python -m venv venv
source venv/bin/activate
pip install metabeeai
cp env.example .env  # fill in API keys

# 2. Add 3 PDFs under YOURDATABASE/papers/
cp your_paper.pdf /path/to/YOURDATABASE/papers/PAPER001/PAPER001_main.pdf
# Repeat for PAPER002, PAPER003

# 3. Process PDFs → merged_v2.json
metabeeai process-pdfs --dir /path/to/YOURDATABASE/papers

# 4. Run LLM extraction (balanced preset recommended)
metabeeai llm --dir /path/to/YOURDATABASE/papers --config balanced
# Output: answers.json per paper

# 5. Review answers (saves answers_extended.json)
metabeeai review

# 6. Create benchmark dataset from GUI reviews
metabeeai prep-benchmark \
  --papers-dir /path/to/YOURDATABASE/papers \
  --output /path/to/YOURDATABASE/benchmark_data_gui.json

# 7. Run evaluation (choose a question or all)
metabeeai benchmark \
  --input /path/to/YOURDATABASE/benchmark_data_gui.json \
  --question bee_species

# 8. Visualize metrics
metabeeai plot-metrics \
  --results-dir /path/to/YOURDATABASE/deepeval_results

# 9. Find problem papers
metabeeai edge-cases --num-cases 5 \
  --results-dir /path/to/YOURDATABASE/deepeval_results \
  --output-dir /path/to/YOURDATABASE/edge_cases
```

**Expected time**:
- PDF processing: ~1-5 min per paper
- LLM extraction: ~2-3 min per paper
- Evaluation: <1 min per question

---


## Troubleshooting

### Common Issues

**Issue**: Module not found errors
```bash
# Solution: Activate virtual environment
source venv/bin/activate
```

**Issue**: API key errors
```bash
# Solution: Check .env file exists and has valid keys
cat .env
```

**Issue**: "Context too long" warnings
```bash
# Solution: Use faster models or reduce batch size
python llm_pipeline.py --config fast
```

**Issue**: Empty GUI window
```bash
# Solution: Check folder names are alphanumeric (not just numeric)
# The GUI now accepts folders like: 4YD2Y4J8, 76DQP2DC, etc.
```

**Issue**: UTF-8 BOM in CSV
```bash
# Solution: Scripts automatically handle BOM with utf-8-sig encoding
# If you see '\ufeff' in column names, the script handles this
```

---


## Best Practices

### 1. Start Small
- Test with 3-5 papers first
- Use `--limit` flags to test scripts
- Verify outputs before scaling up

### 2. Version Control
- Results are timestamped (no overwrites)
- Keep original `answers.json` files unchanged
- Reviewer answers go in separate files

### 3. Cost Management
- Use `--config fast` for initial testing
- Use `--config balanced` for production runs
- Test with specific papers using `--folders` before full runs

### 4. Quality Assurance
- Review edge cases to identify patterns
- Check low-scoring papers manually
- Validate LLM answers with GUI tool

---

## Additional Resources

### Documentation
- Full docs (installation, pipeline, API): [https://metabeeai.readthedocs.io](https://metabeeai.readthedocs.io)
- Module-specific references remain in `docs/` and the Read the Docs site (LLM benchmarking, PDF processing, LLM pipeline, review software, query database)

### External Links

- **Landing AI** (PDF to JSON conversion): https://landing.ai/
- **OpenAI API** (LLM use): https://platform.openai.com/docs
- **DeepEval Docs** (Benchmarking): https://docs.confident-ai.com/


---

**Project**: MetaBeeAI
**Last Updated**: November 14, 2025
**Written by**: Rachel Parkinson, Shuxiang Cao, Mikael Mieskolainen, Alasdair Wilson
**Contact**: Rachel Parkinson r.parkinson@qmul.ac.uk
