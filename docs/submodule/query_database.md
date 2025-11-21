# Query Database - Data Extraction and Analysis

This submodule provides tools for querying and analyzing structured data extracted from scientific papers processed through the MetaBeeAI pipeline.

## Overview

The MetaBeeAI pipeline generates structured JSON data from scientific papers, stored in a queriable format. This submodule provides scripts to:

1. **Query the database** - Extract structured information from `answers.json` files
2. **Perform analyses** - Generate statistical summaries, trends, and network visualizations
3. **Create visualizations** - Produce plots and network diagrams showing relationships

## Installation

This submodule is part of the `metabeeai` package. Install it via:

```bash
pip install metabeeai
```

Or if installing from source:

```bash
pip install -e /path/to/MetaBeeAI
```

**Required dependencies**: pandas, numpy, matplotlib, seaborn, networkx, python-dotenv

---

## Understanding the Database Structure

### Data Storage Format

The MetaBeeAI pipeline stores extracted information from papers in a structured JSON format. Each processed paper contains an `answers.json` file with question-answer pairs:

**Location**: `{METABEEAI_DATA_DIR}/papers/{paper_id}/answers.json`

**Structure**:
```json
{
  "QUESTIONS": {
    "bee_species": {
      "answer": "Apis mellifera, Bombus terrestris",
      "reason": "Species mentioned in methodology section",
      "chunk_ids": ["chunk_001", "chunk_003"]
    },
    "pesticides": {
      "answer": "Imidacloprid at 10 ppb, oral exposure, 7 days",
      "reason": "Pesticide details found in methods",
      "chunk_ids": ["chunk_005", "chunk_007"]
    },
    "additional_stressors": {
      "answer": "Nosema ceranae infection, 10^5 spores per bee",
      "reason": "Additional stressor mentioned in study design",
      "chunk_ids": ["chunk_012"]
    },
    "significance": {
      "answer": "1. Imidacloprid impaired learning. 2. Combined with Nosema increased mortality.",
      "reason": "Key findings extracted from results section",
      "chunk_ids": ["chunk_020", "chunk_021"]
    }
  }
}
```

### Database Configuration

The database location is configured via the `METABEEAI_DATA_DIR` environment variable:

**Set in `.env` file** (project root):
```bash
METABEEAI_DATA_DIR=/path/to/your/data/directory
```

**Directory structure**:
```
{METABEEAI_DATA_DIR}/
└── papers/
    ├── 001/
    │   ├── answers.json          # LLM-generated answers
    │   ├── answers_extended.json # Reviewer answers (optional)
    │   └── pages/
    │       └── merged_v2.json   # Processed PDF chunks
    ├── 002/
    │   └── answers.json
    ├── 95UKMIEY/
    │   └── answers.json
    └── ...
```

### Querying the Database

All scripts in this submodule automatically query the database by:

1. **Reading `METABEEAI_DATA_DIR`** from your `.env` file
2. **Scanning `{METABEEAI_DATA_DIR}/papers/`** for all paper folders
3. **Loading `answers.json`** files from each paper folder
4. **Extracting structured data** based on question types
5. **Saving results** to `query_database/output/`

**No manual database queries needed** - The scripts handle all data access automatically.

---

## Data Extraction Scripts

These scripts query the database and extract structured information from specific question types:

### 1. `investigate_bee_species.py` - Extract Bee Species Data

**Purpose**: Queries the database for bee species information across all papers.

**What it queries**: Extracts data from the `bee_species` question in each `answers.json` file.

**Usage**:
```bash
python -m metabeeai.query_database.investigate_bee_species
```

**Output**:
- `output/bee_species_data.json` - Structured bee species data

**Data structure**:
```json
[
  {
    "paper_id": "729",
    "species_name": "Apis mellifera carnica",
    "genus": "Apis",
    "species": "mellifera",
    "subspecies": "carnica",
    "common_name": "Carniolan honey bee"
  }
]
```

**What it does**:
1. Scans all paper directories for `answers.json` files
2. Extracts bee species information from the `bee_species` question
3. Parses species names into taxonomic components (genus, species, subspecies)
4. Identifies common names where available
5. Handles multiple species per paper
6. Validates and standardizes species names

---

### 2. `investigate_pesticides.py` - Extract Pesticide Data

**Purpose**: Queries the database for pesticide exposure information.

**What it queries**: Extracts data from the `pesticides` question in each `answers.json` file.

**Usage**:
```bash
python -m metabeeai.query_database.investigate_pesticides
```

**Output**:
- `output/pesticides_data.json` - Structured pesticide data

