"""
Tests for metabeeai.process_pdfs submodule.

Tests config integration in batch_deduplicate, process_all, and va_process_papers.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import metabeeai.process_pdfs.batch_deduplicate as batch_deduplicate
import metabeeai.process_pdfs.process_all as process_all
import metabeeai.process_pdfs.va_process_papers as va_process_papers
from metabeeai import config


@pytest.fixture(autouse=True)
def clear_config_cache(monkeypatch):
    """Clear config cache and reset env vars before each test to ensure isolation."""
    config._config_cache.clear()
    # Clear any lingering config-related env vars from previous tests
    monkeypatch.delenv("METABEEAI_CONFIG_FILE", raising=False)
    monkeypatch.delenv("METABEEAI_PAPERS_DIR", raising=False)
    monkeypatch.delenv("LANDING_AI_API_KEY", raising=False)
    yield
    config._config_cache.clear()


class TestBatchDeduplicateConfig:
    """Test batch_deduplicate.py config integration."""

    def test_get_papers_dir_env_var(self, monkeypatch, tmp_path):
        """Test that get_papers_dir respects METABEEAI_PAPERS_DIR env var."""
        test_dir = tmp_path / "env_papers"
        test_dir.mkdir()

        monkeypatch.delenv("METABEEAI_CONFIG_FILE", raising=False)
        monkeypatch.setenv("METABEEAI_PAPERS_DIR", str(test_dir))

        result = batch_deduplicate.get_papers_dir()
        assert result == str(test_dir)

    def test_get_papers_dir_config_file(self, monkeypatch, tmp_path):
        """Test that get_papers_dir uses config file when no env var set."""
        config_dir = tmp_path / "config_papers"
        config_dir.mkdir()

        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(f"papers_dir: {config_dir}\n")

        monkeypatch.setenv("METABEEAI_CONFIG_FILE", str(config_file))
        # Don't set METABEEAI_PAPERS_DIR env var - let config file be used

        result = batch_deduplicate.get_papers_dir()
        assert result == str(config_dir)

    def test_get_papers_dir_config_overrides_env(self, monkeypatch, tmp_path):
        """Test that config file takes precedence over env var."""
        config_dir = tmp_path / "config_papers"
        config_dir.mkdir()
        env_dir = tmp_path / "env_papers"
        env_dir.mkdir()

        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(f"papers_dir: {config_dir}\n")

        monkeypatch.setenv("METABEEAI_CONFIG_FILE", str(config_file))
        monkeypatch.setenv("METABEEAI_PAPERS_DIR", str(env_dir))

        result = batch_deduplicate.get_papers_dir()
        # Config file should win over env var
        assert result == str(config_dir)

    def test_get_papers_dir_default(self, monkeypatch):
        """Test that get_papers_dir returns default when no config set."""
        monkeypatch.delenv("METABEEAI_CONFIG_FILE", raising=False)
        monkeypatch.delenv("METABEEAI_PAPERS_DIR", raising=False)

        result = batch_deduplicate.get_papers_dir()
        assert result == "data/papers"

    def test_find_paper_folders(self, tmp_path):
        """Test finding paper folders in base directory."""
        # Create test structure
        base_dir = tmp_path / "papers"
        base_dir.mkdir()

        (base_dir / "001").mkdir()
        (base_dir / "002").mkdir()
        (base_dir / "003").mkdir()
        (base_dir / "not_a_paper").mkdir()  # Should be ignored (not numeric)

        result = batch_deduplicate.find_paper_folders(base_dir)

        assert len(result) == 3
        folder_names = [f.name for f in result]
        assert "001" in folder_names
        assert "002" in folder_names
        assert "003" in folder_names
        assert "not_a_paper" not in folder_names

    def test_find_merged_json_files(self, tmp_path):
        """Test finding merged JSON files in paper folders."""
        # Create test structure matching implementation (pages/merged_v2.json)
        paper1 = tmp_path / "001"
        pages1 = paper1 / "pages"
        pages1.mkdir(parents=True)
        (pages1 / "merged_v2.json").write_text('{"data": {"chunks": []}}')

        paper2 = tmp_path / "002"
        pages2 = paper2 / "pages"
        pages2.mkdir(parents=True)
        (pages2 / "merged_v2.json").write_text('{"data": {"chunks": []}}')

        result = batch_deduplicate.find_merged_json_files([paper1, paper2])

        assert len(result) == 2
        assert all("json_path" in item for item in result)
        assert all("paper_id" in item for item in result)


class TestProcessAllConfig:
    """Test process_all.py config integration."""

    def test_get_papers_dir_env_var(self, monkeypatch, tmp_path):
        """Test that get_papers_dir respects METABEEAI_PAPERS_DIR env var."""
        test_dir = tmp_path / "env_papers"
        test_dir.mkdir()

        monkeypatch.delenv("METABEEAI_CONFIG_FILE", raising=False)
        monkeypatch.setenv("METABEEAI_PAPERS_DIR", str(test_dir))

        result = process_all.get_papers_dir()
        assert result == str(test_dir)

    def test_get_papers_dir_config_file(self, monkeypatch, tmp_path):
        """Test that get_papers_dir uses config file when no env var set."""
        config_dir = tmp_path / "config_papers"
        config_dir.mkdir()

        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(f"papers_dir: {config_dir}\n")

        monkeypatch.setenv("METABEEAI_CONFIG_FILE", str(config_file))
        # Don't set METABEEAI_PAPERS_DIR env var - let config file be used

        result = process_all.get_papers_dir()
        assert result == str(config_dir)

    def test_get_papers_dir_config_overrides_env(self, monkeypatch, tmp_path):
        """Test that config file takes precedence over env var."""
        config_dir = tmp_path / "config_papers"
        config_dir.mkdir()
        env_dir = tmp_path / "env_papers"
        env_dir.mkdir()

        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(f"papers_dir: {config_dir}\n")

        monkeypatch.setenv("METABEEAI_CONFIG_FILE", str(config_file))
        monkeypatch.setenv("METABEEAI_PAPERS_DIR", str(env_dir))

        result = process_all.get_papers_dir()
        # Config file should win over env var
        assert result == str(config_dir)

    def test_validate_environment_no_api_key(self, monkeypatch):
        """Test that validate_environment returns False when API key missing."""
        monkeypatch.delenv("METABEEAI_CONFIG_FILE", raising=False)
        monkeypatch.delenv("LANDING_AI_API_KEY", raising=False)

        assert process_all.validate_environment() is False

    def test_validate_environment_with_env_api_key(self, monkeypatch):
        """Test that validate_environment passes with env var API key."""
        monkeypatch.delenv("METABEEAI_CONFIG_FILE", raising=False)
        monkeypatch.setenv("LANDING_AI_API_KEY", "test-api-key-123")

        assert process_all.validate_environment() is True

    def test_validate_environment_with_config_file_api_key(self, monkeypatch, tmp_path):
        """Test that validate_environment passes with config file API key."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("landing_api_key: config-key-456\n")

        monkeypatch.setenv("METABEEAI_CONFIG_FILE", str(config_file))
        monkeypatch.delenv("LANDING_AI_API_KEY", raising=False)

        assert process_all.validate_environment() is True

    def test_get_all_paper_folders(self, tmp_path):
        """Test getting all paper folders."""
        papers_dir = tmp_path / "papers"
        papers_dir.mkdir()

        (papers_dir / "001").mkdir()
        (papers_dir / "002").mkdir()
        (papers_dir / "README.txt").write_text("readme")

        result = process_all.get_all_paper_folders(str(papers_dir))

        assert len(result) == 2
        folder_names = [Path(f).name for f in result]
        assert "001" in folder_names
        assert "002" in folder_names

    def test_validate_papers_directory_checks_pdfs(self, tmp_path):
        """Test that validate_papers_directory checks for PDF files."""
        papers_dir = tmp_path / "papers"
        papers_dir.mkdir()

        paper_folder = papers_dir / "001"
        paper_folder.mkdir()
        # No PDF files

        # Function prints error and returns False when missing PDFs
        assert process_all.validate_papers_directory(str(papers_dir), [paper_folder], merge_only=False) is False

    def test_validate_papers_directory_with_pdfs(self, tmp_path):
        """Test validate_papers_directory with PDF files."""
        papers_dir = tmp_path / "papers"
        papers_dir.mkdir()

        paper_folder = papers_dir / "001"
        paper_folder.mkdir()
        (paper_folder / "test.pdf").write_text("fake pdf")

        # Should not raise
        process_all.validate_papers_directory(str(papers_dir), [paper_folder], merge_only=False)


