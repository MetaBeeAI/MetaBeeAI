# LLM Review Software

This submodule provides a graphical user interface (GUI) for reviewing and annotating LLM-generated answers from research papers. Reviewers use this software to create "golden" ground truth answers that are then used in the benchmarking pipeline to evaluate LLM performance.

## Overview

The `llm_review_software` submodule consists of two main components:

1. **BeeGUI** (`beegui.py`) - A PyQt5-based GUI application for interactive review and annotation
2. **PDF Annotator** (`annotator.py`) - A command-line tool for annotating PDFs with bounding boxes

### Purpose

The review software allows human reviewers to:
- Review LLM-generated answers from research papers
- Add, edit, and validate reviewer-provided answers
- Rate answer quality
- Select relevant text chunks from PDFs
- Generate `answers_extended.json` files containing "golden" ground truth answers

These "golden" answers are then used by the `llm_benchmarking` submodule to evaluate LLM performance against human-reviewed ground truth.

---

## Installation

This submodule is part of the `metabeeai` package. Install it via:

```bash
pip install metabeeai
```

Or if installing from source:

```bash
pip install -e /path/to/MetaBeeAI
```

**Required dependencies**: PyQt5, PyMuPDF (fitz), termcolor

---

## Usage

### Launching the Review GUI

When the `metabeeai` package is installed, launch the GUI using:

```bash
metabeeai review
```

The GUI will automatically attempt to load papers from `data/papers/` directory (or you can specify a different folder via File → Open Folder).

**Note**: For Python module syntax alternatives, see the [Alternative: Python Module Syntax](llm-review-software-alternative-python-module-syntax) section below.

---

## BeeGUI - Review Interface

### Interface Overview

The GUI consists of three main panes:

1. **Left Pane**: Paper navigation and controls
   - Paper list (shows all available papers with progress percentage)
   - Previous/Next paper buttons
   - Page navigation controls
   - Zoom slider
   - Modification status indicator

2. **Center Pane**: PDF viewer
   - Displays the current PDF page
   - Shows annotations (bounding boxes) for text chunks
   - Supports panning (drag) and zooming (Ctrl+wheel or slider)
   - Hover tooltips show chunk IDs and associated questions

3. **Right Pane**: Question panel and answer fields
   - Question list (from `answers.json`)
   - Answer input fields:
     - Positive answer
     - Negative answer
     - Positive reason
     - Negative reason
     - Star rating (0-5)
   - Chunk ID list (when a question is selected)
   - Mode buttons (Individual/All)

### Workflow

#### 1. Selecting a Paper

- Papers are listed in the left pane with their progress percentage
- Click on a paper ID to load it
- Use "Prev Paper" / "Next Paper" buttons to navigate
- Progress shows completion percentage based on filled answer fields

#### 2. Navigating PDF Pages

- Use "Prev Page" / "Next Page" buttons
- Use the zoom slider or Ctrl+wheel to zoom in/out
- Double-click the zoom slider to reset to 100%
- Drag to pan when zoomed in

#### 3. Selecting Questions

- Questions appear in the right pane (loaded from `answers.json`)
- Click on a question to select it
- When selected:
  - Associated chunks are highlighted on the PDF
  - Chunk IDs are listed below the question panel
  - Answer fields become editable

#### 4. Adding/Editing Answers

For each question, reviewers can provide:

- **Positive Answer** (`user_answer_positive`): The correct/positive answer
- **Negative Answer** (`user_answer_negative`): What should NOT be included
- **Positive Reason** (`user_reason_positive`): Reasoning for the positive answer
- **Negative Reason** (`user_reason_negative`): Reasoning for the negative answer
- **Rating** (`user_rating`): Star rating (0-5) indicating answer quality

**Note**: All changes are automatically saved to `answers_extended.json` in the paper folder.

#### 5. Annotation Modes

- **Individual Mode**: Shows annotations only for the currently selected question
- **All Mode**: Shows annotations for all questions (useful for overview)

#### 6. Viewing Chunks

- When a question is selected, associated chunk IDs are listed
- Click on a chunk ID to navigate to that chunk's location in the PDF
- Hover over annotations in the PDF to see chunk IDs and related questions

### Keyboard Shortcuts

- **F11**: Toggle full-screen mode
- **Up/Down arrows**: Navigate paper list (when focused)

### Menu Options

- **File → Open Folder**: Select a different papers directory
- **Options → Dark Mode / Light Mode**: Toggle theme
- **Options → Font Size**: Adjust font size (+/- buttons)
- **Help → About**: Application information

---

## PDF Annotator

The `annotator.py` script creates annotated PDFs with bounding boxes for visualization purposes.

### Usage

```bash
metabeeai annotate-pdfs --basepath /path/to/data
```

**Note**: For Python module syntax alternatives, see the [Alternative: Python Module Syntax](llm-review-software-alternative-python-module-syntax) section below.

### What It Does

The annotator processes all papers in the `papers/` directory and creates annotated PDFs:

