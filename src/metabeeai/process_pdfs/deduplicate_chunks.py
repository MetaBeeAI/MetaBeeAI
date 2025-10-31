#!/usr/bin/env python3
"""
Chunk deduplication module for the PDF processing pipeline.
This module provides functions to identify and remove duplicate text chunks
while preserving all chunk IDs and metadata.
"""

import json
import logging
from typing import List, Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce verbosity
logger = logging.getLogger(__name__)


def analyze_chunk_uniqueness(chunks: List[Dict[str, Any]]) -> dict:
    """
    Analyze the uniqueness of chunks in a paper.
    
    Args:
        chunks (List[Dict[str, Any]]): List of chunks to analyze.
        
    Returns:
        dict: Analysis results including duplicate statistics.
    """
    if not chunks:
        return {
            "total_chunks": 0,
            "unique_chunks": 0,
            "duplicate_chunks": 0,
            "duplication_rate": 0.0,
            "duplicate_groups": 0
        }
    
    # Group chunks by text content
    text_groups = {}
    for chunk in chunks:
        text_content = chunk.get('text', '').strip()
        chunk_id = chunk.get('chunk_id', 'unknown')
        
        if text_content in text_groups:
            text_groups[text_content]['chunk_ids'].append(chunk_id)
        else:
            text_groups[text_content] = {
                'chunk_ids': [chunk_id],
                'text_preview': text_content[:100] + '...' if len(text_content) > 100 else text_content
            }
    
    total_chunks = len(chunks)
    unique_chunks = len(text_groups)
    duplicate_chunks = total_chunks - unique_chunks
    duplication_rate = (duplicate_chunks / total_chunks) * 100 if total_chunks > 0 else 0
    
    # Find groups with duplicates
    duplicate_groups = {text: group for text, group in text_groups.items() if len(group['chunk_ids']) > 1}
    
    return {
        "total_chunks": total_chunks,
        "unique_chunks": unique_chunks,
        "duplicate_chunks": duplicate_chunks,
        "duplication_rate": round(duplication_rate, 2),
        "duplicate_groups": len(duplicate_groups),
        "duplicate_details": [
            {
                "text_preview": group['text_preview'],
                "chunk_ids": group['chunk_ids'],
                "count": len(group['chunk_ids'])
            }
            for text, group in duplicate_groups.items()
        ]
    }


