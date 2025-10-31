# LLM Benchmarking Pipeline - Primate Welfare Literature Review

This folder contains scripts for comprehensive benchmarking and evaluation of LLM-generated answers against human reviewer annotations for primate welfare literature review.

## Overview

The pipeline evaluates LLM performance on three question types:
1. **Design** - Study overview, number of groups, sample size
2. **Population** - Species, sex, age, location, housing details
3. **Welfare** - Welfare measures, links to wellbeing/stress

The evaluation uses 5 metrics:
- **Standard Metrics** (3): Faithfulness, Contextual Precision, Contextual Recall
- **G-Eval Metrics** (2): Completeness, Accuracy

---

## File Structure

### Core Scripts

| Script | Purpose |
|--------|---------|
| `prep_benchmark_data.py` | Prepare benchmark data from CSV reviewer answers |
| `prep_benchmark_data_from_GUI_answers.py` | Prepare benchmark data from GUI reviewer answers |
| `deepeval_benchmarking.py` | Run evaluation with all 5 metrics |
| `plot_metrics_comparison.py` | Visualize metrics across question types |
| `edge_cases.py` | Identify lowest-scoring papers for analysis |
| `analyze_edge_cases.py` | Simplified wrapper for edge case analysis |

### Configuration Files

| File | Purpose |
|------|---------|
| `llm_questions.txt` | List of questions from questions.yml |
| `../metabeeai_llm/questions.yml` | Full question definitions with instructions |

### Legacy Scripts (Not Used in Current Pipeline)

| Script | Original Purpose |
|--------|------------------|
| `test_dataset_generation.py` | Legacy dataset generation |
| `reviewer_dataset_generation.py` | Legacy reviewer dataset generation |
| `run_benchmarking.py` | Legacy runner script |
| `deepeval_GEval.py` | Separate G-Eval script (now integrated) |
| `deepeval_llmv2.py` | Legacy LLM v2 evaluation |
| `deepeval_viz2.py` | Legacy visualization |
| `create_comparison_plots.py` | Legacy plotting |
| `analyze_deepeval_results_improved.py` | Legacy analysis |
| `merge_llm_v2.py` | Legacy merging |
| `deepeval_reviewers.py` | Legacy reviewer evaluation |

---

## Complete Workflow

### STEP 1: Prepare Reviewer Answers

You have two options depending on your reviewer data source:

#### Option A: From CSV Golden Answers

If you have reviewer answers in `data/golden_answers.csv`:

```bash
cd ../metabeeai_llm
python convert_goldens.py
```

**Input**: 
- `data/golden_answers.csv` (columns: Paper_id, Sample size, Species, etc.)

**Output**:
- `data/papers/{paper_id}/rev1_answers.json` (copy of answers.json with added `answer_rev1` fields)

**What it does**:
1. Reads CSV with human-curated answers
2. Reformats to match LLM output structure
3. Copies `answers.json` → `rev1_answers.json`
4. Adds `answer_rev1` field for each question

#### Option B: From GUI Answers

If reviewers used the BeeGUI interface:

The `answers_extended.json` files are already in `data/papers/{paper_id}/` - no conversion needed!

---

### STEP 2: Prepare Benchmark Dataset

Convert answers into evaluation format:

#### For CSV-Based Reviewer Answers:

```bash
python prep_benchmark_data.py
```

**Input**:
- `data/papers/{paper_id}/rev1_answers.json` (from Step 1A)
- `data/papers/{paper_id}/answers.json` (LLM answers)
- `data/papers/{paper_id}/pages/merged_v2.json` (full paper text chunks)
- `metabeeai_llm/questions.yml` (question definitions)

**Output**:
- `data/benchmark_data.json` (single JSON file with all test cases)

**Optional arguments**:
```bash
--papers-dir PATH       # Custom papers directory
--questions-yml PATH    # Custom questions file
--output PATH           # Custom output location
```

#### For GUI-Based Reviewer Answers:

```bash
python prep_benchmark_data_from_GUI_answers.py
```

