import json
import asyncio
import logging
import time
from pprint import pprint
from typing import List, Dict, Any, Callable
from tqdm import tqdm  # progress bar for loops
import litellm
from litellm import acompletion
from pydantic import BaseModel

# Configure logging for debugging and error tracking.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RETRY = 100

# Model configuration for hybrid approach
try:
    # Try relative import first (when used as module)
    from .pipeline_config import get_current_config
    config = get_current_config()
    RELEVANCE_MODEL = config['models']['relevance_model']
    ANSWER_MODEL = config['models']['answer_model']
    DEFAULT_RELEVANCE_BATCH_SIZE = config['parallel']['relevance_batch_size']
    DEFAULT_ANSWER_BATCH_SIZE = config['parallel']['answer_batch_size']
    MAX_CONCURRENT_REQUESTS = config['parallel']['max_concurrent_requests']
    BATCH_DELAY = config['parallel']['batch_delay']
except ImportError:
    try:
        # Try direct import (when running script directly)
        from pipeline_config import get_current_config
        config = get_current_config()
        RELEVANCE_MODEL = config['models']['relevance_model']
        ANSWER_MODEL = config['models']['answer_model']
        DEFAULT_RELEVANCE_BATCH_SIZE = config['parallel']['relevance_batch_size']
        DEFAULT_ANSWER_BATCH_SIZE = config['parallel']['answer_batch_size']
        MAX_CONCURRENT_REQUESTS = config['parallel']['max_concurrent_requests']
        BATCH_DELAY = config['parallel']['batch_delay']
    except ImportError:
        # Fallback configuration if pipeline_config.py is not available
        RELEVANCE_MODEL = 'openai/gpt-4o-mini'  # Fast model for relevance scoring
        ANSWER_MODEL = 'openai/gpt-4o'          # High-quality model for answer generation
        DEFAULT_RELEVANCE_BATCH_SIZE = 20       # Default batch size for relevance scoring
        DEFAULT_ANSWER_BATCH_SIZE = 5           # Default batch size for answer generation
        MAX_CONCURRENT_REQUESTS = 25            # Maximum concurrent API requests to avoid rate limiting
        BATCH_DELAY = 0.1                       # Default delay between batches

# Load questions configuration from YAML file
import yaml
import os

