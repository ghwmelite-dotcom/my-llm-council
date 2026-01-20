"""Constitution enforcement and prompt injection."""

from typing import Dict, List, Any, Optional
from .storage import get_constitution
from ..config import CONSTITUTION_CONFIG


def format_constitution_for_prompt(
    constitution: Dict[str, Any] = None,
    include_preamble: bool = True,
    priority_filter: str = None
) -> str:
    """
    Format the constitution for inclusion in a prompt.

    Args:
        constitution: Constitution dict (uses current if None)
        include_preamble: Whether to include the preamble
        priority_filter: Only include articles with this priority or higher

    Returns:
        Formatted constitution string
    """
    if constitution is None:
        constitution = get_constitution()

    parts = []

    # Header
    parts.append("=== COUNCIL CONSTITUTION ===")
    parts.append("")

    # Preamble
    if include_preamble and constitution.get('preamble'):
        parts.append("PREAMBLE:")
        parts.append(constitution['preamble'])
        parts.append("")

    # Articles
    parts.append("ARTICLES:")
    parts.append("")

    priority_order = ['critical', 'high', 'medium', 'low']
    min_priority_index = 0

    if priority_filter:
        try:
            min_priority_index = priority_order.index(priority_filter)
        except ValueError:
            pass

    for article in constitution.get('articles', []):
        # Filter by priority if specified
        article_priority = article.get('priority', 'medium')
        try:
            article_priority_index = priority_order.index(article_priority)
        except ValueError:
            article_priority_index = 2  # Default to medium

        if article_priority_index > min_priority_index:
            continue

        # Format article
        number = article.get('number', '?')
        title = article.get('title', 'Untitled')
        text = article.get('text', '')
        enforcement = article.get('enforcement', 'advisory')

        parts.append(f"Article {number}: {title}")
        parts.append(f"{text}")

        if enforcement == 'strict':
            parts.append("(STRICTLY ENFORCED)")
        elif enforcement == 'mandatory':
            parts.append("(MANDATORY)")

        parts.append("")

    parts.append("=== END CONSTITUTION ===")

    return "\n".join(parts)


def inject_constitution(
    prompt: str,
    position: str = 'prepend',
    priority_filter: str = None
) -> str:
    """
    Inject the constitution into a prompt.

    Args:
        prompt: Original prompt
        position: Where to inject ('prepend', 'append', 'system')
        priority_filter: Only include articles with this priority or higher

    Returns:
        Prompt with constitution injected
    """
    if not CONSTITUTION_CONFIG.get('enabled', True):
        return prompt

    constitution_text = format_constitution_for_prompt(
        priority_filter=priority_filter
    )

    if position == 'prepend':
        return f"{constitution_text}\n\n---\n\n{prompt}"
    elif position == 'append':
        return f"{prompt}\n\n---\n\n{constitution_text}"
    else:
        return f"{constitution_text}\n\n{prompt}"


def create_compliance_check_prompt(
    response: str,
    constitution: Dict[str, Any] = None
) -> str:
    """
    Create a prompt to check if a response complies with the constitution.

    Args:
        response: Response to check
        constitution: Constitution to check against

    Returns:
        Compliance check prompt
    """
    constitution_text = format_constitution_for_prompt(constitution)

    return f"""Review the following response for compliance with the Council Constitution.

{constitution_text}

RESPONSE TO CHECK:
{response}

For each article, determine if the response:
1. COMPLIES - Adheres to the article
2. VIOLATES - Contradicts the article
3. N/A - Article not applicable to this response

Provide your analysis in the following format:

COMPLIANCE ANALYSIS:

Article 1: [COMPLIES/VIOLATES/N/A]
Reason: [Brief explanation]

Article 2: [COMPLIES/VIOLATES/N/A]
Reason: [Brief explanation]

[Continue for all articles]

OVERALL COMPLIANCE: [PASS/FAIL]
VIOLATIONS: [List any violations]
RECOMMENDATIONS: [Any suggestions for improvement]
"""


