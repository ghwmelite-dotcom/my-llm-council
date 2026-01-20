"""Extract memories from council conversations."""

from typing import List, Dict, Any, Optional
from .storage import Memory, get_memory_store
from ..openrouter import query_model
import re


async def extract_memories_from_conversation(
    conversation_id: str,
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    stage3_result: Dict[str, Any],
    aggregate_rankings: List[Dict[str, Any]] = None
) -> List[Memory]:
    """
    Extract memorable insights from a council conversation.

    Args:
        conversation_id: The conversation ID
        user_query: The original user query
        stage1_results: Individual model responses
        stage2_results: Model rankings
        stage3_result: Chairman's synthesis
        aggregate_rankings: Aggregate ranking results

    Returns:
        List of extracted Memory objects
    """
    store = get_memory_store()
    extracted_memories = []

    # Extract key facts from the final synthesis
    fact_memory = await extract_fact_memory(
        user_query, stage3_result, conversation_id
    )
    if fact_memory:
        extracted_memories.append(fact_memory)

    # Extract decision patterns from rankings
    decision_memory = extract_decision_memory(
        user_query, aggregate_rankings, conversation_id
    )
    if decision_memory:
        extracted_memories.append(decision_memory)

    # Extract any notable disagreements or consensus
    insight_memory = extract_insight_memory(
        user_query, stage1_results, stage2_results, conversation_id
    )
    if insight_memory:
        extracted_memories.append(insight_memory)

    return extracted_memories


async def extract_fact_memory(
    user_query: str,
    stage3_result: Dict[str, Any],
    conversation_id: str
) -> Optional[Memory]:
    """
    Extract key facts from the chairman's synthesis.

    Args:
        user_query: The original query
        stage3_result: The synthesis result
        conversation_id: Source conversation ID

    Returns:
        A fact Memory or None
    """
    synthesis = stage3_result.get('response', '')

    if len(synthesis) < 100:
        return None

    # Use a model to extract key facts (simplified - could be more sophisticated)
    extraction_prompt = f"""Given this council synthesis, extract ONE key fact or conclusion that would be worth remembering for future similar questions.

Query: {user_query}

Synthesis:
{synthesis[:1500]}

Respond with a single sentence summarizing the key takeaway. If nothing notable, respond with "NONE"."""

    try:
        response = await query_model(
            "google/gemini-2.5-flash",
            [{"role": "user", "content": extraction_prompt}],
            timeout=30.0
        )

        if response and response.get('content'):
            content = response['content'].strip()
            if content.upper() != "NONE" and len(content) > 10:
                store = get_memory_store()
                return store.add_memory(
                    content=content,
                    memory_type='fact',
                    related_models=[stage3_result.get('model', '')],
                    tags=extract_tags_from_query(user_query),
                    source_conversation=conversation_id,
                    importance=0.6
                )
    except Exception as e:
        print(f"Error extracting fact memory: {e}")

    return None


def extract_decision_memory(
    user_query: str,
    aggregate_rankings: List[Dict[str, Any]],
    conversation_id: str
) -> Optional[Memory]:
    """
    Extract decision patterns from the rankings.

    Args:
        user_query: The original query
        aggregate_rankings: The aggregate rankings
        conversation_id: Source conversation ID

    Returns:
        A decision Memory or None
    """
    if not aggregate_rankings or len(aggregate_rankings) < 2:
        return None

    # Check for clear winner (low average rank)
    top_model = aggregate_rankings[0]
    if top_model['average_rank'] <= 1.5 and top_model['rankings_count'] >= 3:
        store = get_memory_store()
        content = f"For questions about '{extract_topic(user_query)}', {top_model['model'].split('/')[-1]} provided the best response (avg rank: {top_model['average_rank']:.2f})"

        return store.add_memory(
            content=content,
            memory_type='decision',
            related_models=[top_model['model']],
            tags=extract_tags_from_query(user_query),
            source_conversation=conversation_id,
            importance=0.5
        )

    return None


def extract_insight_memory(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    conversation_id: str
) -> Optional[Memory]:
    """
    Extract insights about model agreement/disagreement.

    Args:
        user_query: The original query
        stage1_results: Individual responses
        stage2_results: Rankings
        conversation_id: Source conversation ID

    Returns:
        An insight Memory or None
    """
    # Analyze ranking consistency
    if not stage2_results:
        return None

    # Extract all first choices
    first_choices = []
    for ranking in stage2_results:
        parsed = ranking.get('parsed_ranking', [])
        if parsed:
            first_choices.append(parsed[0])

    if not first_choices:
        return None

    # Check for consensus
    unique_choices = set(first_choices)
    if len(unique_choices) == 1:
        # Perfect consensus
        store = get_memory_store()
        content = f"The council reached unanimous consensus on '{extract_topic(user_query)}'"

        return store.add_memory(
            content=content,
            memory_type='insight',
            related_models=[r['model'] for r in stage1_results],
            tags=['consensus'] + extract_tags_from_query(user_query),
            source_conversation=conversation_id,
            importance=0.7
        )
    elif len(unique_choices) == len(first_choices):
        # Complete disagreement
        store = get_memory_store()
        content = f"The council showed significant disagreement on '{extract_topic(user_query)}' - each model had different top picks"

        return store.add_memory(
            content=content,
            memory_type='insight',
            related_models=[r['model'] for r in stage1_results],
            tags=['disagreement'] + extract_tags_from_query(user_query),
            source_conversation=conversation_id,
            importance=0.6
        )

    return None


def extract_tags_from_query(query: str) -> List[str]:
    """
    Extract topic tags from a query.

    Args:
        query: The user's query

    Returns:
        List of tag strings
    """
    # Simple keyword extraction
    # Could be enhanced with NLP
    stopwords = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why',
        'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should',
        'do', 'does', 'did', 'have', 'has', 'had', 'be', 'been', 'being',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'or',
        'and', 'but', 'if', 'then', 'than', 'that', 'this', 'it', 'its',
        'i', 'me', 'my', 'you', 'your', 'we', 'our', 'they', 'their'
    }

    words = re.findall(r'\b[a-zA-Z]+\b', query.lower())
    tags = [w for w in words if w not in stopwords and len(w) > 2]

    # Return unique tags, limited to 5
    unique_tags = list(dict.fromkeys(tags))
    return unique_tags[:5]


def extract_topic(query: str) -> str:
    """
    Extract a short topic description from a query.

    Args:
        query: The user's query

    Returns:
        A short topic string
    """
    # Take first 50 chars or first sentence
    topic = query[:50]
    if '?' in topic:
        topic = topic.split('?')[0]
    if '.' in topic:
        topic = topic.split('.')[0]

    return topic.strip()


async def summarize_conversation_for_memory(
    user_query: str,
    stage3_result: Dict[str, Any]
) -> Optional[str]:
    """
    Create a summary of the conversation suitable for memory storage.

    Args:
        user_query: The original query
        stage3_result: The synthesis result

    Returns:
        A summary string or None
    """
    synthesis = stage3_result.get('response', '')

    if len(synthesis) < 50:
        return None

    summary_prompt = f"""Summarize this council discussion in 1-2 sentences that capture the key conclusion:

Question: {user_query}

Council's Answer:
{synthesis[:1000]}

Summary:"""

    try:
        response = await query_model(
            "google/gemini-2.5-flash",
            [{"role": "user", "content": summary_prompt}],
            timeout=30.0
        )

        if response and response.get('content'):
            return response['content'].strip()
    except Exception as e:
        print(f"Error summarizing conversation: {e}")

    return None
