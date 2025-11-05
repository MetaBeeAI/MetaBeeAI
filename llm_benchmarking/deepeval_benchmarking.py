"""
DeepEval benchmarking script that evaluates LLM outputs against GUI reviewer answers.

Reads from benchmark_data_gui.json (output from prep_benchmark_data.py)
and compares LLM-generated answers (actual_output) with reviewer answers (expected_output)
from the GUI interface.
"""

import json
import os
import sys
import argparse
import datetime
from dotenv import load_dotenv

# Add parent directory to path to access config
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from config import get_data_dir

# Load environment variables from .env file
load_dotenv()

# Set up command line argument parsing
parser = argparse.ArgumentParser(description='Evaluate benchmark dataset with DeepEval (Standard + G-Eval)')
parser.add_argument('--question', '-q', 
                   type=str,
                   help='Question key to filter by (optional - if not specified, processes all questions). Must match a question_key from the benchmark data.')
parser.add_argument('--input', '-i', type=str, default=None,
                   help='Input benchmark data file (default: auto-detect from config)')
parser.add_argument('--limit', '-l', type=int, 
                   help='Maximum number of test cases to process (optional)')
parser.add_argument('--batch-size', '-b', type=int, default=25,
                   help='Number of test cases to process per batch (default: 25)')
parser.add_argument('--max-retries', '-r', type=int, default=5,
                   help='Maximum retries per batch (default: 5)')
