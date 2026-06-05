import argparse
import asyncio
import copy
import json
import os
import sys
import time

import yaml

from metabeeai.metabeeai_llm.json_multistage_qa import ask_json as ask_json_async
from metabeeai.metabeeai_llm.json_multistage_qa import format_to_list as format_to_list_async


def ask_json(question_text, json_path):
    """
    Asks a question to the JSON file at the specified path and returns the answer.
    """
    return asyncio.run(ask_json_async(question_text, json_path))


def format_to_list(question, text, model="gpt-4o-mini"):
    """
    Formats the JSON file at the specified path to a list.
    """
    return asyncio.run(format_to_list_async(question, text, model))


# ------------------------------------------------------------------------------
# Hierarchical Questions Dictionary
# ------------------------------------------------------------------------------
# Use {placeholder} format syntax in any question that should be parameterized.

# Lazy load questions to avoid import-time errors
_QUESTIONS = None


def _get_questions():
    """
    Lazy loads the questions.yml file when first accessed.
    Returns the questions dictionary.
    """
    global _QUESTIONS
    if _QUESTIONS is None:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        questions_path = os.path.join(script_dir, "questions.yml")

        with open(questions_path, "r") as file:
            # Extract the questions ('QUESTIONS') dictionary to prevent double-wrapping if it exists
            # Otherwise use the whole config as the questions dictionary
            config = yaml.safe_load(file)
            _QUESTIONS = config.get("QUESTIONS", config)

    return _QUESTIONS


# ------------------------------------------------------------------------------
# Helper Function: get_answer
# ------------------------------------------------------------------------------
async def get_answer(question_text, json_path, relevance_model=None, answer_model=None):
    """
    Retrieves the answer for a given question by calling ask_json.
    Returns a dictionary with the required structure: answer, reason, and chunk_ids.

    Args:
        question_text: The question to ask
        json_path: Path to the JSON file containing text chunks
        relevance_model: Model to use for chunk selection (defaults to config)
        answer_model: Model to use for answer generation and reflection (defaults to config)
    """
    result = await ask_json_async(question_text, json_path, relevance_model=relevance_model, answer_model=answer_model)

    # Ensure the result has the required structure
    if isinstance(result, dict):
        # Extract the required fields from the enhanced result
        return {
            "answer": result.get("answer", ""),
            "reason": result.get("reason", ""),
            "chunk_ids": result.get("chunk_ids", []),
            # Pass total question cost to the pipeline for logging (will be popped before saving to answers.json)
            "cost": result.get("cost", 0.0),
            # Pass aggregated token metrics to the pipeline for logging (will be popped before saving to answers.json)
            "metrics": result.get("metrics", {}),
        }
    else:
        # Fallback if result is not a dict
        return {
            "answer": str(result) if result else "",
            "reason": "Answer generated from available information",
            "chunk_ids": [],
            # Safety fallback - pass zero cost so the logging loop doesn't crash
            # (still popped before saving to answers.json)
            "cost": 0.0,
            # Safety fallback - pass empty metrics dictionary so the logging loop doesn't crash
            # (still popped before saving to answers.json)
            "metrics": {},
        }


