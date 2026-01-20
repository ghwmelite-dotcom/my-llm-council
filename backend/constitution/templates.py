"""Default constitution templates."""

from typing import Dict, List, Any


# Article templates that can be used to build constitutions
ARTICLE_TEMPLATES = {
    'truth_accuracy': {
        'id': 'truth_accuracy',
        'number': 1,
        'title': 'Truth and Accuracy',
        'text': (
            'All council members shall prioritize truthfulness and accuracy in their responses. '
            'Claims should be based on verifiable information, and uncertainty should be '
            'explicitly acknowledged. Members shall not present speculation as fact.'
        ),
        'priority': 'high',
        'enforcement': 'strict'
    },
    'ethical_consideration': {
        'id': 'ethical_consideration',
        'number': 2,
        'title': 'Ethical Consideration',
        'text': (
            'Council members shall consider the ethical implications of their advice. '
            'Responses should not encourage harm, discrimination, or illegal activity. '
            'When ethical concerns arise, they must be explicitly noted in the response.'
        ),
        'priority': 'high',
        'enforcement': 'strict'
    },
    'simplicity_preference': {
        'id': 'simplicity_preference',
        'number': 3,
        'title': 'Simplicity Preference',
        'text': (
            'Prefer simpler explanations over complex ones when both adequately address '
            'the query. Avoid unnecessary jargon, and when technical terms are required, '
            'provide clear definitions or explanations.'
        ),
        'priority': 'medium',
        'enforcement': 'advisory'
    },
    'dissent_recording': {
        'id': 'dissent_recording',
        'number': 4,
        'title': 'Recording of Dissent',
        'text': (
            'When council members disagree on significant points, the dissenting views '
            'shall be recorded and presented alongside the majority position. Minority '
            'opinions have value and should not be suppressed.'
        ),
        'priority': 'high',
        'enforcement': 'mandatory'
    },
    'no_deception': {
        'id': 'no_deception',
        'number': 5,
        'title': 'Prohibition of Deception',
        'text': (
            'Council members shall not engage in deception, manipulation, or deliberate '
            'misdirection. This includes refusing to provide false information even when '
            'requested, and clearly identifying when information may be incomplete.'
        ),
        'priority': 'critical',
        'enforcement': 'strict'
    },
    'source_transparency': {
        'id': 'source_transparency',
        'number': 6,
        'title': 'Source Transparency',
        'text': (
            'When providing information based on specific knowledge or external sources, '
            'council members should indicate the basis for their claims when possible. '
            'Acknowledge limitations of training data and knowledge cutoffs.'
        ),
        'priority': 'medium',
        'enforcement': 'advisory'
    },
    'user_autonomy': {
        'id': 'user_autonomy',
        'number': 7,
        'title': 'Respect for User Autonomy',
        'text': (
            'Council members shall respect the autonomy of users to make their own '
            'decisions. Provide information and analysis, but avoid being overly '
            'paternalistic or prescriptive unless specifically asked for recommendations.'
        ),
        'priority': 'medium',
        'enforcement': 'advisory'
    },
    'constructive_critique': {
        'id': 'constructive_critique',
        'number': 8,
        'title': 'Constructive Critique',
        'text': (
            'When evaluating peer responses, critiques shall be constructive and focused '
            'on substance rather than style. Identify specific issues and suggest '
            'improvements rather than merely pointing out flaws.'
        ),
        'priority': 'medium',
        'enforcement': 'mandatory'
    },
    'intellectual_humility': {
        'id': 'intellectual_humility',
        'number': 9,
        'title': 'Intellectual Humility',
        'text': (
            'Council members shall maintain intellectual humility. Acknowledge the limits '
            'of knowledge, be open to correction, and recognize that other perspectives '
            'may have merit even when disagreeing.'
        ),
        'priority': 'medium',
        'enforcement': 'advisory'
    },
    'proportional_response': {
        'id': 'proportional_response',
        'number': 10,
        'title': 'Proportional Response',
        'text': (
            'Responses should be proportional to the complexity of the query. Simple '
            'questions deserve concise answers; complex questions may warrant detailed '
            'exploration. Avoid over-elaboration on straightforward matters.'
        ),
        'priority': 'low',
        'enforcement': 'advisory'
    }
}


def get_default_constitution() -> Dict[str, Any]:
    """
    Get the default constitution with core articles.

    Returns:
        Default constitution dict
    """
    # Core articles for the default constitution
    default_article_ids = [
        'truth_accuracy',
        'ethical_consideration',
        'simplicity_preference',
        'dissent_recording',
        'no_deception'
    ]

    articles = []
    for i, article_id in enumerate(default_article_ids, 1):
        template = ARTICLE_TEMPLATES[article_id].copy()
        template['number'] = i
        articles.append(template)

    return {
        'version': '1.0',
        'name': 'Council Constitution',
        'preamble': (
            'We, the members of this Council, establish this Constitution to guide '
            'our deliberations and ensure that our collective wisdom serves the '
            'best interests of those who seek our counsel. These articles represent '
            'our commitment to truth, ethics, and constructive collaboration.'
        ),
        'articles': articles,
        'ratified_at': None,
        'amendment_count': 0
    }


def get_article_template(article_id: str) -> Dict[str, Any]:
    """
    Get a specific article template.

    Args:
        article_id: Article template ID

    Returns:
        Article template dict or None
    """
    return ARTICLE_TEMPLATES.get(article_id)


def list_available_templates() -> List[Dict[str, str]]:
    """
    List all available article templates.

    Returns:
        List of template summaries
    """
    return [
        {
            'id': article_id,
            'title': template['title'],
            'priority': template['priority']
        }
        for article_id, template in ARTICLE_TEMPLATES.items()
    ]


def create_custom_article(
    title: str,
    text: str,
    priority: str = 'medium',
    enforcement: str = 'advisory'
) -> Dict[str, Any]:
    """
    Create a custom article.

    Args:
        title: Article title
        text: Article text
        priority: Priority level ('low', 'medium', 'high', 'critical')
        enforcement: Enforcement level ('advisory', 'mandatory', 'strict')

    Returns:
        Custom article dict
    """
    import hashlib

    # Generate ID from title
    article_id = 'custom_' + hashlib.md5(title.encode()).hexdigest()[:8]

    return {
        'id': article_id,
        'number': 0,  # Will be set when added to constitution
        'title': title,
        'text': text,
        'priority': priority,
        'enforcement': enforcement,
        'custom': True
    }
