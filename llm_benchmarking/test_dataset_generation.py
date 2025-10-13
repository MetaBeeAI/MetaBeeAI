#!/usr/bin/env python3
"""
Test Dataset Generation for Creative AI

This script generates test datasets using reviewer answers to various questions.
The dataset includes:
1. input: the question asked
2. expected_output: reviewer answers (answer_rev1, answer_rev2 if available)
3. context: relevant text chunks from the papers
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

class TestDatasetGenerator:
    def __init__(self):
        """Initialize the Test Dataset Generator."""
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
    
    def _get_chunk_ids_for_question(self, paper_id: str, question_id: str) -> List[str]:
        """Get chunk IDs for a specific question from answers.json."""
        answers_file = os.path.join(self.papers_dir, paper_id, "answers.json")
        
        try:
            with open(answers_file, 'r', encoding='utf-8') as f:
                answers_data = json.load(f)
                
            # Navigate the nested structure: answers_data -> QUESTIONS -> question_groups -> specific_questions
            if "QUESTIONS" in answers_data:
                questions = answers_data["QUESTIONS"]
                
                # Look for the specific question in various question groups
                for group_key, group_data in questions.items():
                    if isinstance(group_data, dict):
                        # Check if this group contains our question
                        if question_id in group_data:
                            question_data = group_data[question_id]
                            if isinstance(question_data, dict) and "chunk_ids" in question_data:
                                return question_data["chunk_ids"]
                            elif isinstance(question_data, list):
                                return question_data
                        # Also check if the group key itself matches our question
                        elif question_id in group_key:
                            if isinstance(group_data, dict) and "chunk_ids" in group_data:
                                return group_data["chunk_ids"]
                            elif isinstance(group_data, list):
                                return group_data
                                
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not load chunk IDs for paper {paper_id}, question {question_id}: {e}")
        
        return []
    
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
        cleaned = cleaned.replace(''', "'")  # Replace smart apostrophes with regular apostrophes
        cleaned = cleaned.replace(''', "'")  # Replace smart apostrophes with regular apostrophes
        
        # Remove other problematic characters more aggressively
        cleaned = re.sub(r'[^\w\s\.,;:!?()\[\]{}<>@#$%^&*+=|\\/~`-]', '', cleaned)
        
        # Remove HTML-like tags and special formatting
        cleaned = re.sub(r'<[^>]+>', '', cleaned)  # Remove HTML tags
        cleaned = re.sub(r'\*[^*]+\*', '', cleaned)  # Remove markdown emphasis
        cleaned = re.sub(r'#+\s*', '', cleaned)  # Remove markdown headers
        
        # Remove LaTeX-style math expressions
        cleaned = re.sub(r'\$[^$]+\$', '', cleaned)
        cleaned = re.sub(r'\\[a-zA-Z]+', '', cleaned)
        
        # Remove very long sequences of repeated characters
        cleaned = re.sub(r'(.)\1{10,}', r'\1', cleaned)
        
        # Limit text length to prevent extremely long fields
        if len(cleaned) > 1000:
            cleaned = cleaned[:1000] + "... [truncated]"
        
        # Strip leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _get_text_chunks(self, paper_id: str, chunk_ids: List[str]) -> List[str]:
        """Get text chunks from merged_v2.json based on chunk IDs."""
        merged_file = os.path.join(self.papers_dir, paper_id, "pages", "merged_v2.json")
        text_chunks = []
        
        try:
            with open(merged_file, 'r', encoding='utf-8') as f:
                merged_data = json.load(f)
                
            # Navigate the structure: merged_data -> data -> chunks -> list of chunk objects
            if isinstance(merged_data, dict) and "data" in merged_data:
                data = merged_data["data"]
                if isinstance(data, dict) and "chunks" in data:
                    chunks = data["chunks"]
                    
                    if isinstance(chunks, list):
                        # Chunks is a list of chunk objects
                        for chunk in chunks:
                            if isinstance(chunk, dict):
                                chunk_id = chunk.get("chunk_id") or chunk.get("chunk_ID")
                                if chunk_id in chunk_ids:
                                    text = chunk.get("text", "")
                                    if text:
                                        # Clean the text before adding
                                        cleaned_text = self._clean_text(text)
                                        if cleaned_text and cleaned_text not in text_chunks:
                                            text_chunks.append(cleaned_text)
                    elif isinstance(chunks, dict):
                        # Chunks is a dict with chunk_id as keys
                        for chunk_id, chunk_data in chunks.items():
                            if chunk_id in chunk_ids:
                                if isinstance(chunk_data, dict) and "text" in chunk_data:
                                    text = chunk_data["text"]
                                    if text:
                                        # Clean the text before adding
                                        cleaned_text = self._clean_text(text)
                                        if cleaned_text and cleaned_text not in text_chunks:
                                            text_chunks.append(cleaned_text)
                                elif isinstance(chunk_data, str):
                                    if chunk_data:
                                        # Clean the text before adding
                                        cleaned_text = self._clean_text(chunk_data)
                                        if cleaned_text and cleaned_text not in text_chunks:
                                            text_chunks.append(cleaned_text)
                                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load merged data for paper {paper_id}: {e}")
        
        return text_chunks
    
    def _get_all_text_chunks(self, paper_id: str) -> List[str]:
        """Get all text chunks from merged_v2.json for the full paper context."""
        merged_file = os.path.join(self.papers_dir, paper_id, "pages", "merged_v2.json")
        all_text_chunks = []
        
        try:
            with open(merged_file, 'r', encoding='utf-8') as f:
                merged_data = json.load(f)
                
            # Navigate the structure: merged_data -> data -> chunks -> list of chunk objects
            if isinstance(merged_data, dict) and "data" in merged_data:
                data = merged_data["data"]
                if isinstance(data, dict) and "chunks" in data:
                    chunks = data["chunks"]
                    
                    if isinstance(chunks, list):
                        # Chunks is a list of chunk objects
                        for chunk in chunks:
                            if isinstance(chunk, dict):
                                # Only include chunks with chunk_type "text"
                                if chunk.get("chunk_type") == "text":
                                    text = chunk.get("text", "")
                                    if text:
                                        # Clean the text before adding
                                        cleaned_text = self._clean_text(text)
                                        if cleaned_text and cleaned_text not in all_text_chunks:
                                            all_text_chunks.append(cleaned_text)
                    elif isinstance(chunks, dict):
                        # Chunks is a dict with chunk_id as keys
                        for chunk_id, chunk_data in chunks.items():
                            if isinstance(chunk_data, dict):
                                # Only include chunks with chunk_type "text"
                                if chunk_data.get("chunk_type") == "text":
                                    text = chunk_data.get("text", "")
                                    if text:
                                        # Clean the text before adding
                                        cleaned_text = self._clean_text(text)
                                        if cleaned_text and cleaned_text not in all_text_chunks:
                                            all_text_chunks.append(cleaned_text)
                                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load merged data for paper {paper_id}: {e}")
        
        return all_text_chunks
    
    def _deduplicate_contexts(self, full_context: List[str], retrieval_context: List[str]) -> tuple[List[str], List[str]]:
        """Remove duplicate text between full context and retrieval context, prioritizing retrieval context."""
        # Create a set of all text in retrieval context for fast lookup
        retrieval_set = set(retrieval_context)
        
        # Remove any text from full context that appears in retrieval context
        deduplicated_full = []
        for text in full_context:
            if text not in retrieval_set:
                deduplicated_full.append(text)
        
        return deduplicated_full, retrieval_context
    
    def _validate_cleaned_text(self, text: str) -> bool:
        """Validate that cleaned text is safe for CSV export."""
        if not text:
            return False
        
        # Check for problematic characters that could break CSV parsing
        problematic_chars = ['\n', '\r', '\t', '"', '\\']
        for char in problematic_chars:
            if char in text:
                return False
        
        # Check for extremely long text
        if len(text) > 2000:  # More conservative limit for CSV
            return False
        
        return True
    
    def _process_merged_data_file(self, field_name: str) -> List[Dict[str, Any]]:
        """Process a merged data file and extract test dataset entries."""
        merged_file = os.path.join(self.merged_data_dir, f"{field_name}_merged.json")
        test_entries = []
        
        try:
            with open(merged_file, 'r', encoding='utf-8') as f:
                merged_data = json.load(f)
                
            question_text = self.questions.get(field_name, f"Question about {field_name}")
            
            for paper_id, paper_data in merged_data.items():
                # Get context chunks for this paper and question (retrieval context)
                chunk_ids = self._get_chunk_ids_for_question(paper_id, field_name)
                retrieval_chunks = self._get_text_chunks(paper_id, chunk_ids)
                
                # Get all text chunks from the paper (full context)
                full_context_chunks = self._get_all_text_chunks(paper_id)
                
                # Deduplicate contexts to avoid overlap between full context and retrieval context
                deduplicated_full, deduplicated_retrieval = self._deduplicate_contexts(full_context_chunks, retrieval_chunks)
                
                # Log deduplication results for debugging
                if len(full_context_chunks) != len(deduplicated_full):
                    logger.info(f"Paper {paper_id}: Removed {len(full_context_chunks) - len(deduplicated_full)} duplicate chunks between full and retrieval context")
                
                # Get LLM answer if available
                llm_answer = paper_data.get("answer_llm", "")
                
                # Create entry for reviewer 1
                if "answer_rev1" in paper_data:
                    test_entry = {
                        "id": paper_id,  # Add paper ID as the main identifier
                        "input": question_text,
                        "expected_output": paper_data["answer_rev1"],
                        "actual_outputs": llm_answer,
                        "context": deduplicated_full,  # Full paper context (deduplicated)
                        "retrieval_context": deduplicated_retrieval,  # Chunks actually used by LLM
                        "metadata": {
                            "paper_id": paper_id,
                            "question_id": field_name,
                            "reviewer": paper_data.get("rev1", "Unknown"),
                            "rating": paper_data.get("rev1_rating", 0)
                        }
                    }
                    test_entries.append(test_entry)
                
                # Create entry for reviewer 2 if available
                if "answer_rev2" in paper_data:
                    test_entry = {
                        "id": paper_id,  # Add paper ID as the main identifier
                        "input": question_text,
                        "expected_output": paper_data["answer_rev2"],
                        "actual_outputs": llm_answer,
                        "context": deduplicated_full,  # Full paper context (deduplicated)
                        "retrieval_context": deduplicated_retrieval,  # Chunks actually used by LLM
                        "metadata": {
                            "paper_id": paper_id,
                            "question_id": field_name,
                            "reviewer": paper_data.get("rev2", "Unknown"),
                            "rating": paper_data.get("rev2_rating", 0)
                        }
                    }
                    test_entries.append(test_entry)
                    
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error processing {field_name}: {e}")
        
        return test_entries
    
    def _export_to_csv(self, entries: List[Dict[str, Any]], output_file: str) -> None:
        """Export the test dataset to CSV format."""
        csv_file = output_file.replace('.json', '.csv')
        csv_path = os.path.join("llm_benchmarking/test-datasets", csv_file)
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Define the fieldnames for CSV headers
                fieldnames = ['id', 'input', 'expected_output', 'actual_outputs', 'context', 'retrieval_context', 'metadata']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                
                # Write the header row
                writer.writeheader()
                
                # Write each entry
                for entry in entries:
                    # Prepare the row data with additional cleaning and validation
                    cleaned_input = self._clean_text(entry['input'])
                    cleaned_expected = self._clean_text(entry['expected_output'])
                    cleaned_actual = self._clean_text(entry['actual_outputs'])
                    cleaned_context = self._clean_text(' | '.join(entry['context']) if entry['context'] else '')
                    cleaned_retrieval = self._clean_text(' | '.join(entry['retrieval_context']) if entry['retrieval_context'] else '')
                    
                    # Validate all cleaned text fields
                    if not all([
                        self._validate_cleaned_text(cleaned_input),
                        self._validate_cleaned_text(cleaned_expected),
                        self._validate_cleaned_text(cleaned_actual),
                        self._validate_cleaned_text(cleaned_context),
                        self._validate_cleaned_text(cleaned_retrieval)
                    ]):
                        logger.warning(f"Skipping entry with invalid cleaned text for paper {entry['metadata'].get('paper_id', 'unknown')}")
                        continue
                    
                    row = {
                        'id': entry['id'],  # Include the paper ID
                        'input': cleaned_input,
                        'expected_output': cleaned_expected,
                        'actual_outputs': cleaned_actual,
                        'context': cleaned_context,  # Full paper context
                        'retrieval_context': cleaned_retrieval,  # Chunks used by LLM
                        'metadata': json.dumps(entry['metadata'])  # Convert metadata dict to JSON string
                    }
                    writer.writerow(row)
                
            logger.info(f"CSV file exported successfully: {csv_path}")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def generate_test_dataset(self, output_file: str = "test_dataset.json") -> None:
        """Generate the complete test dataset."""
        all_entries = []
        
        logger.info("Starting test dataset generation...")
        
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
        
        logger.info(f"Test dataset generated successfully!")
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
        reviewer_counts = {}
        rating_distribution = {}
        
        for entry in entries:
            question = entry["input"]
            reviewer = entry["metadata"]["reviewer"]
            rating = entry["metadata"]["rating"]
            
            question_counts[question] = question_counts.get(question, 0) + 1
            reviewer_counts[reviewer] = reviewer_counts.get(reviewer, 0) + 1
            rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
        
        logger.info("\n=== Dataset Summary ===")
        logger.info(f"Total entries: {len(entries)}")
        logger.info(f"Unique questions: {len(question_counts)}")
        logger.info(f"Unique reviewers: {len(reviewer_counts)}")
        
        logger.info("\nEntries per question:")
        for question, count in question_counts.items():
            logger.info(f"  {question[:50]}...: {count}")
        
        logger.info("\nEntries per reviewer:")
        for reviewer, count in reviewer_counts.items():
            logger.info(f"  {reviewer}: {count}")
        
        logger.info("\nRating distribution:")
        for rating in sorted(rating_distribution.keys()):
            count = rating_distribution[rating]
            logger.info(f"  Rating {rating}: {count} entries")


def main():
    """Main function to run the test dataset generation."""
    try:
        generator = TestDatasetGenerator()
        generator.generate_test_dataset()
    except Exception as e:
        logger.error(f"Error generating test dataset: {e}")
        raise


if __name__ == "__main__":
    main()