# ------------------------------------------------------------------------------
# Generic Recursive Function to Process a Hierarchical Question Tree
# ------------------------------------------------------------------------------
async def process_question_tree(tree, json_path, context=None, relevance_model=None, answer_model=None):
    """
    Recursively traverses the question tree (a nested dictionary) and obtains answers using get_answer.

    Args:
        tree: The question tree structure
        json_path: Path to the JSON file containing text chunks
        context: Context for formatting questions with placeholders
        relevance_model: Model to use for chunk selection (defaults to config)
        answer_model: Model to use for answer generation and reflection (defaults to config)

    - If a node contains a "question" key, it is treated as a leaf node.
    - The "for_each" key indicates that the associated value should be processed for
      each item in a list provided via the context.
    - The context is used to format questions with placeholders.
    """
    if context is None:
        context = {}

    # If the tree is a dictionary
    if isinstance(tree, dict):
        # If this dictionary has a "question" key, treat it as a leaf.
        if "question" in tree:
            question_text = tree["question"].format(**context)
            answer = await get_answer(question_text, json_path, relevance_model=relevance_model, answer_model=answer_model)
            # Process conditional branch if available.
            return answer
        else:
            result = {}
            for key, value in tree.items():
                if key == "list":
                    # If the key is "list", return the list as is.
                    question_of_the_list = value["question"].format(**context)
                    endpoint_name = value["endpoint_name"]
                    answer = await get_answer(
                        question_of_the_list, json_path, relevance_model=relevance_model, answer_model=answer_model
                    )
                    list_result = await format_to_list_async(question_of_the_list, answer["answer"])
                    list_items = list_result["answer"]
                    result[key] = {}

                    # Preserve the parent list costs so extract_metrics can see them
                    # Sum the costs of both finding the list and formatting it into an array
                    total_list_cost = answer.get("cost", 0.0) + list_result.get("cost", 0.0)

                    # Copy the original list token metrics into the combined run metrics tracker
                    combined_metrics = copy.deepcopy(answer.get("metrics", {}))
                    if list_result and "usage_details" in list_result:
                        usage = list_result["usage_details"]
                        m_name = usage.get("model", "unknown")
                        metric_key = f"Answering|{m_name}"

                        # Initialise counters for the model if it's the first time seeing it in this block
                        if metric_key not in combined_metrics:
                            combined_metrics[metric_key] = {"input": 0, "cached": 0, "output": 0, "cost": 0.0}
                        # Add the list formatting token costs to the combined run tracking data
                        combined_metrics[metric_key]["input"] += usage.get("input_tokens", 0)
                        combined_metrics[metric_key]["cached"] += usage.get("cached_tokens", 0)
                        combined_metrics[metric_key]["output"] += usage.get("output_tokens", 0)
                        combined_metrics[metric_key]["cost"] += usage.get("cost", 0.0)

                    # Store the totals in a dictionary key so they can be processed by the logging function
                    result[key]["_list_metadata"] = {
                        "answer": "List discovery metadata",
                        "cost": total_list_cost,
                        "metrics": combined_metrics,
                    }

                    for item in list_items:
                        new_context = context.copy()
                        new_context[endpoint_name] = item
                        result[key][item] = await process_question_tree(
                            value["for_each"],
                            json_path,
                            new_context,
                            relevance_model=relevance_model,
                            answer_model=answer_model,
                        )
                else:
                    result[key] = await process_question_tree(
                        value, json_path, context, relevance_model=relevance_model, answer_model=answer_model
                    )
            return result
    elif isinstance(tree, list):
        return [
            await process_question_tree(item, json_path, context, relevance_model=relevance_model, answer_model=answer_model)
            for item in tree
        ]
    elif isinstance(tree, str):
        # If the tree itself is a string, treat it as a question.
        question_text = tree.format(**context)
        return await get_answer(question_text, json_path, relevance_model=relevance_model, answer_model=answer_model)
    else:
        return tree


# ------------------------------------------------------------------------------
# Main Function: Retrieve All Answers Based on the Questions Dictionary
# ------------------------------------------------------------------------------
async def get_literature_answers(json_path, relevance_model=None, answer_model=None):
    """
    Processes the entire hierarchical question tree defined in QUESTIONS and returns
    the collected answers.

    Args:
        json_path: Path to the JSON file containing text chunks
        relevance_model: Model to use for chunk selection (defaults to config)
        answer_model: Model to use for answer generation and reflection (defaults to config)
    """
    questions = _get_questions()
    answers = await process_question_tree(questions, json_path, relevance_model=relevance_model, answer_model=answer_model)
    return answers


# ------------------------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------------------------
def merge_json_in_the_folder(folder_path, overwrite=False):
    """
    Merges all JSON files in the specified folder into a single dictionary.
    """

    if not overwrite:
        if os.path.exists(folder_path + "merged.json"):
            print("The file already exists. Set 'overwrite=True' to overwrite.")
            return

    chunks_kept = []
    for file in os.listdir(folder_path):
        if file.endswith(".json"):
            json_path = os.path.join(folder_path, file)

            with open(json_path, "r") as f:
                json_obj = json.load(f)

            chunks = json_obj["data"]["chunks"]

            for chunk in chunks:
                if chunk["chunk_type"] in ["figure", "marginalia"]:
                    continue
                chunks_kept.append(chunk)

    json_obj = {"data": {"chunks": chunks_kept}}

    with open(folder_path + "merged.json", "w") as f:
        json.dump(json_obj, f, indent=2)