parser.add_argument('--model', '-m', type=str, default='gpt-4o',
                   choices=['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
                   help='OpenAI model to use for evaluation (default: gpt-4o)')
parser.add_argument('--max-context-length', type=int, default=200000,
                   help='Maximum context length in characters to process (default: 200000, ~50K tokens for gpt-4o)')
parser.add_argument('--use-retrieval-only', action='store_true',
                   help='Use only retrieval_context instead of full context to reduce token usage')
parser.add_argument('--list-questions', action='store_true',
                   help='List all available question keys in the benchmark data and exit')

args = parser.parse_args()

# Set default input path if not provided (use same logic as prep_benchmark_data.py)
if args.input is None:
    args.input = os.path.join(get_data_dir(), "benchmark_data_gui.json")

# Load benchmark dataset first (needed for --list-questions)
# This is done before API key check so we can list questions without API key
print(f"Loading benchmark data from: {args.input}")
with open(args.input, "r") as f:
    raw_data = json.load(f)

# Expected format: {papers: {...}, test_cases: [...]}
if not isinstance(raw_data, dict) or "test_cases" not in raw_data:
    raise ValueError(
        f"Invalid format: Expected dict with 'papers' and 'test_cases' keys.\n"
        f"This script only works with output from prep_benchmark_data.py"
    )

papers_data = raw_data.get("papers", {})
test_cases_data = raw_data.get("test_cases", [])
print(f"Loaded {len(papers_data)} papers, {len(test_cases_data)} test cases")

# Expand test cases with context from papers_data
data = []
for entry in test_cases_data:
    # Create a copy to avoid modifying the original
    entry_copy = entry.copy()
    paper_id = entry_copy.get("paper_id")
    if paper_id and paper_id in papers_data:
        # Add context from papers_data
        entry_copy["context"] = papers_data[paper_id].get("context", [])
    else:
        # Error if paper not found
        print(f"[WARNING] No context found for paper_id '{paper_id}', using empty context")
        entry_copy["context"] = []
    data.append(entry_copy)

# Extract available question keys from the data
available_question_keys = sorted(set(entry.get("question_key") for entry in data if entry.get("question_key")))

# Count test cases per question
question_counts = {}
for entry in data:
    q_key = entry.get("question_key")
    if q_key:
        question_counts[q_key] = question_counts.get(q_key, 0) + 1

# If --list-questions flag is set, print and exit
if args.list_questions:
    print("\n" + "="*60)
    print("AVAILABLE QUESTION KEYS IN BENCHMARK DATA")
    print("="*60)
    if available_question_keys:
        print(f"\nFound {len(available_question_keys)} question type(s):\n")
        for q_key in available_question_keys:
            count = question_counts.get(q_key, 0)
            print(f"  • {q_key} ({count} test case{'s' if count != 1 else ''})")
        print(f"\nUsage: python deepeval_benchmarking.py --question <question_key>")
        print(f"   Example: python deepeval_benchmarking.py --question {available_question_keys[0]}")
    else:
        print("\n[WARNING] No question keys found in the dataset.")
    print("="*60 + "\n")
    sys.exit(0)

# Only check API key and load deepeval if we're actually running evaluation
# Set API keys from environment
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

os.environ["OPENAI_API_KEY"] = openai_api_key
print("[OK] OpenAI API key loaded from .env file")

from deepeval.dataset import EvaluationDataset
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval import evaluate
from deepeval.metrics import FaithfulnessMetric, ContextualPrecisionMetric, ContextualRecallMetric, GEval
from deepeval.models import GPTModel

print(f"Available question keys in dataset: {', '.join(available_question_keys) if available_question_keys else 'None'}")

# Filter by question type (optional)
print(f"\nOriginal dataset: {len(data)} test cases")

if args.question:
    filtered_data = [entry for entry in data if entry.get("question_key") == args.question]
    if len(filtered_data) == 0:
        print(f"\n[ERROR] No test cases found for question key '{args.question}'")
        print(f"Available question keys: {', '.join(available_question_keys) if available_question_keys else 'None'}")
        sys.exit(1)
    print(f"[OK] Filtered by '{args.question}': {len(filtered_data)} test cases")
else:
    filtered_data = data
    print(f"[OK] Processing all question types")

# Apply limit if specified
if args.limit and len(filtered_data) > args.limit:
    filtered_data = filtered_data[:args.limit]
    print(f"Limited to first {args.limit} test cases")

# Create the dataset
dataset = EvaluationDataset()

# Add test cases to the dataset
skipped_count = 0
for i, entry in enumerate(filtered_data):
    if i % 10 == 0:  # Progress indicator
        print(f"Processing test case {i+1}/{len(filtered_data)}")
    
    # Check for required fields and skip if missing
    required_fields = ["input", "actual_output", "expected_output", "context"]
    missing_fields = [field for field in required_fields if not entry.get(field)]
    
    if missing_fields:
        print(f"[WARNING] Skipping test case {i+1}: Missing fields {missing_fields}")
        skipped_count += 1
        continue
    
    # Get retrieval_context, use context as fallback if missing
    retrieval_context = entry.get("retrieval_context")
    if not retrieval_context:
        retrieval_context = entry["context"]  # Use context as fallback
    
    # Optionally use only retrieval context to reduce token usage
    if args.use_retrieval_only:
        context_to_use = retrieval_context
    else:
        context_to_use = entry["context"]
    
    # Check context length to avoid token limit issues
    context_length = len(str(context_to_use))
    
    if context_length > args.max_context_length:
        print(f"[WARNING] Skipping test case {i+1}: Context too long ({context_length:,} chars, max: {args.max_context_length:,})")
        skipped_count += 1
        continue
    
    try:
        # Create LLMTestCase object with proper identifiers
        test_case = LLMTestCase(
            input=entry["input"],
            actual_output=entry["actual_output"],  # LLM generated answer
            expected_output=entry["expected_output"],  # GUI reviewer answer (expected output)
            context=context_to_use,  # Full paper context or retrieval context only
            retrieval_context=retrieval_context,  # Retrieval context for metrics that need it
            name=f"paper_{entry['paper_id']}_case_{i}",  # Unique name for each test case
            additional_metadata={
                "paper_id": entry.get("paper_id"),
                "question_key": entry.get("question_key"),
                "chunk_ids": entry.get("chunk_ids", []),
                "user_rating": entry.get("user_rating")  # Include user_rating if available
            }
        )
        
        # Set proper identifiers to avoid ID errors
        test_case._identifier = f"paper_{entry['paper_id']}_case_{i}"
        test_case._dataset_id = f"primate_welfare_{args.question if args.question else 'all'}"
        
        # Add as test case
        dataset.add_test_case(test_case)
        
    except Exception as e:
        print(f"[WARNING] Error creating test case {i+1}: {e}")
        skipped_count += 1
        continue

if skipped_count > 0:
    print(f"[WARNING] Skipped {skipped_count} test cases due to missing data or errors")

print("Dataset created successfully!")
print(f"Dataset contains {len(dataset.test_cases)} test cases")

# Warn about long contexts
long_context_count = sum(1 for entry in filtered_data if len(str(entry.get("context", ""))) > 100000)
if long_context_count > 0:
    print(f"[WARNING] {long_context_count} test cases have very long context (>100K chars)")
    print(f"RECOMMENDED: Use --batch-size 10-15 or --use-retrieval-only for best stability")
    
# Show context usage mode
if args.use_retrieval_only:
    print(f"Using retrieval_context only (reduced token usage)")
else:
    print(f"Using full context from papers")

# Configure the specified model
evaluation_model = GPTModel(model=args.model)

# Define ALL metrics: Standard + G-Eval
standard_metrics = [
    FaithfulnessMetric(model=evaluation_model),
    ContextualPrecisionMetric(model=evaluation_model),
    ContextualRecallMetric(model=evaluation_model)
]

geval_metrics = [
    GEval(
        name="Completeness",
        criteria="Completeness - assess if the actual output covers all the key points mentioned in the expected output.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        model=evaluation_model,
        strict_mode=False
    ),
    GEval(
        name="Accuracy",
        criteria="Accuracy - evaluate if the actual output contains accurate information that aligns with the expected output.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        model=evaluation_model,
        strict_mode=False
    )
]

metrics = standard_metrics + geval_metrics

print(f"\nUsing {args.model} for evaluation")

# Model information with context limits
model_info = {
    'gpt-4o-mini': {
        'input': 0.00015, 
        'output': 0.0006, 
        'description': 'Most cost-effective',
        'context_window': '128K tokens (~500K chars)'
    },
    'gpt-4o': {
        'input': 0.0025, 
        'output': 0.01, 
        'description': 'Balanced performance/cost',
        'context_window': '128K tokens (~500K chars)'
    },
    'gpt-4-turbo': {
        'input': 0.01, 
        'output': 0.03, 
        'description': 'Higher cost, better performance',
        'context_window': '128K tokens (~500K chars)'
    },
    'gpt-3.5-turbo': {
        'input': 0.0005, 
        'output': 0.0015, 
        'description': 'Good cost, lower performance',
        'context_window': '16K tokens (~60K chars)'
    }
}

selected_info = model_info[args.model]
print(f"Cost per 1K tokens: Input ${selected_info['input']:.4f}, Output ${selected_info['output']:.4f}")
print(f"{selected_info['description']}")
print(f"Context window: {selected_info['context_window']}")
print(f"Max context length setting: {args.max_context_length:,} chars")

print(f"\nEvaluating with {len(metrics)} metrics (3 Standard + 2 G-Eval):")
print("  Standard Metrics:")
for metric in standard_metrics:
    print(f"    - {metric.__class__.__name__}")
print("  G-Eval Metrics:")
for metric in geval_metrics:
    print(f"    - {metric.name}")

# Initialize results tracking
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
question_type = args.question if args.question else "all_questions"

# Create results directory in the same directory as the input file
# Input file is in get_data_dir(), so output goes to get_data_dir()/deepeval_results/
input_dir = os.path.dirname(os.path.abspath(args.input))
results_dir = os.path.join(input_dir, "deepeval_results")
os.makedirs(results_dir, exist_ok=True)

# Generate unique filenames
results_file = f"{results_dir}/combined_results_{question_type}_{timestamp}.json"
results_jsonl_file = f"{results_dir}/combined_results_{question_type}_{timestamp}.jsonl"

print(f"\nOutput files will be saved in: {results_dir}/")
print(f"File prefix: combined_results_{question_type}_{timestamp}")

# Function to save results incrementally (without context fields)
def save_results_incrementally(results_list, filename, jsonl_filename):
    """Save results incrementally without context/retrieval_context fields"""
    try:
        # Remove context fields from results before saving
        cleaned_results = []
        for result in results_list:
            cleaned_result = result.copy()
            # Remove context fields to save space
            cleaned_result.pop('context', None)
            cleaned_result.pop('retrieval_context', None)
            cleaned_results.append(cleaned_result)
        
        # Save as JSON
        with open(filename, "w") as f:
            json.dump(cleaned_results, f, indent=2)
        
        # Save as JSONL
        with open(jsonl_filename, "w") as f:
            for result in cleaned_results:
                f.write(json.dumps(result) + "\n")
        
        print(f"Incremental save: {len(cleaned_results)} results saved to {filename}")
        return True
    except Exception as e:
        print(f"[WARNING] Incremental save failed: {e}")
        return False

# Function to process test cases in batches
def process_test_cases_in_batches(test_cases, batch_size=25, max_retries=5):
    """Process test cases in batches and save incrementally with retry limits"""
    total_cases = len(test_cases)
    processed_results = []
    
    print(f"\nProcessing {total_cases} test cases in batches of {batch_size}")
    print(f"Maximum retries per batch: {max_retries}")
    
    for batch_start in range(0, total_cases, batch_size):
        batch_end = min(batch_start + batch_size, total_cases)
        batch_cases = test_cases[batch_start:batch_end]
        
        print(f"\nProcessing batch {batch_start//batch_size + 1}: cases {batch_start+1}-{batch_end}")
        
        # Retry logic for each batch
        batch_success = False
        retry_count = 0
        
        while not batch_success and retry_count < max_retries:
            try:
                if retry_count > 0:
                    print(f"Retry attempt {retry_count}/{max_retries} for batch {batch_start//batch_size + 1}")
                
                # Process this batch
                eval_output = evaluate(
                    test_cases=batch_cases,
                    metrics=metrics
                )
                
                # Extract test results from the EvaluationResult object
                # The evaluate() function returns an EvaluationResult with test_results attribute
                test_results = getattr(eval_output, 'test_results', batch_cases)
                
                # Extract results from test cases
                for idx, test_case in enumerate(test_results):
                    result_dict = {
                        "test_case_index": batch_start + idx,
                        "name": test_case.name if hasattr(test_case, 'name') else f"case_{batch_start + idx}",
                        "paper_id": test_case.additional_metadata.get("paper_id"),
                        "question_key": test_case.additional_metadata.get("question_key"),
                        "input": test_case.input,
                        "actual_output": test_case.actual_output,
                        "expected_output": test_case.expected_output,
                        "success": False,  # Will be updated based on metrics
                        "additional_metadata": test_case.additional_metadata,
                        "metrics_data": []
                    }
                    
                    # Extract metric results from test_case.metrics_data
                    if hasattr(test_case, 'metrics_data') and test_case.metrics_data:
                        all_passed = True
                        for metric in test_case.metrics_data:
                            # Build metric data entry matching the expected format
                            metric_entry = {
                                "name": getattr(metric, '__name__', None) or getattr(metric, 'name', metric.__class__.__name__),
                                "score": getattr(metric, 'score', None),
                                "threshold": getattr(metric, 'threshold', None),
                                "success": getattr(metric, 'success', None),
                                "reason": getattr(metric, 'reason', None),
                                "strict_mode": getattr(metric, 'strict_mode', None),
                                "evaluation_model": args.model,
                                "error": str(getattr(metric, 'error', None)) if getattr(metric, 'error', None) else None,
                                "evaluation_cost": getattr(metric, 'evaluation_cost', None)
                            }
                            result_dict["metrics_data"].append(metric_entry)
                            
                            if not metric_entry["success"]:
                                all_passed = False
                        
                        result_dict["success"] = all_passed
                    
                    processed_results.append(result_dict)
                
                # Save incrementally after each batch
                save_results_incrementally(processed_results, results_file, results_jsonl_file)
                
                batch_success = True
                print(f"[OK] Batch {batch_start//batch_size + 1} completed successfully")
                
            except Exception as e:
                retry_count += 1
                print(f"[ERROR] Batch {batch_start//batch_size + 1} failed (attempt {retry_count}/{max_retries}): {str(e)}")
                
                if retry_count >= max_retries:
                    print(f"[WARNING] Batch {batch_start//batch_size + 1} failed after {max_retries} retries. Skipping...")
                    break
    
    return processed_results

# Process all test cases in batches
print("\n" + "="*60)
print("Starting batch processing...")
print("="*60)

final_results = process_test_cases_in_batches(
    dataset.test_cases,
    batch_size=args.batch_size,
    max_retries=args.max_retries
)

# Final save
print("\n" + "="*60)
print("Saving final results...")
save_results_incrementally(final_results, results_file, results_jsonl_file)

# Print summary statistics
print("\n" + "="*60)
print("EVALUATION COMPLETE!")
print("="*60)
print(f"Total test cases processed: {len(final_results)}")
print(f"Results saved to: {results_file}")
print(f"JSONL format: {results_jsonl_file}")

# Calculate average scores
if final_results:
    print("\nAverage Scores:")
    metric_sums = {}
    metric_counts = {}
    
    for result in final_results:
        for metric_entry in result.get("metrics_data", []):
            metric_name = metric_entry.get("name")
            metric_score = metric_entry.get("score")
            
            if metric_name and metric_score is not None:
                if metric_name not in metric_sums:
                    metric_sums[metric_name] = 0
                    metric_counts[metric_name] = 0
                metric_sums[metric_name] += metric_score
                metric_counts[metric_name] += 1
    
    for metric_name in sorted(metric_sums.keys()):
        avg_score = metric_sums[metric_name] / metric_counts[metric_name]
        print(f"  - {metric_name}: {avg_score:.3f}")

print("\nDone!")
