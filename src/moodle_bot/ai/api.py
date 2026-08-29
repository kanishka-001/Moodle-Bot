"""
Backward-compatibility module for ai.api.
All functionality is maintained in moodle_bot.ai.summarizer.
"""

from moodle_bot.ai.summarizer import (
    generate_notification,
    ai,
    file_url,
    tools,
    available_functions,
    get_ai_client,
)

__all__ = [
    "generate_notification",
    "ai",
    "file_url",
    "tools",
    "available_functions",
    "get_ai_client",
]
