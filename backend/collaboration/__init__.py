"""Real-time collaboration module for multi-user conversations."""

from .manager import ConnectionManager, get_connection_manager
from .rooms import Room, get_room_manager

__all__ = [
    'ConnectionManager',
    'get_connection_manager',
    'Room',
    'get_room_manager',
]
