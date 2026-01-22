"""Tool injection for model prompts."""

from typing import List, Dict, Any
from .registry import get_available_tools, Tool


def inject_tools_into_prompt(
    base_prompt: str,
    tools: List[Tool] = None
) -> str:
    """
    Inject tool descriptions into a prompt.

    Args:
        base_prompt: The original prompt
        tools: List of tools to inject (defaults to all available)

    Returns:
        Modified prompt with tool instructions
    """
    if tools is None:
        tools = get_available_tools()

    if not tools:
        return base_prompt

    tool_descriptions = []
    for tool in tools:
        params_str = ", ".join(
            f"{k}: {v.get('description', v.get('type', 'any'))}"
            for k, v in tool.parameters.get("properties", {}).items()
        )
        tool_descriptions.append(
            f"- {tool.name}({params_str}): {tool.description}"
        )

    tools_section = f"""
You have access to the following tools to help answer the question:

{chr(10).join(tool_descriptions)}

To use a tool, include a tool call in your response using this format:
<tool_call>{{"name": "tool_name", "arguments": {{"param": "value"}}}}</tool_call>

You can make multiple tool calls if needed. After tool results are returned, continue your response.

Important:
- Only use tools when necessary for accurate answers
- Cite tool results in your response
- If a tool fails, acknowledge it and proceed with your best knowledge
"""

    # Insert tools section after the first paragraph or at the start
    if "\n\n" in base_prompt:
        parts = base_prompt.split("\n\n", 1)
        return parts[0] + tools_section + "\n\n" + parts[1]
    else:
        return tools_section + "\n\n" + base_prompt


def format_tool_results(results: Dict[str, Dict[str, Any]]) -> str:
    """
    Format tool results for injection into continuation prompt.

    Args:
        results: Tool execution results

    Returns:
        Formatted string
    """
    from .executor import format_tool_results as fmt_results
    return fmt_results(results)


def create_continuation_prompt(
    original_response: str,
    tool_results: str
) -> str:
    """
    Create a continuation prompt after tool execution.

    Args:
        original_response: The model's original response with tool calls
        tool_results: Formatted tool results

    Returns:
        Continuation prompt
    """
    return f"""Your previous response included tool calls. Here are the results:

{tool_results}

Please continue your response, incorporating these tool results. Provide a complete answer to the original question."""
