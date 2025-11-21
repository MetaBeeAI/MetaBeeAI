# PDF Processing Pipeline

This submodule provides scripts for converting PDF scientific papers into structured JSON format suitable for LLM-based information extraction.

## Overview

The PDF processing pipeline converts raw PDF papers into structured JSON chunks through four main steps:

1. **Split PDFs** - Break papers into single-page documents or overlapping 2-page segments
2. **Vision API Processing** - Extract text and structure using Landing AI's Vision Agentic API
3. **Merge JSON Files** - Combine individual page JSON files into a single document
4. **Deduplicate Chunks** - Remove duplicate text chunks (primarily for overlapping pages)

## Installation

This submodule is part of the `metabeeai` package. Install it via:

```bash
pip install metabeeai
```

Or if installing from source:

```bash
pip install -e /path/to/MetaBeeAI
```

**Required dependencies**: PyPDF2, requests, python-dotenv, termcolor, pathlib

---

## Quick Start

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
# LANDING_AI_API_KEY=your_landing_ai_api_key_here
```

The `.env` file is located in the project root directory and is hidden from git for security.

3. **Input Data Format**: Your papers must be organized as follows:
```
papers/
├── 95UKMIEY/
│   └── 95UKMIEY_main.pdf
├── CX9M8HCM/
│   └── CX9M8HCM_main.pdf
├── V7984AAU/
│   └── V7984AAU_main.pdf
...
```

Each paper should have:
- A folder with an alphanumeric name (e.g., `95UKMIEY`, `CX9M8HCM`, `001`, etc.)
- A PDF file named `{folder_name}_main.pdf` inside that folder
- Folders are processed in alphanumeric (lexicographic) order

---

### Basic Usage - Complete Pipeline

When the `metabeeai` package is installed, use the CLI command:

Run all steps for all papers in directory:
```bash
metabeeai process-pdfs
```

Run all steps for a range of papers (alphanumeric order):
```bash
metabeeai process-pdfs --start 95UKMIEY --end CX9M8HCM
```

Run with a custom directory:
```bash
metabeeai process-pdfs --dir /path/to/papers --start 95UKMIEY --end CX9M8HCM
```

**Merge-only mode** (skip expensive PDF splitting and API processing):
```bash
# Process all papers - only merge and deduplicate
metabeeai process-pdfs --merge-only

# Process specific papers - only merge and deduplicate
metabeeai process-pdfs --merge-only --start 95UKMIEY --end CX9M8HCM
```

**Note**: For Python module syntax alternatives, see the [Alternative: Python Module Syntax](#alternative-python-module-syntax) section below.

---

## Core Files

### 1. `process_all.py` - **Main Pipeline Runner**

**Purpose**: Orchestrates all four steps of the PDF processing pipeline in sequence.

**Usage** (CLI - Recommended):

When the `metabeeai` package is installed, use the CLI command:

```bash
# Process all papers (all steps)
metabeeai process-pdfs

# Process papers in a specific range (alphanumeric order)
metabeeai process-pdfs --start 95UKMIEY --end CX9M8HCM

# Process papers from a starting folder to the end
metabeeai process-pdfs --start 95UKMIEY

# Merge-only mode (skip expensive PDF splitting and API processing)
metabeeai process-pdfs --merge-only

# Merge-only for specific papers
metabeeai process-pdfs --merge-only --start 95UKMIEY --end CX9M8HCM

# Filter out marginalia chunks during merging
metabeeai process-pdfs --start 95UKMIEY --end CX9M8HCM --filter-chunk-type marginalia

# Split into overlapping 2-page documents
metabeeai process-pdfs --pages 2

