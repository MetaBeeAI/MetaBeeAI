#!/usr/bin/env python3
"""
Plot comparison of metrics across question types.

This script creates visualization showing mean and standard error
of all 5 metrics (Faithfulness, Contextual Precision, Contextual Recall,
Completeness, Accuracy) across the question types.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Add parent directory to path to access config
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from config import get_data_dir


def load_results(results_dir):
    """Load all benchmark results from JSON files."""
    results_dir = Path(results_dir)
    all_data = []

    json_files = list(results_dir.glob("combined_results_*.json"))

    if not json_files:
        print(f"No combined_results_*.json files found in {results_dir}")
        return []

    print(f"Loading {len(json_files)} result files...")

    for file_path in json_files:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                    print(f"  [OK] Loaded {len(data)} entries from {file_path.name}")
        except Exception as e:
            print(f"  [WARNING] Error loading {file_path.name}: {e}")

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
    """Calculate mean, standard deviation, and standard error from scores."""
    if not scores:
        return 0.0, 0.0, 0.0
    mean = np.mean(scores)
    std = np.std(scores)
    # Standard error = standard deviation / sqrt(n)
    sem = std / np.sqrt(len(scores)) if len(scores) > 0 else 0.0
    return mean, std, sem


def create_individual_metric_plots(metrics_data, output_dir, question_types):
    """
    Create separate bar chart plots for each metric showing mean and standard error.

    Args:
        metrics_data: Dictionary with metric scores organized by question
        output_dir: Directory to save plots
        question_types: List of question keys found in data
    """
    # Define the 5 metrics in order
    metric_names = ["Faithfulness", "Contextual Precision", "Contextual Recall", "Completeness [GEval]", "Accuracy [GEval]"]

    # Generate colors for questions
    colors = plt.cm.Set3(np.linspace(0, 1, len(question_types)))

    plots_dir = Path(output_dir) / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    for metric_name in metric_names:
        # Get data for this metric
        means = []
        sems = []
        labels = []

        for question_key in question_types:
            scores = metrics_data[metric_name].get(question_key, [])
            if scores:
                mean_val, _, sem_val = calculate_stats(scores)
                means.append(mean_val)
                sems.append(sem_val)
                labels.append(question_key.replace("_", " ").title())

        if not means:
            print(f"Skipping {metric_name} (no data)")
            continue

        # Create figure for this metric
        fig, ax = plt.subplots(figsize=(8, 6))

        # Create bar plot with error bars (standard error)
        x_pos = np.arange(len(labels))
        bars = ax.bar(
            x_pos, means, yerr=sems, capsize=8, color=colors[: len(labels)], alpha=0.7, edgecolor="black", linewidth=1.5
        )

        # Customize plot
        ax.set_xlabel("Question Type", fontsize=12, fontweight="bold")
        ax.set_ylabel("Score", fontsize=12, fontweight="bold")
        ax.set_title(f"{metric_name} - Mean ± Standard Error", fontsize=14, fontweight="bold")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=0, ha="center")
        ax.set_ylim(0, max(1.1, max(means) + max(sems) + 0.1) if means else 1.1)
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        # Add value labels on bars
        for bar, mean, sem in zip(bars, means, sems):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + sem + 0.02,
                f"{mean:.3f}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        plt.tight_layout()

        # Save individual plot
        safe_filename = metric_name.replace(" ", "_").replace("[", "").replace("]", "").lower()
        output_path = plots_dir / f"{safe_filename}.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"  [OK] Saved {metric_name} plot to {output_path}")

    return plots_dir


def create_summary_plot(metrics_data, output_dir, question_types):
    """
    Create a summary plot showing average per metric across all questions.

    Args:
        metrics_data: Dictionary with metric scores organized by question
        output_dir: Directory to save plot
        question_types: List of question keys found in data
    """
    # Define the 5 metrics in order
    metric_names = ["Faithfulness", "Contextual Precision", "Contextual Recall", "Completeness [GEval]", "Accuracy [GEval]"]

    plots_dir = Path(output_dir) / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    # Calculate overall mean and SEM for each metric across all questions
    metric_means = []
    metric_sems = []

    for metric_name in metric_names:
        all_scores = []
        for question_key in question_types:
            scores = metrics_data[metric_name].get(question_key, [])
            all_scores.extend(scores)

        if all_scores:
            mean_val, _, sem_val = calculate_stats(all_scores)
            metric_means.append(mean_val)
            metric_sems.append(sem_val)
        else:
            metric_means.append(0.0)
            metric_sems.append(0.0)

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Create bar plot with error bars
    x_pos = np.arange(len(metric_names))
    colors = plt.cm.viridis(np.linspace(0, 1, len(metric_names)))

    bars = ax.bar(x_pos, metric_means, yerr=metric_sems, capsize=8, color=colors, alpha=0.7, edgecolor="black", linewidth=1.5)

    # Customize plot
    ax.set_xlabel("Metric", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average Score (across all questions)", fontsize=12, fontweight="bold")
    ax.set_title("Summary: Average Metric Performance Across All Questions", fontsize=14, fontweight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(metric_names, rotation=45, ha="right")
    ax.set_ylim(0, max(1.1, max(metric_means) + max(metric_sems) + 0.1) if metric_means else 1.1)
    ax.grid(axis="y", alpha=0.3, linestyle="--")

    # Add value labels on bars
    for bar, mean, sem in zip(bars, metric_means, metric_sems):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + sem + 0.02,
            f"{mean:.3f}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()

    # Save summary plot
    output_path = plots_dir / "summary_metrics.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved summary plot to {output_path}")

    return output_path


def print_statistics_table(metrics_data, question_types):
    """Print a formatted table of statistics."""
    metric_names = ["Faithfulness", "Contextual Precision", "Contextual Recall", "Completeness [GEval]", "Accuracy [GEval]"]

    print("\n" + "=" * 80)
    print("STATISTICS SUMMARY")
    print("=" * 80)

    for metric_name in metric_names:
        print(f"\n{metric_name}:")
        print("-" * 60)
        print(f"{'Question':<20} {'Mean':<10} {'Std Error':<12} {'N':<5}")
        print("-" * 60)

        for question_key in question_types:
            scores = metrics_data[metric_name].get(question_key, [])
            if scores:
                mean_val, _, sem_val = calculate_stats(scores)
                print(f"{question_key.replace('_', ' ').title():<20} {mean_val:<10.3f} {sem_val:<12.3f} {len(scores):<5}")
            else:
                print(f"{question_key.replace('_', ' ').title():<20} {'N/A':<10} {'N/A':<12} {0:<5}")

        # Print overall average for this metric
        all_scores = []
        for question_key in question_types:
            scores = metrics_data[metric_name].get(question_key, [])
            all_scores.extend(scores)
        if all_scores:
            mean_val, _, sem_val = calculate_stats(all_scores)
            print("-" * 60)
            print(f"{'Overall Average':<20} {mean_val:<10.3f} {sem_val:<12.3f} {len(all_scores):<5}")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Plot metrics comparison across question types")
    parser.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help="Directory containing evaluation results (default: auto-detect from config)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=None, help="Output directory for plots (default: same as results-dir)"
    )

    args = parser.parse_args()

    # Use config-based defaults if not provided
    data_dir = get_data_dir()
    if args.results_dir is None:
        args.results_dir = os.path.join(data_dir, "deepeval_results")
    if args.output_dir is None:
        args.output_dir = args.results_dir  # Save plots in same directory as results

    print("=" * 80)
    print("METRICS COMPARISON ACROSS QUESTION TYPES")
    print("=" * 80)
    print(f"Results directory: {args.results_dir}")
    print(f"Output directory: {args.output_dir}")
    print("=" * 80)

    # Load results
    data = load_results(args.results_dir)

    if not data:
        print("No data loaded. Exiting.")
        return

    print(f"\n[OK] Total entries loaded: {len(data)}")

    # Organize metrics by question
    metrics_data = organize_metrics_by_question(data)

    # Extract unique question types from data
    question_types_set = set()
    for entry in data:
        question_key = entry.get("question_key")
        if question_key:
            question_types_set.add(question_key)
    question_types = sorted(list(question_types_set))

    if not question_types:
        print("No question types found in data. Exiting.")
        return

    print(f"Found question types: {', '.join(question_types)}")

    # Print statistics table
    print_statistics_table(metrics_data, question_types)

    # Create visualizations
    print("Creating visualizations...")

    # Create individual plots for each metric
    print("Creating individual metric plots...")
    create_individual_metric_plots(metrics_data, args.output_dir, question_types)

    # Create summary plot
    print("Creating summary plot...")
    create_summary_plot(metrics_data, args.output_dir, question_types)

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print(f"Plots saved to: {os.path.join(args.output_dir, 'plots')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
