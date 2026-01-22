"""WebSocket connection manager for real-time collaboration."""

from typing import Dict, Set, Optional, List
from fastapi import WebSocket
from dataclasses import dataclass, field
from datetime import datetime
import json
import asyncio


@dataclass
class ConnectedUser:
    """Represents a connected user."""
    user_id: str
    username: str
    websocket: WebSocket
    connected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    color: str = "#4a90e2"  # Default user color


class ConnectionManager:
    """Manages WebSocket connections for collaborative sessions."""

    def __init__(self):
        # conversation_id -> set of connected users
        self.active_connections: Dict[str, Dict[str, ConnectedUser]] = {}
        # user_id -> conversation_id (track which room each user is in)
        self.user_rooms: Dict[str, str] = {}

    async def connect(
        self,
        websocket: WebSocket,
        conversation_id: str,
        user_id: str,
        username: str
    ):
        """Connect a user to a conversation room."""
        await websocket.accept()

        # Leave any previous room
        if user_id in self.user_rooms:
            old_room = self.user_rooms[user_id]
            await self.disconnect(user_id)

        # Create room if it doesn't exist
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = {}

        # Assign a color based on user count
        colors = ["#4a90e2", "#22c55e", "#f59e0b", "#a855f7", "#ec4899", "#ef4444"]
        user_count = len(self.active_connections[conversation_id])
        color = colors[user_count % len(colors)]

        # Add user to room
        user = ConnectedUser(
            user_id=user_id,
            username=username,
            websocket=websocket,
            color=color
        )
        self.active_connections[conversation_id][user_id] = user
        self.user_rooms[user_id] = conversation_id

        # Notify others that user joined
        await self.broadcast_to_room(
            conversation_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "username": username,
                "color": color,
                "users": self.get_room_users(conversation_id)
            },
            exclude_user=None  # Include everyone
        )

    async def disconnect(self, user_id: str):
        """Disconnect a user from their current room."""
        if user_id not in self.user_rooms:
            return

        conversation_id = self.user_rooms[user_id]
        if conversation_id in self.active_connections:
            user = self.active_connections[conversation_id].get(user_id)
            username = user.username if user else "Unknown"

            if user_id in self.active_connections[conversation_id]:
                del self.active_connections[conversation_id][user_id]

            # Clean up empty rooms
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
            else:
                # Notify others that user left
                await self.broadcast_to_room(
                    conversation_id,
                    {
                        "type": "user_left",
                        "user_id": user_id,
                        "username": username,
                        "users": self.get_room_users(conversation_id)
                    }
                )

        del self.user_rooms[user_id]

    def get_room_users(self, conversation_id: str) -> List[Dict]:
        """Get list of users in a room."""
        if conversation_id not in self.active_connections:
            return []

        return [
            {
                "user_id": user.user_id,
                "username": user.username,
                "color": user.color,
                "connected_at": user.connected_at
            }
            for user in self.active_connections[conversation_id].values()
        ]

    async def broadcast_to_room(
        self,
        conversation_id: str,
        message: dict,
        exclude_user: Optional[str] = None
    ):
        """Broadcast a message to all users in a room."""
        if conversation_id not in self.active_connections:
            return

        for user_id, user in self.active_connections[conversation_id].items():
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await user.websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending to {user_id}: {e}")

    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to a specific user."""
        if user_id not in self.user_rooms:
            return

        conversation_id = self.user_rooms[user_id]
        if conversation_id in self.active_connections:
            user = self.active_connections[conversation_id].get(user_id)
            if user:
                try:
                    await user.websocket.send_text(json.dumps(message))
                except Exception as e:
                    print(f"Error sending to {user_id}: {e}")

    async def broadcast_typing(
        self,
        conversation_id: str,
        user_id: str,
        username: str,
        is_typing: bool
    ):
        """Broadcast typing indicator to room."""
        await self.broadcast_to_room(
            conversation_id,
            {
                "type": "typing",
                "user_id": user_id,
                "username": username,
                "is_typing": is_typing
            },
            exclude_user=user_id
        )

    async def broadcast_cursor(
        self,
        conversation_id: str,
        user_id: str,
        position: dict
    ):
        """Broadcast cursor position to room."""
        user = self.active_connections.get(conversation_id, {}).get(user_id)
        if not user:
            return

        await self.broadcast_to_room(
            conversation_id,
            {
                "type": "cursor",
                "user_id": user_id,
                "username": user.username,
                "color": user.color,
                "position": position
            },
            exclude_user=user_id
        )

    def get_connection_count(self, conversation_id: str) -> int:
        """Get number of connections in a room."""
        if conversation_id not in self.active_connections:
            return 0
        return len(self.active_connections[conversation_id])


# Singleton instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get the singleton connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
