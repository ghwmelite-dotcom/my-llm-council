"""MongoDB-based storage for conversations."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from .config import MONGODB_URI, MONGODB_DB_NAME

# MongoDB client (lazy initialization)
_client = None
_db = None


def get_db():
    """Get MongoDB database connection (lazy initialization)."""
    global _client, _db

    if _db is not None:
        return _db

    if not MONGODB_URI:
        raise ValueError(
            "MONGODB_URI environment variable not set. "
            "Please add your MongoDB connection string to Railway variables."
        )

    try:
        _client = MongoClient(MONGODB_URI)
        # Test connection
        _client.admin.command('ping')
        _db = _client[MONGODB_DB_NAME]
        print(f"Connected to MongoDB database: {MONGODB_DB_NAME}")
        return _db
    except ConnectionFailure as e:
        raise ConnectionFailure(f"Failed to connect to MongoDB: {e}")


def get_conversations_collection():
    """Get the conversations collection."""
    return get_db().conversations


def create_conversation(conversation_id: str) -> Dict[str, Any]:
    """
    Create a new conversation.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        New conversation dict
    """
    conversation = {
        "_id": conversation_id,
        "id": conversation_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Conversation",
        "messages": []
    }

    get_conversations_collection().insert_one(conversation)

    # Return without _id for API compatibility
    return {k: v for k, v in conversation.items() if k != "_id"}


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a conversation from storage.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        Conversation dict or None if not found
    """
    doc = get_conversations_collection().find_one({"_id": conversation_id})

    if doc is None:
        return None

    # Remove MongoDB _id field for API compatibility
    return {k: v for k, v in doc.items() if k != "_id"}


def save_conversation(conversation: Dict[str, Any]):
    """
    Save a conversation to storage.

    Args:
        conversation: Conversation dict to save
    """
    conversation_id = conversation['id']

    # Use _id as the MongoDB document ID
    doc = {**conversation, "_id": conversation_id}

    get_conversations_collection().replace_one(
        {"_id": conversation_id},
        doc,
        upsert=True
    )


def list_conversations() -> List[Dict[str, Any]]:
    """
    List all conversations (metadata only).

    Returns:
        List of conversation metadata dicts
    """
    conversations = []

    # Only fetch the fields we need for the list view
    cursor = get_conversations_collection().find(
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
    result = get_conversations_collection().update_one(
        {"_id": conversation_id},
        {"$push": {"messages": {"role": "user", "content": content}}}
    )

    if result.matched_count == 0:
        raise ValueError(f"Conversation {conversation_id} not found")


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

    result = get_conversations_collection().update_one(
        {"_id": conversation_id},
        {"$push": {"messages": message}}
    )

    if result.matched_count == 0:
        raise ValueError(f"Conversation {conversation_id} not found")


def update_conversation_title(conversation_id: str, title: str):
    """
    Update the title of a conversation.

    Args:
        conversation_id: Conversation identifier
        title: New title for the conversation
    """
    result = get_conversations_collection().update_one(
        {"_id": conversation_id},
        {"$set": {"title": title}}
    )

    if result.matched_count == 0:
        raise ValueError(f"Conversation {conversation_id} not found")
