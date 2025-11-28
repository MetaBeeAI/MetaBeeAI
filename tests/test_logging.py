"""
Tests for metabeeai.logging module.

Tests setup_logger() functionality, config integration, log file creation,
and rotating file handlers.
"""

import logging
from pathlib import Path

from metabeeai import logging as metabeeai_logging


class TestSetupLogger:
    """Test setup_logger() function."""

    def test_setup_logger_creates_logger(self):
        """Test that setup_logger creates a logger instance."""
        logger = metabeeai_logging.setup_logger("test_logger")

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_setup_logger_without_name(self):
        """Test setup_logger with no name argument."""
        logger = metabeeai_logging.setup_logger()

        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_uses_env_log_level(self, monkeypatch):
        """Test that logger uses log level from environment variable."""
        monkeypatch.setenv("METABEEAI_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("METABEEAI_DATA_DIR", "/tmp/test_data")

        logger = metabeeai_logging.setup_logger("test_debug_logger")

        assert logger.level == logging.DEBUG

    def test_setup_logger_uses_env_logs_dir(self, monkeypatch, tmp_path):
        """Test that logger uses logs_dir from environment variable."""
        logs_dir = str(tmp_path / "custom_logs")
        monkeypatch.setenv("METABEEAI_LOGS_DIR", logs_dir)
        monkeypatch.setenv("METABEEAI_LOG_LEVEL", "INFO")

        logger = metabeeai_logging.setup_logger("test_dir_logger")  # NOQA F841

        # Check that logs directory was created
        assert Path(logs_dir).exists()
        assert Path(logs_dir).is_dir()

    def test_setup_logger_defaults_to_data_dir_logs(self, monkeypatch, tmp_path):
        """Test that logger defaults to data_dir/logs when logs_dir is None."""
        data_dir = str(tmp_path / "test_data")
        monkeypatch.delenv("METABEEAI_LOGS_DIR", raising=False)
        monkeypatch.setenv("METABEEAI_DATA_DIR", data_dir)
        monkeypatch.setenv("METABEEAI_LOG_LEVEL", "INFO")

        logger = metabeeai_logging.setup_logger("test_default_logger")  # NOQA F841

        # Check that data_dir/logs was created
        expected_logs_dir = Path(data_dir) / "logs"
        assert expected_logs_dir.exists()
        assert expected_logs_dir.is_dir()

    def test_setup_logger_has_two_handlers(self, monkeypatch, tmp_path):
        """Test that logger has console and file handlers."""
        logs_dir = str(tmp_path / "logs")
        monkeypatch.setenv("METABEEAI_LOGS_DIR", logs_dir)
        monkeypatch.setenv("METABEEAI_LOG_LEVEL", "INFO")

        logger = metabeeai_logging.setup_logger("test_handlers_logger")

        assert len(logger.handlers) == 2

        # Check handler types
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert "StreamHandler" in handler_types
        assert "TimedRotatingFileHandler" in handler_types

    def test_setup_logger_creates_log_file(self, monkeypatch, tmp_path):
        """Test that logger creates metabeeai.log file."""
        logs_dir = str(tmp_path / "logs")
        monkeypatch.setenv("METABEEAI_LOGS_DIR", logs_dir)
        monkeypatch.setenv("METABEEAI_LOG_LEVEL", "INFO")

        logger = metabeeai_logging.setup_logger("test_file_logger")

        # Write a log message to ensure file is created
        logger.info("Test message")

        log_file = Path(logs_dir) / "metabeeai.log"
        assert log_file.exists()
        assert log_file.is_file()

    def test_setup_logger_prevents_duplicate_handlers(self, monkeypatch, tmp_path):
        """Test that calling setup_logger twice doesn't add duplicate handlers."""
        logs_dir = str(tmp_path / "logs")
        monkeypatch.setenv("METABEEAI_LOGS_DIR", logs_dir)
        monkeypatch.setenv("METABEEAI_LOG_LEVEL", "INFO")

        logger_name = "test_duplicate_logger"

        # Call setup_logger twice with same name
        logger1 = metabeeai_logging.setup_logger(logger_name)
        logger2 = metabeeai_logging.setup_logger(logger_name)

        # Should be same logger instance
        assert logger1 is logger2

        # Should still have only 2 handlers
        assert len(logger1.handlers) == 2

    def test_setup_logger_with_different_log_levels(self, monkeypatch, tmp_path):
        """Test logger with different log levels."""
        logs_dir = str(tmp_path / "logs")

        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in log_levels:
            monkeypatch.setenv("METABEEAI_LOGS_DIR", logs_dir)
            monkeypatch.setenv("METABEEAI_LOG_LEVEL", level)

            logger = metabeeai_logging.setup_logger(f"test_{level.lower()}_logger")

            expected_level = getattr(logging, level)
            assert logger.level == expected_level

    def test_setup_logger_formatter(self, monkeypatch, tmp_path):
        """Test that logger handlers have correct formatter."""
        logs_dir = str(tmp_path / "logs")
        monkeypatch.setenv("METABEEAI_LOGS_DIR", logs_dir)
        monkeypatch.setenv("METABEEAI_LOG_LEVEL", "INFO")

        logger = metabeeai_logging.setup_logger("test_formatter_logger")

        for handler in logger.handlers:
            formatter = handler.formatter
            assert formatter is not None
            # Check format string includes expected components
            assert "%(asctime)s" in formatter._fmt
            assert "%(levelname)s" in formatter._fmt
            assert "%(name)s" in formatter._fmt
            assert "%(message)s" in formatter._fmt

    def test_setup_logger_rotating_file_handler_config(self, monkeypatch, tmp_path):
        """Test that TimedRotatingFileHandler has correct configuration."""
        logs_dir = str(tmp_path / "logs")
        monkeypatch.setenv("METABEEAI_LOGS_DIR", logs_dir)
        monkeypatch.setenv("METABEEAI_LOG_LEVEL", "INFO")

        logger = metabeeai_logging.setup_logger("test_rotating_logger")

        # Find the TimedRotatingFileHandler
        file_handler = None
        for handler in logger.handlers:
            if type(handler).__name__ == "TimedRotatingFileHandler":
                file_handler = handler
                break

        assert file_handler is not None
        # Check rotation settings (daily rotation, keep 7 days)
        assert file_handler.when == "D"  # Daily
        # TimedRotatingFileHandler interval is in seconds (1 day = 86400)
        assert file_handler.interval == 86400
        assert file_handler.backupCount == 7


class TestLoggingIntegration:
    """Integration tests for logging with config system."""

    def test_logging_with_env_config(self, monkeypatch, tmp_path):
        """Test logging setup with custom configuration."""
        custom_logs_dir = str(tmp_path / "custom_project_logs")
        monkeypatch.setenv("METABEEAI_LOGS_DIR", custom_logs_dir)
        monkeypatch.setenv("METABEEAI_LOG_LEVEL", "WARNING")

        logger = metabeeai_logging.setup_logger("integration_test_logger")

        # Verify directory created
        assert Path(custom_logs_dir).exists()

        # Verify log level
        assert logger.level == logging.WARNING

        # Test that WARNING level messages are logged but INFO are not
        logger.info("This should not appear")
        logger.warning("This should appear")

        log_file = Path(custom_logs_dir) / "metabeeai.log"
        assert log_file.exists()

        log_content = log_file.read_text()
        assert "This should appear" in log_content
        assert "This should not appear" not in log_content
