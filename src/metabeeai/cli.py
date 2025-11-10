# src/metabeeai/cli.py
"""
MetaBeeAI Command-Line Interface
--------------------------------
Provides multiple subcommands:
- `metabeeai llm`: Run the LLM pipeline to extract literature answers
- `metabeeai process-pdfs`: Process PDFs through the complete pipeline (split, API, merge, deduplicate)
- `metabeeai review`: Launch GUI for reviewing and annotating LLM output
- `metabeeai prep-benchmark`: Prepare benchmarking data from GUI reviewer answers
- `metabeeai benchmark`: Run DeepEval benchmarking on LLM outputs
- `metabeeai edge-cases`: Identify edge cases (low-scoring examples) from benchmarking results
- `metabeeai plot-metrics`: Create visualization plots from benchmarking results
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


def handle_benchmark_command(args):
    """Handle the 'benchmark' subcommand."""
    benchmark_module = importlib.import_module("metabeeai.llm_benchmarking.deepeval_benchmarking")
    # Build sys.argv from parsed args
    sys.argv = ["deepeval_benchmarking.py"]
    if args.question:
        sys.argv.extend(["--question", args.question])
    if args.input:
        sys.argv.extend(["--input", args.input])
    if args.limit:
        sys.argv.extend(["--limit", str(args.limit)])
    if args.batch_size != 25:  # Only add if different from default
        sys.argv.extend(["--batch-size", str(args.batch_size)])
    if args.max_retries != 5:  # Only add if different from default
        sys.argv.extend(["--max-retries", str(args.max_retries)])
    if args.model != "gpt-4o":  # Only add if different from default
        sys.argv.extend(["--model", args.model])
    if args.max_context_length != 200000:  # Only add if different from default
        sys.argv.extend(["--max-context-length", str(args.max_context_length)])
    if args.use_retrieval_only:
        sys.argv.append("--use-retrieval-only")
    if args.list_questions:
        sys.argv.append("--list-questions")
    sys.exit(benchmark_module.main())


def handle_edge_cases_command(args):
    """Handle the 'edge-cases' subcommand."""
    edge_cases_module = importlib.import_module("metabeeai.llm_benchmarking.edge_cases")
    # Build sys.argv from parsed args
    sys.argv = ["edge_cases.py"]
    if args.num_cases != 20:  # Only add if different from default
        sys.argv.extend(["--num-cases", str(args.num_cases)])
    if args.results_dir:
        sys.argv.extend(["--results-dir", args.results_dir])
    if args.merged_data_dir:
        sys.argv.extend(["--merged-data-dir", args.merged_data_dir])
    if args.output_dir:
        sys.argv.extend(["--output-dir", args.output_dir])
    if args.openai_api_key:
        sys.argv.extend(["--openai-api-key", args.openai_api_key])
    if args.model != "gpt-4o":  # Only add if different from default
        sys.argv.extend(["--model", args.model])
    if args.generate_summaries_only:
        sys.argv.append("--generate-summaries-only")
    if args.contextual_only:
        sys.argv.append("--contextual-only")
    if args.generate_contextual_summaries_only:
        sys.argv.append("--generate-contextual-summaries-only")
    sys.exit(edge_cases_module.main())


def handle_plot_metrics_command(args):
    """Handle the 'plot-metrics' subcommand."""
    plot_module = importlib.import_module("metabeeai.llm_benchmarking.plot_metrics_comparison")
    # Build sys.argv from parsed args
    sys.argv = ["plot_metrics_comparison.py"]
    if args.results_dir:
        sys.argv.extend(["--results-dir", args.results_dir])
    if args.output_dir:
        sys.argv.extend(["--output-dir", args.output_dir])
    sys.exit(plot_module.main())


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

    # --- metabee benchmark ---------------------------------------------------
    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Run DeepEval benchmarking on LLM outputs"
    )
    benchmark_parser.add_argument(
        "--question", "-q",
        type=str,
        help="Question key to filter by (optional - if not specified, processes all questions)",
    )
    benchmark_parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Input benchmark data file (default: auto-detect from config)",
    )
    benchmark_parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Maximum number of test cases to process (optional)",
    )
    benchmark_parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=25,
        help="Number of test cases to process per batch (default: 25)",
    )
    benchmark_parser.add_argument(
        "--max-retries", "-r",
        type=int,
        default=5,
        help="Maximum retries per batch (default: 5)",
    )
    benchmark_parser.add_argument(
        "--model", "-m",
        type=str,
        default="gpt-4o",
        choices=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        help="OpenAI model to use for evaluation (default: gpt-4o)",
    )
    benchmark_parser.add_argument(
        "--max-context-length",
        type=int,
        default=200000,
        help="Maximum context length in characters to process (default: 200000, ~50K tokens for gpt-4o)",
    )
    benchmark_parser.add_argument(
        "--use-retrieval-only",
        action="store_true",
        help="Use only retrieval_context instead of full context to reduce token usage",
    )
    benchmark_parser.add_argument(
        "--list-questions",
        action="store_true",
        help="List all available question keys in the benchmark data and exit",
    )

    # --- metabee edge-cases --------------------------------------------------
    edge_cases_parser = subparsers.add_parser(
        "edge-cases",
        help="Identify edge cases (low-scoring examples) from benchmarking results"
    )
    edge_cases_parser.add_argument(
        "--num-cases",
        type=int,
        default=20,
        help="Number of edge cases to identify per question type (default: 20)",
    )
    edge_cases_parser.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help="Directory containing evaluation results (default: auto-detect from config)",
    )
    edge_cases_parser.add_argument(
        "--merged-data-dir",
        type=str,
        default=None,
        help="Directory containing merged evaluation results (not used, kept for compatibility)",
    )
    edge_cases_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for edge cases (default: auto-detect from config)",
    )
    edge_cases_parser.add_argument(
        "--openai-api-key",
        type=str,
        default=None,
        help="OpenAI API key for LLM summarization (or set OPENAI_API_KEY env var)",
    )
    edge_cases_parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="OpenAI model to use for summarization (default: gpt-4o)",
    )
    edge_cases_parser.add_argument(
        "--generate-summaries-only",
        action="store_true",
        help="Only generate LLM summaries for existing edge case files (skip edge case identification)",
    )
    edge_cases_parser.add_argument(
        "--contextual-only",
        action="store_true",
        help="Only run contextual measures analysis (Faithfulness, Contextual Precision, Contextual Recall) for LLM data",
    )
    edge_cases_parser.add_argument(
        "--generate-contextual-summaries-only",
        action="store_true",
        help="Only generate LLM summaries for existing contextual edge case files (skip edge case identification)",
    )

    # --- metabee plot-metrics ------------------------------------------------
    plot_metrics_parser = subparsers.add_parser(
        "plot-metrics",
        help="Create visualization plots from benchmarking results"
    )
    plot_metrics_parser.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help="Directory containing evaluation results (default: auto-detect from config)",
    )
    plot_metrics_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for plots (default: same as results-dir)",
    )

    # Map commands to their handler functions
    command_handlers = {
        "llm": handle_llm_command,
        "process-pdfs": handle_process_pdfs_command,
        "review": handle_review_command,
        "prep-benchmark": handle_prep_benchmark_command,
        "benchmark": handle_benchmark_command,
        "edge-cases": handle_edge_cases_command,
        "plot-metrics": handle_plot_metrics_command,
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
