# LLM Pipeline

This submodule provides the LLM-powered question-answering pipeline for extracting structured information from scientific papers.

## Overview

The pipeline processes PDF documents (already converted to JSON chunks) and answers a predefined set of questions about experimental design, study populations, methodologies, and findings. Users primarily interact with the system by modifying the `questions.yml` file.

## Installation

This submodule is part of the `metabeeai` package. Install it via:

```bash
pip install metabeeai
```

Or if installing from source:

```bash
pip install -e /path/to/MetaBeeAI
```

**Required dependencies**: litellm, pydantic, pyyaml, asyncio, tqdm

### Key Features

**Intelligent Answer Merging**: Add new questions to existing papers without losing previous results. The pipeline automatically merges new answers with existing `answers.json` files.

**Flexible Question Configuration**: Customize questions, instructions, examples, and relevance thresholds via `questions.yml` without touching code.

**Alphanumeric Folder Support**: Process papers in any folder naming format (e.g., `283C6B42`, `4KV2ZB36`) - no numeric constraints.

**Parallel Processing**: Configurable batch processing and concurrency for efficient large-scale analysis.

**Quality Assessment**: Each answer includes confidence metrics, source chunk IDs, and reasoning for transparency.

---

## Core Files

### 1. `questions.yml` - **Main User Interface**

**This is the file you'll interact with to customize the pipeline.**

The YAML file defines all questions the pipeline will ask. Each question has the following fields:

```yaml
question_name:
  question: "Your question text here"
  instructions:
    - "Specific instruction 1"
    - "Specific instruction 2"
  output_format: "Description of expected output format"
  example_output:
    - "Example of a good answer"
    - "Another good example"
  bad_example_output:
    - "Example to avoid"
  no_info_response: "Response when information is not found"
  max_chunks: 5  # Maximum number of text chunks to analyze
  description: "Brief description of this question"
```

#### Field Explanations:

- **`question`**: The actual question text sent to the LLM
- **`instructions`**: List of specific guidelines for answering (e.g., "Extract species names only from methodology sections")
- **`output_format`**: Describes how the answer should be structured (e.g., "Numbered list: '1. Species A; 2. Species B'")
- **`example_output`**: Good examples that show the desired answer format - the LLM uses these as templates
- **`bad_example_output`**: Examples to avoid - helps the LLM understand common mistakes
- **`no_info_response`**: What to return when the paper doesn't contain the requested information
- **`max_chunks`**: Controls how many text chunks from the paper will be analyzed (higher = more comprehensive but slower)
- **`description`**: Internal note about the question's purpose

---

### 2. `llm_pipeline.py` - Main Pipeline Runner

**Purpose**: Orchestrates the entire question-answering process across multiple papers.

**Key Functions**:
- `get_literature_answers(json_path)` - Processes a single paper with all questions
- `process_papers(base_dir, paper_folders)` - Batch processes multiple papers

**How to run** (CLI - Recommended):

When the `metabeeai` package is installed, use the CLI command:

```bash
# Process all papers in the default directory
metabeeai llm

# Process all papers in a specific directory
metabeeai llm --dir /path/to/papers

# Process specific paper folders by name
metabeeai llm --folders 283C6B42 3ZHNVADM 4KV2ZB36

# Process specific folders in a custom directory
metabeeai llm --dir /path/to/papers --folders PAPER_ID1 PAPER_ID2

# Use different models for chunk selection and answer generation
metabeeai llm --relevance-model "openai/gpt-4o-mini" --answer-model "openai/gpt-4o"

# Use high-quality models for both stages
metabeeai llm --relevance-model "openai/gpt-4o" --answer-model "openai/gpt-4o"

# Use predefined configurations (easier!)
metabeeai llm --config fast      # Fast & cheap processing
metabeeai llm --config balanced  # Balanced speed and quality (recommended)
metabeeai llm --config quality   # High quality for critical analysis

# Overwrite existing answers.json files
metabeeai llm --overwrite
```

