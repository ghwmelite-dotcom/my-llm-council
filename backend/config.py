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
# SMART ROUTING: Query Complexity-Based Routing
# =============================================================================

SMART_ROUTING_CONFIG = {
    "enabled": True,
    "complexity_threshold_single": 0.3,  # Below this -> single model
    "complexity_threshold_full": 0.7,    # Above this -> full council
    "single_model": "anthropic/claude-sonnet-4.5",  # Fast, capable model
    "mini_council_size": 3,              # Models for medium complexity
}

# =============================================================================
# SEMANTIC CACHING: Response Caching by Query Similarity
# =============================================================================

SEMANTIC_CACHE_CONFIG = {
    "enabled": True,
    "storage_path": "data/cache/semantic_cache.json",
    "similarity_threshold": 0.85,  # Min similarity for cache hit
    "max_cache_size": 1000,        # Max cached responses
    "ttl_hours": 24,               # Time-to-live in hours
}

# =============================================================================
# FACTUAL VERIFICATION: Stage 1.5 Contradiction Detection
# =============================================================================

VERIFICATION_CONFIG = {
    "enabled": True,
    "model": "anthropic/claude-sonnet-4.5",  # Model for claim extraction
    "min_claims_for_verification": 3,         # Min claims to trigger verification
    "contradiction_threshold": 0.7,           # Confidence threshold for contradictions
}

# =============================================================================
# AGENTIC TOOLS: Tool Use for Council Members
# =============================================================================

TOOLS_CONFIG = {
    "enabled": True,
    "available_tools": ["web_search", "calculator", "code_executor"],
    "max_tool_calls_per_response": 3,
    "tool_timeout_seconds": 30,
    "code_execution_enabled": False,  # Safety default - enable carefully
}

# =============================================================================
# API GATEWAY: OpenAI-Compatible API Endpoint
# =============================================================================

API_GATEWAY_CONFIG = {
    "enabled": True,
    "require_api_key": False,  # Set True to require COUNCIL_API_KEY env var
    "default_council": "general",
    "include_deliberation_default": False,  # Include stage data in responses
    "model_name_mapping": {
        # Map OpenAI model names to councils for compatibility
        "gpt-4": "general",
        "gpt-4o": "general",
        "gpt-3.5-turbo": "general",
        "claude-3-opus": "general",
        "council-math": "math",
        "council-ethics": "ethics",
        "council-creative": "creative",
    },
}

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