**Input**:
- `data/papers/{paper_id}/answers_extended.json` (GUI reviewer answers)
- `data/papers/{paper_id}/answers.json` (LLM answers)
- `data/papers/{paper_id}/pages/merged_v2.json` (full paper text)

**Output**:
- `data/benchmark_data_gui.json`

---

### STEP 3: Run Evaluation

Execute DeepEval benchmarking with all metrics:

```bash
# Evaluate specific question type
python deepeval_benchmarking.py --question welfare

# Evaluate all questions
python deepeval_benchmarking.py

# With custom settings
python deepeval_benchmarking.py \
  --question welfare \
  --model gpt-4o \
  --batch-size 10 \
  --max-context-length 200000
```

**Command-line options**:
- `--question {design,population,welfare}` - Filter by question type (optional)
- `--input PATH` - Input benchmark file (default: `data/benchmark_data.json`)
- `--limit N` - Limit to first N test cases
- `--batch-size N` - Test cases per batch (default: 25)
- `--max-retries N` - Max retries per batch (default: 5)
- `--model {gpt-4o,gpt-4o-mini,gpt-4-turbo}` - Evaluation model (default: gpt-4o)
- `--max-context-length N` - Max context chars (default: 200,000)
- `--use-retrieval-only` - Use only retrieval context (saves tokens)

**Input**:
- `data/benchmark_data.json` (from Step 2)

**Output**:
- `deepeval_results/combined_results_{question}_{timestamp}.json`
- `deepeval_results/combined_results_{question}_{timestamp}.jsonl`

**Metrics Evaluated**:
1. **Faithfulness** - No contradictions with retrieval context
2. **Contextual Precision** - Relevant chunks ranked correctly
3. **Contextual Recall** - Expected output supported by retrieval
4. **Completeness [GEval]** - Covers all key points (threshold: 0.5)
5. **Accuracy [GEval]** - Accurate information alignment (threshold: 0.5)

**Cost Estimate**: ~$0.03 per test case with gpt-4o

---

### STEP 4: Visualize Results

Create comparison plots across question types:

```bash
python plot_metrics_comparison.py
```

**Input**:
- `deepeval_results/combined_results_*.json` (from Step 3)

**Output**:
- `deepeval_results/plots/metrics_comparison.png`
- Console output with statistics table

**What it shows**:
- 5 subplots (one per metric)
- 3 bars per subplot (one per question type)
- Error bars showing standard deviation
- Mean values labeled on each bar

---

### STEP 5: Identify Edge Cases (Optional)

Find lowest-scoring papers for detailed analysis:

```bash
# Get bottom 3 papers
python edge_cases.py --num-cases 3

# Get bottom 5 papers
python edge_cases.py --num-cases 5
```

**Command-line options**:
- `--num-cases N` - Number of edge cases per question (default: 20)
- `--results-dir PATH` - Results directory (default: `deepeval_results`)
- `--output-dir PATH` - Output directory (default: `edge_cases`)

**Input**:
- `deepeval_results/combined_results_*.json` (from Step 3)

**Output**:
- `edge_cases/combined/combined_{question}.json` - Bottom N papers per question
- `edge_cases/combined/summary-report.json` - LLM-generated insights
- `edge_cases/edge-case-report.md` - Human-readable report
- `edge_cases/edge_cases_summary.json` - Overall statistics

**What it identifies**:
- Papers with lowest combined scores across all metrics
- Common failure patterns (via LLM analysis)
- Specific metric weaknesses per question type

---

## Data Format

### Benchmark Data Format (`benchmark_data.json`)

```json
[
  {
    "paper_id": "4YD2Y4J8",
    "question_key": "welfare",
    "input": "What are the measures of welfare used...",
    "actual_output": "LLM answer",
    "expected_output": "Reviewer answer",
    "context": ["chunk1", "chunk2", ...],
    "retrieval_context": ["retrieved_chunk1", ...],
    "chunk_ids": ["id1", "id2", ...]
  }
]
```

### Evaluation Results Format

