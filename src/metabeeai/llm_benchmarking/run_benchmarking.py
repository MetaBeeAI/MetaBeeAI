#!/usr/bin/env python3
"""
Main benchmarking runner for MetaBeeAI LLM evaluation.

Orchestrates the complete benchmarking workflow:
1. Prepare benchmark data from GUI reviewer answers
2. Run DeepEval benchmarking with all 5 metrics
3. Visualize metrics across question types
4. Identify edge cases (lowest-scoring papers)

Usage:
    python run_benchmarking.py
    python run_benchmarking.py --question bee_species
    python run_benchmarking.py --skip-prep
    python run_benchmarking.py --skip-edge-cases
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path to access config
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from config import get_data_dir


def run_command(cmd, description, cwd=None):
    """Run a command and handle errors."""
    print("\n" + "="*60)
    print(f"STEP: {description}")
    print("="*60)
    print(f"Running: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True, cwd=cwd)
        print(f"[OK] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error in {description}: {e}")
        return False
    except FileNotFoundError:
        print(f"[ERROR] Could not find required script")
        return False


def build_prep_args(args):
    """Build arguments for prep_benchmark_data.py"""
    cmd = [sys.executable, "prep_benchmark_data.py"]
    if args.prep_papers_dir:
        cmd.extend(["--papers-dir", args.prep_papers_dir])
    if args.prep_questions_yml:
        cmd.extend(["--questions-yml", args.prep_questions_yml])
    if args.prep_output:
        cmd.extend(["--output", args.prep_output])
    return cmd


def build_deepeval_args(args):
    """Build arguments for deepeval_benchmarking.py"""
    cmd = [sys.executable, "deepeval_benchmarking.py"]
    if args.question:
        cmd.extend(["--question", args.question])
    if args.input:
        cmd.extend(["--input", args.input])
    if args.limit:
        cmd.extend(["--limit", str(args.limit)])
    if args.batch_size:
        cmd.extend(["--batch-size", str(args.batch_size)])
    if args.max_retries:
        cmd.extend(["--max-retries", str(args.max_retries)])
    if args.model:
        cmd.extend(["--model", args.model])
    if args.max_context_length:
        cmd.extend(["--max-context-length", str(args.max_context_length)])
    if args.use_retrieval_only:
        cmd.append("--use-retrieval-only")
    if args.list_questions:
        cmd.append("--list-questions")
    return cmd


def build_plot_args(args):
    """Build arguments for plot_metrics_comparison.py"""
    cmd = [sys.executable, "plot_metrics_comparison.py"]
    if args.plot_results_dir:
        cmd.extend(["--results-dir", args.plot_results_dir])
    if args.plot_output_dir:
        cmd.extend(["--output-dir", args.plot_output_dir])
    return cmd


def build_edge_cases_args(args):
    """Build arguments for edge_cases.py"""
    cmd = [sys.executable, "edge_cases.py"]
    if args.num_edge_cases:
        cmd.extend(["--num-cases", str(args.num_edge_cases)])
    if args.edge_results_dir:
        cmd.extend(["--results-dir", args.edge_results_dir])
    if args.edge_output_dir:
        cmd.extend(["--output-dir", args.edge_output_dir])
    if args.edge_openai_api_key:
        cmd.extend(["--openai-api-key", args.edge_openai_api_key])
    if args.edge_model:
        cmd.extend(["--model", args.edge_model])
    if args.generate_summaries_only:
        cmd.append("--generate-summaries-only")
    if args.contextual_only:
        cmd.append("--contextual-only")
    if args.generate_contextual_summaries_only:
        cmd.append("--generate-contextual-summaries-only")
    return cmd


def run_benchmarking_pipeline(args):
    """
    Run the complete benchmarking pipeline.
    """
    print("\n" + "="*60)
    print("METABEEAI LLM BENCHMARKING PIPELINE")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.question:
        print(f"Question Filter: {args.question}")
    print("="*60)
    
    success = True
    llm_benchmarking_dir = Path(__file__).parent
    
    # Step 1: Prepare benchmark data
    if not args.skip_prep:
        cmd = build_prep_args(args)
        if not run_command(cmd, "Prepare benchmark data from GUI reviewer answers", 
                          cwd=str(llm_benchmarking_dir)):
            return False
    else:
        print("\n[SKIP] Skipping benchmark data preparation (--skip-prep)")
    
    # Step 2: Run DeepEval benchmarking
    if not args.skip_evaluation:
        cmd = build_deepeval_args(args)
        if not run_command(cmd, "Run DeepEval benchmarking with all 5 metrics", 
                          cwd=str(llm_benchmarking_dir)):
            return False
    else:
        print("\n[SKIP] Skipping evaluation (--skip-evaluation)")
    
    # Step 3: Create visualizations
    if not args.skip_plotting:
        cmd = build_plot_args(args)
        if not run_command(cmd, "Create metric comparison plots", 
                          cwd=str(llm_benchmarking_dir)):
            success = False  # Continue even if plotting fails
    else:
        print("\n[SKIP] Skipping plotting (--skip-plotting)")
    
    # Step 4: Identify edge cases
    if not args.skip_edge_cases:
        cmd = build_edge_cases_args(args)
        if not run_command(cmd, f"Identify bottom {args.num_edge_cases or 3} edge cases", 
                          cwd=str(llm_benchmarking_dir)):
            success = False  # Continue even if edge cases fail
    else:
        print("\n[SKIP] Skipping edge case analysis (--skip-edge-cases)")
    
    return success


def main():
    parser = argparse.ArgumentParser(
        description="Run complete MetaBeeAI LLM benchmarking pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline (all steps)
  python run_benchmarking.py
  
  # Run for specific question only
  python run_benchmarking.py --question bee_species
  
  # Skip data preparation (if already done)
  python run_benchmarking.py --skip-prep
  
  # Run only evaluation and plotting
  python run_benchmarking.py --skip-prep --skip-edge-cases
        """
    )
    
    # Step control flags
    parser.add_argument(
        '--skip-prep',
        action='store_true',
        help='Skip benchmark data preparation step'
    )
    
    parser.add_argument(
        '--skip-evaluation',
        action='store_true',
        help='Skip DeepEval benchmarking step'
    )
    
    parser.add_argument(
        '--skip-plotting',
        action='store_true',
        help='Skip plotting step'
    )
    
    parser.add_argument(
        '--skip-edge-cases',
        action='store_true',
        help='Skip edge case analysis step'
    )
    
    # prep_benchmark_data.py arguments
    parser.add_argument(
        '--prep-papers-dir',
        type=str,
        default=None,
        help='[prep] Base directory containing paper folders'
    )
    
    parser.add_argument(
        '--prep-questions-yml',
        type=str,
        default=None,
        help='[prep] Path to questions.yml file'
    )
    
    parser.add_argument(
        '--prep-output',
        type=str,
        default=None,
        help='[prep] Output file path for benchmark data'
    )
    
    # deepeval_benchmarking.py arguments
    parser.add_argument(
        '--question', '-q',
        type=str,
        default=None,
        help='[eval] Question key to filter by'
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        default=None,
        help='[eval] Input benchmark data file'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='[eval] Maximum number of test cases to process'
    )
    
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=None,
        help='[eval] Number of test cases to process per batch'
    )
    
    parser.add_argument(
        '--max-retries', '-r',
        type=int,
        default=None,
        help='[eval] Maximum retries per batch'
    )
    
    parser.add_argument(
        '--model', '-m',
        type=str,
        default=None,
        help='[eval] OpenAI model to use for evaluation'
    )
    
    parser.add_argument(
        '--max-context-length',
        type=int,
        default=None,
        help='[eval] Maximum context length in characters'
    )
    
    parser.add_argument(
        '--use-retrieval-only',
        action='store_true',
        help='[eval] Use only retrieval_context instead of full context'
    )
    
    parser.add_argument(
        '--list-questions',
        action='store_true',
        help='[eval] List all available question keys and exit'
    )
    
    # plot_metrics_comparison.py arguments
    parser.add_argument(
        '--plot-results-dir',
        type=str,
        default=None,
        help='[plot] Directory containing evaluation results'
    )
    
    parser.add_argument(
        '--plot-output-dir',
        type=str,
        default=None,
        help='[plot] Output directory for plots'
    )
    
    # edge_cases.py arguments
    parser.add_argument(
        '--num-edge-cases', '-n',
        type=int,
        default=3,
        help='[edge] Number of edge cases to identify per question (default: 3)'
    )
    
    parser.add_argument(
        '--edge-results-dir',
        type=str,
        default=None,
        help='[edge] Directory containing evaluation results'
    )
    
    parser.add_argument(
        '--edge-output-dir',
        type=str,
        default=None,
        help='[edge] Output directory for edge cases'
    )
    
    parser.add_argument(
        '--edge-openai-api-key',
        type=str,
        default=None,
        help='[edge] OpenAI API key for LLM summarization'
    )
    
    parser.add_argument(
        '--edge-model',
        type=str,
        default=None,
        help='[edge] OpenAI model to use for summarization'
    )
    
    parser.add_argument(
        '--generate-summaries-only',
        action='store_true',
        help='[edge] Only generate LLM summaries for existing edge case files'
    )
    
    parser.add_argument(
        '--contextual-only',
        action='store_true',
        help='[edge] Only run contextual measures analysis'
    )
    
    parser.add_argument(
        '--generate-contextual-summaries-only',
        action='store_true',
        help='[edge] Only generate contextual LLM summaries'
    )
    
    args = parser.parse_args()
    
    # Run the pipeline
    success = run_benchmarking_pipeline(args)
    
    # Final summary
    print("\n" + "="*60)
    if success:
        print("[SUCCESS] BENCHMARKING PIPELINE COMPLETED SUCCESSFULLY")
    else:
        print("[WARNING] BENCHMARKING PIPELINE COMPLETED WITH WARNINGS")
    print("="*60)
    
    data_dir = get_data_dir()
    print(f"\nOutput locations:")
    print(f"  - Benchmark data: {os.path.join(data_dir, 'benchmark_data_gui.json')}")
    print(f"  - Evaluation results: {os.path.join(data_dir, 'deepeval_results')}/")
    print(f"  - Plots: {os.path.join(data_dir, 'deepeval_results', 'plots')}/")
    print(f"  - Edge cases: {os.path.join(data_dir, 'edge_cases')}/")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