**Note**: For Python module syntax alternatives, see the [Alternative: Python Module Syntax](#alternative-python-module-syntax) section below.

**Input data format**: Expects papers in folders with any alphanumeric names like:
```
papers/
├── 283C6B42/
│   └── pages/
│       └── merged_v2.json  # Required file
├── 3ZHNVADM/
│   └── pages/
│       └── merged_v2.json
├── 4KV2ZB36/
│   └── pages/
│       └── merged_v2.json
...
```

**Output**: Creates `answers.json` in each paper folder with structured responses.

**Important**: The pipeline now **merges** new answers with existing ones. If `answers.json` already exists:
- New questions (e.g., "welfare") will be **added** to the file
- Existing questions (e.g., "design", "population") will be **updated** if they're in the current run
- Questions not in the current run will be **preserved** as-is
- This allows you to add new question types incrementally without losing previous results

---

## Model Selection

The pipeline uses two different LLM models for different stages:

### **Chunk Selection Model** (`--relevance-model`)
- **Purpose**: Selects the most relevant text chunks for each question
- **Default**: `openai/gpt-4o-mini` (fast and cost-effective)
- **Recommended**: `openai/gpt-4o-mini` for speed, `openai/gpt-4o` for accuracy

### **Answer Generation Model** (`--answer-model`)
- **Purpose**: Generates answers from individual chunks and synthesizes final responses
- **Default**: `openai/gpt-4o` (high quality)
- **Recommended**: `openai/gpt-4o` for best results, `openai/gpt-4o-mini` for speed

### **Model Combinations**:

| Use Case | Relevance Model | Answer Model | Description |
|----------|----------------|--------------|-------------|
| **Fast & Cheap** | `gpt-4o-mini` | `gpt-4o-mini` | Fastest processing, lowest cost |
| **Balanced** | `gpt-4o-mini` | `gpt-4o` | Good chunk selection, high-quality answers |
| **High Quality** | `gpt-4o` | `gpt-4o` | Best accuracy, slower processing |

### **Command Line Examples**:
```bash
# Use defaults (from pipeline_config.py)
metabeeai llm

# Use predefined configurations (recommended)
metabeeai llm --config fast      # Fast & cheap processing
metabeeai llm --config balanced  # Balanced speed and quality
metabeeai llm --config quality   # High quality for critical analysis

# Custom model combinations
metabeeai llm --relevance-model "openai/gpt-4o-mini" --answer-model "openai/gpt-4o-mini"
metabeeai llm --relevance-model "openai/gpt-4o-mini" --answer-model "openai/gpt-4o"
metabeeai llm --relevance-model "openai/gpt-4o" --answer-model "openai/gpt-4o"
```

### **Predefined Configurations**:

The easiest way to use different model combinations is with the `--config` option:

| Configuration | Command | Relevance Model | Answer Model | Use Case |
|---------------|---------|----------------|--------------|----------|
| **Fast** | `--config fast` | `gpt-4o-mini` | `gpt-4o-mini` | High-volume processing, cost-sensitive |
| **Balanced** | `--config balanced` | `gpt-4o-mini` | `gpt-4o` | **Recommended for most use cases** |
| **Quality** | `--config quality` | `gpt-4o` | `gpt-4o` | Critical analysis, maximum accuracy |

### **Custom Model Selection**:
```bash
# Fast processing with mini models
metabeeai llm --relevance-model "openai/gpt-4o-mini" --answer-model "openai/gpt-4o-mini"

# Balanced approach (recommended)
metabeeai llm --relevance-model "openai/gpt-4o-mini" --answer-model "openai/gpt-4o"

# High quality for critical analysis
metabeeai llm --relevance-model "openai/gpt-4o" --answer-model "openai/gpt-4o"
```

---

---

### 4. `pipeline_config.py` - Configuration Settings

**Purpose**: Configure LLM models and parallel processing parameters.

**Key Settings**:
- **Model Selection**: Choose between GPT-4o-mini (fast), GPT-4o (high quality), or hybrid
- **Parallel Processing**: Batch sizes and concurrency limits
- **Performance Tuning**: Enable/disable progress bars, logging, etc.

**How to modify**:
Edit the file and change `CURRENT_CONFIG`:
```python
CURRENT_CONFIG = QUALITY_CONFIG  # High quality
# CURRENT_CONFIG = FAST_CONFIG   # Fast & cheap
# CURRENT_CONFIG = BALANCED_CONFIG  # Balanced
```

**View current configuration** (CLI):
```bash
python -m metabeeai.metabeeai_llm.pipeline_config
```

**Note**: For Python module syntax alternatives, see the [Alternative: Python Module Syntax](#alternative-python-module-syntax) section below.

---

### 5. `json_multistage_qa.py` - Core Q&A Engine (Library)

**Purpose**: The underlying LLM question-answering engine (used by `llm_pipeline.py`).

**Key Functions**:
- `ask_json(question, json_path, relevance_model, answer_model)` - Answers a single question about a paper
- `get_answer(question, chunk, model)` - Generates answers from individual text chunks
- `filter_all_chunks(question, chunks, max_chunks, model)` - Selects most relevant chunks
- `reflect_answers(question, chunks, model)` - Synthesizes final answer from multiple chunks

**Usage**: This is primarily a library module. It can be imported and used programmatically:

```python
from metabeeai.metabeeai_llm.json_multistage_qa import ask_json
import asyncio

result = asyncio.run(ask_json(
    question="What methodology was used in this study?",
    json_path="papers/001/pages/merged_v2.json",
    relevance_model="openai/gpt-4o-mini",
    answer_model="openai/gpt-4o"
))
print(result['answer'])
```

**Note**: For testing purposes, it can also be run directly as a script (see Python module syntax section below).

---

## Quick Start Guide

### Prerequisites

1. **Environment Setup**:
```bash
# Activate your virtual environment
source ../venv/bin/activate  # On Mac/Linux
# Or: ..\venv\Scripts\activate  # On Windows
```

2. **API Keys**: Configure your API keys in the `.env` file:
```bash
# Copy the example environment file
cp ../env.example ../.env

# Edit the .env file and add your API key
# OPENAI_API_KEY=your_openai_api_key_here
```

The `.env` file is located in the project root directory and is hidden from git for security.

3. **Data Format**: Your papers must be processed into the required JSON format:
```json
{
  "data": {
    "chunks": [
      {
        "chunk_id": "unique_id",
        "text": "The extracted text content...",
        "chunk_type": "paragraph",
        "metadata": {...}
      }
    ]
  }
}
```

This format is generated automatically by the PDF processing pipeline (see `../process_pdfs/`).

---

### Basic Usage

**Step 1: Customize Questions** (Optional)

Edit `questions.yml` to add/modify questions. See the examples in the file.

**Step 2: Process Papers**

```bash
# Process all papers in the default directory
metabeeai llm

# Process specific paper folders by name
metabeeai llm --folders 283C6B42 3ZHNVADM 4KV2ZB36

# Process all papers in a custom directory
metabeeai llm --dir /path/to/papers

# Use predefined configuration (recommended)
metabeeai llm --config balanced
```

**Step 3: Review Results**

Check the `answers.json` file in each paper folder:
```json
{
  "QUESTIONS": {
    "methodology": {
      "answer": "Randomized controlled trial with 20 subjects per group",
      "reason": "Methodology found in methods section",
      "chunk_ids": ["chunk_001", "chunk_003"]
    },
    ...
  }
}
```

**Step 4: Adding New Questions Later (Optional)**

The pipeline intelligently merges results, so you can add new questions without losing existing work:

```bash
# 1. Add a new question to questions.yml (e.g., "findings")
# 2. Re-run the pipeline
metabeeai llm

# 3. Your answers.json now contains BOTH old and new questions:
# {
#   "QUESTIONS": {
#     "design": {...},      ← Preserved from previous run
#     "population": {...},  ← Preserved from previous run
#     "findings": {...}     ← Newly added
#   }
# }
```

**How Merging Works:**
- **Existing questions not in current run** → Preserved unchanged
- **New questions** → Added to the file
- **Questions in both old file and current run** → Updated with new results

**Pro Tip**: To add new questions without updating existing ones, comment out the existing questions in `questions.yml` before running.

---

## Advanced Configuration

### Adjusting Question Sensitivity

In `questions.yml`, tune these parameters:

- **`max_chunks`**: Increase for more comprehensive coverage (slower)
  - Recommended: 3-7 chunks
  - Higher values for complex questions requiring broad context

### Example Tuning:

```yaml
# For questions where information might be scattered
pesticides:
  max_chunks: 7  # More chunks for comprehensive coverage

# For questions requiring precise information
bee_species:
  max_chunks: 3  # Fewer chunks for focused analysis
```

---

## Understanding Output Structure

Each question returns:
```json
{
  "answer": "The synthesized answer",
  "reason": "Explanation of how the answer was derived",
  "chunk_ids": ["id1", "id2"],  // Source chunks used
  "relevance_info": {
    "total_chunks_processed": 50,
    "relevant_chunks_found": 3,
    "question_config": {...}
  },
  "question_metadata": {
    "instructions": [...],
    "example_output": [...]
  },
  "quality_assessment": {
    "confidence": "high|medium|low",
    "issues": [],
    "recommendations": []
  }
}
```

---

## Troubleshooting

### "No relevant chunks found"
- **Cause**: Question is too specific or chunks don't contain the information
- **Fix**: Increase `max_chunks` in `questions.yml` or rephrase the question

### "Rate limit exceeded"
- **Cause**: Too many parallel requests to OpenAI API
- **Fix**: Adjust `pipeline_config.py` to reduce batch sizes and concurrent requests

### "KeyError" or missing fields
- **Cause**: Input JSON doesn't match expected format
- **Fix**: Verify your merged_v2.json files have the correct structure (see Data Format section)

### Slow processing
- **Cause**: Using high-quality models or large batch sizes
- **Fix**: Switch to `FAST_CONFIG` in `pipeline_config.py` or reduce `max_chunks` in `questions.yml`

---

## Adding New Questions Incrementally

The pipeline supports adding new question types to existing papers without losing previous answers.

### Workflow for Adding New Questions:

**Example Scenario**: You already have "design" and "population" answers, and want to add "findings" questions.

1. **Edit `questions.yml`** to add your new question:

```yaml
QUESTIONS:
  design:
    # ... existing question ...

  population:
    # ... existing question ...

  welfare:  # NEW QUESTION
    question: "What findings were reported?"
    # ... configuration ...
```

2. **Run the pipeline** - it will automatically merge results:
```bash
# Process all papers - adds "findings" answers while keeping "design" and "population"
metabeeai llm

# Or process specific papers
metabeeai llm --folders 283C6B42 3ZHNVADM
```

3. **Result**: Your `answers.json` will now contain all three question types:
```json
{
  "QUESTIONS": {
    "design": { ... },      // Preserved from previous run
    "population": { ... },  // Preserved from previous run
    "findings": { ... }     // Newly added
  }
}
```

### Important Notes:
- **Safe to re-run**: Old answers are preserved if not in current `questions.yml`
- **Selective updates**: Only run specific questions by temporarily removing others from `questions.yml`
- **Updates overwrite**: If you re-run a question that already exists, it will be updated with new results
- **Tip**: Comment out existing questions in `questions.yml` if you only want to add new ones

---

## Adding New Questions

1. Open `questions.yml`
2. Add a new entry following this template:

```yaml
your_question_name:
  question: "What information do you want to extract?"
  instructions:
    - "Be specific about what to include/exclude"
    - "Mention which sections to look in"
  output_format: "Describe the expected format"
  example_output:
    - "1. Example answer following the format"
  bad_example_output:
    - "Avoid answers like this that are too verbose"
  no_info_response: "Information not found"
  max_chunks: 5
  description: "Brief note about this question"
```

3. The pipeline will automatically detect and process your new question on the next run.

---

## Related Documentation

- **PDF Processing**: See `../process_pdfs/README.md` for converting PDFs to the required JSON format
- **Data Analysis**: See `../query_database/` for analyzing extracted data
- **Benchmarking**: See `../llm_benchmarking/` for quality evaluation

---

## Dependencies

Core dependencies are included when installing the `metabeeai` package:
- `litellm` - Unified LLM API interface
- `pydantic` - Data validation
- `pyyaml` - YAML parsing
- `asyncio` - Async processing (built-in)
- `tqdm` - Progress bars

If installing from source, dependencies can be installed via:
```bash
pip install -r requirements.txt
```

---

## Tips for Best Results

1. **Write specific instructions**: The more detailed your instructions in `questions.yml`, the better the results
2. **Provide good examples**: The LLM learns from `example_output` - make them representative
3. **Test on sample papers**: Use `test_comprehensive_pipeline.py` before processing hundreds of papers
4. **Monitor costs**: GPT-4o is expensive - use FAST_CONFIG for initial testing
5. **Iterate on questions**: Review results and refine instructions based on what you see

---

## Alternative: Python Module Syntax

Instead of using the CLI commands, you can also run the scripts directly as Python modules. This is useful if you need to integrate the functionality into other Python scripts or prefer direct module execution.

### Running the Main Pipeline

```bash
# Process all papers in the default directory
python -m metabeeai.metabeeai_llm.llm_pipeline

# Process all papers in a specific directory
python -m metabeeai.metabeeai_llm.llm_pipeline --dir /path/to/papers

# Process specific paper folders by name
python -m metabeeai.metabeeai_llm.llm_pipeline --folders 283C6B42 3ZHNVADM 4KV2ZB36

# Use predefined configurations
python -m metabeeai.metabeeai_llm.llm_pipeline --config balanced

# Use custom models
python -m metabeeai.metabeeai_llm.llm_pipeline --relevance-model "openai/gpt-4o-mini" --answer-model "openai/gpt-4o"
```

### Viewing Configuration

```bash
# View current pipeline configuration
python -m metabeeai.metabeeai_llm.pipeline_config
```

### Using the Q&A Engine Programmatically

```python
import asyncio
from metabeeai.metabeeai_llm.json_multistage_qa import ask_json

# Answer a single question about a paper
result = asyncio.run(ask_json(
    question="What methodology was used in this study?",
    json_path="papers/001/pages/merged_v2.json",
    relevance_model="openai/gpt-4o-mini",
    answer_model="openai/gpt-4o"
))
print(result['answer'])
```

### Importing Functions for Custom Scripts

```python
from metabeeai.metabeeai_llm.llm_pipeline import get_literature_answers, process_papers
from metabeeai.metabeeai_llm.json_multistage_qa import ask_json, filter_all_chunks

# Use functions programmatically in your own scripts
# ...
```

All command-line arguments are identical between CLI commands and Python module syntax. The only difference is the invocation method.

---

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review existing test scripts for usage examples
3. Verify your data format matches the requirements

---

**Last Updated**: Nov 21 2025