def load_questions_config():
    """Load questions configuration from the YAML file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    questions_path = os.path.join(script_dir, 'questions.yml')
    
    try:
        with open(questions_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Extract both QUESTIONS and GLOBAL_CONFIG
        questions = config.get('QUESTIONS', {})
        global_config = config.get('GLOBAL_CONFIG', {})
        
        # Merge global config into questions for easy access
        if global_config:
            questions['GLOBAL_CONFIG'] = global_config
        
        logger.info(f"Loaded {len(questions)} question configurations and global config")
        return questions
    except Exception as e:
        logger.error(f"Error loading questions config: {e}")
        # Return default configuration if YAML loading fails
        return {}

# Load the configuration
QUESTIONS_CONFIG = load_questions_config()

# --------------------------------------------------------------------------
# Data Models using Pydantic for response validation
# --------------------------------------------------------------------------

# Relevance model removed - no longer needed with simplified approach


class Answer(BaseModel):
    """
    Model for representing the answer response.

    Attributes:
        reason (str): Explanation or reasoning behind the answer.
        answer (str): The answer to the provided question.
    """
    reason: str
    answer: str


class AnswerWithChunkId(BaseModel):
    """
    Model for representing the answer response with chunk ID.

    Attributes:
        reason (str): Explanation or reasoning behind the answer.
        answer (str): The answer to the provided question.
        chunk_ids (List[str]): List of chunk IDs used to generate the answer.
    """
    reason: str
    answer: str
    chunk_ids: List[str]


class AnswerList(BaseModel):
    """
    Model for representing a list of answers.

    Attributes:
        answer: List of strings.
    """
    answer: List[str]


# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

def load_json_file(path: str) -> Dict[str, Any]:
    """
    Load a JSON file from the given file path.

    Args:
        path (str): The file path to the JSON file.

    Returns:
        Dict[str, Any]: Parsed JSON object.
    """
    with open(path, 'r') as f:
        return json.load(f)


def get_question_config(question_text: str) -> dict:
    """
    Get configuration for a specific question type based on the question text.
    
    Args:
        question_text (str): The question text to analyze.
        
    Returns:
        dict: Configuration with max_chunks, description, and no_info_response.
    """
    question_lower = question_text.lower()
    
    # Try to find a matching question in the YAML configuration
    for question_key, question_config in QUESTIONS_CONFIG.items():
        config_question = question_config.get('question', '').lower()
        # Check if questions match (either contains the other)
        if (question_lower in config_question or config_question in question_lower or 
            question_key.lower() in question_lower):
            # Extract configuration from YAML
            config = {
                'max_chunks': question_config.get('max_chunks', 5),
                'description': question_config.get('description', 'Default configuration'),
                'no_info_response': question_config.get('no_info_response', 'Information not found in the provided text.')
            }
            logger.info(f"Found question config for '{question_key}': {config}")
            return config
    
    # No match found, use default configuration
    logger.info("No question type match found, using default configuration")
    return {
        'max_chunks': 5,
        'description': 'Default configuration for general questions',
        'no_info_response': 'Information not found in the provided text.'
    }


def get_default_config(question_type: str) -> dict:
    """
    Get default configuration for a question type if YAML loading fails.
    
    Args:
        question_type (str): The type of question.
        
    Returns:
        dict: Default configuration.
    """
    # Return generic defaults
    return {
        'max_chunks': 5,
        'description': 'Default configuration for general questions',
        'no_info_response': 'Information not found in the provided text.'
    }


def get_question_metadata(question_text: str) -> dict:
    """
    Get metadata for a specific question from the YAML configuration.
    Uses both exact matching and keyword-based matching for better question identification.
    
    Args:
        question_text (str): The question text to look up.
        
    Returns:
        dict: Question metadata including instructions, output_format, examples, etc.
    """
    question_lower = question_text.lower()
    
    # First, try exact question matching
    for question_key, question_config in QUESTIONS_CONFIG.items():
        if question_key == 'GLOBAL_CONFIG':
            continue  # Skip global config
            
        if question_config.get('question', '').lower() in question_lower or question_key.lower() in question_lower:
            return {
                'question_key': question_key,
                'question': question_config.get('question', ''),
                'instructions': question_config.get('instructions', []),
                'output_format': question_config.get('output_format', ''),
                'example_output': question_config.get('example_output', []),
                'bad_example_output': question_config.get('bad_example_output', []),
                'max_chunks': question_config.get('max_chunks', 5),
                'no_info_response': question_config.get('no_info_response', 'Information not found in the provided text.'),
                'description': question_config.get('description', 'Default configuration')
            }
    
    # If no exact match, return empty metadata
    return {}
    
    return {}





def should_use_no_info_response(question: str, chunks: List[Dict[str, Any]], final_answer: str) -> bool:
    """
    Determine if the no_info_response should be used instead of the current answer.
    
    Args:
        question (str): The question being answered.
        chunks (List[Dict[str, Any]]): List of relevant chunks used.
        final_answer (str): The final synthesized answer.
        
    Returns:
        bool: True if no_info_response should be used, False otherwise.
    """
    # Check for explicit insufficient info response
    if final_answer == 'INSUFFICIENT_INFO':
        return True
    
    # Check for insufficient information indicators in the answer
    insufficient_indicators = [
        'not specified', 'not mentioned', 'not described', 'not reported',
        'unclear', 'ambiguous', 'contradictory', 'incomplete', 'no information',
        'cannot determine', 'insufficient data', 'limited information'
    ]
    
    answer_lower = final_answer.lower()
    if any(indicator in answer_lower for indicator in insufficient_indicators):
        return True
    
    # Check if chunks were found
    if not chunks:
        return True
    
    # Check if answer is too generic or vague
    generic_indicators = [
        'the study', 'the research', 'the paper', 'the authors',
        'more research needed', 'further study required', 'additional investigation'
    ]
    
    if any(indicator in answer_lower for indicator in generic_indicators):
        # Only use no_info_response if the answer is very generic
        if len(final_answer.split()) < 20:  # Very short, generic answer
            return True
    
    return False


def assess_answer_quality(question: str, chunks: List[Dict[str, Any]], final_answer: str) -> dict:
    """
    Assess the quality of the final answer based on available chunks and question requirements.
    
    Args:
        question (str): The question being answered.
        chunks (List[Dict[str, Any]]): List of relevant chunks used.
        final_answer (str): The final synthesized answer.
        
    Returns:
        dict: Quality assessment including confidence and recommendations.
    """
    question_metadata = get_question_metadata(question)
    
    # Check if answer contains the expected format/patterns
    output_format = question_metadata.get('output_format', '')
    example_outputs = question_metadata.get('example_output', [])
    
    quality_metrics = {
        'confidence': 'medium',
        'issues': [],
        'recommendations': []
    }
    
    # Check for insufficient information indicators
    insufficient_indicators = [
        'not specified', 'not mentioned', 'not described', 'not reported',
        'unclear', 'unclear', 'ambiguous', 'contradictory', 'incomplete'
    ]
    
    answer_lower = final_answer.lower()
    if any(indicator in answer_lower for indicator in insufficient_indicators):
        quality_metrics['confidence'] = 'low'
        quality_metrics['issues'].append('Answer contains insufficient information indicators')
        quality_metrics['recommendations'].append('Consider using no_info_response')
    
    # Check if chunks were found
    if not chunks:
        quality_metrics['confidence'] = 'low'
        quality_metrics['issues'].append('No relevant chunks found')
        quality_metrics['recommendations'].append('Review question formulation or chunk selection criteria')
    
    # Check if answer matches expected format
    if output_format and not any(keyword in answer_lower for keyword in output_format.lower().split()):
        quality_metrics['confidence'] = 'medium'
        quality_metrics['issues'].append('Answer may not match expected output format')
    
    return quality_metrics


# --------------------------------------------------------------------------
# Asynchronous Processing Functions
# --------------------------------------------------------------------------

async def format_to_list(question,text, model: str = 'openai/gpt-4o-mini') -> Dict[str, Any]:
    """
    Retrieve an answer for the given question using the provided text chunk.

    This function constructs a prompt by embedding the question and text chunk,
    calls the asynchronous API to obtain an answer, and adds the parsed answer
    to the chunk dictionary.

    Args:
        question (str): The question for which the answer is sought.
        chunk (Dict[str, Any]): Dictionary containing the text and related data.
        model (str, optional): Model identifier for the API call. Defaults to 'openai/gpt-4o'.

    Returns:
        Dict[str, Any]: Updated chunk with an added 'answer' field containing the response.
    """
    prompt: str = f"""
