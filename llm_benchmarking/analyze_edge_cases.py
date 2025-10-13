#!/usr/bin/env python3
"""
Simple wrapper for edge case analysis with primate welfare benchmarking data.
Uses the edge_cases.py script with appropriate defaults.
"""

import argparse
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(
        description='Identify edge cases (lowest scoring papers) from benchmarking results'
    )
    parser.add_argument(
        '--num-cases', '-n',
        type=int,
        default=3,
        help='Number of edge cases to identify (default: 3, for bottom 3 papers)'
    )
    parser.add_argument(
        '--question', '-q',
        choices=['design', 'population', 'welfare', 'all'],
        default='all',
        help='Question type to analyze (default: all)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='llm_benchmarking/edge_cases',
        help='Output directory (default: llm_benchmarking/edge_cases)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print(f"🔍 Edge Case Analysis for Primate Welfare Benchmarking")
    print("="*60)
    print(f"📊 Analyzing bottom {args.num_cases} papers")
    print(f"❓ Question type: {args.question}")
    print(f"📁 Output directory: {args.output_dir}")
    print("="*60)
    
    # Build command for edge_cases.py
    cmd = [
        sys.executable,
        "llm_benchmarking/edge_cases.py",
        "--num-cases", str(args.num_cases),
        "--results-dir", "llm_benchmarking/deepeval_results",
        "--output-dir", args.output_dir
    ]
    
    # Run the edge case analysis
    result = subprocess.run(cmd, cwd=".")
    
    if result.returncode == 0:
        print("\n" + "="*60)
        print("✅ Edge case analysis complete!")
        print(f"📁 Check results in: {args.output_dir}/")
        print("="*60)
    else:
        print("\n❌ Edge case analysis failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

