"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio

from . import storage
from .council import (
    run_full_council, run_full_council_tier2,
    generate_conversation_title, stage1_collect_responses,
    stage2_collect_rankings, stage3_synthesize_final, stage3_synthesize_stream,
    calculate_aggregate_rankings, stage2b_collect_rebuttals,
    stage2_devils_advocate, check_consensus,
    stage1_single_model, stage1_mini_council
)
from .config import COUNCIL_MODELS, DEBATE_CONFIG, SMART_ROUTING_CONFIG, SEMANTIC_CACHE_CONFIG, VERIFICATION_CONFIG
from .routing import route_query_smart
from .cache import check_cache, cache_response, get_cache_stats, clear_cache
from .verification import run_verification_stage, should_run_verification
from .api import gateway_router
from .costs import CostTracker
from .export import export_to_markdown, export_to_html
from .analytics import get_analytics
from .feedback import get_feedback_storage
from .memory import get_memory_store, get_relevant_memories, inject_memory_into_prompt
from .memory.extraction import extract_memories_from_conversation
from .multimodal import store_image, get_image, delete_image, cleanup_old_images, prepare_multimodal_messages, is_vision_capable
from .collaboration import get_connection_manager, get_room_manager
from .plugins import get_plugin_registry, PluginConfig
from .plugins.builtin import BUILTIN_PLUGINS, list_builtin_plugins
from .routing.ml import get_routing_model, collect_training_sample, train_model, get_training_store

# Tier 4 imports
from .predictions import (
    place_prediction, resolve_prediction, get_user_predictions,
    update_elo_ratings, get_model_elo, get_elo_leaderboard
)
from .predictions.leaderboard import (
    get_leaderboard, get_model_stats, get_prediction_market_summary
)
from .constitution import (
    get_constitution, get_article, get_constitution_history,
    inject_constitution, format_constitution_for_prompt
)
from .constitution.amendments import (
    propose_amendment, vote_on_amendment, get_pending_amendments,
    process_amendment_vote, get_amendment_history
)
from .observer import (
    run_meta_analysis, detect_biases, generate_observer_report,
    get_cognitive_health_score
)
from .observer.analyzer import get_analysis_history, get_aggregate_statistics

app = FastAPI(title="LLM Council API")

# Enable CORS
import os
DEFAULT_CORS = "http://localhost:5173,http://localhost:3000,https://my-llm-council.up.railway.app"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", DEFAULT_CORS).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount OpenAI-compatible API gateway
app.include_router(gateway_router)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str
    image_ids: Optional[List[str]] = None


class SendMessageV2Request(BaseModel):
    """Request to send a message with Tier 2 features."""
    content: str
    enable_debate: bool = True
    max_debate_rounds: Optional[int] = None
    user_response: Optional[str] = None


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/config")
async def get_config():
    """Get current council configuration."""
    from .config import CHAIRMAN_MODEL
    return {
        "models": COUNCIL_MODELS,
        "chairman": CHAIRMAN_MODEL,
        "debate_enabled": DEBATE_CONFIG.get("enabled", True),
        "max_debate_rounds": DEBATE_CONFIG.get("max_rounds", 3),
        "consensus_threshold": DEBATE_CONFIG.get("consensus_threshold", 0.8),
    }


class UpdateConfigRequest(BaseModel):
    """Request to update council configuration."""
    models: List[str]
    chairman: str


@app.post("/api/config")
async def update_config(request: UpdateConfigRequest):
    """Update council configuration (session-only, not persisted)."""
    from . import config

    # Validate models list
    if not request.models or len(request.models) == 0:
        raise HTTPException(status_code=400, detail="At least one model required")

    if len(request.models) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 models allowed")

    # Update the config module's global variables
    config.COUNCIL_MODELS = request.models
    config.CHAIRMAN_MODEL = request.chairman if request.chairman in request.models else request.models[0]

    return {
        "status": "updated",
        "models": config.COUNCIL_MODELS,
        "chairman": config.CHAIRMAN_MODEL,
    }


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    deleted = storage.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "id": conversation_id}