```json
[
  {
    "test_case_index": 0,
    "name": "paper_4YD2Y4J8_case_0",
    "paper_id": "4YD2Y4J8",
    "question_key": "welfare",
    "input": "Question text",
    "actual_output": "LLM answer",
    "expected_output": "Reviewer answer",
    "success": false,
    "additional_metadata": {
      "paper_id": "4YD2Y4J8",
      "question_key": "welfare",
      "chunk_ids": [...]
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
      },
      {
        "name": "Completeness [GEval]",
        "score": 0.65,
        "threshold": 0.5,
        "success": true,
        "reason": "Explanation...",
        "strict_mode": false,
        "evaluation_model": "gpt-4o",
        "error": null,
        "evaluation_cost": 0.003
      }
    ]
  }
]
```

**Note**: `context` and `retrieval_context` are NOT saved in results files to save space.

---

## Question Types

The pipeline evaluates three question types defined in `../metabeeai_llm/questions.yml`:

### 1. Design
**Question**: "What is the overview of the study, the number of groups being monitored and the sample size?"

**Expected format**: Numbered list with overview, groups, and sample size per study

### 2. Population
**Question**: "What species, sex, age range, mean age and SD, are studied? At what location and were they pair or group housed, and what was the social group composition?"

**Expected format**: List with species, sex, age, location, housing, composition

### 3. Welfare
**Question**: "What are the measures of welfare used in the study, and has the link between the measure and welfare, wellbeing, or chronic stress been made?"

**Expected format**: Numbered list with measure, link, description, units, collection method

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT DATA                                                  │
├─────────────────────────────────────────────────────────────┤
│ • data/golden_answers.csv (CSV reviewer answers)            │
│ • data/papers/{paper_id}/answers_extended.json (GUI answers)│
│ • data/papers/{paper_id}/answers.json (LLM answers)         │
│ • data/papers/{paper_id}/pages/merged_v2.json (paper text)  │
│ • metabeeai_llm/questions.yml (question definitions)        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: CONVERT REVIEWER ANSWERS                           │
├─────────────────────────────────────────────────────────────┤
│ Script: ../metabeeai_llm/convert_goldens.py                │
│ Output: data/papers/{paper_id}/rev1_answers.json            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: PREPARE BENCHMARK DATASET                          │
├─────────────────────────────────────────────────────────────┤
│ Script: prep_benchmark_data.py OR                           │
│         prep_benchmark_data_from_GUI_answers.py             │
│ Output: data/benchmark_data.json (30 entries)               │
│         - 10 papers × 3 questions                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: RUN DEEPEVAL BENCHMARKING                          │
├─────────────────────────────────────────────────────────────┤
│ Script: deepeval_benchmarking.py                            │
│ Output: deepeval_results/combined_results_{q}_{time}.json   │
│ Metrics: 5 total (3 standard + 2 G-Eval)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: VISUALIZE RESULTS                                   │
├─────────────────────────────────────────────────────────────┤
│ Script: plot_metrics_comparison.py                          │
│ Output: deepeval_results/plots/metrics_comparison.png       │
│ Shows: Mean ± SD for each metric across questions           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: IDENTIFY EDGE CASES (Optional)                      │
├─────────────────────────────────────────────────────────────┤
│ Script: edge_cases.py                                        │
│ Output: edge_cases/combined/combined_{question}.json         │
│         edge_cases/edge-case-report.md                       │
│ Shows: Bottom N papers with lowest scores                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start Guide

### Prerequisites

1. **Environment Setup**:
```bash
cd /Users/user/Documents/primate-welfare
source venv/bin/activate
```

2. **API Keys**: Create `.env` file in project root:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

3. **Required Data**: Ensure you have:
- LLM answers: `data/papers/{paper_id}/answers.json`
- Paper text: `data/papers/{paper_id}/pages/merged_v2.json`
- Reviewer answers: Either CSV or GUI format

---

### Complete Pipeline Example

