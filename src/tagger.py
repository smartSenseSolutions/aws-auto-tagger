"""
Simplified CloudTrail Resource Tagger - Clean and Concise

This replaces the original 450-line tagger.py with something much simpler.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List
from .services import get_service_config, tag_resource
from .clients import get_clients
from .utils import logger
from .data import TaggingStats, ResourceInfo, EventProcessingResult, TaggingConfig


class CloudTrailTagger:
    """Simplified CloudTrail Resource Tagger"""

    def __init__(self, region: str = "us-east-1", config: TaggingConfig = None):
        self.region = region
        self.config = config or TaggingConfig()
        self.clients = get_clients(region)

    def run(self, hours: int = 24) -> EventProcessingResult:
        """Main execution - much simpler than before"""
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting CloudTrail resource tagging for region {self.region}")
        logger.info(f"Looking back {hours} hours for events")

        # Get events
        events = self._get_events(hours)
        if not events:
            logger.warning("No CloudTrail events found")
            return self._empty_result(start_time)

        logger.info(f"Found {len(events)} CloudTrail events to process")

        # Process events
        stats = TaggingStats()
        resources_info = []

        for event in events:
            stats.processed += 1
            event_name = event.get("EventName", "")
            username = event.get("Username", "Unknown")

            # Check if we support this event
            service_config = get_service_config(event_name)
            if not service_config:
                logger.debug(f"Skipping unsupported event: {event_name}")
                continue

            # Extract resource IDs (can be multiple!)
            resource_ids = self._extract_resource_ids(event, service_config)
            if not resource_ids:
                logger.debug(f"No resource IDs found in event: {event_name}")
                continue

            logger.info(
                f"Processing {event_name} by {username} - found {len(resource_ids)} resource(s)"
            )

            # Extract creation time from event
            creation_time = self._format_creation_time(event.get("EventTime"))

            # Tag each resource
            for resource_id in resource_ids:
                success = tag_resource(
                    service_config["eventsource"],
                    service_config["resource_type"],
                    resource_id,
                    username,
                    creation_time,
                    self.config,
                    self.clients,
                )

                # Track results
                if success:
                    stats.tagged += 1
                else:
                    stats.errors += 1

                resources_info.append(
                    ResourceInfo(
                        resource_type=service_config["resource_type"],
                        resource_id=resource_id,
                        event_name=event_name,
                        username=username,
                        event_time=event.get("EventTime"),
                        tagged=success,
                    )
                )

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Tagging completed in {duration:.2f} seconds")
        logger.info(
            f"Summary: {stats.processed} events processed, {stats.tagged} resources tagged, {stats.errors} errors"
        )

        return EventProcessingResult(
            stats=stats,
            resources=resources_info,
            start_time=start_time,
            end_time=end_time,
            region=self.region,
        )

    def _get_events(self, hours: int) -> List[Dict]:
        """Get CloudTrail events - simplified"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)

        logger.debug(f"Querying CloudTrail events from {start_time} to {end_time}")

        events = []
        paginator = self.clients["cloudtrail"].get_paginator("lookup_events")

        try:
            for page in paginator.paginate(
                StartTime=start_time,
                EndTime=end_time,
                LookupAttributes=[
                    {"AttributeKey": "ReadOnly", "AttributeValue": "false"}
                ],
            ):
                events.extend(page["Events"])
                logger.debug(f"Retrieved {len(page['Events'])} events from this page")
        except Exception as e:
            logger.error(f"Error fetching CloudTrail events: {e}")
            return []

        logger.debug(f"Total CloudTrail events retrieved: {len(events)}")
        return events

    def _extract_resource_ids(self, event: Dict, config: Dict) -> List[str]:
        """Extract resource IDs from event using JMESPath - much cleaner!"""
        import json
        import jmespath

        try:
            cloud_trail_event = json.loads(event.get("CloudTrailEvent", "{}"))
            section = cloud_trail_event.get(config["section"], {})

            # Use JMESPath for clean extraction
            result = jmespath.search(config["jmespath"], section)

            # Handle both single values and lists
            if isinstance(result, list):
                return [str(r) for r in result if r]
            elif result:
                return [str(result)]
            else:
                return []
        except Exception as e:
            logger.error(f"Error extracting with JMESPath: {e}")
            return []

    def _format_creation_time(
        self, event_time, time_format: str = "%Y-%m-%d %H:%M:%S UTC"
    ) -> str:
        """Format creation time from CloudTrail event to a given format"""
        if not event_time:
            return None

        try:
            if isinstance(event_time, datetime):
                return event_time.strftime(time_format)
            else:
                # Parse ISO format from CloudTrail
                parsed_time = datetime.fromisoformat(
                    str(event_time).replace("Z", "+00:00")
                )
                return parsed_time.strftime(time_format)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not format creation time {event_time}: {e}")
            return str(event_time)

    def _empty_result(self, start_time: datetime) -> EventProcessingResult:
        """Create empty result"""
        return EventProcessingResult(
            stats=TaggingStats(),
            resources=[],
            start_time=start_time,
            end_time=datetime.now(timezone.utc),
            region=self.region,
        )
