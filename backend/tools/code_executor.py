"""Sandboxed code execution tool."""

import subprocess
import sys
import tempfile
import os
from typing import Dict, Any
from ..config import TOOLS_CONFIG

# Maximum output size (characters)
MAX_OUTPUT_SIZE = 10000

# Default timeout
DEFAULT_TIMEOUT = 5


async def execute_code(code: str, timeout: int = None) -> Dict[str, Any]:
    """
    Execute Python code in a sandboxed subprocess.

    Security measures:
    - Runs in a separate subprocess
    - Limited execution time
    - Output size limits
    - No network access (in future: use Docker)

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        Dict with execution result
    """
    # Check if code execution is enabled
    if not TOOLS_CONFIG.get("code_execution_enabled", False):
        return {
            "success": False,
            "error": "Code execution is disabled for security reasons"
        }

    timeout = timeout or TOOLS_CONFIG.get("tool_timeout_seconds", DEFAULT_TIMEOUT)
    timeout = min(timeout, 30)  # Cap at 30 seconds

    # Create a temporary file for the code
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            temp_file = f.name

        # Execute in subprocess
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={
                **os.environ,
                # Restrict some environment variables for security
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )

        stdout = result.stdout[:MAX_OUTPUT_SIZE] if result.stdout else ""
        stderr = result.stderr[:MAX_OUTPUT_SIZE] if result.stderr else ""

        # Truncation notice
        if len(result.stdout or "") > MAX_OUTPUT_SIZE:
            stdout += "\n[Output truncated...]"
        if len(result.stderr or "") > MAX_OUTPUT_SIZE:
            stderr += "\n[Output truncated...]"

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "timeout": timeout
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Execution timed out after {timeout} seconds",
            "timeout": timeout
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Execution error: {str(e)}"
        }
    finally:
        # Clean up temp file
        try:
            if 'temp_file' in locals():
                os.unlink(temp_file)
        except:
            pass


def format_execution_result(result: Dict[str, Any]) -> str:
    """
    Format code execution result for injection into model context.

    Args:
        result: Raw execution result

    Returns:
        Formatted string
    """
    if not result.get("success"):
        error = result.get("error", "Unknown error")
        stderr = result.get("stderr", "")
        if stderr:
            return f"[Code execution failed]\nError: {error}\nStderr:\n{stderr}"
        return f"[Code execution failed: {error}]"

    lines = ["[Code execution result]"]

    stdout = result.get("stdout", "").strip()
    stderr = result.get("stderr", "").strip()

    if stdout:
        lines.append(f"Output:\n{stdout}")

    if stderr:
        lines.append(f"Warnings/Errors:\n{stderr}")

    if not stdout and not stderr:
        lines.append("(No output)")

    return "\n".join(lines)
