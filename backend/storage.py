"""Storage for conversations - MongoDB or JSON file fallback."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import MONGODB_URI, MONGODB_DB_NAME

# Storage mode
_use_mongodb = bool(MONGODB_URI)
_client = None
_db = None

# JSON storage directory (for local development)
_DATA_DIR = Path(__file__).parent.parent / "data" / "conversations"


def _ensure_data_dir():
    """Ensure the JSON data directory exists."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _get_conversation_path(conversation_id: str) -> Path:
    """Get the file path for a conversation."""
    return _DATA_DIR / f"{conversation_id}.json"


def get_db():
    """Get MongoDB database connection (lazy initialization)."""
    global _client, _db

    if not _use_mongodb:
        return None

    if _db is not None:
        return _db

    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure

        _client = MongoClient(MONGODB_URI)
        # Test connection
        _client.admin.command('ping')
        _db = _client[MONGODB_DB_NAME]
        print(f"Connected to MongoDB database: {MONGODB_DB_NAME}")
        return _db
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        print("Falling back to JSON file storage")
        return None


def get_conversations_collection():
    """Get the conversations collection (MongoDB only)."""
    db = get_db()
    if db is None:
        return None
    return db.conversations


def create_conversation(conversation_id: str) -> Dict[str, Any]:
    """
    Create a new conversation.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        New conversation dict
    """
    conversation = {
        "id": conversation_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Conversation",
        "messages": []
    }

    collection = get_conversations_collection()
    if collection is not None:
        # MongoDB storage
        doc = {**conversation, "_id": conversation_id}
        collection.insert_one(doc)
    else:
        # JSON file storage
        _ensure_data_dir()
        with open(_get_conversation_path(conversation_id), 'w') as f:
            json.dump(conversation, f, indent=2)

    return conversation


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a conversation from storage.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        Conversation dict or None if not found
    """
    collection = get_conversations_collection()
    if collection is not None:
        # MongoDB storage
        doc = collection.find_one({"_id": conversation_id})
        if doc is None:
            return None
        return {k: v for k, v in doc.items() if k != "_id"}
    else:
        # JSON file storage
        path = _get_conversation_path(conversation_id)
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return json.load(f)


def save_conversation(conversation: Dict[str, Any]):
    """
    Save a conversation to storage.

    Args:
        conversation: Conversation dict to save
    """
    conversation_id = conversation['id']

    collection = get_conversations_collection()
    if collection is not None:
        # MongoDB storage
        doc = {**conversation, "_id": conversation_id}
        collection.replace_one(
            {"_id": conversation_id},
            doc,
            upsert=True
        )
    else:
        # JSON file storage
        _ensure_data_dir()
        with open(_get_conversation_path(conversation_id), 'w') as f:
            json.dump(conversation, f, indent=2)


def list_conversations() -> List[Dict[str, Any]]:
    """
    List all conversations (metadata only).

    Returns:
        List of conversation metadata dicts
    """
    conversations = []

    collection = get_conversations_collection()
    if collection is not None:
        # MongoDB storage
        cursor = collection.find(
            {},
            {"_id": 0, "id": 1, "created_at": 1, "title": 1, "messages": 1}
        )

        for doc in cursor:
            conversations.append({
                "id": doc["id"],
                "created_at": doc["created_at"],
                "title": doc.get("title", "New Conversation"),
                "message_count": len(doc.get("messages", []))
            })
    else:
        # JSON file storage
        _ensure_data_dir()
        for path in _DATA_DIR.glob("*.json"):
            try:
                with open(path, 'r') as f:
                    doc = json.load(f)
                    conversations.append({
                        "id": doc["id"],
                        "created_at": doc["created_at"],
                        "title": doc.get("title", "New Conversation"),
                        "message_count": len(doc.get("messages", []))
                    })
            except (json.JSONDecodeError, KeyError):
                continue

    # Sort by creation time, newest first
    conversations.sort(key=lambda x: x["created_at"], reverse=True)

    return conversations


def add_user_message(conversation_id: str, content: str):
    """
    Add a user message to a conversation.

    Args:
        conversation_id: Conversation identifier
        content: User message content
    """
    collection = get_conversations_collection()
    if collection is not None:
        # MongoDB storage
        result = collection.update_one(
            {"_id": conversation_id},
            {"$push": {"messages": {"role": "user", "content": content}}}
        )
        if result.matched_count == 0:
            raise ValueError(f"Conversation {conversation_id} not found")
    else:
        # JSON file storage
        conversation = get_conversation(conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")
        conversation["messages"].append({"role": "user", "content": content})
        save_conversation(conversation)


def add_assistant_message(
    conversation_id: str,
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any],
    rebuttals: Optional[List[Dict[str, Any]]] = None,
    devils_advocate: Optional[Dict[str, Any]] = None,
    debate_rounds: Optional[List[Dict[str, Any]]] = None
):
    """
    Add an assistant message with all stages to a conversation.

    Args:
        conversation_id: Conversation identifier
        stage1: List of individual model responses
        stage2: List of model rankings
        stage3: Final synthesized response
        rebuttals: Optional list of rebuttals from Tier 2 debate
        devils_advocate: Optional devil's advocate challenge
        debate_rounds: Optional list of debate round info
    """
    message = {
        "role": "assistant",
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3
    }

    # Add optional Tier 2 fields if present
    if rebuttals:
        message["rebuttals"] = rebuttals
    if devils_advocate:
        message["devils_advocate"] = devils_advocate
    if debate_rounds:
        message["debate_rounds"] = debate_rounds

    collection = get_conversations_collection()
    if collection is not None:
        # MongoDB storage
        result = collection.update_one(
            {"_id": conversation_id},
            {"$push": {"messages": message}}
        )
        if result.matched_count == 0:
            raise ValueError(f"Conversation {conversation_id} not found")
    else:
        # JSON file storage
        conversation = get_conversation(conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")
        conversation["messages"].append(message)
        save_conversation(conversation)


def update_conversation_title(conversation_id: str, title: str):
    """
    Update the title of a conversation.

    Args:
        conversation_id: Conversation identifier
        title: New title for the conversation
    """
    collection = get_conversations_collection()
    if collection is not None:
        # MongoDB storage
        result = collection.update_one(
            {"_id": conversation_id},
            {"$set": {"title": title}}
        )
        if result.matched_count == 0:
            raise ValueError(f"Conversation {conversation_id} not found")
    else:
        # JSON file storage
        conversation = get_conversation(conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")
        conversation["title"] = title
        save_conversation(conversation)
