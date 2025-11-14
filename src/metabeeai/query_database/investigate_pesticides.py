#!/usr/bin/env python3
"""
Script to investigate pesticide data across all answers.json files in METABEEAI_DATA_DIR.

This script:
1. Finds all answers.json files in paper subdirectories
2. Extracts the "pesticides" answer from each file
3. Parses pesticide names from numbered lists (e.g., "1. imidacloprid, ...; 2. thiamethoxam, ...")
4. Associates each pesticide with the paper ID
5. Saves results as CSV in query_database/output/

Usage:
    python investigate_pesticides.py
"""

import json
import os
import re
from typing import List, Tuple


# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    env_file = os.path.join(parent_dir, ".env")

    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


# Get papers directory with proper .env loading
def get_papers_dir():
    """
    Get the papers directory path from METABEEAI_DATA_DIR environment variable.
    """
    # Load .env file first
    load_env_file()

    # Get data directory from environment variable
    data_dir = os.getenv("METABEEAI_DATA_DIR")
    if data_dir:
        papers_dir = os.path.join(data_dir, "papers")
        if os.path.exists(papers_dir):
            return papers_dir
        else:
            print(f"Warning: Papers directory not found at {papers_dir}")

    # Fallback to default relative path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    default_papers_dir = os.path.join(parent_dir, "data", "papers")

    if os.path.exists(default_papers_dir):
        return default_papers_dir

    # Final fallback
    return "/Users/user/Documents/MetaBeeAI/pipeline/data/papers"


