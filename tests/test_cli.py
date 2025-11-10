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
    
    def test_cli_has_review_command(self):
        """Test that 'review' subcommand exists."""
        with patch('sys.argv', ['metabee', 'review', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0
    
    def test_cli_has_prep_benchmark_command(self):
        """Test that 'prep-benchmark' subcommand exists."""
        with patch('sys.argv', ['metabee', 'prep-benchmark', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0
    
    def test_cli_has_benchmark_command(self):
        """Test that 'benchmark' subcommand exists."""
        with patch('sys.argv', ['metabee', 'benchmark', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0
    
    def test_cli_has_edge_cases_command(self):
        """Test that 'edge-cases' subcommand exists."""
        with patch('sys.argv', ['metabee', 'edge-cases', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0
    
    def test_cli_has_plot_metrics_command(self):
        """Test that 'plot-metrics' subcommand exists."""
        with patch('sys.argv', ['metabee', 'plot-metrics', '--help']):
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


class TestReviewCommand:
    """Test the 'review' subcommand."""
    
    @patch('metabeeai.cli.handle_review_command')
    def test_review_command_launches(self, mock_handler):
        """Test that 'review' command handler is called."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'review']):
            with pytest.raises(SystemExit):
                cli.main()
        
        # Check handler was called
        assert mock_handler.called
        args = mock_handler.call_args[0][0]
        # Review command has no arguments, just verify it was called
        assert args is not None


class TestPrepBenchmarkCommand:
    """Test the 'prep-benchmark' subcommand."""
    
    @patch('metabeeai.cli.handle_prep_benchmark_command')
    def test_prep_benchmark_defaults(self, mock_handler):
        """Test that 'prep-benchmark' command has correct default values."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'prep-benchmark']):
            with pytest.raises(SystemExit):
                cli.main()
        
        # Check handler was called
        assert mock_handler.called
        args = mock_handler.call_args[0][0]
        
        # Check defaults
        assert args.papers_dir is None
        assert args.questions_yml is None
        assert args.output is None
    
    @patch('metabeeai.cli.handle_prep_benchmark_command')
    def test_prep_benchmark_with_papers_dir(self, mock_handler):
        """Test 'prep-benchmark' command with --papers-dir argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'prep-benchmark', '--papers-dir', '/test/papers']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.papers_dir == '/test/papers'
    
    @patch('metabeeai.cli.handle_prep_benchmark_command')
    def test_prep_benchmark_with_questions_yml(self, mock_handler):
        """Test 'prep-benchmark' command with --questions-yml argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'prep-benchmark', '--questions-yml', '/test/questions.yml']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.questions_yml == '/test/questions.yml'
    
    @patch('metabeeai.cli.handle_prep_benchmark_command')
    def test_prep_benchmark_with_output(self, mock_handler):
        """Test 'prep-benchmark' command with --output argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'prep-benchmark', '--output', '/test/output.json']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.output == '/test/output.json'
    
    @patch('metabeeai.cli.handle_prep_benchmark_command')
    def test_prep_benchmark_with_all_args(self, mock_handler):
        """Test 'prep-benchmark' command with all arguments."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', [
            'metabee', 'prep-benchmark',
            '--papers-dir', '/test/papers',
            '--questions-yml', '/test/questions.yml',
            '--output', '/test/output.json'
        ]):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.papers_dir == '/test/papers'
        assert args.questions_yml == '/test/questions.yml'
        assert args.output == '/test/output.json'


class TestBenchmarkCommand:
    """Test the 'benchmark' subcommand."""
    
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_defaults(self, mock_handler):
        """Test that 'benchmark' command has correct default values."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'benchmark']):
            with pytest.raises(SystemExit):
                cli.main()
        
        # Check handler was called
        assert mock_handler.called
        args = mock_handler.call_args[0][0]
        
        # Check defaults
        assert args.question is None
        assert args.input is None
        assert args.limit is None
        assert args.batch_size == 25
        assert args.max_retries == 5
        assert args.model == "gpt-4o"
        assert args.max_context_length == 200000
        assert args.use_retrieval_only is False
        assert args.list_questions is False
    
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_with_question(self, mock_handler):
        """Test 'benchmark' command with --question argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'benchmark', '--question', 'test_question']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.question == 'test_question'
    
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_with_short_question_flag(self, mock_handler):
        """Test 'benchmark' command with -q short flag."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'benchmark', '-q', 'test_q']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.question == 'test_q'
    
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_with_input(self, mock_handler):
        """Test 'benchmark' command with --input argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'benchmark', '--input', '/test/input.json']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.input == '/test/input.json'
    
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_with_limit(self, mock_handler):
        """Test 'benchmark' command with --limit argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'benchmark', '--limit', '10']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.limit == 10
    
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_with_batch_size(self, mock_handler):
        """Test 'benchmark' command with --batch-size argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'benchmark', '--batch-size', '15']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.batch_size == 15
    
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_with_max_retries(self, mock_handler):
        """Test 'benchmark' command with --max-retries argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'benchmark', '--max-retries', '3']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.max_retries == 3
    
    @pytest.mark.parametrize("model", ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_with_model_choices(self, mock_handler, model):
        """Test 'benchmark' command with different --model choices."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'benchmark', '--model', model]):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.model == model
    
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_with_max_context_length(self, mock_handler):
        """Test 'benchmark' command with --max-context-length argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'benchmark', '--max-context-length', '100000']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.max_context_length == 100000
    
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_with_use_retrieval_only(self, mock_handler):
        """Test 'benchmark' command with --use-retrieval-only flag."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'benchmark', '--use-retrieval-only']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.use_retrieval_only is True
    
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_with_list_questions(self, mock_handler):
        """Test 'benchmark' command with --list-questions flag."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'benchmark', '--list-questions']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.list_questions is True
    
    @patch('metabeeai.cli.handle_benchmark_command')
    def test_benchmark_with_all_args(self, mock_handler):
        """Test 'benchmark' command with all arguments."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', [
            'metabee', 'benchmark',
            '--question', 'test_question',
            '--input', '/test/input.json',
            '--limit', '50',
            '--batch-size', '10',
            '--max-retries', '3',
            '--model', 'gpt-4o-mini',
            '--max-context-length', '150000',
            '--use-retrieval-only'
        ]):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.question == 'test_question'
        assert args.input == '/test/input.json'
        assert args.limit == 50
        assert args.batch_size == 10
        assert args.max_retries == 3
        assert args.model == 'gpt-4o-mini'
        assert args.max_context_length == 150000
        assert args.use_retrieval_only is True