# Skip specific steps
metabeeai process-pdfs --skip-split --skip-api
```

**Note**: For Python module syntax alternatives, see the [Alternative: Python Module Syntax](#alternative-python-module-syntax) section below.

**Command-line options**:
- `--start FOLDER`: First folder name to process (optional; defaults to first folder in alphanumeric order)
- `--end FOLDER`: Last folder name to process (optional; defaults to last folder in alphanumeric order)
- `--dir PATH`: Custom papers directory (default: from config/env)
- `--merge-only`: Only run merge and deduplication steps (skip expensive PDF splitting and API processing)
- `--skip-split`: Skip PDF splitting step
- `--skip-api`: Skip Vision API processing step
- `--skip-merge`: Skip JSON merging step
- `--skip-deduplicate`: Skip chunk deduplication step
- `--filter-chunk-type TYPE [TYPE ...]`: Filter out specific chunk types (e.g., marginalia, figure)

**Output**: Creates the following files for each paper:
- `papers/XXX/pages/main_p01-02.pdf`, `main_p02-03.pdf`, etc. (split PDFs)
- `papers/XXX/pages/main_p01-02.pdf.json`, etc. (API responses)
- `papers/XXX/pages/merged_v2.json` (final merged and deduplicated file)

---

### 2. `split_pdf.py` - PDF Splitter

**Purpose**: Splits multi-page PDFs into either single-page documents or overlapping 2-page segments.

**Why overlapping pages?**: Scientific papers often have content that spans across pages (tables, paragraphs). Overlapping 2-page segments ensure we don't lose information at page boundaries.

**Usage**:

This script can be run directly as a Python module:

```bash
# Split into single-page documents (default)
python -m metabeeai.process_pdfs.split_pdf /path/to/papers

# Split into single-page documents (explicit)
python -m metabeeai.process_pdfs.split_pdf /path/to/papers --pages 1

# Split into overlapping 2-page documents
python -m metabeeai.process_pdfs.split_pdf /path/to/papers --pages 2
```

**Note**: For Python module syntax alternatives, see the [Alternative: Python Module Syntax](#alternative-python-module-syntax) section below.

**Command-line options**:
- `--pages {1,2}`: Number of pages per split (default: 1)
  - `1` = single-page documents (`main_p01.pdf`, `main_p02.pdf`, etc.)
  - `2` = overlapping 2-page documents (`main_p01-02.pdf`, `main_p02-03.pdf`, etc.)

**How it works**:
1. Finds all `{folder_name}_main.pdf` files in paper folders
2. Creates a `pages/` subdirectory in each paper folder
3. Generates split PDFs based on `--pages` option:

   **Single-page mode (--pages 1)**:
   - `main_p01.pdf` (page 1)
   - `main_p02.pdf` (page 2)
   - `main_p03.pdf` (page 3)
   - etc.

   **Overlapping 2-page mode (--pages 2)**:
   - `main_p01-02.pdf` (pages 1-2)
   - `main_p02-03.pdf` (pages 2-3)
   - `main_p03-04.pdf` (pages 3-4)
   - etc.

**Example**:
- **Single-page mode**: A 10-page paper generates 10 split PDFs
- **2-page mode**: A 10-page paper generates 9 overlapping split PDFs

---

### 3. `va_process_papers.py` - Vision API Processor
#### Options

- `--pages {1,2}`: Number of pages per split (default: 1)
  - `1` = single-page documents (`main_p01.pdf`, `main_p02.pdf`, etc.)
  - `2` = overlapping 2-page documents (`main_p01-02.pdf`, `main_p02-03.pdf`, etc.)

- **Single-page mode**: A 10-page paper generates 10 split PDFs of 1 page each.
- **2-page mode**: A 10-page paper generates 9 overlapping split PDFs of 2 pages each.

#### `split_pdf` examples

```bash
# Split into single-page documents (default)
python split_pdf.py /path/to/papers

# Split into single-page documents (explicit)
python split_pdf.py /path/to/papers --pages 1

# Split into overlapping 2-page documents
python split_pdf.py /path/to/papers --pages 2
```

---

### `va_process_papers` - Vision API Processor

**Purpose**: Processes each split PDF through Landing AI's Vision Agentic Document Analysis API to extract text and structure.

**Usage**:

This script can be run directly as a Python module:

```bash
# Process all papers
python -m metabeeai.process_pdfs.va_process_papers --dir data/papers

# Start from a specific folder (useful for resuming - alphanumeric order)
python -m metabeeai.process_pdfs.va_process_papers --dir data/papers --start 95UKMIEY
```

**Note**: For Python module syntax alternatives, see the [Alternative: Python Module Syntax](#alternative-python-module-syntax) section below.

**Command-line options**:
- `--dir PATH`: Papers directory (default: data/papers)
- `--start FOLDER`: Starting folder name (alphanumeric order, e.g., 95UKMIEY, CX9M8HCM)

**How it works**:
1. Processes folders in alphanumeric order
2. Finds all split PDF files in `papers/{FOLDER}/pages/`
3. Sends each PDF to the Vision Agentic API
4. Saves the JSON response as `{pdf_filename}.json`
5. Skips files that already have JSON outputs (resume-friendly)
6. Logs all processing activity with timestamps

**Output**: Creates JSON files with this structure:
```json
{
  "data": {
    "chunks": [
      {
        "chunk_id": "unique_id",
        "text": "Extracted text content...",
        "chunk_type": "paragraph",
        "grounding": [
          {
            "page": 0,
            "bbox": [x1, y1, x2, y2]
          }
        ],
        "metadata": {...}
      }
    ]
  }
}
```

**Important**: This step requires a valid `LANDING_AI_API_KEY` in your `.env` file.

---

### 4. `merger.py` - JSON Merger

**Purpose**: Combines individual page JSON files into a single `merged_v2.json` file per paper, handling overlapping pages correctly.

**Usage**:

This script can be run directly as a Python module:

```bash
# Merge all papers
python -m metabeeai.process_pdfs.merger --basepath /path/to/data

