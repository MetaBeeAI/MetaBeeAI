# MetaBeeAI Literature Review Pipeline

A comprehensive pipeline for extracting, analyzing, and benchmarking structured information from scientific literature using Large Language Models and Vision AI.

---

## 🔑 Required API Accounts

Before starting, you need to set up the following API accounts:

| Service | Purpose | Sign Up | Cost |
|---------|---------|---------|------|
| **OpenAI** | LLM processing and evaluation | [platform.openai.com](https://platform.openai.com) | Pay-per-use (~$1-5 per 10 papers) |
| **LandingLens API** | PDF text extraction with vision AI | [landing.ai](https://landing.ai) | Contact for pricing |

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

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate  # Mac/Linux
# Or: venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt
```

### 2. Prepare Your PDFs

Organize papers in `data/papers/`:

```
data/papers/
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

## 📋 Pipeline Overview

The pipeline consists of 5 main stages:

```
PDFs → Vision AI Processing → LLM Analysis → Human Review → Benchmarking → Analysis
```

### Stage 1: PDF Processing → Structured JSON
**Folder**: `process_pdfs/`  
**Input**: PDF files  
**Output**: JSON chunks with text and coordinates  
**Details**: See `process_pdfs/README.md`

### Stage 2: LLM Question Answering → Extracted Information  
**Folder**: `metabeeai_llm/`  
**Input**: JSON chunks  
**Output**: Structured answers with citations  
**Details**: See `metabeeai_llm/README.md`

### Stage 3: Human Review & Annotation → Validated Answers
**Folder**: `llm_review_software/`  
**Input**: LLM answers  
**Output**: Human-validated answers  
**Details**: GUI-based review interface

### Stage 4: Benchmarking → Performance Metrics
**Folder**: `llm_benchmarking/`  
**Input**: LLM + reviewer answers  
**Output**: Evaluation metrics and comparisons  
**Details**: See `llm_benchmarking/README.md`

### Stage 5: Data Analysis → Insights
**Folder**: `query_database/`  
**Input**: Structured answers across papers  
**Output**: Trend analysis, network plots, summaries  
**Details**: Query and aggregate data

---

## 🔄 Complete Workflow

### Step 1: Process PDFs to JSON

```bash
cd process_pdfs
python process_all.py
```

**What it does**: Converts PDFs → structured JSON chunks  
**Output**: `data/papers/{paper_id}/pages/merged_v2.json`  
**For details**: `process_pdfs/README.md`

---

### Step 2: Extract Information with LLM

```bash
cd metabeeai_llm

# Process all papers
python llm_pipeline.py

# Or process specific papers
python llm_pipeline.py --folders 4YD2Y4J8 76DQP2DC
```

**What it does**: LLM answers questions from `questions.yml`  
**Output**: `data/papers/{paper_id}/answers.json`  
**Questions**: Defined in `metabeeai_llm/questions.yml`  
**For details**: `metabeeai_llm/README.md`

---

### Step 3: Human Review (Optional)

```bash
cd llm_review_software
python beegui.py
```

**What it does**: GUI interface for reviewing and annotating LLM answers  
**Output**: `data/papers/{paper_id}/answers_extended.json`  
**Features**: View PDFs, edit answers, rate quality

---

### Step 4: Benchmarking & Evaluation

#### 4a. Prepare Reviewer Data

If you have **CSV golden answers**:
```bash
cd metabeeai_llm
python convert_goldens.py
```
**Output**: `data/papers/{paper_id}/rev1_answers.json`

If you used the **GUI review tool**, the data is already ready in `answers_extended.json`.

#### 4b. Create Benchmark Dataset

For CSV reviewer answers:
```bash
cd llm_benchmarking
python prep_benchmark_data.py
```

For GUI reviewer answers:
```bash
python prep_benchmark_data_from_GUI_answers.py
```

**Output**: `data/benchmark_data.json` or `data/benchmark_data_gui.json`

#### 4c. Run Evaluation

```bash
# Evaluate all questions
python deepeval_benchmarking.py --question design
python deepeval_benchmarking.py --question population
python deepeval_benchmarking.py --question welfare

# Or evaluate all at once
python deepeval_benchmarking.py
```

**Output**: `deepeval_results/combined_results_{question}_{timestamp}.json`  
**Cost**: ~$0.95 for 10 papers × 3 questions  
**For details**: `llm_benchmarking/README.md`

#### 4d. Visualize Results

```bash
python plot_metrics_comparison.py
```

**Output**: `deepeval_results/plots/metrics_comparison.png`

#### 4e. Identify Problem Papers (Optional)

```bash
# Get bottom 3 papers
python edge_cases.py --num-cases 3
```

**Output**: `edge_cases/edge-case-report.md`

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

## 📁 Project Structure

```
primate-welfare/
├── .env                        # API keys (create from env.example)
├── config.py                   # Centralized configuration
├── requirements.txt            # Python dependencies
│
├── data/                       # Data directory
│   ├── papers/                 # Paper-specific data
│   │   └── {paper_id}/
│   │       ├── {paper_id}_main.pdf          # Original PDF
│   │       ├── pages/
│   │       │   ├── main_p01.pdf.json        # Page JSONs
│   │       │   └── merged_v2.json           # Merged & deduplicated
│   │       ├── answers.json                 # LLM answers
│   │       ├── rev1_answers.json            # With CSV reviewer answers
│   │       └── answers_extended.json        # GUI reviewer answers
│   ├── golden_answers.csv      # CSV reviewer answers (input)
│   ├── benchmark_data.json     # Benchmark dataset
│   └── benchmark_data_gui.json # Benchmark dataset (GUI)
│
├── process_pdfs/               # Stage 1: PDF Processing
│   ├── README.md              # Detailed documentation
│   ├── process_all.py         # Main processing script
│   ├── split_pdf.py           # PDF splitting
│   ├── va_process_papers.py   # Vision AI extraction
│   ├── merger.py              # JSON merging
│   └── deduplicate_chunks.py  # Deduplication
│
├── metabeeai_llm/             # Stage 2: LLM Q&A
│   ├── README.md              # Detailed documentation
│   ├── llm_pipeline.py        # Main LLM pipeline
│   ├── questions.yml          # Question definitions
│   ├── convert_goldens.py     # CSV → JSON converter
│   └── json_multistage_qa.py  # Core LLM functions
│
├── llm_review_software/       # Stage 3: Human Review
│   ├── beegui.py              # GUI review interface
│   └── annotator.py           # Annotation logic
│
├── llm_benchmarking/          # Stage 4: Evaluation
│   ├── README.md              # Detailed documentation
│   ├── prep_benchmark_data.py # Prepare from CSV
│   ├── prep_benchmark_data_from_GUI_answers.py # Prepare from GUI
│   ├── deepeval_benchmarking.py # Run evaluation
│   ├── plot_metrics_comparison.py # Visualize results
│   ├── edge_cases.py          # Find problem papers
│   └── deepeval_results/      # Evaluation outputs
│       ├── combined_results_*.json
│       └── plots/
│
└── query_database/            # Stage 5: Data Analysis
    ├── README.md              # Analysis documentation
    ├── trend_analysis.py      # Temporal trends
    ├── network_analysis.py    # Relationship networks
    └── output/                # Analysis outputs
```

---

## 🎯 Common Use Cases

### Use Case 1: Process New Papers

```bash
# 1. Add PDFs to data/papers/{paper_id}/
# 2. Process PDFs
cd process_pdfs
python process_all.py

# 3. Extract information
cd ../metabeeai_llm
python llm_pipeline.py
```

**Result**: Structured answers in `answers.json` for each paper

---

### Use Case 2: Review LLM Answers

```bash
cd llm_review_software
python beegui.py
```

**Features**:
- View PDF alongside LLM answers
- Edit and validate answers
- Rate answer quality
- Navigate between papers

---

### Use Case 3: Benchmark LLM Performance

```bash
# 1. Prepare reviewer answers (if from CSV)
cd metabeeai_llm
python convert_goldens.py

# 2. Create benchmark dataset
cd ../llm_benchmarking
python prep_benchmark_data.py

# 3. Run evaluation
python deepeval_benchmarking.py --question welfare

# 4. Visualize
python plot_metrics_comparison.py

# 5. Find problem papers
python edge_cases.py --num-cases 3
```

**Result**: 
- Performance metrics across 5 dimensions
- Comparison plots
- Edge case analysis

---

### Use Case 4: Analyze Extracted Data

```bash
cd query_database

# Analyze welfare measure trends
python trend_analysis.py

# Analyze relationships between variables
python network_analysis.py
```

**Result**: Plots and reports in `query_database/output/`

---

## 📊 Question Types

The pipeline currently handles three question types for primate welfare:

### 1. Design
**Question**: What is the overview of the study, the number of groups being monitored and the sample size?

**Example Answer**: 
```
1. Overview: Compares wounding rates between groups, looking at impacts 
of age, group composition, and presence of young silverbacks; 
Groups: 45; n = 180
```

### 2. Population
**Question**: What species, sex, age range, mean age and SD, are studied? At what location and were they pair or group housed, and what was the social group composition?

**Example Answer**:
```
Species 1: western lowland Gorilla; sex: M and F; age range: 1-55 years; 
mean age: NA; location: USA (across 28 AZA accredited zoos); 
social group: Group; composition: Mixed-sex groups (n = 26; 41 males, 
91 females) and bachelor groups (n = 19; 48 males)
```

### 3. Welfare
**Question**: What are the measures of welfare used in the study, and has the link between the measure and welfare, wellbeing, or chronic stress been made?

**Example Answer**:
```
1. Measure: Wounding rates; Link made: Y; Welfare measure description: 
Rates of wounding over period of many years; Units: Wounds per gorilla 
per month; Collection method: Animal care staff recorded all wounds that 
occurred within groups using a standardized data sheet
```

Questions are fully defined in `metabeeai_llm/questions.yml` with instructions, examples, and configuration.

---

## 🔧 Configuration

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

## 📈 Benchmarking Metrics

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

## 💰 Cost Estimates

Based on typical usage with GPT-4o:

| Task | Papers | Questions | Cost |
|------|--------|-----------|------|
| **LLM Extraction** | 10 | 3 per paper | ~$2-3 |
| **Benchmarking** | 10 | 3 questions | ~$0.95 |
| **Edge Case Analysis** | 3 bottom papers | All questions | ~$0.05 |
| **TOTAL** | 10 papers | Full pipeline | **~$3-4** |

**Cost Reduction Options**:
- Use `gpt-4o-mini` instead of `gpt-4o` (3-5x cheaper)
- Use `--use-retrieval-only` flag (reduces context)
- Process fewer papers initially for testing

---

## 📚 Detailed Documentation

Each component has detailed documentation:

| Component | Documentation |
|-----------|---------------|
| **PDF Processing** | `process_pdfs/README.md` |
| **LLM Pipeline** | `metabeeai_llm/README.md` |
| **Benchmarking** | `llm_benchmarking/README.md` |
| **Data Analysis** | `query_database/README.md` |

---

## 🎓 Tutorial: Process Your First 3 Papers

### Complete Example

```bash
# 1. Set up environment
source venv/bin/activate
cp env.example .env
# Edit .env with your API keys

# 2. Add 3 PDFs to data/papers/
mkdir -p data/papers/PAPER001
cp your_paper.pdf data/papers/PAPER001/PAPER001_main.pdf
# Repeat for PAPER002, PAPER003

# 3. Process PDFs
cd process_pdfs
python process_all.py
# Output: merged_v2.json for each paper

# 4. Run LLM extraction
cd ../metabeeai_llm
python llm_pipeline.py
# Output: answers.json for each paper

# 5. Review answers (optional)
cd ../llm_review_software
python beegui.py
# Manually review and validate

# 6. If you have reviewer answers in CSV:
cd ../metabeeai_llm
python convert_goldens.py

# 7. Create benchmark dataset
cd ../llm_benchmarking
python prep_benchmark_data.py
# Output: data/benchmark_data.json

# 8. Run evaluation
python deepeval_benchmarking.py --question welfare
# Output: deepeval_results/combined_results_welfare_*.json

# 9. Visualize results
python plot_metrics_comparison.py
# Output: deepeval_results/plots/metrics_comparison.png

# 10. Find problem papers
python edge_cases.py --num-cases 2
# Output: edge_cases/edge-case-report.md
```

**Expected time**: 
- PDF processing: ~5-10 min per paper
- LLM extraction: ~2-3 min per paper
- Evaluation: ~1-2 min per question

---

## 🔍 Understanding the Output

### LLM Answers (`answers.json`)

```json
{
  "QUESTIONS": {
    "welfare": {
      "answer": "1. Measure: Wounding rates; Link made: Y; ...",
      "reason": "The study provides detailed information...",
      "chunk_ids": ["uuid1", "uuid2"]
    }
  }
}
```

- **answer**: LLM's structured response
- **reason**: Why this answer was generated
- **chunk_ids**: Source text chunks used

### Benchmark Results

```json
{
  "paper_id": "4YD2Y4J8",
  "question_key": "welfare",
  "actual_output": "LLM answer",
  "expected_output": "Reviewer answer",
  "success": true/false,
  "metrics_data": [
    {
      "name": "Faithfulness",
      "score": 0.85,
      "success": true,
      "reason": "Explanation..."
    }
  ]
}
```

- **success**: True if all metrics passed thresholds
- **metrics_data**: Detailed results for each metric
- Score interpretation: See `llm_benchmarking/README.md`

---

## 🛠️ Troubleshooting

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
# Solution: Increase limit or use retrieval only
python deepeval_benchmarking.py --max-context-length 300000
# Or
python deepeval_benchmarking.py --use-retrieval-only
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

## 🔬 Current Dataset

**Primate Welfare Literature Review**

- **Total Papers**: 41 papers in `data/papers/`
- **With Golden Answers**: 10 papers in `data/golden_answers.csv`
- **With GUI Answers**: 1 paper with `answers_extended.json`
- **Questions**: 3 per paper (design, population, welfare)
- **Species Covered**: Gorillas, macaques, chimpanzees, bonobos, orangutans, lemurs, marmosets, slow lorises

**Sample Papers**:
- 4YD2Y4J8: Western lowland gorilla wounding rates
- 76DQP2DC: Rhesus macaque welfare and personality
- WIZ9MV3T: Chimpanzee locomotion as wellbeing indicator
- V7984AAU: Body condition score in slow lorises
- 8BV8BLU8: Orangutan subjective wellbeing

---

## 📝 Key Scripts Reference

### PDF Processing
- `process_pdfs/process_all.py` - Main processor

### LLM Extraction  
- `metabeeai_llm/llm_pipeline.py` - Extract information from papers
- `metabeeai_llm/convert_goldens.py` - Convert CSV → JSON reviewer answers

### Benchmarking
- `llm_benchmarking/prep_benchmark_data.py` - Prepare benchmark dataset
- `llm_benchmarking/deepeval_benchmarking.py` - Run evaluation (5 metrics)
- `llm_benchmarking/plot_metrics_comparison.py` - Visualize results
- `llm_benchmarking/edge_cases.py` - Find lowest-scoring papers

### Review Interface
- `llm_review_software/beegui.py` - GUI for reviewing answers

---

## 🎯 Best Practices

### 1. Start Small
- Test with 3-5 papers first
- Use `--limit` flags to test scripts
- Verify outputs before scaling up

### 2. Version Control
- Results are timestamped (no overwrites)
- Keep original `answers.json` files unchanged
- Reviewer answers go in separate files

### 3. Cost Management
- Use `gpt-4o-mini` for initial testing
- Test with `--limit 1` before full runs
- Monitor costs via `evaluation_cost` fields

### 4. Quality Assurance
- Review edge cases to identify patterns
- Check low-scoring papers manually
- Validate LLM answers with GUI tool

---

## 📖 Additional Resources

### Documentation
- **LLM Benchmarking**: `llm_benchmarking/README.md` (comprehensive guide)
- **PDF Processing**: `process_pdfs/README.md`
- **LLM Pipeline**: `metabeeai_llm/README.md`

### External Links
- **DeepEval Docs**: https://docs.confident-ai.com/
- **OpenAI API**: https://platform.openai.com/docs
- **Landing AI**: https://landing.ai/

---

## 🤝 Contributing

When adding new question types:

1. **Define in `questions.yml`**:
   ```yaml
   new_question:
     question: "Your question here?"
     instructions: [...]
     output_format: "..."
     example_output: [...]
     max_chunks: 6
     min_score: 0.4
   ```

2. **Update CSV template** (if using CSV reviewers):
   - Add column for new question
   - Update `convert_goldens.py` to handle it

3. **Update question lists**:
   - `llm_benchmarking/llm_questions.txt`
   - `llm_benchmarking/edge_cases.py` (question_types list)

4. **Re-run pipeline** from Step 2

---

## 📞 Support

For issues:
1. Check relevant README in component folder
2. Review error messages carefully
3. Verify all input files exist
4. Check API keys and credits
5. Consult script-specific documentation

---

**Project**: Primate Welfare Literature Review  
**Version**: 2.0  
**Last Updated**: October 8, 2025  
**Contact**: See project documentation