```bash
# 1. Convert CSV reviewer answers (if using CSV)
cd metabeeai_llm
python convert_goldens.py
cd ../llm_benchmarking

# 2. Prepare benchmark dataset
python prep_benchmark_data.py
# Output: data/benchmark_data.json (30 entries for 10 papers)

# 3. Run evaluation for all questions
python deepeval_benchmarking.py --question design
python deepeval_benchmarking.py --question population
python deepeval_benchmarking.py --question welfare
# Output: deepeval_results/combined_results_{question}_{timestamp}.json

# 4. Create visualization
python plot_metrics_comparison.py
# Output: deepeval_results/plots/metrics_comparison.png

# 5. Identify bottom 3 papers
python edge_cases.py --num-cases 3
# Output: edge_cases/edge-case-report.md
```

---

## Detailed Script Documentation

### 1. `convert_goldens.py` (in metabeeai_llm/)

Converts CSV golden answers to JSON format matching LLM pipeline output.

**Usage**:
```bash
python convert_goldens.py [--csv PATH] [--dir PATH]
```

**Process**:
1. Reads `data/golden_answers.csv` (handles UTF-8 BOM)
2. Formats each CSV row into structured answers
3. Copies `answers.json` → `rev1_answers.json` for each paper
4. Adds `answer_rev1` field alongside LLM's `answer` field

**Output Structure**:
```json
{
  "QUESTIONS": {
    "welfare": {
      "answer": "LLM answer",
      "answer_rev1": "Reviewer answer from CSV",
      "reason": "LLM reasoning",
      "chunk_ids": [...]
    }
  }
}
```

---

### 2. `prep_benchmark_data.py`

Prepares benchmark dataset from papers with CSV reviewer answers.

**Usage**:
```bash
python prep_benchmark_data.py \
  --papers-dir data/papers \
  --questions-yml ../metabeeai_llm/questions.yml \
  --output data/benchmark_data.json
```

**Process**:
1. Loads questions from `questions.yml`
2. For each paper with `rev1_answers.json`:
   - Extracts LLM answer and chunk IDs
   - Extracts reviewer answer
   - Loads full paper text from `merged_v2.json`
   - Extracts retrieval context (chunks used by LLM)
3. Creates test case for each question

**Statistics Displayed**:
- Papers processed vs skipped
- Entries per question type
- Character counts for answers and retrieval

---

### 3. `prep_benchmark_data_from_GUI_answers.py`

Same as `prep_benchmark_data.py` but uses GUI reviewer answers.

**Usage**:
```bash
python prep_benchmark_data_from_GUI_answers.py
```

**Key Difference**:
- Reads from `answers_extended.json` instead of `rev1_answers.json`
- Extracts `user_answer_positive` field as reviewer answer
- Output: `data/benchmark_data_gui.json`

---

### 4. `deepeval_benchmarking.py`

Main evaluation script - runs all 5 metrics on benchmark data.

**Usage**:
```bash
# Basic usage
python deepeval_benchmarking.py --question welfare

# All questions at once
python deepeval_benchmarking.py

# With custom settings
python deepeval_benchmarking.py \
  --question welfare \
  --model gpt-4o \
  --batch-size 10 \
  --max-context-length 200000 \
  --use-retrieval-only
```

**Metrics Evaluated**:

1. **FaithfulnessMetric** (threshold: 0.5)
   - Checks for contradictions with retrieval context
   - High score = answer aligns with source text

2. **ContextualPrecisionMetric** (threshold: 0.5)
   - Evaluates if relevant chunks are ranked highly
   - High score = important info retrieved first

3. **ContextualRecallMetric** (threshold: 0.5)
   - Checks if expected output is supported by retrieval
   - High score = all key points have source support

4. **Completeness [GEval]** (threshold: 0.5)
   - Assesses coverage of key points
   - Uses GPT-4o to evaluate completeness

5. **Accuracy [GEval]** (threshold: 0.5)
   - Evaluates information accuracy
   - Uses GPT-4o to compare answers

**Processing**:
- Batched evaluation (default: 25 cases/batch)
- Automatic retries on failures (default: 5 retries)
- Incremental saving after each batch
- Handles up to 200K char contexts (~50K tokens)

