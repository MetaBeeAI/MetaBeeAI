"""
Tests for metabeeai.config module.

Tests config hierarchy (CLI args > env vars > YAML config > defaults),
load_config(), get_config_value(), get_config_param(), and COMMON_PARAMS.
"""

import os
from unittest.mock import patch

import pytest

from metabeeai import config


class TestLoadConfig:
    """Test load_config() function."""

    def test_load_config_returns_empty_when_no_file(self):
        """Test that load_config returns empty dict when no config file exists."""
        result = config.load_config("/nonexistent/path/to/config.yaml")
        assert result == {}

    def test_load_config_from_yaml_file(self, tmp_path):
        """Test loading a valid YAML config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
data_dir: ./custom_data
papers_dir: ./custom_papers
log_level: DEBUG
openai_api_key: sk-test123
""")

        result = config.load_config(str(config_file))

        assert result is not None
        assert result["data_dir"] == "./custom_data"
        assert result["papers_dir"] == "./custom_papers"
        assert result["log_level"] == "DEBUG"
        assert result["openai_api_key"] == "sk-test123"

    def test_load_config_with_nested_structure(self, tmp_path):
        """Test loading YAML config with nested structure."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
data_dir: ./data
llm:
  model: gpt-4
  temperature: 0.7
  max_tokens: 1000
benchmarking:
  batch_size: 10
  max_retries: 3
""")

        result = config.load_config(str(config_file))

        assert result["data_dir"] == "./data"
        assert result["llm"]["model"] == "gpt-4"
        assert result["llm"]["temperature"] == 0.7
        assert result["llm"]["max_tokens"] == 1000
        assert result["benchmarking"]["batch_size"] == 10

    def test_load_config_from_env_var(self, tmp_path, monkeypatch):
        """Test loading config file path from METABEEAI_CONFIG_FILE env var."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("data_dir: ./env_data\n")

        monkeypatch.setenv("METABEEAI_CONFIG_FILE", str(config_file))

        result = config.load_config()

        assert result is not None
        assert result["data_dir"] == "./env_data"

    def test_load_config_caches_result(self, tmp_path):
        """Test that load_config caches the result."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("data_dir: ./cached_data\n")

        # Load twice
        result1 = config.load_config(str(config_file))
        result2 = config.load_config(str(config_file))

        # Should return same cached object
        assert result1 is result2


class TestGetConfigValue:
    """Test get_config_value() function and config hierarchy."""

    def test_get_config_value_returns_default(self):
        """Test that get_config_value returns default when no other source."""
        result = config.get_config_value("nonexistent_key", default="default_value")
        assert result == "default_value"

    def test_get_config_value_from_env_var(self, monkeypatch):
        """Test that env var takes precedence over default."""
        monkeypatch.setenv("TEST_ENV_VAR", "env_value")

        result = config.get_config_value("test_key", env_var="TEST_ENV_VAR", default="default_value")

        assert result == "env_value"

    def test_get_config_value_from_yaml(self, tmp_path):
        """Test that YAML config is used when no env var."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("test_key: yaml_value\n")

        result = config.get_config_value(
            "test_key", config_path=str(config_file), env_var="NONEXISTENT_VAR", default="default_value"
        )

        assert result == "yaml_value"

    def test_config_hierarchy_yaml_over_env(self, tmp_path, monkeypatch):
        """Test that YAML config takes precedence over env var."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("test_key: yaml_value\n")
        monkeypatch.setenv("TEST_ENV_VAR", "env_value")

        result = config.get_config_value(
            "test_key", config_path=str(config_file), env_var="TEST_ENV_VAR", default="default_value"
        )

        assert result == "yaml_value"

    def test_config_hierarchy_yaml_over_default(self, tmp_path):
        """Test that YAML config takes precedence over default."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("test_key: yaml_value\n")

        result = config.get_config_value("test_key", config_path=str(config_file), default="default_value")

        assert result == "yaml_value"

    def test_get_config_value_with_dot_notation(self, tmp_path):
        """Test accessing nested YAML values with dot notation."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  model: gpt-4
  temperature: 0.7
""")

        result = config.get_config_value("llm.model", config_path=str(config_file))

        assert result == "gpt-4"

    def test_get_config_value_dot_notation_missing_key(self, tmp_path):
        """Test that missing nested key returns default."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("llm:\n  model: gpt-4\n")

        result = config.get_config_value("llm.nonexistent", config_path=str(config_file), default="default_value")

        assert result == "default_value"


