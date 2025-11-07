# PDF Processing Pipeline

This folder contains scripts for converting PDF scientific papers into structured JSON format suitable for LLM-based information extraction.

## Overview

The PDF processing pipeline converts raw PDF papers into structured JSON chunks through four main steps, each of these steps can be run independently or together via the `process_all.py` script.

1. **Split PDFs** - Break papers into single-page documents or overlapping 2-page segments
2. **Vision API Processing** - Extract text and structure using Landing AI's Vision Agentic API
3. **Merge JSON Files** - Combine individual page JSON files into a single document
4. **Deduplicate Chunks** - Remove duplicate text chunks (primarily for overlapping pages)

---

**Input Data Format**: Your papers must be organized as follows:

```text
papers/
├── 95UKMIEY/
│   └── 95UKMIEY_main.pdf
├── CX9M8HCM/
│   └── CX9M8HCM_main.pdf
├── V7984AAU/
│   └── V7984AAU_main.pdf
...
```

For each pdf you intend to process, you need:

- A PDF file named with a unique alphanumeric key in the form of `{key}_main.pdf` (e.g., `95UKMIEY_main.pdf`, `CX9M8HCM_main.pdf`, `001_main.pdf`, etc.)
- The PDF should be placed in a folder named with the same key, e.g., `papers/001/001_main.pdf`
- Folders will be processed in alphanumeric (lexicographic) order
- PDFs should be complete scientific papers (not split or partial)

---

## Execution

Run all steps for all papers in directory:

```bash
python process_all.py
```

Run all steps for a range of papers (alphanumeric order):

```bash
python process_all.py --start 95UKMIEY --end CX9M8HCM
```

Run with a custom directory:

```bash
python process_all.py --dir /path/to/papers --start 95UKMIEY --end CX9M8HCM
```

### Merge-only mode

To skip the expensive PDF splitting and Vision API processing steps (if already done previously), you can use `--merge-only`:

```bash
# Process all papers - only merge and deduplicate
python process_all.py --merge-only

# Process specific papers - only merge and deduplicate
python process_all.py --merge-only --start 95UKMIEY --end CX9M8HCM
```

---

## Running individual steps

### `process_all.py` - **Whole PDF Processing Pipeline**

Orchestrates all four steps of the PDF processing pipeline in sequence.

#### Output

Creates the following files for each paper:

- The split PDFs: `papers/XXX/pages/main_p01-02.pdf`, `main_p02-03.pdf`, etc.
- The API responses: `papers/XXX/pages/main_p01-02.pdf.json`, etc.
- The final merged and deduplicated file: `papers/XXX/pages/merged_v2.json`

#### Options

- `--start FOLDER`: First folder name to process (optional; defaults to first folder in alphanumeric order)
- `--end FOLDER`: Last folder name to process (optional; defaults to last folder in alphanumeric order)
- `--dir PATH`: Custom papers directory (default: from config/env)
- `--merge-only`: Only run merge and deduplication steps (skip expensive PDF splitting and API processing)
- `--skip-split`: Skip PDF splitting step
- `--skip-api`: Skip Vision API processing step
- `--skip-merge`: Skip JSON merging step
- `--skip-deduplicate`: Skip chunk deduplication step
- `--filter-chunk-type TYPE [TYPE ...]`: Filter out specific chunk types (e.g., marginalia, figure)

#### Examples

```bash
# Process all papers (all steps)
python process_all.py

# Process papers in a specific range (alphanumeric order)
python process_all.py --start 95UKMIEY --end CX9M8HCM

# Process papers from a starting folder to the end
python process_all.py --start 95UKMIEY

# Merge-only mode (skip expensive PDF splitting and API processing)
python process_all.py --merge-only

# Merge-only and specific range of papers
python process_all.py --merge-only --start 95UKMIEY --end CX9M8HCM

# Filter out marginalia chunks during merging
python process_all.py --start 95UKMIEY --end CX9M8HCM --filter-chunk-type marginalia
```

---

### `split_pdf` - PDF Splitter

