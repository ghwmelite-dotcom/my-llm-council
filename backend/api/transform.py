"""Transform between OpenAI format and council format."""

from typing import List, Dict, Any, Tuple
from .models import ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatCompletionChoice, UsageStats
from ..config import API_GATEWAY_CONFIG, SPECIALIZED_COUNCILS
import uuid
import time


def transform_openai_request(request: ChatCompletionRequest) -> Tuple[str, str]:
    """
    Transform OpenAI request to council query.

    Args:
        request: OpenAI-compatible request

    Returns:
        Tuple of (query_text, council_type)
    """
    # Extract the user's query from messages
    # Use the last user message as the query
    query = ""
    system_context = ""

    for msg in request.messages:
        if msg.role == "user":
            query = msg.content
        elif msg.role == "system":
            system_context = msg.content

    # If there's system context, prepend it
    if system_context:
        query = f"[System Context: {system_context}]\n\n{query}"

    # Map model name to council type
    council_type = get_council_for_model(request.model)

    return query, council_type


def get_council_for_model(model_name: str) -> str:
    """
    Get the appropriate council for a model name.

    Args:
        model_name: The model name from the request

    Returns:
        Council type string
    """
    config = API_GATEWAY_CONFIG
    mapping = config.get("model_name_mapping", {})

    # Check explicit mapping
    if model_name in mapping:
        return mapping[model_name]

    # Check if model name matches a council name
    if model_name in SPECIALIZED_COUNCILS:
        return model_name

    # Check for council- prefix
    if model_name.startswith("council-"):
        council_name = model_name[8:]  # Remove "council-" prefix
        if council_name in SPECIALIZED_COUNCILS:
            return council_name

    # Default council
    return config.get("default_council", "general")


def transform_council_response(
    stage3_result: Dict[str, Any],
    request: ChatCompletionRequest,
    stage1_results: List[Dict[str, Any]] = None,
    stage2_results: List[Dict[str, Any]] = None,
    metadata: Dict[str, Any] = None
) -> ChatCompletionResponse:
    """
    Transform council response to OpenAI format.

    Args:
        stage3_result: The final synthesis from the council
        request: Original request for context
        stage1_results: Optional Stage 1 data for deliberation
        stage2_results: Optional Stage 2 data for deliberation
        metadata: Optional additional metadata

    Returns:
        OpenAI-compatible response
    """
    config = API_GATEWAY_CONFIG

    # Get the synthesized content
    content = stage3_result.get("response", stage3_result.get("content", ""))

    # Build deliberation metadata if requested
    include_deliberation = request.include_deliberation
    if include_deliberation is None:
        include_deliberation = config.get("include_deliberation_default", False)

    council_metadata = None
    if include_deliberation:
        council_metadata = {
            "stage1_responses": stage1_results or [],
            "stage2_rankings": stage2_results or [],
            "chairman_model": stage3_result.get("model", "unknown"),
            "aggregate_rankings": metadata.get("aggregate_rankings", []) if metadata else [],
        }

    # Create response
    response = ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:24]}",
        created=int(time.time()),
        model=request.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=content
                ),
                finish_reason="stop"
            )
        ],
        usage=UsageStats(
            prompt_tokens=estimate_tokens(str(request.messages)),
            completion_tokens=estimate_tokens(content),
            total_tokens=0  # Will be calculated
        ),
        council_metadata=council_metadata
    )

    # Calculate total tokens
    response.usage.total_tokens = response.usage.prompt_tokens + response.usage.completion_tokens

    return response


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Simple estimation: ~4 characters per token for English text.

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // 4