- **Red boxes**: Question-answer chunks (from `merged_v2.json`)
- **Blue boxes**: Chunks referenced in `answers.json` (with field names as labels)

Output files are saved as `{paper_id}_main_annotated.pdf` in each paper folder.

### Command-Line Arguments

- `--basepath PATH`: Base path containing the `papers` folder (default: current directory)

---

## File Structure

### Required Files for Each Paper

Each paper folder should contain:

```
{paper_id}/
├── {paper_id}_main.pdf              # Original PDF
├── answers.json                      # LLM-generated answers (input)
├── answers_extended.json             # Reviewer answers (output - "golden" answers)
└── pages/
    └── merged_v2.json                # Processed paper chunks with grounding
```

### Output Format: `answers_extended.json`

The GUI creates/updates `answers_extended.json` with the following structure:

```json
{
  "QUESTIONS": {
    "question_key": {
      "user_answer_positive": "Reviewer's positive answer",
      "user_answer_negative": "What should NOT be included",
      "user_reason_positive": "Reasoning for positive answer",
      "user_reason_negative": "Reasoning for negative answer",
      "user_rating": 4
    }
  }
}
```

This file serves as the "golden" ground truth for benchmarking.

---

## Integration with Benchmarking Pipeline

The `answers_extended.json` files created by this review software are used as ground truth in the benchmarking pipeline:

1. **Review Phase** (this software):
   - Reviewers use BeeGUI to create `answers_extended.json` files
   - These contain human-reviewed "golden" answers

2. **Benchmarking Phase** (`llm_benchmarking` submodule):
   - `prep_benchmark_data.py` reads `answers_extended.json` files
   - Compares LLM answers (`answers.json`) against golden answers
   - Creates benchmark datasets for evaluation

See the `llm_benchmarking` README for details on the benchmarking workflow.

---

## Tips and Best Practices

### For Reviewers

1. **Start with Progress Overview**: Check the progress percentage in the paper list to see completion status

2. **Use Annotation Modes**:
   - Use "Individual" mode when focusing on one question
   - Use "All" mode to see all annotations and avoid duplicates

3. **Navigate Efficiently**:
   - Use keyboard shortcuts for faster navigation
   - Click chunk IDs to jump to specific locations

4. **Complete All Fields**: For best benchmarking results, fill in all answer fields (positive/negative answers and reasons)

5. **Save Frequently**: Changes auto-save, but you can verify by checking the "Modified" timestamp

### Data Quality

- Ensure `answers_extended.json` files are complete before running benchmarking
- Reviewers should be consistent in their rating criteria
- Check that chunk IDs in answers match actual PDF content

---

## Troubleshooting

### Issue: GUI doesn't launch

**Solution**: Ensure PyQt5 is installed:
```bash
pip install PyQt5
```

### Issue: Papers not showing in list

**Check**:
1. Papers directory exists and contains paper folders
2. Each paper folder has `{paper_id}_main.pdf` and `pages/merged_v2.json`
3. Paper folder names are numeric (e.g., "002", "003")

### Issue: PDF not displaying

**Check**:
1. PDF file exists: `{paper_id}_main.pdf`
2. File is not corrupted
3. PyMuPDF (fitz) is installed: `pip install pymupdf`

### Issue: Questions not appearing

**Check**:
1. `answers.json` exists in the paper folder
2. File has valid JSON structure with "QUESTIONS" key
3. File encoding is UTF-8

### Issue: Answers not saving

**Check**:
1. Write permissions on the paper folder
2. Disk space available
3. Check console output for error messages

---

## Configuration

The GUI automatically detects the papers directory from the `metabeeai.config` module. Default location is `data/papers/`.

You can change the directory via:
- **File → Open Folder** menu option
- The directory is remembered during the session

---

## Future Enhancements

The following features are planned for future versions:

- Screenshots and detailed visual guides for paper selection
- Step-by-step instructions for adding responses
- Batch processing capabilities
- Export/import functionality for reviewer annotations
- Collaborative review features

---

## References

- **Benchmarking Pipeline**: See `llm_benchmarking` submodule README
- **PDF Processing**: See `process_pdfs` submodule README
- **LLM Pipeline**: See `metabeeai_llm` submodule README

---

(llm-review-software-alternative-python-module-syntax)=
## Alternative: Python Module Syntax

Instead of using the CLI commands, you can also run the scripts directly as Python modules. This is useful if you need to integrate the functionality into other Python scripts or prefer direct module execution.

### Launching the Review GUI

```bash
python -m metabeeai.llm_review_software.beegui
```

### Running the PDF Annotator

```bash
python -m metabeeai.llm_review_software.annotator --basepath /path/to/data
```

### Example with Custom Options

```bash
# Annotate PDFs with custom base path
python -m metabeeai.llm_review_software.annotator --basepath /custom/path/to/data
```

All command-line arguments are identical between CLI commands and Python module syntax. The only difference is the invocation method.

---

## Support

For issues or questions:
1. Check this README first
2. Review error messages in console output
3. Verify file structure matches requirements
4. Check that all dependencies are installed

---

**Last Updated**: Nov 21 2025
