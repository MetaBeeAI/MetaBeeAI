# LLM Benchmarking Pipeline - MetaBeeAI

This folder contains scripts for comprehensive benchmarking and evaluation of LLM-generated answers against GUI reviewer annotations for bee research literature review.

## Overview

The pipeline evaluates LLM performance by comparing generated answers to reviewer-provided answers from the GUI interface. The evaluation uses 5 metrics:
- **Standard Metrics** (3): Faithfulness, Contextual Precision, Contextual Recall
- **G-Eval Metrics** (2): Completeness, Accuracy

---

## File Structure

### Core Scripts

| Script | Purpose |
|--------|---------|
| `prep_benchmark_data.py` | Prepare benchmark data from GUI reviewer answers (answers_extended.json) |
| `deepeval_benchmarking.py` | Run evaluation with all 5 metrics |
| `plot_metrics_comparison.py` | Visualize metrics across question types |
| `edge_cases.py` | Identify lowest-scoring papers for analysis |
| `run_benchmarking.py` | **Main wrapper script** - orchestrates entire pipeline |

### Configuration Files

| File | Purpose |
|------|---------|
| `../metabeeai_llm/questions.yml` | Full question definitions with instructions |
| `../config.py` | Configuration for data directories and paths |

---

## Quick Start

### Complete Pipeline (Recommended)

Run all steps in one command:

```bash
python run_benchmarking.py
```

This executes:
1. Prepare benchmark data
2. Run DeepEval evaluation
3. Generate visualizations
4. Identify edge cases

### Custom Options

```bash
# Run for specific question only
python run_benchmarking.py --question bee_species

# Skip data preparation (if already done)
python run_benchmarking.py --skip-prep

# Run only evaluation and plotting
python run_benchmarking.py --skip-prep --skip-edge-cases

# Custom batch size for evaluation
python run_benchmarking.py --batch-size 10 --max-retries 3
```

### Individual Steps

For more control, you can run each step individually:

```bash
# Step 1: Prepare benchmark data
python prep_benchmark_data.py

# Step 2: Run evaluation
python deepeval_benchmarking.py --question bee_species

# Step 3: Create visualizations
python plot_metrics_comparison.py

# Step 4: Identify edge cases
python edge_cases.py --num-cases 3
```

---

## Complete Workflow

### STEP 1: Prepare Benchmark Dataset

Convert GUI reviewer answers into evaluation format:

```bash
python prep_benchmark_data.py
```

**Input**:
- `data/papers/{paper_id}/answers_extended.json` (GUI reviewer answers)
- `data/papers/{paper_id}/answers.json` (LLM answers)
- `data/papers/{paper_id}/pages/merged_v2.json` (full paper text chunks)
- `metabeeai_llm/questions.yml` (question definitions)

**Output**:
- `data/benchmark_data_gui.json` (nested structure with papers and test_cases)

**Optional arguments**:
```bash
--papers-dir PATH       # Custom papers directory
--questions-yml PATH    # Custom questions file
--output PATH           # Custom output location
```

**Data Structure**:
The output uses an efficient nested structure:
```json
{
  "papers": {
    "002": {
      "context": ["chunk1", "chunk2", ...],
      "chunk_map": {"id1": "text1", ...}
    }
  },
  "test_cases": [
    {
      "paper_id": "002",
      "question_key": "bee_species",
      "input": "Question text",
      "actual_output": "LLM answer",
      "expected_output": "Reviewer answer",
      "retrieval_context": ["retrieved_chunk1", ...],
      "chunk_ids": ["id1", "id2", ...],
      "user_rating": 4
    }
  ]
}
```

**Key Features**:
- Full paper context stored once per paper (not duplicated for each question)
- Includes `user_rating` from GUI answers when available
- Efficient storage for papers with multiple questions

---

### STEP 2: Run Evaluation

Execute DeepEval benchmarking with all metrics:

