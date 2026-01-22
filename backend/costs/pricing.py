"""Model pricing information for cost calculations.

Prices are in USD per 1M tokens.
Source: OpenRouter pricing (approximate, may change).
"""

from typing import Dict, Tuple, Optional

# Pricing in USD per 1M tokens: (input_price, output_price)
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    # OpenAI models
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-4-turbo": (10.00, 30.00),
    "openai/gpt-4": (30.00, 60.00),
    "openai/gpt-3.5-turbo": (0.50, 1.50),
    "openai/o1": (15.00, 60.00),
    "openai/o1-mini": (3.00, 12.00),
    "openai/o1-preview": (15.00, 60.00),
    "openai/o3-mini": (1.10, 4.40),

    # Anthropic models
    "anthropic/claude-3.5-sonnet": (3.00, 15.00),
    "anthropic/claude-3.5-sonnet-20241022": (3.00, 15.00),
    "anthropic/claude-sonnet-4.5": (3.00, 15.00),
    "anthropic/claude-3-opus": (15.00, 75.00),
    "anthropic/claude-3-sonnet": (3.00, 15.00),
    "anthropic/claude-3-haiku": (0.25, 1.25),
    "anthropic/claude-3.5-haiku": (0.80, 4.00),

    # Google models
    "google/gemini-pro": (0.125, 0.375),
    "google/gemini-pro-1.5": (1.25, 5.00),
    "google/gemini-2.0-flash-001": (0.10, 0.40),
    "google/gemini-2.5-flash": (0.15, 0.60),
    "google/gemini-2.5-pro": (1.25, 10.00),
    "google/gemini-flash-1.5": (0.075, 0.30),

    # Meta models
    "meta-llama/llama-3.1-405b-instruct": (2.70, 2.70),
    "meta-llama/llama-3.1-70b-instruct": (0.52, 0.75),
    "meta-llama/llama-3.1-8b-instruct": (0.055, 0.055),
    "meta-llama/llama-3.3-70b-instruct": (0.18, 0.40),

    # Mistral models
    "mistralai/mistral-large": (2.00, 6.00),
    "mistralai/mistral-medium": (2.70, 8.10),
    "mistralai/mistral-small": (0.20, 0.60),
    "mistralai/mixtral-8x7b-instruct": (0.24, 0.24),
    "mistralai/mixtral-8x22b-instruct": (0.65, 0.65),

    # Cohere models
    "cohere/command-r-plus": (2.50, 10.00),
    "cohere/command-r": (0.15, 0.60),

    # DeepSeek models
    "deepseek/deepseek-chat": (0.14, 0.28),
    "deepseek/deepseek-r1": (0.55, 2.19),

    # Qwen models
    "qwen/qwen-2.5-72b-instruct": (0.35, 0.40),
    "qwen/qwen-2.5-coder-32b-instruct": (0.18, 0.18),
    "qwen/qwq-32b": (0.12, 0.18),

    # xAI models
    "x-ai/grok-2": (2.00, 10.00),
    "x-ai/grok-beta": (5.00, 15.00),
}

# Default pricing for unknown models (conservative estimate)
DEFAULT_PRICING: Tuple[float, float] = (5.00, 15.00)


def get_model_pricing(model: str) -> Tuple[float, float]:
    """
    Get pricing for a model.

    Args:
        model: OpenRouter model identifier

    Returns:
        Tuple of (input_price_per_1M, output_price_per_1M)
    """
    return MODEL_PRICING.get(model, DEFAULT_PRICING)


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """
    Calculate the cost for a model query.

    Args:
        model: OpenRouter model identifier
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens

    Returns:
        Cost in USD
    """
    input_price, output_price = get_model_pricing(model)

    # Convert from per-1M to per-token
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price

    return input_cost + output_cost


def format_cost(cost: float) -> str:
    """
    Format a cost value for display.

    Args:
        cost: Cost in USD

    Returns:
        Formatted string (e.g., "$0.0012" or "$1.23")
    """
    if cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1.00:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"
