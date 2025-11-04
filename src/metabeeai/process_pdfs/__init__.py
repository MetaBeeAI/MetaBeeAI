# process_pdfs/__init__.py
# PDF processing utilities for MetaBeeAI pipeline

from .split_pdf import split_pdfs
from .va_process_papers import process_papers
from .merger import process_all_papers, adjust_and_merge_json
from .batch_deduplicate import batch_deduplicate
from .deduplicate_chunks import (
    analyze_chunk_uniqueness,
    deduplicate_chunks,
    process_merged_json_file
)

__all__ = [
    'split_pdfs',
    'process_papers',
    'process_all_papers',
    'adjust_and_merge_json',
    'batch_deduplicate',
    'analyze_chunk_uniqueness',
    'deduplicate_chunks',
    'process_merged_json_file'
]
