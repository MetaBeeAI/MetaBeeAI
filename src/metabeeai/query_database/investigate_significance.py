#!/usr/bin/env python3
"""
Script to investigate significance data from answers.json files.
Extracts significance information and categorizes into:
1. Level of biological organization (molecular, sub-individual, individual, population, community)
2. Study type (field, lab)
3. Variable measured (e.g., drone weight, reproductive output)
4. Significance (significant, not significant)
"""

import argparse
import json
import os
import re
from typing import Dict, List, Tuple

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def load_env_file():
    """Load environment variables from .env file if it exists."""
    # Try current directory first
    env_file = ".env"
    if not os.path.exists(env_file):
        # Fallback to parent directory
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")

    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


def get_papers_dir():
    """Get the papers directory path from environment variable or use default."""
    # Load environment variables
    load_env_file()

    # Try to get from environment variable first
    data_dir = os.getenv("METABEEAI_DATA_DIR")
    if data_dir:
        papers_dir = os.path.join(data_dir, "papers")
    else:
        # Fallback to default path
        papers_dir = os.path.join(os.path.dirname(__file__), "..", "data", "papers")

    return papers_dir


def find_answers_files(papers_dir: str) -> List[Tuple[str, str]]:
    """Find all answers.json files in the papers directory."""
    answers_files = []

    if not os.path.exists(papers_dir):
        print(f"Papers directory not found: {papers_dir}")
        return answers_files

    for paper_id in os.listdir(papers_dir):
        paper_dir = os.path.join(papers_dir, paper_id)
        if os.path.isdir(paper_dir):
            answers_file = os.path.join(paper_dir, "answers.json")
            if os.path.exists(answers_file):
                answers_files.append((paper_id, answers_file))

    return sorted(answers_files)


def load_pesticides_data(output_dir: str) -> Dict[str, List[Dict[str, str]]]:
    """Load pesticides data and organize by paper_id."""
    pesticides_file = os.path.join(output_dir, "pesticides_data.json")
    pesticides_by_paper = {}

    if os.path.exists(pesticides_file):
        with open(pesticides_file, "r", encoding="utf-8") as f:
            pesticides_data = json.load(f)

        for entry in pesticides_data:
            paper_id = entry["paper_id"]
            if paper_id not in pesticides_by_paper:
                pesticides_by_paper[paper_id] = []
            pesticides_by_paper[paper_id].append(
                {"pesticide_name": entry["pesticide_name"], "original_answer": entry["original_answer"]}
            )

    return pesticides_by_paper


