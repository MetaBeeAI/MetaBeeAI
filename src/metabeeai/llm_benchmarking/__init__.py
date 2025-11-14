"""
LLM Benchmarking Module

This module provides tools for generating test datasets and evaluating LLM outputs
using DeepEval for benchmarking purposes.

Main Components:

- Dataset Generation:
  - test_dataset_generation.py: Generates test datasets from reviewer answers
  - reviewer_dataset_generation.py: Generates reviewer comparison datasets
  - merge_answers.py: Merges LLM and reviewer answers for dataset creation

- DeepEval Evaluation:
  - deepeval_benchmarking.py: Traditional DeepEval metrics evaluation
  - deepeval_GEval.py: G-Eval correctness assessment
  - deepeval_reviewers.py: Reviewer comparison evaluation
  - deepeval_results_analysis.py: Results consolidation and visualization

- Analysis:
  - reviewer_rating.py: Analyzes reviewer ratings and generates statistical plots
"""
# TODO: these imports do not exist

# from .merge_answers import merge_answers
# from .reviewer_rating import (
#     calculate_question_stats,
#     calculate_reviewer_agreement,
#     calculate_reviewer_individual_stats,
#     plot_question_ratings,
#     plot_reviewer_agreement,
#     plot_individual_reviewer_ratings
# )

# __all__ = [
#     "merge_answers",
#     "calculate_question_stats",
#     "calculate_reviewer_agreement", 
#     "calculate_reviewer_individual_stats",
#     "plot_question_ratings",
#     "plot_reviewer_agreement",
#     "plot_individual_reviewer_ratings"
# ]