class TestCommonParams:
    """Test COMMON_PARAMS registry and get_config_param()."""

    def test_common_params_structure(self):
        """Test that COMMON_PARAMS has expected structure."""
        expected_keys = [
            "data_dir",
            "papers_dir",
            "output_dir",
            "results_dir",
            "logs_dir",
            "log_level",
            "openai_api_key",
            "landing_api_key",
        ]

        assert set(config.COMMON_PARAMS.keys()) == set(expected_keys)

        # Check each param has required fields
        for name, param in config.COMMON_PARAMS.items():
            assert "env_var" in param
            assert "yaml_key" in param
            assert "default" in param

    def test_get_config_param_returns_default(self):
        """Test get_config_param returns default value."""
        result = config.get_config_param("data_dir")
        assert result == "data"

        result = config.get_config_param("log_level")
        assert result == "INFO"

    def test_get_config_param_from_env(self, monkeypatch):
        """Test get_config_param reads from environment variable."""
        monkeypatch.setenv("METABEEAI_DATA_DIR", "/custom/data")

        result = config.get_config_param("data_dir")

        assert result == "/custom/data"

    def test_get_config_param_from_yaml(self, tmp_path):
        """Test get_config_param reads from YAML config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
data_dir: /yaml/data
papers_dir: /yaml/papers
log_level: DEBUG
""")

        result = config.get_config_param("data_dir", config_path=str(config_file))
        assert result == "/yaml/data"

        result = config.get_config_param("log_level", config_path=str(config_file))
        assert result == "DEBUG"

    def test_get_config_param_hierarchy(self, tmp_path, monkeypatch):
        """Test full config hierarchy: yaml > env > default."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
data_dir: /yaml/data
papers_dir: /yaml/papers
log_level: DEBUG
""")

        # Set env var for data_dir (YAML should take precedence)
        monkeypatch.setenv("METABEEAI_DATA_DIR", "/env/data")

        # data_dir: YAML takes precedence over env var
        assert config.get_config_param("data_dir", str(config_file)) == "/yaml/data"

        # papers_dir: YAML value (no env var set)
        assert config.get_config_param("papers_dir", str(config_file)) == "/yaml/papers"

        # output_dir: default value (not in YAML, no env var)
        assert config.get_config_param("output_dir", str(config_file)) == "data/output"

    def test_get_config_param_api_keys(self, tmp_path, monkeypatch):
        """Test API key config parameters."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
openai_api_key: yaml-key-123
landing_api_key: yaml-landing-456
""")

        # From YAML
        assert config.get_config_param("openai_api_key", str(config_file)) == "yaml-key-123"

        # YAML takes precedence over env var
        monkeypatch.setenv("OPENAI_API_KEY", "env-key-789")
        assert config.get_config_param("openai_api_key", str(config_file)) == "yaml-key-123"

    def test_get_config_param_logs_dir_default_none(self):
        """Test that logs_dir defaults to None (not a path)."""
        result = config.get_config_param("logs_dir")
        assert result is None

    def test_get_config_param_invalid_name(self):
        """Test get_config_param with invalid parameter name."""
        with pytest.raises(ValueError, match="Unknown param: 'nonexistent_param'"):
            config.get_config_param("nonexistent_param")


class TestConfigIntegration:
    """Integration tests for config system."""

    def test_config_with_cli_flag(self, tmp_path, monkeypatch):
        """Test config loaded via --config CLI flag (via env var)."""
        config_file = tmp_path / "cli_config.yaml"
        config_file.write_text("""
data_dir: /cli/data
papers_dir: /cli/papers
log_level: WARNING
openai_api_key: cli-key-123
""")

        # CLI sets METABEEAI_CONFIG_FILE env var
        monkeypatch.setenv("METABEEAI_CONFIG_FILE", str(config_file))

        # Config should be loaded from this file
        result = config.load_config()
        assert result["data_dir"] == "/cli/data"
        assert result["log_level"] == "WARNING"

    def test_config_precedence_all_sources(self, tmp_path, monkeypatch):
        """Test full precedence chain with all sources."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
data_dir: /yaml/data
papers_dir: /yaml/papers
output_dir: /yaml/output
log_level: DEBUG
""")

        # Set some env vars
        monkeypatch.setenv("METABEEAI_DATA_DIR", "/env/data")
        monkeypatch.setenv("METABEEAI_LOG_LEVEL", "ERROR")

        # Test precedence for each param
        # data_dir: env var wins
        assert config.get_config_param("data_dir", str(config_file)) == "/yaml/data"

        # papers_dir: YAML wins (no env var)
        assert config.get_config_param("papers_dir", str(config_file)) == "/yaml/papers"

        # output_dir: YAML wins (no env var)
        assert config.get_config_param("output_dir", str(config_file)) == "/yaml/output"

        # results_dir: default wins (not in YAML, no env var)
        assert config.get_config_param("results_dir", str(config_file)) == "data/results"

        # log_level: YAML wins over env
        assert config.get_config_param("log_level", str(config_file)) == "DEBUG"

    class TestCLIConfigIntegration:
        """Test CLI --config flag integration with config system."""

        @patch("metabeeai.cli.handle_llm_command")
        def test_cli_config_flag_sets_env_var(self, mock_handler, tmp_path):
            """Test that --config CLI flag sets METABEEAI_CONFIG_FILE env var."""
            from metabeeai import cli

            mock_handler.side_effect = SystemExit(0)

            # Create a temporary config file
            config_file = tmp_path / "cli_config.yaml"
            config_file.write_text("""
    data_dir: ./cli_test_data
    papers_dir: ./cli_test_papers
    log_level: DEBUG
    """)

            # --config is a global argument and must be placed before the subcommand
            with patch("sys.argv", ["metabeeai", "--config", str(config_file), "llm"]):
                with pytest.raises(SystemExit):
                    cli.main()

            # Verify the config argument was passed through
            args = mock_handler.call_args[0][0]
            assert args.config == str(config_file)

        @patch("metabeeai.cli.handle_llm_command")
        def test_cli_config_flag_loads_yaml(self, mock_handler, tmp_path, monkeypatch):
            """Test that --config flag causes YAML to be loaded."""
            from metabeeai import cli

            mock_handler.side_effect = SystemExit(0)

            config_file = tmp_path / "test_config.yaml"
            config_file.write_text("""
    data_dir: /cli/yaml/data
    papers_dir: /cli/yaml/papers
    """)

            # Clear any existing config env var
            monkeypatch.delenv("METABEEAI_CONFIG_FILE", raising=False)

            with patch("sys.argv", ["metabeeai", "--config", str(config_file), "llm"]):
                with pytest.raises(SystemExit):
                    cli.main()

            # After CLI sets env var, config should be loadable
            assert os.environ.get("METABEEAI_CONFIG_FILE") == str(config_file)
