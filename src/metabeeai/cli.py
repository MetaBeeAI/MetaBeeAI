# src/metabeeai/cli.py
"""
MetaBeeAI Command-Line Interface
--------------------------------
Phase 1: replicate the LLM pipeline runner (`metabee run`).
Future: add subcommands for process_pdfs, benchmarking, etc.
"""

import sys
import argparse
import importlib
from pathlib import Path
from dotenv import load_dotenv


def main():
    """CLI entrypoint for `metabee run`."""
    load_dotenv()  # auto-load API keys and config

    parser = argparse.ArgumentParser(
        prog="metabee",
        description="MetaBeeAI command-line interface",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- metabee run ---------------------------------------------------------
    run_parser = subparsers.add_parser(
        "run", help="Run the LLM pipeline to extract literature answers"
    )
    run_parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Base directory containing paper folders (default: auto-detect from config)",
    )
    run_parser.add_argument(
        "--folders",
        type=str,
        nargs="+",
        default=None,
        help="Specific paper folder names to process (e.g., 283C6B42 3ZHNVADM). "
             "If not specified, all folders will be processed.",
    )
    run_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing merged.json files",
    )
    run_parser.add_argument(
        "--relevance-model",
        type=str,
        default=None,
        help="Model for chunk selection (e.g., 'openai/gpt-4o-mini')",
    )
    run_parser.add_argument(
        "--answer-model",
        type=str,
        default=None,
        help="Model for answer generation (e.g., 'openai/gpt-4o')",
    )
    run_parser.add_argument(
        "--config",
        type=str,
        choices=["fast", "balanced", "quality"],
        default=None,
        help="Use predefined configuration: "
             "'fast', 'balanced', or 'quality'",
    )

    # Parse top-level args
    args, extra = parser.parse_known_args()

    if args.command == "run":
        # Import lazily to avoid circulars
        pipeline = importlib.import_module("metabeeai.metabeeai_llm.llm_pipeline")
        # Re-use its argparse logic
        sys.argv = ["llm_pipeline.py"] + extra  # forward any unparsed args
        sys.exit(pipeline.main() if hasattr(pipeline, "main") else pipeline.__main__())

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
