"""3-stage LLM Council orchestration with Tier 2 debate functionality."""

from typing import List, Dict, Any, Tuple, Optional, AsyncGenerator
from .openrouter import query_models_parallel, query_model, query_model_stream
from .config import (
    COUNCIL_MODELS, CHAIRMAN_MODEL, DEBATE_CONFIG,
    DEVILS_ADVOCATE_CONFIG, USER_PARTICIPATION_CONFIG
)
from .multimodal import prepare_multimodal_messages
import re


async def stage1_collect_responses(
    user_query: str,
    image_ids: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Stage 1: Collect individual responses from all council models.

    Args:
        user_query: The user's question
        image_ids: Optional list of image IDs for multimodal queries

    Returns:
        Tuple of (results list, usage list)
        - results: List of dicts with 'model' and 'response' keys
        - usage: List of dicts with 'model', 'input_tokens', 'output_tokens'
    """
    base_messages = [{"role": "user", "content": user_query}]

    # Query all models in parallel with multimodal support
    responses = await query_models_parallel(COUNCIL_MODELS, base_messages, image_ids=image_ids)

    # Format results and collect usage
    stage1_results = []
    usage_data = []
    for model, response in responses.items():
        if response is not None:  # Only include successful responses
            stage1_results.append({
                "model": model,
                "response": response.get('content', '')
            })
            # Collect usage data
            usage = response.get('usage', {})
            if usage:
                usage_data.append({
                    "model": model,
                    "input_tokens": usage.get('input_tokens', 0),
                    "output_tokens": usage.get('output_tokens', 0),
                })

    return stage1_results, usage_data


async def stage1_with_user_response(
    user_query: str,
    user_response: str
) -> List[Dict[str, Any]]:
    """
    Stage 1 variant: Include user's own answer alongside AI models.

    Args:
        user_query: The user's question
        user_response: The user's own answer to include

    Returns:
        List of dicts with 'model' and 'response' keys (user included)
    """
    # Get AI responses
    ai_responses = await stage1_collect_responses(user_query)

    # Add user response
    ai_responses.append({
        "model": USER_PARTICIPATION_CONFIG.get("user_label", "User"),
        "response": user_response,
        "is_user": True
    })

    return ai_responses


async def stage1_single_model(
    user_query: str,
    model: str,
    image_ids: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Stage 1 variant: Query only a single model for simple queries.

    Args:
        user_query: The user's question
        model: The model identifier to query
        image_ids: Optional list of image IDs for multimodal queries

    Returns:
        Tuple of (results list, usage list)
    """
    base_messages = [{"role": "user", "content": user_query}]
    if image_ids:
        messages = prepare_multimodal_messages(base_messages, image_ids, model)
    else:
        messages = base_messages
    response = await query_model(model, messages)

    if response is not None:
        usage = response.get('usage', {})
        usage_data = []
        if usage:
            usage_data.append({
                "model": model,
                "input_tokens": usage.get('input_tokens', 0),
                "output_tokens": usage.get('output_tokens', 0),
            })
        return [{
            "model": model,
            "response": response.get('content', '')
        }], usage_data

    return [], []


async def stage1_mini_council(
    user_query: str,
    models: List[str],
    image_ids: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Stage 1 variant: Query a subset of models (mini council).

    Args:
        user_query: The user's question
        models: List of model identifiers to query
        image_ids: Optional list of image IDs for multimodal queries

    Returns:
        Tuple of (results list, usage list)
    """
    messages = [{"role": "user", "content": user_query}]

    # Query selected models in parallel with multimodal support
    responses = await query_models_parallel(models, messages, image_ids=image_ids)

    # Format results and collect usage
    stage1_results = []
    usage_data = []
    for model, response in responses.items():
        if response is not None:
            stage1_results.append({
                "model": model,
                "response": response.get('content', '')
            })
            usage = response.get('usage', {})
            if usage:
                usage_data.append({
                    "model": model,
                    "input_tokens": usage.get('input_tokens', 0),
                    "output_tokens": usage.get('output_tokens', 0),
                })

    return stage1_results, usage_data


async def stage2_collect_rankings(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    verification_context: str = ""
) -> Tuple[List[Dict[str, Any]], Dict[str, str], List[Dict[str, Any]]]:
    """
    Stage 2: Each model ranks the anonymized responses.

    Args:
        user_query: The original user query
        stage1_results: Results from Stage 1
        verification_context: Optional verification context from Stage 1.5

    Returns:
        Tuple of (rankings list, label_to_model mapping, usage list)
    """
    # Create anonymized labels for responses (Response A, Response B, etc.)
    labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, ...

    # Create mapping from label to model name
    label_to_model = {
        f"Response {label}": result['model']
        for label, result in zip(labels, stage1_results)
    }

    # Build the ranking prompt
    responses_text = "\n\n".join([
        f"Response {label}:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    ranking_prompt = f"""You are evaluating different responses to the following question:

Question: {user_query}

Here are the responses from different models (anonymized):

{responses_text}

Your task:
1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Example of the correct format for your ENTIRE response:

Response A provides good detail on X but misses Y...
Response B is accurate but lacks depth on Z...
Response C offers the most comprehensive answer...

FINAL RANKING:
1. Response C
2. Response A
3. Response B
{verification_context}
Now provide your evaluation and ranking:"""

    messages = [{"role": "user", "content": ranking_prompt}]

    # Get rankings from all council models in parallel
    responses = await query_models_parallel(COUNCIL_MODELS, messages)

    # Format results and collect usage
    stage2_results = []
    usage_data = []
    for model, response in responses.items():
        if response is not None:
            full_text = response.get('content', '')
            parsed = parse_ranking_from_text(full_text)
            stage2_results.append({
                "model": model,
                "ranking": full_text,
                "parsed_ranking": parsed
            })
            usage = response.get('usage', {})
            if usage:
                usage_data.append({
                    "model": model,
                    "input_tokens": usage.get('input_tokens', 0),
                    "output_tokens": usage.get('output_tokens', 0),
                })

    return stage2_results, label_to_model, usage_data


def extract_critiques_for_model(
    model: str,
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, str]]:
    """
    Extract critiques directed at a specific model from Stage 2 rankings.

    Args:
        model: The model to extract critiques for
        stage2_results: Rankings from Stage 2
        label_to_model: Mapping from labels to model names

    Returns:
        List of critiques with 'from_model' and 'critique' keys
    """
    # Find the label for this model
    model_label = None
    for label, m in label_to_model.items():
        if m == model:
            model_label = label.replace("Response ", "")
            break

    if not model_label:
        return []

    critiques = []
    for ranking in stage2_results:
        if ranking['model'] == model:
            continue  # Skip self-evaluation

        ranking_text = ranking['ranking']

        # Look for critique sections mentioning this response
        # Pattern: "Response X..." followed by critique text
        pattern = rf"Response {model_label}[:\s]+(.*?)(?=Response [A-Z]|FINAL RANKING:|$)"
        matches = re.findall(pattern, ranking_text, re.DOTALL | re.IGNORECASE)

        for match in matches:
            critique = match.strip()
            # Only include substantive critiques
            if len(critique) >= DEBATE_CONFIG.get("min_critique_length", 50):
                critiques.append({
                    "from_model": ranking['model'],
                    "critique": critique
                })

    return critiques


def generate_rebuttal_prompt(
    model: str,
    original_response: str,
    critiques: List[Dict[str, str]],
    user_query: str
) -> str:
    """
    Generate a prompt for a model to rebut critiques of their response.

    Args:
        model: The model being asked to rebut
        original_response: The model's original response
        critiques: List of critiques from other models
        user_query: The original user query

    Returns:
        Rebuttal prompt string
    """
    critiques_text = "\n\n".join([
        f"Critique from {c['from_model'].split('/')[-1]}:\n{c['critique']}"
        for c in critiques
    ])

    return f"""You previously provided the following response to a question:

Original Question: {user_query}

Your Response:
{original_response}

Other council members have provided the following critiques of your response:

{critiques_text}

Please respond to these critiques. You may:
1. Defend your original position with additional evidence or reasoning
2. Acknowledge valid points and refine your answer
3. Clarify any misunderstandings

Keep your rebuttal focused and concise. Do not completely rewrite your answer - just address the specific critiques."""


async def stage2b_collect_rebuttals(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Stage 2B: Collect rebuttals from models whose responses were criticized.

    Args:
        user_query: The original user query
        stage1_results: Original responses from Stage 1
        stage2_results: Rankings from Stage 2
        label_to_model: Mapping from labels to model names

    Returns:
        List of rebuttals with model and rebuttal text
    """
    rebuttals = []

    # For each model, extract critiques and request rebuttal
    for result in stage1_results:
        model = result['model']
        original_response = result['response']

        # Skip user responses
        if result.get('is_user'):
            continue

        critiques = extract_critiques_for_model(model, stage2_results, label_to_model)

        # Only request rebuttal if there are critiques
        if critiques:
            prompt = generate_rebuttal_prompt(
                model, original_response, critiques, user_query
            )
            messages = [{"role": "user", "content": prompt}]

            response = await query_model(model, messages)

            if response:
                rebuttals.append({
                    "model": model,
                    "critiques_addressed": len(critiques),
                    "rebuttal": response.get('content', '')
                })

    return rebuttals


def check_consensus(
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> Tuple[bool, Optional[str]]:
    """
    Check if there's consensus among the rankings.

    Args:
        stage2_results: Rankings from Stage 2
        label_to_model: Mapping from labels to model names

    Returns:
        Tuple of (has_consensus, top_model_if_consensus)
    """
    threshold = DEBATE_CONFIG.get("consensus_threshold", 0.8)

    # Count how many times each model is ranked first
    first_place_counts = {}
    total_rankings = 0

    for ranking in stage2_results:
        parsed = ranking.get('parsed_ranking', [])
        if parsed:
            first_choice = parsed[0]
            if first_choice in label_to_model:
                model = label_to_model[first_choice]
                first_place_counts[model] = first_place_counts.get(model, 0) + 1
                total_rankings += 1

    if total_rankings == 0:
        return False, None

    # Check if any model has consensus
    for model, count in first_place_counts.items():
        if count / total_rankings >= threshold:
            return True, model

    return False, None


async def stage2_devils_advocate(
    user_query: str,
    top_response: Dict[str, Any],
    aggregate_rankings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Devil's advocate challenges the top-ranked response.

    Args:
        user_query: The original user query
        top_response: The top-ranked response from Stage 1
        aggregate_rankings: Aggregate rankings from Stage 2

    Returns:
        Devil's advocate challenge
    """
    if not DEVILS_ADVOCATE_CONFIG.get("enabled", True):
        return None

    advocate_model = DEVILS_ADVOCATE_CONFIG.get("model", "anthropic/claude-sonnet-4.5")

    challenge_prompt = f"""You are playing Devil's Advocate. Your job is to challenge the top-ranked response to the following question, even if you might personally agree with it.

Original Question: {user_query}

Top-Ranked Response (from {top_response['model']}):
{top_response['response']}

This response received an average ranking of {aggregate_rankings[0]['average_rank']:.2f} from the council.

Your task:
1. Identify potential weaknesses, blind spots, or assumptions in this response
2. Present counterarguments or alternative perspectives
3. Highlight any edge cases where this answer might fail
4. Question any unsupported claims

Be rigorous but fair. The goal is to stress-test the response, not to be contrarian for its own sake."""

    messages = [{"role": "user", "content": challenge_prompt}]

    response = await query_model(advocate_model, messages)

    if response:
        return {
            "model": advocate_model,
            "role": "devils_advocate",
            "challenge": response.get('content', ''),
            "target_model": top_response['model']
        }

    return None


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    rebuttals: Optional[List[Dict[str, Any]]] = None,
    devils_advocate: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Stage 3: Chairman synthesizes final response.

    Args:
        user_query: The original user query
        stage1_results: Individual model responses from Stage 1
        stage2_results: Rankings from Stage 2
        rebuttals: Optional rebuttals from Stage 2B
        devils_advocate: Optional devil's advocate challenge

    Returns:
        Tuple of (result dict, usage list)
        - result: Dict with 'model' and 'response' keys
        - usage: List of usage dicts
    """
    # Build comprehensive context for chairman
    stage1_text = "\n\n".join([
        f"Model: {result['model']}\nResponse: {result['response']}"
        for result in stage1_results
    ])

    stage2_text = "\n\n".join([
        f"Model: {result['model']}\nRanking: {result['ranking']}"
        for result in stage2_results
    ])

    # Include rebuttals if available
    rebuttals_text = ""
    if rebuttals:
        rebuttals_text = "\n\nREBUTTALS:\n" + "\n\n".join([
            f"Model: {r['model']}\nRebuttal: {r['rebuttal']}"
            for r in rebuttals
        ])

    # Include devil's advocate if available
    devils_text = ""
    if devils_advocate:
        devils_text = f"\n\nDEVIL'S ADVOCATE CHALLENGE:\n{devils_advocate['challenge']}"

    chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: {user_query}

STAGE 1 - Individual Responses:
{stage1_text}

STAGE 2 - Peer Rankings:
{stage2_text}
{rebuttals_text}
{devils_text}

Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality
- Any rebuttals and how they affect the strength of arguments
- The devil's advocate challenge and whether the concerns are valid
- Any patterns of agreement or disagreement

Provide a clear, well-reasoned final answer that represents the council's collective wisdom:"""

    messages = [{"role": "user", "content": chairman_prompt}]

    # Query the chairman model
    response = await query_model(CHAIRMAN_MODEL, messages)

    usage_data = []
    if response is None:
        # Fallback if chairman fails
        return {
            "model": CHAIRMAN_MODEL,
            "response": "Error: Unable to generate final synthesis."
        }, usage_data

    # Collect usage data
    usage = response.get('usage', {})
    if usage:
        usage_data.append({
            "model": CHAIRMAN_MODEL,
            "input_tokens": usage.get('input_tokens', 0),
            "output_tokens": usage.get('output_tokens', 0),
        })

    return {
        "model": CHAIRMAN_MODEL,
        "response": response.get('content', '')
    }, usage_data


async def stage3_synthesize_stream(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    rebuttals: Optional[List[Dict[str, Any]]] = None,
    devils_advocate: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stage 3: Chairman synthesizes final response with streaming output.

    Args:
        user_query: The original user query
        stage1_results: Individual model responses from Stage 1
        stage2_results: Rankings from Stage 2
        rebuttals: Optional rebuttals from Stage 2B
        devils_advocate: Optional devil's advocate challenge

    Yields:
        Dict with 'type' ('token' or 'complete') and content
    """
    # Build comprehensive context for chairman (same as non-streaming version)
    stage1_text = "\n\n".join([
        f"Model: {result['model']}\nResponse: {result['response']}"
        for result in stage1_results
    ])

    stage2_text = "\n\n".join([
        f"Model: {result['model']}\nRanking: {result['ranking']}"
        for result in stage2_results
    ])

    # Include rebuttals if available
    rebuttals_text = ""
    if rebuttals:
        rebuttals_text = "\n\nREBUTTALS:\n" + "\n\n".join([
            f"Model: {r['model']}\nRebuttal: {r['rebuttal']}"
            for r in rebuttals
        ])

    # Include devil's advocate if available
    devils_text = ""
    if devils_advocate:
        devils_text = f"\n\nDEVIL'S ADVOCATE CHALLENGE:\n{devils_advocate['challenge']}"

    chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: {user_query}

STAGE 1 - Individual Responses:
{stage1_text}

STAGE 2 - Peer Rankings:
{stage2_text}
{rebuttals_text}
{devils_text}

Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality
- Any rebuttals and how they affect the strength of arguments
- The devil's advocate challenge and whether the concerns are valid
- Any patterns of agreement or disagreement

Provide a clear, well-reasoned final answer that represents the council's collective wisdom:"""

    messages = [{"role": "user", "content": chairman_prompt}]

    # Estimate input tokens (roughly 4 characters per token)
    input_text_length = len(chairman_prompt)
    estimated_input_tokens = input_text_length // 4

    # Stream from the chairman model
    full_response = ""
    try:
        async for token in query_model_stream(CHAIRMAN_MODEL, messages):
            full_response += token
            yield {
                "type": "token",
                "token": token
            }

        # Estimate output tokens
        estimated_output_tokens = len(full_response) // 4

        # Yield the complete response at the end with usage estimate
        yield {
            "type": "complete",
            "model": CHAIRMAN_MODEL,
            "response": full_response,
            "usage": {
                "input_tokens": estimated_input_tokens,
                "output_tokens": estimated_output_tokens,
                "estimated": True,
            }
        }
    except Exception as e:
        yield {
            "type": "error",
            "error": str(e),
            "model": CHAIRMAN_MODEL,
            "response": full_response or "Error: Unable to generate final synthesis."
        }


def parse_ranking_from_text(ranking_text: str) -> List[str]:
    """
    Parse the FINAL RANKING section from the model's response.

    Args:
        ranking_text: The full text response from the model

    Returns:
        List of response labels in ranked order
    """
    # Look for "FINAL RANKING:" section
    if "FINAL RANKING:" in ranking_text:
        # Extract everything after "FINAL RANKING:"
        parts = ranking_text.split("FINAL RANKING:")
        if len(parts) >= 2:
            ranking_section = parts[1]
            # Try to extract numbered list format (e.g., "1. Response A")
            # This pattern looks for: number, period, optional space, "Response X"
            numbered_matches = re.findall(r'\d+\.\s*Response [A-Z]', ranking_section)
            if numbered_matches:
                # Extract just the "Response X" part
                return [re.search(r'Response [A-Z]', m).group() for m in numbered_matches]

            # Fallback: Extract all "Response X" patterns in order
            matches = re.findall(r'Response [A-Z]', ranking_section)
            return matches

    # Fallback: try to find any "Response X" patterns in order
    matches = re.findall(r'Response [A-Z]', ranking_text)
    return matches


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all models.

    Args:
        stage2_results: Rankings from each model
        label_to_model: Mapping from anonymous labels to model names

    Returns:
        List of dicts with model name and average rank, sorted best to worst
    """
    from collections import defaultdict

    # Track positions for each model
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        ranking_text = ranking['ranking']

        # Parse the ranking from the structured format
        parsed_ranking = parse_ranking_from_text(ranking_text)

        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_model:
                model_name = label_to_model[label]
                model_positions[model_name].append(position)

    # Calculate average position for each model
    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append({
                "model": model,
                "average_rank": round(avg_rank, 2),
                "rankings_count": len(positions)
            })

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x['average_rank'])

    return aggregate


async def generate_conversation_title(user_query: str) -> str:
    """
    Generate a short title for a conversation based on the first user message.

    Args:
        user_query: The first user message

    Returns:
        A short title (3-5 words)
    """
    title_prompt = f"""Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.

Question: {user_query}

Title:"""

    messages = [{"role": "user", "content": title_prompt}]

    # Use gemini-2.5-flash for title generation (fast and cheap)
    response = await query_model("google/gemini-2.5-flash", messages, timeout=30.0)

    if response is None:
        # Fallback to a generic title
        return "New Conversation"

    title = response.get('content', 'New Conversation').strip()

    # Clean up the title - remove quotes, limit length
    title = title.strip('"\'')

    # Truncate if too long
    if len(title) > 50:
        title = title[:47] + "..."

    return title


async def run_full_council(user_query: str) -> Tuple[List, List, Dict, Dict]:
    """
    Run the complete 3-stage council process.

    Args:
        user_query: The user's question

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata)
    """
    # Stage 1: Collect individual responses
    stage1_results, stage1_usage = await stage1_collect_responses(user_query)

    # If no models responded successfully, return error
    if not stage1_results:
        return [], [], {
            "model": "error",
            "response": "All models failed to respond. Please try again."
        }, {}

    # Stage 2: Collect rankings
    stage2_results, label_to_model, stage2_usage = await stage2_collect_rankings(user_query, stage1_results)

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Stage 3: Synthesize final answer
    stage3_result, stage3_usage = await stage3_synthesize_final(
        user_query,
        stage1_results,
        stage2_results
    )

    # Prepare metadata
    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings
    }

    return stage1_results, stage2_results, stage3_result, metadata


async def run_full_council_tier2(
    user_query: str,
    enable_debate: bool = True,
    max_debate_rounds: int = None,
    user_response: Optional[str] = None
) -> Tuple[List, List, List, Dict, Dict, List, Optional[Dict]]:
    """
    Run the enhanced Tier 2 council process with multi-round debate.

    Args:
        user_query: The user's question
        enable_debate: Whether to enable multi-round debate
        max_debate_rounds: Maximum debate rounds (defaults to config)
        user_response: Optional user response to include

    Returns:
        Tuple of (stage1_results, stage2_results, rebuttals, stage3_result,
                  metadata, debate_rounds, devils_advocate)
    """
    # Stage 1: Collect responses (with optional user response)
    if user_response and USER_PARTICIPATION_CONFIG.get("enabled", True):
        stage1_results = await stage1_with_user_response(user_query, user_response)
    else:
        stage1_results = await stage1_collect_responses(user_query)

    if not stage1_results:
        return [], [], [], {
            "model": "error",
            "response": "All models failed to respond. Please try again."
        }, {}, [], None

    # Stage 2: Collect rankings
    stage2_results, label_to_model = await stage2_collect_rankings(user_query, stage1_results)
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Multi-round debate
    debate_rounds = []
    all_rebuttals = []

    if enable_debate and DEBATE_CONFIG.get("enabled", True):
        max_rounds = max_debate_rounds or DEBATE_CONFIG.get("max_rounds", 3)

        for round_num in range(max_rounds):
            # Check for consensus
            has_consensus, top_model = check_consensus(stage2_results, label_to_model)
            if has_consensus:
                debate_rounds.append({
                    "round": round_num + 1,
                    "status": "consensus_reached",
                    "top_model": top_model
                })
                break

            # Collect rebuttals
            rebuttals = await stage2b_collect_rebuttals(
                user_query, stage1_results, stage2_results, label_to_model
            )

            if not rebuttals:
                debate_rounds.append({
                    "round": round_num + 1,
                    "status": "no_rebuttals",
                })
                break

            all_rebuttals.extend(rebuttals)
            debate_rounds.append({
                "round": round_num + 1,
                "status": "rebuttals_collected",
                "rebuttal_count": len(rebuttals)
            })

    # Devil's advocate
    devils_advocate = None
    if DEVILS_ADVOCATE_CONFIG.get("enabled", True) and aggregate_rankings:
        # Find the top-ranked model's response
        top_model = aggregate_rankings[0]["model"]
        top_response = next(
            (r for r in stage1_results if r["model"] == top_model),
            stage1_results[0]
        )
        devils_advocate = await stage2_devils_advocate(
            user_query, top_response, aggregate_rankings
        )

    # Stage 3: Synthesize with all debate context
    stage3_result = await stage3_synthesize_final(
        user_query,
        stage1_results,
        stage2_results,
        all_rebuttals,
        devils_advocate
    )

    # Prepare metadata
    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings,
        "debate_rounds": len(debate_rounds),
        "user_participated": user_response is not None
    }

    # Calculate user rank if they participated
    if user_response:
        user_label = USER_PARTICIPATION_CONFIG.get("user_label", "User")
        user_ranking = next(
            (r for r in aggregate_rankings if r["model"] == user_label),
            None
        )
        if user_ranking:
            metadata["user_rank"] = aggregate_rankings.index(user_ranking) + 1
            metadata["user_average_rank"] = user_ranking["average_rank"]

    return (
        stage1_results,
        stage2_results,
        all_rebuttals,
        stage3_result,
        metadata,
        debate_rounds,
        devils_advocate
    )
