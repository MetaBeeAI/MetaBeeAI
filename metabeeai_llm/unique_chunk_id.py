#!/usr/bin/env python3
# Check if each chunk_id contained in the json files (except merged.json) in each pages/ subfolder is unique
# If duplicates are found, print the chunk_id and the file paths
# Results are saved to a JSON log file with summary statistics

import os
import json
import datetime
import argparse
from collections import defaultdict

def check_chunk_ids_in_pages_dir(papers_dir=None):
    """
    Check for duplicate chunk IDs in the specified directory.
    
    Args:
        papers_dir: Directory containing paper subfolders (defaults to config)
    """
    # Import centralized configuration if papers_dir not provided
    if papers_dir is None:
        import sys
        sys.path.append('..')
        from config import get_papers_dir
        papers_dir = get_papers_dir()
    
    # Validate papers directory
    if not os.path.exists(papers_dir):
        print(f"Error: Directory '{papers_dir}' does not exist")
        return
        
    # Create results structure for logging
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "timestamp": timestamp,
        "papers_dir": papers_dir,
        "summary": {
            "total_subfolders_checked": 0,
            "subfolders_with_duplicates": 0
        },
        "results": {}
    }
    
    print(f"Checking for duplicate chunk IDs in: {papers_dir}")
    
    # Walk through all directories under the papers directory
    for root, dirs, files in os.walk(papers_dir):
        # Check if we're in a pages directory
        if os.path.basename(root) == "pages":
            print(f"\nChecking chunk_ids in: {root}")
            results["summary"]["total_subfolders_checked"] += 1
            
            # Dictionary to track chunk_ids: {chunk_id: [file_paths]}
            chunk_id_map = defaultdict(list)
            duplicate_found = False
            
            # Process each JSON file in this pages directory
            for file in files:
                if file.endswith(".json") and file != "merged.json":
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)
                            for chunk in data.get("chunks", []):
                                chunk_id = chunk.get("chunk_id")
                                if chunk_id:
                                    chunk_id_map[chunk_id].append(file_path)
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
            
            # Store subfolder results
            subfolder_results = {
                "has_duplicates": False,
                "duplicates": {}
            }
            
            # Check for duplicates and report them
            for chunk_id, file_paths in chunk_id_map.items():
                if len(file_paths) > 1:
                    duplicate_found = True
                    subfolder_results["has_duplicates"] = True
                    subfolder_results["duplicates"][chunk_id] = file_paths
                    
                    print(f"Duplicate chunk_id found: {chunk_id}")
                    for path in file_paths:
                        print(f"  - {path}")
            
            if duplicate_found:
                results["summary"]["subfolders_with_duplicates"] += 1
            else:
                print("All chunk_ids are unique in this directory.")
                
            # Add this subfolder to the results
            results["results"][root] = subfolder_results
    
    # Print summary
    total = results["summary"]["total_subfolders_checked"]
    with_duplicates = results["summary"]["subfolders_with_duplicates"]
    
    print("\n" + "="*50)
    print(f"SUMMARY: Checked {total} subfolders")
    
    if with_duplicates == 0:
        print("No duplicate chunk_ids found in any subfolder!")
    else:
        print(f"Found duplicate chunk_ids in {with_duplicates} subfolder(s)!")
    
    # Determine log directory - either use logs within papers_dir or standalone logs
    if os.path.isabs(papers_dir):
        # If absolute path, put logs in that directory
        log_dir = os.path.join(papers_dir, "logs")
    else:
        # For relative paths, use data/logs
        log_dir = "data/logs"
        
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"chunk_id_check_{timestamp}.json")
    
    with open(log_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {log_file}")

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Check for duplicate chunk IDs in papers directory')
    parser.add_argument('--dir', type=str, help='Papers directory (default: data/papers)', default="data/papers")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the check with the specified directory
    check_chunk_ids_in_pages_dir(args.dir)

if __name__ == "__main__":
    main() 