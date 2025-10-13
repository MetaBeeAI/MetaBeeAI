# config.py
# Centralized configuration for MetaBeeAI pipeline

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Data directory configuration
# Default to "data" if not specified in environment
DEFAULT_DATA_DIR = "data"

def get_data_dir():
    """
    Get the base data directory from environment variable or use default.
    
    Returns:
        str: Path to the base data directory
    """
    return os.getenv("METABEEAI_DATA_DIR", DEFAULT_DATA_DIR)

def get_papers_dir():
    """
    Get the papers directory path.
    
    Returns:
        str: Path to the papers directory
    """
    base_dir = get_data_dir()
    papers_dir = os.path.join(base_dir, "papers")
    return papers_dir

def get_logs_dir():
    """
    Get the logs directory path.
    
    Returns:
        str: Path to the logs directory
    """
    base_dir = get_data_dir()
    logs_dir = os.path.join(base_dir, "logs")
    return logs_dir

def get_output_dir():
    """
    Get the output directory path.
    
    Returns:
        str: Path to the output directory
    """
    base_dir = get_data_dir()
    output_dir = os.path.join(base_dir, "output")
    return output_dir

def ensure_directories_exist():
    """
    Ensure that all necessary directories exist.
    Creates them if they don't exist.
    """
    directories = [
        get_data_dir(),
        get_papers_dir(),
        get_logs_dir(),
        get_output_dir()
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

# Convenience variables for backward compatibility
BASE_DIR = get_data_dir()
PAPERS_DIR = get_papers_dir()
LOGS_DIR = get_logs_dir()
OUTPUT_DIR = get_output_dir()