```bash
# List available questions
python deepeval_benchmarking.py --list-questions

# Evaluate specific question type
python deepeval_benchmarking.py --question bee_species

# Evaluate all questions
python deepeval_benchmarking.py

# With custom settings
python deepeval_benchmarking.py \
  --question bee_species \
  --model gpt-4o \
  --batch-size 10 \
  --max-context-length 200000
```

**Command-line options**:
- `--question KEY` - Filter by question key (optional, dynamically determined from data)
- `--list-questions` - List all available question keys and exit
- `--input PATH` - Input benchmark file (default: auto-detect from config)
- `--limit N` - Limit to first N test cases
- `--batch-size N` - Test cases per batch (default: 25)
- `--max-retries N` - Max retries per batch (default: 5)
- `--model {gpt-4o,gpt-4o-mini,gpt-4-turbo,gpt-3.5-turbo}` - Evaluation model (default: gpt-4o)
- `--max-context-length N` - Max context chars (default: 200,000)
- `--use-retrieval-only` - Use only retrieval context (saves tokens)

**Input**:
- `data/benchmark_data_gui.json` (from Step 1)

**Output**:
- `data/deepeval_results/combined_results_{question}_{timestamp}.json`
- `data/deepeval_results/combined_results_{question}_{timestamp}.jsonl`

**Metrics Evaluated**:
1. **Faithfulness** - No contradictions with retrieval context
2. **Contextual Precision** - Relevant chunks ranked correctly
3. **Contextual Recall** - Expected output supported by retrieval
4. **Completeness [GEval]** - Covers all key points (threshold: 0.5)
5. **Accuracy [GEval]** - Accurate information alignment (threshold: 0.5)

**Cost Estimate**: ~$0.03 per test case with gpt-4o

---

### STEP 3: Visualize Results

Create comparison plots across question types:

```bash
python plot_metrics_comparison.py
```

**Input**:
- `data/deepeval_results/combined_results_*.json` (from Step 2)

**Output**:
- `data/deepeval_results/plots/{metric_name}.png` - Individual plots per metric
- `data/deepeval_results/plots/summary_metrics.png` - Summary plot across all metrics
- Console output with statistics table

**What it shows**:
- Individual bar charts for each metric (Faithfulness, Contextual Precision, Contextual Recall, Completeness, Accuracy)
- X-axis: Question types found in the data
- Y-axis: Mean score ± Standard Error
- Summary plot showing overall average per metric across all questions
- Error bars showing standard error of the mean

**Optional arguments**:
```bash
--results-dir PATH    # Custom results directory (default: auto-detect from config)
--output-dir PATH     # Custom output directory (default: same as results-dir)
```

---

### STEP 4: Identify Edge Cases (Optional)

Find lowest-scoring papers for detailed analysis:

```bash
# Get bottom 3 papers
python edge_cases.py --num-cases 3

# Get bottom 5 papers
python edge_cases.py --num-cases 5
```

**Command-line options**:
- `--num-cases N` - Number of edge cases per question (default: 3)
- `--results-dir PATH` - Results directory (default: auto-detect from config)
- `--output-dir PATH` - Output directory (default: auto-detect from config)
- `--openai-api-key KEY` - OpenAI API key for LLM summarization
- `--model MODEL` - OpenAI model for summarization (default: gpt-4o)
- `--generate-summaries-only` - Only generate LLM summaries for existing edge case files
- `--contextual-only` - Only run contextual measures analysis
- `--generate-contextual-summaries-only` - Only generate contextual LLM summaries

**Input**:
- `data/deepeval_results/combined_results_*.json` (from Step 2)

**Output**:
- `data/edge_cases/combined/combined_{question}.json` - Bottom N papers per question
- `data/edge_cases/combined/summary-report.json` - LLM-generated insights
- `data/edge_cases/edge-case-report.md` - Human-readable report
- `data/edge_cases/edge_cases_summary.json` - Overall statistics

