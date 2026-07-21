from __future__ import annotations


# Canonical Codex JSONL item types that represent a tool or an external side
# effect.  Model-only stages use this set as a second, fail-closed guard after
# capability-level feature isolation.
TOOL_EVENT_ITEM_TYPES = frozenset(
    {
        "browser_use",
        "command_execution",
        "computer_use",
        "file_change",
        "image_generation",
        "mcp_tool_call",
        "web_search",
    }
)