class TestVAProcessPapersConfig:
    """Test va_process_papers.py config integration."""

    @patch("metabeeai.process_pdfs.va_process_papers.requests.post")
    def test_process_papers_uses_env_api_key(self, mock_post, monkeypatch, tmp_path):
        """Test that process_papers uses LANDING_AI_API_KEY env var."""
        monkeypatch.delenv("METABEEAI_CONFIG_FILE", raising=False)
        monkeypatch.setenv("LANDING_AI_API_KEY", "env-api-key-123")

        mock_response = MagicMock()
        mock_response.text = "{}"
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Create test paper directory with pages and PDFs
        papers_dir = tmp_path / "papers"
        papers_dir.mkdir()
        paper_folder = papers_dir / "001"
        paper_folder.mkdir()
        pages_dir = paper_folder / "pages"
        pages_dir.mkdir()
        (pages_dir / "main_p01.pdf").write_text("fake pdf")

        va_process_papers.process_papers(papers_dir=str(papers_dir), start_folder="001")

        # Verify request was made with env API key
        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        assert "headers" in call_kwargs
        assert "Authorization" in call_kwargs["headers"]
        assert "env-api-key-123" in call_kwargs["headers"]["Authorization"]

    @patch("metabeeai.process_pdfs.va_process_papers.requests.post")
    def test_process_papers_uses_config_file_api_key(self, mock_post, monkeypatch, tmp_path):
        """Test that process_papers uses config file API key when no env var set."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("landing_api_key: config-api-key-456\n")

        monkeypatch.setenv("METABEEAI_CONFIG_FILE", str(config_file))
        # Don't set LANDING_AI_API_KEY env var - let config file be used

        mock_response = MagicMock()
        mock_response.text = "{}"
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Create test paper directory with pages and PDFs
        papers_dir = tmp_path / "papers"
        papers_dir.mkdir()
        paper_folder = papers_dir / "001"
        paper_folder.mkdir()
        pages_dir = paper_folder / "pages"
        pages_dir.mkdir()
        (pages_dir / "main_p01.pdf").write_text("fake pdf")

        va_process_papers.process_papers(papers_dir=str(papers_dir), start_folder="001")

        # Verify request was made with config file API key
        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        assert "headers" in call_kwargs
        assert "Authorization" in call_kwargs["headers"]
        assert "config-api-key-456" in call_kwargs["headers"]["Authorization"]

    @patch("metabeeai.process_pdfs.va_process_papers.requests.post")
    def test_process_papers_config_overrides_env(self, mock_post, monkeypatch, tmp_path):
        """Test that config file API key takes precedence over env var."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("landing_api_key: config-api-key-456\n")

        monkeypatch.setenv("METABEEAI_CONFIG_FILE", str(config_file))
        monkeypatch.setenv("LANDING_AI_API_KEY", "env-api-key-123")

        mock_response = MagicMock()
        mock_response.text = "{}"
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Create test paper directory with pages and PDFs
        papers_dir = tmp_path / "papers"
        papers_dir.mkdir()
        paper_folder = papers_dir / "001"
        paper_folder.mkdir()
        pages_dir = paper_folder / "pages"
        pages_dir.mkdir()
        (pages_dir / "main_p01.pdf").write_text("fake pdf")

        va_process_papers.process_papers(papers_dir=str(papers_dir), start_folder="001")

        # Verify request was made with config file API key (config wins over env)
        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        assert "headers" in call_kwargs
        assert "Authorization" in call_kwargs["headers"]
        assert "config-api-key-456" in call_kwargs["headers"]["Authorization"]


