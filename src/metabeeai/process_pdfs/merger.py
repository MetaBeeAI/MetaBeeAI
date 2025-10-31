# Splitted json merger tool which handles both single-page and overlapping
# 2-page PDF formats
# 
# Execute with:
#   python metabeeai_llm/merger.py --basepath data
#
# m.mieskolainen@imperial.ac.uk, 2025

import argparse
import json
import os
from termcolor import cprint

def detect_page_mode(json_files):
    """
    Detect whether PDFs are single-page or 2-page overlapping format.
    
    Returns:
        str: 'single' for single-page (main_p01.pdf.json), 
             'overlap' for 2-page overlapping (main_p01-02.pdf.json)
    """
    if not json_files:
        return 'single'
    
    # Check the first filename for the pattern
    first_file = os.path.basename(json_files[0])
    # Remove .json extension and check if there's a hyphen in the page numbers
    # Pattern: main_p01-02.pdf.json (overlap) vs main_p01.pdf.json (single)
    if '-' in first_file and 'main_p' in first_file:
        return 'overlap'
    return 'single'

def adjust_and_merge_json(json_files, output_file, filter_types=None):
    if filter_types is None:
        filter_types = []
    merged = {"data": {"chunks": []}}
    page_offset = 0  # global offset for merged pages
    
    # Detect whether we're dealing with single-page or overlapping 2-page PDFs
    page_mode = detect_page_mode(json_files)

    for i, file in enumerate(json_files):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Collect all page numbers from grounding entries in this file (only for chunks not filtered out)
        pages_in_file = []
        for chunk in data["data"]["chunks"]:
            if filter_types and "chunk_type" in chunk and chunk["chunk_type"] in filter_types:
                continue
            if "grounding" in chunk:
                for g in chunk["grounding"]:
                    pages_in_file.append(g["page"])

        if pages_in_file:
            file_min_page = min(pages_in_file)
            file_max_page = max(pages_in_file)
        else:
            file_min_page = 0
            file_max_page = 0

        if page_mode == 'single':
            # Single-page mode: no overlap, just sequential pages
            for chunk in data["data"]["chunks"]:
                if filter_types and "chunk_type" in chunk and chunk["chunk_type"] in filter_types:
                    continue
                if "grounding" in chunk:
                    for g in chunk["grounding"]:
                        # Adjust page number by offset (each file adds 1 page)
                        g["page"] = g["page"] + page_offset
                merged["data"]["chunks"].append(chunk)
            # Each file represents 1 page
            page_offset += 1
        else:
            # Overlapping 2-page mode: handle overlap
            if i == 0:
                # For the first file, no overlap to remove.
                max_new_page_this_file = None
                for chunk in data["data"]["chunks"]:
                    if filter_types and "chunk_type" in chunk and chunk["chunk_type"] in filter_types:
                        continue
                    if "grounding" in chunk:
                        for g in chunk["grounding"]:
                            new_page = g["page"] + page_offset
                            g["page"] = new_page
                            if max_new_page_this_file is None or new_page > max_new_page_this_file:
                                max_new_page_this_file = new_page
                    merged["data"]["chunks"].append(chunk)
                if max_new_page_this_file is not None:
                    page_offset = max_new_page_this_file + 1
            else:
                # For subsequent files, adjust overlapping page by mapping overlapping grounding entries
                # to the same global page (page_offset - 1) instead of skipping them.
                max_new_page_this_file = None
                for chunk in data["data"]["chunks"]:
                    if filter_types and "chunk_type" in chunk and chunk["chunk_type"] in filter_types:
                        continue
                    if "grounding" in chunk:
                        new_grounding = []
                        for g in chunk["grounding"]:
                            if g["page"] == file_min_page:
                                # Map the overlapping page to the previous global page
                                new_page = (g["page"] - file_min_page) + (page_offset - 1)
                            else:
                                new_page = (g["page"] - (file_min_page + 1)) + page_offset
                            g["page"] = new_page
                            new_grounding.append(g)
                            if max_new_page_this_file is None or new_page > max_new_page_this_file:
                                max_new_page_this_file = new_page
                        chunk["grounding"] = new_grounding
                    merged["data"]["chunks"].append(chunk)
                # Update offset based on the number of pages in the current file.
                page_offset += (file_max_page - file_min_page)

    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(merged, out, indent=2)


def process_all_papers(base_papers_dir, filter_types):
    # Process each paper folder in alphanumeric sorted order
    paper_folders = sorted([
        folder for folder in os.listdir(base_papers_dir)
        if os.path.isdir(os.path.join(base_papers_dir, folder))
    ])

    for paper_folder in paper_folders:
        paper_path = os.path.join(base_papers_dir, paper_folder)
        pages_dir = os.path.join(paper_path, "pages")

        if os.path.isdir(pages_dir):
            # Find all JSON files starting with "main_" in the pages subfolder.
            json_files = [
                os.path.join(pages_dir, f)
                for f in os.listdir(pages_dir)
                if f.startswith("main_") and f.endswith(".json")
            ]
            json_files.sort()
            if json_files:
                output_file = os.path.join(pages_dir, "merged_v2.json")
                page_mode = detect_page_mode(json_files)
                mode_desc = "single-page" if page_mode == 'single' else "overlapping 2-page"
                adjust_and_merge_json(json_files, output_file, filter_types)
                cprint(f"Paper {paper_folder}: Merged {len(json_files)} files ({mode_desc} mode) into {output_file}", "green")

                # Load the merged file to compute total pages and total chunks.
                with open(output_file, "r", encoding="utf-8") as f:
                    merged_data = json.load(f)
                chunks = merged_data["data"]["chunks"]
                total_chunks = len(chunks)

                # Compute unique pages from all grounding entries.
                pages = {g["page"]
                         for chunk in chunks if "grounding" in chunk
                         for g in chunk["grounding"]}
                total_pages = max(pages) + 1 if pages else 0
                print(f"Paper {paper_folder}: Total pages: {total_pages}, Total chunks: {total_chunks}")


def main():
    parser = argparse.ArgumentParser(
        description="Merge JSON files for papers and print page/chunk counts per paper."
    )
    parser.add_argument(
        "--basepath",
        type=str,
        default=os.getcwd(),
        help="Base path containing the 'papers' folder. Defaults to the current working directory."
    )
    parser.add_argument(
        "--filter-chunk-type",
        nargs='+',
        default=[],
        help="List of keywords for filtering out chunks based on 'chunk_type' (e.g., marginalia)."
    )
    args = parser.parse_args()

    papers_dir = os.path.join(args.basepath, "papers")
    if not os.path.isdir(papers_dir):
        print(f"Error: papers folder not found in {args.basepath}")
        return
    process_all_papers(papers_dir, args.filter_chunk_type)


if __name__ == "__main__":
    main()
