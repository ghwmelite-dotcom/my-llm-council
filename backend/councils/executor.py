"""Execute specialized council sessions."""

from typing import Dict, List, Any, Optional, Tuple
from .definitions import Council, get_council, get_default_council
from .router import route_query
from ..openrouter import query_models_parallel, query_model
from ..council import (
    parse_ranking_from_text,
    calculate_aggregate_rankings
)


async def run_specialized_council(
    query: str,
    council: Council = None,
    is_appeal: bool = False
) -> Dict[str, Any]:
    """
    Run a complete specialized council session.

    Args:
        query: The user's query
        council: Optional specific council to use (auto-routes if None)
        is_appeal: Whether this is an appeal (changes some behavior)

    Returns:
        Dict with stage1, stage2, stage3 results and metadata
    """
    # Route to council if not specified
    routing_info = {}
    confidence = 1.0

    if council is None:
        council, confidence, routing_info = route_query(query)

    # Stage 1: Collect responses from council models
    stage1_results = await collect_council_responses(query, council)

    if not stage1_results:
        return {
            'stage1': [],
            'stage2': [],
            'stage3': {
                'model': 'error',
                'response': 'All council models failed to respond.'
            },
            'metadata': {
                'council': council.id,
                'routing': routing_info
            }
        }

    # Stage 2: Collect rankings
    stage2_results, label_to_model = await collect_council_rankings(
        query, stage1_results, council
    )

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Stage 3: Chairman synthesis
    stage3_result = await synthesize_council_response(
        query, stage1_results, stage2_results, council, is_appeal
    )

    return {
        'stage1': stage1_results,
        'stage2': stage2_results,
        'stage3': stage3_result,
        'metadata': {
            'council': council.id,
            'council_name': council.name,
            'routing': routing_info,
            'routing_confidence': confidence,
            'label_to_model': label_to_model,
            'aggregate_rankings': aggregate_rankings,
            'model_count': len(council.models)
        }
    }


async def collect_council_responses(
    query: str,
    council: Council
) -> List[Dict[str, Any]]:
    """
    Collect responses from all council members.

    Args:
        query: The user's query
        council: The council to use

    Returns:
        List of model responses
    """
    messages = [{"role": "user", "content": query}]

    # Query all council models in parallel
    responses = await query_models_parallel(council.models, messages)

    # Format results
    results = []
    for model, response in responses.items():
        if response is not None:
            results.append({
                'model': model,
                'response': response.get('content', '')
            })

    return results


async def collect_council_rankings(
    query: str,
    stage1_results: List[Dict[str, Any]],
    council: Council
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Collect rankings from council members.

    Args:
        query: The original query
        stage1_results: The stage 1 responses
        council: The council to use

    Returns:
        Tuple of (rankings list, label_to_model mapping)
    """
    # Create anonymized labels
    labels = [chr(65 + i) for i in range(len(stage1_results))]

    label_to_model = {
        f"Response {label}": result['model']
        for label, result in zip(labels, stage1_results)
    }

    # Build ranking prompt
    responses_text = "\n\n".join([
        f"Response {label}:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    ranking_prompt = f"""You are a member of the {council.name}.
{council.description}

You are evaluating different responses to the following question:

Question: {query}

Here are the responses (anonymized):

{responses_text}

Your task:
1. Evaluate each response based on the criteria relevant to {council.name}
2. Provide a final ranking from best to worst

IMPORTANT: End your response with:
FINAL RANKING:
1. Response X
2. Response Y
(etc.)

Provide your evaluation:"""

    messages = [{"role": "user", "content": ranking_prompt}]

    # Get rankings from council models
    responses = await query_models_parallel(council.models, messages)

    # Format results
    results = []
    for model, response in responses.items():
        if response is not None:
            full_text = response.get('content', '')
            parsed = parse_ranking_from_text(full_text)
            results.append({
                'model': model,
                'ranking': full_text,
                'parsed_ranking': parsed
            })

    return results, label_to_model


async def synthesize_council_response(
    query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    council: Council,
    is_appeal: bool = False
) -> Dict[str, Any]:
    """
    Have the council chairman synthesize the final response.

    Args:
        query: The original query
        stage1_results: Individual responses
        stage2_results: Rankings
        council: The council
        is_appeal: Whether this is an appeal

    Returns:
        Chairman's synthesis
    """
    # Build context
    stage1_text = "\n\n".join([
        f"Model: {r['model']}\nResponse: {r['response']}"
        for r in stage1_results
    ])

    stage2_text = "\n\n".join([
        f"Model: {r['model']}\nRanking: {r['ranking']}"
        for r in stage2_results
    ])

    role_context = ""
    if is_appeal:
        role_context = """
You are reviewing an APPEAL. Your decision is final and binding.
Consider all evidence carefully before rendering your judgment.
"""

    chairman_prompt = f"""You are the Chairman of the {council.name}.
{council.description}
{role_context}

Original Question: {query}

STAGE 1 - Council Member Responses:
{stage1_text}

STAGE 2 - Peer Rankings:
{stage2_text}

As Chairman, synthesize the council's collective wisdom into a final, authoritative answer.
Consider the individual responses, their rankings, and any patterns of agreement or disagreement.

Provide the council's official response:"""

    messages = [{"role": "user", "content": chairman_prompt}]

    response = await query_model(council.chairman, messages)

    if response is None:
        return {
            'model': council.chairman,
            'response': 'Error: Chairman failed to synthesize response.'
        }

    return {
        'model': council.chairman,
        'response': response.get('content', '')
    }


async def quick_council_query(
    query: str,
    council_id: str = None
) -> str:
    """
    Quick single-response query to a council (skips ranking).

    Args:
        query: The user's query
        council_id: Optional specific council

    Returns:
        The council's response string
    """
    if council_id:
        council = get_council(council_id) or get_default_council()
    else:
        council, _, _ = route_query(query)

    # Just query the chairman directly for speed
    messages = [{"role": "user", "content": query}]
    response = await query_model(council.chairman, messages)

    if response:
        return response.get('content', '')

    return "Unable to get response from council."