class TestProcessPDFsIntegration:
    """Integration tests for process_pdfs submodule."""

    def test_batch_deduplicate_workflow_with_env(self, monkeypatch, tmp_path):
        """Test batch deduplication workflow using env var config."""
        papers_dir = tmp_path / "papers"
        papers_dir.mkdir()

        monkeypatch.delenv("METABEEAI_CONFIG_FILE", raising=False)
        monkeypatch.setenv("METABEEAI_PAPERS_DIR", str(papers_dir))

        # Create test paper with merged file
        paper = papers_dir / "001"
        paper.mkdir()
        merged_file = paper / "001_merged.json"
        merged_file.write_text("""
        {
            "chunks": [
                {"text": "Test chunk 1"},
                {"text": "Test chunk 2"}
            ]
        }
        """)

        # Test that get_papers_dir returns configured directory
        result = batch_deduplicate.get_papers_dir()
        assert result == str(papers_dir)

    def test_process_all_with_config_file(self, monkeypatch, tmp_path):
        """Test process_all with config file."""
        papers_dir = tmp_path / "papers"
        papers_dir.mkdir()

        paper = papers_dir / "001"
        paper.mkdir()
        (paper / "test.pdf").write_text("fake pdf")

        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(f"papers_dir: {papers_dir}\nlanding_api_key: test-key-123\n")

        monkeypatch.setenv("METABEEAI_CONFIG_FILE", str(config_file))

        # Verify config functions work with real config hierarchy
        assert process_all.get_papers_dir() == str(papers_dir)
        assert process_all.validate_environment() is True
