# process_pdfs/__init__.py
# PDF processing utilities for MetaBeeAI pipeline

# Avoid name clash between submodule 'batch_deduplicate' and function 'batch_deduplicate'
from .batch_deduplicate import run_batch_deduplicate
from .deduplicate_chunks import analyze_chunk_uniqueness, deduplicate_chunks, process_merged_json_file
from .merger import adjust_and_merge_json, process_all_papers
from .split_pdf import split_pdfs
from .va_process_papers import process_papers

__all__ = [
    "split_pdfs",
    "process_papers",
    "process_all_papers",
    "adjust_and_merge_json",
    "run_batch_deduplicate",
    "analyze_chunk_uniqueness",
    "deduplicate_chunks",
    "process_merged_json_file",
]
