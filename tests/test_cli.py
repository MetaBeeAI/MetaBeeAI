"""
Tests for cli execution and argument parsing.
"""

import pytest
from unittest.mock import patch

from metabeeai import cli


class TestCLISubcommands:
    """Test that subcommands are registered correctly."""
    
    def test_cli_has_llm_command(self):
        """Test that 'llm' subcommand exists."""
        with patch('sys.argv', ['metabee', 'llm', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            # Help exits with 0
            assert exc_info.value.code == 0
    
    def test_cli_has_process_pdfs_command(self):
        """Test that 'process-pdfs' subcommand exists."""
        with patch('sys.argv', ['metabee', 'process-pdfs', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0
    
    def test_cli_requires_subcommand(self):
        """Test that CLI requires a subcommand."""
        with patch('sys.argv', ['metabee']):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            # Should exit with error code
            assert exc_info.value.code != 0


class TestLLMCommand:
    """Test the 'llm' subcommand arguments and defaults."""
    
    @patch('metabeeai.cli.handle_llm_command')
    def test_llm_defaults(self, mock_handler):
        """Test that 'llm' command has correct default values."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'llm']):
            with pytest.raises(SystemExit):
                cli.main()
        
        # Check handler was called
        assert mock_handler.called
        args = mock_handler.call_args[0][0]
        
        # Check defaults
        assert args.dir is None
        assert args.folders is None
        assert args.overwrite is False
        assert args.relevance_model is None
        assert args.answer_model is None
        assert args.config is None
    
    @patch('metabeeai.cli.handle_llm_command')
    def test_llm_with_dir(self, mock_handler):
        """Test 'llm' command with --dir argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'llm', '--dir', '/test/path']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.dir == '/test/path'
    
    @patch('metabeeai.cli.handle_llm_command')
    def test_llm_with_folders(self, mock_handler):
        """Test 'llm' command with --folders argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'llm', '--folders', '002', '003', '004']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.folders == ['002', '003', '004']
    
    @patch('metabeeai.cli.handle_llm_command')
    def test_llm_with_overwrite(self, mock_handler):
        """Test 'llm' command with --overwrite flag."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'llm', '--overwrite']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.overwrite is True
    
    @patch('metabeeai.cli.handle_llm_command')
    def test_llm_with_models(self, mock_handler):
        """Test 'llm' command with model arguments."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', [
            'metabee', 'llm',
            '--relevance-model', 'openai/gpt-4o-mini',
            '--answer-model', 'openai/gpt-4o'
        ]):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.relevance_model == 'openai/gpt-4o-mini'
        assert args.answer_model == 'openai/gpt-4o'
    
    @pytest.mark.parametrize("config_value", ['fast', 'balanced', 'quality'])
    @patch('metabeeai.cli.handle_llm_command')
    def test_llm_with_config(self, mock_handler, config_value):
        """Test 'llm' command with --config argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'llm', '--config', config_value]):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.config == config_value


class TestProcessPDFsCommand:
    """Test the 'process-pdfs' subcommand arguments and defaults."""
    
    @patch('metabeeai.cli.handle_process_pdfs_command')
    def test_process_pdfs_defaults(self, mock_handler):
        """Test that 'process-pdfs' command has correct default values."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'process-pdfs']):
            with pytest.raises(SystemExit):
                cli.main()
        
        # Check handler was called
        assert mock_handler.called
        args = mock_handler.call_args[0][0]
        
        # Check defaults - all skip flags should be False
        assert args.dir is None
        assert args.start is None
        assert args.end is None
        assert args.merge_only is False
        assert args.skip_split is False
        assert args.skip_api is False
        assert args.skip_merge is False
        assert args.skip_deduplicate is False
        assert args.filter_chunk_type == []
        assert args.pages == 1
    
    @patch('metabeeai.cli.handle_process_pdfs_command')
    def test_process_pdfs_with_dir(self, mock_handler):
        """Test 'process-pdfs' command with --dir argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'process-pdfs', '--dir', '/test/papers']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.dir == '/test/papers'
    
    @patch('metabeeai.cli.handle_process_pdfs_command')
    def test_process_pdfs_with_range(self, mock_handler):
        """Test 'process-pdfs' command with --start and --end arguments."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'process-pdfs', '--start', '002', '--end', '010']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.start == '002'
        assert args.end == '010'
    
    @pytest.mark.parametrize("flag,attr_name", [
        ('--skip-split', 'skip_split'),
        ('--skip-api', 'skip_api'),
        ('--skip-merge', 'skip_merge'),
        ('--skip-deduplicate', 'skip_deduplicate'),
    ])
    @patch('metabeeai.cli.handle_process_pdfs_command')
    def test_process_pdfs_skip_flags(self, mock_handler, flag, attr_name):
        """Test 'process-pdfs' command with individual skip flags."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'process-pdfs', flag]):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        # The specified flag should be True
        assert getattr(args, attr_name) is True
        
        # Other skip flags should be False
        all_skip_flags = ['skip_split', 'skip_api', 'skip_merge', 'skip_deduplicate']
        for other_flag in all_skip_flags:
            if other_flag != attr_name:
                assert getattr(args, other_flag) is False
    
    @patch('metabeeai.cli.handle_process_pdfs_command')
    def test_process_pdfs_merge_only(self, mock_handler):
        """Test 'process-pdfs' command with --merge-only flag."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'process-pdfs', '--merge-only']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.merge_only is True
    
    @patch('metabeeai.cli.handle_process_pdfs_command')
    def test_process_pdfs_multiple_skip_flags(self, mock_handler):
        """Test 'process-pdfs' command with multiple skip flags."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'process-pdfs', '--skip-split', '--skip-api', '--skip-merge']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.skip_split is True
        assert args.skip_api is True
        assert args.skip_merge is True
        assert args.skip_deduplicate is False  # This one wasn't set
    
    @patch('metabeeai.cli.handle_process_pdfs_command')
    def test_process_pdfs_with_filter_chunk_type(self, mock_handler):
        """Test 'process-pdfs' command with --filter-chunk-type argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'process-pdfs', '--filter-chunk-type', 'marginalia', 'figure']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.filter_chunk_type == ['marginalia', 'figure']
    
    @pytest.mark.parametrize("pages_value,expected", [
        (None, 1),  # Default (no --pages flag)
        ('1', 1),   # Explicit --pages 1
        ('2', 2),   # Explicit --pages 2
    ])
    @patch('metabeeai.cli.handle_process_pdfs_command')
    def test_process_pdfs_pages(self, mock_handler, pages_value, expected):
        """Test 'process-pdfs' command with different --pages values."""
        mock_handler.side_effect = SystemExit(0)
        
        if pages_value is None:
            argv = ['metabee', 'process-pdfs']
        else:
            argv = ['metabee', 'process-pdfs', '--pages', pages_value]
        
        with patch('sys.argv', argv):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.pages == expected


class TestDefaultBehavior:
    """Test that defaults result in running all steps (not skipping anything)."""
    
    @patch('metabeeai.cli.handle_process_pdfs_command')
    def test_all_steps_run_by_default(self, mock_handler):
        """Test that running 'process-pdfs' without flags means all steps will run."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'process-pdfs']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        
        # All skip flags must be False (meaning steps WILL run)
        assert args.skip_split is False, "Default should run split step"
        assert args.skip_api is False, "Default should run API step"
        assert args.skip_merge is False, "Default should run merge step"
        assert args.skip_deduplicate is False, "Default should run deduplicate step"
        assert args.merge_only is False, "Default should not be merge-only mode"


