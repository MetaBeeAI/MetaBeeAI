#!/usr/bin/env python3
"""
Batch deduplication script for processing all merged_v2.json files in the METABEEAI_DATA_DIR.
This script will find all paper folders and deduplicate their merged_v2.json files.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import json

# Try to get the papers directory from config, with fallbacks
def get_papers_dir():
    """Get the papers directory path with multiple fallback options."""
    # Try to load from config.py if available
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        sys.path.append(parent_dir)
        
        # Try to import config without dotenv dependency
        import importlib.util
        config_path = os.path.join(parent_dir, "config.py")
        
        if os.path.exists(config_path):
            # Read config file manually to avoid dotenv dependency
            with open(config_path, 'r') as f:
                config_content = f.read()
            
            # Extract METABEEAI_DATA_DIR from config content
            import re
            match = re.search(r'METABEEAI_DATA_DIR["\']?\s*,\s*["\']?([^"\']+)["\']?', config_content)
            if match:
                base_dir = match.group(1)
                papers_dir = os.path.join(base_dir, "papers")
                if os.path.exists(papers_dir):
                    return papers_dir
    except Exception as e:
        pass
    
    # Fallback 1: Check common locations
    common_paths = [
        os.path.join(os.path.expanduser("~"), "Documents", "MetaBeeAI_dataset2", "papers"),
        os.path.join(os.path.expanduser("~"), "Documents", "MetaBeeAI_dataset2"),
        "data/papers",
        "papers"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # Fallback 2: Use current working directory
    return os.path.join(os.getcwd(), "papers")

# Import the deduplication module
from deduplicate_chunks import process_merged_json_file, analyze_chunk_uniqueness

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce verbosity - only show warnings and errors
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_paper_folders(base_dir: Path) -> List[Path]:
    """
    Find all paper folders in the base directory.
    
    Args:
        base_dir (Path): Base directory containing paper folders.
        
    Returns:
        List[Path]: List of paper folder paths.
    """
    paper_folders = []
    
    if not base_dir.exists():
        logger.error(f"Base directory does not exist: {base_dir}")
        return paper_folders
    
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.isdigit():
            paper_folders.append(item)
    
    # Sort numerically
    paper_folders.sort(key=lambda x: int(x.name))
    

    
    return paper_folders


def find_merged_json_files(paper_folders: List[Path]) -> List[Dict[str, Any]]:
    """
    Find all merged_v2.json files in paper folders.
    
    Args:
        paper_folders (List[Path]): List of paper folder paths.
        
    Returns:
        List[Dict[str, Any]]: List of file information dictionaries.
    """
    merged_files = []
    
    for paper_folder in paper_folders:
        pages_dir = paper_folder / "pages"
        merged_json_path = pages_dir / "merged_v2.json"
        
        if merged_json_path.exists():
            merged_files.append({
                "paper_id": paper_folder.name,
                "paper_path": paper_folder,
                "json_path": merged_json_path,
                "pages_dir": pages_dir
            })
        else:
            logger.warning(f"No merged_v2.json found in {paper_folder}")
    
    return merged_files


def process_single_paper(file_info: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """
    Process a single paper's merged_v2.json file.
    
    Args:
        file_info (Dict[str, Any]): Information about the file to process.
        dry_run (bool): If True, only analyze without making changes.
        
    Returns:
        Dict[str, Any]: Processing results.
    """
    paper_id = file_info["paper_id"]
    json_path = file_info["json_path"]
    
    logger.info(f"Processing paper {paper_id}: {json_path}")
    
    try:
        if dry_run:
            # Just analyze without deduplicating
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunks = data.get('data', {}).get('chunks', [])
            analysis = analyze_chunk_uniqueness(chunks)
            
            return {
                "paper_id": paper_id,
                "status": "analyzed",
                "file_path": str(json_path),
                "analysis": analysis,
                "message": "Dry run - no changes made"
            }
        else:
            # Actually process the file
            result = process_merged_json_file(json_path)
            result["paper_id"] = paper_id
            
            # Debug: log what we got back
            logger.warning(f"Paper {paper_id} result: {result}")
            
            return result
            
    except Exception as e:
        logger.error(f"Error processing paper {paper_id}: {e}")
        return {
            "paper_id": paper_id,
            "status": "error",
            "file_path": str(json_path),
            "error": str(e)
        }


def batch_deduplicate(base_dir: Path = None, dry_run: bool = False, 
                     start_paper: int = None, end_paper: int = None, 
                     folder_list: list = None) -> Dict[str, Any]:
    """
    Process all merged_v2.json files in the base directory.
    
    Args:
        base_dir (Path): Base directory containing paper folders.
        dry_run (bool): If True, only analyze without making changes.
        start_paper (int): First paper number to process (inclusive) - for numeric folders.
        end_paper (int): Last paper number to process (inclusive) - for numeric folders.
        folder_list (list): List of folder names to process (overrides start_paper/end_paper).
        
    Returns:
        Dict[str, Any]: Summary of processing results.
    """
    if base_dir is None:
        base_dir = Path(get_papers_dir())
    
    logger.info(f"Starting batch deduplication in: {base_dir}")
    if dry_run:
        logger.info("DRY RUN MODE - No files will be modified")
    
    # Find all paper folders
    paper_folders = find_paper_folders(base_dir)
    logger.info(f"Found {len(paper_folders)} paper folders")
    
    # Filter by folder list if specified
    if folder_list is not None:
        filtered_folders = []
        folder_names = set(folder_list)  # Convert to set for faster lookup
        for folder in paper_folders:
            if folder.name in folder_names:
                filtered_folders.append(folder)
        paper_folders = filtered_folders
        logger.info(f"Filtered to {len(paper_folders)} papers from provided folder list")
    # Otherwise filter by paper range if specified (for backward compatibility)
    elif start_paper is not None or end_paper is not None:
        filtered_folders = []
        for folder in paper_folders:
            try:
                paper_num = int(folder.name)
                if start_paper is not None and paper_num < start_paper:
                    continue
                if end_paper is not None and paper_num > end_paper:
                    continue
                filtered_folders.append(folder)
            except ValueError:
                # Skip folders that don't have numeric names
                continue
        
        paper_folders = filtered_folders
        logger.info(f"Filtered to {len(paper_folders)} papers in range {start_paper or 'start'} to {end_paper or 'end'}")
    
    # Find merged JSON files
    merged_files = find_merged_json_files(paper_folders)
    logger.info(f"Found {len(merged_files)} merged_v2.json files to process")
    
    if not merged_files:
        logger.warning("No merged_v2.json files found to process")
        return {"status": "no_files_found", "total_papers": 0}
    
    # Process each file
    results = []
    total_processed = 0
    total_duplicates_removed = 0
    
    for file_info in merged_files:
        result = process_single_paper(file_info, dry_run)
        results.append(result)
        
        # Check if processing was successful (either status="success" or success=True)
        if result.get("status") == "success" or result.get("success") == True:
            total_processed += 1
            # Count duplicates from deduplication_info
            if "deduplication_info" in result:
                duplicates = result["deduplication_info"].get("duplicates_removed", 0)
                total_duplicates_removed += duplicates
                logger.warning(f"Paper {result.get('paper_id')}: Found {duplicates} duplicates in deduplication_info")
            # Also check deduplication_stats as fallback
            elif "deduplication_stats" in result:
                duplicates = result["deduplication_stats"].get("duplicate_chunks", 0)
                total_duplicates_removed += duplicates
                logger.warning(f"Paper {result.get('paper_id')}: Found {duplicates} duplicates in deduplication_stats")
            else:
                logger.warning(f"Paper {result.get('paper_id')}: No duplicate info found in result keys: {list(result.keys())}")
        elif result.get("status") == "analyzed":
            total_processed += 1
            # In dry-run mode, count duplicates from the analysis
            if "analysis" in result:
                duplicates = result["analysis"].get("duplicate_chunks", 0)
                total_duplicates_removed += duplicates
                logger.warning(f"Paper {result.get('paper_id')}: Found {duplicates} duplicates in analysis")
        else:
            logger.warning(f"Paper {result.get('paper_id')}: Unexpected result structure: {list(result.keys())}")
    
    # Generate summary
    summary = {
        "status": "completed",
        "total_papers": len(merged_files),
        "processed_papers": total_processed,
        "total_duplicates_removed": total_duplicates_removed,
        "dry_run": dry_run,
        "base_directory": str(base_dir),
        "results": results
    }
    
    # Log summary
    logger.info(f"Batch processing completed:")
    logger.info(f"  Total papers: {len(merged_files)}")
    logger.info(f"  Processed: {total_processed}")
    logger.info(f"  Total duplicates removed: {total_duplicates_removed}")
    
    return summary


def save_results_summary(summary: Dict[str, Any], output_file: Path = None) -> None:
    """
    Save the processing results summary to a file.
    
    Args:
        summary (Dict[str, Any]): Processing summary to save.
        output_file (Path): Output file path (defaults to timestamped file).
    """
    if output_file is None:
        timestamp = summary.get("timestamp", "unknown")
        output_file = Path(f"deduplication_summary_{timestamp}.json")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Results summary saved to: {output_file}")
    except Exception as e:
        logger.error(f"Error saving results summary: {e}")


def main():
    """Main entry point for the batch deduplication script."""
    parser = argparse.ArgumentParser(
        description="Batch deduplicate merged_v2.json files in paper folders"
    )
    
    parser.add_argument(
        "--base-dir",
        type=str,
        help="Base directory containing paper folders (defaults to METABEEAI_DATA_DIR)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze files without making changes"
    )
    
    parser.add_argument(
        "--start-paper",
        type=int,
        help="First paper number to process (inclusive)"
    )
    
    parser.add_argument(
        "--end-paper", 
        type=int,
        help="Last paper number to process (inclusive)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for results summary (defaults to timestamped file)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine base directory
    if args.base_dir:
        base_dir = Path(args.base_dir)
    else:
        base_dir = None  # Will use default from config
    
    # Run batch processing
    try:
        summary = batch_deduplicate(
            base_dir=base_dir,
            dry_run=args.dry_run,
            start_paper=args.start_paper,
            end_paper=args.end_paper
        )
        
        # Save results if requested
        if args.output:
            save_results_summary(summary, Path(args.output))
        elif not args.dry_run:
            # Auto-save results for actual processing runs
            save_results_summary(summary)
        
        # Print final summary
        print("\n" + "="*60)
        print("BATCH DEDUPLICATION SUMMARY")
        print("="*60)
        print(f"Status: {summary['status']}")
        print(f"Total papers: {summary['total_papers']}")
        
        if summary['status'] == 'no_files_found':
            print("No merged_v2.json files found to process.")
            print("Make sure you have:")
            print("1. Run the merger tool to create merged_v2.json files")
            print("2. Specified the correct paper range")
            print("3. Papers are in the expected directory structure")
        else:
            print(f"Processed: {summary.get('processed_papers', 0)}")
            print(f"Total duplicates removed: {summary.get('total_duplicates_removed', 0)}")
            print(f"Dry run: {summary['dry_run']}")
            print(f"Base directory: {summary['base_directory']}")
            
            if summary['dry_run']:
                print("\nThis was a dry run. No files were modified.")
                print("Run without --dry-run to actually deduplicate files.")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
