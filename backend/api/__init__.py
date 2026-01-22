"""OpenAI-compatible API gateway for LLM Council."""

from .gateway import router as gateway_router
from .models import ChatCompletionRequest, ChatCompletionResponse
from .transform import transform_openai_request, transform_council_response
from .streaming import stream_openai_response
from .auth import verify_api_key

__all__ = [
    'gateway_router',
    'ChatCompletionRequest',
    'ChatCompletionResponse',
    'transform_openai_request',
    'transform_council_response',
    'stream_openai_response',
    'verify_api_key',
]
