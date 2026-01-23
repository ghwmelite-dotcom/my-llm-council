"""User storage for authentication."""

import json
import os
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import asdict

from .models import User
from .password import hash_password, verify_password
from ..config import data_path


class UserStore:
    """Manages user data storage."""

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = data_path("auth", "users.json")
        self.storage_path = storage_path
        self.users: Dict[str, User] = {}
        self.username_index: Dict[str, str] = {}  # username -> user_id
        self._ensure_dir()
        self._load_users()

    def _ensure_dir(self):
        """Ensure the storage directory exists."""
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)

    def _load_users(self):
        """Load users from JSON file."""
        print(f"[UserStore] Attempting to load users from: {self.storage_path}")
        print(f"[UserStore] File exists: {os.path.exists(self.storage_path)}")

        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    raw_content = f.read()
                    print(f"[UserStore] File size: {len(raw_content)} bytes")
                    data = json.loads(raw_content)
                    user_count = len(data.get('users', []))
                    print(f"[UserStore] Found {user_count} users in file")
                    for user_data in data.get('users', []):
                        user = User(**user_data)
                        self.users[user.id] = user
                        self.username_index[user.username.lower()] = user.id
                        print(f"[UserStore] Loaded user: {user.username} (id: {user.id})")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[UserStore] ERROR loading users: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[UserStore] No users file found, starting fresh")

    def _save_users(self):
        """Save users to JSON file."""
        self._ensure_dir()
        data = {
            'users': [self._user_to_dict(u) for u in self.users.values()],
            'last_updated': datetime.utcnow().isoformat(),
            'count': len(self.users)
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _user_to_dict(self, user: User) -> dict:
        """Convert User to dict for storage."""
        return {
            'id': user.id,
            'username': user.username,
            'password_hash': user.password_hash,
            'display_name': user.display_name,
            'created_at': user.created_at,
            'last_login': user.last_login,
            'email': user.email,
            'avatar_color': user.avatar_color,
            'onboarding_complete': user.onboarding_complete,
            'preferences': user.preferences,
            'conversation_ids': user.conversation_ids,
        }

    def create_user(
        self,
        username: str,
        password: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None
    ) -> Optional[User]:
        """
        Create a new user.

        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            display_name: Display name (defaults to username)
            email: Optional email address

        Returns:
            Created User or None if username exists
        """
        # Check if username exists (case-insensitive)
        if username.lower() in self.username_index:
            return None

        # Generate avatar color based on username hash
        colors = ["#4a90e2", "#22c55e", "#f59e0b", "#a855f7", "#ec4899", "#ef4444", "#06b6d4", "#8b5cf6"]
        color_index = hash(username) % len(colors)

        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=hash_password(password),
            display_name=display_name or username,
            created_at=datetime.utcnow().isoformat(),
            email=email,
            avatar_color=colors[color_index],
            onboarding_complete=False,
            preferences={},
            conversation_ids=[]
        )

        self.users[user.id] = user
        self.username_index[username.lower()] = user.id
        self._save_users()

        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username (case-insensitive)."""
        user_id = self.username_index.get(username.lower())
        if user_id:
            return self.users.get(user_id)
        return None

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User if credentials are valid, None otherwise
        """
        user = self.get_user_by_username(username)
        if user and verify_password(password, user.password_hash):
            # Update last login
            user.last_login = datetime.utcnow().isoformat()
            self._save_users()
            return user
        return None

    def update_user(self, user_id: str, **updates) -> Optional[User]:
        """Update user properties."""
        user = self.users.get(user_id)
        if not user:
            return None

        for key, value in updates.items():
            if hasattr(user, key) and key not in ('id', 'username', 'password_hash'):
                setattr(user, key, value)

        self._save_users()
        return user

    def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user password."""
        user = self.users.get(user_id)
        if not user:
            return False

        user.password_hash = hash_password(new_password)
        self._save_users()
        return True

    def add_conversation(self, user_id: str, conversation_id: str):
        """Add a conversation to user's list."""
        user = self.users.get(user_id)
        if user and conversation_id not in user.conversation_ids:
            user.conversation_ids.append(conversation_id)
            self._save_users()

    def remove_conversation(self, user_id: str, conversation_id: str):
        """Remove a conversation from user's list."""
        user = self.users.get(user_id)
        if user and conversation_id in user.conversation_ids:
            user.conversation_ids.remove(conversation_id)
            self._save_users()

    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        user = self.users.get(user_id)
        if user:
            del self.username_index[user.username.lower()]
            del self.users[user_id]
            self._save_users()
            return True
        return False

    def username_exists(self, username: str) -> bool:
        """Check if username exists."""
        return username.lower() in self.username_index


# Singleton instance
_user_store: Optional[UserStore] = None


def get_user_store() -> UserStore:
    """Get the singleton user store instance."""
    global _user_store
    if _user_store is None:
        _user_store = UserStore()
    return _user_store
