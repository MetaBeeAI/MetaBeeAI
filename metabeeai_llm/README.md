# MetaBeeAI LLM Pipeline

This folder contains the LLM-powered question-answering pipeline for extracting structured information from scientific papers.

## Overview

The pipeline processes PDF documents (already converted to JSON chunks) and answers a predefined set of questions about primate welfare, experimental design, study populations, and findings. Users primarily interact with the system by modifying the `questions.yml` file.

### Key Features

✨ **Intelligent Answer Merging**: Add new questions to existing papers without losing previous results. The pipeline automatically merges new answers with existing `answers.json` files.

🔧 **Flexible Question Configuration**: Customize questions, instructions, examples, and relevance thresholds via `questions.yml` without touching code.

📁 **Alphanumeric Folder Support**: Process papers in any folder naming format (e.g., `283C6B42`, `4KV2ZB36`) - no numeric constraints.

⚡ **Parallel Processing**: Configurable batch processing and concurrency for efficient large-scale analysis.

📊 **Quality Assessment**: Each answer includes confidence metrics, source chunk IDs, and reasoning for transparency.

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
  min_score: 0.4  # Minimum relevance score (0-1)
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
- **`min_score`**: Relevance threshold for chunk selection (lower = more permissive, higher = stricter filtering)
- **`description`**: Internal note about the question's purpose

---

### 2. `llm_pipeline.py` - Main Pipeline Runner

**Purpose**: Orchestrates the entire question-answering process across multiple papers.

**Key Functions**:
- `get_literature_answers(json_path)` - Processes a single paper with all questions
- `process_papers(base_dir, paper_folders)` - Batch processes multiple papers

**How to run**:
```bash
# Process all papers in the default directory
python llm_pipeline.py

# Process all papers in a specific directory
python llm_pipeline.py --dir /path/to/papers

# Process specific paper folders by name
python llm_pipeline.py --folders 283C6B42 3ZHNVADM 4KV2ZB36

# Process specific folders in a custom directory
python llm_pipeline.py --dir /path/to/papers --folders PAPER_ID1 PAPER_ID2
```

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

### 3. `json_multistage_qa.py` - Core Q&A Engine

**Purpose**: The underlying LLM question-answering engine (used by `llm_pipeline.py`).

**Key Functions**:
- `ask_json(question, json_path)` - Answers a single question about a paper
- `get_answer(question, chunk)` - Generates answers from individual text chunks
- `filter_all_chunks(question, chunks)` - Selects most relevant chunks
- `reflect_answers(question, chunks)` - Synthesizes final answer from multiple chunks

**How to run directly** (for testing individual questions):
```python
import asyncio
from json_multistage_qa import ask_json

result = asyncio.run(ask_json(
    question="What species of bee were tested?",
    json_path="papers/001/pages/merged_v2.json"
))
print(result['answer'])
```

**Process flow**:
1. Loads question configuration from `questions.yml`
2. Filters relevant text chunks using LLM-based selection
3. Queries each chunk independently for answers
4. Synthesizes a final answer from all chunk responses
5. Returns structured output with answer, reasoning, and source chunk IDs

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

View current configuration:
```bash
python pipeline_config.py
```

---

### 5. `unique_chunk_id.py` - Chunk ID Validator

**Purpose**: Verifies that all chunk IDs in the processed JSON files are unique (quality control).

**How to run**:
```bash
python unique_chunk_id.py --dir data/papers
```

**Output**: Generates a log file identifying any duplicate chunk IDs across papers.

---

### 6. `test_comprehensive_pipeline.py` - Validation Script

**Purpose**: Tests the entire pipeline on sample papers to ensure everything works correctly.

**How to run**:
```bash
python test_comprehensive_pipeline.py
```

**What it does**:
- Verifies file structure (checks for `merged_v2.json` files)
- Processes test papers with all questions
- Validates output structure contains required fields
- Saves results to `test_comprehensive_results.json`

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
python llm_pipeline.py

# Process specific paper folders by name
python llm_pipeline.py --folders 283C6B42 3ZHNVADM 4KV2ZB36

