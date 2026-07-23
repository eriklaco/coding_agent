"""Conversation history helpers (sliding window for now; summarization later)."""

from coding_agent.config import MAX_HISTORY_MESSAGES


def trim_history[T](
    messages: list[T],
    *,
    max_messages: int = MAX_HISTORY_MESSAGES,
) -> list[T]:
    """Keep the system message and the most recent turns within *max_messages*.

    A real implementation would count tokens and/or summarize old turns instead
    of dropping them outright.
    """
    if len(messages) <= max_messages:
        return messages
    if not messages:
        return messages

    system = messages[0]
    keep = max_messages - 1
    return [system, *messages[-keep:]]