**What it identifies**:
- Papers with lowest combined scores across all metrics
- Common failure patterns (via LLM analysis)
- Specific metric weaknesses per question type

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT DATA                                                  │
├─────────────────────────────────────────────────────────────┤
│ • data/papers/{paper_id}/answers_extended.json (GUI answers)│
│ • data/papers/{paper_id}/answers.json (LLM answers)         │
│ • data/papers/{paper_id}/pages/merged_v2.json (paper text)  │
│ • metabeeai_llm/questions.yml (question definitions)        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: PREPARE BENCHMARK DATASET                          │
├─────────────────────────────────────────────────────────────┤
│ Script: prep_benchmark_data.py                              │
│ Output: data/benchmark_data_gui.json                        │
│         - Nested structure: papers + test_cases             │
│         - Includes user_rating from GUI                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: RUN DEEPEVAL BENCHMARKING                         │
├─────────────────────────────────────────────────────────────┤
│ Script: deepeval_benchmarking.py                            │
│ Output: data/deepeval_results/combined_results_{q}_{time}.json│
│ Metrics: 5 total (3 standard + 2 G-Eval)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: VISUALIZE RESULTS                                   │
├─────────────────────────────────────────────────────────────┤
│ Script: plot_metrics_comparison.py                          │
│ Output: data/deepeval_results/plots/                        │
│         - Individual metric plots                           │
│         - Summary plot                                      │
│ Shows: Mean ± Standard Error for each metric               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: IDENTIFY EDGE CASES (Optional)                      │
├─────────────────────────────────────────────────────────────┤
│ Script: edge_cases.py                                       │
│ Output: data/edge_cases/                                    │
│         - Bottom N papers per question                      │
│         - LLM-generated insights                           │
│ Shows: Lowest-scoring papers with analysis                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Using the Wrapper Script

The `run_benchmarking.py` script provides a convenient way to run the entire pipeline or selected steps:

### Basic Usage

```bash
# Run complete pipeline
python run_benchmarking.py

# Run for specific question
python run_benchmarking.py --question bee_species
```

### Step Control

```bash
# Skip data preparation (if already done)
python run_benchmarking.py --skip-prep

# Skip evaluation (if already done)
python run_benchmarking.py --skip-evaluation

# Skip plotting
python run_benchmarking.py --skip-plotting

# Skip edge case analysis
python run_benchmarking.py --skip-edge-cases
```

### Passing Arguments to Individual Scripts

All arguments from individual scripts are available through the wrapper:

```bash
# Prep data arguments
python run_benchmarking.py --prep-papers-dir /custom/path --prep-output /custom/output.json

# Evaluation arguments
python run_benchmarking.py --question bee_species --batch-size 10 --model gpt-4o-mini

# Plotting arguments
python run_benchmarking.py --plot-results-dir /custom/results --plot-output-dir /custom/plots

# Edge case arguments
python run_benchmarking.py --num-edge-cases 5 --edge-model gpt-4o
```

### Argument Prefixes

Arguments are prefixed to avoid conflicts:
- `--prep-*` - Arguments for `prep_benchmark_data.py`
- No prefix - Arguments for `deepeval_benchmarking.py` (main evaluation)
- `--plot-*` - Arguments for `plot_metrics_comparison.py`
- `--edge-*` - Arguments for `edge_cases.py`

---

## Data Format

### Benchmark Data Format (`benchmark_data_gui.json`)

The new format uses a nested structure for efficiency:

```json
{
  "papers": {
    "002": {
      "context": ["chunk1", "chunk2", ...],
      "chunk_map": {"id1": "text1", "id2": "text2", ...}
    },
    "003": {
      "context": ["chunk1", ...],
      "chunk_map": {...}
    }
  },
  "test_cases": [
    {
      "paper_id": "002",
      "question_key": "bee_species",
      "input": "What species of bee...",
      "actual_output": "LLM answer",
      "expected_output": "Reviewer answer",
      "retrieval_context": ["retrieved_chunk1", ...],
      "chunk_ids": ["id1", "id2", ...],
      "user_rating": 4
    },
    {
      "paper_id": "002",
      "question_key": "pesticides",
      ...
    }
  ]
}
```

**Benefits**:
- Full paper context stored once per paper (not duplicated)
- Efficient for papers with multiple questions
- Includes user ratings from GUI interface

### Evaluation Results Format

