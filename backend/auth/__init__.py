"""Authentication module for user registration and login."""

from .models import User, UserCreate, UserLogin, UserResponse, UserUpdate, OnboardingUpdate
from .storage import get_user_store
from .jwt_handler import create_token, verify_token, get_current_user
from .password import hash_password, verify_password

__all__ = [
    'User',
    'UserCreate',
    'UserLogin',
    'UserResponse',
    'UserUpdate',
    'OnboardingUpdate',
    'get_user_store',
    'create_token',
    'verify_token',
    'get_current_user',
    'hash_password',
    'verify_password',
]
