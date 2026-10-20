"""
Utilities for AWS CloudTrail Resource Tagger v1
"""

import logging
import os
import re
from dataclasses import field

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_email(value: str) -> bool:
    """True if value looks like an email address"""
    return bool(_EMAIL_RE.match(value))


def env_field(name: str, default: str = ""):
    """Dataclass field read from env var `name` when the dataclass is instantiated.

    Empty counts as unset: serverless.yml passes unset vars through as ''.
    """
    return field(default_factory=lambda: os.getenv(name) or default)


def arn_type_and_name(arn: str) -> tuple[str, str]:
    """('ec2:instance', 'i-0abc') from an ARN; ('s3', 'my-bucket') when there's no type part"""
    parts = arn.split(":", 5)
    service, resource = parts[2], parts[5] if len(parts) == 6 else ""
    head, *rest = re.split(r"[/:]", resource, maxsplit=1)
    return (f"{service}:{head}", rest[0]) if rest else (service, head)


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