def extract_significance_with_llm(
    paper_id: str,
    significance_answer: str,
    experimental_methodology: str = "",
    pesticides_for_paper: List[Dict[str, str]] = None,
) -> List[Dict[str, str]]:
    """
    Use GPT-4 to extract and categorize significance findings.

    Args:
        paper_id: Paper ID for context
        significance_answer: The significance answer text
        experimental_methodology: The experimental methodology for context

    Returns:
        List of dictionaries with significance data
    """
    if not significance_answer or not OPENAI_AVAILABLE:
        return []

    try:
        # Load environment variables (including OpenAI API key)
        load_env_file()

        # Check if API key is available
        if not os.getenv("OPENAI_API_KEY"):
            print(f"  Warning: OPENAI_API_KEY not found in environment for paper {paper_id}")
            return []

        # Initialize OpenAI client
        client = openai.OpenAI()

        # Build pesticides context
        pesticides_context = ""
        if pesticides_for_paper:
            pesticides_context = (
                f"\nPESTICIDES TESTED IN THIS STUDY: {', '.join([p['pesticide_name'] for p in pesticides_for_paper])}"
            )

        prompt = f"""
You are an expert at analyzing scientific findings and categorizing them by biological organization level, study type, variables measured, significance, and specific pesticide tested.

TASK: Extract and categorize ONLY findings about BIOLOGICAL EFFECTS on bees, not exposure confirmation or residue analysis.

SIGNIFICANCE FINDINGS: {significance_answer}

EXPERIMENTAL CONTEXT: {experimental_methodology}{pesticides_context}

IMPORTANT: Only extract findings about actual biological effects/impacts on bees. EXCLUDE:
- Residue analysis results
- Exposure confirmation
- Detection of pesticides in samples
- Measurements of pesticide levels
- Foraging observations (unless they show behavioral effects)

INCLUDE ONLY findings about:
- Biological effects (mortality, behavior, development, reproduction, health)
- Physiological changes
- Performance metrics
- Survival outcomes
- Behavioral changes

For each finding, extract:
1. **level**: The level of biological organization where the effect was measured
   - "molecular" (e.g., gene expression, enzyme activity, protein levels)
   - "sub-individual" (e.g., organ function, tissue damage, cellular responses)
   - "individual" (e.g., behavior, survival, weight, individual bee health)
   - "population" (e.g., colony size, reproductive output, population dynamics)
   - "community" (e.g., species interactions, ecosystem effects)

2. **study_type**: Whether this was a "field" or "lab" study (infer from context)

3. **variable_measured**: The specific biological variable or endpoint measured (e.g., "drone weight", "reproductive output", "mortality", "colony development")

4. **significance**: Whether the effect was "significant" or "not significant" (look for explicit statements of significance, p-values, or clear language about effects)

5. **pesticide_tested**: The specific pesticide that was tested for this effect. If multiple pesticides were tested, determine which one is associated with this specific finding. If the finding is about a general effect or all pesticides combined, use "multiple" or "all pesticides". If no specific pesticide is mentioned, use "unspecified".

EXAMPLES:
- "No adverse effect of clothianidin on colony development" → pesticide_tested: "clothianidin"
- "LD50 for thiamethoxam was 6.63 ng" → pesticide_tested: "thiamethoxam"
- "No effect on sucrose consumption" (when only one pesticide tested) → pesticide_tested: [name of that pesticide]
- "Both pesticides showed similar effects" → pesticide_tested: "multiple"

DO NOT INCLUDE:
- "Residue analysis confirmed exposure" (this is about detection, not biological effect)
- "Bumble bees were observed foraging" (this is observation, not effect)
- "Measured levels ranging from X to Y" (this is residue analysis)

Return ONLY a JSON array of objects with "level", "study_type", "variable_measured", "significance", and "pesticide_tested" keys. Extract each distinct biological effect finding as a separate object.
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a scientific data extraction expert. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=1000,
        )

        # Parse the response
        response_text = response.choices[0].message.content.strip()

        # Extract JSON from response
        json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
        if json_match:
            findings = json.loads(json_match.group())
            return findings

    except Exception as e:
        print(f"GPT-4 processing failed for paper {paper_id}: {e}")

    return []


def save_progress(results, output_dir, checkpoint_file):
    """Save current progress to checkpoint file."""
    checkpoint_path = os.path.join(output_dir, checkpoint_file)
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"  Progress saved to checkpoint: {checkpoint_path}")


def load_progress(output_dir, checkpoint_file):
    """Load progress from checkpoint file."""
    checkpoint_path = os.path.join(output_dir, checkpoint_file)
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            results = json.load(f)
        print(f"  Loaded progress from checkpoint: {len(results)} entries")
        return results
    return []


def main():
    """Main function to process all answers.json files and create CSV output."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Extract significance data")
    parser.add_argument("--no-llm", action="store_true", help="Skip GPT-4 processing")
    parser.add_argument("--test-papers", type=int, help="Process only first N papers for testing")
    parser.add_argument("--start-from", type=str, help="Start processing from this paper ID")
    parser.add_argument("--save-interval", type=int, default=50, help="Save progress every N papers (default: 50)")
    args = parser.parse_args()

    papers_dir = get_papers_dir()
    print(f"Looking for papers in: {papers_dir}")

    # Find all answers.json files
    answers_files = find_answers_files(papers_dir)

    # Limit papers for testing if specified
    if args.test_papers:
        answers_files = answers_files[: args.test_papers]
        print(f"Processing first {len(answers_files)} papers for testing")
    else:
        print(f"Found {len(answers_files)} answers.json files")

    # Configuration
    use_llm_processing = not args.no_llm
    if use_llm_processing:
        print("GPT-4 processing enabled")
    else:
        print("GPT-4 processing disabled")

    # Set up output directory and checkpoint file
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    checkpoint_file = "significance_data_checkpoint.json"

    # Load pesticides data for cross-referencing
    print("Loading pesticides data...")
    pesticides_by_paper = load_pesticides_data(output_dir)
    print(f"Loaded pesticides data for {len(pesticides_by_paper)} papers")

    # Load existing progress or start fresh
    results = load_progress(output_dir, checkpoint_file)

    # Determine starting point
    start_index = 0
    if args.start_from:
        for i, (paper_id, _) in enumerate(answers_files):
            if paper_id == args.start_from:
                start_index = i
                break
        print(f"Starting from paper {args.start_from} (index {start_index})")
    elif results:
        # Find the last processed paper
        processed_papers = {r["paper_id"] for r in results}
        for i, (paper_id, _) in enumerate(answers_files):
            if paper_id not in processed_papers:
                start_index = i
                break
        else:
            print("All papers already processed!")
            return
        print(f"Resuming from paper {answers_files[start_index][0]} (index {start_index})")

    # Process papers
    papers_to_process = answers_files[start_index:]
    print(f"Processing {len(papers_to_process)} papers")

    for i, (paper_id, file_path) in enumerate(papers_to_process):
        current_index = start_index + i
        print(f"Processing paper {paper_id}... ({current_index + 1}/{len(answers_files)})")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract significance information
            questions = data.get("QUESTIONS", {})
            significance_data = questions.get("significance", {})
            significance_answer = significance_data.get("answer", "")
            reason = significance_data.get("reason", "")

            # Get experimental methodology for context
            experimental_data = questions.get("experimental_methodology", {})
            experimental_methodology = experimental_data.get("answer", "")

            # Get pesticides for this paper
            pesticides_for_paper = pesticides_by_paper.get(paper_id, [])

            # Extract significance findings
            if significance_answer and use_llm_processing:
                print("  Extracting significance findings...")
                if pesticides_for_paper:
                    print(f"  Pesticides in this study: {', '.join([p['pesticide_name'] for p in pesticides_for_paper])}")
                findings = extract_significance_with_llm(
                    paper_id, significance_answer, experimental_methodology, pesticides_for_paper
                )

                # Post-process findings: improve pesticide assignment
                if findings:
                    # First, identify which pesticides are actually mentioned in the significance text
                    significance_lower = significance_answer.lower()
                    mentioned_pesticides = []
                    for pesticide in pesticides_for_paper:
                        pesticide_name = pesticide["pesticide_name"].lower()
                        if pesticide_name in significance_lower:
                            mentioned_pesticides.append(pesticide)

                    # If only one pesticide is mentioned in the text, default all findings to that pesticide
                    if len(mentioned_pesticides) == 1:
                        primary_pesticide = mentioned_pesticides[0]["pesticide_name"]
                        for finding in findings:
                            if finding.get("pesticide_tested", "").lower() in ["unspecified", ""]:
                                finding["pesticide_tested"] = primary_pesticide
                                print(f"    Defaulted unspecified pesticide to: {primary_pesticide} (only mentioned pesticide)")
                    else:
                        # Multiple pesticides mentioned or none clearly mentioned - try to match each finding
                        for finding in findings:
                            current_pesticide = finding.get("pesticide_tested", "").lower()

                            # If only one pesticide in study and finding is unspecified, default to that pesticide
                            if len(pesticides_for_paper) == 1 and current_pesticide in ["unspecified", ""]:
                                single_pesticide = pesticides_for_paper[0]["pesticide_name"]
                                finding["pesticide_tested"] = single_pesticide
                                print(f"    Defaulted unspecified pesticide to: {single_pesticide}")

                            # If multiple pesticides but text clearly mentions one, try to match it
                            elif len(mentioned_pesticides) > 0 and current_pesticide in ["unspecified", ""]:
                                # Use the first mentioned pesticide as default
                                primary_pesticide = mentioned_pesticides[0]["pesticide_name"]
                                finding["pesticide_tested"] = primary_pesticide
                                print(f"    Defaulted unspecified pesticide to: {primary_pesticide} (first mentioned)")

                    # Report ignored pesticides
                    ignored_pesticides = [p for p in pesticides_for_paper if p not in mentioned_pesticides]
                    if ignored_pesticides:
                        ignored_names = [p["pesticide_name"] for p in ignored_pesticides]
                        print(f"    Ignored pesticides not mentioned in significance: {', '.join(ignored_names)}")

                if findings:
                    for finding in findings:
                        results.append(
                            {
                                "paper_id": paper_id,
                                "level": finding.get("level", ""),
                                "study_type": finding.get("study_type", ""),
                                "variable_measured": finding.get("variable_measured", ""),
                                "significance": finding.get("significance", ""),
                                "pesticide_tested": finding.get("pesticide_tested", ""),
                                "original_answer": significance_answer,
                                "reason": reason,
                            }
                        )
                    print(f"  Extracted {len(findings)} findings")
                else:
                    # No findings extracted, add empty entry
                    results.append(
                        {
                            "paper_id": paper_id,
                            "level": "",
                            "study_type": "",
                            "variable_measured": "",
                            "significance": "",
                            "pesticide_tested": "",
                            "original_answer": significance_answer,
                            "reason": reason,
                        }
                    )
            else:
                # No LLM processing or no significance data
                results.append(
                    {
                        "paper_id": paper_id,
                        "level": "",
                        "study_type": "",
                        "variable_measured": "",
                        "significance": "",
                        "pesticide_tested": "",
                        "original_answer": significance_answer,
                        "reason": reason,
                    }
                )

            # Save progress periodically
            if (i + 1) % args.save_interval == 0:
                save_progress(results, output_dir, checkpoint_file)

        except Exception as e:
            print(f"Error processing {paper_id}: {e}")
            continue

    # Save final progress
    save_progress(results, output_dir, checkpoint_file)

    # Save final results to JSON and CSV
    print("\nGenerating final output files...")

    # Save full results as JSON (handles multi-line text properly)
    json_file = os.path.join(output_dir, "significance_data.json")
    with open(json_file, "w", encoding="utf-8") as jsonfile:
        json.dump(results, jsonfile, indent=2, ensure_ascii=False)

    # Remove checkpoint file after successful completion
    checkpoint_path = os.path.join(output_dir, checkpoint_file)
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        print(f"  Removed checkpoint file: {checkpoint_path}")

    print("\nResults saved to:")
    print(f"  JSON (full data): {json_file}")
    print(f"Total significance entries: {len(results)}")

    # Print summary statistics
    entries_with_data = [r for r in results if r["level"]]
    unique_levels = set(result["level"] for result in entries_with_data)
    unique_study_types = set(result["study_type"] for result in entries_with_data)
    unique_variables = set(result["variable_measured"] for result in entries_with_data)
    unique_significance = set(result["significance"] for result in entries_with_data)
    papers_with_significance = set(result["paper_id"] for result in entries_with_data)

    print(f"Entries with extracted data: {len(entries_with_data)}")
    print(f"Unique biological levels: {len(unique_levels)}")
    print(f"Unique study types: {len(unique_study_types)}")
    print(f"Unique variables measured: {len(unique_variables)}")
    print(f"Unique significance outcomes: {len(unique_significance)}")
    print(f"Papers with significance data: {len(papers_with_significance)}")

    # Show breakdowns
    if entries_with_data:
        print("\nBiological level breakdown:")
        level_counts = {}
        for result in entries_with_data:
            level_counts[result["level"]] = level_counts.get(result["level"], 0) + 1
        for level, count in sorted(level_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {level}: {count}")

        print("\nStudy type breakdown:")
        study_counts = {}
        for result in entries_with_data:
            study_counts[result["study_type"]] = study_counts.get(result["study_type"], 0) + 1
        for study_type, count in sorted(study_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {study_type}: {count}")

        print("\nSignificance breakdown:")
        sig_counts = {}
        for result in entries_with_data:
            sig_counts[result["significance"]] = sig_counts.get(result["significance"], 0) + 1
        for significance, count in sorted(sig_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {significance}: {count}")

    # Show sample results
    print("\nSample results:")
    for i, result in enumerate(entries_with_data[:10]):
        print(
            f"  {result['paper_id']}: {result['level']} | {result['study_type']} | {result['variable_measured']} | {result['significance']}"
        )

    if len(entries_with_data) > 10:
        print(f"  ... and {len(entries_with_data) - 10} more entries")


if __name__ == "__main__":
    main()
