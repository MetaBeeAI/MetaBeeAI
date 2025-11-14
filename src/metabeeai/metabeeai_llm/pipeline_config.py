#!/usr/bin/env python3
"""
Configuration file for the MetaBeeAI LLM pipeline.
Users can modify these settings to customize the pipeline behavior.
"""

# Model Configuration
# Choose between different model combinations for optimal performance vs. cost

# Option 1: Fast and Cost-Effective (Recommended for high-volume processing)
FAST_CONFIG = {
    "relevance_model": "openai/gpt-4o-mini",  # Fast relevance scoring
    "answer_model": "openai/gpt-4o-mini",  # Fast answer generation
    "description": "Fast and cost-effective processing",
}

# Option 2: Balanced Performance (Recommended for most use cases)
BALANCED_CONFIG = {
    "relevance_model": "openai/gpt-4o-mini",  # Fast relevance scoring
    "answer_model": "openai/gpt-4o",  # High-quality answer generation
    "description": "Balanced speed and quality",
}

# Option 3: High Quality (Recommended for critical analysis)
QUALITY_CONFIG = {
    "relevance_model": "openai/gpt-4o",  # High-quality relevance scoring
    "answer_model": "openai/gpt-4o",  # High-quality answer generation
    "description": "Maximum quality, slower processing",
}

# Current Configuration (change this to switch between options)
# Temporarily using QUALITY_CONFIG to bypass gpt-4o-mini rate limit
CURRENT_CONFIG = QUALITY_CONFIG

# Parallel Processing Configuration
PARALLEL_CONFIG = {
    "relevance_batch_size": 3,  # Further reduced to avoid rate limiting
    "answer_batch_size": 2,  # Further reduced to avoid rate limiting
    "max_concurrent_requests": 5,  # Further reduced to avoid rate limiting
    "batch_delay": 0.5,  # Increased delay between batches
}

# Performance Tuning
PERFORMANCE_CONFIG = {
    "enable_parallel_processing": True,  # Enable/disable parallel processing
    "enable_batch_processing": True,  # Enable/disable batch processing
    "enable_progress_bars": True,  # Enable/disable progress bars
    "enable_detailed_logging": False,  # Enable/disable detailed logging
}

# Rate Limiting and Retry Configuration
RETRY_CONFIG = {
    "max_retries": 100,  # Maximum number of retries for failed API calls
    "retry_delay": 1,  # Delay between retries in seconds
    "exponential_backoff": True,  # Use exponential backoff for retries
}


def get_current_config():
    """Get the current configuration dictionary."""
    return {"models": CURRENT_CONFIG, "parallel": PARALLEL_CONFIG, "performance": PERFORMANCE_CONFIG, "retry": RETRY_CONFIG}


def print_config():
    """Print the current configuration."""
    config = get_current_config()
    print("🔧 MetaBeeAI Pipeline Configuration")
    print("=" * 50)

    print("📊 Model Configuration:")
    print(f"  • Relevance Model: {config['models']['relevance_model']}")
    print(f"  • Answer Model: {config['models']['answer_model']}")
    print(f"  • Description: {config['models']['description']}")

    print("\n⚡ Parallel Processing:")
    print(f"  • Relevance Batch Size: {config['parallel']['relevance_batch_size']}")
    print(f"  • Answer Batch Size: {config['parallel']['answer_batch_size']}")
    print(f"  • Max Concurrent Requests: {config['parallel']['max_concurrent_requests']}")

    print("\n🎯 Performance Settings:")
    print(f"  • Parallel Processing: {'✅ Enabled' if config['performance']['enable_parallel_processing'] else '❌ Disabled'}")
    print(f"  • Batch Processing: {'✅ Enabled' if config['performance']['enable_batch_processing'] else '❌ Disabled'}")
    print(f"  • Progress Bars: {'✅ Enabled' if config['performance']['enable_progress_bars'] else '❌ Disabled'}")

    print("\n🔄 Retry Configuration:")
    print(f"  • Max Retries: {config['retry']['max_retries']}")
    print(f"  • Retry Delay: {config['retry']['retry_delay']}s")
    print(f"  • Exponential Backoff: {'✅ Enabled' if config['retry']['exponential_backoff'] else '❌ Disabled'}")


if __name__ == "__main__":
    print_config()
