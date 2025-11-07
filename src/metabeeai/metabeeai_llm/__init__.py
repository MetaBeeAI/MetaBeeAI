"""
MetaBeeAI LLM Subpackage
========================

This subpackage contains high-level functions for LLM-assisted PDF
processing and literature review.

It re-exports commonly used tools from lower-level modules so that they
can be imported directly from ``metabeeai_llm``.
"""

from importlib import metadata

__all__ = [
    "split_pdfs",
    "process_papers",
    "check_chunk_ids_in_pages_dir",
    "get_literature_answers",
    "merge_json_in_the_folder",
]

__version__ = metadata.version("metabeeai")

# Import public-facing functions
# ---------------------------------------------------------------------

# Re-exported from other subpackages
from metabeeai.process_pdfs.split_pdf import split_pdfs
from metabeeai.process_pdfs.va_process_papers import process_papers

# Local implementations
from .unique_chunk_id import check_chunk_ids_in_pages_dir
from .llm_pipeline import get_literature_answers, merge_json_in_the_folder
