"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details')
            }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}


async def query_model_with_tools(
    model: str,
    messages: List[Dict[str, str]],
    tools: List[Dict[str, Any]] = None,
    timeout: float = 120.0,
    max_tool_rounds: int = 3
) -> Optional[Dict[str, Any]]:
    """
    Query a model with tool support and handle tool execution loop.

    Args:
        model: OpenRouter model identifier
        messages: List of message dicts with 'role' and 'content'
        tools: List of tool definitions in OpenAI format
        timeout: Request timeout in seconds
        max_tool_rounds: Maximum rounds of tool execution

    Returns:
        Response dict with 'content', 'tool_calls', and 'tool_results', or None if failed
    """
    from .tools import parse_tool_calls, execute_tools, format_tool_results
    from .config import TOOLS_CONFIG

    if not tools or not TOOLS_CONFIG.get("enabled", True):
        return await query_model(model, messages, timeout)

    all_tool_results = []
    current_messages = messages.copy()

    for round_num in range(max_tool_rounds):
        # Query the model
        response = await query_model(model, current_messages, timeout)

        if response is None:
            return None

        content = response.get('content', '')

        # Parse any tool calls from the response
        tool_calls = parse_tool_calls(content)

        if not tool_calls:
            # No more tool calls, return final response
            response['tool_results'] = all_tool_results
            return response

        # Execute tools
        results = await execute_tools(tool_calls)
        all_tool_results.append(results)

        # Format results for context
        results_text = format_tool_results(results)

        # Add assistant response and tool results to conversation
        current_messages.append({
            "role": "assistant",
            "content": content
        })
        current_messages.append({
            "role": "user",
            "content": f"Tool execution results:\n{results_text}\n\nPlease continue your response incorporating these results."
        })

    # Max rounds reached, return last response
    response['tool_results'] = all_tool_results
    return response