Splits multi-page PDFs into either a collection of single-page documents or overlapping 2-page segments.
These smaller PDFs can be fed into the Vision API for text extraction, where the full documents are too large to process at once.

**Why overlapping pages?**: Scientific papers often have content that spans across pages (tables, paragraphs). Overlapping 2-page segments ensure we don't lose information at page boundaries.
In practice, we have found the single-page mode to be sufficient for most papers, but you may find using overlapping pages improves text continuity in some cases.

1. Finds all `{folder_name}_main.pdf` files in paper folders
2. Creates a `pages/` subdirectory in each paper folder
3. Generates split PDFs, the length of which is controlled by the `--pages` parameter.

#### Output

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

1. Processes folders in alphanumeric order
2. Finds all split PDF files in `papers/{FOLDER}/pages/`
3. Sends each PDF to the Vision Agentic API
4. Saves the JSON response as `{pdf_filename}.json`
5. Skips files that already have JSON outputs (resume-friendly)
6. Logs all processing activity with timestamps

#### Output

Creates JSON files with the following structure:

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

#### Options

- `--dir PATH`: Papers directory (default: data/papers)
- `--start FOLDER`: Starting folder name (alphanumeric order, e.g., 95UKMIEY, CX9M8HCM)

**Important**: SSince this step accesses the Vision API, it requires a valid `LANDING_AI_API_KEY` in your `.env` file.

#### `va_process_papers` examples

```bash
# Process all papers in the default directory
python va_process_papers.py --dir /path/to/papers

# Process papers starting from a specific paper
python va_process_papers.py --dir /path/to/papers --start 95UKMIEY
```

---

### `merger.py` - JSON Merger

The output of the Vision API is one JSON file per split PDF, this step combines these JSON files into a single `merged_v2.json` file per paper, handling overlapping pages correctly.

1. Finds all `main_*.json` files in `papers/XXX/pages/`
2. Adjusts page numbers to account for overlapping pages
3. Merges all chunks into a single JSON structure
4. Optionally filters out specified chunk types
5. Saves as `merged_v2.json`

Since pages overlap, the merger maps overlapping pages to the same global page number to avoid duplication.

- File 1 (pages 1-2): Global pages 1-2
- File 2 (pages 2-3): Page 2 maps to global page 2, page 3 becomes global page 3
- File 3 (pages 3-4): Page 3 maps to global page 3, page 4 becomes global page 4

#### Options

- `--basepath PATH`: Base path containing the `papers/` folder
- `--filter-chunk-type TYPE [TYPE ...]`: Chunk types to exclude from output

#### `merger.py` examples

```bash
# Merge all papers
python merger.py --basepath /path/to/data

# Filter out marginalia chunks
python merger.py --basepath /path/to/data --filter-chunk-type marginalia

# Filter multiple chunk types
python merger.py --basepath /path/to/data --filter-chunk-type marginalia figure
```

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

### `batch_deduplicate.py` - Batch Deduplication

Processes all `merged_v2.json` files in a directory to remove duplicates.

1. Finds all folders in the papers directory with `merged_v2.json` files
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

#### Options

- `--base-dir PATH`: Base directory containing paper folders
- `--start-paper N`: First paper number to process (for numeric folders only)
- `--end-paper N`: Last paper number to process (for numeric folders only)
- `--dry-run`: Analyze files without making changes
- `--output FILE`: Save results summary to file
- `--verbose`, `-v`: Enable verbose logging

#### `batch_deduplicate.py` examples

```bash
# Deduplicate all papers
python batch_deduplicate.py

# Deduplicate papers in a range (for numeric folders, backward compatibility)
python batch_deduplicate.py --start-paper 1 --end-paper 10

# Dry run (analyze without modifying files)
python batch_deduplicate.py --dry-run

# Custom directory
python batch_deduplicate.py --base-dir /path/to/papers

# Verbose output
python batch_deduplicate.py --verbose
```

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

```text
Raw PDF → Split PDF → Vision API → Individual JSONs → Merged JSON → Deduplicated JSON
```