Please evaluate the following question and the answer text to the question. The answer should contain one or more entities.
Return the entities in a list format.

<Question>
{question}
</Question>

<Text>
{text}
</Text>
    """.strip()

    messages = [{"content": prompt, "role": "user"}]

    result = None
    for i in range(RETRY):
        try:
            # Call the API asynchronously expecting a response conforming to the Answer model.
            response = await acompletion(model=model, messages=messages, response_format=AnswerList,temperature=0)
            # Parse the JSON string from the API response.
            result = json.loads(response.choices[0].message.content)
            logger.info("Answer restructured", result)
            break
        except Exception as e:
            logger.error("Error obtaining answer restructuring",  e)
            time.sleep(1)
            continue
    return result


async def get_answer(question: str, chunk: Dict[str, Any], model: str = ANSWER_MODEL) -> Dict[str, Any]:
    """
    Retrieve an answer for the given question using the provided text chunk.

    This function constructs a prompt by embedding the question with text chunk,
    instructions, examples, and bad examples to guide the LLM response quality.

    Args:
        question (str): The question to test relevance against.
        chunk (Dict[str, Any]): Dictionary containing the text to be evaluated.
        model (str, optional): Model identifier for the API call. Defaults to ANSWER_MODEL.

    Returns:
        Dict[str, Any]: Updated chunk with an added 'answer' field containing the response.
    """
    text: str = chunk.get('text', '')
    
    # Get question metadata to access instructions, examples, and bad examples
    question_metadata = get_question_metadata(question)
    
    # Build enhanced prompt with examples
    prompt_parts = [f"<Question>\n{question}\n</Question>"]
    
    # Add instructions if available
    if question_metadata.get('instructions'):
        instructions_text = "\n".join([f"- {instruction}" for instruction in question_metadata['instructions']])
        prompt_parts.append(f"<Instructions>\n{instructions_text}\n</Instructions>")
    
    # Add output format if available
    if question_metadata.get('output_format'):
        prompt_parts.append(f"<Output Format>\n{question_metadata['output_format']}\n</Output Format>")
    
    # Add good examples if available
    if question_metadata.get('example_output'):
        examples_text = "\n".join([f"✅ Good: {example}" for example in question_metadata['example_output']])
        prompt_parts.append(f"<Good Examples>\n{examples_text}\n</Good Examples>")
    
    # Add bad examples if available
    if question_metadata.get('bad_example_output'):
        bad_examples_text = "\n".join([f"❌ Avoid: {example}" for example in question_metadata['bad_example_output']])
        prompt_parts.append(f"<Bad Examples - AVOID THESE>\n{bad_examples_text}\n</Bad Examples>")
    
    # Add the text chunk
    prompt_parts.append(f"<Text>\n{text}\n</Text>")
    
    # Add final guidance
    prompt_parts.append("""