def check_compliance(
    response: str,
    constitution: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Check if a response complies with the constitution.

    This is a synchronous version that performs basic keyword checks.
    For full AI-powered compliance checking, use the async version
    with an LLM call.

    Args:
        response: Response to check
        constitution: Constitution to check against

    Returns:
        Compliance report dict
    """
    if constitution is None:
        constitution = get_constitution()

    response_lower = response.lower()
    violations = []
    warnings = []

    for article in constitution.get('articles', []):
        article_id = article.get('id', '')
        title = article.get('title', '')
        enforcement = article.get('enforcement', 'advisory')

        # Basic heuristic checks based on article ID
        if article_id == 'truth_accuracy':
            # Check for definitive statements about uncertain topics
            uncertain_indicators = [
                'i am certain', 'definitely', 'without a doubt',
                'there is no question', '100%'
            ]
            for indicator in uncertain_indicators:
                if indicator in response_lower:
                    if enforcement == 'strict':
                        violations.append({
                            'article': title,
                            'issue': 'Contains potentially overconfident language',
                            'severity': 'medium'
                        })
                    else:
                        warnings.append({
                            'article': title,
                            'issue': 'Contains potentially overconfident language'
                        })
                    break

        elif article_id == 'no_deception':
            # Check for deceptive patterns
            deception_indicators = [
                'pretend', 'act as if', 'fabricate', 'make up',
                'invent a story', 'lie about'
            ]
            for indicator in deception_indicators:
                if indicator in response_lower:
                    violations.append({
                        'article': title,
                        'issue': 'Contains potentially deceptive language',
                        'severity': 'high'
                    })
                    break

        elif article_id == 'ethical_consideration':
            # Check for harmful content indicators
            harm_indicators = [
                'how to harm', 'how to hurt', 'how to kill',
                'how to steal', 'how to hack illegally'
            ]
            for indicator in harm_indicators:
                if indicator in response_lower:
                    violations.append({
                        'article': title,
                        'issue': 'Contains potentially harmful content',
                        'severity': 'critical'
                    })
                    break

    # Calculate overall compliance
    critical_violations = [v for v in violations if v.get('severity') == 'critical']
    high_violations = [v for v in violations if v.get('severity') == 'high']

    compliant = len(critical_violations) == 0 and len(high_violations) == 0

    return {
        'compliant': compliant,
        'violations': violations,
        'warnings': warnings,
        'violation_count': len(violations),
        'warning_count': len(warnings),
        'articles_checked': len(constitution.get('articles', []))
    }


def get_enforcement_instructions() -> str:
    """
    Get enforcement instructions for inclusion in prompts.

    Returns:
        Enforcement instruction string
    """
    return """CONSTITUTION ENFORCEMENT INSTRUCTIONS:

You are bound by the Council Constitution provided above. When formulating your response:

1. Review the relevant articles before responding
2. Ensure your response does not violate any STRICTLY ENFORCED or MANDATORY articles
3. Consider ADVISORY articles as guidance
4. If a response would violate the constitution, explain why you cannot comply
5. When in doubt, err on the side of caution and transparency

Failure to comply with the constitution may result in your response being flagged or rejected.
"""


def get_constitution_summary() -> Dict[str, Any]:
    """
    Get a summary of the current constitution.

    Returns:
        Constitution summary
    """
    constitution = get_constitution()
    articles = constitution.get('articles', [])

    return {
        'name': constitution.get('name'),
        'version': constitution.get('version'),
        'article_count': len(articles),
        'amendment_count': constitution.get('amendment_count', 0),
        'ratified_at': constitution.get('ratified_at'),
        'last_modified': constitution.get('last_modified'),
        'articles': [
            {
                'number': a.get('number'),
                'title': a.get('title'),
                'priority': a.get('priority'),
                'enforcement': a.get('enforcement')
            }
            for a in articles
        ]
    }
