"""Tool registry and definitions for agentic council."""

from dataclasses import dataclass, field
from typing import Callable, Dict, Any, List, Optional
from ..config import TOOLS_CONFIG


@dataclass
class Tool:
    """Definition of an available tool."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters
    function: Optional[Callable] = None
    enabled: bool = True

    def to_openai_format(self) -> dict:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


# Web search tool
WEB_SEARCH_TOOL = Tool(
    name="web_search",
    description="Search the web for current information. Use this for questions about recent events, current data, or information that may have changed since training.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            }
        },
        "required": ["query"]
    }
)

# Calculator tool
CALCULATOR_TOOL = Tool(
    name="calculator",
    description="Perform mathematical calculations. Use this for precise arithmetic, algebra, or mathematical operations.",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '2 + 2 * 3', 'sqrt(16)', 'sin(pi/2)')"
            }
        },
        "required": ["expression"]
    }
)

# Code executor tool
CODE_EXECUTOR_TOOL = Tool(
    name="code_executor",
    description="Execute Python code in a sandboxed environment. Use this to run code, test algorithms, or verify programming solutions.",
    parameters={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute"
            },
            "timeout": {
                "type": "integer",
                "description": "Maximum execution time in seconds (default: 5)",
                "default": 5
            }
        },
        "required": ["code"]
    }
)

# Tool registry
TOOL_REGISTRY: Dict[str, Tool] = {
    "web_search": WEB_SEARCH_TOOL,
    "calculator": CALCULATOR_TOOL,
    "code_executor": CODE_EXECUTOR_TOOL
}


def get_tool(name: str) -> Optional[Tool]:
    """
    Get a tool by name.

    Args:
        name: Tool name

    Returns:
        Tool if found and enabled, None otherwise
    """
    tool = TOOL_REGISTRY.get(name)
    if tool and tool.enabled:
        # Check if tool is in available_tools config
        available = TOOLS_CONFIG.get("available_tools", [])
        if name in available:
            return tool
    return None


def get_available_tools() -> List[Tool]:
    """
    Get all available tools based on configuration.

    Returns:
        List of enabled Tool objects
    """
    if not TOOLS_CONFIG.get("enabled", True):
        return []

    available_names = TOOLS_CONFIG.get("available_tools", [])
    tools = []

    for name in available_names:
        tool = TOOL_REGISTRY.get(name)
        if tool and tool.enabled:
            # Special check for code executor
            if name == "code_executor" and not TOOLS_CONFIG.get("code_execution_enabled", False):
                continue
            tools.append(tool)

    return tools


def get_tools_for_openai() -> List[dict]:
    """
    Get tools in OpenAI function calling format.

    Returns:
        List of tool definitions for OpenAI API
    """
    tools = get_available_tools()
    return [t.to_openai_format() for t in tools]