**Output Format**:
```json
[
  {
    "test_case_index": 0,
    "name": "paper_4YD2Y4J8_case_0",
    "paper_id": "4YD2Y4J8",
    "question_key": "welfare",
    "input": "Question text",
    "actual_output": "LLM answer",
    "expected_output": "Reviewer answer",
    "success": true/false,
    "metrics_data": [
      {
        "name": "Faithfulness",
        "score": 0.85,
        "threshold": 0.5,
        "success": true,
        "reason": "Detailed explanation",
        "evaluation_model": "gpt-4o",
        "evaluation_cost": 0.002
      }
    ]
  }
]
```

**Important Notes**:
- Context fields are NOT saved in results (saves space)
- Results saved as both .json and .jsonl formats
- Timestamped filenames prevent overwrites
- Shows average scores at completion

---

### 5. `plot_metrics_comparison.py`

Creates visualization comparing metrics across question types.

**Usage**:
```bash
python plot_metrics_comparison.py \
  --results-dir deepeval_results \
  --output deepeval_results/plots/metrics_comparison.png
```

**Output**:
- Single figure with 5 subplots
- Bar charts with error bars
- Mean values labeled on bars
- 300 DPI publication-quality image

**Console Output**:
- Statistics table with mean ± std for each metric
- Sample sizes (N) for each question type

---

### 6. `edge_cases.py`

Identifies lowest-scoring papers for detailed review.

**Usage**:
```bash
# Bottom 3 papers
python edge_cases.py --num-cases 3

# Bottom 5 papers  
python edge_cases.py --num-cases 5

# All papers ranked
python edge_cases.py --num-cases 10
```

**How it works**:
1. Loads all evaluation results
2. Calculates combined score (average across all metrics)
3. Sorts papers by combined score (lowest first)
4. Takes bottom N papers per question type
5. Generates LLM summary of common failure patterns

**Output Files**:
- `edge_cases/combined/combined_{question}.json` - Raw edge case data
- `edge_cases/edge-case-report.md` - Markdown report
- `edge_cases/combined/summary-report.json` - LLM insights

---

## Cost Breakdown

### Typical Costs (10 papers, 3 questions, gpt-4o)

| Step | Description | Cost |
|------|-------------|------|
| **Step 1** | Convert goldens | $0.00 (no LLM) |
| **Step 2** | Prepare benchmark | $0.00 (no LLM) |
| **Step 3** | Evaluation (5 metrics × 30 entries) | ~$0.95 |
| **Step 4** | Plotting | $0.00 (no LLM) |
| **Step 5** | Edge cases (3 per question) | ~$0.05 |
| **TOTAL** | | **~$1.00** |

**Cost per entry**: ~$0.032 (for 5 metrics)

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
1. CSV properly formatted with Paper_id column
2. `rev1_answers.json` or `answers_extended.json` exists
3. Paper folder names match Paper_id in CSV

### Issue: Empty results files

**Check**:
1. OpenAI API key is valid
2. Sufficient API credits
3. Check error messages in console output

---

## Output Directory Structure

```
llm_benchmarking/
├── deepeval_results/           # Evaluation results
│   ├── combined_results_design_*.json
│   ├── combined_results_population_*.json
│   ├── combined_results_welfare_*.json
│   └── plots/
│       └── metrics_comparison.png
├── edge_cases/                 # Edge case analysis
│   ├── combined/
│   │   ├── combined_design.json
│   │   ├── combined_population.json
│   │   ├── combined_welfare.json
│   │   └── summary-report.json
│   ├── edge_cases_summary.json
│   └── edge-case-report.md
└── README.md                   # This file
```

---

## Tips and Best Practices

### 1. Running Evaluations Efficiently

- **Start with one question**: Test with `--question welfare --limit 5` first
- **Use appropriate batch size**: 10-25 for most papers, 5-10 for very long papers
- **Monitor costs**: Check evaluation_cost in results to track spending

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

## Example Workflow - 10 Papers

