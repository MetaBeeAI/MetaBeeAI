# Fixed PDF annotator
#
# Execute with:
#   python metabee/annotator.py --basepath data
#
# m.mieskolainen@imperial.ac.uk, 2025

import argparse
import json
import os

import fitz  # PyMuPDF
from termcolor import cprint


def convert_relative_to_absolute(page, rel_box):
    # Get page dimensions (width, height)
    width, height = page.rect.width, page.rect.height
    # Convert relative (0-1) coordinates to absolute values
    l = rel_box["l"] * width
    t = rel_box["t"] * height
    r = rel_box["r"] * width
    b = rel_box["b"] * height
    return fitz.Rect(l, t, r, b)


def annotate_pdf(pdf_path, merged_json_path, output_pdf, answers_json_path=None):
    """
    Annotate PDFs with bounding boxes.
    First, annotate all "question-answer" chunks (red boxes).
    Then, if an answers.json file is provided, gather field names for each chunk_id and annotate
    with blue boxes and a combined text label.
    """

    # Load merged JSON file.
    with open(merged_json_path, "r", encoding="utf-8") as f:
        merged = json.load(f)
    cprint(f"Loaded merged JSON: {merged_json_path}", "white")

    doc = fitz.open(pdf_path)

    # Annotate "question-answer" chunks with red rectangles.
    for chunk in merged["data"]["chunks"]:
        if chunk.get("chunk_type") == "question-answer":
            if "grounding" in chunk:
                for g in chunk["grounding"]:
                    page_num = g["page"]
                    if page_num < len(doc):
                        page = doc[page_num]
                        rect = convert_relative_to_absolute(page, g["box"])
                        # Draw a red rectangle with a width of 1.
                        page.draw_rect(rect, color=(1, 0, 0), width=1)

    # If answers.json is provided, process it.
    if answers_json_path and os.path.isfile(answers_json_path):
        with open(answers_json_path, "r", encoding="utf-8") as f:
            answers = json.load(f)
        cprint(f"Loaded answers JSON: {answers_json_path}", "cyan")

        # Build a dictionary mapping chunk_id to chunk for quick lookup.
        chunk_dict = {}
        for chunk in merged["data"]["chunks"]:
            cid = chunk.get("chunk_id")
            if cid:
                chunk_dict[cid] = chunk

        # Build a mapping from chunk_id to a set of field names.
        cid_to_fields = {}

        # Helper: Recursively extract chunk_ids from nested dictionaries.
        def extract_chunk_ids(d, current_label):
            if isinstance(d, dict):
                if "chunk_ids" in d:
                    for cid in d["chunk_ids"]:
                        cid_to_fields.setdefault(cid, set()).add(current_label)
                else:
                    for k, v in d.items():
                        extract_chunk_ids(v, k)
            elif isinstance(d, list):
                for item in d:
                    extract_chunk_ids(item, current_label)

        questions = answers.get("QUESTIONS", {})
        for question_key, question_value in questions.items():
            # For questions, either the field value directly has chunk_ids or search recursively.
            if isinstance(question_value, dict):
                for field_key, field_value in question_value.items():
                    if isinstance(field_value, dict) and "chunk_ids" in field_value:
                        for cid in field_value["chunk_ids"]:
                            cid_to_fields.setdefault(cid, set()).add(field_key)
                    else:
                        extract_chunk_ids(field_value, field_key)

        # Annotate each chunk from answers.json using the aggregated field names.
        for cid, fields in cid_to_fields.items():
            if cid in chunk_dict:
                chunk = chunk_dict[cid]
                if "grounding" in chunk:
                    for g in chunk["grounding"]:
                        page_num = g["page"]
                        if page_num < len(doc):
                            page = doc[page_num]
                            rect = convert_relative_to_absolute(page, g["box"])

                            # Draw a blue rectangle for answer-related chunks.
                            page.draw_rect(rect, color=(0, 0, 1), width=1)

                            # Insert a text annotation at the top left of the box.
                            field_text = ", ".join(sorted(fields))
                            annot_text = f"{cid}: ({field_text})"

                            shift = -5
                            page.insert_text(
                                (rect.x0, rect.y0 + shift), annot_text, fontname="helv", fontsize=5, color=(0, 0, 1)
                            )
            else:
                cprint(f"Warning: Chunk id {cid} not found in merged JSON", "yellow")
    else:
        cprint("No answers.json found - not processing answer-based annotations", "red")

    try:
        doc.save(output_pdf)
        cprint(f"Annotated PDF saved as: {output_pdf}", "green")
    except Exception as e:
        cprint(f"Error in saving PDF: {output_pdf}. Exception: {e}", "red")


def process_all_papers(base_papers_dir):
    """
    Process each paper folder (names that are digits) in sorted order.
    """
    paper_folders = sorted(
        [
            folder
            for folder in os.listdir(base_papers_dir)
            if os.path.isdir(os.path.join(base_papers_dir, folder)) and folder.isdigit()
        ]
    )

    for paper_folder in paper_folders:
        paper_path = os.path.join(base_papers_dir, paper_folder)
        pages_dir = os.path.join(paper_path, "pages")

        # Define file paths (adjust filenames as needed).
        original_pdf_path = os.path.join(paper_path, f"{paper_folder}_main.pdf")
        merged_json_path = os.path.join(pages_dir, "merged_v2.json")
        output_pdf = os.path.join(paper_path, f"{paper_folder}_main_annotated.pdf")
        answers_json_path = os.path.join(paper_path, "answers.json")

        # Check if necessary files exist.
        if not os.path.isfile(original_pdf_path):
            cprint(f"Paper {paper_folder}: Missing original PDF: {original_pdf_path}", "red")
            continue
        if not os.path.isfile(merged_json_path):
            cprint(f"Paper {paper_folder}: Missing merged JSON: {merged_json_path}", "red")
            continue

        # Annotate PDF (answers_json_path is optional).
        annotate_pdf(original_pdf_path, merged_json_path, output_pdf, answers_json_path)
        cprint(f"Paper {paper_folder}: Processing complete", "magenta")
        print()


def main():
    parser = argparse.ArgumentParser(description="Annotate PDFs using merged JSON and answers.json for papers.")
    parser.add_argument(
        "--basepath",
        type=str,
        default=os.getcwd(),
        help="Base path containing the 'papers' folder. Defaults to the current working directory.",
    )
    args = parser.parse_args()

    papers_dir = os.path.join(args.basepath, "papers")
    if not os.path.isdir(papers_dir):
        cprint(f"Error: 'papers' folder not found in {args.basepath}", "red")
        return
    process_all_papers(papers_dir)


if __name__ == "__main__":
    main()
