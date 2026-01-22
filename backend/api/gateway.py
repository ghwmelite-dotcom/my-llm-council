"""OpenAI-compatible API gateway router."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
import uuid
import json

from .models import (
    ChatCompletionRequest, ChatCompletionResponse,
    ModelInfo, ModelList, ChatMessage, ChatCompletionChoice
)
from .transform import transform_openai_request, transform_council_response
from .streaming import stream_openai_response
from .auth import verify_api_key
from ..config import API_GATEWAY_CONFIG, SPECIALIZED_COUNCILS
from ..council import (
    stage1_collect_responses, stage2_collect_rankings,
    stage3_synthesize_final, calculate_aggregate_rankings
)
from ..routing import route_query_smart
from ..cache import check_cache, cache_response

router = APIRouter(prefix="/v1", tags=["OpenAI Compatible API"])


@router.get("/models")
async def list_models(
    api_key: Optional[str] = Depends(verify_api_key)
) -> ModelList:
    """
    List available models (councils).

    Returns models that can be used in the /chat/completions endpoint.
    """
    models = []

    # Add council models
    for council_name, council_config in SPECIALIZED_COUNCILS.items():
        models.append(ModelInfo(
            id=f"council-{council_name}",
            owned_by="llm-council"
        ))

    # Add compatibility aliases
    mapping = API_GATEWAY_CONFIG.get("model_name_mapping", {})
    for alias in mapping.keys():
        models.append(ModelInfo(
            id=alias,
            owned_by="llm-council"
        ))

    return ModelList(data=models)


@router.get("/models/{model_id}")
async def get_model(
    model_id: str,
    api_key: Optional[str] = Depends(verify_api_key)
) -> ModelInfo:
    """
    Get information about a specific model.
    """
    # Check if it's a valid council or alias
    if model_id in SPECIALIZED_COUNCILS:
        return ModelInfo(id=model_id, owned_by="llm-council")

    if model_id.startswith("council-"):
        council_name = model_id[8:]
        if council_name in SPECIALIZED_COUNCILS:
            return ModelInfo(id=model_id, owned_by="llm-council")

    mapping = API_GATEWAY_CONFIG.get("model_name_mapping", {})
    if model_id in mapping:
        return ModelInfo(id=model_id, owned_by="llm-council")

    raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


@router.post("/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Create a chat completion using the LLM Council.

    This is an OpenAI-compatible endpoint. Send requests in the same format
    as OpenAI's /v1/chat/completions endpoint.

    The model name maps to a council:
    - "gpt-4", "gpt-3.5-turbo" -> general council
    - "council-math" -> math council
    - "council-creative" -> creative council
    - etc.
    """
    config = API_GATEWAY_CONFIG

    if not config.get("enabled", True):
        raise HTTPException(
            status_code=503,
            detail="API Gateway is disabled"
        )

    # Transform request to council format
    query, council_type = transform_openai_request(request)

    if request.stream:
        # Streaming response
        return await create_streaming_completion(request, query, council_type)
    else:
        # Non-streaming response
        return await create_sync_completion(request, query, council_type)


async def create_sync_completion(
    request: ChatCompletionRequest,
    query: str,
    council_type: str
) -> ChatCompletionResponse:
    """
    Create a synchronous (non-streaming) completion.
    """
    from ..config import SEMANTIC_CACHE_CONFIG

    # Check cache
    cache_result = check_cache(query) if SEMANTIC_CACHE_CONFIG.get("enabled", True) else None

    if cache_result:
        cached_response, similarity = cache_result
        return transform_council_response(
            cached_response.stage3_result,
            request,
            cached_response.stage1_results,
            cached_response.stage2_results,
            cached_response.metadata
        )

    # Get council config
    council_config = SPECIALIZED_COUNCILS.get(council_type, SPECIALIZED_COUNCILS["general"])
    models = council_config.get("models", [])

    # Run council stages
    try:
        # Stage 1: Collect responses
        from ..council import stage1_mini_council
        stage1_results = await stage1_mini_council(query, models)

        if not stage1_results:
            raise HTTPException(
                status_code=500,
                detail="All models failed to respond"
            )

        # Stage 2: Collect rankings
        stage2_results, label_to_model = await stage2_collect_rankings(query, stage1_results)
        aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Stage 3: Synthesize
        stage3_result = await stage3_synthesize_final(query, stage1_results, stage2_results)

        metadata = {
            "label_to_model": label_to_model,
            "aggregate_rankings": aggregate_rankings
        }

        # Cache the response
        if SEMANTIC_CACHE_CONFIG.get("enabled", True):
            cache_response(
                query=query,
                stage1_results=stage1_results,
                stage2_results=stage2_results,
                stage3_result=stage3_result,
                metadata=metadata
            )

        # Transform to OpenAI format
        return transform_council_response(
            stage3_result,
            request,
            stage1_results,
            stage2_results,
            metadata
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Council error: {str(e)}"
        )


async def create_streaming_completion(
    request: ChatCompletionRequest,
    query: str,
    council_type: str
):
    """
    Create a streaming completion.
    """
    import asyncio

    async def generate():
        request_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        import time
        created = int(time.time())

        # Send initial chunk
        initial = {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": request.model,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
        }
        yield f"data: {json.dumps(initial)}\n\n"

        try:
            # Get council config
            council_config = SPECIALIZED_COUNCILS.get(council_type, SPECIALIZED_COUNCILS["general"])
            models = council_config.get("models", [])

            # Run council (simplified for streaming)
            from ..council import stage1_mini_council
            stage1_results = await stage1_mini_council(query, models)

            if stage1_results:
                stage2_results, label_to_model = await stage2_collect_rankings(query, stage1_results)
                stage3_result = await stage3_synthesize_final(query, stage1_results, stage2_results)

                content = stage3_result.get("response", "")

                # Stream content in chunks
                chunk_size = 20
                for i in range(0, len(content), chunk_size):
                    chunk_text = content[i:i + chunk_size]
                    chunk = {
                        "id": request_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": request.model,
                        "choices": [{"index": 0, "delta": {"content": chunk_text}, "finish_reason": None}]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.01)  # Small delay for streaming effect

        except Exception as e:
            error_chunk = {
                "id": request_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [{"index": 0, "delta": {"content": f"[Error: {str(e)}]"}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

        # Final chunk
        final = {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": request.model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
        yield f"data: {json.dumps(final)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