```bash
# Activate environment
source venv/bin/activate

# Step 1: Convert CSV answers to JSON (one-time)
cd metabeeai_llm
python convert_goldens.py
# Output: 10 papers with rev1_answers.json

# Step 2: Prepare benchmark data (one-time)
cd ../llm_benchmarking
python prep_benchmark_data.py
# Output: data/benchmark_data.json (30 test cases)

# Step 3: Run evaluations (can run in parallel)
python deepeval_benchmarking.py --question design &
python deepeval_benchmarking.py --question population &
python deepeval_benchmarking.py --question welfare &
wait
# Output: 3 result files in deepeval_results/
# Cost: ~$0.95 total

# Step 4: Create visualizations
python plot_metrics_comparison.py
# Output: deepeval_results/plots/metrics_comparison.png

# Step 5: Analyze bottom 3 papers
python edge_cases.py --num-cases 3
# Output: edge_cases/edge-case-report.md

# Review results
open deepeval_results/plots/metrics_comparison.png
open edge_cases/edge-case-report.md
```

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
python deepeval_benchmarking.py --question welfare --limit 3
```

### Analyzing Specific Papers

To analyze specific papers, you can filter the benchmark data before evaluation:

```python
# Create custom subset
import json

with open('data/benchmark_data.json', 'r') as f:
    data = json.load(f)

# Filter for specific papers
papers_of_interest = ['4YD2Y4J8', '76DQP2DC', 'CX9M8HCM']
filtered = [e for e in data if e['paper_id'] in papers_of_interest]

with open('data/benchmark_data_subset.json', 'w') as f:
    json.dump(filtered, f, indent=2)

# Then evaluate
python deepeval_benchmarking.py --input data/benchmark_data_subset.json
```

---

## File Size Considerations

**Benchmark Data** (`benchmark_data.json`):
- Size: ~2.7 MB for 30 entries
- Includes full context and retrieval context
- Used as input only (not modified)

**Evaluation Results**:
- Size: ~600-800 KB per question type
- Context fields removed to save space
- Keeps all metric scores and reasons

**Edge Cases**:
- Size: ~100-150 KB per question type
- Only bottom N papers included
- Full details preserved for analysis

---

## Performance Benchmarks

Based on 10 papers × 3 questions = 30 test cases:

| Metric | Design | Population | Welfare | Overall |
|--------|--------|------------|---------|---------|
| **Faithfulness** | 0.85 ± 0.15 | 1.00 ± 0.00 | 0.96 ± 0.10 | 0.94 |
| **Contextual Precision** | 0.90 ± 0.24 | 0.98 ± 0.05 | 0.79 ± 0.34 | 0.89 |
| **Contextual Recall** | 0.70 ± 0.22 | 0.69 ± 0.21 | 0.71 ± 0.29 | 0.70 |
| **Completeness** | 0.48 ± 0.21 | 0.54 ± 0.21 | 0.51 ± 0.19 | 0.51 |
| **Accuracy** | 0.42 ± 0.22 | 0.48 ± 0.20 | 0.45 ± 0.20 | 0.45 |

**Key Findings**:
- Standard metrics perform well (0.7-1.0 range)
- G-Eval metrics show moderate performance (0.4-0.5 range)
- Population questions perform best overall
- Contextual Recall consistent across all questions

---

## Future Improvements

### Potential Enhancements

1. **Add More Metrics**:
   - BLEU/ROUGE scores for text similarity
   - BERTScore for semantic similarity
   - Custom domain-specific metrics

2. **Automated Report Generation**:
   - PDF reports with plots and tables
   - Executive summary with key findings
   - Comparison with previous runs

3. **Interactive Dashboard**:
   - Web interface for results exploration
   - Drill-down into specific papers
   - Real-time evaluation monitoring

4. **Batch Processing Optimization**:
   - Adaptive batch sizing based on context length
   - Parallel processing for multiple questions
   - Resume from checkpoint on interruption

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
5. Consult DeepEval documentation for metric-specific issues

---

**Last Updated**: October 8, 2025  
**Pipeline Version**: 2.0 (Primate Welfare)
