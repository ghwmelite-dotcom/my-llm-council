"""Extract factual claims from model responses using LLM."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import re
from ..openrouter import query_model
from ..config import VERIFICATION_CONFIG


@dataclass
class Claim:
    """A factual claim extracted from a response."""
    text: str                           # The claim text
    model: str                          # Which model made this claim
    category: str = "general"           # Category: factual, statistical, definitional, etc.
    confidence: float = 0.5             # How confident the extractor is this is a claim
    supporting_context: str = ""        # Surrounding context from the response

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "model": self.model,
            "category": self.category,
            "confidence": self.confidence,
            "supporting_context": self.supporting_context
        }


CLAIM_EXTRACTION_PROMPT = """Analyze the following response and extract all factual claims that can be verified as true or false.

Response to analyze:
{response}

Extract factual claims following these rules:
1. Focus on concrete, verifiable statements (dates, numbers, facts, definitions)
2. Ignore opinions, recommendations, and subjective statements
3. Include claims about cause-effect relationships
4. Include statistical claims and numerical data
5. Include definitional claims (X is defined as Y)

Return a JSON array of claims with this structure:
[
  {{
    "text": "the exact factual claim",
    "category": "factual|statistical|definitional|causal|temporal",
    "confidence": 0.0-1.0
  }}
]

Only return the JSON array, nothing else. If no factual claims are found, return an empty array: []
"""


async def extract_claims(
    response: str,
    model_source: str
) -> List[Claim]:
    """
    Extract factual claims from a model's response.

    Args:
        response: The text response to analyze
        model_source: The model that generated this response

    Returns:
        List of extracted Claim objects
    """
    config = VERIFICATION_CONFIG
    extractor_model = config.get("model", "anthropic/claude-sonnet-4.5")

    prompt = CLAIM_EXTRACTION_PROMPT.format(response=response)
    messages = [{"role": "user", "content": prompt}]

    result = await query_model(extractor_model, messages, timeout=60.0)

    if not result:
        return []

    content = result.get('content', '[]')

    # Parse JSON from response
    claims = []
    try:
        # Try to extract JSON from the response
        # Handle cases where the model wraps it in markdown code blocks
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            parsed = json.loads(json_match.group())
            for item in parsed:
                claims.append(Claim(
                    text=item.get("text", ""),
                    model=model_source,
                    category=item.get("category", "general"),
                    confidence=item.get("confidence", 0.5),
                    supporting_context=""
                ))
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract claims heuristically
        pass

    return claims


async def extract_claims_batch(
    responses: List[Dict[str, Any]]
) -> Dict[str, List[Claim]]:
    """
    Extract claims from multiple responses in parallel.

    Args:
        responses: List of stage 1 responses with 'model' and 'response' keys

    Returns:
        Dict mapping model name to list of claims
    """
    import asyncio

    tasks = []
    models = []

    for resp in responses:
        model = resp.get('model', 'unknown')
        text = resp.get('response', '')
        models.append(model)
        tasks.append(extract_claims(text, model))

    results = await asyncio.gather(*tasks)

    return {model: claims for model, claims in zip(models, results)}