<Important Guidelines>
- Provide ONLY the specific information requested
- Use the exact format specified in Output Format
- Follow the Good Examples pattern
- AVOID the Bad Examples patterns (no explanations, no context, no repetition)
- Be concise and direct
- If the text doesn't contain the requested information, return an empty answer
</Important Guidelines>
""")
    
    prompt = "\n".join(prompt_parts).strip()

    messages = [{"content": prompt, "role": "user"}]

    for i in range(RETRY):
        try:
            # Call the API asynchronously expecting a response conforming to the Answer model.
            response = await acompletion(model=model, messages=messages, response_format=Answer,temperature=0)
            # Parse the JSON string from the API response.
            chunk['answer'] = json.loads(response.choices[0].message.content)
            logger.info("Answer obtained for chunk %s: %s", chunk.get('chunk_id'), chunk['answer'])
            break
        except Exception as e:
            logger.error("Error obtaining answer for chunk %s: %s", chunk.get('chunk_id'), e)
            chunk['answer'] = None  # In case of error, mark answer as None.
            time.sleep(1)
            continue
    return chunk


async def get_top_relevant_chunks(
    chunks: List[Dict[str, Any]], 
    question: str, 
    question_metadata: Dict[str, Any],
    max_chunks: int = 5,
    model: str = RELEVANCE_MODEL
) -> List[Dict[str, Any]]:
    """
    Get the top most relevant chunks for a question using a single LLM call.
    
    Args:
        chunks: List of text chunks to evaluate
        question: The question being asked
        question_metadata: Metadata about the question from YAML config
        max_chunks: Maximum number of chunks to return
        model: The LLM model to use for chunk selection
    
    Returns:
        List of the most relevant chunks
    """
    try:
        # Filter out obviously irrelevant chunks first
        filtered_chunks = []
        for chunk in chunks:
            text = chunk.get('text', '').lower()
            # Skip chunks that are clearly not relevant (headers, metadata, etc.)
            if any(skip_term in text for skip_term in ['crossmark', 'logo', 'journal:', 'year:', 'doi:', 'authors:', 'accepted:', 'published online:', '© the author']):
                continue
            filtered_chunks.append(chunk)
        
        if not filtered_chunks:
            return []
        
        # Build the prompt for chunk selection
        prompt_parts = [
            f"Question: {question}",
            "",
            f"Instructions: {question_metadata.get('instructions', [])}",
            "",
            f"Output Format: {question_metadata.get('output_format', '')}",
            "",
            "Good Examples:",
            *[f"- {example}" for example in question_metadata.get('example_output', [])],
            "",
            "Bad Examples:",
            *[f"- {example}" for example in question_metadata.get('bad_example_output', [])],
            "",
            f"Task: From the following {len(filtered_chunks)} text chunks, select the top {max_chunks} most relevant chunks that will best answer the question.",
            "",
            "Text Chunks:",
        ]
        
        # Add chunks with IDs for reference
        for i, chunk in enumerate(filtered_chunks):
            chunk_text = chunk.get('text', '')[:500]  # Limit text length
            chunk_id = chunk.get('chunk_id', f'chunk_{i}')
            prompt_parts.append(f"Chunk {i+1} (ID: {chunk_id}): {chunk_text}...")
            # Debug: Log chunk content to see what we're actually working with
            logger.info(f"DEBUG: Chunk {i+1} content preview: {chunk_text[:100]}...")
        
        # Build dynamic instructions based on question metadata
        instructions_list = [
            f"1. Analyze all chunks and select the top {max_chunks} most relevant ones",
            "2. Skip chunks that are just headers, metadata, or don't contain relevant information",
            "3. Return ONLY the chunk numbers (1, 2, 3, etc.) in order of relevance",
            f"4. If fewer than {max_chunks} chunks contain relevant information, return only the relevant ones"
        ]
        
        # Add question-specific instructions if available
        if question_metadata.get('instructions'):
            instructions_list.insert(1, f"2. Follow these specific guidelines: {'; '.join(question_metadata['instructions'])}")
            # Renumber the remaining instructions
            for i in range(2, len(instructions_list)):
                instructions_list[i] = f"{i+2}. {instructions_list[i].split('. ', 1)[1]}"
        
        prompt_parts.extend([
            "",
            "Instructions:",
            *instructions_list,
            "",
            "Response format: Return only the chunk numbers separated by commas, e.g., '1,3,5'"
        ])
        
        prompt = "\n".join(prompt_parts).strip()
        
        messages = [
            {"role": "system", "content": "You are an expert at identifying the most relevant text chunks for scientific questions. Return only the chunk numbers in order of relevance."},
            {"role": "user", "content": prompt}
        ]
        
        response = await acompletion(model=model, messages=messages, temperature=0)
        
        if response and hasattr(response, 'choices') and response.choices:
            result = response.choices[0].message.content
            logger.info(f"DEBUG: LLM chunk selection response: {result}")
            
            # Parse the response to get chunk numbers
            try:
                # Extract numbers from response (e.g., "1,3,5" or "Chunks 1, 3, and 5")
                import re
                numbers = re.findall(r'\d+', str(result))
                selected_indices = [int(num) - 1 for num in numbers[:max_chunks]]  # Convert to 0-based indices
                logger.info(f"DEBUG: Parsed chunk indices: {selected_indices}")
                
                # Get the selected chunks
                selected_chunks = []
                for idx in selected_indices:
                    if 0 <= idx < len(filtered_chunks):
                        selected_chunks.append(filtered_chunks[idx])
                        logger.info(f"DEBUG: Selected chunk {idx+1}: {filtered_chunks[idx].get('chunk_id')} - Content: {filtered_chunks[idx].get('text', '')[:100]}...")
                
                logger.info(f"Selected {len(selected_chunks)} chunks from {len(filtered_chunks)} total chunks")
                return selected_chunks
                
            except Exception as e:
                logger.error(f"Error parsing chunk selection response: {e}")
                # Fallback: return first few chunks
                return filtered_chunks[:max_chunks]
        else:
            logger.error("No valid response from LLM for chunk selection")
            # Fallback: return first few chunks
            return filtered_chunks[:max_chunks]
            
    except Exception as e:
        logger.error(f"Error selecting top chunks: {e}")
        # Fallback: return first few chunks
        return chunks[:max_chunks]


async def filter_all_chunks(question: str, chunks: List[Dict[str, Any]], max_chunks: int = 5, batch_size: int = None) -> List[Dict[str, Any]]:
    """
    Get the top most relevant chunks for a question using a single LLM call.
    
    Args:
        question (str): The question used for relevance evaluation.
        chunks (List[Dict[str, Any]]): List of text chunk dictionaries.
        max_chunks (int): Maximum number of chunks to return.
        batch_size (int): Not used in simplified approach, kept for compatibility.

    Returns:
        List[Dict[str, Any]]: List of top relevant chunks.
    """
    if not chunks:
        return []
    
    # Get question metadata for the prompt
    question_metadata = get_question_metadata(question)
    
    logger.info(f"Selecting top {max_chunks} chunks from {len(chunks)} total chunks using single LLM call")
    
    # Use the new simplified approach
    relevant_chunks = await get_top_relevant_chunks(
        chunks=chunks,
        question=question,
        question_metadata=question_metadata,
        max_chunks=max_chunks
    )
    
    logger.info(f"Selected {len(relevant_chunks)} relevant chunks")
    return relevant_chunks


async def query_all_chunks(question: str, chunks: List[Dict[str, Any]], batch_size: int = 5) -> List[Dict[str, Any]]:
    """
    Query each relevant text chunk to obtain an answer to the question.
    Uses parallel processing with configurable batch sizes for optimal performance.

    Args:
        question (str): The question to be answered.
        chunks (List[Dict[str, Any]]): List of text chunks that passed the relevance filter.
        batch_size (int): Number of chunks to process in parallel (default: 5).

    Returns:
        List[Dict[str, Any]]: List of chunks updated with answers.
    """
    if not chunks:
        return []
    
    # Process chunks in parallel batches to avoid overwhelming the API
    all_answered_chunks = []
    
    # Split chunks into batches for parallel processing
    chunk_batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
    
    logger.info(f"Generating answers for {len(chunks)} chunks in {len(chunk_batches)} batches of {batch_size}")
    
    for batch_idx, batch in enumerate(chunk_batches):
        logger.info(f"Processing answer batch {batch_idx + 1}/{len(chunk_batches)} ({len(batch)} chunks)")
        
        # Process this batch in parallel
        tasks = [get_answer(question, chunk) for chunk in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions and collect valid results
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"Error generating answer for chunk in batch {batch_idx + 1}: {result}")
                # Mark chunk as failed on error
                batch[i]['answer'] = {'answer': 'Error occurred during answer generation', 'reason': f'Error: {str(result)}'}
            else:
                all_answered_chunks.append(result)
        
        # Small delay between batches to avoid rate limiting
        if batch_idx < len(chunk_batches) - 1:
            await asyncio.sleep(BATCH_DELAY)
    
    logger.info(f"Successfully generated answers for {len(all_answered_chunks)} chunks")
    return all_answered_chunks


async def reflect_answers(question: str, chunks: List[Dict[str, Any]], model: str = ANSWER_MODEL) -> Any:
    """
    Reflect on the answers from different text chunks to derive a consolidated answer.
    If no good answer can be synthesized, returns the no_info_response from question metadata.

    Args:
        question (str): The question to be reflected upon.
        chunks (List[Dict[str, Any]]): List of text chunks with answers.
        model (str, optional): Model identifier for the API call. Defaults to 'openai/gpt-4o-mini'.

    Returns:
        Any: The final consolidated answer parsed from the API response.
    """
    # Get question metadata to access no_info_response
    question_metadata = get_question_metadata(question)
    no_info_response = question_metadata.get('no_info_response', 'Information not found in the provided text.')
    
    formatted_chunks: str = "\n".join(
        f"""
