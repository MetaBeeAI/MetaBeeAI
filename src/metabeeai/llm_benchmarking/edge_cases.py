#!/usr/bin/env python3
"""
Edge Case Identification Script for LLM Benchmarking

This script identifies edge cases (low-scoring examples) from DeepEval results
for both LLM and reviewer comparisons across different metrics and question types.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import openai
import pandas as pd

# Add parent directory to path to access config
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from config import get_data_dir

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("[OK] Loaded environment variables from .env file")
except ImportError:
    print("Note: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Or set environment variables manually.")


class EdgeCaseIdentifier:
    """Identifies edge cases from evaluation results."""

    def __init__(
        self,
        results_dir: Optional[str] = None,
        merged_data_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o",
    ):
        """
        Initialize the EdgeCaseIdentifier.

        Args:
            results_dir: Directory containing individual evaluation results (default: get_data_dir()/deepeval_results)
            merged_data_dir: Directory containing merged evaluation results (not used, kept for compatibility)
            output_dir: Directory to save edge case results (default: get_data_dir()/edge_cases)
            openai_api_key: OpenAI API key for LLM summarization
            model: OpenAI model to use for summarization
        """
        # Use config-based defaults if not provided
        data_dir = get_data_dir()
        if results_dir is None:
            results_dir = os.path.join(data_dir, "deepeval_results")
        if output_dir is None:
            output_dir = os.path.join(data_dir, "edge_cases")

        self.results_dir = Path(results_dir)
        self.merged_data_dir = Path(merged_data_dir) if merged_data_dir else None
        self.output_dir = Path(output_dir)
        self.model = model

        # Set up OpenAI client if API key is provided
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
            print(f"OpenAI client initialized with provided API key. Model: {self.model}")
        else:
            # Try to get from environment variable
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                if api_key.strip() and api_key != "your_openai_api_key_here":
                    openai.api_key = api_key
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    print(f"OpenAI client initialized with environment variable. Model: {self.model}")
                else:
                    self.openai_client = None
                    print("Warning: OPENAI_API_KEY in .env file appears to be a placeholder. Please set a valid API key.")
            else:
                self.openai_client = None
                print("Warning: No OpenAI API key found in environment variables. LLM summarization will be skipped.")
                print("Make sure you have a .env file with OPENAI_API_KEY=your_actual_key")

        # Test API connection if client is available
        if self.openai_client:
            self.test_api_connection()

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)

        # Question types - will be extracted dynamically from data if available
        # Default empty list, will be populated when loading data
        self.question_types = []

        # Metrics we're looking for (matches deepeval_benchmarking.py)
        self.metrics = ["Completeness [GEval]", "Accuracy [GEval]", "Faithfulness", "Contextual Precision", "Contextual Recall"]

        # Data sources (primate welfare: all data in one set)
        self.data_sources = ["combined"]

    def test_api_connection(self):
        """Test the OpenAI API connection with a simple call."""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": "Hello, this is a test."}], max_tokens=10
            )
            print(f"[OK] OpenAI API connection successful. Model: {self.model}")
        except Exception as e:
            print(f"[ERROR] OpenAI API connection failed: {e}")
            self.openai_client = None

    def load_merged_data(self, source: str) -> List[Dict]:
        """
        Load data from individual result files in results_dir.
        For primate welfare project, source is ignored - we just load from combined_results_*.json files.
        """
        all_data = []

        # Look for combined_results_*.json files in results_dir
        if not self.results_dir.exists():
            print(f"Warning: {self.results_dir} not found")
            return []

        json_files = list(self.results_dir.glob("combined_results_*.json"))

        if not json_files:
            print(f"Warning: No combined_results_*.json files found in {self.results_dir}")
            return []

        print(f"  Found {len(json_files)} result files to process")

        for file_path in json_files:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                        print(f"    Loaded {len(data)} entries from {file_path.name}")
            except Exception as e:
                print(f"  Error loading {file_path.name}: {e}")

        # Extract unique question types from loaded data
        if all_data and not self.question_types:
            question_types_set = set()
            for entry in all_data:
                question_key = entry.get("question_key")
                if question_key:
                    question_types_set.add(question_key)
            self.question_types = sorted(list(question_types_set))
            if self.question_types:
                print(f"  Extracted question types from data: {', '.join(self.question_types)}")

        return all_data

    def get_metric_score(self, metrics_data: List[Dict], metric_name: str) -> Optional[float]:
        """Extract score for a specific metric from metrics_data."""
        for metric in metrics_data:
            if metric.get("name") == metric_name:
                return metric.get("score")
        return None

    def get_metric_reason(self, metrics_data: List[Dict], metric_name: str) -> Optional[str]:
        """Extract reason for a specific metric from metrics_data."""
        for metric in metrics_data:
            if metric.get("name") == metric_name:
                return metric.get("reason")
        return None

    def calculate_combined_score(self, metrics_data: List[Dict]) -> Tuple[float, Dict[str, float], Dict[str, str]]:
        """
        Calculate a combined score across all metrics for a test case.

        Args:
            metrics_data: List of metric data for a test case

        Returns:
            Tuple of (combined_score, individual_scores_dict, individual_reasons_dict)
        """
        individual_scores = {}
        individual_reasons = {}
        available_metrics = 0
        total_score = 0.0

        for metric in self.metrics:
            score = self.get_metric_score(metrics_data, metric)
            if score is not None:
                individual_scores[metric] = score
                total_score += score
                available_metrics += 1

                # Get the reason for this metric
                reason = self.get_metric_reason(metrics_data, metric)
                if reason:
                    individual_reasons[metric] = reason

        # Calculate average score if metrics are available
        combined_score = total_score / available_metrics if available_metrics > 0 else 0.0

        return combined_score, individual_scores, individual_reasons

    def summarize_reasons_with_llm(self, edge_cases: List[Dict], question_type: str) -> Optional[str]:
        """
        Use LLM to summarize the reasons across edge cases for a specific question type.

        Args:
            edge_cases: List of edge cases for a question type
            question_type: Type of question being summarized

        Returns:
            LLM-generated summary of reasons, or None if LLM is not available
        """
        if not self.openai_client:
            return None

        if not edge_cases:
            return "No edge cases found for this question type."

        # Extract all reasons from the edge cases
        all_reasons = []
        for case in edge_cases:
            for metric, reason in case["individual_reasons"].items():
                if reason and reason != "No reason provided":
                    # Handle both regular and contextual edge cases
                    combined_score = case.get("combined_score") or case.get("contextual_combined_score", 0)
                    all_reasons.append(
                        {
                            "metric": metric,
                            "reason": reason,
                            "score": case["individual_scores"].get(metric, 0),
                            "combined_score": combined_score,
                        }
                    )

        if not all_reasons:
            return "No detailed reasons found in the edge cases."

        # Create a focused prompt for analyzing the reasons
        prompt = f"""Analyze the evaluation reasons for {len(edge_cases)} low-scoring edge cases for the question type: "{question_type}".

