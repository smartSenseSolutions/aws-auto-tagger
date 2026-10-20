"""
Delivery interface for cleanup reminders, so the reminder logic doesn't depend on Slack.
"""

from abc import ABC, abstractmethod

from .utils import logger


class Notifier(ABC):
    """Delivers reminder text. Implementations: Slack (src/slack.py), LogNotifier (dry run)."""

    @abstractmethod
    def send_to_owner(self, email: str, text: str) -> bool:
        """Deliver to the person with this email; False if they can't be reached here"""

    @abstractmethod
    def send_fallback(self, text: str) -> None:
        """Deliver the resources whose owner couldn't be reached"""


class LogNotifier(Notifier):
    """Dry run: logs every message instead of sending it"""

    def send_to_owner(self, email: str, text: str) -> bool:
        logger.info(f"[dry run] to {email}:\n{text}")
        return True

    def send_fallback(self, text: str) -> None:
        logger.info(f"[dry run] fallback:\n{text}")
