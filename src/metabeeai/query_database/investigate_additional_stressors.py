#!/usr/bin/env python3
"""
Script to investigate additional stressors data from answers.json files.
Extracts additional stressors information and saves to both JSON and CSV formats.
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


def extract_stressor_names(stressors_answer: str) -> List[Dict[str, str]]:
    """
    Extract stressor names and types from an additional stressors answer string.
    Returns empty list for negative responses like "No additional stressors were tested".

    Args:
        stressors_answer: The raw answer from the additional_stressors field

    Returns:
        List of dictionaries with 'stressor_type' and 'stressor_name' keys
    """
    if not stressors_answer or stressors_answer.strip() == "":
        return []

    # Check for negative responses indicating no additional stressors were tested
    negative_responses = [
        "no additional stressors were tested",
        "no additional stressors tested",
        "no additional stressors were used",
        "no additional stressors used",
        "no additional stressors specified",
        "no additional stressors mentioned",
        "no additional stressors found",
        "additional stressors not tested",
        "additional stressors not used",
        "additional stressors not specified",
        "additional stressors not mentioned",
        "no stressors were tested",
        "no stressors tested",
        "no stressors were used",
        "no stressors used",
        "no stressors specified",
        "no stressors mentioned",
        "no stressors found",
        "stressors not tested",
        "stressors not used",
        "stressors not specified",
        "stressors not mentioned",
        "no additional environmental stressors",
        "no environmental stressors",
    ]

    answer_lower = stressors_answer.lower().strip()

    # Check if the answer indicates no additional stressors were tested
    for negative_response in negative_responses:
        if negative_response in answer_lower:
            return []

    stressor_data = []

    # Enhanced pattern to capture more detailed information
    # Pattern: "1. Stressor Type: Specific Name" or "1. Stressor Type: Specific Name, details..."
    pattern = r"\d+\.\s*([^:]+?):\s*([^,\n;]+?)(?=,|\n|;|$)"

    matches = re.findall(pattern, stressors_answer, re.MULTILINE)

    for stressor_type, stressor_details in matches:
        # Clean up the stressor type
        stressor_type_clean = stressor_type.strip()
        stressor_type_clean = re.sub(r"[.,;:!?]+$", "", stressor_type_clean).strip()

        # Clean up the stressor details
        stressor_details_clean = stressor_details.strip()
        stressor_details_clean = re.sub(r"[.,;:!?]+$", "", stressor_details_clean).strip()

        # Extract specific stressor name from details
        specific_name = extract_specific_stressor_name(stressor_details_clean)

        if stressor_type_clean and specific_name:
            stressor_data.append(
                {"stressor_type": standardize_stressor_type(stressor_type_clean), "stressor_name": specific_name}
            )

    # If no enhanced pattern found, try the original simple pattern
    if not stressor_data:
        simple_pattern = r"\d+\.\s*([^,:;]+?)(?=:|,|;)"
        matches = re.findall(simple_pattern, stressors_answer)

        for match in matches:
            stressor_name = match.strip()
            stressor_name = re.sub(r"[.,;:!?]+$", "", stressor_name).strip()

            if stressor_name and is_valid_stressor_name(stressor_name):
                # Try to infer stressor type from the name
                stressor_type = infer_stressor_type(stressor_name)
                stressor_data.append(
                    {"stressor_type": stressor_type, "stressor_name": standardize_stressor_name(stressor_name)}
                )

    return stressor_data


def extract_specific_stressor_name(stressor_details: str) -> str:
    """
    Extract specific stressor name from detailed description.

    Args:
        stressor_details: The detailed description of the stressor

    Returns:
        Specific stressor name
    """
    if not stressor_details:
        return ""

    # Look for scientific names in italics (e.g., *Varroa destructor*)
    italic_pattern = r"\*([^*]+)\*"
    italic_matches = re.findall(italic_pattern, stressor_details)
    if italic_matches:
        return italic_matches[0].strip()

    # Look for common patterns like "X infection", "X virus", "X stress"
    patterns = [
        r"([A-Za-z][A-Za-z0-9\s\-]+?)\s+(?:infection|virus|stress|exposure)",
        r"([A-Za-z][A-Za-z0-9\s\-]+?)\s+(?:cells|mg|ppm|ppb|μg|ng)",
        r"([A-Za-z][A-Za-z0-9\s\-]+?)\s+(?:°C|°F|temperature)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, stressor_details, re.IGNORECASE)
        if matches:
            return matches[0].strip()

    # If no specific pattern found, take the first meaningful phrase
    words = stressor_details.split()
    meaningful_words = []

    for word in words[:5]:  # Limit to first 5 words
        word_clean = re.sub(r"[^\w\-]", "", word)
        if len(word_clean) > 2 and not word_clean.isdigit():
            meaningful_words.append(word_clean)

    return " ".join(meaningful_words) if meaningful_words else stressor_details.strip()


def standardize_stressor_type(stressor_type: str) -> str:
    """
    Standardize stressor type into the 5 allowed categories.

    Args:
        stressor_type: Raw stressor type

    Returns:
        Standardized stressor type (parasite, pathogen, temperature, chemical, other)
    """
    if not stressor_type:
        return "other"

    stressor_type_lower = stressor_type.lower().strip()

    # Define category mappings to the 5 allowed categories
    type_mappings = {
        # Parasite category
        "parasite": "parasite",
        "parasitic": "parasite",
        # Pathogen category
        "pathogen": "pathogen",
        "pathogenic": "pathogen",
        "virus": "pathogen",
        "viral": "pathogen",
        "bacterial": "pathogen",
        "fungal": "pathogen",
        # Temperature category
        "temperature": "temperature",
        "thermal": "temperature",
        "heat": "temperature",
        "cold": "temperature",
        # Chemical category
        "chemical": "chemical",
        "heavy metal": "chemical",
        "metal": "chemical",
        "pesticide": "chemical",
        "herbicide": "chemical",
        "fungicide": "chemical",
        "insecticide": "chemical",
    }

    # Check for exact matches first
    if stressor_type_lower in type_mappings:
        return type_mappings[stressor_type_lower]

    # Check for partial matches
    for key, value in type_mappings.items():
        if key in stressor_type_lower:
            return value

    # Everything else goes to "other"
    return "other"


def infer_stressor_type(stressor_name: str) -> str:
    """
    Infer stressor type from stressor name when type is not explicitly given.

    Args:
        stressor_name: The stressor name

    Returns:
        Inferred stressor type (parasite, pathogen, temperature, chemical, other)
    """
    if not stressor_name:
        return "other"

    stressor_name_lower = stressor_name.lower()

    # Common stressor name patterns
    if any(word in stressor_name_lower for word in ["varroa", "nosema", "crithidia", "tracheal", "mite"]):
        return "parasite"
    elif any(word in stressor_name_lower for word in ["virus", "disease", "infection", "bacteria", "fungus"]):
        return "pathogen"
    elif any(word in stressor_name_lower for word in ["temperature", "heat", "cold", "thermal", "°c", "°f"]):
        return "temperature"
    elif any(word in stressor_name_lower for word in ["chemical", "metal", "pesticide", "herbicide", "hg", "cd", "pb"]):
        return "chemical"

    return "other"


def refine_stressor_with_llm(paper_id: str, stressor_type: str, stressor_name: str, original_answer: str) -> Dict[str, str]:
    """
    Use GPT-4 to refine and standardize stressor extraction.

    Args:
        paper_id: Paper ID for context
        stressor_type: Current stressor type
        stressor_name: Current stressor name
        original_answer: Original answer text for context

    Returns:
        Dictionary with refined 'stressor_type' and 'stressor_name'
    """
    if not stressor_name or not original_answer or not OPENAI_AVAILABLE:
        return {"stressor_type": stressor_type, "stressor_name": stressor_name}

    try:
        # Load environment variables (including OpenAI API key)
        load_env_file()

        # Check if API key is available
        if not os.getenv("OPENAI_API_KEY"):
            print(f"  Warning: OPENAI_API_KEY not found in environment for paper {paper_id}")
            return {"stressor_type": stressor_type, "stressor_name": stressor_name}

        # Initialize OpenAI client
        client = openai.OpenAI()

        prompt = f"""