# Process all papers in a custom directory
python llm_pipeline.py --dir /path/to/papers
```

**Step 3: Review Results**

Check the `answers.json` file in each paper folder:
```json
{
  "QUESTIONS": {
    "bee_species": {
      "answer": "1. Apis mellifera carnica; 2. Bombus terrestris",
      "reason": "Species found in methodology section",
      "chunk_ids": ["chunk_001", "chunk_003"]
    },
    ...
  }
}
```

**Step 4: Adding New Questions Later (Optional)**

The pipeline intelligently merges results, so you can add new questions without losing existing work:

```bash
# 1. Add a new question to questions.yml (e.g., "welfare")
# 2. Re-run the pipeline
python llm_pipeline.py

# 3. Your answers.json now contains BOTH old and new questions:
# {
#   "QUESTIONS": {
#     "design": {...},      ← Preserved from previous run
#     "population": {...},  ← Preserved from previous run  
#     "welfare": {...}      ← Newly added
#   }
# }
```

**How Merging Works:**
- ✅ **Existing questions not in current run** → Preserved unchanged
- ✅ **New questions** → Added to the file
- ⚠️ **Questions in both old file and current run** → Updated with new results

**Pro Tip**: To add new questions without updating existing ones, comment out the existing questions in `questions.yml` before running.

---

## Advanced Configuration

### Adjusting Question Sensitivity

In `questions.yml`, tune these parameters:

- **`max_chunks`**: Increase for more comprehensive coverage (slower)
  - Recommended: 3-7 chunks
  - Higher values for complex questions requiring broad context

- **`min_score`**: Adjust relevance filtering
  - Lower (0.1-0.3): Permissive, captures more context
  - Medium (0.4-0.6): Balanced
  - Higher (0.7-1.0): Strict, only highly relevant chunks

### Example Tuning:

```yaml
# For questions where information might be scattered
pesticides:
  max_chunks: 7
  min_score: 0.2  # Lower threshold to catch all mentions

# For questions requiring precise information
bee_species:
  max_chunks: 3
  min_score: 0.7  # Higher threshold for explicit statements
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
- **Fix**: Lower `min_score` in `questions.yml` or rephrase the question

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

**Example Scenario**: You already have "design" and "population" answers, and want to add "welfare" questions.

1. **Edit `questions.yml`** to add your new question:

```yaml
QUESTIONS:
  design:
    # ... existing question ...
  
  population:
    # ... existing question ...
  
  welfare:  # NEW QUESTION
    question: "What welfare measures were used?"
    # ... configuration ...
```

2. **Run the pipeline** - it will automatically merge results:
```bash
# Process all papers - adds "welfare" answers while keeping "design" and "population"
python llm_pipeline.py

# Or process specific papers
python llm_pipeline.py --folders 283C6B42 3ZHNVADM
```

3. **Result**: Your `answers.json` will now contain all three question types:
```json
{
  "QUESTIONS": {
    "design": { ... },      // Preserved from previous run
    "population": { ... },  // Preserved from previous run
    "welfare": { ... }      // Newly added
  }
}
```

### Important Notes:
- ✅ **Safe to re-run**: Old answers are preserved if not in current `questions.yml`
- ✅ **Selective updates**: Only run specific questions by temporarily removing others from `questions.yml`
- ⚠️ **Updates overwrite**: If you re-run a question that already exists, it will be updated with new results
- 💡 **Tip**: Comment out existing questions in `questions.yml` if you only want to add new ones

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
  min_score: 0.4
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

Core dependencies (install via `pip install -r ../requirements.txt`):
- `litellm` - Unified LLM API interface
- `pydantic` - Data validation
- `pyyaml` - YAML parsing
- `asyncio` - Async processing
- `tqdm` - Progress bars

---

## Tips for Best Results

1. **Write specific instructions**: The more detailed your instructions in `questions.yml`, the better the results
2. **Provide good examples**: The LLM learns from `example_output` - make them representative
3. **Test on sample papers**: Use `test_comprehensive_pipeline.py` before processing hundreds of papers
4. **Monitor costs**: GPT-4o is expensive - use FAST_CONFIG for initial testing
5. **Iterate on questions**: Review results and refine instructions based on what you see

---

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review existing test scripts for usage examples
3. Verify your data format matches the requirements

---

**Last Updated**: October 2025

