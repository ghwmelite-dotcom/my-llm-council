"""Room management for collaborative conversations."""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path

from ..config import data_path


@dataclass
class Room:
    """Represents a collaborative room/session."""
    id: str
    conversation_id: str
    name: str
    created_by: str
    created_at: str
    is_public: bool = False
    max_users: int = 10
    invite_code: Optional[str] = None


class RoomManager:
    """Manages collaborative rooms."""

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = data_path("collaboration", "rooms.json")
        self.storage_path = storage_path
        self.rooms: Dict[str, Room] = {}
        self._ensure_storage_dir()
        self._load_rooms()

    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)

    def _load_rooms(self):
        """Load rooms from JSON file."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for room_data in data.get('rooms', []):
                        room = Room(**room_data)
                        self.rooms[room.id] = room
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading rooms: {e}")
                self.rooms = {}

    def _save_rooms(self):
        """Save rooms to JSON file."""
        self._ensure_storage_dir()
        data = {
            'rooms': [
                {
                    'id': r.id,
                    'conversation_id': r.conversation_id,
                    'name': r.name,
                    'created_by': r.created_by,
                    'created_at': r.created_at,
                    'is_public': r.is_public,
                    'max_users': r.max_users,
                    'invite_code': r.invite_code,
                }
                for r in self.rooms.values()
            ]
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def create_room(
        self,
        room_id: str,
        conversation_id: str,
        name: str,
        created_by: str,
        is_public: bool = False,
        max_users: int = 10,
        invite_code: Optional[str] = None
    ) -> Room:
        """Create a new collaborative room."""
        room = Room(
            id=room_id,
            conversation_id=conversation_id,
            name=name,
            created_by=created_by,
            created_at=datetime.utcnow().isoformat(),
            is_public=is_public,
            max_users=max_users,
            invite_code=invite_code
        )
        self.rooms[room_id] = room
        self._save_rooms()
        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by ID."""
        return self.rooms.get(room_id)

    def get_room_by_conversation(self, conversation_id: str) -> Optional[Room]:
        """Get a room by conversation ID."""
        for room in self.rooms.values():
            if room.conversation_id == conversation_id:
                return room
        return None

    def get_room_by_invite_code(self, invite_code: str) -> Optional[Room]:
        """Get a room by invite code."""
        for room in self.rooms.values():
            if room.invite_code == invite_code:
                return room
        return None

    def get_public_rooms(self) -> List[Room]:
        """Get all public rooms."""
        return [r for r in self.rooms.values() if r.is_public]

    def delete_room(self, room_id: str) -> bool:
        """Delete a room."""
        if room_id in self.rooms:
            del self.rooms[room_id]
            self._save_rooms()
            return True
        return False

    def update_room(self, room_id: str, **updates) -> Optional[Room]:
        """Update room properties."""
        if room_id not in self.rooms:
            return None

        room = self.rooms[room_id]
        for key, value in updates.items():
            if hasattr(room, key):
                setattr(room, key, value)

        self._save_rooms()
        return room


# Singleton instance
_room_manager: Optional[RoomManager] = None


def get_room_manager() -> RoomManager:
    """Get the singleton room manager instance."""
    global _room_manager
    if _room_manager is None:
        _room_manager = RoomManager()
    return _room_manager
