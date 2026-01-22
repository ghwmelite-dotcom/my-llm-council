"""Password hashing utilities."""

import hashlib
import secrets
import hmac


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2 with SHA-256.

    Args:
        password: Plain text password

    Returns:
        Hashed password string (salt$hash format)
    """
    salt = secrets.token_hex(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )
    hash_hex = hash_bytes.hex()
    return f"{salt}${hash_hex}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password to verify
        password_hash: Stored hash (salt$hash format)

    Returns:
        True if password matches, False otherwise
    """
    try:
        salt, stored_hash = password_hash.split('$')
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        computed_hash = hash_bytes.hex()
        return hmac.compare_digest(computed_hash, stored_hash)
    except (ValueError, AttributeError):
        return False
