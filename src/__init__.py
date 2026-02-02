"""
AWS CloudTrail Resource Tagger v1 - Simplified and Clean

This version uses JMESPath for clean resource extraction and
is much simpler than the original complex implementation.
"""

from .tagger import CloudTrailTagger
from .services import get_supported_events
from .utils import logger, setup_logger

__version__ = "1.0.0"
__all__ = [
    "CloudTrailTagger",
    "get_supported_events",
    "logger",
    "setup_logger",
]