class TestEdgeCasesCommand:
    """Test the 'edge-cases' subcommand."""
    
    @patch('metabeeai.cli.handle_edge_cases_command')
    def test_edge_cases_defaults(self, mock_handler):
        """Test that 'edge-cases' command has correct default values."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'edge-cases']):
            with pytest.raises(SystemExit):
                cli.main()
        
        # Check handler was called
        assert mock_handler.called
        args = mock_handler.call_args[0][0]
        
        # Check defaults
        assert args.num_cases == 20
        assert args.results_dir is None
        assert args.merged_data_dir is None
        assert args.output_dir is None
        assert args.openai_api_key is None
        assert args.model == "gpt-4o"
        assert args.generate_summaries_only is False
        assert args.contextual_only is False
        assert args.generate_contextual_summaries_only is False
    
    @patch('metabeeai.cli.handle_edge_cases_command')
    def test_edge_cases_with_num_cases(self, mock_handler):
        """Test 'edge-cases' command with --num-cases argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'edge-cases', '--num-cases', '10']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.num_cases == 10
    
    @patch('metabeeai.cli.handle_edge_cases_command')
    def test_edge_cases_with_results_dir(self, mock_handler):
        """Test 'edge-cases' command with --results-dir argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'edge-cases', '--results-dir', '/test/results']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.results_dir == '/test/results'
    
    @patch('metabeeai.cli.handle_edge_cases_command')
    def test_edge_cases_with_output_dir(self, mock_handler):
        """Test 'edge-cases' command with --output-dir argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'edge-cases', '--output-dir', '/test/output']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.output_dir == '/test/output'
    
    @patch('metabeeai.cli.handle_edge_cases_command')
    def test_edge_cases_with_model(self, mock_handler):
        """Test 'edge-cases' command with --model argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'edge-cases', '--model', 'gpt-4o-mini']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.model == 'gpt-4o-mini'
    
    @patch('metabeeai.cli.handle_edge_cases_command')
    def test_edge_cases_with_generate_summaries_only(self, mock_handler):
        """Test 'edge-cases' command with --generate-summaries-only flag."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'edge-cases', '--generate-summaries-only']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.generate_summaries_only is True
    
    @patch('metabeeai.cli.handle_edge_cases_command')
    def test_edge_cases_with_contextual_only(self, mock_handler):
        """Test 'edge-cases' command with --contextual-only flag."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'edge-cases', '--contextual-only']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.contextual_only is True
    
    @patch('metabeeai.cli.handle_edge_cases_command')
    def test_edge_cases_with_generate_contextual_summaries_only(self, mock_handler):
        """Test 'edge-cases' command with --generate-contextual-summaries-only flag."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'edge-cases', '--generate-contextual-summaries-only']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.generate_contextual_summaries_only is True
    
    @patch('metabeeai.cli.handle_edge_cases_command')
    def test_edge_cases_with_all_args(self, mock_handler):
        """Test 'edge-cases' command with all arguments."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', [
            'metabee', 'edge-cases',
            '--num-cases', '15',
            '--results-dir', '/test/results',
            '--merged-data-dir', '/test/merged',
            '--output-dir', '/test/output',
            '--openai-api-key', 'test-key',
            '--model', 'gpt-4-turbo',
            '--contextual-only'
        ]):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.num_cases == 15
        assert args.results_dir == '/test/results'
        assert args.merged_data_dir == '/test/merged'
        assert args.output_dir == '/test/output'
        assert args.openai_api_key == 'test-key'
        assert args.model == 'gpt-4-turbo'
        assert args.contextual_only is True


class TestPlotMetricsCommand:
    """Test the 'plot-metrics' subcommand."""
    
    @patch('metabeeai.cli.handle_plot_metrics_command')
    def test_plot_metrics_defaults(self, mock_handler):
        """Test that 'plot-metrics' command has correct default values."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'plot-metrics']):
            with pytest.raises(SystemExit):
                cli.main()
        
        # Check handler was called
        assert mock_handler.called
        args = mock_handler.call_args[0][0]
        
        # Check defaults
        assert args.results_dir is None
        assert args.output_dir is None
    
    @patch('metabeeai.cli.handle_plot_metrics_command')
    def test_plot_metrics_with_results_dir(self, mock_handler):
        """Test 'plot-metrics' command with --results-dir argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'plot-metrics', '--results-dir', '/test/results']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.results_dir == '/test/results'
    
    @patch('metabeeai.cli.handle_plot_metrics_command')
    def test_plot_metrics_with_output_dir(self, mock_handler):
        """Test 'plot-metrics' command with --output-dir argument."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', ['metabee', 'plot-metrics', '--output-dir', '/test/output']):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.output_dir == '/test/output'
    
    @patch('metabeeai.cli.handle_plot_metrics_command')
    def test_plot_metrics_with_all_args(self, mock_handler):
        """Test 'plot-metrics' command with all arguments."""
        mock_handler.side_effect = SystemExit(0)
        
        with patch('sys.argv', [
            'metabee', 'plot-metrics',
            '--results-dir', '/test/results',
            '--output-dir', '/test/output'
        ]):
            with pytest.raises(SystemExit):
                cli.main()
        
        args = mock_handler.call_args[0][0]
        assert args.results_dir == '/test/results'
        assert args.output_dir == '/test/output'


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
        assert 'review' in result.stdout
        assert 'prep-benchmark' in result.stdout
        assert 'benchmark' in result.stdout
        assert 'edge-cases' in result.stdout
        assert 'plot-metrics' in result.stdout
    
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
    
    def test_installed_cli_review_help(self):
        """Test that the installed CLI 'review' subcommand shows help."""
        import subprocess
        result = subprocess.run(['metabeeai', 'review', '--help'], capture_output=True, text=True)
        assert result.returncode == 0
        # Review command has no arguments, just verify it doesn't error
    
    def test_installed_cli_prep_benchmark_help(self):
        """Test that the installed CLI 'prep-benchmark' subcommand shows help."""
        import subprocess
        result = subprocess.run(['metabeeai', 'prep-benchmark', '--help'], capture_output=True, text=True)
        assert result.returncode == 0
        assert '--papers-dir' in result.stdout
        assert '--questions-yml' in result.stdout
        assert '--output' in result.stdout
    
    def test_installed_cli_benchmark_help(self):
        """Test that the installed CLI 'benchmark' subcommand shows help."""
        import subprocess
        result = subprocess.run(['metabeeai', 'benchmark', '--help'], capture_output=True, text=True)
        assert result.returncode == 0
        assert '--question' in result.stdout
        assert '--input' in result.stdout
        assert '--limit' in result.stdout
        assert '--batch-size' in result.stdout
        assert '--max-retries' in result.stdout
        assert '--model' in result.stdout
        assert '--max-context-length' in result.stdout
        assert '--use-retrieval-only' in result.stdout
        assert '--list-questions' in result.stdout
    
    def test_installed_cli_edge_cases_help(self):
        """Test that the installed CLI 'edge-cases' subcommand shows help."""
        import subprocess
        result = subprocess.run(['metabeeai', 'edge-cases', '--help'], capture_output=True, text=True)
        assert result.returncode == 0
        assert '--num-cases' in result.stdout
        assert '--results-dir' in result.stdout
        assert '--output-dir' in result.stdout
        assert '--model' in result.stdout
        assert '--generate-summaries-only' in result.stdout
        assert '--contextual-only' in result.stdout
    
    def test_installed_cli_plot_metrics_help(self):
        """Test that the installed CLI 'plot-metrics' subcommand shows help."""
        import subprocess
        result = subprocess.run(['metabeeai', 'plot-metrics', '--help'], capture_output=True, text=True)
        assert result.returncode == 0
        assert '--results-dir' in result.stdout
        assert '--output-dir' in result.stdout
    
    def test_installed_cli_requires_subcommand(self):
        """Test that the installed CLI requires a subcommand."""
        import subprocess
        result = subprocess.run(['metabeeai'], capture_output=True, text=True)
        assert result.returncode != 0
        assert 'required' in result.stderr.lower() or 'choose from' in result.stderr.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
