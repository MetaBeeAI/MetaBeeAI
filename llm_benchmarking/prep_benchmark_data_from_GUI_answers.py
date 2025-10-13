"""
Prepare benchmarking data using reviewer answers from answers_extended.json (GUI output).

This script extracts question-answer pairs from papers where reviewers have used
the GUI to provide answers in answers_extended.json files.
"""

import json
import os
import sys
import yaml
from pathlib import Path

# Add parent directory to path to access config
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from config import get_papers_dir, get_data_dir


def load_questions_from_yml(questions_yml_path):
    """Load questions from the questions.yml file."""
    with open(questions_yml_path, 'r') as f:
        questions_config = yaml.safe_load(f)
    
    questions = {}
    if 'QUESTIONS' in questions_config:
        for question_key, question_data in questions_config['QUESTIONS'].items():
            if isinstance(question_data, dict) and 'question' in question_data:
                questions[question_key] = question_data['question']
    
    return questions


def load_merged_json(paper_path):
    """Load the merged_v2.json file containing all text chunks."""
    merged_path = os.path.join(paper_path, "pages", "merged_v2.json")
    
    if not os.path.exists(merged_path):
        return None
    
    with open(merged_path, 'r') as f:
        merged_data = json.load(f)
    
    return merged_data


def get_text_chunks(merged_data):
    """Extract all text chunks from merged_v2.json."""
    if not merged_data or 'data' not in merged_data or 'chunks' not in merged_data['data']:
        return {}
    
    # Create a mapping of chunk_id to text
    chunk_map = {}
    for chunk in merged_data['data']['chunks']:
        if 'chunk_id' in chunk and 'text' in chunk:
            chunk_map[chunk['chunk_id']] = chunk['text']
    
    return chunk_map


def get_retrieval_context(chunk_map, chunk_ids):
    """Get the text for specific chunk IDs (retrieval context)."""
    if not chunk_ids:
        return []
    
    retrieval_texts = []
    for chunk_id in chunk_ids:
        if chunk_id in chunk_map:
            retrieval_texts.append(chunk_map[chunk_id])
    
    return retrieval_texts


def extract_question_name(question_path):
    """
    Extract the final question name from a nested path like 'welfare' or 'design'
    Returns the last part after any dots.
    """
    return question_path.split('.')[-1]


def extract_llm_answer_data(answers_dict, question_key):
    """Extract LLM answer, chunk_ids from the answers dictionary."""
    # Navigate the nested structure
    if 'QUESTIONS' in answers_dict:
        questions_root = answers_dict['QUESTIONS']
        
        # Check outer level first
        if question_key in questions_root:
            answer_data = questions_root[question_key]
        # Check nested QUESTIONS level
        elif 'QUESTIONS' in questions_root and question_key in questions_root['QUESTIONS']:
            answer_data = questions_root['QUESTIONS'][question_key]
        else:
            return None, []
    else:
        # Old format - direct access
        if question_key in answers_dict:
            answer_data = answers_dict[question_key]
        else:
            return None, []
    
    if isinstance(answer_data, dict):
        answer = answer_data.get('answer', '')
        chunk_ids = answer_data.get('chunk_ids', [])
        return answer, chunk_ids
    else:
        return str(answer_data), []


def extract_reviewer_answer(extended_data, question_key):
    """Extract reviewer answer from answers_extended.json."""
    if 'QUESTIONS' not in extended_data:
        return None
    
    questions = extended_data['QUESTIONS']
    
    # Try direct access first
    if question_key in questions:
        question_data = questions[question_key]
        if isinstance(question_data, dict):
            return question_data.get('user_answer_positive', '')
    
    # Try with nested paths (in case question_key is just the last part)
    for full_path, question_data in questions.items():
        if extract_question_name(full_path) == question_key:
            if isinstance(question_data, dict):
                return question_data.get('user_answer_positive', '')
    
    return None


