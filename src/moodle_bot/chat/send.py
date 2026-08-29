"""
Backward-compatibility wrapper for moodle_bot.chat.send.
Main logic is maintained in moodle_bot.chat.sender.
"""

from moodle_bot.chat.sender import send_message, send_msg

__all__ = ["send_message", "send_msg"]