<Reference text chunk_id:{chunk.get('chunk_id', 'N/A')}>
{chunk.get('text', '')}
</Reference text chunk_id:{chunk.get('chunk_id', 'N/A')}>
<Answer chunk_id:{chunk.get('chunk_id', 'N/A')}>
{chunk.get('answer', '')}
</Answer chunk_id:{chunk.get('chunk_id', 'N/A')}>
        """.strip() for chunk in chunks
    )

    # Build enhanced reflection prompt with examples and guidelines
    prompt_parts = [f"<Question>\n{question}\n</Question>"]
    
    # Add instructions if available
    if question_metadata.get('instructions'):
        instructions_text = "\n".join([f"- {instruction}" for instruction in question_metadata['instructions']])
        prompt_parts.append(f"<Instructions>\n{instructions_text}\n</Instructions>")
    
    # Add output format if available
    if question_metadata.get('output_format'):
        prompt_parts.append(f"<Output Format>\n{question_metadata['output_format']}\n</Output Format>")
    
    # Add good examples if available
    if question_metadata.get('example_output'):
        examples_text = "\n".join([f"✅ Good: {example}" for example in question_metadata['example_output']])
        prompt_parts.append(f"<Good Examples>\n{examples_text}\n</Good Examples>")
    
    # Add bad examples if available
    if question_metadata.get('bad_example_output'):
        bad_examples_text = "\n".join([f"❌ Avoid: {example}" for example in question_metadata['bad_example_output']])
        prompt_parts.append(f"<Bad Examples - AVOID THESE>\n{bad_examples_text}\n</Bad Examples>")
    
    # Add the formatted chunks
    prompt_parts.append(f"<Text Chunks and Answers>\n{formatted_chunks}\n</Text Chunks and Answers>")
    
    # Add final guidance
    prompt_parts.append("""