@app.get("/api/conversations/{conversation_id}/export/markdown")
async def export_conversation_markdown(conversation_id: str):
    """Export a conversation as Markdown."""
    from fastapi.responses import PlainTextResponse
    from .export.markdown import get_markdown_filename

    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    markdown_content = export_to_markdown(conversation)
    filename = get_markdown_filename(conversation)

    return PlainTextResponse(
        content=markdown_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@app.get("/api/conversations/{conversation_id}/export/html")
async def export_conversation_html(conversation_id: str):
    """Export a conversation as HTML (for PDF printing)."""
    from fastapi.responses import HTMLResponse
    from .export.html import get_html_filename

    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    html_content = export_to_html(conversation)
    filename = get_html_filename(conversation)

    return HTMLResponse(
        content=html_content,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    storage.add_user_message(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Run the 3-stage council process
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1_results,
        stage2_results,
        stage3_result
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        try:
            # Initialize cost tracker for this query
            cost_tracker = CostTracker(conversation_id)
            query_start_time = asyncio.get_event_loop().time()
            analytics = get_analytics()

            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Check semantic cache first
            cache_result = check_cache(request.content) if SEMANTIC_CACHE_CONFIG.get("enabled", True) else None
            if cache_result:
                cached_response, similarity = cache_result
                yield f"data: {json.dumps({'type': 'cache_hit', 'data': {'similarity': similarity, 'original_query': cached_response.query, 'routing_tier': cached_response.routing_tier}})}\n\n"

                # Return cached results
                yield f"data: {json.dumps({'type': 'stage1_complete', 'data': cached_response.stage1_results})}\n\n"
                yield f"data: {json.dumps({'type': 'stage2_complete', 'data': cached_response.stage2_results, 'metadata': cached_response.metadata})}\n\n"
                yield f"data: {json.dumps({'type': 'stage3_complete', 'data': cached_response.stage3_result})}\n\n"

                # Wait for title generation if it was started
                if title_task:
                    title = await title_task
                    storage.update_conversation_title(conversation_id, title)
                    yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

                # Save cached response as new message
                storage.add_assistant_message(
                    conversation_id,
                    cached_response.stage1_results,
                    cached_response.stage2_results,
                    cached_response.stage3_result
                )

                yield f"data: {json.dumps({'type': 'complete', 'metadata': {'cached': True, 'similarity': similarity}})}\n\n"
                return

            # Smart routing: determine council size based on complexity
            routing_decision = None
            if SMART_ROUTING_CONFIG.get("enabled", True):
                routing_decision = route_query_smart(request.content)
                yield f"data: {json.dumps({'type': 'routing_decision', 'data': routing_decision.to_dict()})}\n\n"

            # Stage 1: Collect responses based on routing decision
            if routing_decision and routing_decision.tier == 1:
                # Single model for simple queries
                yield f"data: {json.dumps({'type': 'stage1_start', 'data': {'models': routing_decision.models, 'tier': 1}})}\n\n"
                stage1_results, stage1_usage = await stage1_single_model(request.content, routing_decision.models[0], image_ids=request.image_ids)
            elif routing_decision and routing_decision.tier == 2:
                # Mini council for medium complexity
                yield f"data: {json.dumps({'type': 'stage1_start', 'data': {'models': routing_decision.models, 'tier': 2}})}\n\n"
                stage1_results, stage1_usage = await stage1_mini_council(request.content, routing_decision.models, image_ids=request.image_ids)
            else:
                # Full council (default)
                yield f"data: {json.dumps({'type': 'stage1_start', 'data': {'models': COUNCIL_MODELS, 'tier': 3}})}\n\n"
                stage1_results, stage1_usage = await stage1_collect_responses(request.content, image_ids=request.image_ids)

            # Track Stage 1 costs
            for usage in stage1_usage:
                cost_tracker.add_usage(
                    usage['model'],
                    usage['input_tokens'],
                    usage['output_tokens'],
                    'stage1'
                )

            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 1.5: Factual verification (if enabled and applicable)
            verification_report = None
            stage2_verification_context = ""
            current_tier = routing_decision.tier if routing_decision else 3

            if should_run_verification(stage1_results, current_tier):
                yield f"data: {json.dumps({'type': 'stage1_5_start', 'data': {'reason': 'Verifying factual claims'}})}\n\n"
                verification_report, stage2_verification_context = await run_verification_stage(
                    stage1_results, request.content
                )
                if verification_report:
                    yield f"data: {json.dumps({'type': 'stage1_5_complete', 'data': verification_report.to_dict()})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'stage1_5_complete', 'data': {'skipped': True, 'reason': 'Not enough claims to verify'}})}\n\n"

            # Stage 2: Collect rankings (with verification context if available)
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model, stage2_usage = await stage2_collect_rankings(request.content, stage1_results, stage2_verification_context)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

            # Track Stage 2 costs
            for usage in stage2_usage:
                cost_tracker.add_usage(
                    usage['model'],
                    usage['input_tokens'],
                    usage['output_tokens'],
                    'stage2'
                )

            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings, 'verification_report': verification_report.to_dict() if verification_report else None}})}\n\n"

            # Stage 3: Synthesize final answer with streaming tokens
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = None
            async for chunk in stage3_synthesize_stream(request.content, stage1_results, stage2_results):
                if chunk['type'] == 'token':
                    yield f"data: {json.dumps({'type': 'stage3_token', 'token': chunk['token']})}\n\n"
                elif chunk['type'] == 'complete':
                    stage3_result = {'model': chunk['model'], 'response': chunk['response']}
                    # Track Stage 3 costs (estimated from streaming)
                    usage = chunk.get('usage', {})
                    if usage:
                        cost_tracker.add_usage(
                            chunk['model'],
                            usage.get('input_tokens', 0),
                            usage.get('output_tokens', 0),
                            'stage3'
                        )
                    yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"
                elif chunk['type'] == 'error':
                    stage3_result = {'model': chunk['model'], 'response': chunk['response']}
                    yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result
            )

            # Cache the response for future similar queries
            if SEMANTIC_CACHE_CONFIG.get("enabled", True):
                cache_response(
                    query=request.content,
                    stage1_results=stage1_results,
                    stage2_results=stage2_results,
                    stage3_result=stage3_result,
                    metadata={'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings},
                    routing_tier=routing_decision.tier if routing_decision else 3
                )

            # Complete cost tracking and emit summary
            cost_tracker.complete()
            cost_summary = cost_tracker.get_summary()
            yield f"data: {json.dumps({'type': 'cost_summary', 'data': cost_summary})}\n\n"

            # Record analytics
            query_duration = (asyncio.get_event_loop().time() - query_start_time) * 1000
            models_used = [r['model'] for r in stage1_results] if stage1_results else []
            current_tier = routing_decision.tier if routing_decision else 3

            # Record model usage from cost tracker
            for usage in cost_tracker.query_cost.usage_records:
                analytics.record_model_usage(
                    model=usage.model,
                    tokens_in=usage.input_tokens,
                    tokens_out=usage.output_tokens,
                    cost=usage.cost
                )

            # Record rankings if available
            if aggregate_rankings:
                for idx, rank_item in enumerate(aggregate_rankings, 1):
                    analytics.record_ranking(
                        model=rank_item['model'],
                        rank=idx,
                        total_models=len(aggregate_rankings)
                    )

            # Record query
            analytics.record_query(
                query_id=conversation_id,
                tier=current_tier,
                models_used=models_used,
                total_cost=cost_summary.get('total_cost', 0),
                total_tokens=cost_summary.get('total_tokens', 0),
                duration_ms=query_duration,
                cache_hit=False
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# =============================================================================
# Cache API Endpoints
# =============================================================================

@app.get("/api/cache/stats")
async def api_get_cache_stats():
    """Get semantic cache statistics."""
    return get_cache_stats()


@app.get("/api/costs/pricing")
async def api_get_pricing():
    """Get model pricing information."""
    from .costs.pricing import MODEL_PRICING, DEFAULT_PRICING, format_cost
    return {
        "models": {
            model: {
                "input_per_1m": price[0],
                "output_per_1m": price[1],
                "input_formatted": format_cost(price[0]),
                "output_formatted": format_cost(price[1]),
            }
            for model, price in MODEL_PRICING.items()
        },
        "default_pricing": {
            "input_per_1m": DEFAULT_PRICING[0],
            "output_per_1m": DEFAULT_PRICING[1],
        }
    }


# =============================================================================
# Analytics API Endpoints
# =============================================================================

@app.get("/api/analytics/summary")
async def api_get_analytics_summary():
    """Get analytics summary."""
    analytics = get_analytics()
    return analytics.get_summary().to_dict()


@app.get("/api/analytics/models")
async def api_get_model_analytics():
    """Get model performance leaderboard."""
    analytics = get_analytics()
    return {
        "models": analytics.get_model_leaderboard()
    }


@app.get("/api/analytics/model/{model_id:path}")
async def api_get_single_model_analytics(model_id: str):
    """Get analytics for a specific model."""
    analytics = get_analytics()
    if model_id in analytics.model_metrics:
        return analytics.model_metrics[model_id].to_dict()
    raise HTTPException(status_code=404, detail="Model not found in analytics")


# =============================================================================
# Feedback API Endpoints
# =============================================================================

class FeedbackRequest(BaseModel):
    """Request to submit feedback."""
    message_index: int
    rating: int
    feedback_type: str = "overall"
    comment: Optional[str] = None


@app.post("/api/conversations/{conversation_id}/feedback")
async def submit_feedback(conversation_id: str, request: FeedbackRequest):
    """Submit feedback for a response."""
    # Verify conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if request.message_index >= len(conversation.get('messages', [])):
        raise HTTPException(status_code=400, detail="Invalid message index")

    feedback_storage = get_feedback_storage()
    feedback = feedback_storage.add_feedback(
        conversation_id=conversation_id,
        message_index=request.message_index,
        rating=request.rating,
        feedback_type=request.feedback_type,
        comment=request.comment
    )
    return feedback.to_dict()


@app.get("/api/conversations/{conversation_id}/feedback")
async def get_conversation_feedback(conversation_id: str):
    """Get all feedback for a conversation."""
    feedback_storage = get_feedback_storage()
    feedback = feedback_storage.get_feedback_for_conversation(conversation_id)
    return {"feedback": [f.to_dict() for f in feedback]}


@app.get("/api/feedback/stats")
async def get_feedback_stats():
    """Get overall feedback statistics."""
    feedback_storage = get_feedback_storage()
    return feedback_storage.get_feedback_stats()


@app.post("/api/cache/clear")
async def api_clear_cache():
    """Clear the semantic cache."""
    return clear_cache()


# ==================== Memory API ====================

class AddMemoryRequest(BaseModel):
    """Request to add a new memory."""
    content: str
    memory_type: str = "insight"
    tags: list = []
    importance: float = 0.5


class UpdateMemoryRequest(BaseModel):
    """Request to update a memory."""
    content: Optional[str] = None
    memory_type: Optional[str] = None
    tags: Optional[list] = None
    importance: Optional[float] = None


@app.get("/api/memories")
async def list_memories(
    memory_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50
):
    """List all memories with optional filtering."""
    store = get_memory_store()

    if memory_type:
        memories = store.get_memories_by_type(memory_type)
    elif tag:
        memories = store.get_memories_by_tag(tag)
    else:
        memories = store.get_all_memories()

    # Sort by created_at descending and limit
    memories = sorted(memories, key=lambda m: m.created_at, reverse=True)[:limit]

    return {
        "memories": [
            {
                "id": m.id,
                "type": m.type,
                "content": m.content,
                "created_at": m.created_at,
                "tags": m.tags,
                "importance": m.importance,
                "access_count": m.access_count,
                "related_models": m.related_models,
            }
            for m in memories
        ],
        "total": len(store.get_all_memories())
    }


@app.post("/api/memories")
async def add_memory(request: AddMemoryRequest):
    """Add a new memory."""
    store = get_memory_store()
    memory = store.add_memory(
        content=request.content,
        memory_type=request.memory_type,
        tags=request.tags,
        importance=request.importance
    )
    return {
        "id": memory.id,
        "type": memory.type,
        "content": memory.content,
        "created_at": memory.created_at,
        "tags": memory.tags,
        "importance": memory.importance
    }


@app.get("/api/memories/{memory_id}")
async def get_memory(memory_id: str):
    """Get a specific memory."""
    store = get_memory_store()
    memory = store.get_memory(memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {
        "id": memory.id,
        "type": memory.type,
        "content": memory.content,
        "created_at": memory.created_at,
        "tags": memory.tags,
        "importance": memory.importance,
        "access_count": memory.access_count,
        "related_models": memory.related_models,
    }


@app.put("/api/memories/{memory_id}")
async def update_memory(memory_id: str, request: UpdateMemoryRequest):
    """Update a memory."""
    store = get_memory_store()

    updates = {}
    if request.content is not None:
        updates["content"] = request.content
    if request.memory_type is not None:
        updates["type"] = request.memory_type
    if request.tags is not None:
        updates["tags"] = request.tags
    if request.importance is not None:
        updates["importance"] = request.importance

    memory = store.update_memory(memory_id, **updates)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")

    return {
        "id": memory.id,
        "type": memory.type,
        "content": memory.content,
        "tags": memory.tags,
        "importance": memory.importance
    }


@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory."""
    store = get_memory_store()
    deleted = store.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted", "id": memory_id}


@app.get("/api/memories/search")
async def search_memories(query: str, limit: int = 10):
    """Search memories by relevance to a query."""
    memories = get_relevant_memories(query, limit=limit)
    return {
        "query": query,
        "memories": [
            {
                "id": m.id,
                "type": m.type,
                "content": m.content,
                "tags": m.tags,
                "importance": m.importance
            }
            for m in memories
        ]
    }


@app.post("/api/conversations/{conversation_id}/extract-memories")
async def extract_memories_from_conv(conversation_id: str):
    """Extract and save memories from a conversation."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Find the most recent assistant message with all stages
    messages = conversation.get("messages", [])
    assistant_messages = [m for m in messages if m.get("role") == "assistant"]

    if not assistant_messages:
        return {"conversation_id": conversation_id, "extracted_count": 0, "memories": []}

    # Get the last assistant message and the preceding user message
    last_assistant = assistant_messages[-1]
    user_query = ""
    for i, m in enumerate(messages):
        if m == last_assistant and i > 0:
            user_query = messages[i - 1].get("content", "")
            break

    if not user_query or not last_assistant.get("stage3"):
        return {"conversation_id": conversation_id, "extracted_count": 0, "memories": []}

    # Extract memories
    memories = await extract_memories_from_conversation(
        conversation_id=conversation_id,
        user_query=user_query,
        stage1_results=last_assistant.get("stage1", []),
        stage2_results=last_assistant.get("stage2", []),
        stage3_result=last_assistant.get("stage3", {}),
        aggregate_rankings=last_assistant.get("metadata", {}).get("aggregate_rankings", [])
    )

    return {
        "conversation_id": conversation_id,
        "extracted_count": len(memories),
        "memories": [
            {
                "id": m.id,
                "type": m.type,
                "content": m.content,
                "tags": m.tags
            }
            for m in memories
        ]
    }


@app.get("/api/memories/stats")
async def get_memory_stats():
    """Get memory statistics."""
    store = get_memory_store()
    all_memories = store.get_all_memories()

    # Count by type
    type_counts = {}
    for m in all_memories:
        type_counts[m.type] = type_counts.get(m.type, 0) + 1

    # Get most accessed
    most_accessed = sorted(all_memories, key=lambda m: m.access_count, reverse=True)[:5]

    # Get highest importance
    highest_importance = sorted(all_memories, key=lambda m: m.importance, reverse=True)[:5]

    return {
        "total_memories": len(all_memories),
        "by_type": type_counts,
        "most_accessed": [
            {"id": m.id, "content": m.content[:100], "access_count": m.access_count}
            for m in most_accessed
        ],
        "highest_importance": [
            {"id": m.id, "content": m.content[:100], "importance": m.importance}
            for m in highest_importance
        ]
    }


# ==================== Image Upload API ====================

@app.post("/api/images/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image for use in multimodal queries."""
    # Read file content
    content = await file.read()

    # Store the image
    stored = store_image(
        content=content,
        filename=file.filename or "image",
        content_type=file.content_type or "image/jpeg"
    )

    if stored is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid image. Max size: 10MB. Allowed types: jpeg, png, gif, webp"
        )

    return {
        "id": stored.id,
        "filename": stored.filename,
        "content_type": stored.content_type,
        "size_bytes": stored.size_bytes
    }


@app.get("/api/images/{image_id}")
async def get_image_info(image_id: str):
    """Get image metadata (not the actual image data)."""
    image = get_image(image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    return {
        "id": image.id,
        "filename": image.filename,
        "content_type": image.content_type,
        "size_bytes": image.size_bytes,
        "created_at": image.created_at
    }


@app.delete("/api/images/{image_id}")
async def delete_uploaded_image(image_id: str):
    """Delete an uploaded image."""
    deleted = delete_image(image_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"status": "deleted", "id": image_id}


@app.post("/api/images/cleanup")
async def cleanup_images():
    """Remove images older than 24 hours."""
    count = cleanup_old_images()
    return {"removed_count": count}


@app.get("/api/images/{image_id}/thumbnail")
async def get_image_thumbnail(image_id: str):
    """Get image as base64 for preview."""
    image = get_image(image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    return {
        "id": image.id,
        "content_type": image.content_type,
        "data_url": f"data:{image.content_type};base64,{image.base64_data}"
    }


# ==================== Real-time Collaboration API ====================

class CreateRoomRequest(BaseModel):
    """Request to create a collaborative room."""
    name: str
    is_public: bool = False
    max_users: int = 10


@app.post("/api/conversations/{conversation_id}/room")
async def create_collaboration_room(conversation_id: str, request: CreateRoomRequest):
    """Create a collaborative room for a conversation."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    room_manager = get_room_manager()

    # Check if room already exists for this conversation
    existing = room_manager.get_room_by_conversation(conversation_id)
    if existing:
        return {
            "id": existing.id,
            "name": existing.name,
            "is_public": existing.is_public,
            "invite_code": existing.invite_code,
            "already_exists": True
        }

    # Generate invite code
    import secrets
    invite_code = secrets.token_urlsafe(8)

    room = room_manager.create_room(
        room_id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        name=request.name,
        created_by="system",  # Could be user ID in a real system
        is_public=request.is_public,
        max_users=request.max_users,
        invite_code=invite_code
    )

    return {
        "id": room.id,
        "name": room.name,
        "is_public": room.is_public,
        "invite_code": room.invite_code,
        "max_users": room.max_users
    }


@app.get("/api/rooms/{room_id}")
async def get_room_info(room_id: str):
    """Get room information."""
    room_manager = get_room_manager()
    room = room_manager.get_room(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    connection_manager = get_connection_manager()
    users = connection_manager.get_room_users(room.conversation_id)

    return {
        "id": room.id,
        "name": room.name,
        "conversation_id": room.conversation_id,
        "is_public": room.is_public,
        "max_users": room.max_users,
        "current_users": len(users),
        "users": users
    }


@app.get("/api/rooms/join/{invite_code}")
async def join_room_by_code(invite_code: str):
    """Get room info by invite code for joining."""
    room_manager = get_room_manager()
    room = room_manager.get_room_by_invite_code(invite_code)
    if room is None:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    connection_manager = get_connection_manager()
    current_users = connection_manager.get_connection_count(room.conversation_id)

    if current_users >= room.max_users:
        raise HTTPException(status_code=403, detail="Room is full")

    return {
        "room_id": room.id,
        "conversation_id": room.conversation_id,
        "name": room.name,
        "current_users": current_users,
        "max_users": room.max_users
    }


@app.get("/api/rooms/public")
async def list_public_rooms():
    """List all public rooms."""
    room_manager = get_room_manager()
    connection_manager = get_connection_manager()

    rooms = room_manager.get_public_rooms()
    result = []

    for room in rooms:
        users = connection_manager.get_room_users(room.conversation_id)
        result.append({
            "id": room.id,
            "name": room.name,
            "conversation_id": room.conversation_id,
            "current_users": len(users),
            "max_users": room.max_users
        })

    return {"rooms": result}


@app.websocket("/ws/collaborate/{conversation_id}")
async def websocket_collaborate(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time collaboration."""
    connection_manager = get_connection_manager()

    # Get user info from query params
    user_id = websocket.query_params.get("user_id", str(uuid.uuid4()))
    username = websocket.query_params.get("username", f"User-{user_id[:4]}")

    await connection_manager.connect(websocket, conversation_id, user_id, username)

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "typing":
                await connection_manager.broadcast_typing(
                    conversation_id,
                    user_id,
                    username,
                    data.get("is_typing", False)
                )

            elif message_type == "cursor":
                await connection_manager.broadcast_cursor(
                    conversation_id,
                    user_id,
                    data.get("position", {})
                )

            elif message_type == "message_sent":
                # Broadcast to all users that a new message was sent
                await connection_manager.broadcast_to_room(
                    conversation_id,
                    {
                        "type": "new_message",
                        "user_id": user_id,
                        "username": username,
                        "content": data.get("content", ""),
                        "timestamp": data.get("timestamp")
                    },
                    exclude_user=user_id
                )

            elif message_type == "stage_update":
                # Broadcast stage update to all users
                await connection_manager.broadcast_to_room(
                    conversation_id,
                    {
                        "type": "stage_update",
                        "stage": data.get("stage"),
                        "data": data.get("data")
                    }
                )

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        await connection_manager.disconnect(user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await connection_manager.disconnect(user_id)


# ==================== Plugin System API ====================

class PluginSettingsRequest(BaseModel):
    """Request to update plugin settings."""
    settings: Dict[str, Any]


@app.get("/api/plugins")
async def list_plugins():
    """List all registered plugins."""
    registry = get_plugin_registry()
    return {
        "plugins": registry.list_plugins(),
        "available_builtin": list_builtin_plugins()
    }


@app.post("/api/plugins/{plugin_name}/enable")
async def enable_plugin(plugin_name: str):
    """Enable a plugin."""
    registry = get_plugin_registry()

    # If plugin not registered, try to register from builtin
    if not registry.get_plugin(plugin_name):
        plugin_class = BUILTIN_PLUGINS.get(plugin_name)
        if plugin_class:
            registry.register(plugin_class)
        else:
            raise HTTPException(status_code=404, detail="Plugin not found")

    if registry.enable_plugin(plugin_name):
        return {"status": "enabled", "plugin": plugin_name}
    raise HTTPException(status_code=404, detail="Plugin not found")


@app.post("/api/plugins/{plugin_name}/disable")
async def disable_plugin(plugin_name: str):
    """Disable a plugin."""
    registry = get_plugin_registry()
    if registry.disable_plugin(plugin_name):
        return {"status": "disabled", "plugin": plugin_name}
    raise HTTPException(status_code=404, detail="Plugin not found")


@app.get("/api/plugins/{plugin_name}")
async def get_plugin_info(plugin_name: str):
    """Get plugin information."""
    registry = get_plugin_registry()
    plugin = registry.get_plugin(plugin_name)
    if plugin:
        return plugin.get_info()
    raise HTTPException(status_code=404, detail="Plugin not found")


@app.put("/api/plugins/{plugin_name}/settings")
async def update_plugin_settings(plugin_name: str, request: PluginSettingsRequest):
    """Update plugin settings."""
    registry = get_plugin_registry()
    if registry.update_settings(plugin_name, request.settings):
        plugin = registry.get_plugin(plugin_name)
        return {"status": "updated", "plugin": plugin.get_info()}
    raise HTTPException(status_code=404, detail="Plugin not found")


@app.post("/api/plugins/builtin/{plugin_name}/register")
async def register_builtin_plugin(plugin_name: str):
    """Register a built-in plugin."""
    plugin_class = BUILTIN_PLUGINS.get(plugin_name)
    if not plugin_class:
        raise HTTPException(status_code=404, detail="Built-in plugin not found")

    registry = get_plugin_registry()
    plugin = registry.register(plugin_class)
    return {"status": "registered", "plugin": plugin.get_info()}


@app.delete("/api/plugins/{plugin_name}")
async def unregister_plugin(plugin_name: str):
    """Unregister a plugin."""
    registry = get_plugin_registry()
    if registry.unregister(plugin_name):
        return {"status": "unregistered", "plugin": plugin_name}
    raise HTTPException(status_code=404, detail="Plugin not found")


# ==================== ML Routing API ====================

class RoutingFeedbackRequest(BaseModel):
    """Request to submit routing feedback."""
    query: str
    predicted_tier: int
    actual_tier: int
    feedback_score: float
    conversation_id: Optional[str] = None


class PredictRoutingRequest(BaseModel):
    """Request to predict routing tier."""
    query: str


@app.post("/api/routing/predict")
async def predict_routing(request: PredictRoutingRequest):
    """Predict the optimal routing tier for a query."""
    model = get_routing_model()
    prediction = model.predict(request.query)

    return {
        "tier": prediction.tier,
        "confidence": prediction.confidence,
        "reasoning": prediction.reasoning,
        "features": prediction.features,
    }


@app.post("/api/routing/feedback")
async def submit_routing_feedback(request: RoutingFeedbackRequest):
    """Submit feedback on a routing decision to improve the model."""
    sample = collect_training_sample(
        query=request.query,
        predicted_tier=request.predicted_tier,
        actual_tier=request.actual_tier,
        feedback_score=request.feedback_score,
        conversation_id=request.conversation_id,
    )

    # Update model with this feedback
    model = get_routing_model()
    model.update_weights(sample.features, request.actual_tier)

    return {
        "status": "feedback_recorded",
        "training_samples": model.training_samples,
    }


@app.post("/api/routing/train")
async def train_routing_model():
    """Train the routing model on all collected samples."""
    result = train_model()
    return result


@app.get("/api/routing/model")
async def get_routing_model_info():
    """Get routing model information and statistics."""
    model = get_routing_model()
    store = get_training_store()

    return {
        "model": model.get_model_info(),
        "training_data": store.get_stats(),
    }


@app.get("/api/routing/training-data")
async def get_training_data(limit: int = 50):
    """Get recent training samples."""
    store = get_training_store()
    samples = store.get_samples(limit=limit)

    return {
        "samples": [
            {
                "query": s.query[:100] + "..." if len(s.query) > 100 else s.query,
                "predicted_tier": s.predicted_tier,
                "actual_tier": s.actual_tier,
                "feedback_score": s.feedback_score,
                "timestamp": s.timestamp,
            }
            for s in samples
        ],
        "total": len(store.samples),
    }


@app.post("/api/conversations/{conversation_id}/message/stream/v2")
async def send_message_stream_v2(conversation_id: str, request: SendMessageV2Request):
    """
    Send a message with Tier 2 features: multi-round debate, devil's advocate, user participation.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        try:
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Determine models to use
            models = COUNCIL_MODELS.copy()
            if request.user_response:
                yield f"data: {json.dumps({'type': 'user_participating', 'data': {'enabled': True}})}\n\n"

            # Stage 1: Collect responses
            yield f"data: {json.dumps({'type': 'stage1_start', 'data': {'models': models}})}\n\n"

            if request.user_response:
                from .council import stage1_with_user_response
                stage1_results = await stage1_with_user_response(request.content, request.user_response)
            else:
                stage1_results = await stage1_collect_responses(request.content)

            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(request.content, stage1_results)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Multi-round debate (Tier 2)
            all_rebuttals = []
            debate_rounds = []

            if request.enable_debate and DEBATE_CONFIG.get("enabled", True):
                max_rounds = request.max_debate_rounds or DEBATE_CONFIG.get("max_rounds", 3)

                for round_num in range(max_rounds):
                    # Check for consensus
                    has_consensus, top_model = check_consensus(stage2_results, label_to_model)
                    if has_consensus:
                        yield f"data: {json.dumps({'type': 'consensus_reached', 'data': {'round': round_num + 1, 'top_model': top_model}})}\n\n"
                        debate_rounds.append({
                            "round": round_num + 1,
                            "status": "consensus_reached",
                            "top_model": top_model
                        })
                        break

                    # Signal rebuttal round start
                    yield f"data: {json.dumps({'type': 'rebuttal_round_start', 'data': {'round': round_num + 1}})}\n\n"

                    # Collect rebuttals
                    rebuttals = await stage2b_collect_rebuttals(
                        request.content, stage1_results, stage2_results, label_to_model
                    )

                    if not rebuttals:
                        yield f"data: {json.dumps({'type': 'rebuttal_round_complete', 'data': {'round': round_num + 1, 'status': 'no_rebuttals'}})}\n\n"
                        debate_rounds.append({
                            "round": round_num + 1,
                            "status": "no_rebuttals"
                        })
                        break

                    all_rebuttals.extend(rebuttals)

                    # Send each rebuttal
                    for rebuttal in rebuttals:
                        yield f"data: {json.dumps({'type': 'rebuttal_complete', 'data': rebuttal})}\n\n"

                    yield f"data: {json.dumps({'type': 'rebuttal_round_complete', 'data': {'round': round_num + 1, 'rebuttal_count': len(rebuttals)}})}\n\n"
                    debate_rounds.append({
                        "round": round_num + 1,
                        "status": "rebuttals_collected",
                        "rebuttal_count": len(rebuttals)
                    })

                yield f"data: {json.dumps({'type': 'debate_complete', 'data': {'rounds': len(debate_rounds), 'total_rebuttals': len(all_rebuttals)}})}\n\n"

            # Devil's advocate (Tier 2)
            devils_advocate = None
            if aggregate_rankings:
                yield f"data: {json.dumps({'type': 'devils_advocate_start'})}\n\n"

                top_model = aggregate_rankings[0]["model"]
                top_response = next(
                    (r for r in stage1_results if r["model"] == top_model),
                    stage1_results[0]
                )
                devils_advocate = await stage2_devils_advocate(
                    request.content, top_response, aggregate_rankings
                )

                if devils_advocate:
                    yield f"data: {json.dumps({'type': 'devils_advocate_complete', 'data': devils_advocate})}\n\n"

            # Stage 3: Synthesize final answer with all context
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(
                request.content, stage1_results, stage2_results,
                all_rebuttals, devils_advocate
            )
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Calculate user rank if they participated
            user_rank_info = None
            if request.user_response:
                from .config import USER_PARTICIPATION_CONFIG
                user_label = USER_PARTICIPATION_CONFIG.get("user_label", "User")
                user_ranking = next(
                    (r for r in aggregate_rankings if r["model"] == user_label),
                    None
                )
                if user_ranking:
                    user_rank_info = {
                        "rank": aggregate_rankings.index(user_ranking) + 1,
                        "average_rank": user_ranking["average_rank"],
                        "total_participants": len(aggregate_rankings)
                    }
                    yield f"data: {json.dumps({'type': 'user_rank', 'data': user_rank_info})}\n\n"

            # Save complete assistant message (extended format)
            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result,
                rebuttals=all_rebuttals,
                devils_advocate=devils_advocate,
                debate_rounds=debate_rounds
            )

            # Send completion event with full metadata
            yield f"data: {json.dumps({'type': 'complete', 'metadata': {'debate_rounds': len(debate_rounds), 'total_rebuttals': len(all_rebuttals), 'devils_advocate_included': devils_advocate is not None, 'user_participated': request.user_response is not None, 'user_rank': user_rank_info}})}\n\n"

        except Exception as e:
            import traceback
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'traceback': traceback.format_exc()})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# =============================================================================
# Tier 4: Predictions API
# =============================================================================

class PlacePredictionRequest(BaseModel):
    """Request to place a prediction."""
    user_id: str
    predicted_winner: str
    confidence: float = 0.5


class ResolvePredictionRequest(BaseModel):
    """Request to resolve predictions."""
    actual_winner: str


class VoteRequest(BaseModel):
    """Request to vote on an amendment."""
    voter_id: str
    vote: bool
    reason: Optional[str] = None


class ProposeAmendmentRequest(BaseModel):
    """Request to propose an amendment."""
    amendment_type: str  # 'add', 'modify', 'remove'
    reason: str
    proposed_by: str
    target_article_id: Optional[str] = None
    proposed_text: Optional[str] = None
    proposed_title: Optional[str] = None
    voting_days: int = 7


@app.post("/api/predictions/{conversation_id}")
async def api_place_prediction(conversation_id: str, request: PlacePredictionRequest):
    """Place a prediction on which model will win the council debate."""
    try:
        prediction = place_prediction(
            user_id=request.user_id,
            conversation_id=conversation_id,
            predicted_winner=request.predicted_winner,
            confidence=request.confidence
        )
        return {
            "id": prediction.id,
            "user_id": prediction.user_id,
            "conversation_id": prediction.conversation_id,
            "predicted_winner": prediction.predicted_winner,
            "confidence": prediction.confidence,
            "placed_at": prediction.placed_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/predictions/{conversation_id}/resolve")
async def api_resolve_predictions(conversation_id: str, request: ResolvePredictionRequest):
    """Resolve all predictions for a conversation."""
    from .predictions.betting import resolve_conversation_predictions
    resolved = resolve_conversation_predictions(conversation_id, request.actual_winner)

    # Update Elo ratings
    if resolved:
        loser_ids = list(set(
            p.predicted_winner for p in resolved if not p.correct
        ))
        if loser_ids:
            elo_updates = update_elo_ratings(
                request.actual_winner, loser_ids, conversation_id
            )
            return {
                "resolved_count": len(resolved),
                "elo_updates": elo_updates
            }

    return {"resolved_count": len(resolved)}


@app.get("/api/predictions/user/{user_id}")
async def api_get_user_predictions(user_id: str):
    """Get all predictions for a user."""
    predictions = get_user_predictions(user_id)
    from .predictions.betting import get_user_prediction_stats
    stats = get_user_prediction_stats(user_id)
    return {
        "predictions": predictions,
        "stats": stats
    }


@app.get("/api/leaderboard")
async def api_get_leaderboard(
    type: str = "elo",
    limit: int = 20,
    time_period: str = "all"
):
    """Get leaderboard data."""
    return get_leaderboard(type, limit, time_period)


@app.get("/api/leaderboard/model/{model_id}")
async def api_get_model_stats(model_id: str):
    """Get comprehensive stats for a model."""
    return get_model_stats(model_id)


@app.get("/api/predictions/summary")
async def api_get_market_summary():
    """Get prediction market summary."""
    return get_prediction_market_summary()


# =============================================================================
# Tier 4: Constitution API
# =============================================================================

@app.get("/api/constitution")
async def api_get_constitution():
    """Get the current constitution."""
    return get_constitution()


@app.get("/api/constitution/formatted")
async def api_get_formatted_constitution(priority_filter: str = None):
    """Get the constitution formatted for display."""
    return {"text": format_constitution_for_prompt(priority_filter=priority_filter)}


@app.get("/api/constitution/article/{article_id}")
async def api_get_article(article_id: str):
    """Get a specific article."""
    article = get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@app.get("/api/constitution/history")
async def api_get_constitution_history(limit: int = 50):
    """Get constitution change history."""
    return get_constitution_history(limit)


@app.get("/api/amendments")
async def api_get_amendments():
    """Get all pending amendments."""
    return get_pending_amendments()


@app.get("/api/amendments/history")
async def api_get_amendment_history(limit: int = 50):
    """Get amendment history."""
    return get_amendment_history(limit)


@app.post("/api/amendments")
async def api_propose_amendment(request: ProposeAmendmentRequest):
    """Propose a new amendment."""
    try:
        amendment = propose_amendment(
            amendment_type=request.amendment_type,
            reason=request.reason,
            proposed_by=request.proposed_by,
            target_article_id=request.target_article_id,
            proposed_text=request.proposed_text,
            proposed_title=request.proposed_title,
            voting_days=request.voting_days
        )
        return {
            "id": amendment.id,
            "type": amendment.type,
            "status": amendment.status,
            "voting_deadline": amendment.voting_deadline
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/amendments/{amendment_id}/vote")
async def api_vote_on_amendment(amendment_id: str, request: VoteRequest):
    """Vote on an amendment."""
    amendment = vote_on_amendment(
        amendment_id,
        request.voter_id,
        request.vote,
        request.reason
    )
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    return {
        "id": amendment.id,
        "votes_for": amendment.votes_for,
        "votes_against": amendment.votes_against,
        "status": amendment.status
    }


@app.post("/api/amendments/{amendment_id}/process")
async def api_process_amendment(amendment_id: str):
    """Process an amendment's voting results."""
    amendment = process_amendment_vote(amendment_id)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    return {
        "id": amendment.id,
        "status": amendment.status,
        "votes_for": amendment.votes_for,
        "votes_against": amendment.votes_against
    }


# =============================================================================
# Tier 4: Observer API
# =============================================================================

@app.post("/api/observer/analyze/{conversation_id}")
async def api_run_observer_analysis(conversation_id: str):
    """Run observer analysis on a conversation."""
    conversation = storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Extract stage data from last assistant message
    messages = conversation.get("messages", [])
    assistant_messages = [m for m in messages if m.get("role") == "assistant"]

    if not assistant_messages:
        raise HTTPException(status_code=400, detail="No assistant messages to analyze")

    last_message = assistant_messages[-1]
    stage1 = last_message.get("stage1", [])
    stage2 = last_message.get("stage2", [])
    stage3 = last_message.get("stage3", {}).get("content", "")

    # Get original query from user message
    user_messages = [m for m in messages if m.get("role") == "user"]
    query = user_messages[-1].get("content", "") if user_messages else ""

    # Run analysis
    analysis = run_meta_analysis(
        conversation_id=conversation_id,
        responses=stage1,
        rankings=stage2,
        synthesis=stage3,
        query=query
    )

    return analysis


@app.get("/api/observer/report/{conversation_id}")
async def api_get_observer_report(conversation_id: str, format: str = "full"):
    """Get observer report for a conversation."""
    conversation = storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Extract stage data
    messages = conversation.get("messages", [])
    assistant_messages = [m for m in messages if m.get("role") == "assistant"]

    if not assistant_messages:
        raise HTTPException(status_code=400, detail="No assistant messages to analyze")

    last_message = assistant_messages[-1]
    stage1 = last_message.get("stage1", [])
    stage2 = last_message.get("stage2", [])
    stage3 = last_message.get("stage3", {}).get("content", "")

    user_messages = [m for m in messages if m.get("role") == "user"]
    query = user_messages[-1].get("content", "") if user_messages else ""

    report = generate_observer_report(
        conversation_id=conversation_id,
        responses=stage1,
        rankings=stage2,
        synthesis=stage3,
        query=query,
        format=format
    )

    return report


@app.get("/api/observer/health/{conversation_id}")
async def api_get_cognitive_health(conversation_id: str):
    """Get cognitive health score for a conversation."""
    conversation = storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = conversation.get("messages", [])
    assistant_messages = [m for m in messages if m.get("role") == "assistant"]

    if not assistant_messages:
        return {"score": 0, "health_level": "unknown", "message": "No data to analyze"}

    last_message = assistant_messages[-1]
    stage1 = last_message.get("stage1", [])
    stage2 = last_message.get("stage2", [])

    user_messages = [m for m in messages if m.get("role") == "user"]
    query = user_messages[-1].get("content", "") if user_messages else ""

    return get_cognitive_health_score(stage1, stage2, query)


@app.get("/api/observer/history")
async def api_get_analysis_history(limit: int = 50):
    """Get observer analysis history."""
    return get_analysis_history(limit)


@app.get("/api/observer/statistics")
async def api_get_observer_statistics():
    """Get aggregate observer statistics."""
    return get_aggregate_statistics()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