You are an expert at extracting and categorizing biological stressors from scientific text.

TASK: Refine the current stressor extraction by finding the BEST MATCH in the original text.

ORIGINAL TEXT: {original_answer}

CURRENT EXTRACTION TO REFINE:
- Type: {stressor_type}
- Name: {stressor_name}

REQUIREMENTS:
1. Find the stressor in the original text that BEST MATCHES the current extraction
2. Extract the ACTUAL stressor name (not units, durations, or containers)
3. Categorize into exactly one of these 5 types:
   - "parasite" (e.g., Varroa destructor, Nosema, Crithidia)
   - "pathogen" (e.g., viruses, bacteria, fungi)
   - "temperature" (e.g., heat, cold, thermal stress)
   - "chemical" (e.g., pesticides, metals, toxins)
   - "other" (anything else)

4. Return ONLY the BEST MATCH, not all stressors

EXAMPLES:
- Current: "for hour" from "4°C for 1 hour" → temperature, "4°C"
- Current: "pollen mixture" from "HgCl₂ in pollen mixture" → chemical, "HgCl₂"
- Current: "mJcm²" from "UV light exposure: 30 mJ/cm²" → other, "UV light"
- Current: "32C" from "Temperature stress: 32°C" → temperature, "32°C"

Return ONLY a JSON object with "type" and "name" keys for the best match. If no good match found,
return {{"type": "{stressor_type}", "name": "{stressor_name}"}}.
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a scientific data extraction expert. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=500,
        )

        # Parse the response
        response_text = response.choices[0].message.content.strip()

        # Extract JSON from response (in case there's extra text)
        # Try to find either an object {...} or array [...]
        object_match = re.search(r"\{[^}]*\}", response_text, re.DOTALL)
        array_match = re.search(r"\[.*\]", response_text, re.DOTALL)

        if object_match:
            stressor = json.loads(object_match.group())
            return {"stressor_type": stressor.get("type", "other"), "stressor_name": stressor.get("name", stressor_name)}
        elif array_match:
            stressors = json.loads(array_match.group())
            if stressors and len(stressors) > 0:
                # Return the first stressor from array
                first_stressor = stressors[0]
                return {
                    "stressor_type": first_stressor.get("type", "other"),
                    "stressor_name": first_stressor.get("name", stressor_name),
                }

    except Exception as e:
        print(f"GPT-4 processing failed for paper {paper_id}: {e}")

    # Fallback to original values
    return {"stressor_type": stressor_type, "stressor_name": stressor_name}