```json
[
  {
    "test_case_index": 0,
    "name": "paper_002_case_0",
    "paper_id": "002",
    "question_key": "bee_species",
    "input": "Question text",
    "actual_output": "LLM answer",
    "expected_output": "Reviewer answer",
    "success": false,
    "additional_metadata": {
      "paper_id": "002",
      "question_key": "bee_species",
      "chunk_ids": [...],
      "user_rating": 4
    },
    "metrics_data": [
      {
        "name": "Faithfulness",
        "score": 0.85,
        "threshold": 0.5,
        "success": true,
        "reason": "Explanation...",
        "strict_mode": false,
        "evaluation_model": "gpt-4o",
        "error": null,
        "evaluation_cost": 0.002
      }
    ]
  }
]
```

**Note**: `context` and `retrieval_context` are NOT saved in results files to save space.

---

## Configuration

All scripts use `config.py` for default paths:

- **Data directory**: Determined by `get_data_dir()` from `config.py`
- **Papers directory**: Determined by `get_papers_dir()` from `config.py`
- **Output locations**:
  - Benchmark data: `{data_dir}/benchmark_data_gui.json`
  - Evaluation results: `{data_dir}/deepeval_results/`
  - Plots: `{data_dir}/deepeval_results/plots/`
  - Edge cases: `{data_dir}/edge_cases/`

This ensures consistency across all scripts and makes it easy to change data locations.

---

## Prerequisites

1. **Environment Setup**:
```bash
cd /Users/user/Documents/MetaBeeAI/MetaBeeAI
source venv/bin/activate
```

2. **API Keys**: Create `.env` file in project root:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

3. **Required Data**: Ensure you have:
- LLM answers: `data/papers/{paper_id}/answers.json`
- Paper text: `data/papers/{paper_id}/pages/merged_v2.json`
- Reviewer answers: `data/papers/{paper_id}/answers_extended.json` (GUI format)

4. **Required Packages**:
```bash
pip install deepeval openai python-dotenv pyyaml numpy matplotlib pandas
```

---

## Cost Breakdown

### Typical Costs (example: 10 papers, multiple questions, gpt-4o)

| Step | Description | Cost |
|------|-------------|------|
| **Step 1** | Prepare benchmark | $0.00 (no LLM) |
| **Step 2** | Evaluation (5 metrics × N entries) | ~$0.03 per entry |
| **Step 3** | Plotting | $0.00 (no LLM) |
| **Step 4** | Edge cases (3 per question) | ~$0.05 |
| **TOTAL** | | **~$0.03 per entry + $0.05 edge cases** |

**Cost per entry**: ~$0.032 (for 5 metrics with gpt-4o)

---

## Troubleshooting

### Issue: "Context too long" warnings

**Solution 1**: Increase limit
```bash
python deepeval_benchmarking.py --max-context-length 300000
```

**Solution 2**: Use retrieval context only
```bash
python deepeval_benchmarking.py --use-retrieval-only
```

### Issue: Batch failures

**Solution**: Reduce batch size
```bash
python deepeval_benchmarking.py --batch-size 10
```

### Issue: Missing reviewer answers

**Check**:
1. `answers_extended.json` exists in paper folder
2. File contains `QUESTIONS` structure
3. Paper folder names match paper IDs

### Issue: "No question keys found"

**Check**:
1. Benchmark data file exists and is valid JSON
2. File contains `test_cases` array
3. Test cases have `question_key` field

### Issue: Empty results files

**Check**:
1. OpenAI API key is valid in `.env` file
2. Sufficient API credits
3. Check error messages in console output

---

## Output Directory Structure

```
data/
├── benchmark_data_gui.json          # Benchmark dataset
├── deepeval_results/                 # Evaluation results
│   ├── combined_results_*.json
│   ├── combined_results_*.jsonl
│   └── plots/
│       ├── faithfulness.png
│       ├── contextual_precision.png
│       ├── contextual_recall.png
│       ├── completeness_geval.png
│       ├── accuracy_geval.png
│       └── summary_metrics.png
└── edge_cases/                      # Edge case analysis
    ├── combined/
    │   ├── combined_{question}.json
    │   └── summary-report.json
    ├── edge_cases_summary.json
    └── edge-case-report.md
```