<Important Guidelines>
- Synthesize the BEST answer from all available chunks
- Use the exact format specified in Output Format
- Follow the Good Examples pattern exactly
- AVOID the Bad Examples patterns (no explanations, no context, no repetition)
- Be concise and direct - provide ONLY the requested information
- Only return "INSUFFICIENT_INFO" if absolutely no relevant information can be found
- If information is contradictory, try to resolve conflicts and provide the most likely answer
- Ensure your answer matches the quality and format of the Good Examples
</Important Guidelines>
""")
    
    prompt = "\n".join(prompt_parts).strip()

    messages = [{"content": prompt, "role": "user"}]

    for i in range(RETRY):
        try:
            response = await acompletion(model=model, messages=messages, response_format=AnswerWithChunkId,temperature=0)
            result = json.loads(response.choices[0].message.content)
            logger.info("Reflected answer: %s", result)
            return result
        except Exception as e:
            logger.error("Error reflecting answers: %s", e)
            time.sleep(1)


# --------------------------------------------------------------------------
# Batch Processing Helpers with tqdm progress bar
# --------------------------------------------------------------------------

def chunked(lst: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.

    Args:
        lst (List[Any]): The list to split.
        batch_size (int): The size of each chunk.

    Returns:
        List[List[Any]]: List of chunks.
    """
    return [lst[i:i + batch_size] for i in range(0, len(lst), batch_size)]