def extract_metrics(answers_dict, prefix=""):
    """
    Iterates through the answers dictionary to extract costs and model metrics, removing them from the dictionary.
    Deletes any temporary tracking keys so they are not in the final JSON.
    """
    costs = {}
    metrics = {}
    total = 0.0

    # Handle lists if the top-level question yml is an array
    if isinstance(answers_dict, list):
        for i, item in enumerate(answers_dict):
            if isinstance(item, dict):
                sub_costs, sub_metrics, sub_total = extract_metrics(item, prefix=f"{prefix}[{i}].")
                costs.update(sub_costs)
                metrics.update(sub_metrics)
                total += sub_total
        return costs, metrics, total

    # Use list() to modify the dictionary while looping
    for key in list(answers_dict.keys()):
        value = answers_dict[key]

        if isinstance(value, dict):
            if "metrics" in value and "answer" in value:
                # Use pop() to extract the data and delete the keys from the dictionary
                costs[prefix + key] = value.pop("cost", 0.0)
                metrics[prefix + key] = value.pop("metrics", {})
                total += costs[prefix + key]
            else:
                # If it's a nested category dictionary, go one layer deeper
                sub_costs, sub_metrics, sub_total = extract_metrics(value, prefix=f"{prefix}{key}.")

                # Merge the numbers found in the sub-category into the main tracking dictionaries
                costs.update(sub_costs)
                metrics.update(sub_metrics)
                total += sub_total

            # If it's a hidden overhead key (starts with _), remove the shell from the dictionary
            if key.startswith("_"):
                answers_dict.pop(key)

        elif isinstance(value, list):
            # If the value is a list of sub-questions, loop through the list
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    # Go one layer deeper into the list items
                    # Adds [i] to the prefix to track which list item the cost belongs to
                    sub_costs, sub_metrics, sub_total = extract_metrics(item, prefix=f"{prefix}{key}[{i}].")

                    # Merge the numbers found in the sub-category into the main tracking dictionaries
                    costs.update(sub_costs)
                    metrics.update(sub_metrics)
                    total += sub_total

    return costs, metrics, total