**Detailed steps** (example with overlapping 2-page mode):

1. **Input**: `95UKMIEY_main.pdf` (10 pages)

2. **After Splitting** (with `--pages 2`):

   ```text
   pages/main_p01-02.pdf
   pages/main_p02-03.pdf
   pages/main_p03-04.pdf
   ...
   pages/main_p09-10.pdf
   ```

   **Or with single-page mode** (`--pages 1`, default):

   ```text
   pages/main_p01.pdf
   pages/main_p02.pdf
   pages/main_p03.pdf
   ...
   pages/main_p10.pdf
   ```

3. **After API Processing**:

   ```text
   pages/main_p01-02.pdf.json  (or main_p01.pdf.json in single-page mode)
   pages/main_p02-03.pdf.json  (or main_p02.pdf.json in single-page mode)
   ...
   pages/main_p09-10.pdf.json  (or main_p10.pdf.json in single-page mode)
   ```

4. **After Merging**:

   ```text
   pages/merged_v2.json (contains all chunks with adjusted page numbers)
   ```

5. **After Deduplication**:

   ```text
   pages/merged_v2.json (duplicates removed, chunk IDs preserved)
   ```

---

## Troubleshooting FAQ

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
- **Fix**: Run `python merger.py --basepath /path/to/data` first

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
python process_all.py --merge-only

# Process specific papers - merge and deduplicate only
python process_all.py --merge-only --start 1 --end 10
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
python process_all.py

# Process all papers with merge-only
python process_all.py --merge-only
```

The script will:

1. Scan the papers directory for all subfolders
2. Sort them alphanumerically (lexicographic order: `283C6B42`, `3ZHNVADM`, `4KV2ZB36`, etc.)
3. Process from the first to the last folder found

### Filtering Chunk Types

You can filter out specific chunk types during merging:

```bash
# Remove marginalia (page numbers, headers, footers)
python process_all.py --start 95UKMIEY --end CX9M8HCM --filter-chunk-type marginalia

# Remove multiple types
python process_all.py --start 95UKMIEY --end CX9M8HCM --filter-chunk-type marginalia figure

# When running merger separately
python merger.py --basepath /path/to/data --filter-chunk-type marginalia
```

Common chunk types to filter:
- `marginalia` - Headers, footers, page numbers
- `figure` - Figure captions (if you only want main text)
- `table` - Table content (if you only want prose)

### Resuming Processing

If processing is interrupted, the pipeline is resume-friendly:

```bash
# API processing automatically skips existing JSON files
python va_process_papers.py --dir /path/to/papers --start 95UKMIEY

# Process all with resumption from a specific folder
python process_all.py --start 95UKMIEY

# Deduplication can be re-run on specific papers (numeric folders)
python batch_deduplicate.py --start-paper 50 --end-paper 100
```

### Dry Run Mode

Test the pipeline without making changes:

```bash
# Analyze duplication without modifying files
python batch_deduplicate.py --dry-run

# See what would happen
python batch_deduplicate.py --dry-run --verbose
```

---

## Performance Tips

1. **Parallel Processing**: The Vision API processes one file at a time. For faster processing, consider running multiple instances on different paper ranges:

   ```bash
   # Terminal 1
   python process_all.py --start 283C6B42 --end 76DQP2DC
   
   # Terminal 2  
   python process_all.py --start 8BV8BLU8 --end ZTRRIKQ3
   ```

2. **Resume from Failures**: If processing fails partway through, use `--skip-split` and `--start` to resume:

   ```bash
   python process_all.py --start 95UKMIEY --skip-split
   ```

3. **Monitor Progress**: Check log files created in the papers directory:

   ```bash
   tail -f papers/processing_log_*.txt
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
   cd ../metabeeai_llm
   python llm_pipeline.py --start 95UKMIEY --end CX9M8HCM
   ```

---

## Related Documentation

- **LLM Pipeline**: See `./metabeeai_llm` for LLM-based extraction
- **Data Analysis**: See `../query_database` for analyzing extracted data
- **Configuration**: See `../config.py` for centralized configuration

---