# Filter out marginalia chunks
python -m metabeeai.process_pdfs.merger --basepath /path/to/data --filter-chunk-type marginalia

# Filter multiple chunk types
python -m metabeeai.process_pdfs.merger --basepath /path/to/data --filter-chunk-type marginalia figure
```

**Note**: For Python module syntax alternatives, see the [Alternative: Python Module Syntax](#alternative-python-module-syntax) section below.

**Command-line options**:
- `--basepath PATH`: Base path containing the `papers/` folder
- `--filter-chunk-type TYPE [TYPE ...]`: Chunk types to exclude from output

**How it works**:
1. Finds all `main_*.json` files in `papers/XXX/pages/`
2. Adjusts page numbers to account for overlapping pages
3. Merges all chunks into a single JSON structure
4. Optionally filters out specified chunk types
5. Saves as `merged_v2.json`

**Page number adjustment**: Since pages overlap, the merger maps overlapping pages to the same global page number to avoid duplication.

**Example**:
- File 1 (pages 1-2): Global pages 1-2
- File 2 (pages 2-3): Page 2 maps to global page 2, page 3 becomes global page 3
- File 3 (pages 3-4): Page 3 maps to global page 3, page 4 becomes global page 4

**Output format**:
```json
{
  "data": {
    "chunks": [
      {
        "chunk_id": "unique_id",
        "text": "...",
        "chunk_type": "paragraph",
        "grounding": [{"page": 0, "bbox": [...]}],
        "metadata": {...}
      }
    ]
  }
}
```

---

### 5. `deduplicate_chunks.py` - Chunk Deduplication Module

**Purpose**: Provides functions to identify and remove duplicate text chunks that result from overlapping pages.

**Usage as a module**:
```python
from deduplicate_chunks import analyze_chunk_uniqueness, deduplicate_chunks

# Analyze duplication
analysis = analyze_chunk_uniqueness(chunks)
print(f"Found {analysis['duplicate_chunks']} duplicates")

# Deduplicate
deduplicated_chunks = deduplicate_chunks(chunks)
```

**Key functions**:
- `analyze_chunk_uniqueness(chunks)` - Returns statistics about duplicates
- `deduplicate_chunks(chunks)` - Removes duplicates while preserving all chunk IDs
- `get_duplicate_summary(chunks)` - Human-readable summary of duplicates
- `process_merged_json_file(path)` - Process a single merged JSON file

**How deduplication works**:
1. Groups chunks by text content
2. For duplicate groups, keeps one chunk but preserves all chunk IDs
3. Adds metadata about the deduplication process

**Duplicate handling**: When duplicates are found, the deduplicated chunk includes:
- `chunk_id`: Primary chunk ID (first occurrence)
- `chunk_ids`: List of all chunk IDs with the same text
- `original_chunk_id`: Reference to the original ID

---

### 6. `batch_deduplicate.py` - Batch Deduplication Runner

**Purpose**: Processes all `merged_v2.json` files in a directory to remove duplicates.

**Usage**:

This script can be run directly as a Python module:

```bash
# Deduplicate all papers
python -m metabeeai.process_pdfs.batch_deduplicate

# Deduplicate papers in a range (for numeric folders, backward compatibility)
python -m metabeeai.process_pdfs.batch_deduplicate --start-paper 1 --end-paper 10

# Dry run (analyze without modifying files)
python -m metabeeai.process_pdfs.batch_deduplicate --dry-run

# Custom directory
python -m metabeeai.process_pdfs.batch_deduplicate --base-dir /path/to/papers