async def process_papers(
    base_dir=None,
    paper_folders=None,
    overwrite_merged=False,
    relevance_model=None,
    answer_model=None,
    start_folder=None,
    end_folder=None,
):
    """
    Processes papers in the specified directory.

    Args:
        base_dir: Base directory containing paper folders (defaults to config)
        paper_folders: List of specific paper folder names to process (defaults to all folders)
        start_folder: Optional start folder (inclusive, alphanumeric)
        end_folder: Optional end folder (inclusive, alphanumeric)
        overwrite_merged: Whether to overwrite existing merged.json files
        relevance_model: Model to use for chunk selection (defaults to config)
        answer_model: Model to use for answer generation and reflection (defaults to config)
    """
    # Import centralized configuration if base_dir not provided
    if base_dir is None:
        from metabeeai.config import get_config_param

        base_dir = get_config_param("papers_dir")

    # Validate base directory
    if not os.path.exists(base_dir):
        print(f"Error: Base directory '{base_dir}' not found")
        return

    # Add trailing slash if missing
    if not base_dir.endswith("/"):
        base_dir += "/"

    # If no specific folders provided, get all subdirectories
    if paper_folders is None:
        paper_folders = []
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            # Only include directories (not files)
            if os.path.isdir(item_path) and not item.startswith("."):
                paper_folders.append(item)
        paper_folders.sort()  # Sort for consistent processing order
        if start_folder or end_folder:
            filtered = []
            for folder in paper_folders:
                if start_folder and folder < start_folder:
                    continue
                if end_folder and folder > end_folder:
                    continue
                filtered.append(folder)
            paper_folders = filtered

    total_papers = len(paper_folders)
    completed_papers = 0
    failed_papers = []

    # Create progress log file
    log_file = os.path.join(base_dir, "processing_log.txt")

    print(f"🚀 Starting pipeline: {total_papers} papers to process")
    print(f"📁 Papers directory: {base_dir}")
    print(f"📝 Progress log: {log_file}")
    print("=" * 60)

    # Initialise the global metrics dictionary to hold the total token and cost counts across all files in the run
    global_metrics = {}

    for paper_folder in paper_folders:
        paper_path = os.path.join(base_dir, paper_folder)

        # Show overall progress
        remaining = total_papers - completed_papers
        print(f"\n📊 Progress: {completed_papers}/{total_papers} completed, {remaining} remaining")
        print(f"🔄 Processing paper {paper_folder}...")

        # Skip if the paper directory doesn't exist
        if not os.path.exists(paper_path):
            print(f"⏭️  Skipping {paper_folder} - directory not found")
            continue

        try:
            pages_path = os.path.join(paper_path, "pages/")
            if not os.path.exists(pages_path):
                print(f"⏭️  Skipping {paper_folder} - pages directory not found")
                continue

            # Check if merged_v2.json exists
            json_path = os.path.join(pages_path, "merged_v2.json")
            if not os.path.exists(json_path):
                print(f"⏭️  Skipping {paper_folder} - merged_v2.json not found")
                continue

            # Process the paper with progress tracking
            questions = _get_questions()
            print(f"  📖 Processing {len(questions)} questions...")

            # Temporarily reduce logging verbosity and suppress all output during processing
            import logging
            import sys
            from io import StringIO

            # Capture and suppress all output during processing
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            original_log_level = logging.getLogger().level

            # Suppress all output
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            logging.getLogger().setLevel(logging.ERROR)

            try:
                literature_answers = await get_literature_answers(
                    json_path, relevance_model=relevance_model, answer_model=answer_model
                )
            finally:
                # Restore all output
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                logging.getLogger().setLevel(original_log_level)

            # Merge with existing answers.json if it exists
            answers_path = os.path.join(paper_path, "answers.json")

            # Load existing answers if the file exists
            existing_answers = {}
            if os.path.exists(answers_path):
                try:
                    with open(answers_path, "r") as f:
                        existing_data = json.load(f)
                        # Handle both old format (direct dict) and new format (with QUESTIONS key)
                        if "QUESTIONS" in existing_data:
                            existing_answers = existing_data["QUESTIONS"]
                        else:
                            existing_answers = existing_data
                    print(f"  📝 Found existing answers with {len(existing_answers)} question(s)")
                except Exception as e:
                    print(f"  ⚠️  Could not read existing answers: {e}")

            # Merge new answers with existing ones
            # New answers will update existing keys, but won't delete old keys
            if existing_answers:
                # Preserve existing answers that aren't in the new results
                for key in existing_answers:
                    if key not in literature_answers:
                        literature_answers[key] = existing_answers[key]
                print(f"  🔄 Merged answers: {len(literature_answers)} total question(s)")

            # Extract the metrics, removing the tracking data from the dictionary
            # Happens before saving so the data doesn't get written into answers.json
            costs, question_metrics, total_cost = extract_metrics(literature_answers)

            # Save the merged results in QUESTIONS format
            output_data = {"QUESTIONS": literature_answers}

            with open(answers_path, "w") as f:
                json.dump(output_data, f, indent=2)

            completed_papers += 1
            print(f"  ✅ Paper {paper_folder} completed successfully")

            # Print and log the metrics
            log_lines = []
            for q_key, q_cost in costs.items():
                # Format individual cost metrics for clear reading in the log file
                log_lines.append(f"- {q_key}: ${q_cost:.4f}")

                # Collect token usage totals into global_metrics for the final summary
                q_m = question_metrics.get(q_key, {})
                for model_name, tokens in q_m.items():
                    if model_name not in global_metrics:
                        global_metrics[model_name] = {"input": 0, "cached": 0, "output": 0, "cost": 0.0}
                    global_metrics[model_name]["input"] += tokens["input"]
                    global_metrics[model_name]["cached"] += tokens["cached"]
                    global_metrics[model_name]["output"] += tokens["output"]
                    global_metrics[model_name]["cost"] += tokens["cost"]

            # Time stamp with the total single-paper cost, saved to tracking log
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_lines.append(f"{paper_folder}: COMPLETED at {timestamp} | Total Cost: ${total_cost:.4f}\n")

            # Log completion
            with open(log_file, "a") as f:
                f.write("\n".join(log_lines))

        except Exception as e:
            print(f"  ❌ Error processing paper {paper_folder}: {str(e)}")
            failed_papers.append(paper_folder)

            # Log failure
            with open(log_file, "a") as f:
                f.write(f"{paper_folder}: FAILED at {time.strftime('%Y-%m-%d %H:%M:%S')} - {str(e)}\n")
            continue

    # Final summary
    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETED!")
    print(f"✅ Successfully processed: {completed_papers}/{total_papers} papers")
    if failed_papers:
        print(f"❌ Failed papers: {', '.join(failed_papers)}")
    print(f"📝 Detailed log: {log_file}")

    # Full run information for the end of the processing log file
    # Executes once the whole stack of folders has finished processing
    if global_metrics:
        # Calculate the overall total costs and total tokens used across all files processed
        overall_total_cost = sum(m["cost"] for m in global_metrics.values())
        overall_total_tokens = sum(m["input"] + m["cached"] + m["output"] for m in global_metrics.values())

        # Title for readability
        summary_lines = ["\nFull Run Totals:"]
        # Iterate through global_metrics to generate the final text lines for the log file
        for model_key, m in global_metrics.items():
            # Separate the combined key to identify the phase and model name strings
            if "|" in model_key:
                phase, model_name = model_key.split("|", 1)
                model_display = f"{phase} Model: {model_name}"
            else:
                # Use the full key as the display name if the data format doesn't have the '|' splitting it
                model_display = f"Model: {model_key}"

            # Format the metrics into an easy to read text block with all the usage information
            summary_lines.append(
                f"{model_display}\n"
                f"New Input Tokens: {m['input']}\n"
                f"Cached Input Tokens: {m['cached']}\n"
                f"Output Tokens: {m['output']}\n"
                f"Overall Cost: ${m['cost']:.4f}\n"
            )

        # Add the combined run totals to the end of the summary
        summary_lines.append(f"Total Tokens Combined: {overall_total_tokens}")
        summary_lines.append(f"Total Cost Combined: ${overall_total_cost:.4f}\n")

        # Write the summary into the log file at the end of the run
        with open(log_file, "a") as f:
            f.write("\n".join(summary_lines))


