# src/metabeeai/cli.py
"""
MetaBeeAI Command-Line Interface
--------------------------------
Provides multiple subcommands:
- `metabeeai llm`: Run the LLM pipeline to extract literature answers
- `metabeeai process-pdfs`: Process PDFs through the complete pipeline (split, API, merge, deduplicate)
- `metabeeai review`: Launch GUI for reviewing and annotating LLM output
- `metabeeai prep-benchmark`: Prepare benchmarking data from GUI reviewer answers
Future: add subcommands for run-all, run benchmarks, query_database, etc.
"""

import sys
import argparse
import importlib
from pathlib import Path
from dotenv import load_dotenv


def handle_llm_command(args):
    """Handle the 'llm' subcommand."""
    pipeline = importlib.import_module("metabeeai.metabeeai_llm.llm_pipeline")
    # Build sys.argv from parsed args
    sys.argv = ["llm_pipeline.py"]
    if args.dir:
        sys.argv.extend(["--dir", args.dir])
    if args.folders:
        sys.argv.extend(["--folders"] + args.folders)
    if args.overwrite:
        sys.argv.append("--overwrite")
    if args.relevance_model:
        sys.argv.extend(["--relevance-model", args.relevance_model])
    if args.answer_model:
        sys.argv.extend(["--answer-model", args.answer_model])
    if args.config:
        sys.argv.extend(["--config", args.config])
    sys.exit(pipeline.main() if hasattr(pipeline, "main") else pipeline.__main__())


def handle_process_pdfs_command(args):
    """Handle the 'process-pdfs' subcommand."""
    process_module = importlib.import_module("metabeeai.process_pdfs.process_all")
    # Build sys.argv from parsed args
    sys.argv = ["process_all.py"]
    if args.dir:
        sys.argv.extend(["--dir", args.dir])
    if args.start:
        sys.argv.extend(["--start", args.start])
    if args.end:
        sys.argv.extend(["--end", args.end])
    if args.merge_only:
        sys.argv.append("--merge-only")
    if args.skip_split:
        sys.argv.append("--skip-split")
    if args.skip_api:
        sys.argv.append("--skip-api")
    if args.skip_merge:
        sys.argv.append("--skip-merge")
    if args.skip_deduplicate:
        sys.argv.append("--skip-deduplicate")
    if args.filter_chunk_type:
        sys.argv.extend(["--filter-chunk-type"] + args.filter_chunk_type)
    if args.pages != 1:
        sys.argv.extend(["--pages", str(args.pages)])
    sys.exit(process_module.main())


def handle_review_command(args):
    """Handle the 'review' subcommand (GUI for reviewing and annotating LLM output)."""
    beegui_module = importlib.import_module("metabeeai.llm_review_software.beegui")
    sys.exit(beegui_module.main())


def handle_prep_benchmark_command(args):
    """Handle the 'prep-benchmark' subcommand."""
    prep_module = importlib.import_module("metabeeai.llm_benchmarking.prep_benchmark_data")
    # Build sys.argv from parsed args
    sys.argv = ["prep_benchmark_data.py"]
    if args.papers_dir:
        sys.argv.extend(["--papers-dir", args.papers_dir])
    if args.questions_yml:
        sys.argv.extend(["--questions-yml", args.questions_yml])
    if args.output:
        sys.argv.extend(["--output", args.output])
    sys.exit(prep_module.main())


def main():
    """CLI entrypoint for metabeeai."""
    load_dotenv()  # auto-load API keys and config

    parser = argparse.ArgumentParser(
        prog="metabee",
        description="MetaBeeAI command-line interface",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- metabee llm ---------------------------------------------------------
    llm_parser = subparsers.add_parser(
        "llm", help="Run the LLM pipeline to extract literature answers"
    )
    llm_parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Base directory containing paper folders (default: auto-detect from config)",
    )
    llm_parser.add_argument(
        "--folders",
        type=str,
        nargs="+",
        default=None,
        help="Specific paper folder names to process (e.g., 283C6B42 3ZHNVADM). "
             "If not specified, all folders will be processed.",
    )
    llm_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing merged.json files",
    )
    llm_parser.add_argument(
        "--relevance-model",
        type=str,
        default=None,
        help="Model for chunk selection (e.g., 'openai/gpt-4o-mini')",
    )
    llm_parser.add_argument(
        "--answer-model",
        type=str,
        default=None,
        help="Model for answer generation (e.g., 'openai/gpt-4o')",
    )
    llm_parser.add_argument(
        "--config",
        type=str,
        choices=["fast", "balanced", "quality"],
        default=None,
        help="Use predefined configuration: "
             "'fast', 'balanced', or 'quality'",
    )

    # --- metabee process-pdfs ------------------------------------------------
    process_parser = subparsers.add_parser(
        "process-pdfs",
        help="Process PDFs through the complete pipeline (split, API, merge, deduplicate)"
    )
    process_parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Directory containing paper subfolders (defaults to config/env)",
    )
    process_parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="First folder name to process (alphanumeric order, defaults to first folder)",
    )
    process_parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="Last folder name to process (alphanumeric order, defaults to last folder)",
    )
    process_parser.add_argument(
        "--merge-only",
        action="store_true",
        help="Only run merge and deduplication steps (skip expensive PDF splitting and API processing)",
    )
    process_parser.add_argument(
        "--skip-split",
        action="store_true",
        help="Skip PDF splitting step",
    )
    process_parser.add_argument(
        "--skip-api",
        action="store_true",
        help="Skip Vision API processing step",
    )
    process_parser.add_argument(
        "--skip-merge",
        action="store_true",
        help="Skip JSON merging step",
    )
    process_parser.add_argument(
        "--skip-deduplicate",
        action="store_true",
        help="Skip deduplication step",
    )
    process_parser.add_argument(
        "--filter-chunk-type",
        nargs="+",
        default=[],
        help="Chunk types to filter out during merging (e.g., marginalia figure)",
    )
    process_parser.add_argument(
        "--pages",
        type=int,
        choices=[1, 2],
        default=1,
        help="Number of pages per split: 1 for single-page (default), 2 for overlapping 2-page",
    )

    # --- metabee review ------------------------------------------------------
    review_parser = subparsers.add_parser(
        "review",
        help="Launch GUI for reviewing and annotating LLM output"
    )
    # No arguments needed - the GUI handles file selection

    # --- metabee prep-benchmark ----------------------------------------------
    prep_benchmark_parser = subparsers.add_parser(
        "prep-benchmark",
        help="Prepare benchmarking data from GUI reviewer answers"
    )
    prep_benchmark_parser.add_argument(
        "--papers-dir",
        type=str,
        default=None,
        help="Base directory containing paper folders (default: auto-detect from config)",
    )
    prep_benchmark_parser.add_argument(
        "--questions-yml",
        type=str,
        default=None,
        help="Path to questions.yml file (default: ../metabeeai_llm/questions.yml)",
    )
    prep_benchmark_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: data/benchmark_data_gui.json)",
    )

    # Map commands to their handler functions
    command_handlers = {
        "llm": handle_llm_command,
        "process-pdfs": handle_process_pdfs_command,
        "review": handle_review_command,
        "prep-benchmark": handle_prep_benchmark_command,
    }

    # Parse top-level args
    args = parser.parse_args()

    # Dispatch to the appropriate handler
    handler = command_handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
