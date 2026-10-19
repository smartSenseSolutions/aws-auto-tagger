"""
Data classes for AWS CloudTrail Resource Tagger

This module contains all dataclasses used as return types and data structures
throughout the application.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from .utils import env_field


@dataclass(frozen=True)
class Settings:
    """Runtime settings from environment variables, read when instantiated.

    ponytail: stdlib on purpose, the Lambda package has no dependency bundling
    (no pydantic-settings). Add type coercion here if a non-str setting shows up.
    """

    aws_region: str = env_field("AWS_REGION", "us-east-1")
    # IAM Identity Center directory for SSO owner_email lookup; empty = skip the lookup
    identity_store_id: str = env_field("IDENTITY_STORE_ID")
    identity_store_region: str = env_field("IDENTITY_STORE_REGION")


@dataclass
class TaggingStats:
    """Statistics from a tagging operation"""

    processed: int = 0
    tagged: int = 0
    errors: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.processed == 0:
            return 0.0
        return (self.tagged / self.processed) * 100

    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage"""
        if self.processed == 0:
            return 0.0
        return (self.errors / self.processed) * 100


@dataclass
class ResourceInfo:
    """Information about a discovered resource"""

    resource_type: str
    resource_id: str
    event_name: str
    username: str
    event_time: Optional[datetime] = None
    tagged: bool = False
    error_message: Optional[str] = None


@dataclass
class EventProcessingResult:
    """Result of processing CloudTrail events"""

    stats: TaggingStats
    resources: List[ResourceInfo]
    start_time: datetime
    end_time: datetime
    region: str

    @property
    def duration_seconds(self) -> float:
        """Calculate processing duration in seconds"""
        return (self.end_time - self.start_time).total_seconds()


@dataclass
class ExtractorConfig:
    """Configuration for resource extractors"""

    event_name: str
    resource_type: str
    section: str = "responseElements"
    simple_path: Optional[List[str]] = None
    array_path: Optional[List[str]] = None
    item_key: Optional[str] = None
    extraction_function: Optional[callable] = None


@dataclass
class CloudTrailEventSummary:
    """Summary of CloudTrail events retrieved"""

    total_events: int
    creation_events: int
    time_range_hours: int
    region: str
    start_time: datetime
    end_time: datetime


@dataclass
class TaggingConfig:
    """Configuration for resource tagging behavior"""

    owner_tag_name: str = "owner"
    creation_time_tag_name: str = "created_at"
    owner_email_tag_name: str = "owner_email"
    iam_email_tag_key: str = "EMAIL_ID"
    creation_time_format: str = "%Y-%m-%d %H:%M:%S UTC"
    include_creation_time: bool = True
    additional_tags: dict = None

    def __post_init__(self):
        if self.additional_tags is None:
            self.additional_tags = {}