# Verbose output
python -m metabeeai.process_pdfs.batch_deduplicate --verbose
```

**Note**: For Python module syntax alternatives, see the [Alternative: Python Module Syntax](#alternative-python-module-syntax) section below.

**Command-line options**:
- `--base-dir PATH`: Base directory containing paper folders
- `--start-paper N`: First paper number to process (for numeric folders only)
- `--end-paper N`: Last paper number to process (for numeric folders only)
- `--dry-run`: Analyze files without making changes
- `--output FILE`: Save results summary to file
- `--verbose`, `-v`: Enable verbose logging

**Note**: When called from `process_all.py`, the folder list is automatically provided to support alphanumeric folder names.

**How it works**:
1. Finds all paper folders with `merged_v2.json` files
2. Analyzes each file for duplicate chunks
3. Deduplicates and overwrites the file (unless `--dry-run`)
4. Generates a summary report

**Output**: Creates a summary JSON file with:
```json
{
  "status": "completed",
  "total_papers": 10,
  "processed_papers": 10,
  "total_duplicates_removed": 145,
  "results": [...]
}
```

---

## Individual Script Usage

### Running Steps Separately

If you need to run individual steps (useful for debugging or resuming):

#### Step 1: Split PDFs
```bash
python -m metabeeai.process_pdfs.split_pdf /path/to/papers
```

#### Step 2: Process with Vision API
```bash
python -m metabeeai.process_pdfs.va_process_papers --dir /path/to/papers
```

#### Step 3: Merge JSON files
```bash
python -m metabeeai.process_pdfs.merger --basepath /path/to/data
```

#### Step 4: Deduplicate chunks
```bash
python -m metabeeai.process_pdfs.batch_deduplicate --base-dir /path/to/papers
```

**Note**: For Python module syntax alternatives, see the [Alternative: Python Module Syntax](#alternative-python-module-syntax) section below.

---

## Input Data Format

### Required Directory Structure

```
papers/
├── 95UKMIEY/
│   └── 95UKMIEY_main.pdf
├── CX9M8HCM/
│   └── CX9M8HCM_main.pdf
├── V7984AAU/
│   └── V7984AAU_main.pdf
...
```

**Requirements**:
- Each paper must be in a folder with an alphanumeric name (any format: `95UKMIEY`, `001`, `ABC123`, etc.)
- PDF file must be named `{folder_name}_main.pdf` (matching the folder name)
- Folders are processed in alphanumeric (lexicographic) order
- PDFs should be complete scientific papers (not split or partial)

### PDF Requirements

- **Format**: Valid PDF files
- **Content**: Text-based PDFs work best (scanned PDFs may have lower quality)
- **Size**: No strict limits, but very large files may take longer to process
- **Pages**: Multi-page documents are fully supported

---

## Output Data Format

### Final Output: `merged_v2.json`

The pipeline produces a `merged_v2.json` file for each paper with the following structure:

```json
{
  "data": {
    "chunks": [
      {
        "chunk_id": "unique_chunk_identifier",
        "text": "The extracted text content from the PDF...",
        "chunk_type": "paragraph",
        "grounding": [
          {
            "page": 0,
            "bbox": [x1, y1, x2, y2]
          }
        ],
        "chunk_ids": ["id1", "id2"],
        "metadata": {
          "confidence": 0.95,
          "font_size": 12,
          ...
        }
      }
    ]
  },
  "deduplication_info": {
    "original_chunks": 500,
    "unique_chunks": 450,
    "duplicates_removed": 50,
    "duplication_rate": 10.0,
    "duplicate_groups": 25
  }
}
```

### Field Descriptions:

- **chunk_id**: Unique identifier for this chunk
- **text**: Extracted text content
- **chunk_type**: Type of content (paragraph, heading, table, figure, marginalia, etc.)
- **grounding**: Location information
  - **page**: Page number (0-indexed)
  - **bbox**: Bounding box coordinates [x1, y1, x2, y2]
- **chunk_ids**: List of all chunk IDs with identical text (after deduplication)
- **metadata**: Additional information from the Vision API
- **deduplication_info**: Statistics about the deduplication process

This format is designed to be consumed by the LLM pipeline in `../metabeeai_llm/`.

---

## Understanding the Process Flow

### Complete Pipeline Flow

```
Raw PDF → Split PDF → Vision API → Individual JSONs → Merged JSON → Deduplicated JSON
```

**Detailed steps** (example with overlapping 2-page mode):

1. **Input**: `95UKMIEY_main.pdf` (10 pages)

2. **After Splitting** (with `--pages 2`):
   ```
   pages/main_p01-02.pdf
   pages/main_p02-03.pdf
   pages/main_p03-04.pdf
   ...
   pages/main_p09-10.pdf
   ```

   **Or with single-page mode** (`--pages 1`, default):
   ```
   pages/main_p01.pdf
   pages/main_p02.pdf
   pages/main_p03.pdf
   ...
   pages/main_p10.pdf
   ```

3. **After API Processing**:
   ```
   pages/main_p01-02.pdf.json  (or main_p01.pdf.json in single-page mode)
   pages/main_p02-03.pdf.json  (or main_p02.pdf.json in single-page mode)
   ...
   pages/main_p09-10.pdf.json  (or main_p10.pdf.json in single-page mode)
   ```

4. **After Merging**:
   ```
   pages/merged_v2.json (contains all chunks with adjusted page numbers)
   ```

5. **After Deduplication**:
   ```
   pages/merged_v2.json (duplicates removed, chunk IDs preserved)
   ```

---

## Troubleshooting

### "LANDING_AI_API_KEY not found"
- **Cause**: API key not configured in `.env` file
- **Fix**:
  ```bash
  cp ../env.example ../.env
  # Edit .env and add your LANDING_AI_API_KEY
  ```

### "PDF file not found"
- **Cause**: PDF file not named correctly or in wrong location
- **Fix**: Ensure PDFs are named `{folder_number}_main.pdf` and in the correct folder

### "No merged_v2.json files found"
- **Cause**: Merger step hasn't been run yet or failed
- **Fix**: Run `python -m metabeeai.process_pdfs.merger --basepath /path/to/data` first, or use `metabeeai process-pdfs --skip-split --skip-api` to run merge and deduplication steps

### API processing is slow
- **Cause**: Vision API processes each page individually
- **Solution**: This is normal. Processing time depends on:
  - Number of papers
  - Pages per paper
  - API response time
  - The script will automatically resume if interrupted

### Duplicate chunks remain after deduplication
- **Cause**: Chunks might have slight text differences
- **Fix**: Check the deduplication_info in merged_v2.json for statistics
- **Note**: Only exact text matches are considered duplicates

### Out of API quota
- **Cause**: Too many API calls
- **Fix**:
  - The script automatically skips already-processed files
  - Use `--start` parameter to resume from a specific paper
  - Contact Landing AI to increase your quota

---

## Advanced Usage

### Merge-Only Mode (Cost-Effective)

If you've already run the expensive PDF splitting and Vision API processing steps, you can use `--merge-only` to only run the merge and deduplication steps:

```bash
# Process all papers - merge and deduplicate only
metabeeai process-pdfs --merge-only