def prepare_benchmark_data(papers_dir, questions_yml_path, output_path):
    """
    Prepare benchmarking data by extracting questions, answers, and context.
    Uses answers_extended.json for reviewer answers.
    
    Args:
        papers_dir: Path to the directory containing paper folders
        questions_yml_path: Path to questions.yml file
        output_path: Path to save the output JSON file
    """
    # Load questions from yml
    questions = load_questions_from_yml(questions_yml_path)
    
    print(f"📊 Loading questions from: {questions_yml_path}")
    print(f"📁 Papers directory: {papers_dir}")
    print(f"❓ Found {len(questions)} questions: {list(questions.keys())}")
    print("=" * 60)
    
    benchmark_data = []
    papers_processed = 0
    papers_skipped = 0
    
    # Iterate through paper folders
    for paper_id in sorted(os.listdir(papers_dir)):
        paper_path = os.path.join(papers_dir, paper_id)
        
        # Skip non-directories and hidden folders
        if not os.path.isdir(paper_path) or paper_id.startswith('.'):
            continue
        
        print(f"\n🔄 Processing paper: {paper_id}")
        
        # Check if answers_extended.json exists (papers with GUI reviewer answers)
        extended_answers_path = os.path.join(paper_path, "answers_extended.json")
        answers_path = os.path.join(paper_path, "answers.json")
        
        if not os.path.exists(extended_answers_path):
            print(f"  ⏭️  Skipping (no answers_extended.json)")
            papers_skipped += 1
            continue
        
        if not os.path.exists(answers_path):
            print(f"  ⚠️  Warning: No answers.json found")
            papers_skipped += 1
            continue
        
        # Load the answers
        with open(extended_answers_path, 'r') as f:
            extended_answers = json.load(f)
        
        with open(answers_path, 'r') as f:
            llm_answers = json.load(f)
        
        # Load merged_v2.json for context
        merged_data = load_merged_json(paper_path)
        if not merged_data:
            print(f"  ⚠️  Warning: No merged_v2.json found")
            papers_skipped += 1
            continue
        
        # Get all text chunks
        chunk_map = get_text_chunks(merged_data)
        all_context = list(chunk_map.values())
        
        print(f"  📄 Found {len(chunk_map)} text chunks")
        
        # Process each question
        for question_key, question_text in questions.items():
            # Extract LLM answer
            llm_answer, llm_chunk_ids = extract_llm_answer_data(llm_answers, question_key)
            
            # Extract reviewer answer from answers_extended.json
            reviewer_answer = extract_reviewer_answer(extended_answers, question_key)
            
            # Only include if we have both LLM and reviewer answers
            if not llm_answer or not reviewer_answer:
                print(f"  ⏭️  Skipping {question_key} (missing LLM or reviewer answer)")
                continue
            
            # Get retrieval context
            retrieval_context = get_retrieval_context(chunk_map, llm_chunk_ids)
            
            # Create benchmark data entry (same format as prep_benchmark_data.py)
            entry = {
                "paper_id": paper_id,
                "question_key": question_key,
                "input": question_text,
                "actual_output": llm_answer,
                "expected_output": reviewer_answer,
                "context": all_context,
                "retrieval_context": retrieval_context,
                "chunk_ids": llm_chunk_ids
            }
            
            benchmark_data.append(entry)
            print(f"  ✅ Added {question_key} (LLM: {len(llm_answer)} chars, Reviewer: {len(reviewer_answer)} chars, Retrieval: {len(retrieval_context)} chunks)")
        
        papers_processed += 1
    
    # Save to JSON file
    with open(output_path, 'w') as f:
        json.dump(benchmark_data, f, indent=2)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"🎉 BENCHMARK DATA PREPARATION COMPLETED!")
    print(f"✅ Papers processed: {papers_processed}")
    print(f"⏭️  Papers skipped: {papers_skipped}")
    print(f"📊 Total benchmark entries: {len(benchmark_data)}")
    print(f"💾 Output saved to: {output_path}")
    
    # Print statistics by question type
    print("\n📈 Entries by question type:")
    question_counts = {}
    for entry in benchmark_data:
        q_key = entry['question_key']
        question_counts[q_key] = question_counts.get(q_key, 0) + 1
    
    for q_key, count in sorted(question_counts.items()):
        print(f"  - {q_key}: {count} entries")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Prepare benchmarking data from papers with GUI reviewer answers (answers_extended.json)"
    )
    parser.add_argument(
        "--papers-dir",
        type=str,
        default=None,
        help="Base directory containing paper folders (default: auto-detect from config)"
    )
    parser.add_argument(
        "--questions-yml",
        type=str,
        default=None,
        help="Path to questions.yml file (default: ../metabeeai_llm/questions.yml)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: data/benchmark_data_gui.json)"
    )
    
    args = parser.parse_args()
    
    # Set defaults
    if args.papers_dir is None:
        args.papers_dir = get_papers_dir()
    
    if args.questions_yml is None:
        args.questions_yml = os.path.join(parent_dir, "metabeeai_llm", "questions.yml")
    
    if args.output is None:
        args.output = os.path.join(get_data_dir(), "benchmark_data_gui.json")
    
    # Run the preparation
    prepare_benchmark_data(args.papers_dir, args.questions_yml, args.output)
