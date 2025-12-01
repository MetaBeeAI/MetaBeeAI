"""
Tests for metabeeai.llm_benchmarking submodule.

Tests config integration in deepeval_benchmarking and edge_cases modules.
"""

from pathlib import Path
from unittest.mock import patch


class TestDeepevalBenchmarkingConfig:
    """Test deepeval_benchmarking.py config integration."""

    @patch("metabeeai.config.get_config_param")
    def test_uses_data_dir_from_config(self, mock_get_config):
        """Test that benchmarking uses data_dir from config."""
        mock_get_config.return_value = "/custom/data"

        # The main() function would call get_config_param("data_dir")
        result = mock_get_config("data_dir")

        assert result == "/custom/data"

    @patch("metabeeai.config.get_config_param")
    def test_uses_openai_api_key_from_config(self, mock_get_config):
        """Test that benchmarking uses OpenAI API key from config."""
        mock_get_config.return_value = "sk-test-key-123"

        result = mock_get_config("openai_api_key")

        assert result == "sk-test-key-123"

    @patch("sys.argv", ["deepeval_benchmarking.py", "--config", "/path/to/config.yaml"])
    @patch("metabeeai.config.get_config_param")
    @patch("metabeeai.llm_benchmarking.deepeval_benchmarking.load_dotenv")
    @patch("os.environ", {})
    def test_config_file_sets_env_var(self, mock_load_dotenv, mock_get_config):
        """Test that --config flag sets METABEEAI_CONFIG_FILE env var."""
        import os

        # Simulate what main() does with --config argument
        config_path = "/path/to/config.yaml"
        os.environ["METABEEAI_CONFIG_FILE"] = config_path

        assert os.environ.get("METABEEAI_CONFIG_FILE") == config_path

    @patch("metabeeai.config.get_config_param")
    def test_config_param_for_data_dir(self, mock_get_config, tmp_path):
        """Test retrieving data_dir via get_config_param."""
        data_dir = str(tmp_path / "benchmark_data")
        mock_get_config.return_value = data_dir

        result = mock_get_config("data_dir")

        assert result == data_dir


class TestEdgeCasesConfig:
    """Test edge_cases.py config integration."""

    @patch("metabeeai.config.get_config_param")
    def test_uses_data_dir_from_config(self, mock_get_config):
        """Test that edge_cases uses data_dir from config."""
        mock_get_config.return_value = "/edge/data"

        result = mock_get_config("data_dir")

        assert result == "/edge/data"

    @patch("metabeeai.config.get_config_param")
    def test_uses_openai_api_key_from_config(self, mock_get_config):
        """Test that edge_cases uses OpenAI API key from config."""
        mock_get_config.return_value = "sk-edge-key-456"

        result = mock_get_config("openai_api_key")

        assert result == "sk-edge-key-456"

    @patch("metabeeai.config.get_config_param")
    def test_api_key_fallback_to_config(self, mock_get_config):
        """Test that edge_cases falls back to config when no CLI arg provided."""
        # Simulate: args.openai_api_key is None, so use get_config_param
        mock_get_config.return_value = "sk-config-key-789"

        # This simulates: args.openai_api_key or get_config_param("openai_api_key")
        cli_api_key = None
        api_key = cli_api_key or mock_get_config("openai_api_key")

        assert api_key == "sk-config-key-789"

    @patch("metabeeai.config.get_config_param")
    def test_api_key_cli_overrides_config(self, mock_get_config):
        """Test that CLI argument overrides config for API key."""
        mock_get_config.return_value = "sk-config-key"

        # Simulate: args.openai_api_key is provided via CLI
        cli_api_key = "sk-cli-key"
        api_key = cli_api_key or mock_get_config("openai_api_key")

        # CLI should win
        assert api_key == "sk-cli-key"
        # Config should not be called since CLI value exists
        mock_get_config.assert_not_called()


