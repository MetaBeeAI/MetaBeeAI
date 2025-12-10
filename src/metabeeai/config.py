# Centralized configuration loader for MetaBeeAI
# Hierarchy: CLI arg > env var > YAML > hardcoded default
import logging
import os

import yaml
from dotenv import load_dotenv

# Use standard logging to avoid circular import with metabeeai.logging
logger = logging.getLogger(__name__)

load_dotenv()

DEFAULT_CONFIG_PATHS = [
    os.path.join(os.getcwd(), "config.yaml"),
]

# Cache for loaded config to avoid re-reading files
_config_cache = {}


def load_config(config_path=None):
    """
    Load config from YAML file. Path is determined by:
    1. config_path arg (if provided)
    2. METABEEAI_CONFIG_FILE env var
    3. Default location (./config.yaml in current directory)

    Results are cached. Returns dict (empty if no file found).
    """
    # Determine which config file to use
    path = (
        config_path
        or os.environ.get("METABEEAI_CONFIG_FILE")
        or next((p for p in DEFAULT_CONFIG_PATHS if os.path.isfile(p)), None)
    )

    # Check cache
    if path and path in _config_cache:
        return _config_cache[path]

    # Load from file
    if path and os.path.isfile(path):
        with open(path, "r") as f:
            config = yaml.safe_load(f) or {}
            _config_cache[path] = config
            return config

    return {}


def get_config_value(key, config_path=None, env_var=None, default=None):
    """
    Get a config parameter value using the hierarchy:
    1. YAML config file (explicit config_path or METABEEAI_CONFIG_FILE env var)
    2. Environment variable (if env_var provided)
    3. Default value

    Note: Check CLI args BEFORE calling this function.

    Full hierarchy (handled by caller + this function):
    - CLI arg (caller checks this first)
    - Config file from CLI arg (config_path parameter)
    - Config file from METABEEAI_CONFIG_FILE env var (load_config checks this)
    - Direct env var for the parameter (METABEEAI_PAPERS_DIR, etc)
    - Default value

    Args:
        key: Config key (use dots for nested keys: 'llm.model')
        config_path: Path to config file (if None, uses METABEEAI_CONFIG_FILE env or defaults)
        env_var: Environment variable name to check as fallback
        default: Default value if not found elsewhere

    Returns:
        The config value from the highest priority source

    Example:
        # In entrypoint after argparse
        data_dir = args.data_dir if args.data_dir is not None else get_config_value(
            'data_dir',
            config_path=args.config,
            env_var='METABEEAI_DATA_DIR',
            default='data'
        )
    """
    # Check YAML config first (load and cache)
    config = load_config(config_path)
    if config:
        # Support dot notation: 'llm.model' -> config['llm']['model']
        if "." in key:
            value = config
            for part in key.split("."):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    value = None
                    break
            if value is not None:
                return value
        # Direct key lookup
        if key in config:
            return config[key]

    # Check environment variable as fallback
    if env_var and os.environ.get(env_var) is not None:
        return os.environ[env_var]

    return default


# Registry of common config parameters (shared across entrypoints)
COMMON_PARAMS = {
    "data_dir": {
        "env_var": "METABEEAI_DATA_DIR",
        "yaml_key": "data_dir",
        "default": "data",
    },
    "papers_dir": {
        "env_var": "METABEEAI_PAPERS_DIR",
        "yaml_key": "papers_dir",
        "default": "data/papers",
    },
    "output_dir": {
        "env_var": "METABEEAI_OUTPUT_DIR",
        "yaml_key": "output_dir",
        "default": "data/output",
    },
    "results_dir": {
        "env_var": "METABEEAI_RESULTS_DIR",
        "yaml_key": "results_dir",
        "default": "data/results",
    },
    "logs_dir": {
        "env_var": "METABEEAI_LOGS_DIR",
        "yaml_key": "logs_dir",
        "default": None,  # Will default to data_dir/logs if not set
    },
    "log_level": {
        "env_var": "METABEEAI_LOG_LEVEL",
        "yaml_key": "log_level",
        "default": "INFO",
    },
    "openai_api_key": {
        "env_var": "OPENAI_API_KEY",
        "yaml_key": "openai_api_key",
        "default": None,
    },
    "landing_api_key": {
        "env_var": "LANDING_AI_API_KEY",
        "yaml_key": "landing_api_key",
        "default": None,
    },
}


def get_config_param(name, config_path=None):
    """
    Get a common config parameter by name.

    Convenience wrapper for parameters shared across entrypoints.
    For custom params, use get_config_value() directly.

    Args:
        name: Parameter name (must be in COMMON_PARAMS)
        config_path: Path to config file

    Returns:
        The config value

    Example:
        data_dir = args.data_dir if args.data_dir is not None else get_config_param(
            'data_dir',
            config_path=args.config
        )
    """
    if name not in COMMON_PARAMS:
        raise ValueError(f"Unknown param: '{name}'. Available: {list(COMMON_PARAMS.keys())}")

    p = COMMON_PARAMS[name]
    return get_config_value(p["yaml_key"], config_path=config_path, env_var=p["env_var"], default=p["default"])


def get_papers_dir(config_path=None):
    """Return the papers directory from config/env/defaults."""
    return get_config_param("papers_dir", config_path=config_path)


def get_data_dir(config_path=None):
    """Return the base data directory from config/env/defaults."""
    return get_config_param("data_dir", config_path=config_path)