def standardize_stressor_name(name: str) -> str:
    """
    Standardize stressor name by keeping only the first word or hyphenated compound words,
    and converting to lowercase.

    Args:
        name: Raw stressor name

    Returns:
        Standardized stressor name in lowercase
    """
    if not name:
        return ""

    # Split by spaces and take the first part
    first_part = name.split()[0] if name.split() else ""

    # Check if it's a hyphenated compound (like "Temperature stress" -> "temperature")
    # For now, we'll just take the first word before any "+" or "-" that separates different stressors
    if "+" in first_part:
        first_part = first_part.split("+")[0].strip()
    elif " + " in name:
        # Handle cases like "Parasite + Pathogen stress"
        first_part = name.split(" + ")[0].strip()

    # Remove any remaining punctuation and convert to lowercase
    first_part = re.sub(r"[^\w\-]", "", first_part)

    return first_part.lower()


def is_valid_stressor_name(name: str) -> bool:
    """
    Check if a string is likely a valid stressor name.

    Args:
        name: String to check

    Returns:
        True if likely a stressor name, False otherwise
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

    # Skip common non-stressor words that might be extracted
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
        "stress",
        "stressor",
        "additional",
        "environmental",
        "factors",
        "conditions",
    ]

    if name.lower() in skip_words:
        return False

    # Skip words that are mostly numbers with letters (like "da⁻¹")
    if re.search(r"\d+", name) and len(re.findall(r"[a-zA-Z]", name)) <= 2:
        return False

    # Must start with a letter
    if not name[0].isalpha():
        return False

    # Accept common stressor abbreviations and short forms
    if len(name) >= 2 and len(name) <= 4 and name.isupper() and name.isalpha():
        return True

    # For longer names, require at least 3 characters
    if len(name) >= 3:
        return True

    return False


def main():
    """Main function to process all answers.json files and create CSV output."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Extract additional stressors data")
    parser.add_argument("--no-llm", action="store_true", help="Skip GPT-4 refinement")
    parser.add_argument("--test-papers", type=int, help="Process only first N papers for testing")
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
    use_llm_refinement = not args.no_llm
    if use_llm_refinement:
        print("GPT-4 refinement enabled")
    else:
        print("GPT-4 refinement disabled")

    results = []

    for paper_id, file_path in answers_files:
        print(f"Processing paper {paper_id}...")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract additional stressors information
            questions = data.get("QUESTIONS", {})
            stressors_data = questions.get("additional_stressors", {})
            stressors_answer = stressors_data.get("answer", "")
            reason = stressors_data.get("reason", "")

            stressor_data = extract_stressor_names(stressors_answer)

            # Handle empty results (no stressors found)
            if not stressor_data:
                results.append(
                    {
                        "paper_id": paper_id,
                        "stressor_type": "",
                        "stressor_name": "",
                        "original_answer": stressors_answer,
                        "reason": reason,
                    }
                )
            else:
                # Add all stressor data to results
                for stressor in stressor_data:
                    stressor_type = stressor["stressor_type"]
                    stressor_name = stressor["stressor_name"]

                    # Apply GPT-4 refinement if enabled
                    if use_llm_refinement and stressor_name:
                        print(f"  Refining stressor: {stressor_type} - {stressor_name}")
                        refined = refine_stressor_with_llm(paper_id, stressor_type, stressor_name, stressors_answer)
                        stressor_type = refined["stressor_type"]
                        stressor_name = refined["stressor_name"]
                        print(f"  Refined to: {stressor_type} - {stressor_name}")

                    results.append(
                        {
                            "paper_id": paper_id,
                            "stressor_type": stressor_type,
                            "stressor_name": stressor_name,
                            "original_answer": stressors_answer,
                            "reason": reason,
                        }
                    )

        except Exception as e:
            print(f"Error processing {paper_id}: {e}")
            continue

    # Save results to JSON and CSV
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Save full results as JSON (handles multi-line text properly)
    json_file = os.path.join(output_dir, "additional_stressors_data.json")
    with open(json_file, "w", encoding="utf-8") as jsonfile:
        json.dump(results, jsonfile, indent=2, ensure_ascii=False)

    print("\nResults saved to:")
    print(f"  JSON (full data): {json_file}")
    print(f"Total stressor entries: {len(results)}")

    # Print summary statistics
    unique_stressors = set(result["stressor_name"] for result in results if result["stressor_name"])
    unique_types = set(result["stressor_type"] for result in results if result["stressor_type"])
    papers_with_stressors = set(result["paper_id"] for result in results if result["stressor_name"])

    print(f"Unique stressors found: {len(unique_stressors)}")
    print(f"Unique stressor types: {len(unique_types)}")
    print(f"Papers with stressor data: {len(papers_with_stressors)}")

    # Show stressor type breakdown
    print("\nStressor type breakdown:")
    type_counts = {}
    for result in results:
        if result["stressor_type"]:
            type_counts[result["stressor_type"]] = type_counts.get(result["stressor_type"], 0) + 1

    for stressor_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {stressor_type}: {count}")

    # Show sample results
    print("\nSample results:")
    for i, result in enumerate(results[:10]):
        if result["stressor_name"]:  # Only show non-empty entries
            print(f"  {result['paper_id']}: {result['stressor_type']} - {result['stressor_name']}")

    if len([r for r in results if r["stressor_name"]]) > 10:
        print(f"  ... and {len([r for r in results if r['stressor_name']]) - 10} more entries")


if __name__ == "__main__":
    main()
