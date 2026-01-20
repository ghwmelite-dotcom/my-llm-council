"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# MongoDB connection (for persistent storage)
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "llm_council")

# Council members - list of OpenRouter model identifiers
COUNCIL_MODELS = [
    "openai/gpt-5.1",
    "google/gemini-3-pro-preview",
    "anthropic/claude-sonnet-4.5",
    "x-ai/grok-4",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "google/gemini-3-pro-preview"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# =============================================================================
# TIER 2: Deeper Deliberation Configuration
# =============================================================================

# Multi-round debate settings
DEBATE_CONFIG = {
    "enabled": True,
    "max_rounds": 3,
    "consensus_threshold": 0.8,  # 80% agreement to stop early
    "min_critique_length": 50,   # Minimum characters for a critique to trigger rebuttal
}

# Devil's advocate settings
DEVILS_ADVOCATE_CONFIG = {
    "enabled": True,
    "challenge_top_ranked": True,  # Always challenge the top-ranked response
    "model": "anthropic/claude-sonnet-4.5",  # Model to play devil's advocate
}

# User participation settings
USER_PARTICIPATION_CONFIG = {
    "enabled": True,
    "anonymize_user": True,  # User response shown as "Response X" during peer review
    "user_label": "User",    # Label for de-anonymized display
}

# =============================================================================
# TIER 3: Living System Configuration
# =============================================================================

# Memory settings
MEMORY_CONFIG = {
    "enabled": True,
    "storage_path": "data/memory/memories.json",
    "relationships_path": "data/memory/relationships.json",
    "max_memories_per_query": 5,
    "memory_relevance_threshold": 0.3,
}

# Specialized councils
SPECIALIZED_COUNCILS = {
    "general": {
        "name": "General Council",
        "description": "Default council for general questions",
        "models": COUNCIL_MODELS,
        "chairman": CHAIRMAN_MODEL,
        "keywords": [],  # Matches anything
    },
    "math": {
        "name": "Mathematics Council",
        "description": "Specialized council for mathematical and logical problems",
        "models": [
            "openai/o1",
            "anthropic/claude-sonnet-4.5",
            "google/gemini-3-pro-preview",
        ],
        "chairman": "openai/o1",
        "keywords": ["math", "calculate", "equation", "proof", "theorem", "algebra", "calculus", "statistics"],
    },
    "ethics": {
        "name": "Ethics Council",
        "description": "Specialized council for ethical and philosophical questions",
        "models": [
            "anthropic/claude-sonnet-4.5",
            "openai/gpt-5.1",
            "google/gemini-3-pro-preview",
        ],
        "chairman": "anthropic/claude-sonnet-4.5",
        "keywords": ["ethics", "moral", "right", "wrong", "should", "ought", "philosophy", "values"],
    },
    "creative": {
        "name": "Creative Council",
        "description": "Specialized council for creative and artistic tasks",
        "models": [
            "anthropic/claude-sonnet-4.5",
            "openai/gpt-5.1",
            "x-ai/grok-4",
        ],
        "chairman": "anthropic/claude-sonnet-4.5",
        "keywords": ["write", "story", "poem", "creative", "imagine", "fiction", "art", "design"],
    },
    "supreme": {
        "name": "Supreme Council",
        "description": "Full council for appeals and complex matters",
        "models": COUNCIL_MODELS + ["openai/o1"],
        "chairman": "google/gemini-3-pro-preview",
        "keywords": [],  # Only used for appeals
    },
}

# Real-time feeds settings
FEEDS_CONFIG = {
    "enabled": True,
    "news_api_key": os.getenv("NEWS_API_KEY"),
    "weather_api_key": os.getenv("OPENWEATHER_API_KEY"),
    "cache_duration_minutes": 15,
    "keywords": ["current", "today", "latest", "news", "weather", "now"],
}

# =============================================================================
# TIER 4: Meta & Experimental Configuration
# =============================================================================

# Prediction market settings
PREDICTIONS_CONFIG = {
    "enabled": True,
    "storage_path": "data/predictions",
    "initial_elo": 1500,
    "k_factor": 32,  # Elo K-factor for rating changes
}

# Constitution settings
CONSTITUTION_CONFIG = {
    "enabled": True,
    "storage_path": "data/constitution/constitution.json",
    "enforce_in_prompts": True,
    "allow_amendments": True,
    "amendment_vote_threshold": 0.75,  # 75% of models must agree
}

# Observer model settings
OBSERVER_CONFIG = {
    "enabled": True,
    "model": "anthropic/claude-sonnet-4.5",
    "analyze_biases": True,
    "detect_groupthink": True,
    "cognitive_biases": [
        "confirmation_bias",
        "anchoring",
        "groupthink",
        "availability_heuristic",
        "blind_spots",
    ],
}