---

## Tips and Best Practices

### 1. Running Evaluations Efficiently

- **Start with one question**: Test with `--question bee_species --limit 5` first
- **List available questions**: Use `--list-questions` to see what's available
- **Use appropriate batch size**: 10-25 for most papers, 5-10 for very long papers
- **Monitor costs**: Check `evaluation_cost` in results to track spending

### 2. Context Management

- **Default (200K chars)**: Handles most papers well
- **Very long papers**: Use `--use-retrieval-only` flag
- **GPT-4o recommended**: Better quality, handles longer contexts

### 3. Incremental Processing

Results are saved incrementally:
- Each batch is saved immediately
- Safe to interrupt and resume
- No data loss on failures

### 4. Analyzing Results

1. **Start with visualization**: Run `plot_metrics_comparison.py` first
2. **Identify weak areas**: Look at metrics with lowest scores
3. **Deep dive**: Use `edge_cases.py` to find specific problem papers
4. **Read markdown report**: Human-friendly summary of issues

---

## Metric Interpretation Guide

### Score Ranges

| Score | Interpretation |
|-------|----------------|
| **0.9 - 1.0** | Excellent - Very close match to reviewer |
| **0.7 - 0.9** | Good - Most key points covered |
| **0.5 - 0.7** | Moderate - Some missing or incorrect info |
| **0.3 - 0.5** | Poor - Significant gaps or errors |
| **0.0 - 0.3** | Very Poor - Major discrepancies |

### Metric-Specific Interpretation

**Faithfulness** (High is better):
- Score < 0.7: LLM hallucinating or contradicting source text
- Action: Check retrieval quality, review chunk selection

**Contextual Precision** (High is better):
- Score < 0.7: Irrelevant chunks ranked highly
- Action: Improve retrieval ranking, adjust chunk relevance scoring

**Contextual Recall** (High is better):
- Score < 0.7: Missing important context chunks
- Action: Increase max_chunks, lower min_score threshold

**Completeness [GEval]** (High is better):
- Score < 0.5: Missing key points from expected answer
- Action: Review prompt, check if info exists in paper

**Accuracy [GEval]** (High is better):
- Score < 0.5: Inaccurate information vs expected answer
- Action: Check if LLM misinterpreting source text

---

## Advanced Usage

### Custom Evaluation Settings

```bash
# Use cheaper model for initial tests
python deepeval_benchmarking.py --model gpt-4o-mini

# Process only retrieval context (faster, cheaper)
python deepeval_benchmarking.py --use-retrieval-only

# Handle very long papers
python deepeval_benchmarking.py --max-context-length 300000 --batch-size 10

# Limit for testing
python deepeval_benchmarking.py --question bee_species --limit 3
```

### Using the Wrapper with Custom Arguments

```bash
# Full pipeline with custom settings
python run_benchmarking.py \
  --question bee_species \
  --batch-size 10 \
  --model gpt-4o-mini \
  --num-edge-cases 5

# Skip steps and customize
python run_benchmarking.py \
  --skip-prep \
  --skip-edge-cases \
  --plot-output-dir /custom/plots
```

---

## References

- **DeepEval Documentation**: https://docs.confident-ai.com/
- **GPT-4o Model Card**: https://platform.openai.com/docs/models/gpt-4o
- **Project Config**: `../config.py`
- **Question Definitions**: `../metabeeai_llm/questions.yml`
- **LLM Pipeline**: `../metabeeai_llm/llm_pipeline.py`

---

## Support

For issues or questions:
1. Check this README first
2. Review error messages in console output
3. Check that all input files exist and are properly formatted
4. Verify API keys and credits
5. Use `--list-questions` to verify available question keys
6. Consult DeepEval documentation for metric-specific issues

---

**Last Updated**: 2025  
**Pipeline Version**: 3.0 (Simplified GUI-based pipeline)