class TestInstalledCLI:
    """Test the installed 'metabeeai' command (integration tests)."""
    
    def test_installed_cli_exists(self):
        """Test that the metabeeai command is installed and accessible."""
        import subprocess
        result = subprocess.run(['which', 'metabeeai'], capture_output=True, text=True)
        assert result.returncode == 0, "metabeeai command not found in PATH"
        assert 'metabeeai' in result.stdout
    
    def test_installed_cli_help(self):
        """Test that the installed CLI shows help."""
        import subprocess
        result = subprocess.run(['metabeeai', '--help'], capture_output=True, text=True)
        assert result.returncode == 0
        assert 'llm' in result.stdout
        assert 'process-pdfs' in result.stdout
    
    def test_installed_cli_llm_help(self):
        """Test that the installed CLI 'llm' subcommand shows help."""
        import subprocess
        result = subprocess.run(['metabeeai', 'llm', '--help'], capture_output=True, text=True)
        assert result.returncode == 0
        assert '--dir' in result.stdout
        assert '--folders' in result.stdout
        assert '--overwrite' in result.stdout
        assert '--relevance-model' in result.stdout
        assert '--answer-model' in result.stdout
        assert '--config' in result.stdout
    
    def test_installed_cli_process_pdfs_help(self):
        """Test that the installed CLI 'process-pdfs' subcommand shows help."""
        import subprocess
        result = subprocess.run(['metabeeai', 'process-pdfs', '--help'], capture_output=True, text=True)
        assert result.returncode == 0
        assert '--dir' in result.stdout
        assert '--start' in result.stdout
        assert '--end' in result.stdout
        assert '--skip-split' in result.stdout
        assert '--skip-api' in result.stdout
        assert '--skip-merge' in result.stdout
        assert '--skip-deduplicate' in result.stdout
        assert '--merge-only' in result.stdout
        assert '--filter-chunk-type' in result.stdout
        assert '--pages' in result.stdout
    
    def test_installed_cli_requires_subcommand(self):
        """Test that the installed CLI requires a subcommand."""
        import subprocess
        result = subprocess.run(['metabeeai'], capture_output=True, text=True)
        assert result.returncode != 0
        assert 'required' in result.stderr.lower() or 'choose from' in result.stderr.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
