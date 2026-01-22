"""Plugin hook definitions."""

from enum import Enum


class PluginHook(str, Enum):
    """Available plugin hook points."""

    # Pre-processing hooks
    ON_QUERY_RECEIVED = "on_query_received"

    # Stage hooks
    ON_STAGE1_COMPLETE = "on_stage1_complete"
    ON_STAGE2_COMPLETE = "on_stage2_complete"
    ON_SYNTHESIS_COMPLETE = "on_synthesis_complete"

    # Post-processing hooks
    ON_RESPONSE_COMPLETE = "on_response_complete"


# Hook descriptions for documentation
HOOK_DESCRIPTIONS = {
    PluginHook.ON_QUERY_RECEIVED: "Called when a user query is received. Can modify the query before processing.",
    PluginHook.ON_STAGE1_COMPLETE: "Called after Stage 1 (individual responses) is complete. Can modify responses.",
    PluginHook.ON_STAGE2_COMPLETE: "Called after Stage 2 (rankings) is complete. Can modify rankings.",
    PluginHook.ON_SYNTHESIS_COMPLETE: "Called after Stage 3 (synthesis) is complete. Can modify the final answer.",
    PluginHook.ON_RESPONSE_COMPLETE: "Called when the full response is ready. Can add metadata or transform output.",
}