I've extracted {len(all_reasons)} evaluation reasons from these cases. Please provide a CONCISE summary with exactly TWO sections:

**Section 1: Main Issues (max 3 primary issues)**
- Identify the 3 most critical problems causing low scores
- Be specific but brief (1-2 sentences per issue)

**Section 2: Recommendations for Improving Prompt**
- Provide 2-3 actionable suggestions for prompt engineering
- Focus on how to get better responses for this question type

Keep the entire summary under 200 words. Be direct and actionable.

Here are the evaluation reasons to analyze:

"""

        # Add the reasons in a more focused format
        for i, reason_data in enumerate(all_reasons, 1):
            prompt += f"{i}. {reason_data['metric']}: {reason_data['reason']}\n"

        prompt += "\nProvide a concise summary with exactly the two sections requested."

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert analyst specializing in evaluating LLM responses. Provide concise, structured summaries with exactly the requested format. Be brief and actionable.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.1,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return f"Error generating summary: {e}"

    def identify_edge_cases(self, data: List[Dict], question_type: str, num_cases: int = 20) -> List[Dict]:
        """
        Identify edge cases for a specific question type using combined scores across all metrics.

        Args:
            data: List of evaluation results
            question_type: Type of question to filter by
            num_cases: Number of edge cases to return

        Returns:
            List of edge cases sorted by combined score (lowest first)
        """
        edge_cases = []

        for item in data:
            # Check if this item matches the question type
            # Try both question_key (new format) and question_id (old format)
            question_key = item.get("question_key") or item.get("additional_metadata", {}).get("question_id")
            if question_key != question_type:
                continue

            metadata = item.get("additional_metadata", {})

            # Calculate combined score across all metrics
            combined_score, individual_scores, individual_reasons = self.calculate_combined_score(item.get("metrics_data", []))

            # Skip if no metrics were available
            if not individual_scores:
                continue

            # Create edge case entry
            edge_case = {
                "test_case_index": item.get("test_case_index"),
                "name": item.get("name"),
                "input": item.get("input"),
                "actual_output": item.get("actual_output"),
                "expected_output": item.get("expected_output"),
                "combined_score": combined_score,
                "individual_scores": individual_scores,
                "individual_reasons": individual_reasons,
                "question_type": question_type,
                "paper_id": metadata.get("paper_id"),
                "success": item.get("success"),
                "additional_metadata": metadata,
            }

            edge_cases.append(edge_case)

        # Sort by combined score (lowest first) and return top N cases
        edge_cases.sort(key=lambda x: x["combined_score"])
        return edge_cases[:num_cases]

    def identify_contextual_edge_cases(self, data: List[Dict], question_type: str, num_cases: int = 20) -> List[Dict]:
        """
        Identify edge cases for a specific question type using only contextual measures
        (contextual precision, contextual recall, faithfulness) for LLM data.

        Args:
            data: List of evaluation results
            question_type: Type of question to filter by
            num_cases: Number of edge cases to return

        Returns:
            List of edge cases sorted by contextual combined score (lowest first)
        """
        edge_cases = []

        # Define contextual metrics
        contextual_metrics = ["Faithfulness", "Contextual Precision", "Contextual Recall"]

        for item in data:
            # Check if this item matches the question type
            # Try both question_key (new format) and question_id (old format)
            question_key = item.get("question_key") or item.get("additional_metadata", {}).get("question_id")
            if question_key != question_type:
                continue

            metadata = item.get("additional_metadata", {})

            # Calculate combined score across only contextual metrics
            individual_scores = {}
            individual_reasons = {}
            available_metrics = 0
            total_score = 0.0

            for metric in contextual_metrics:
                score = self.get_metric_score(item.get("metrics_data", []), metric)
                if score is not None:
                    individual_scores[metric] = score
                    total_score += score
                    available_metrics += 1

                    # Get the reason for this metric
                    reason = self.get_metric_reason(item.get("metrics_data", []), metric)
                    if reason:
                        individual_reasons[metric] = reason

            # Skip if no contextual metrics were available
            if not individual_scores:
                continue

            # Calculate average contextual score
            contextual_combined_score = total_score / available_metrics if available_metrics > 0 else 0.0

            # Create edge case entry
            edge_case = {
                "test_case_index": item.get("test_case_index"),
                "name": item.get("name"),
                "input": item.get("input"),
                "actual_output": item.get("actual_output"),
                "expected_output": item.get("expected_output"),
                "contextual_combined_score": contextual_combined_score,
                "individual_scores": individual_scores,
                "individual_reasons": individual_reasons,
                "question_type": question_type,
                "paper_id": metadata.get("paper_id"),
                "success": item.get("success"),
                "additional_metadata": metadata,
            }

            edge_cases.append(edge_case)

        # Sort by contextual combined score (lowest first) and return top N cases
        edge_cases.sort(key=lambda x: x["contextual_combined_score"])
        return edge_cases[:num_cases]

    def process_contextual_source(self, source: str, num_cases: int = 20) -> Dict[str, List[Dict]]:
        """
        Process contextual edge cases for LLM data only.

        Args:
            source: Data source (should be "llm" for contextual analysis)
            num_cases: Number of edge cases per question type

        Returns:
            Dictionary of contextual edge cases organized by question type
        """
        if source != "llm":
            print(f"Contextual analysis is only available for LLM data, not {source}")
            return {}

        print(f"Processing contextual measures for {source} data...")

        # Load data
        data = self.load_merged_data(source)
        if not data:
            print(f"No data found for {source}")
            return {}

        # Organize contextual edge cases by question type
        contextual_edge_cases_by_question = {}

        for question_type in self.question_types:
            print(f"  Finding contextual edge cases for {question_type}")
            contextual_edge_cases = self.identify_contextual_edge_cases(data, question_type, num_cases)
            contextual_edge_cases_by_question[question_type] = contextual_edge_cases

        return contextual_edge_cases_by_question

    def save_contextual_edge_cases(self, source: str, contextual_edge_cases_by_question: Dict[str, List[Dict]]):
        """Save contextual edge cases to files organized by source and question type."""
        source_dir = self.output_dir / source
        source_dir.mkdir(exist_ok=True)

        for question_type, cases in contextual_edge_cases_by_question.items():
            if not cases:
                continue

            # Create filename for contextual measures
            filename = f"{source}_{question_type}_contextual.json"
            filepath = source_dir / filename

            # Save contextual edge cases
            with open(filepath, "w") as f:
                json.dump(cases, f, indent=2)

            print(f"  Saved {len(cases)} contextual edge cases to {filepath}")

    def generate_contextual_source_summary_report(self, source: str, contextual_edge_cases_by_question: Dict[str, List[Dict]]):
        """
        Generate a summary report for contextual measures of a specific source with LLM-powered reason summarization.

        Args:
            source: Data source (should be "llm" for contextual analysis)
            contextual_edge_cases_by_question: Dictionary of contextual edge cases organized by question type
        """
        if source != "llm":
            print(f"Contextual summary report is only available for LLM data, not {source}")
            return None

        source_dir = self.output_dir / source
        source_dir.mkdir(exist_ok=True)

        summary_report = {
            "source": source,
            "analysis_type": "contextual_measures",
            "measures_analyzed": ["Faithfulness", "Contextual Precision", "Contextual Recall"],
            "generated_at": str(pd.Timestamp.now()),
            "total_edge_cases": 0,
            "question_type_summaries": {},
            "overall_statistics": {},
        }

        total_cases = 0
        all_scores = []

        # Generate summaries for each question type
        for question_type, cases in contextual_edge_cases_by_question.items():
            if not cases:
                continue

            total_cases += len(cases)

            # Collect scores for statistics
            question_scores = [case["contextual_combined_score"] for case in cases]
            all_scores.extend(question_scores)

            # Generate LLM summary of reasons
            print(f"    Generating LLM summary for contextual measures - {question_type}...")
            llm_summary = self.summarize_reasons_with_llm(cases, question_type)

            summary_report["question_type_summaries"][question_type] = {
                "num_cases": len(cases),
                "score_range": {
                    "min": min(question_scores),
                    "max": max(question_scores),
                    "mean": sum(question_scores) / len(question_scores),
                },
                "llm_summary": llm_summary,
                "sample_cases": [
                    {
                        "name": case["name"],
                        "contextual_combined_score": case["contextual_combined_score"],
                        "paper_id": case.get("paper_id"),
                        "input": case["input"][:100] + "..." if len(case["input"]) > 100 else case["input"],
                        "expected_output": case["expected_output"][:150] + "..."
                        if len(case["expected_output"]) > 150
                        else case["expected_output"],
                        "actual_output": case["actual_output"][:150] + "..."
                        if len(case["actual_output"]) > 150
                        else case["actual_output"],
                    }
                    for case in cases[:3]  # Include first 3 cases as samples
                ],
            }

        # Overall statistics
        if all_scores:
            summary_report["overall_statistics"] = {
                "total_cases": total_cases,
                "score_range": {"min": min(all_scores), "max": max(all_scores), "mean": sum(all_scores) / len(all_scores)},
            }

        summary_report["total_edge_cases"] = total_cases

        # Save the contextual summary report
        summary_path = source_dir / "summary-report-context.json"
        with open(summary_path, "w") as f:
            json.dump(summary_report, f, indent=2)

        print(f"  Generated contextual summary report: {summary_path}")
        return summary_report

    def generate_contextual_markdown_report(self, contextual_edge_cases: Dict[str, List[Dict]]):
        """
        Generate a comprehensive markdown report for contextual measures analysis.

        Args:
            contextual_edge_cases: Dictionary containing contextual edge cases for LLM data
        """
        markdown_path = self.output_dir / "edge-case-report-context.md"

        with open(markdown_path, "w") as f:
            f.write("# Contextual Measures Edge Case Analysis Report\n\n")
            f.write(f"*Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(
                "*This report focuses on Faithfulness, Contextual Precision, and Contextual Recall measures for LLM data only.*\n\n"
            )

            # Overall statistics
            total_cases = sum(len(cases) for cases in contextual_edge_cases.values())
            f.write("## Overview\n\n")
            f.write(f"- **Total Contextual Edge Cases Analyzed**: {total_cases}\n")
            f.write("- **Data Source**: LLM data only\n")
            f.write("- **Measures Analyzed**: Faithfulness, Contextual Precision, Contextual Recall\n")
            f.write(f"- **Question Types**: {', '.join(self.question_types)}\n\n")

            # Try to load the contextual summary report
            summary_path = self.output_dir / "llm" / "summary-report-context.json"
            if summary_path.exists():
                try:
                    with open(summary_path, "r") as summary_file:
                        summary_data = json.load(summary_file)

                    # Overall statistics
                    if "overall_statistics" in summary_data:
                        stats = summary_data["overall_statistics"]
                        f.write("## Overall Statistics\n\n")
                        f.write(f"- **Total Cases**: {stats.get('total_cases', 0)}\n")
                        f.write(
                            f"- **Score Range**: {stats.get('score_range', {}).get('min', 0):.3f} - {stats.get('score_range', {}).get('max', 0):.3f}\n"
                        )
                        f.write(f"- **Average Score**: {stats.get('score_range', {}).get('mean', 0):.3f}\n\n")

                    # Question type summaries
                    if "question_type_summaries" in summary_data:
                        f.write("## Question Type Analysis\n\n")

                        for question_type, q_data in summary_data["question_type_summaries"].items():
                            f.write(f"### {question_type.replace('_', ' ').title()}\n\n")

                            # Basic stats
                            f.write(f"- **Number of Cases**: {q_data.get('num_cases', 0)}\n")
                            score_range = q_data.get("score_range", {})
                            f.write(f"- **Score Range**: {score_range.get('min', 0):.3f} - {score_range.get('max', 0):.3f}\n")
                            f.write(f"- **Average Score**: {score_range.get('mean', 0):.3f}\n\n")

                            # LLM Summary
                            llm_summary = q_data.get("llm_summary")
                            if llm_summary and llm_summary != "No detailed reasons found in the edge cases.":
                                f.write("**LLM Analysis:**\n\n")
                                f.write(f"{llm_summary}\n\n")
                            else:
                                f.write("**LLM Analysis:** Not available\n\n")

                            # Sample cases
                            sample_cases = q_data.get("sample_cases", [])
                            if sample_cases:
                                f.write("**Sample Contextual Edge Cases:**\n\n")
                                for i, case in enumerate(sample_cases[:3], 1):
                                    f.write(
                                        f"{i}. **{case.get('name', 'Unknown')}** (Paper {case.get('paper_id', 'Unknown')})\n"
                                    )
                                    f.write(f"   - Contextual Combined Score: {case.get('contextual_combined_score', 0):.3f}\n")
                                    f.write(f"   - Input: {case.get('input', 'N/A')}\n")
                                    f.write(f"   - **Expected Output:** {case.get('expected_output', 'N/A')}\n")
                                    f.write(f"   - **Actual Output:** {case.get('actual_output', 'N/A')}\n\n")

                            f.write("---\n\n")

                except Exception as e:
                    f.write(f"*Error loading contextual summary data: {e}*\n\n")
            else:
                f.write("*No contextual summary report found*\n\n")

            # Footer
            f.write("---\n\n")
            f.write("*This report was generated automatically by the Contextual Measures Edge Case Analysis tool.*\n")

        print(f"  Generated contextual markdown report: {markdown_path}")
        return markdown_path

    def process_source(self, source: str, num_cases: int = 20) -> Dict[str, List[Dict]]:
        """
        Process edge cases for a specific data source.

        Args:
            source: Data source ("llm" or "reviewer")
            num_cases: Number of edge cases per question type

        Returns:
            Dictionary of edge cases organized by question type
        """
        print(f"Processing {source} data...")

        # Load data
        data = self.load_merged_data(source)
        if not data:
            print(f"No data found for {source}")
            return {}

        # Organize edge cases by question type
        edge_cases_by_question = {}

        for question_type in self.question_types:
            print(f"  Finding edge cases for {question_type}")
            edge_cases = self.identify_edge_cases(data, question_type, num_cases)
            edge_cases_by_question[question_type] = edge_cases

        return edge_cases_by_question

    def save_edge_cases(self, source: str, edge_cases_by_question: Dict[str, List[Dict]]):
        """Save edge cases to files organized by source and question type."""
        source_dir = self.output_dir / source
        source_dir.mkdir(exist_ok=True)

        for question_type, cases in edge_cases_by_question.items():
            if not cases:
                continue

            # Create filename
            filename = f"{source}_{question_type}.json"
            filepath = source_dir / filename

            # Save edge cases
            with open(filepath, "w") as f:
                json.dump(cases, f, indent=2)

            print(f"  Saved {len(cases)} edge cases to {filepath}")

    def generate_source_summary_report(self, source: str, edge_cases_by_question: Dict[str, List[Dict]]):
        """
        Generate a summary report for a specific source with LLM-powered reason summarization.

        Args:
            source: Data source ("llm" or "reviewer")
            edge_cases_by_question: Dictionary of edge cases organized by question type
        """
        source_dir = self.output_dir / source
        source_dir.mkdir(exist_ok=True)

        summary_report = {
            "source": source,
            "generated_at": str(pd.Timestamp.now()),
            "total_edge_cases": 0,
            "question_type_summaries": {},
            "overall_statistics": {},
        }

        total_cases = 0
        all_scores = []

        # Generate summaries for each question type
        for question_type, cases in edge_cases_by_question.items():
            if not cases:
                continue

            total_cases += len(cases)

            # Collect scores for statistics
            question_scores = [case["combined_score"] for case in cases]
            all_scores.extend(question_scores)

            # Generate LLM summary of reasons
            print(f"    Generating LLM summary for {question_type}...")
            llm_summary = self.summarize_reasons_with_llm(cases, question_type)

            summary_report["question_type_summaries"][question_type] = {
                "num_cases": len(cases),
                "score_range": {
                    "min": min(question_scores),
                    "max": max(question_scores),
                    "mean": sum(question_scores) / len(question_scores),
                },
                "llm_summary": llm_summary,
                "sample_cases": [
                    {
                        "name": case["name"],
                        "combined_score": case["combined_score"],
                        "paper_id": case.get("paper_id"),
                        "input": case["input"][:100] + "..." if len(case["input"]) > 100 else case["input"],
                        "expected_output": case["expected_output"][:150] + "..."
                        if len(case["expected_output"]) > 150
                        else case["expected_output"],
                        "actual_output": case["actual_output"][:150] + "..."
                        if len(case["actual_output"]) > 150
                        else case["actual_output"],
                    }
                    for case in cases[:3]  # Include first 3 cases as samples
                ],
            }

        # Overall statistics
        if all_scores:
            summary_report["overall_statistics"] = {
                "total_cases": total_cases,
                "score_range": {"min": min(all_scores), "max": max(all_scores), "mean": sum(all_scores) / len(all_scores)},
            }

        summary_report["total_edge_cases"] = total_cases

        # Save the summary report
        summary_path = source_dir / "summary-report.json"
        with open(summary_path, "w") as f:
            json.dump(summary_report, f, indent=2)

        print(f"  Generated summary report: {summary_path}")
        return summary_report

    def generate_markdown_report(self, all_edge_cases: Dict[str, Dict[str, List[Dict]]]):
        """
        Generate a comprehensive markdown report with all LLM summaries and edge case analysis.

        Args:
            all_edge_cases: Dictionary containing all identified edge cases
        """
        markdown_path = self.output_dir / "edge-case-report.md"

        with open(markdown_path, "w") as f:
            f.write("# Edge Case Analysis Report\n\n")
            f.write(f"*Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")

            # Overall statistics
            total_cases = sum(sum(len(cases) for cases in source_cases.values()) for source_cases in all_edge_cases.values())
            f.write("## Overview\n\n")
            f.write(f"- **Total Edge Cases Analyzed**: {total_cases}\n")
            f.write(f"- **Data Sources**: {', '.join(all_edge_cases.keys())}\n")
            f.write(f"- **Question Types**: {', '.join(self.question_types)}\n\n")

            # Process each source
            for source in self.data_sources:
                f.write(f"## {source.upper()} Analysis\n\n")

                # Try to load the summary report for this source
                summary_path = self.output_dir / source / "summary-report.json"
                if summary_path.exists():
                    try:
                        with open(summary_path, "r") as summary_file:
                            summary_data = json.load(summary_file)

                        # Overall statistics for this source
                        if "overall_statistics" in summary_data:
                            stats = summary_data["overall_statistics"]
                            f.write("### Overall Statistics\n\n")
                            f.write(f"- **Total Cases**: {stats.get('total_cases', 0)}\n")
                            f.write(
                                f"- **Score Range**: {stats.get('score_range', {}).get('min', 0):.3f} - {stats.get('score_range', {}).get('max', 0):.3f}\n"
                            )
                            f.write(f"- **Average Score**: {stats.get('score_range', {}).get('mean', 0):.3f}\n\n")

                        # Question type summaries
                        if "question_type_summaries" in summary_data:
                            f.write("### Question Type Analysis\n\n")

                            for question_type, q_data in summary_data["question_type_summaries"].items():
                                f.write(f"#### {question_type.replace('_', ' ').title()}\n\n")

                                # Basic stats
                                f.write(f"- **Number of Cases**: {q_data.get('num_cases', 0)}\n")
                                score_range = q_data.get("score_range", {})
                                f.write(
                                    f"- **Score Range**: {score_range.get('min', 0):.3f} - {score_range.get('max', 0):.3f}\n"
                                )
                                f.write(f"- **Average Score**: {score_range.get('mean', 0):.3f}\n\n")

                                # LLM Summary
                                llm_summary = q_data.get("llm_summary")
                                if llm_summary and llm_summary != "No detailed reasons found in the edge cases.":
                                    f.write("**LLM Analysis:**\n\n")
                                    f.write(f"{llm_summary}\n\n")
                                else:
                                    f.write("**LLM Analysis:** Not available\n\n")

                                # Sample cases
                                sample_cases = q_data.get("sample_cases", [])
                                if sample_cases:
                                    f.write("**Sample Edge Cases:**\n\n")
                                    for i, case in enumerate(sample_cases[:3], 1):
                                        f.write(
                                            f"{i}. **{case.get('name', 'Unknown')}** (Paper {case.get('paper_id', 'Unknown')})\n"
                                        )
                                        f.write(f"   - Combined Score: {case.get('combined_score', 0):.3f}\n")
                                        f.write(f"   - Input: {case.get('input', 'N/A')}\n")
                                        f.write(f"   - **Expected Output:** {case.get('expected_output', 'N/A')}\n")
                                        f.write(f"   - **Actual Output:** {case.get('actual_output', 'N/A')}\n\n")

                                f.write("---\n\n")

                    except Exception as e:
                        f.write(f"*Error loading summary data: {e}*\n\n")
                else:
                    f.write(f"*No summary report found for {source}*\n\n")

                f.write("\n")

            # Footer
            f.write("---\n\n")
            f.write("*This report was generated automatically by the Edge Case Analysis tool.*\n")

        print(f"  Generated markdown report: {markdown_path}")
        return markdown_path

    def generate_llm_summaries_from_files(self, source: str):
        """
        Generate LLM summaries by reading existing edge case files and analyzing the reasons.
        This method should be called after edge case files are created.

        Args:
            source: Data source ("llm" or "reviewer")
        """
        if not self.openai_client:
            print(f"  Skipping LLM summarization for {source} - no OpenAI client available")
            return

        source_dir = self.output_dir / source
        if not source_dir.exists():
            print(f"  Source directory {source_dir} does not exist")
            return

        # Find all edge case files for this source
        edge_case_files = list(source_dir.glob(f"{source}_*.json"))
        edge_case_files = [f for f in edge_case_files if f.name != "summary-report.json"]

        if not edge_case_files:
            print(f"  No edge case files found for {source}")
            return

        print(f"  Generating LLM summaries for {source} from {len(edge_case_files)} files...")

        # Load and analyze each edge case file
        for edge_case_file in edge_case_files:
            try:
                with open(edge_case_file, "r") as f:
                    edge_cases = json.load(f)

                if not edge_cases:
                    continue

                # Extract question type from filename
                question_type = edge_case_file.stem.replace(f"{source}_", "")

                print(f"    Analyzing {question_type} ({len(edge_cases)} cases)...")

                # Generate LLM summary
                llm_summary = self.summarize_reasons_with_llm(edge_cases, question_type)

                # Update the existing summary report
                summary_report_path = source_dir / "summary-report.json"
                if summary_report_path.exists():
                    with open(summary_report_path, "r") as f:
                        summary_report = json.load(f)

                    # Update the LLM summary for this question type
                    if question_type in summary_report.get("question_type_summaries", {}):
                        summary_report["question_type_summaries"][question_type]["llm_summary"] = llm_summary
                        summary_report["question_type_summaries"][question_type]["llm_summary_generated_at"] = str(
                            pd.Timestamp.now()
                        )

                    # Save updated summary report
                    with open(summary_report_path, "w") as f:
                        json.dump(summary_report, f, indent=2)

                    print(f"      Updated summary report with LLM analysis for {question_type}")

            except Exception as e:
                print(f"      Error processing {edge_case_file}: {e}")
                continue

    def generate_contextual_llm_summaries_from_files(self, source: str):
        """
        Generate LLM summaries for contextual measures by reading existing contextual edge case files.
        This method should be called after contextual edge case files are created.

        Args:
            source: Data source (should be "llm" for contextual analysis)
        """
        if source != "llm":
            print(f"Contextual LLM summarization is only available for LLM data, not {source}")
            return

        if not self.openai_client:
            print(f"  Skipping contextual LLM summarization for {source} - no OpenAI client available")
            return

        source_dir = self.output_dir / source
        if not source_dir.exists():
            print(f"  Source directory {source_dir} does not exist")
            return

        # Find all contextual edge case files for this source
        contextual_edge_case_files = list(source_dir.glob(f"{source}_*_contextual.json"))

        if not contextual_edge_case_files:
            print(f"  No contextual edge case files found for {source}")
            return

        print(f"  Generating contextual LLM summaries for {source} from {len(contextual_edge_case_files)} files...")

        # Load and analyze each contextual edge case file
        for edge_case_file in contextual_edge_case_files:
            try:
                with open(edge_case_file, "r") as f:
                    edge_cases = json.load(f)

                if not edge_cases:
                    continue

                # Extract question type from filename
                question_type = edge_case_file.stem.replace(f"{source}_", "").replace("_contextual", "")

                print(f"    Analyzing contextual measures for {question_type} ({len(edge_cases)} cases)...")

                # Generate LLM summary
                llm_summary = self.summarize_reasons_with_llm(edge_cases, question_type)

                # Update the existing contextual summary report
                summary_report_path = source_dir / "summary-report-context.json"
                if summary_report_path.exists():
                    with open(summary_report_path, "r") as f:
                        summary_report = json.load(f)

                    # Update the LLM summary for this question type
                    if question_type in summary_report.get("question_type_summaries", {}):
                        summary_report["question_type_summaries"][question_type]["llm_summary"] = llm_summary
                        summary_report["question_type_summaries"][question_type]["llm_summary_generated_at"] = str(
                            pd.Timestamp.now()
                        )

                    # Save updated summary report
                    with open(summary_report_path, "w") as f:
                        json.dump(summary_report, f, indent=2)

                    print(f"      Updated contextual summary report with LLM analysis for {question_type}")

            except Exception as e:
                print(f"      Error processing {edge_case_file}: {e}")
                continue

    def generate_summary_report(self, all_edge_cases: Dict[str, Dict[str, List[Dict]]]):
        """Generate a summary report of all identified edge cases."""
        summary = {"total_edge_cases": 0, "by_source": {}, "by_question_type": {}, "lowest_combined_scores": []}

        for source, source_cases in all_edge_cases.items():
            source_total = 0
            summary["by_source"][source] = {}

            for question_type, cases in source_cases.items():
                if question_type not in summary["by_question_type"]:
                    summary["by_question_type"][question_type] = 0

                num_cases = len(cases)
                source_total += num_cases
                summary["by_question_type"][question_type] += num_cases

                # Track lowest combined scores
                for case in cases:
                    summary["lowest_combined_scores"].append(
                        {
                            "source": source,
                            "question_type": question_type,
                            "combined_score": case["combined_score"],
                            "individual_scores": case["individual_scores"],
                            "individual_reasons": case["individual_reasons"],
                            "paper_id": case.get("paper_id"),
                            "name": case["name"],
                        }
                    )

            summary["by_source"][source]["total"] = source_total
            summary["total_edge_cases"] += source_total

        # Sort lowest combined scores
        summary["lowest_combined_scores"].sort(key=lambda x: x["combined_score"])

        # Save summary
        summary_path = self.output_dir / "edge_cases_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary report saved to {summary_path}")
        print(f"Total edge cases identified: {summary['total_edge_cases']}")

        return summary

    def run_analysis(self, num_cases: int = 20) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Run the complete edge case analysis.

        Args:
            num_cases: Number of edge cases to identify per question type

        Returns:
            Dictionary containing all identified edge cases
        """
        print(f"Starting edge case analysis (targeting {num_cases} cases per question type)...")

        all_edge_cases = {}

        # Process each data source
        for source in self.data_sources:
            edge_cases = self.process_source(source, num_cases)
            all_edge_cases[source] = edge_cases

            # Save edge cases for this source
            self.save_edge_cases(source, edge_cases)

            # Generate source-specific summary report
            print(f"  Generating summary report for {source}...")
            self.generate_source_summary_report(source, edge_cases)

        # Generate overall summary report
        summary = self.generate_summary_report(all_edge_cases)

        # Now generate LLM summaries from the created files
        print("\nGenerating LLM summaries from edge case files...")
        for source in self.data_sources:
            print(f"  Processing {source}...")
            self.generate_llm_summaries_from_files(source)

        # Generate comprehensive markdown report
        print("\nGenerating markdown report...")
        self.generate_markdown_report(all_edge_cases)

        print("\nEdge case analysis complete!")
        return all_edge_cases

    def run_contextual_analysis(self, num_cases: int = 20) -> Dict[str, List[Dict]]:
        """
        Run contextual measures edge case analysis for LLM data only.

        Args:
            num_cases: Number of edge cases to identify per question type

        Returns:
            Dictionary containing contextual edge cases organized by question type
        """
        print(f"Starting contextual measures edge case analysis (targeting {num_cases} cases per question type)...")

        # Process contextual measures for LLM data only
        contextual_edge_cases = self.process_contextual_source("llm", num_cases)

        if not contextual_edge_cases:
            print("No contextual edge cases found for LLM data")
            return {}

        # Save contextual edge cases
        self.save_contextual_edge_cases("llm", contextual_edge_cases)

        # Generate contextual summary report
        print("  Generating contextual summary report for LLM...")
        self.generate_contextual_source_summary_report("llm", contextual_edge_cases)

        # Generate contextual markdown report
        print("  Generating contextual markdown report...")
        self.generate_contextual_markdown_report(contextual_edge_cases)

        # Now generate LLM summaries from the created contextual files
        print("  Generating LLM summaries from contextual edge case files...")
        self.generate_contextual_llm_summaries_from_files("llm")

        print("Contextual measures edge case analysis complete!")
        return contextual_edge_cases


