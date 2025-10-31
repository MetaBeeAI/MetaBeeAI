#!/usr/bin/env python3
"""
Main benchmarking runner for MetaBeeAI LLM evaluation.
Orchestrates the complete benchmarking workflow for different comparison types:
- llmv1: LLM v1 vs Reviewer 1 (original baseline)
- llmv2: LLM v2 vs Reviewer 3 (improved version)
- rev: Reviewer 1 vs Reviewer 2 (inter-reviewer agreement)

Usage:
    python run_benchmarking.py --type llmv1
    python run_benchmarking.py --type llmv2 --question bee_species
    python run_benchmarking.py --type rev --skip-dataset
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

def run_command(cmd, description):
    """Run a command and handle errors."""
    print("\n" + "="*60)
    print(f"STEP: {description}")
    print("="*60)
    print(f"Running: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error in {description}: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ Error: Could not find required script")
        return False

def run_llmv1_benchmarking(question=None, skip_dataset=False, skip_geval=False):
    """Run LLM v1 vs Reviewer 1 benchmarking."""
    print("\n" + "🔬 "*20)
    print("LLM V1 VS REVIEWER 1 BENCHMARKING PIPELINE")
    print("🔬 "*20)
    
    # Step 1: Generate test dataset (if not skipped)
    if not skip_dataset:
        if not run_command(
            ["python", "test_dataset_generation.py"],
            "Generate LLM v1 vs Reviewer 1 test dataset"
        ):
            return False
    else:
        print("\n⏭️  Skipping dataset generation (--skip-dataset)")
    
    # Step 2: Run standard DeepEval benchmarking
    cmd = ["python", "deepeval_benchmarking.py"]
    if question:
        cmd.extend(["--question", question])
    
    if not run_command(cmd, "Run DeepEval standard metrics evaluation"):
        return False
    
    # Step 3: Run GEval benchmarking (if not skipped)
    if not skip_geval:
        cmd = ["python", "deepeval_GEval.py"]
        if question:
            cmd.extend(["--question", question])
        
        if not run_command(cmd, "Run DeepEval GEval metrics evaluation"):
            return False
    else:
        print("\n⏭️  Skipping GEval evaluation (--skip-geval)")
    
    print("\n" + "✓"*60)
    print("LLM V1 BENCHMARKING COMPLETED")
    print("✓"*60)
    return True

def run_llmv2_benchmarking(question=None, skip_dataset=False):
    """Run LLM v2 vs Reviewer 3 benchmarking."""
    print("\n" + "🔬 "*20)
    print("LLM V2 VS REVIEWER 3 BENCHMARKING PIPELINE")
    print("🔬 "*20)
    
    # Step 1: Merge LLM v2 data (if not skipped)
    if not skip_dataset:
        if not run_command(
            ["python", "merge_llm_v2.py"],
            "Merge LLM v2 answers with reviewer data"
        ):
            return False
    else:
        print("\n⏭️  Skipping dataset generation (--skip-dataset)")
    
    # Step 2: Run LLM v2 evaluation
    cmd = ["python", "deepeval_llmv2.py"]
    if question:
        cmd.extend(["--question", question])
    
    if not run_command(cmd, "Run LLM v2 vs Reviewer 3 evaluation"):
        return False
    
    print("\n" + "✓"*60)
    print("LLM V2 BENCHMARKING COMPLETED")
    print("✓"*60)
    return True

def run_reviewer_benchmarking(question=None, skip_dataset=False, faithfulness_only=False):
    """Run Reviewer vs Reviewer benchmarking."""
    print("\n" + "🔬 "*20)
    print("REVIEWER VS REVIEWER BENCHMARKING PIPELINE")
    print("🔬 "*20)
    
    # Step 1: Generate reviewer comparison dataset (if not skipped)
    if not skip_dataset:
        if not run_command(
            ["python", "reviewer_dataset_generation.py"],
            "Generate Reviewer vs Reviewer test dataset"
        ):
            return False
    else:
        print("\n⏭️  Skipping dataset generation (--skip-dataset)")
    
    # Step 2: Run reviewer comparison evaluation
    cmd = ["python", "deepeval_reviewers.py"]
    if question:
        cmd.extend(["--question", question])
    if faithfulness_only:
        cmd.extend(["--faithfulness-only", "--add-context"])
    
    if not run_command(cmd, "Run Reviewer vs Reviewer evaluation"):
        return False
    
    print("\n" + "✓"*60)
    print("REVIEWER BENCHMARKING COMPLETED")
    print("✓"*60)
    return True

def run_analysis(comparison_type=None):
    """Run comprehensive analysis and visualization."""
    print("\n" + "📊 "*20)
    print("ANALYSIS AND VISUALIZATION")
    print("📊 "*20)
    
    # Step 1: Generate comprehensive summary
    if not run_command(
        ["python", "analyze_deepeval_results_improved.py"],
        "Generate comprehensive summary CSV"
    ):
        return False
    
    # Step 2: Create merged data and plots
    if not run_command(
        ["python", "deepeval_results_analysis.py"],
        "Create merged data and individual metric plots"
    ):
        return False
    
    # Step 3: Create comparison plots
    if not run_command(
        ["python", "create_comparison_plots.py"],
        "Create comparison plots across metrics"
    ):
        return False
    
    print("\n" + "✓"*60)
    print("ANALYSIS COMPLETED")
    print("✓"*60)
    print("\nOutput locations:")
    print("  - Summary CSV: deepeval-results/summary_all_results_improved.csv")
    print("  - Merged data: deepeval-analyses/merged-data/")
    print("  - Plots: deepeval-analyses/ and comparison_plots/")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Run MetaBeeAI LLM benchmarking pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run LLM v1 benchmarking (all questions)
  python run_benchmarking.py --type llmv1
  
  # Run LLM v2 benchmarking for specific question
  python run_benchmarking.py --type llmv2 --question bee_species
  
  # Run reviewer comparison benchmarking
  python run_benchmarking.py --type rev
  
  # Run all benchmarking types
  python run_benchmarking.py --type all
  
  # Skip dataset generation (if already done)
  python run_benchmarking.py --type llmv1 --skip-dataset
  
  # Run only analysis (after benchmarking is done)
  python run_benchmarking.py --analyze-only
        """
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=['llmv1', 'llmv2', 'rev', 'all'],
        help='Type of benchmarking to run'
    )
    
    parser.add_argument(
        '--question', '-q',
        choices=['bee_species', 'pesticides', 'additional_stressors', 
                'experimental_methodology', 'significance', 'future_research'],
        help='Specific question type to evaluate (default: all questions)'
    )
    
    parser.add_argument(
        '--skip-dataset',
        action='store_true',
        help='Skip dataset generation step (use existing datasets)'
    )
    
    parser.add_argument(
        '--skip-geval',
        action='store_true',
        help='Skip GEval evaluation (only for llmv1)'
    )
    
    parser.add_argument(
        '--faithfulness-only',
        action='store_true',
        help='Run only faithfulness metric (only for rev type)'
    )
    
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only run analysis and visualization (skip benchmarking)'
    )
    
    parser.add_argument(
        '--no-analysis',
        action='store_true',
        help='Skip analysis step after benchmarking'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.analyze_only and not args.type:
        parser.error("--type is required unless using --analyze-only")
    
    # Print header
    print("\n" + "="*60)
    print("METABEEAI LLM BENCHMARKING PIPELINE")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.type:
        print(f"Benchmarking Type: {args.type.upper()}")
    if args.question:
        print(f"Question Filter: {args.question}")
    print("="*60)
    
    # Run analysis only if requested
    if args.analyze_only:
        success = run_analysis()
        sys.exit(0 if success else 1)
    
    # Run selected benchmarking type(s)
    success = True
    
    if args.type == 'llmv1' or args.type == 'all':
        success = run_llmv1_benchmarking(
            question=args.question,
            skip_dataset=args.skip_dataset,
            skip_geval=args.skip_geval
        ) and success
    
    if args.type == 'llmv2' or args.type == 'all':
        success = run_llmv2_benchmarking(
            question=args.question,
            skip_dataset=args.skip_dataset
        ) and success
    
    if args.type == 'rev' or args.type == 'all':
        success = run_reviewer_benchmarking(
            question=args.question,
            skip_dataset=args.skip_dataset,
            faithfulness_only=args.faithfulness_only
        ) and success
    
    if not success:
        print("\n" + "✗"*60)
        print("BENCHMARKING FAILED")
        print("✗"*60)
        sys.exit(1)
    
    # Run analysis unless skipped
    if not args.no_analysis:
        print("\n\nProceeding to analysis phase...")
        success = run_analysis(comparison_type=args.type) and success
    else:
        print("\n⏭️  Skipping analysis (--no-analysis)")
    
    # Final summary
    print("\n" + "="*60)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("="*60)
    
    if args.type == 'all':
        print("\nCompleted all benchmarking types:")
        print("  ✓ LLM v1 vs Reviewer 1")
        print("  ✓ LLM v2 vs Reviewer 3")
        print("  ✓ Reviewer 1 vs Reviewer 2")
    else:
        print(f"\nCompleted {args.type.upper()} benchmarking")
    
    if not args.no_analysis:
        print("\n✓ Analysis and visualization completed")
        print("\nNext steps:")
        print("  1. Review summary CSV: deepeval-results/summary_all_results_improved.csv")
        print("  2. Check plots in: deepeval-analyses/ and comparison_plots/")
        print("  3. Review detailed results in: deepeval-results/")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

