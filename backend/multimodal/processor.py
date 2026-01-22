"""Process multimodal messages for different models."""

from typing import List, Dict, Any, Optional
from .storage import StoredImage, get_image, get_data_url


# Models that support vision/image inputs
VISION_CAPABLE_MODELS = {
    'openai/gpt-4o',
    'openai/gpt-4o-mini',
    'anthropic/claude-sonnet-4.5',
    'anthropic/claude-3.5-haiku',
    'google/gemini-2.5-pro',
    'google/gemini-2.5-flash',
    'x-ai/grok-2',
}


def is_vision_capable(model: str) -> bool:
    """
    Check if a model supports vision/image inputs.

    Args:
        model: OpenRouter model identifier

    Returns:
        True if model supports images
    """
    return model in VISION_CAPABLE_MODELS


def prepare_multimodal_messages(
    messages: List[Dict[str, Any]],
    image_ids: List[str],
    model: str
) -> List[Dict[str, Any]]:
    """
    Prepare messages with image content for a model.

    For vision-capable models, images are included in the message.
    For text-only models, a note about images is added instead.

    Args:
        messages: Original message list
        image_ids: List of image IDs to include
        model: Target model identifier

    Returns:
        Modified messages list
    """
    if not image_ids:
        return messages

    # Get the images
    images = []
    for image_id in image_ids:
        image = get_image(image_id)
        if image:
            images.append(image)

    if not images:
        return messages

    # Find the last user message to modify
    modified_messages = messages.copy()

    for i in range(len(modified_messages) - 1, -1, -1):
        if modified_messages[i].get('role') == 'user':
            original_content = modified_messages[i].get('content', '')

            if is_vision_capable(model):
                # Create multimodal content array
                content_parts = [
                    {"type": "text", "text": original_content}
                ]

                for image in images:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": get_data_url(image),
                            "detail": "auto"
                        }
                    })

                modified_messages[i] = {
                    "role": "user",
                    "content": content_parts
                }
            else:
                # For text-only models, add a note about the images
                image_note = f"\n\n[Note: The user has also provided {len(images)} image(s) with this query, but this model cannot view images. Please respond based on the text content only.]"
                modified_messages[i] = {
                    "role": "user",
                    "content": original_content + image_note
                }

            break

    return modified_messages


def get_image_summary(image_ids: List[str]) -> str:
    """
    Get a summary of attached images for logging/display.

    Args:
        image_ids: List of image IDs

    Returns:
        Summary string
    """
    images = []
    for image_id in image_ids:
        image = get_image(image_id)
        if image:
            images.append(image)

    if not images:
        return ""

    total_size = sum(img.size_bytes for img in images) / 1024  # KB
    return f"{len(images)} image(s), {total_size:.1f} KB total"
