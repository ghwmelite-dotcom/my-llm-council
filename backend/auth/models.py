"""User models for authentication."""

from pydantic import BaseModel, Field
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    """User data model."""
    id: str
    username: str
    password_hash: str
    display_name: str
    created_at: str
    last_login: Optional[str] = None
    email: Optional[str] = None
    avatar_color: str = "#4a90e2"
    onboarding_complete: bool = False
    preferences: dict = field(default_factory=dict)
    conversation_ids: List[str] = field(default_factory=list)


class UserCreate(BaseModel):
    """Request model for user registration."""
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=6, max_length=100)
    display_name: Optional[str] = None
    email: Optional[str] = None


class UserLogin(BaseModel):
    """Request model for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Response model for user data (excludes sensitive info)."""
    id: str
    username: str
    display_name: str
    created_at: str
    last_login: Optional[str]
    email: Optional[str]
    avatar_color: str
    onboarding_complete: bool
    preferences: dict
    conversation_count: int


class UserUpdate(BaseModel):
    """Request model for updating user profile."""
    display_name: Optional[str] = None
    email: Optional[str] = None
    avatar_color: Optional[str] = None
    preferences: Optional[dict] = None


class OnboardingUpdate(BaseModel):
    """Request model for updating onboarding status."""
    complete: bool
    steps_completed: Optional[List[str]] = None