**Data structure**:
```json
[
  {
    "paper_id": "729",
    "pesticide_name": "imidacloprid",
    "dose": "10 ppb",
    "exposure_method": "oral",
    "duration": "7 days"
  }
]
```

**What it does**:
1. Extracts pesticide information from the `pesticides` question
2. Parses chemical names, doses, exposure methods, and durations
3. Handles multiple pesticides per paper
4. Standardizes pesticide names (converts to lowercase)
5. Extracts quantitative dose information when available
6. Categorizes exposure methods (oral, contact, topical, field, etc.)

---

### 3. `investigate_additional_stressors.py` - Extract Stressor Data

**Purpose**: Queries the database for non-pesticide stressors tested in studies.

**What it queries**: Extracts data from the `additional_stressors` question in each `answers.json` file.

**Usage**:
```bash
python -m metabeeai.query_database.investigate_additional_stressors
```

**Output**:
- `output/additional_stressors_data.json` - Structured stressor data

**Data structure**:
```json
[
  {
    "paper_id": "729",
    "stressor_type": "Pathogen",
    "stressor_name": "Nosema ceranae",
    "details": "10^5 spores per bee, oral inoculation, 7 days"
  }
]
```

**What it does**:
1. Extracts additional stressor information from the `additional_stressors` question
2. Categorizes stressors by type (Temperature, Pathogen, Parasite, Nutritional, Chemical, Environmental)
3. Extracts stressor names and application details
4. Handles multiple stressors per paper
5. Excludes pesticides (captured separately by `investigate_pesticides.py`)

---

### 4. `investigate_significance.py` - Extract Findings Data

**Purpose**: Queries the database for key findings and significance statements.

**What it queries**: Extracts data from the `significance` question in each `answers.json` file.

**Usage**:
```bash
python -m metabeeai.query_database.investigate_significance
```

**Output**:
- `output/significance_data.json` - Structured findings data

**Data structure**:
```json
[
  {
    "paper_id": "729",
    "finding": "Imidacloprid at 10 ppb impaired learning and memory",
    "category": "Cognitive Effects"
  }
]
```

**What it does**:
1. Extracts key findings from the `significance` question
2. Parses individual findings from multi-point answers
3. Categorizes findings by impact type
4. Preserves both original and processed versions of data
5. Handles quantitative results and effect descriptions

---

## Analysis Scripts

These scripts analyze the extracted data and generate visualizations:

### 5. `trend_analysis.py` - Trend and Co-occurrence Analysis

**Purpose**: Analyzes trends and co-occurrence patterns between bee species and pesticides.

**What it analyzes**: Uses extracted data from `bee_species_data.json` and `pesticides_data.json`.

**Usage**:
```bash
python -m metabeeai.query_database.trend_analysis
```

**Input**:
- `output/bee_species_data.json` - From `investigate_bee_species.py`
- `output/pesticides_data.json` - From `investigate_pesticides.py`

**Output**:
- `output/trend_analysis_plots/top_bee_pesticide_combinations.png` - Most common bee-pesticide pairs
- `output/trend_analysis_plots/most_studied_bee_species.png` - Most frequently studied species
- `output/trend_analysis_plots/most_tested_nicotinic_pesticides.png` - Most tested neonicotinoids
- `output/trend_analysis_report.txt` - Statistical summary report

**What it does**:
1. **Filters data**:
   - Focuses on nicotinic cholinergic pesticides (neonicotinoids, sulfoximines, butenolides, spinosyns)
   - Standardizes bee species names (uses genus + species when available)
   - Excludes papers without proper species identification

2. **Calculates statistics**:
   - Counts studies per bee species
   - Counts studies per pesticide
   - Identifies bee-pesticide co-occurrences
   - Ranks top combinations

3. **Generates visualizations**:
   - Bar charts of most studied species and pesticides
   - Co-occurrence frequency plots
   - Top combinations rankings

4. **Creates summary report**:
   - Total papers analyzed
   - Unique species and pesticides
   - Study distribution metrics
   - Top 20 bee-pesticide combinations

**Nicotinic pesticides included**:
- **Neonicotinoids**: imidacloprid, thiamethoxam, clothianidin, acetamiprid, thiacloprid, dinotefuran, nitenpyram
- **Sulfoximines**: sulfoxaflor
- **Butenolides**: flupyradifurone
- **Spinosyns**: spinosad, spinetoram

---

### 6. `network_analysis.py` - Network Visualization

**Purpose**: Creates network visualizations showing relationships between bees, pesticides, and stressors.

**What it analyzes**: Uses extracted data from all three extraction scripts.

**Usage**:
```bash
python -m metabeeai.query_database.network_analysis
```

