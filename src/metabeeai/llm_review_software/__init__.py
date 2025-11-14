# llm_review_software/__init__.py
# LLM review and annotation software for MetaBeeAI pipeline

from .annotator import annotate_pdf
from .beegui import MainWindow

# TODO this import does not exist
# from metabeeai.process_pdfs.merger import merge_json_in_the_folder

__all__ = [
    "MainWindow",
    "annotate_pdf",
]
