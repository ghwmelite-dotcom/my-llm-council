"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException
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
    stage2_collect_rankings, stage3_synthesize_final,
    calculate_aggregate_rankings, stage2b_collect_rebuttals,
    stage2_devils_advocate, check_consensus
)
from .config import COUNCIL_MODELS, DEBATE_CONFIG

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

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str


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
    return {
        "models": COUNCIL_MODELS,
        "debate_enabled": DEBATE_CONFIG.get("enabled", True),
        "max_debate_rounds": DEBATE_CONFIG.get("max_rounds", 3),
        "consensus_threshold": DEBATE_CONFIG.get("consensus_threshold", 0.8),
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
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Stage 1: Collect responses
            yield f"data: {json.dumps({'type': 'stage1_start', 'data': {'models': COUNCIL_MODELS}})}\n\n"
            stage1_results = await stage1_collect_responses(request.content)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(request.content, stage1_results)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3: Synthesize final answer
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(request.content, stage1_results, stage2_results)
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