**Input**:
- `output/bee_species_data.json` - From `investigate_bee_species.py`
- `output/pesticides_data.json` - From `investigate_pesticides.py`
- `output/additional_stressors_data.json` - From `investigate_additional_stressors.py`

**Output**:
- `output/network_plots/tripartite_network.png` - 3-way network: bees, pesticides, stressors
- `output/network_statistics.txt` - Network connectivity statistics
- `output/pesticide_stressor_summary.txt` - Co-occurrence analysis

**What it does**:
1. **Creates tripartite network**:
   - Three node types: bee species (green), pesticides (red), stressors (blue)
   - Edge thickness proportional to number of studies
   - Shows complex relationships between all three factors
   - Uses force-directed layout for clarity

2. **Calculates network statistics**:
   - Node counts (species, pesticides, stressors)
   - Edge counts (relationships)
   - Degree centrality (most connected nodes)
   - Network density metrics
   - Papers with single vs. multiple factors

3. **Analyzes pesticide-stressor interactions**:
   - Papers testing pesticides only
   - Papers testing stressors only
   - Papers testing both (interaction studies)
   - Top pesticide-stressor combinations
   - Identifies nicotinic vs. other pesticides

**Network interpretation**:
- **Node size**: Number of connections
- **Edge thickness**: Number of studies with that combination
- **Color coding**: Green (bees), Red (pesticides), Blue (stressors)

---

## Complete Workflow

### Step 1: Configure Database Location

Ensure your `.env` file contains:
```bash
METABEEAI_DATA_DIR=/path/to/your/data/directory
```

### Step 2: Extract Data (Query Database)

Run all extraction scripts to query the database and extract structured data:

```bash
# Extract bee species data
python -m metabeeai.query_database.investigate_bee_species

# Extract pesticide data
python -m metabeeai.query_database.investigate_pesticides

# Extract additional stressors data
python -m metabeeai.query_database.investigate_additional_stressors

# Extract significance/findings data
python -m metabeeai.query_database.investigate_significance
```

### Step 3: Run Analyses

Analyze the extracted data and create visualizations:

```bash
# Analyze trends and co-occurrences
python -m metabeeai.query_database.trend_analysis

# Create network visualizations
python -m metabeeai.query_database.network_analysis
```

### Step 4: Review Outputs

Check the generated files:
```bash
ls -lh output/
ls -lh output/trend_analysis_plots/
ls -lh output/network_plots/
```

---

## Output File Structure

```
query_database/output/
├── bee_species_data.json                          # Bee species extraction results
├── pesticides_data.json                           # Pesticide extraction results
├── additional_stressors_data.json                 # Stressor extraction results
├── significance_data.json                         # Findings extraction results
├── trend_analysis_plots/
│   ├── top_bee_pesticide_combinations.png         # Most common pairs
│   ├── most_studied_bee_species.png               # Species frequency
│   └── most_tested_nicotinic_pesticides.png       # Pesticide frequency
├── trend_analysis_report.txt                      # Statistical summary
├── network_plots/
│   └── tripartite_network.png                     # 3-way network visualization
├── network_statistics.txt                         # Network metrics
└── pesticide_stressor_summary.txt                 # Interaction analysis
```

---

## Understanding the Outputs

### Trend Analysis Report

The `trend_analysis_report.txt` provides:
- **Dataset overview**: Total papers, unique species, unique pesticides
- **Top bee species**: Most frequently studied species (e.g., *Apis mellifera*)
- **Top pesticides**: Most tested nicotinic pesticides (e.g., imidacloprid)
- **Top combinations**: Most common bee-pesticide pairs tested together
- **Study distribution**: How studies are distributed across species and pesticides

### Network Statistics

The `network_statistics.txt` provides:
- **Network size**: Number of nodes and edges
- **Connectivity**: Most connected species, pesticides, stressors
- **Degree centrality**: Which factors appear in most studies
- **Network density**: How interconnected the research landscape is

### Pesticide-Stressor Summary

The `pesticide_stressor_summary.txt` provides:
- **Interaction patterns**: Papers testing pesticides alone, stressors alone, or both
- **Co-occurrence**: Most common pesticide-stressor combinations
- **Pesticide classification**: Which pesticides are nicotinic cholinergic
- **Research gaps**: Understudied combinations

---

## Prerequisites

1. **Data Requirements**:
   - Must have run the LLM pipeline first (`metabeeai llm`)
   - Each paper must have an `answers.json` file
   - Database location configured via `METABEEAI_DATA_DIR` in `.env`

2. **Expected data structure**:
```
{METABEEAI_DATA_DIR}/
└── papers/
    ├── 001/
    │   └── answers.json
    ├── 002/
    │   └── answers.json
    ├── 95UKMIEY/
    │   └── answers.json
    └── ...
```