async def process_batches_async(
        question: str,
        chunks: List[Dict[str, Any]],
        batch_size: int,
        process_func: Callable[[str, List[Dict[str, Any]]], Any],
        desc: str = "Processing batches"
) -> List[Any]:
    """
    Process chunks in batches asynchronously with progress tracking.

    Args:
        question (str): The question being processed.
        chunks (List[Dict[str, Any]]): List of chunks to process.
        batch_size (int): Size of each batch.
        process_func (Callable): Function to process each batch.
        desc (str): Description for the progress bar.

    Returns:
        List[Any]: Results from processing all batches.
    """
    if not chunks:
        return []

    batches = chunked(chunks, batch_size)
    results = []

    for batch in tqdm(batches, desc=desc):
        batch_results = await process_func(question, batch)
        results.extend(batch_results)

    return results


# --------------------------------------------------------------------------
# Main Execution Flow
# --------------------------------------------------------------------------

async def ask_json(question: str = None, json_path: str=None, batch_size=256) -> None:
    """
    Main asynchronous entry point for processing text chunks to extract and reflect on answers.

    Steps performed:
      1. Load JSON data containing text chunks.
      2. Filter chunks based on relevance to the question.
      3. Query each relevant chunk to retrieve an answer.
      4. Reflect on the collected answers to generate a final consolidated answer.
    """

    if question is None:
        question: str = "What is the main topic of the paper?"
    if json_path is None:
        # Try to get default path from config
        try:
            import sys
            sys.path.append('..')
            from config import get_papers_dir
            default_papers_dir = get_papers_dir()
            json_path = os.path.join(default_papers_dir, "001", "pages", "merged_v2.json")
        except ImportError:
            # Fallback to relative path
            json_path: str = "papers/001/pages/merged_v2.json"

    # Load JSON data from file.
    json_obj: Dict[str, Any] = load_json_file(json_path)
    original_chunks: List[Dict[str, Any]] = json_obj.get('data', {}).get('chunks', [])
    BATCH_SIZE: int = batch_size
    
    # Create a fresh copy of chunks for each question to avoid state persistence
    # This prevents chunks from being modified by previous questions
    chunks = [chunk.copy() for chunk in original_chunks]
    logger.info(f"Using {len(chunks)} fresh chunks from merged_v2.json (deduplication handled in PDF processing)")
    
    # DEBUG: Check first few chunks
    logger.info(f"DEBUG: First chunk keys: {list(chunks[0].keys()) if chunks else 'No chunks'}")
    logger.info(f"DEBUG: Sample chunk text: {chunks[0].get('text', '')[:100] if chunks else 'No chunks'}...")

    # Step 1: Get question-specific configuration
    question_config = get_question_config(question)
    logger.info(f"Question config: {question_config}")
    
    # Step 2: Filter out irrelevant chunks with question-specific settings.
    # Use parallel processing with optimized batch sizes
    relevance_batch_size = min(DEFAULT_RELEVANCE_BATCH_SIZE, len(chunks), MAX_CONCURRENT_REQUESTS)
    
    # Step 2: Filter out irrelevant chunks with question-specific settings.
    # Use parallel processing with optimized batch sizes
    relevance_batch_size = min(DEFAULT_RELEVANCE_BATCH_SIZE, len(chunks), MAX_CONCURRENT_REQUESTS)
    relevant_chunks: List[Dict[str, Any]] = await filter_all_chunks(
        question, chunks, 
        question_config['max_chunks'], 
        batch_size=relevance_batch_size
    )

    if len(relevant_chunks) == 0:
        logger.info("No relevant chunks found for the question: %s", question)
        return {
            "answer": question_config.get('no_info_response', 'Information not found in the provided text.'),
            "chunk_ids": [],
            "reason": "No relevant chunks found for the question.",
            "relevance_info": {
                "total_chunks_processed": len(chunks),
                "relevant_chunks_found": 0,
                "question_config": question_config,
                "selected_chunks": []
            },
            "question_metadata": get_question_metadata(question),
            "quality_assessment": {
                "confidence": "high",
                "issues": ["No relevant chunks found"],
                "recommendations": ["Review question formulation or chunk selection criteria"]
            }
        }
    
    # Log selected chunks for debugging
    logger.info(f"Found {len(relevant_chunks)} relevant chunks:")
    for i, chunk in enumerate(relevant_chunks):
        chunk_id = chunk.get('chunk_id', 'N/A')
        logger.info(f"  Chunk {i+1}: ID {chunk_id}")

    # Step 2: Query each relevant chunk for its answer.
    # Use parallel processing with optimized batch sizes for answer generation
    answer_batch_size = min(DEFAULT_ANSWER_BATCH_SIZE, len(relevant_chunks), MAX_CONCURRENT_REQUESTS)
    answered_chunks: List[Dict[str, Any]] = await query_all_chunks(
        question, relevant_chunks, 
        batch_size=answer_batch_size
    )
    # Step 3: Reflect on all collected answers to produce the final answer.
    final_result: Any = await reflect_answers(question, answered_chunks)
    # final_result: Any = await process_batches_async(
    #     question, answered_chunks, BATCH_SIZE, reflect_answers, desc="Reflecting answers"
    # )

    logger.info("Final result: %s", final_result)
    
    # Check if the reflection stage determined insufficient information
    if isinstance(final_result, dict) and final_result.get('answer') == 'INSUFFICIENT_INFO':
        logger.info("Reflection stage determined insufficient information, using no_info_response")
        final_result['answer'] = question_config.get('no_info_response', 'Information not found in the provided text.')
        final_result['reason'] = 'Insufficient or incoherent information found in relevant chunks'
    
    # Get question metadata for enhanced output
    question_metadata = get_question_metadata(question)
    
    # Assess the quality of the final answer
    answer_quality = assess_answer_quality(question, relevant_chunks, final_result.get('answer', ''))
    
    # Ensure the final_result has the required structure
    if isinstance(final_result, dict):
        # Ensure required fields exist
        if 'answer' not in final_result:
            final_result['answer'] = question_config.get('no_info_response', 'Information not found in the provided text.')
        if 'reason' not in final_result:
            final_result['reason'] = 'Answer generated from available information'
        if 'chunk_ids' not in final_result:
            final_result['chunk_ids'] = [chunk.get('chunk_id', 'N/A') for chunk in relevant_chunks]
    else:
        # If final_result is not a dict, create the proper structure
        final_result = {
            'answer': str(final_result),
            'reason': 'Answer generated from available information',
            'chunk_ids': [chunk.get('chunk_id', 'N/A') for chunk in relevant_chunks]
        }
    
    # Create the enhanced result with the required structure
    enhanced_result = {
        "answer": final_result.get('answer', ''),
        "reason": final_result.get('reason', ''),
        "chunk_ids": final_result.get('chunk_ids', []),
        # Additional metadata fields
        "relevance_info": {
            "total_chunks_processed": len(chunks),
            "relevant_chunks_found": len(relevant_chunks),
            "question_config": question_config,
            "selected_chunks": [
                {
                    "chunk_id": chunk.get('chunk_id', 'N/A'),
                    "text_preview": chunk.get('text', '')[:200] + "..." if len(chunk.get('text', '')) > 200 else chunk.get('text', '')
                }
                for chunk in relevant_chunks
            ]
        },
        "question_metadata": question_metadata,
        "quality_assessment": answer_quality
    }
    
    pprint(enhanced_result)
    return enhanced_result


# Entry point when running as a script.
if __name__ == "__main__":
    asyncio.run(ask_json())
