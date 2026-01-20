"""Inject memories into prompts for context-aware responses."""

from typing import List, Dict, Any, Optional
from .storage import Memory
from .retrieval import get_relevant_memories, get_memories_for_model


def build_memory_context(
    memories: List[Memory],
    max_length: int = 1500
) -> str:
    """
    Build a formatted context string from memories.

    Args:
        memories: List of Memory objects to include
        max_length: Maximum length of the context string

    Returns:
        Formatted context string
    """
    if not memories:
        return ""

    context_parts = []
    current_length = 0

    for memory in memories:
        # Format memory entry
        memory_entry = f"- [{memory.type.upper()}] {memory.content}"

        if memory.tags:
            memory_entry += f" (tags: {', '.join(memory.tags)})"

        entry_length = len(memory_entry)

        # Check if we'd exceed max length
        if current_length + entry_length + 1 > max_length:
            break

        context_parts.append(memory_entry)
        current_length += entry_length + 1  # +1 for newline

    return "\n".join(context_parts)


def inject_memory_into_prompt(
    base_prompt: str,
    query: str,
    context: Dict[str, Any] = None,
    max_memories: int = 5
) -> str:
    """
    Inject relevant memories into a prompt.

    Args:
        base_prompt: The original prompt
        query: The user's query (used for memory retrieval)
        context: Optional context for better memory selection
        max_memories: Maximum number of memories to inject

    Returns:
        Enhanced prompt with memory context
    """
    # Get relevant memories
    memories = get_relevant_memories(query, context, limit=max_memories)

    if not memories:
        return base_prompt

    # Build memory context
    memory_context = build_memory_context(memories)

    # Create the enhanced prompt
    memory_section = f"""
RELEVANT COUNCIL MEMORIES:
The following memories from previous council sessions may be relevant:

{memory_context}

Consider these memories when formulating your response, but prioritize the current question.

---

"""

    # Insert memory section at the beginning of the prompt
    enhanced_prompt = memory_section + base_prompt

    return enhanced_prompt


def inject_model_memories(
    base_prompt: str,
    model_id: str,
    query: str,
    max_memories: int = 3
) -> str:
    """
    Inject memories specific to a model into their prompt.

    Args:
        base_prompt: The original prompt
        model_id: The model receiving the prompt
        query: The user's query
        max_memories: Maximum memories to inject

    Returns:
        Enhanced prompt with model-specific memories
    """
    # Get model-specific memories
    model_memories = get_memories_for_model(model_id, limit=max_memories)

    # Also get query-relevant memories
    query_memories = get_relevant_memories(query, limit=max_memories)

    # Combine and deduplicate
    all_memory_ids = set()
    combined_memories = []

    for memory in model_memories + query_memories:
        if memory.id not in all_memory_ids:
            all_memory_ids.add(memory.id)
            combined_memories.append(memory)
            if len(combined_memories) >= max_memories:
                break

    if not combined_memories:
        return base_prompt

    memory_context = build_memory_context(combined_memories)

    memory_section = f"""
RELEVANT CONTEXT FROM PREVIOUS SESSIONS:
{memory_context}

---

"""

    return memory_section + base_prompt


def create_memory_aware_ranking_prompt(
    base_ranking_prompt: str,
    query: str,
    responses: List[Dict[str, Any]]
) -> str:
    """
    Create a ranking prompt that considers past council decisions.

    Args:
        base_ranking_prompt: The original ranking prompt
        query: The user's query
        responses: The responses being ranked

    Returns:
        Memory-enhanced ranking prompt
    """
    # Get memories related to past rankings and decisions
    memories = get_relevant_memories(
        query,
        context={'topic': 'ranking'},
        limit=3
    )

    if not memories:
        return base_ranking_prompt

    memory_context = build_memory_context(memories)

    memory_note = f"""
NOTE: The council has relevant experience with similar topics:
{memory_context}

Consider this context when evaluating the responses, but judge each response on its own merits.

"""

    # Insert after the responses but before the ranking instructions
    if "Your task:" in base_ranking_prompt:
        parts = base_ranking_prompt.split("Your task:")
        return parts[0] + memory_note + "Your task:" + parts[1]

    return base_ranking_prompt + "\n" + memory_note


def get_synthesis_memories(query: str, limit: int = 3) -> str:
    """
    Get memories formatted for the chairman's synthesis stage.

    Args:
        query: The user's query
        limit: Maximum memories

    Returns:
        Formatted memory context for synthesis
    """
    memories = get_relevant_memories(
        query,
        context={'topic': 'synthesis', 'type': 'decision'},
        limit=limit
    )

    if not memories:
        return ""

    memory_context = build_memory_context(memories)

    return f"""
COUNCIL MEMORY BANK:
Past decisions and insights that may inform your synthesis:
{memory_context}

"""
