#!/usr/bin/env python3
"""
Plot comparison of metrics across question types.

This script creates visualization showing mean and standard deviation
of all 5 metrics (Faithfulness, Contextual Precision, Contextual Recall,
Completeness, Accuracy) across the 3 question types.
"""

import json
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
import argparse


def load_results(results_dir):
    """Load all benchmark results from JSON files."""
    results_dir = Path(results_dir)
    all_data = []
    
    json_files = list(results_dir.glob("combined_results_*.json"))
    
    if not json_files:
        print(f"❌ No combined_results_*.json files found in {results_dir}")
        return []
    
    print(f"📂 Loading {len(json_files)} result files...")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                    print(f"  ✓ Loaded {len(data)} entries from {file_path.name}")
        except Exception as e:
            print(f"  ⚠️  Error loading {file_path.name}: {e}")
    
    return all_data


def organize_metrics_by_question(data):
    """
    Organize metric scores by question type and metric name.
    
    Returns:
        Dict[metric_name][question_key] = list of scores
    """
    # Structure: metrics[metric_name][question_key] = [scores]
    metrics = defaultdict(lambda: defaultdict(list))
    
    for entry in data:
        question_key = entry.get("question_key")
        metrics_data = entry.get("metrics_data", [])
        
        if not question_key:
            continue
        
        for metric in metrics_data:
            metric_name = metric.get("name")
            metric_score = metric.get("score")
            
            if metric_name and metric_score is not None:
                metrics[metric_name][question_key].append(metric_score)
    
    return metrics


def calculate_stats(scores):
    """Calculate mean and standard deviation from scores."""
    if not scores:
        return 0.0, 0.0
    return np.mean(scores), np.std(scores)


def create_comparison_plot(metrics_data, output_path):
    """
    Create a figure with 5 subplots (one per metric) comparing 3 questions.
    
    Args:
        metrics_data: Dictionary with metric scores organized by question
        output_path: Path to save the figure
    """
    # Define the 5 metrics in order
    metric_names = [
        "Faithfulness",
        "Contextual Precision",
        "Contextual Recall",
        "Completeness [GEval]",
        "Accuracy [GEval]"
    ]
    
    # Question types in order
    question_types = ["design", "population", "welfare"]
    question_labels = ["Design", "Population", "Welfare"]
    
    # Create figure with 5 subplots
    fig, axes = plt.subplots(1, 5, figsize=(20, 4))
    fig.suptitle('Metric Performance Across Question Types', fontsize=16, fontweight='bold', y=1.02)
    
    colors = ['#2E86AB', '#A23B72', '#F18F01']  # Blue, Purple, Orange
    
    for idx, metric_name in enumerate(metric_names):
        ax = axes[idx]
        
        # Get data for this metric
        means = []
        stds = []
        
        for question_key in question_types:
            scores = metrics_data[metric_name].get(question_key, [])
            mean_val, std_val = calculate_stats(scores)
            means.append(mean_val)
            stds.append(std_val)
        
        # Create bar plot with error bars
        x_pos = np.arange(len(question_types))
        bars = ax.bar(x_pos, means, yerr=stds, capsize=5, 
                      color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        
        # Customize subplot
        ax.set_xlabel('Question Type', fontsize=10, fontweight='bold')
        ax.set_ylabel('Score', fontsize=10, fontweight='bold')
        ax.set_title(metric_name, fontsize=11, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(question_labels, rotation=0)
        ax.set_ylim(0, 1.1)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add value labels on bars
        for i, (bar, mean, std) in enumerate(zip(bars, means, stds)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + std + 0.02,
                   f'{mean:.2f}',
                   ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"📊 Plot saved to: {output_path}")
    
    return fig


def print_statistics_table(metrics_data):
    """Print a formatted table of statistics."""
    metric_names = [
        "Faithfulness",
        "Contextual Precision",
        "Contextual Recall",
        "Completeness [GEval]",
        "Accuracy [GEval]"
    ]
    
    question_types = ["design", "population", "welfare"]
    
    print("\n" + "="*80)
    print("📊 STATISTICS SUMMARY")
    print("="*80)
    
    for metric_name in metric_names:
        print(f"\n{metric_name}:")
        print("-" * 60)
        print(f"{'Question':<15} {'Mean':<10} {'Std Dev':<10} {'N':<5}")
        print("-" * 60)
        
        for question_key in question_types:
            scores = metrics_data[metric_name].get(question_key, [])
            if scores:
                mean_val, std_val = calculate_stats(scores)
                print(f"{question_key.capitalize():<15} {mean_val:<10.3f} {std_val:<10.3f} {len(scores):<5}")
            else:
                print(f"{question_key.capitalize():<15} {'N/A':<10} {'N/A':<10} {0:<5}")
    
    print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Plot metrics comparison across question types'
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        default='llm_benchmarking/deepeval_results',
        help='Directory containing evaluation results (default: llm_benchmarking/deepeval_results)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='llm_benchmarking/deepeval_results/plots/metrics_comparison.png',
        help='Output file path (default: llm_benchmarking/deepeval_results/plots/metrics_comparison.png)'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("📊 METRICS COMPARISON ACROSS QUESTION TYPES")
    print("="*80)
    
    # Load results
    data = load_results(args.results_dir)
    
    if not data:
        print("❌ No data loaded. Exiting.")
        return
    
    print(f"\n✓ Total entries loaded: {len(data)}")
    
    # Organize metrics by question
    metrics_data = organize_metrics_by_question(data)
    
    # Print statistics table
    print_statistics_table(metrics_data)
    
    # Create visualization
    print("\n📊 Creating visualization...")
    create_comparison_plot(metrics_data, args.output)
    
    print("\n" + "="*80)
    print("✅ Analysis complete!")
    print(f"📊 Plot saved to: {args.output}")
    print("="*80)


if __name__ == "__main__":
    main()

