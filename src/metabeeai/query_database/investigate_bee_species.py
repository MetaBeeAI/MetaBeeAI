#!/usr/bin/env python3
"""
Script to investigate bee species data across all answers.json files in METABEEAI_DATA_DIR.

This script:
1. Finds all answers.json files in paper subdirectories
2. Extracts the "bee_species" answer from each file
3. Cleans species names by removing numbers, punctuation, and formatting
4. Associates each species list with the paper ID
5. Saves results as CSV in query_database/output/

Usage:
    python investigate_bee_species.py
"""

import csv
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


def clean_species_name(species_text: str) -> str:
    """
    Clean species names by removing numbers, punctuation, and formatting.

    Args:
        species_text: Raw species text from answers.json

    Returns:
        Cleaned species name
    """
    if not species_text or species_text.strip() == "":
        return "Species not specified"

    # Remove common prefixes and formatting
    cleaned = species_text.strip()

    # Remove numbered lists (e.g., "1. ", "2. ", etc.)
    cleaned = re.sub(r"^\d+\.\s*", "", cleaned)

    # Remove newline characters and extra whitespace
    cleaned = re.sub(r"\n", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Remove extra punctuation at the beginning/end
    cleaned = cleaned.strip(".,;:!?")

    return cleaned.strip() if cleaned.strip() else "Species not specified"


def extract_bee_species_from_file(file_path: str) -> tuple:
    """
    Extract bee_species answer and reason from an answers.json file.

    Args:
        file_path: Path to the answers.json file

    Returns:
        Tuple of (answer, reason) or (None, None) if not found
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Navigate to the bee_species answer
        if "QUESTIONS" in data and "bee_species" in data["QUESTIONS"]:
            bee_species_data = data["QUESTIONS"]["bee_species"]
            answer = bee_species_data.get("answer", "")
            reason = bee_species_data.get("reason", "")
            return answer, reason

        return None, None
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"Error reading {file_path}: {e}")
        return None, None


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


def parse_species_name(species_name: str) -> tuple:
    """
    Parse a species name into genus, species, and subspecies components.

    Args:
        species_name: The cleaned species name

    Returns:
        Tuple of (genus, species, subspecies)
    """
    if not species_name or species_name == "Species not specified":
        return "", "", ""

    # Split by spaces
    parts = species_name.strip().split()

    if len(parts) == 0:
        return "", "", ""
    elif len(parts) == 1:
        return parts[0], "", ""
    elif len(parts) == 2:
        return parts[0], parts[1], ""
    else:
        # 3 or more parts: genus, species, subspecies (and any additional words)
        return parts[0], parts[1], " ".join(parts[2:])


def extract_common_name_from_reason(reason: str) -> str:
    """
    Extract common bee names from the reason field.

    Args:
        reason: The reason text from answers.json

    Returns:
        Common name if found, empty string otherwise
    """
    if not reason:
        return ""

    # Common bee name patterns to look for
    common_names = ["honeybee", "honeybees", "honey bee", "honey bees", "bumblebee", "bumblebees", "bumble bee", "bumble bees"]

    reason_lower = reason.lower()

    for common_name in common_names:
        if common_name in reason_lower:
            return common_name

    return ""


def parse_species_list(species_answer: str) -> List[str]:
    """
    Parse a species answer string into individual species names.

    Args:
        species_answer: The raw answer from the bee_species field

    Returns:
        List of cleaned species names
    """
    if not species_answer or species_answer.strip() == "":
        return ["Species not specified"]

    # Handle cases where multiple species are listed with numbers
    species_list = []

    # Split by common patterns that indicate multiple species
    # Look for numbered lists or semicolons
    if re.search(r"\d+\.", species_answer):
        # Split by numbered list pattern
        parts = re.split(r"\s*\d+\.\s*", species_answer)
        for part in parts:
            cleaned = clean_species_name(part)
            if cleaned and cleaned != "Species not specified":
                species_list.append(cleaned)
    elif ";" in species_answer:
        # Split by semicolons
        parts = species_answer.split(";")
        for part in parts:
            cleaned = clean_species_name(part)
            if cleaned and cleaned != "Species not specified":
                species_list.append(cleaned)
    else:
        # Single species or other format
        cleaned = clean_species_name(species_answer)
        species_list.append(cleaned)

    return species_list if species_list else ["Species not specified"]


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

        # Extract bee_species answer and reason
        species_answer, reason = extract_bee_species_from_file(file_path)

        if species_answer is None:
            print(f"  No bee_species data found in {file_path}")
            continue

        # Parse species list
        species_list = parse_species_list(species_answer)

        # Add to results
        for species in species_list:
            # Parse species name into components
            genus, species_part, subspecies = parse_species_name(species)

            # Extract common name from reason if species is "Species not specified"
            common_name = ""
            if species == "Species not specified":
                common_name = extract_common_name_from_reason(reason)

            results.append(
                {
                    "paper_id": paper_id,
                    "species_name": species,
                    "genus": genus,
                    "species": species_part,
                    "subspecies": subspecies,
                    "common_name": common_name,
                    "original_answer": species_answer,
                    "reason": reason,
                }
            )

    # Save results to JSON and CSV
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Save full results as JSON (handles multi-line text properly)
    json_file = os.path.join(output_dir, "bee_species_data.json")
    with open(json_file, "w", encoding="utf-8") as jsonfile:
        json.dump(results, jsonfile, indent=2, ensure_ascii=False)

    # Save clean results as CSV (without original_answer and reason to avoid parsing issues)
    csv_file = os.path.join(output_dir, "bee_species_data.csv")
    with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["paper_id", "species_name", "genus", "species", "subspecies", "common_name"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        # Write only clean fields for CSV
        clean_results = [
            {
                "paper_id": r["paper_id"],
                "species_name": r["species_name"],
                "genus": r["genus"],
                "species": r["species"],
                "subspecies": r["subspecies"],
                "common_name": r["common_name"],
            }
            for r in results
        ]
        writer.writerows(clean_results)

    print("\nResults saved to:")
    print(f"  JSON (full data): {json_file}")
    print(f"  CSV (clean): {csv_file}")
    print(f"Total species entries: {len(results)}")

    # Print summary statistics
    unique_species = set(result["species_name"] for result in results)
    papers_with_species = set(result["paper_id"] for result in results)

    print(f"Unique species found: {len(unique_species)}")
    print(f"Papers with species data: {len(papers_with_species)}")

    # Show some examples
    print("\nSample results:")
    for i, result in enumerate(results[:5]):
        if result["common_name"]:
            print(f"  {result['paper_id']}: {result['species_name']} (common: {result['common_name']})")
        else:
            print(
                f"  {result['paper_id']}: {result['species_name']} -> {result['genus']} {result['species']} {result['subspecies']}"
            )

    if len(results) > 5:
        print(f"  ... and {len(results) - 5} more entries")


if __name__ == "__main__":
    main()
