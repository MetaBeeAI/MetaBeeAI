# Centralized configuration loader for MetaBeeAI
# Hierarchy: CLI arg > env var > YAML > hardcoded default
import os
import yaml

DEFAULT_CONFIG_PATHS = [
    os.path.join(os.getcwd(), "config.yaml"),
    os.path.expanduser("~/.metabeeai/config.yaml"),
]

def load_config(cli_config_path=None):
    """
    Load config from YAML file, with path determined by:
    1. CLI arg (if provided)
    2. METABEEAI_CONFIG_FILE env var
    3. Default locations (cwd/config.yaml, ~/.metabeeai/config.yaml)
    Returns a dict (may be empty if no file found).
    """
    config_path = (
        cli_config_path
        or os.environ.get("METABEEAI_CONFIG_FILE")
        or next((p for p in DEFAULT_CONFIG_PATHS if os.path.isfile(p)), None)
    )
    if config_path and os.path.isfile(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def get_config_value(key, cli_value=None, config=None, env_var=None, default=None):
    """
    Get the effective value for a config parameter, using the hierarchy:
    1. CLI arg (cli_value)
    2. Environment variable (env_var, if provided)
    3. YAML config (config dict, if provided)
    4. Hardcoded default
    """
    if cli_value is not None:
        return cli_value
    if env_var and os.environ.get(env_var) is not None:
        return os.environ[env_var]
    if config and key in config:
        return config[key]
    return default

# Example usage in an entrypoint:
# config = load_config(cli_config_path=args.config)
# papers_dir = get_config_value("papers_dir", cli_value=args.papers_dir, config=config, env_var="METABEEAI_PAPERS_DIR", default="./data/papers")
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
    directories = [get_data_dir(), get_papers_dir(), get_logs_dir(), get_output_dir()]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# Convenience variables for backward compatibility
BASE_DIR = get_data_dir()
PAPERS_DIR = get_papers_dir()
LOGS_DIR = get_logs_dir()
OUTPUT_DIR = get_output_dir()
