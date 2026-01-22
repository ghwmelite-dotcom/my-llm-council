"""API key authentication for gateway."""

import os
from typing import Optional
from fastapi import HTTPException, Header
from ..config import API_GATEWAY_CONFIG


def verify_api_key(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Verify API key from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        The API key if valid, None if auth not required

    Raises:
        HTTPException: If auth required but key invalid
    """
    config = API_GATEWAY_CONFIG

    # Check if authentication is required
    if not config.get("require_api_key", False):
        return None

    # Get valid API keys from environment
    valid_keys = get_valid_api_keys()

    if not valid_keys:
        # No keys configured, auth disabled
        return None

    # Check for Authorization header
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Parse Bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Use: Bearer <api_key>",
            headers={"WWW-Authenticate": "Bearer"}
        )

    api_key = authorization[7:]  # Remove "Bearer " prefix

    # Validate key
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return api_key


def get_valid_api_keys() -> set:
    """
    Get set of valid API keys from environment.

    Keys can be set via:
    - COUNCIL_API_KEY: Single key
    - COUNCIL_API_KEYS: Comma-separated list of keys

    Returns:
        Set of valid API key strings
    """
    keys = set()

    # Single key
    single_key = os.getenv("COUNCIL_API_KEY")
    if single_key:
        keys.add(single_key)

    # Multiple keys
    multi_keys = os.getenv("COUNCIL_API_KEYS", "")
    if multi_keys:
        for key in multi_keys.split(","):
            key = key.strip()
            if key:
                keys.add(key)

    return keys
