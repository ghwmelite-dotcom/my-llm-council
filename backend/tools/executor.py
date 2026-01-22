"""Tool execution orchestrator."""

import asyncio
import json
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from .registry import get_tool, get_available_tools
from .web_search import web_search, format_search_results
from .calculator import calculate, format_calculation_result
from .code_executor import execute_code, format_execution_result
from ..config import TOOLS_CONFIG


@dataclass
class ToolCall:
    """A parsed tool call from model output."""
    name: str
    arguments: Dict[str, Any]
    raw: str = ""


def parse_tool_calls(response_text: str) -> List[ToolCall]:
    """
    Parse tool calls from model response.

    Supports multiple formats:
    1. OpenAI function calling format (JSON in tool_calls)
    2. XML-style tags: <tool_call>{"name": "...", "arguments": {...}}</tool_call>
    3. Markdown code blocks with tool_call label

    Args:
        response_text: The model's response text

    Returns:
        List of parsed ToolCall objects
    """
    calls = []

    # Pattern 1: XML-style tags
    xml_pattern = r'<tool_call>\s*({[^}]+})\s*</tool_call>'
    for match in re.finditer(xml_pattern, response_text, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            calls.append(ToolCall(
                name=data.get("name", ""),
                arguments=data.get("arguments", {}),
                raw=match.group(0)
            ))
        except json.JSONDecodeError:
            pass

    # Pattern 2: Markdown code blocks labeled as tool_call
    md_pattern = r'```tool_call\s*\n({[^`]+})\s*\n```'
    for match in re.finditer(md_pattern, response_text, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            calls.append(ToolCall(
                name=data.get("name", ""),
                arguments=data.get("arguments", {}),
                raw=match.group(0)
            ))
        except json.JSONDecodeError:
            pass

    # Pattern 3: JSON objects with "tool" or "function" keys
    json_pattern = r'\{[^{}]*"(?:tool|function)"[^{}]*\}'
    for match in re.finditer(json_pattern, response_text):
        try:
            data = json.loads(match.group(0))
            name = data.get("tool") or data.get("function") or data.get("name")
            args = data.get("arguments") or data.get("args") or data.get("params", {})
            if name:
                calls.append(ToolCall(
                    name=name,
                    arguments=args if isinstance(args, dict) else {},
                    raw=match.group(0)
                ))
        except json.JSONDecodeError:
            pass

    return calls


async def execute_single_tool(
    tool_call: ToolCall
) -> Tuple[str, Dict[str, Any]]:
    """
    Execute a single tool call.

    Args:
        tool_call: The tool call to execute

    Returns:
        Tuple of (tool_name, result_dict)
    """
    tool = get_tool(tool_call.name)

    if not tool:
        return tool_call.name, {
            "success": False,
            "error": f"Unknown or disabled tool: {tool_call.name}"
        }

    try:
        if tool_call.name == "web_search":
            query = tool_call.arguments.get("query", "")
            result = await web_search(query)

        elif tool_call.name == "calculator":
            expression = tool_call.arguments.get("expression", "")
            result = await calculate(expression)

        elif tool_call.name == "code_executor":
            code = tool_call.arguments.get("code", "")
            timeout = tool_call.arguments.get("timeout", 5)
            result = await execute_code(code, timeout)

        else:
            result = {
                "success": False,
                "error": f"Tool {tool_call.name} not implemented"
            }

        return tool_call.name, result

    except Exception as e:
        return tool_call.name, {
            "success": False,
            "error": f"Tool execution error: {str(e)}"
        }


async def execute_tools(
    tool_calls: List[ToolCall],
    max_calls: int = None
) -> Dict[str, Dict[str, Any]]:
    """
    Execute multiple tool calls in parallel.

    Args:
        tool_calls: List of tool calls to execute
        max_calls: Maximum number of calls to execute

    Returns:
        Dict mapping tool names to results
    """
    max_calls = max_calls or TOOLS_CONFIG.get("max_tool_calls_per_response", 3)

    # Limit number of calls
    calls_to_execute = tool_calls[:max_calls]

    # Execute in parallel
    tasks = [execute_single_tool(call) for call in calls_to_execute]
    results = await asyncio.gather(*tasks)

    return {name: result for name, result in results}


def format_tool_results(results: Dict[str, Dict[str, Any]]) -> str:
    """
    Format tool results for injection back into model context.

    Args:
        results: Dict mapping tool names to results

    Returns:
        Formatted string for context injection
    """
    if not results:
        return ""

    lines = ["\n--- Tool Results ---"]

    for tool_name, result in results.items():
        if tool_name == "web_search":
            lines.append(format_search_results(result))
        elif tool_name == "calculator":
            lines.append(format_calculation_result(result))
        elif tool_name == "code_executor":
            lines.append(format_execution_result(result))
        else:
            # Generic formatting
            if result.get("success"):
                lines.append(f"[{tool_name}] Result: {result}")
            else:
                lines.append(f"[{tool_name}] Error: {result.get('error', 'Unknown')}")

    lines.append("--- End Tool Results ---\n")

    return "\n".join(lines)