def extract_pesticides_from_file(file_path: str) -> str:
    """
    Extract pesticides answer from an answers.json file.

    Args:
        file_path: Path to the answers.json file

    Returns:
        The pesticides answer, or None if not found
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Navigate to the pesticides answer
        if "QUESTIONS" in data and "pesticides" in data["QUESTIONS"]:
            return data["QUESTIONS"]["pesticides"].get("answer", "")

        return None
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"Error reading {file_path}: {e}")
        return None


def find_all_answers_files(papers_dir: str) -> List[Tuple[str, str]]:
    """
    Find all answers.json files in paper subdirectories.

    Args:
        papers_dir: Path to the papers directory

    Returns:
        List of tuples (paper_id, file_path)
    """
    answers_files = []

    if not os.path.exists(papers_dir):
        print(f"Papers directory not found: {papers_dir}")
        return answers_files

    # Look for numbered subdirectories (001, 002, etc.)
    for item in os.listdir(papers_dir):
        item_path = os.path.join(papers_dir, item)
        if os.path.isdir(item_path) and item.isdigit():
            answers_file = os.path.join(item_path, "answers.json")
            if os.path.exists(answers_file):
                answers_files.append((item, answers_file))
            else:
                print(f"No answers.json found in {item_path}")

    return answers_files


def extract_pesticide_names(pesticides_answer: str) -> List[str]:
    """
    Extract pesticide names from a pesticides answer string.
    Only extracts actual pesticide names, filtering out numbers, dosages, and other non-pesticide text.
    Returns empty list for negative responses like "No pesticides were tested".

    Args:
        pesticides_answer: The raw answer from the pesticides field

    Returns:
        List of pesticide names only, or empty list for negative responses
    """
    if not pesticides_answer or pesticides_answer.strip() == "":
        return []

    # Check for negative responses indicating no pesticides were tested
    negative_responses = [
        "no pesticides were tested",
        "no pesticides tested",
        "no pesticides were used",
        "no pesticides used",
        "no pesticides specified",
        "no pesticides mentioned",
        "no pesticides found",
        "pesticides not tested",
        "pesticides not used",
        "pesticides not specified",
        "pesticides not mentioned",
        "no chemical treatments",
        "no chemical exposure",
        "no exposure to pesticides",
        "pesticide-free",
        "no treatments",
        "no chemicals tested",
        "no chemicals used",
    ]

    answer_lower = pesticides_answer.lower().strip()

    # Check if the answer indicates no pesticides were tested
    for negative_response in negative_responses:
        if negative_response in answer_lower:
            return []

    pesticide_names = []

    # Pattern to match numbered lists: "1. pesticide_name:" or "1. pesticide_name,"
    # This captures only the pesticide name before the first colon or comma
    pattern = r"\d+\.\s*([^,:;]+?)(?=:|,|;)"

    matches = re.findall(pattern, pesticides_answer)

    for match in matches:
        # Clean up the pesticide name
        pesticide_name = match.strip()

        # Remove any trailing punctuation and extra whitespace
        pesticide_name = re.sub(r"[.,;:!?]+$", "", pesticide_name).strip()

        # Standardize: keep only first word or hyphenated compound words
        pesticide_name = standardize_pesticide_name(pesticide_name, pesticides_answer)

        # Additional filtering to remove non-pesticide entries
        if pesticide_name and is_valid_pesticide_name(pesticide_name):
            pesticide_names.append(pesticide_name)

    # If no numbered lists found, try to extract from other patterns
    if not pesticide_names:
        # Look for pesticide names that might not be in numbered lists
        # This is a fallback for cases where pesticides are mentioned differently
        words = pesticides_answer.split()
        potential_pesticides = []

        for i, word in enumerate(words):
            # Skip very short words, numbers, and common words
            if len(word) > 3 and word.lower() not in [
                "the",
                "and",
                "was",
                "were",
                "tested",
                "used",
                "at",
                "in",
                "on",
                "for",
                "with",
                "to",
                "of",
                "a",
                "an",
                "no",
                "pesticides",
                "specified",
            ]:
                # Check if it looks like a pesticide name (starts with letter, contains letters/numbers/hyphens)
                if re.match(r"^[a-zA-Z][a-zA-Z0-9\-]*$", word):
                    standardized_word = standardize_pesticide_name(word, pesticides_answer)
                    if standardized_word and is_valid_pesticide_name(standardized_word):
                        potential_pesticides.append(standardized_word)

        if potential_pesticides:
            pesticide_names = potential_pesticides[:5]  # Limit to first 5 potential matches

    return pesticide_names


def standardize_pesticide_name(name: str, original_answer: str = "") -> str:
    """
    Standardize pesticide name by keeping only the first word or hyphenated compound words,
    and converting to lowercase. Also handles 3-letter code expansions.

    Args:
        name: Raw pesticide name
        original_answer: Original answer text for context (used for "pro" disambiguation)

    Returns:
        Standardized pesticide name in lowercase
    """
    if not name:
        return ""

    # Split by spaces and take the first part
    first_part = name.split()[0] if name.split() else ""

    # Check if it's a hyphenated compound (like "Thiacloprid + Deltamethrin" -> "Thiacloprid")
    # For now, we'll just take the first word before any "+" or "-" that separates different chemicals
    if "+" in first_part:
        first_part = first_part.split("+")[0].strip()
    elif " + " in name:
        # Handle cases like "Thiacloprid + Deltamethrin"
        first_part = name.split(" + ")[0].strip()

    # Remove any remaining punctuation and convert to lowercase
    first_part = re.sub(r"[^\w\-]", "", first_part).lower()

    # Handle 3-letter code expansions
    three_letter_codes = {
        "fpf": "flupyradifurone",
        "flp": "flupyradifurone",
        "imi": "imidacloprid",
        "clo": "clothianidin",
        "dmf": "dmf",  # Keep as is
        "npv": "nuclear polyhedrosis virus",
    }

    # Special handling for "pro" - check original answer for disambiguation
    if first_part == "pro":
        if "prothioconazole" in original_answer.lower():
            return "prothioconazole"
        elif "prochloraz" in original_answer.lower():
            return "prochloraz"
        else:
            return "pro"  # Default if no match found

    # Check if it's a 3-letter code we can expand
    if first_part in three_letter_codes:
        return three_letter_codes[first_part]

    return first_part


def is_valid_pesticide_name(name: str) -> bool:
    """
    Check if a string is likely a valid pesticide name.

    Args:
        name: String to check

    Returns:
        True if likely a pesticide name, False otherwise
    """
    if not name or len(name) < 2:
        return False

    # Skip if it's purely numeric
    if name.isdigit():
        return False

    # Skip if it's a decimal number (like "625", "875", etc.)
    try:
        float(name)
        return False
    except ValueError:
        pass

    # Skip common non-pesticide words that might be extracted
    skip_words = [
        "concentration",
        "exposure",
        "method",
        "duration",
        "specified",
        "oral",
        "topical",
        "application",
        "contact",
        "residual",
        "continuous",
        "hours",
        "days",
        "weeks",
        "through",
        "sugar",
        "syrup",
        "pollen",
        "pastry",
        "mg",
        "mL",
        "g",
        "da",
        "ppm",
        "ppb",
        "and",
        "the",
        "was",
        "were",
        "tested",
        "used",
        "at",
        "in",
        "on",
        "for",
        "with",
        "to",
        "of",
    ]

    if name.lower() in skip_words:
        return False

    # Skip words that are mostly numbers with letters (like "da⁻¹")
    if re.search(r"\d+", name) and len(re.findall(r"[a-zA-Z]", name)) <= 2:
        return False

    # Must start with a letter
    if not name[0].isalpha():
        return False

    # Accept chemical abbreviations (all caps, 2-4 characters)
    if len(name) >= 2 and len(name) <= 4 and name.isupper() and name.isalpha():
        return True

    # For longer names, require at least 3 characters
    if len(name) >= 3:
        return True

    return False


def main():
    """Main function to process all answers.json files and create CSV output."""

    # Get papers directory from config
    papers_dir = get_papers_dir()
    print(f"Looking for papers in: {papers_dir}")

    # Find all answers.json files
    answers_files = find_all_answers_files(papers_dir)
    print(f"Found {len(answers_files)} answers.json files")

    if not answers_files:
        print("No answers.json files found. Exiting.")
        return

    # Process each file
    results = []

    for paper_id, file_path in answers_files:
        print(f"Processing paper {paper_id}...")

        # Extract pesticides answer
        pesticides_answer = extract_pesticides_from_file(file_path)

        if pesticides_answer is None:
            print(f"  No pesticides data found in {file_path}")
            continue

        # Parse pesticide names
        pesticide_names = extract_pesticide_names(pesticides_answer)

        # Handle empty results (no pesticides found)
        if not pesticide_names:
            results.append({"paper_id": paper_id, "pesticide_name": "", "original_answer": pesticides_answer})
        else:
            # Remove duplicates and add to results
            unique_pesticides = list(set(pesticide_names))  # Remove duplicates within the same paper

            for pesticide in unique_pesticides:
                results.append({"paper_id": paper_id, "pesticide_name": pesticide, "original_answer": pesticides_answer})

    # Save results to JSON and CSV
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Save full results as JSON (handles multi-line text properly)
    json_file = os.path.join(output_dir, "pesticides_data.json")
    with open(json_file, "w", encoding="utf-8") as jsonfile:
        json.dump(results, jsonfile, indent=2, ensure_ascii=False)

    print("\nResults saved to:")
    print(f"  JSON (full data): {json_file}")
    print(f"Total pesticide entries: {len(results)}")

    # Print summary statistics
    unique_pesticides = set(result["pesticide_name"] for result in results)
    papers_with_pesticides = set(result["paper_id"] for result in results)

    print(f"Unique pesticides found: {len(unique_pesticides)}")
    print(f"Papers with pesticide data: {len(papers_with_pesticides)}")

    # Show some examples
    print("\nSample results:")
    for i, result in enumerate(results[:5]):
        print(f"  {result['paper_id']}: {result['pesticide_name']}")

    if len(results) > 5:
        print(f"  ... and {len(results) - 5} more entries")


if __name__ == "__main__":
    main()
