"""Temporary image storage for multimodal inputs."""

import os
import uuid
import base64
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

from ..config import data_path


UPLOAD_DIR = Path(data_path("uploads"))
METADATA_FILE = UPLOAD_DIR / "metadata.json"
MAX_AGE_HOURS = 24  # Images expire after 24 hours
MAX_SIZE_MB = 10  # Maximum image size


@dataclass
class StoredImage:
    """Represents a stored image."""
    id: str
    filename: str
    content_type: str
    size_bytes: int
    created_at: str
    base64_data: str


def _ensure_upload_dir():
    """Ensure the upload directory exists."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _load_metadata() -> Dict[str, Any]:
    """Load metadata from JSON file."""
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"images": {}}
    return {"images": {}}


def _save_metadata(metadata: Dict[str, Any]):
    """Save metadata to JSON file."""
    _ensure_upload_dir()
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)


def store_image(
    content: bytes,
    filename: str,
    content_type: str
) -> Optional[StoredImage]:
    """
    Store an uploaded image.

    Args:
        content: Image bytes
        filename: Original filename
        content_type: MIME type (e.g., "image/jpeg")

    Returns:
        StoredImage object or None if failed
    """
    _ensure_upload_dir()

    # Validate size
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        return None

    # Validate content type
    allowed_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    if content_type not in allowed_types:
        return None

    # Generate unique ID
    image_id = str(uuid.uuid4())

    # Convert to base64
    base64_data = base64.b64encode(content).decode('utf-8')

    # Create stored image record
    stored_image = StoredImage(
        id=image_id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(content),
        created_at=datetime.utcnow().isoformat(),
        base64_data=base64_data
    )

    # Save metadata
    metadata = _load_metadata()
    metadata["images"][image_id] = asdict(stored_image)
    _save_metadata(metadata)

    return stored_image


def get_image(image_id: str) -> Optional[StoredImage]:
    """
    Retrieve a stored image.

    Args:
        image_id: The image ID

    Returns:
        StoredImage object or None if not found
    """
    metadata = _load_metadata()
    image_data = metadata.get("images", {}).get(image_id)

    if image_data:
        return StoredImage(**image_data)
    return None


def delete_image(image_id: str) -> bool:
    """
    Delete a stored image.

    Args:
        image_id: The image ID

    Returns:
        True if deleted, False if not found
    """
    metadata = _load_metadata()
    if image_id in metadata.get("images", {}):
        del metadata["images"][image_id]
        _save_metadata(metadata)
        return True
    return False


def cleanup_old_images() -> int:
    """
    Remove images older than MAX_AGE_HOURS.

    Returns:
        Number of images removed
    """
    metadata = _load_metadata()
    cutoff = datetime.utcnow() - timedelta(hours=MAX_AGE_HOURS)

    to_delete = []
    for image_id, image_data in metadata.get("images", {}).items():
        created = datetime.fromisoformat(image_data["created_at"])
        if created < cutoff:
            to_delete.append(image_id)

    for image_id in to_delete:
        del metadata["images"][image_id]

    if to_delete:
        _save_metadata(metadata)

    return len(to_delete)


def get_data_url(image: StoredImage) -> str:
    """
    Get the data URL for an image.

    Args:
        image: StoredImage object

    Returns:
        Data URL string for use in API calls
    """
    return f"data:{image.content_type};base64,{image.base64_data}"