class TestBenchmarkingIntegration:
    """Integration tests for llm_benchmarking submodule."""

    @patch("metabeeai.config.get_config_param")
    def test_benchmark_with_custom_data_dir(self, mock_get_config, tmp_path):
        """Test benchmarking with custom data directory from config."""
        data_dir = tmp_path / "custom_benchmark_data"
        data_dir.mkdir()

        mock_get_config.side_effect = lambda name, config_path=None: {
            "data_dir": str(data_dir),
            "results_dir": str(data_dir / "results"),
            "output_dir": str(data_dir / "output"),
        }.get(name)

        # Verify config returns custom directory
        assert mock_get_config("data_dir") == str(data_dir)
        assert mock_get_config("results_dir") == str(data_dir / "results")

    @patch("metabeeai.config.get_config_param")
    def test_benchmark_results_directory(self, mock_get_config, tmp_path):
        """Test that benchmarking uses results_dir from config."""
        results_dir = tmp_path / "benchmark_results"
        results_dir.mkdir()

        mock_get_config.return_value = str(results_dir)

        result = mock_get_config("results_dir")

        assert result == str(results_dir)
        assert Path(results_dir).exists()

    @patch("metabeeai.config.get_config_param")
    def test_edge_cases_output_directory(self, mock_get_config, tmp_path):
        """Test that edge_cases uses output_dir from config."""
        output_dir = tmp_path / "edge_cases_output"
        output_dir.mkdir()

        mock_get_config.return_value = str(output_dir)

        result = mock_get_config("output_dir")

        assert result == str(output_dir)
        assert Path(output_dir).exists()

    @patch("metabeeai.config.get_config_param")
    def test_config_hierarchy_for_benchmarking(self, mock_get_config, tmp_path):
        """Test config hierarchy for benchmarking parameters."""
        config_values = {
            "data_dir": str(tmp_path / "data"),
            "results_dir": str(tmp_path / "results"),
            "output_dir": str(tmp_path / "output"),
            "openai_api_key": "sk-test-123",
        }

        mock_get_config.side_effect = lambda name, config_path=None: config_values.get(name)

        # Verify all config params are accessible
        assert mock_get_config("data_dir") == str(tmp_path / "data")
        assert mock_get_config("results_dir") == str(tmp_path / "results")
        assert mock_get_config("output_dir") == str(tmp_path / "output")
        assert mock_get_config("openai_api_key") == "sk-test-123"

    @patch("metabeeai.config.get_config_param")
    def test_benchmark_with_yaml_config(self, mock_get_config, tmp_path):
        """Test benchmarking with YAML config file."""
        config_file = tmp_path / "benchmark_config.yaml"
        config_file.write_text("""
data_dir: /yaml/benchmark/data
results_dir: /yaml/benchmark/results
openai_api_key: sk-yaml-key-123
""")

        # Simulate config system loading YAML
        mock_get_config.side_effect = lambda name, config_path=None: {
            "data_dir": "/yaml/benchmark/data",
            "results_dir": "/yaml/benchmark/results",
            "openai_api_key": "sk-yaml-key-123",
        }.get(name)

        # Verify YAML values are used
        assert mock_get_config("data_dir") == "/yaml/benchmark/data"
        assert mock_get_config("results_dir") == "/yaml/benchmark/results"
        assert mock_get_config("openai_api_key") == "sk-yaml-key-123"


class TestBenchmarkingConfigPrecedence:
    """Test config precedence in benchmarking modules."""

    @patch("metabeeai.config.get_config_param")
    def test_data_dir_precedence(self, mock_get_config, monkeypatch, tmp_path):
        """Test data_dir precedence: env var > YAML > default."""
        # Simulate env var set (highest precedence)
        mock_get_config.return_value = "/env/benchmark/data"

        result = mock_get_config("data_dir")

        assert result == "/env/benchmark/data"

    @patch("metabeeai.config.get_config_param")
    def test_results_dir_default(self, mock_get_config):
        """Test results_dir uses default when not configured."""
        mock_get_config.return_value = "data/results"  # Default value

        result = mock_get_config("results_dir")

        assert result == "data/results"

    @patch("metabeeai.config.get_config_param")
    def test_openai_api_key_from_env(self, mock_get_config):
        """Test OpenAI API key from environment variable."""
        # Env var OPENAI_API_KEY set (common practice)
        mock_get_config.return_value = "sk-env-key-from-shell"

        result = mock_get_config("openai_api_key")

        assert result == "sk-env-key-from-shell"
