"""Streaming response conversion for OpenAI compatibility."""

import json
import time
import uuid
from typing import AsyncGenerator, Dict, Any


async def stream_openai_response(
    council_stream: AsyncGenerator[str, None],
    model: str,
    request_id: str = None
) -> AsyncGenerator[str, None]:
    """
    Convert council SSE stream to OpenAI streaming format.

    Args:
        council_stream: The council's event stream
        model: Model name for the response
        request_id: Optional request ID

    Yields:
        OpenAI-formatted SSE chunks
    """
    request_id = request_id or f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created = int(time.time())

    # Send initial chunk
    initial_chunk = {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {"role": "assistant"},
            "finish_reason": None
        }]
    }
    yield f"data: {json.dumps(initial_chunk)}\n\n"

    # Process council events
    accumulated_content = ""

    async for event in council_stream:
        # Parse council event
        if event.startswith("data: "):
            try:
                data = json.loads(event[6:])
                event_type = data.get("type", "")

                # Handle different event types
                if event_type == "stage3_complete":
                    # Main response content
                    stage3_data = data.get("data", {})
                    content = stage3_data.get("response", stage3_data.get("content", ""))

                    # Stream content in chunks
                    chunk_size = 50  # Characters per chunk
                    for i in range(0, len(content), chunk_size):
                        chunk_text = content[i:i + chunk_size]
                        chunk = {
                            "id": request_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model,
                            "choices": [{
                                "index": 0,
                                "delta": {"content": chunk_text},
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"

                elif event_type == "cache_hit":
                    # Cache hit - will get stage3_complete from cached data
                    pass

                elif event_type == "complete":
                    # Council finished - send done
                    pass

                elif event_type == "error":
                    # Error occurred
                    error_msg = data.get("message", "Unknown error")
                    error_chunk = {
                        "id": request_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": f"[Error: {error_msg}]"},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"

            except json.JSONDecodeError:
                pass

    # Send final chunk with finish_reason
    final_chunk = {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"


def format_sse_event(data: Dict[str, Any]) -> str:
    """
    Format data as an SSE event.

    Args:
        data: Data to format

    Returns:
        SSE-formatted string
    """
    return f"data: {json.dumps(data)}\n\n"
