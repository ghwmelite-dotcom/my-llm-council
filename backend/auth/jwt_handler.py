"""JWT token handling for authentication."""

import json
import hmac
import hashlib
import base64
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Header


# Secret key for signing tokens - use environment variable in production
JWT_SECRET = os.getenv("JWT_SECRET", "llm-council-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days


def _base64url_encode(data: bytes) -> str:
    """Base64 URL-safe encoding without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _base64url_decode(data: str) -> bytes:
    """Base64 URL-safe decoding with padding restoration."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def create_token(user_id: str, username: str) -> str:
    """
    Create a JWT token for a user.

    Args:
        user_id: The user's ID
        username: The user's username

    Returns:
        JWT token string
    """
    # Header
    header = {
        "alg": JWT_ALGORITHM,
        "typ": "JWT"
    }

    # Payload
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_EXPIRATION_HOURS)).timestamp())
    }

    # Encode header and payload
    header_encoded = _base64url_encode(json.dumps(header).encode())
    payload_encoded = _base64url_encode(json.dumps(payload).encode())

    # Create signature
    message = f"{header_encoded}.{payload_encoded}"
    signature = hmac.new(
        JWT_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    signature_encoded = _base64url_encode(signature)

    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict, or None if invalid
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None

        header_encoded, payload_encoded, signature_encoded = parts

        # Verify signature
        message = f"{header_encoded}.{payload_encoded}"
        expected_signature = hmac.new(
            JWT_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()

        provided_signature = _base64url_decode(signature_encoded)

        if not hmac.compare_digest(expected_signature, provided_signature):
            return None

        # Decode payload
        payload = json.loads(_base64url_decode(payload_encoded))

        # Check expiration
        if payload.get('exp', 0) < datetime.utcnow().timestamp():
            return None

        return payload

    except Exception:
        return None


async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to get current user from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        User payload dict or None if not authenticated
    """
    if not authorization:
        return None

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    token = parts[1]
    return verify_token(token)


async def require_auth(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    FastAPI dependency that requires authentication.

    Raises HTTPException if not authenticated.
    """
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
