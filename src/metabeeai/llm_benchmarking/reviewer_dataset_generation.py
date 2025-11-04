#!/usr/bin/env python3
"""
Reviewer 1 vs Reviewer 2 Dataset Generation for Creative AI

This script generates a test dataset that compares answers from two different reviewers
for the same questions about bee research papers. The dataset includes:
1. input: the question asked
2. expected_output: reviewer 1 answers (used as gold standard)
3. actual_outputs: reviewer 2 answers (for comparison)
4. metadata: paper ID, question type, and both reviewers' ratings

This dataset is useful for:
- Evaluating inter-reviewer agreement
- Training models to identify consensus vs. disagreement
- Understanding how different reviewers interpret the same questions
"""

import os
import json
import csv
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Rev1vRev2DatasetGenerator:
    def __init__(self):
        """Initialize the Reviewer 1 vs Reviewer 2 Dataset Generator."""
        self.data_dir = os.getenv("METABEEAI_DATA_DIR")
        if not self.data_dir:
            raise ValueError("METABEEAI_DATA_DIR environment variable not set")
        
        self.papers_dir = os.path.join(self.data_dir, "papers")
        self.merged_data_dir = "llm_benchmarking/final_merged_data"
        
        # Load questions mapping
        self.questions = self._load_questions()
        
        # Question ID to field name mapping
        self.question_id_mapping = {
            "bee_species": "bee_species",
            "pesticides": "pesticides", 
            "addional_stressors": "additional_stressors",
            "experimental_methodology": "experimental_methodology",
            "significance": "significance",
            "future_research": "future_research",
            "limitations": "limitations"
        }
        
        logger.info(f"Initialized with data directory: {self.data_dir}")
        logger.info(f"Papers directory: {self.papers_dir}")
    
    def _load_questions(self) -> Dict[str, str]:
        """Load questions from llm_questions.txt."""
        questions_file = "llm_benchmarking/llm_questions.txt"
        questions = {}
        
        try:
            with open(questions_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:
                        # Parse the format: "question_id": "question_text"
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            question_id = parts[0].strip().strip('"')
                            question_text = parts[1].strip().strip('"')
                            questions[question_id] = question_text
        except FileNotFoundError:
            logger.error(f"Questions file not found: {questions_file}")
            raise
        
        logger.info(f"Loaded {len(questions)} questions")
        return questions
    
    def _clean_text(self, text: str) -> str:
        """Clean and sanitize text by removing problematic characters and formatting."""
        if not text:
            return ""
        
        # Remove or replace problematic characters
        cleaned = text
        
        # Replace newlines and carriage returns with spaces
        cleaned = re.sub(r'[\r\n]+', ' ', cleaned)
        
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove or replace problematic characters that can break CSV
        cleaned = cleaned.replace('"', '"')  # Replace smart quotes with regular quotes
        cleaned = cleaned.replace('"', '"')  # Replace smart quotes with regular quotes
        cleaned = cleaned.replace(chr(8217), "'")  # Replace smart apostrophes with regular apostrophes
        
        # Remove or replace other problematic characters
        cleaned = cleaned.replace('–', '-')  # Replace en dash with hyphen
        cleaned = cleaned.replace('—', '-')  # Replace em dash with hyphen
        cleaned = cleaned.replace('…', '...')  # Replace ellipsis with three dots
        
        # Strip leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _validate_text_for_csv(self, text: str) -> bool:
        """Validate that cleaned text is suitable for CSV export."""
        if not text:
            return False
        
        # Check for extremely long text
        if len(text) > 2000:  # More conservative limit for CSV
            return False
        
        return True
    
    def _process_merged_data_file(self, field_name: str) -> List[Dict[str, Any]]:
        """Process a merged data file and extract reviewer comparison entries."""
        merged_file = os.path.join(self.merged_data_dir, f"{field_name}_merged.json")
        comparison_entries = []
        
        try:
            with open(merged_file, 'r', encoding='utf-8') as f:
                merged_data = json.load(f)
                
            question_text = self.questions.get(field_name, f"Question about {field_name}")
            
            for paper_id, paper_data in merged_data.items():
                # Only process entries that have both reviewers
                if "answer_rev1" in paper_data and "answer_rev2" in paper_data:
                    # Check that both answers are not empty
                    if paper_data["answer_rev1"].strip() and paper_data["answer_rev2"].strip():
                        comparison_entry = {
                            "id": paper_id,  # Add paper ID as the main identifier
                            "input": question_text,
                            "expected_output": paper_data["answer_rev1"],  # Reviewer 1 as gold standard
                            "actual_outputs": paper_data["answer_rev2"],   # Reviewer 2 for comparison
                            "metadata": {
                                "paper_id": paper_id,
                                "question_id": field_name,
                                "rev1": paper_data.get("rev1", "Unknown"),
                                "rev2": paper_data.get("rev2", "Unknown"),
                                "rev1_rating": paper_data.get("rev1_rating", 0),
                                "rev2_rating": paper_data.get("rev2_rating", 0)
                            }
                        }
                        comparison_entries.append(comparison_entry)
                    else:
                        logger.debug(f"Skipping paper {paper_id} - one or both answers are empty")
                else:
                    logger.debug(f"Skipping paper {paper_id} - missing one or both reviewers")
                    
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error processing {field_name}: {e}")
        
        return comparison_entries
    
    def _export_to_csv(self, entries: List[Dict[str, Any]], output_file: str) -> None:
        """Export the reviewer comparison dataset to CSV format."""
        csv_file = output_file.replace('.json', '.csv')
        csv_path = os.path.join("llm_benchmarking/test-datasets", csv_file)
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Define the fieldnames for CSV headers
                fieldnames = ['id', 'input', 'expected_output', 'actual_outputs', 'metadata']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                
                # Write the header row
                writer.writeheader()
                
                # Write each entry
                for entry in entries:
                    # Prepare the row data with additional cleaning and validation
                    cleaned_input = self._clean_text(entry['input'])
                    cleaned_expected = self._clean_text(entry['expected_output'])
                    cleaned_actual = self._clean_text(entry['actual_outputs'])
                    
                    # Validate all cleaned text fields
                    if not all([
                        self._validate_text_for_csv(cleaned_input),
                        self._validate_text_for_csv(cleaned_expected),
                        self._validate_text_for_csv(cleaned_actual)
                    ]):
                        logger.warning(f"Skipping entry with invalid cleaned text for paper {entry['metadata'].get('paper_id', 'unknown')}")
                        continue
                    
                    row = {
                        'id': entry['id'],  # Include the paper ID
                        'input': cleaned_input,
                        'expected_output': cleaned_expected,
                        'actual_outputs': cleaned_actual,
                        'metadata': json.dumps(entry['metadata'])  # Convert metadata dict to JSON string
                    }
                    writer.writerow(row)
                
            logger.info(f"CSV file exported successfully: {csv_path}")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def generate_rev1vrev2_dataset(self, output_file: str = "rev_test_dataset.json") -> None:
        """Generate the complete reviewer comparison dataset."""
        all_entries = []
        
        logger.info("Starting reviewer comparison dataset generation...")
        
        for field_name in self.question_id_mapping.values():
            logger.info(f"Processing field: {field_name}")
            entries = self._process_merged_data_file(field_name)
            all_entries.extend(entries)
            logger.info(f"Generated {len(entries)} entries for {field_name}")
        
        # Save the complete dataset as JSON
        output_path = os.path.join("llm_benchmarking/test-datasets", output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_entries, f, indent=2, ensure_ascii=False)
        
        # Export to CSV format
        self._export_to_csv(all_entries, output_file)
        
        logger.info(f"Reviewer comparison dataset generated successfully!")
        logger.info(f"Total entries: {len(all_entries)}")
        logger.info(f"JSON output file: {output_path}")
        logger.info(f"CSV output file: {output_path.replace('.json', '.csv')}")
        
        # Print summary statistics
        self._print_summary_statistics(all_entries)
    
    def _print_summary_statistics(self, entries: List[Dict[str, Any]]) -> None:
        """Print summary statistics for the generated dataset."""
        if not entries:
            logger.warning("No entries generated")
            return
        
        # Count by question type
        question_counts = {}
        rev1_counts = {}
        rev2_counts = {}
        rating_comparison = {}
        
        for entry in entries:
            question = entry["input"]
            rev1 = entry["metadata"]["rev1"]
            rev2 = entry["metadata"]["rev2"]
            rev1_rating = entry["metadata"]["rev1_rating"]
            rev2_rating = entry["metadata"]["rev2_rating"]
            
            question_counts[question] = question_counts.get(question, 0) + 1
            rev1_counts[rev1] = rev1_counts.get(rev1, 0) + 1
            rev2_counts[rev2] = rev2_counts.get(rev2, 0) + 1
            
            # Track rating differences
            rating_diff = rev1_rating - rev2_rating
            if rating_diff not in rating_comparison:
                rating_comparison[rating_diff] = 0
            rating_comparison[rating_diff] += 1
        
        logger.info("\n=== Dataset Summary ===")
        logger.info(f"Total entries: {len(entries)}")
        logger.info(f"Unique questions: {len(question_counts)}")
        logger.info(f"Unique Reviewer 1s: {len(rev1_counts)}")
        logger.info(f"Unique Reviewer 2s: {len(rev2_counts)}")
        
        logger.info("\nEntries per question:")
        for question, count in question_counts.items():
            logger.info(f"  {question[:50]}...: {count}")
        
        logger.info("\nEntries per Reviewer 1:")
        for rev1, count in rev1_counts.items():
            logger.info(f"  {rev1}: {count}")
        
        logger.info("\nEntries per Reviewer 2:")
        for rev2, count in rev2_counts.items():
            logger.info(f"  {rev2}: {count}")
        
        logger.info("\nRating difference distribution (Rev1 - Rev2):")
        for diff in sorted(rating_comparison.keys()):
            count = rating_comparison[diff]
            if diff > 0:
                logger.info(f"  Rev1 higher by {diff}: {count} entries")
            elif diff < 0:
                logger.info(f"  Rev2 higher by {abs(diff)}: {count} entries")
            else:
                logger.info(f"  Same rating: {count} entries")


def main():
    """Main function to run the reviewer comparison dataset generation."""
    try:
        generator = Rev1vRev2DatasetGenerator()
        generator.generate_rev1vrev2_dataset()
    except Exception as e:
        logger.error(f"Error generating reviewer comparison dataset: {e}")
        raise


if __name__ == "__main__":
    main()