3. **Environment Configuration**:
   - Create `.env` file in project root (if not exists)
   - Add: `METABEEAI_DATA_DIR=/path/to/your/data/directory`

---

## Data Quality Notes

### Bee Species Standardization

The scripts automatically standardize bee species names:
- **Priority 1**: Use genus + species when both available
- **Priority 2**: Use `species_name` field if genus/species missing
- **Filtered out**: "Species not specified" entries
- **Example**: "Apis mellifera carnica" → genus: "Apis", species: "mellifera", subspecies: "carnica"

### Pesticide Name Cleaning

Pesticide names are automatically cleaned:
- Converted to lowercase for consistency
- Chemical names preferred over trade names
- Standardized spelling (e.g., "imidacloprid" not "Imidacloprid")

### Stressor Categorization

Stressors are automatically categorized into types:
- **Pathogen**: Bacteria, viruses, fungi
- **Parasite**: Varroa, Nosema, tracheal mites
- **Temperature**: Heat stress, cold stress
- **Nutritional**: Diet restriction, pollen quality
- **Chemical**: Non-pesticide chemicals
- **Environmental**: Other environmental factors

---

## Advanced Usage

### Custom Database Queries

You can write custom scripts to query the database:

```python
import json
import os
from pathlib import Path

# Get papers directory from config
from metabeeai.config import get_papers_dir

papers_dir = get_papers_dir()

# Query all answers.json files
for paper_folder in os.listdir(papers_dir):
    answers_path = Path(papers_dir) / paper_folder / "answers.json"

    if answers_path.exists():
        with open(answers_path, 'r') as f:
            answers = json.load(f)

        # Extract specific question
        bee_species = answers.get("QUESTIONS", {}).get("bee_species", {})
        print(f"Paper {paper_folder}: {bee_species.get('answer', 'N/A')}")
```

### Filtering by Date Range

If your data includes date information, you can filter papers:

```python
# Example: Add to any investigate_*.py script
import datetime

# Filter papers from 2020 onwards
if paper_metadata.get('year') and int(paper_metadata['year']) >= 2020:
    # Process this paper
    pass
```

### Custom Analysis

You can load the extracted JSON files for custom analyses:

```python
import json
import pandas as pd

# Load extracted data
with open('output/bee_species_data.json', 'r') as f:
    bee_data = json.load(f)

bee_df = pd.DataFrame(bee_data)

# Custom analysis
genus_counts = bee_df['genus'].value_counts()
print(f"Most studied genus: {genus_counts.index[0]}")
```

---

## Troubleshooting

### "METABEEAI_DATA_DIR not set"
- **Fix**: Add to `.env` file: `METABEEAI_DATA_DIR=/path/to/data`

### "No answers.json files found"
- **Cause**: LLM pipeline hasn't been run yet
- **Fix**: Run `metabeeai llm` first to generate `answers.json` files

### Empty output files
- **Cause**: No data found for that question type
- **Check**: Review sample `answers.json` files to ensure questions were answered

### Network visualization issues
- **Cause**: Missing data files from extraction phase
- **Fix**: Run all `investigate_*.py` scripts before `network_analysis.py`

### "Species not specified" appears frequently
- **Cause**: LLM couldn't extract species names from papers
- **Expected**: These are automatically filtered out in trend and network analyses

---

## Dependencies

Core dependencies are included when installing the `metabeeai` package:
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `matplotlib` - Plotting
- `seaborn` - Statistical visualization
- `networkx` - Network analysis
- `python-dotenv` - Environment variable management

If installing from source, dependencies can be installed via:
```bash
pip install -r requirements.txt
```

---

(alternative-python-module-syntax)=
## Alternative: Python Module Syntax

All scripts can be run directly as Python modules. The examples above use this syntax. For programmatic access:

```python
# Import functions for custom scripts
from metabeeai.query_database.investigate_bee_species import get_papers_dir, extract_bee_species
from metabeeai.query_database.investigate_pesticides import extract_pesticides_from_file
from metabeeai.query_database.trend_analysis import analyze_co_occurrence

# Use functions programmatically
# ...
```

---

## Related Documentation

- **LLM Pipeline**: See `../metabeeai_llm/README.md` for generating `answers.json` files
- **Benchmarking**: See `../llm_benchmarking/README.md` for evaluating LLM quality
- **PDF Processing**: See `../process_pdfs/README.md` for preparing PDFs
- **Review Software**: See `../llm_review_software/README.md` for creating golden answers

---

**Last Updated**: November 21 2025