# Process specific papers - merge and deduplicate only
metabeeai process-pdfs --merge-only --start 95UKMIEY --end CX9M8HCM
```

This is useful when:
- You've already processed PDFs through the Vision API
- You want to re-run merging with different filter options
- You want to re-deduplicate after manual edits to JSON files
- You're testing the merge/deduplication logic without API costs

**Note**: Merge-only mode validates that JSON files exist (not PDFs) and automatically skips the split and API steps.

### Processing All Papers Automatically

If you don't specify `--start` and `--end`, the pipeline will automatically detect and process all folders in your papers directory:

```bash
# Process all papers found in the directory
metabeeai process-pdfs

# Process all papers with merge-only
metabeeai process-pdfs --merge-only
```

The script will:
1. Scan the papers directory for all subfolders
2. Sort them alphanumerically (lexicographic order: `283C6B42`, `3ZHNVADM`, `4KV2ZB36`, etc.)
3. Process from the first to the last folder found

### Filtering Chunk Types

You can filter out specific chunk types during merging:

```bash
# Remove marginalia (page numbers, headers, footers)
metabeeai process-pdfs --start 95UKMIEY --end CX9M8HCM --filter-chunk-type marginalia

# Remove multiple types
metabeeai process-pdfs --start 95UKMIEY --end CX9M8HCM --filter-chunk-type marginalia figure

# When running merger separately
python -m metabeeai.process_pdfs.merger --basepath /path/to/data --filter-chunk-type marginalia
```

Common chunk types to filter:
- `marginalia` - Headers, footers, page numbers
- `figure` - Figure captions (if you only want main text)
- `table` - Table content (if you only want prose)

### Resuming Processing

If processing is interrupted, the pipeline is resume-friendly:

```bash
# API processing automatically skips existing JSON files
python -m metabeeai.process_pdfs.va_process_papers --dir /path/to/papers --start 95UKMIEY

