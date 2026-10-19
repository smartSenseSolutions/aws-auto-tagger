"""
Utilities for AWS CloudTrail Resource Tagger v1
"""

import logging
import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_email(value: str) -> bool:
    """True if value looks like an email address"""
    return bool(_EMAIL_RE.match(value))


# Configure logger for v1 package
def setup_logger(level=logging.INFO):
    """Setup logger for v1 package"""
    logger = logging.getLogger("")

    if not logger.handlers:  # Avoid duplicate handlers
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger


# Global logger instance for v1
logger = setup_logger()