def main(argv=None):
    """Main entry point."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Process paper folders to extract literature answers")
    # YAML config file path (sets METABEEAI_CONFIG_FILE for downstream lookups)
    parser.add_argument(
        "--config",
        "--config-file",
        dest="config",
        type=str,
        default=None,
        help="Path to config YAML file (overrides METABEEAI_CONFIG_FILE and defaults)",
    )
    # Base directory and selection of folders
    parser.add_argument(
        "--dir", type=str, default=None, help="Base directory containing paper folders (default: auto-detect from config)"
    )
    parser.add_argument(
        "--papers",
        type=str,
        nargs="+",
        default=None,
        help=("Specific paper IDs to process (e.g., 283C6B42 3ZHNVADM). If not specified, all folders will be processed."),
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start processing from this paper ID (alphanumeric, optional; only applies when --papers is not set)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End processing at this paper ID (alphanumeric, optional; only applies when --papers is not set)",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing merged.json files")
    # Models
    parser.add_argument(
        "--relevance-model",
        type=str,
        default=None,
        help="Model to use for chunk selection (e.g., 'openai/gpt-4o-mini', 'openai/gpt-4o'). Default: from config",
    )
    parser.add_argument(
        "--answer-model",
        type=str,
        default=None,
        help=(
            "Model to use for answer generation and reflection (e.g., 'openai/gpt-4o-mini', 'openai/gpt-4o'). "
            "Default: from config"
        ),
    )
    # Preset selector (fast/balanced/quality)
    parser.add_argument(
        "--preset",
        type=str,
        choices=["fast", "balanced", "quality"],
        default=None,
        help="Use predefined configuration preset: 'fast', 'balanced', or 'quality'",
    )

    args = parser.parse_args(argv)

    # Respect provided config file for downstream lookups
    if args.config:
        os.environ["METABEEAI_CONFIG_FILE"] = args.config

    # Handle predefined configurations
    if args.preset:
        from metabeeai.metabeeai_llm.pipeline_config import BALANCED_CONFIG, FAST_CONFIG, QUALITY_CONFIG

        config_map = {"fast": FAST_CONFIG, "balanced": BALANCED_CONFIG, "quality": QUALITY_CONFIG}
        selected_config = config_map[args.preset]

        # Override model arguments with config values if not explicitly provided
        if args.relevance_model is None:
            args.relevance_model = selected_config["relevance_model"]
        if args.answer_model is None:
            args.answer_model = selected_config["answer_model"]

        print(f"🔧 Using {args.preset.upper()} configuration:")
        print(f"   Relevance Model: {args.relevance_model}")
        print(f"   Answer Model: {args.answer_model}")
        print(f"   Description: {selected_config['description']}")

    import asyncio

    asyncio.run(
        process_papers(
            base_dir=args.dir,
            paper_folders=args.papers,
            overwrite_merged=args.overwrite,
            relevance_model=args.relevance_model,
            answer_model=args.answer_model,
            start_folder=args.start,
            end_folder=args.end,
        )
    )


if __name__ == "__main__":
    main(sys.argv[1:])