# Process all with resumption from a specific folder
metabeeai process-pdfs --start 95UKMIEY

# Deduplication can be re-run on specific papers (numeric folders)
python -m metabeeai.process_pdfs.batch_deduplicate --start-paper 50 --end-paper 100
```

### Dry Run Mode

Test the pipeline without making changes:

```bash
# Analyze duplication without modifying files
python -m metabeeai.process_pdfs.batch_deduplicate --dry-run

# See what would happen
python -m metabeeai.process_pdfs.batch_deduplicate --dry-run --verbose
```

---

## Performance Tips

1. **Parallel Processing**: The Vision API processes one file at a time. For faster processing, consider running multiple instances on different paper ranges:
   ```bash
   # Terminal 1
   metabeeai process-pdfs --start 283C6B42 --end 76DQP2DC

   # Terminal 2
   metabeeai process-pdfs --start 8BV8BLU8 --end ZTRRIKQ3
   ```

2. **Resume from Failures**: If processing fails partway through, use `--skip-split` and `--start` to resume:
   ```bash
   metabeeai process-pdfs --start 95UKMIEY --skip-split
   ```

3. **Monitor Progress**: Check log files created in the papers directory:
   ```bash
   tail -f papers/processing_log_*.txt
   ```

---

## Dependencies

Core dependencies are included when installing the `metabeeai` package:
- `PyPDF2` - PDF manipulation
- `requests` - API calls
- `python-dotenv` - Environment variable management
- `termcolor` - Colored console output
- `pathlib` - Path operations (built-in)

If installing from source, dependencies can be installed via:
```bash
pip install -r requirements.txt
```

---

## Next Steps

After processing your PDFs:

1. Verify output files:
   ```bash
   ls papers/95UKMIEY/pages/merged_v2.json
   ```

2. Check deduplication statistics in the JSON file

3. Proceed to the LLM pipeline:
   ```bash
   metabeeai llm --folders 95UKMIEY CX9M8HCM
   ```

---

## Alternative: Python Module Syntax

Instead of using the CLI commands, you can also run the scripts directly as Python modules. This is useful if you need to integrate the functionality into other Python scripts or prefer direct module execution.

### Running the Complete Pipeline

```bash
# Process all papers (all steps)
python -m metabeeai.process_pdfs.process_all

# Process papers in a specific range (alphanumeric order)
python -m metabeeai.process_pdfs.process_all --start 95UKMIEY --end CX9M8HCM

# Process papers from a starting folder to the end
python -m metabeeai.process_pdfs.process_all --start 95UKMIEY

# Merge-only mode (skip expensive PDF splitting and API processing)
python -m metabeeai.process_pdfs.process_all --merge-only

# Filter out marginalia chunks during merging
python -m metabeeai.process_pdfs.process_all --start 95UKMIEY --end CX9M8HCM --filter-chunk-type marginalia

# Split into overlapping 2-page documents
python -m metabeeai.process_pdfs.process_all --pages 2
```

### Running Individual Steps

```bash
# Step 1: Split PDFs
python -m metabeeai.process_pdfs.split_pdf /path/to/papers --pages 2

# Step 2: Process with Vision API
python -m metabeeai.process_pdfs.va_process_papers --dir /path/to/papers --start 95UKMIEY

# Step 3: Merge JSON files
python -m metabeeai.process_pdfs.merger --basepath /path/to/data --filter-chunk-type marginalia

# Step 4: Deduplicate chunks
python -m metabeeai.process_pdfs.batch_deduplicate --base-dir /path/to/papers --dry-run
```

### Using Functions Programmatically

```python
from metabeeai.process_pdfs.split_pdf import split_pdfs
from metabeeai.process_pdfs.va_process_papers import process_papers
from metabeeai.process_pdfs.merger import process_all_papers
from metabeeai.process_pdfs.batch_deduplicate import batch_deduplicate
from metabeeai.process_pdfs.deduplicate_chunks import deduplicate_chunks, analyze_chunk_uniqueness

# Use functions programmatically in your own scripts
# ...
```

All command-line arguments are identical between CLI commands and Python module syntax. The only difference is the invocation method.

---

## Related Documentation

- **LLM Pipeline**: See `../metabeeai_llm/README.md` for extracting information from processed papers
- **Data Analysis**: See `../query_database/` for analyzing extracted data
- **Configuration**: See `../config.py` for centralized configuration

---

**Last Updated**: Nov 21 2025