def deduplicate_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate chunks based on text content while preserving chunk IDs.
    
    Args:
        chunks (List[Dict[str, Any]]): List of chunks to deduplicate.
        
    Returns:
        List[Dict[str, Any]]: Deduplicated list of chunks with merged chunk IDs.
    """
    if not chunks:
        return chunks
    
    # Create a dictionary to group chunks by text content
    text_groups = {}
    
    for chunk in chunks:
        text_content = chunk.get('text', '').strip()
        chunk_id = chunk.get('chunk_id', 'unknown')
        
        if text_content in text_groups:
            # Add this chunk_id to the existing group
            text_groups[text_content]['chunk_ids'].append(chunk_id)
            # Keep the chunk with the most metadata (merge if needed)
            existing_chunk = text_groups[text_content]['chunk']
            if len(chunk) > len(existing_chunk):
                text_groups[text_content]['chunk'] = chunk
        else:
            # Create new group
            text_groups[text_content] = {
                'chunk': chunk,
                'chunk_ids': [chunk_id]
            }
    
    # Create deduplicated list with merged chunk IDs
    deduplicated_chunks = []
    for text_content, group in text_groups.items():
        chunk = group['chunk'].copy()
        chunk['chunk_ids'] = group['chunk_ids']  # Replace single ID with list of all IDs
        chunk['original_chunk_id'] = chunk.get('chunk_id')  # Keep original for reference
        chunk['chunk_id'] = group['chunk_ids'][0]  # Use first ID as primary
        deduplicated_chunks.append(chunk)
    
    return deduplicated_chunks


def get_duplicate_summary(chunks: List[Dict[str, Any]]) -> str:
    """
    Get a human-readable summary of duplicate chunks.
    
    Args:
        chunks (List[Dict[str, Any]]): List of chunks to analyze.
        
    Returns:
        str: Summary of duplicate information.
    """
    analysis = analyze_chunk_uniqueness(chunks)
    
    if analysis['duplicate_chunks'] == 0:
        return "No duplicate chunks found."
    
    summary = f"Found {analysis['duplicate_chunks']} duplicate chunks ({analysis['duplication_rate']}% duplication rate). "
    summary += f"Reduced from {analysis['total_chunks']} to {analysis['unique_chunks']} unique chunks.\n\n"
    
    if analysis['duplicate_details']:
        summary += "Duplicate groups:\n"
        for i, group in enumerate(analysis['duplicate_details'][:5], 1):  # Show first 5 groups
            summary += f"  {i}. {group['text_preview']}\n"
            summary += f"     IDs: {', '.join(group['chunk_ids'][:3])}{'...' if len(group['chunk_ids']) > 3 else ''}\n"
            summary += f"     Count: {group['count']}\n\n"
        
        if len(analysis['duplicate_details']) > 5:
            summary += f"  ... and {len(analysis['duplicate_details']) - 5} more duplicate groups.\n"
    
    return summary


def process_merged_json_file(json_file_path: Path, output_path: Path = None) -> dict:
    """
    Process a merged JSON file to deduplicate chunks and save the result.
    
    Args:
        json_file_path (Path): Path to the input merged JSON file.
        output_path (Path): Path to save the deduplicated output (defaults to overwrite input).
        
    Returns:
        dict: Deduplication statistics and results.
    """
    if output_path is None:
        output_path = json_file_path
    
    logger.info(f"Processing {json_file_path}")
    
    try:
        # Load the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract chunks
        chunks = data.get('data', {}).get('chunks', [])
        if not chunks:
            logger.warning(f"No chunks found in {json_file_path}")
            return {"error": "No chunks found"}
        
        # Analyze uniqueness
        uniqueness_analysis = analyze_chunk_uniqueness(chunks)
        logger.info(f"Found {uniqueness_analysis['duplicate_chunks']} duplicates ({uniqueness_analysis['duplication_rate']}% duplication rate)")
        
        # Deduplicate if needed
        if uniqueness_analysis['duplicate_chunks'] > 0:
            logger.info(f"Deduplicating chunks: {uniqueness_analysis['duplicate_chunks']} duplicates found")
            deduplicated_chunks = deduplicate_chunks(chunks)
            
            # Update the data structure
            data['data']['chunks'] = deduplicated_chunks
            
            # Add deduplication metadata
            data['deduplication_info'] = {
                "original_chunks": uniqueness_analysis['total_chunks'],
                "unique_chunks": uniqueness_analysis['unique_chunks'],
                "duplicates_removed": uniqueness_analysis['duplicate_chunks'],
                "duplication_rate": uniqueness_analysis['duplication_rate'],
                "duplicate_groups": uniqueness_analysis['duplicate_groups']
            }
            
            # Save the deduplicated file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved deduplicated file to {output_path}")
            
            return {
                "success": True,
                "input_file": str(json_file_path),
                "output_file": str(output_path),
                "deduplication_stats": uniqueness_analysis,
                "deduplication_info": data['deduplication_info']
            }
        else:
            logger.info("No duplicates found, file unchanged")
            return {
                "success": True,
                "input_file": str(json_file_path),
                "output_file": str(json_file_path),
                "deduplication_stats": uniqueness_analysis,
                "message": "No duplicates found, file unchanged"
            }
            
    except Exception as e:
        logger.error(f"Error processing {json_file_path}: {e}")
        return {"error": str(e), "input_file": str(json_file_path)}


if __name__ == "__main__":
    # Test the module with sample data
    print("Testing deduplication module...")
    
    # Create sample chunks
    sample_chunks = [
        {"chunk_id": "chunk_001", "text": "The study used Apis mellifera workers from 20 colonies."},
        {"chunk_id": "chunk_002", "text": "Bees were exposed to imidacloprid at 10 ppb concentration."},
        {"chunk_id": "chunk_003", "text": "The study used Apis mellifera workers from 20 colonies."},  # Duplicate
        {"chunk_id": "chunk_004", "text": "Results showed significant effects on foraging behavior."},
    ]
    
    # Test analysis
    analysis = analyze_chunk_uniqueness(sample_chunks)
    print(f"Analysis: {analysis}")
    
    # Test deduplication
    deduplicated = deduplicate_chunks(sample_chunks)
    print(f"Deduplicated: {len(deduplicated)} chunks")
    
    # Test summary
    summary = get_duplicate_summary(sample_chunks)
    print(f"Summary:\n{summary}")
