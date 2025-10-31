"""MetaBeeAI"""

from importlib import import_module

_submodules = [
    "llm_benchmarking",
    "llm_review_software",
    "metabeeai_llm",
    "process_pdfs",
    "query_database",
]

for _name in _submodules:
        globals()[_name] = import_module(f"{__name__}.{_name}")

__all__ = _submodules