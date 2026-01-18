"""Wrapper for tracking voice interactions."""
from .statistics import ConversationStatistics

_statistics_tracker = ConversationStatistics()

def track_voice_interaction(*args, **kwargs):
    _statistics_tracker.add_conversation_result(*args, **kwargs)