def main():
    """Main function to run edge case identification."""
    parser = argparse.ArgumentParser(description="Identify edge cases from evaluation results")
    parser.add_argument(
        "--num-cases", type=int, default=20, help="Number of edge cases to identify per question type (default: 20)"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help="Directory containing evaluation results (default: auto-detect from config)",
    )
    parser.add_argument(
        "--merged-data-dir",
        type=str,
        default=None,
        help="Directory containing merged evaluation results (not used, kept for compatibility)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=None, help="Output directory for edge cases (default: auto-detect from config)"
    )
    parser.add_argument(
        "--openai-api-key", type=str, default=None, help="OpenAI API key for LLM summarization (or set OPENAI_API_KEY env var)"
    )
    parser.add_argument("--model", type=str, default="gpt-4o", help="OpenAI model to use for summarization (default: gpt-4o)")
    parser.add_argument(
        "--generate-summaries-only",
        action="store_true",
        help="Only generate LLM summaries for existing edge case files (skip edge case identification)",
    )
    parser.add_argument(
        "--contextual-only",
        action="store_true",
        help="Only run contextual measures analysis (Faithfulness, Contextual Precision, Contextual Recall) for LLM data",
    )
    parser.add_argument(
        "--generate-contextual-summaries-only",
        action="store_true",
        help="Only generate LLM summaries for existing contextual edge case files (skip edge case identification)",
    )

    args = parser.parse_args()

    # Initialize the identifier
    identifier = EdgeCaseIdentifier(
        results_dir=args.results_dir,
        merged_data_dir=args.merged_data_dir,
        output_dir=args.output_dir,
        openai_api_key=args.openai_api_key,
        model=args.model,
    )

    if args.generate_summaries_only:
        # Only generate summaries for existing files
        print("Generating LLM summaries for existing edge case files...")
        for source in ["llm", "reviewer"]:
            print(f"Processing {source}...")
            identifier.generate_llm_summaries_from_files(source)
    elif args.contextual_only:
        # Run contextual measures analysis only
        print("Running contextual measures analysis for LLM data...")
        contextual_edge_cases = identifier.run_contextual_analysis(num_cases=args.num_cases)

        # Print some quick stats
        if contextual_edge_cases:
            total_cases = sum(len(cases) for cases in contextual_edge_cases.values())
            print("\nQuick Statistics:")
            print(f"  LLM Contextual Measures: {total_cases} total edge cases")
        else:
            print("\nNo contextual edge cases found")
    elif args.generate_contextual_summaries_only:
        # Only generate contextual LLM summaries for existing files
        print("Generating contextual LLM summaries for existing contextual edge case files...")
        identifier.generate_contextual_llm_summaries_from_files("llm")
    else:
        # Run full analysis
        edge_cases = identifier.run_analysis(num_cases=args.num_cases)

        # Print some quick stats
        print("\nQuick Statistics:")
        for source, source_cases in edge_cases.items():
            total_cases = sum(len(cases) for cases in source_cases.values())
            print(f"  {source.capitalize()}: {total_cases} total edge cases")


if __name__ == "__main__":
    main()
