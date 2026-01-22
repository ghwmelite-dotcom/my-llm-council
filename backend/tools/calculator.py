"""Calculator tool implementation with safe math evaluation."""

import math
import re
from typing import Dict, Any, Union

# Safe math functions available
SAFE_MATH_FUNCTIONS = {
    # Basic math
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sum': sum,
    'pow': pow,

    # Math module functions
    'sqrt': math.sqrt,
    'exp': math.exp,
    'log': math.log,
    'log10': math.log10,
    'log2': math.log2,

    # Trigonometry
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'atan2': math.atan2,
    'sinh': math.sinh,
    'cosh': math.cosh,
    'tanh': math.tanh,

    # Angle conversion
    'degrees': math.degrees,
    'radians': math.radians,

    # Special functions
    'factorial': math.factorial,
    'gcd': math.gcd,
    'ceil': math.ceil,
    'floor': math.floor,

    # Constants
    'pi': math.pi,
    'e': math.e,
    'tau': math.tau,
    'inf': math.inf,
}


def safe_eval(expression: str) -> Union[float, int, str]:
    """
    Safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression string

    Returns:
        Result of evaluation or error message
    """
    # Remove any dangerous characters
    dangerous_patterns = [
        r'__',           # Dunder methods
        r'import',       # Imports
        r'exec',         # Code execution
        r'eval',         # Nested eval
        r'open',         # File operations
        r'os\.',         # OS module
        r'sys\.',        # Sys module
        r'subprocess',   # Subprocess
        r'compile',      # Code compilation
        r'globals',      # Global access
        r'locals',       # Local access
        r'getattr',      # Attribute access
        r'setattr',      # Attribute setting
        r'delattr',      # Attribute deletion
        r'class',        # Class definition
        r'lambda',       # Lambda functions (could be dangerous)
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, expression, re.IGNORECASE):
            return f"Error: Expression contains forbidden pattern: {pattern}"

    # Prepare the evaluation namespace
    safe_namespace = {"__builtins__": {}}
    safe_namespace.update(SAFE_MATH_FUNCTIONS)

    try:
        # Try to evaluate the expression
        result = eval(expression, safe_namespace)

        # Handle special float values
        if isinstance(result, float):
            if math.isnan(result):
                return "Result: NaN (Not a Number)"
            if math.isinf(result):
                return f"Result: {'Infinity' if result > 0 else '-Infinity'}"

        return result

    except SyntaxError as e:
        return f"Syntax error: {str(e)}"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except ValueError as e:
        return f"Math error: {str(e)}"
    except OverflowError:
        return "Error: Result too large to compute"
    except Exception as e:
        return f"Calculation error: {str(e)}"


async def calculate(expression: str) -> Dict[str, Any]:
    """
    Perform a mathematical calculation.

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        Dict with calculation result
    """
    # Clean up the expression
    expression = expression.strip()

    # Evaluate
    result = safe_eval(expression)

    if isinstance(result, str) and (result.startswith("Error:") or result.startswith("Syntax")):
        return {
            "success": False,
            "expression": expression,
            "error": result
        }

    return {
        "success": True,
        "expression": expression,
        "result": result,
        "result_type": type(result).__name__
    }


def format_calculation_result(result: Dict[str, Any]) -> str:
    """
    Format calculation result for injection into model context.

    Args:
        result: Raw calculation result

    Returns:
        Formatted string
    """
    if not result.get("success"):
        return f"[Calculation failed: {result.get('error', 'Unknown error')}]"

    expr = result.get("expression", "")
    res = result.get("result", "")

    return f"Calculation: {expr} = {res}"
