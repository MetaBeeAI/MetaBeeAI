# Query Database - Data Extraction and Analysis

This folder contains scripts for extracting structured data from LLM-generated answers and performing network and trend analyses on bee-pesticide research data.

## Overview

The query database pipeline consists of two main phases:
1. **Data Extraction** - Extract structured information from `answers.json` files
2. **Analysis & Visualization** - Analyze relationships, trends, and co-occurrences

---

## Workflow

### Phase 1: Data Extraction (Run First)

Extract structured data from LLM answers for different question types:

```bash
# Extract bee species data
python investigate_bee_species.py

# Extract pesticide data
python investigate_pesticides.py

# Extract additional stressors data
python investigate_additional_stressors.py

# Extract significance/findings data
python investigate_significance.py
```

**What these scripts do**: Parse `answers.json` files from the LLM pipeline and extract structured information into JSON/CSV files for analysis.

### Phase 2: Analysis & Visualization (Run After Extraction)

Analyze the extracted data and create visualizations:

```bash
# Analyze trends and co-occurrences
python trend_analysis.py

# Create network visualizations
python network_analysis.py
```

**What these scripts do**: Load the extracted data files and generate statistical analyses, plots, and network visualizations.

---

## Data Extraction Scripts

### 1. `investigate_bee_species.py`

**Purpose**: Extracts bee species information from LLM answers.

**Usage**:
```bash
python investigate_bee_species.py
```

**Input**:
- `{papers_dir}/{paper_id}/answers.json` - LLM-generated answers

**Output**:
- `output/bee_species_data.json` - Structured bee species data

**Data structure**:
```json
{
  "paper_id": "729",
  "species_name": "Apis mellifera carnica",
  "genus": "Apis",
  "species": "mellifera",
  "subspecies": "carnica",
  "common_name": "Carniolan honey bee"
}
```

**What it does**:
1. Scans all paper directories for `answers.json` files
2. Extracts bee species information from the `bee_species` question
3. Parses species names into taxonomic components (genus, species, subspecies)
4. Identifies common names where available
5. Handles multiple species per paper
6. Validates and standardizes species names

---

### 2. `investigate_pesticides.py`

**Purpose**: Extracts pesticide exposure information from LLM answers.

**Usage**:
```bash
python investigate_pesticides.py
```

**Input**:
- `{papers_dir}/{paper_id}/answers.json` - LLM-generated answers

**Output**:
- `output/pesticides_data.json` - Structured pesticide data

**Data structure**:
```json
{
  "paper_id": "729",
  "pesticide_name": "imidacloprid",
  "dose": "10 ppb",
  "exposure_method": "oral",
  "duration": "7 days"
}
```

**What it does**:
1. Extracts pesticide information from the `pesticides` question
2. Parses chemical names, doses, exposure methods, and durations
3. Handles multiple pesticides per paper
4. Standardizes pesticide names (converts to lowercase)
5. Extracts quantitative dose information when available
6. Categorizes exposure methods (oral, contact, topical, field, etc.)

---

### 3. `investigate_additional_stressors.py`

**Purpose**: Extracts information about non-pesticide stressors tested in studies.

**Usage**:
```bash
python investigate_additional_stressors.py
```

**Input**:
- `{papers_dir}/{paper_id}/answers.json` - LLM-generated answers

**Output**:
- `output/additional_stressors_data.json` - Structured stressor data

**Data structure**:
```json
{
  "paper_id": "729",
  "stressor_type": "Pathogen",
  "stressor_name": "Nosema ceranae",
  "details": "10^5 spores per bee, oral inoculation, 7 days"
}
```

**What it does**:
1. Extracts additional stressor information from the `additional_stressors` question
2. Categorizes stressors by type (Temperature, Pathogen, Parasite, Nutritional, Chemical, Environmental)
3. Extracts stressor names and application details
4. Handles multiple stressors per paper
5. Excludes pesticides (captured separately by `investigate_pesticides.py`)

---

### 4. `investigate_significance.py`

**Purpose**: Extracts key findings and significance statements from studies.

**Usage**:
```bash
python investigate_significance.py
```

**Input**:
- `{papers_dir}/{paper_id}/answers.json` - LLM-generated answers

**Output**:
- `output/significance_data.json` - Structured findings data

**Data structure**:
```json
{
  "paper_id": "729",
  "finding": "Imidacloprid at 10 ppb impaired learning and memory",
  "category": "Cognitive Effects"
}
```

**What it does**:
1. Extracts key findings from the `significance` question
2. Parses individual findings from multi-point answers
3. Categorizes findings by impact type
4. Preserves both original and processed versions of data
5. Handles quantitative results and effect descriptions

---

## Analysis Scripts

### 5. `trend_analysis.py`

**Purpose**: Analyzes trends and co-occurrence patterns between bee species and pesticides.

**Usage**:
```bash
python trend_analysis.py
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

### 6. `network_analysis.py`

**Purpose**: Creates network visualizations showing relationships between bees, pesticides, and stressors.

**Usage**:
```bash
python network_analysis.py
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

## Prerequisites

1. **Environment Setup**:
```bash
# Activate your virtual environment
source ../venv/bin/activate  # On Mac/Linux
```

2. **Data Requirements**:
- Must have run the LLM pipeline first (`../metabeeai_llm/llm_pipeline.py`)
- Each paper must have an `answers.json` file
- `METABEEAI_DATA_DIR` environment variable must be set in `.env`

3. **Expected data structure**:
```
papers/
├── 001/
│   └── answers.json
├── 002/
│   └── answers.json
└── ...
```

---

## Complete Workflow Example

```bash
# Step 1: Activate environment
source ../venv/bin/activate

# Step 2: Extract all data types
python investigate_bee_species.py
python investigate_pesticides.py
python investigate_additional_stressors.py
python investigate_significance.py

# Step 3: Run analyses
python trend_analysis.py
python network_analysis.py

# Step 4: Review outputs
ls -lh output/
ls -lh output/trend_analysis_plots/
ls -lh output/network_plots/
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

## Advanced Usage

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
- **Fix**: Run `python ../metabeeai_llm/llm_pipeline.py --start 1 --end 10` first

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

## Dependencies

Core dependencies (install via `pip install -r ../requirements.txt`):
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `matplotlib` - Plotting
- `seaborn` - Statistical visualization
- `networkx` - Network analysis
- `python-dotenv` - Environment variable management

---

## Related Documentation

- **LLM Pipeline**: See `../metabeeai_llm/README.md` for generating `answers.json` files
- **Benchmarking**: See `../llm_benchmarking/README.md` for evaluating LLM quality
- **PDF Processing**: See `../process_pdfs/README.md` for preparing PDFs

---

**Last Updated**: October 2025
