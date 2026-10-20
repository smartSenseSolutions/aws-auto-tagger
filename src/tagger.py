"""
Simplified CloudTrail Resource Tagger - Clean and Concise

This replaces the original 450-line tagger.py with something much simpler.
"""

import json
import boto3
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from .services import get_service_config, tag_resource
from .clients import get_clients
from .utils import is_email, logger
from .data import (
    TaggingStats,
    ResourceInfo,
    EventProcessingResult,
    Settings,
    TaggingConfig,
)

# Identity Center creates its permission-set roles under this IAM path
SSO_ROLE_PATH = "role/aws-reserved/sso.amazonaws.com/"


class CloudTrailTagger:
    """Simplified CloudTrail Resource Tagger"""

    def __init__(
        self,
        region: str = "us-east-1",
        config: TaggingConfig = None,
        settings: Settings = None,
    ):
        self.region = region
        self.config = config or TaggingConfig()
        self.settings = settings or Settings()
        self.clients = get_clients(region)
        self._email_cache: Dict[str, str] = {}

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
            service_config = get_service_config(
                event_name, event.get("EventSource", "")
            )
            if not service_config:
                logger.debug(f"Skipping unsupported event: {event_name}")
                continue

            try:
                detail = json.loads(event.get("CloudTrailEvent", "{}"))
                if not isinstance(detail, dict):
                    raise ValueError("not a JSON object")
            except ValueError as e:
                logger.error(f"Invalid CloudTrailEvent JSON for {event_name}: {e}")
                continue

            # A failed create (e.g. AlreadyExists) still logs the requested name, which
            # can point at someone else's resource: never tag from failed calls.
            if detail.get("errorCode"):
                logger.debug(f"Skipping failed {event_name}: {detail['errorCode']}")
                continue

            # Extract resource IDs (can be multiple!)
            resource_ids = self._extract_resource_ids(detail, service_config)
            if not resource_ids:
                logger.debug(f"No resource IDs found in event: {event_name}")
                continue

            logger.info(
                f"Processing {event_name} by {username} - found {len(resource_ids)} resource(s)"
            )

            # Extract creation time from event
            creation_time = self._format_creation_time(event.get("EventTime"))
            owner_email = self._owner_email(detail.get("userIdentity", {}))

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
                    owner_email=owner_email,
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

    def _extract_resource_ids(self, detail: Dict, config: Dict) -> List[str]:
        """Extract resource IDs from the parsed CloudTrailEvent using JMESPath - much cleaner!"""
        import jmespath

        try:
            section = detail.get(config["section"], {})

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

    def _owner_email(self, identity: Dict) -> str:
        """IAM users and Identity Center (SSO) users only; everything else is Unknown.

        Takes CloudTrail `userIdentity`.
        - SSO: the session name is set by Identity Center (not the caller) for its
          reserved roles; the email comes from the user's Identity Store profile.
        - IAM user: the user name if it looks like an email, else a valid EMAIL_ID tag.
        Other assumed-role/federated session names are caller-chosen, so never trusted.
        """
        if identity.get("type") == "AssumedRole":
            issuer = identity.get("sessionContext", {}).get("sessionIssuer", {})
            session = identity.get("arn", "").rsplit("/", 1)[-1]
            # anchored: resource part must start with the reserved path (not just contain it)
            resource = issuer.get("arn", "").split(":", 5)[-1]
            if resource.startswith(SSO_ROLE_PATH) and resource.rsplit("/", 1)[
                -1
            ].startswith("AWSReservedSSO_"):
                key = f"sso:{session}"
                if key not in self._email_cache:
                    self._email_cache[key] = self._sso_email(session)
                return self._email_cache[key]
            return "Unknown"

        user = identity.get("userName")
        if identity.get("type") != "IAMUser" or not user:
            return "Unknown"
        if is_email(user):
            return user
        # cache by principal ARN (name only if CloudTrail omits it)
        key = identity.get("arn", user)
        if key not in self._email_cache:
            email = "Unknown"
            try:
                # ponytail: first page only, IAM caps users at 50 tags
                tags = self.clients["iam"].list_user_tags(UserName=user)["Tags"]
                tag = next(
                    (
                        t["Value"]
                        for t in tags
                        if t["Key"] == self.config.iam_email_tag_key
                    ),
                    "",
                )
                if is_email(tag):
                    email = tag
            except Exception as e:
                logger.debug(f"No IAM email lookup for {user}: {e}")
            self._email_cache[key] = email
        return self._email_cache[key]

    def _sso_email(self, username: str) -> str:
        """Primary email from the Identity Center user profile.

        Falls back to the session name if it looks like an email (lookup not
        configured or failed), else Unknown.
        """
        email = username if is_email(username) else "Unknown"
        store = self.settings.identity_store_id
        if not store:
            return email
        try:
            if "identitystore" not in self.clients:
                self.clients["identitystore"] = boto3.client(
                    "identitystore",
                    region_name=self.settings.identity_store_region or self.region,
                )
            ids = self.clients["identitystore"]
            user_id = ids.get_user_id(
                IdentityStoreId=store,
                AlternateIdentifier={
                    "UniqueAttribute": {
                        "AttributePath": "userName",
                        "AttributeValue": username,
                    }
                },
            )["UserId"]
            emails = ids.describe_user(IdentityStoreId=store, UserId=user_id)["Emails"]
            # primary first; first page only, a profile has a handful of emails
            for e in sorted(emails, key=lambda e: not e.get("Primary")):
                if is_email(e.get("Value", "")):
                    return e["Value"]
        except Exception as e:
            logger.debug(f"No Identity Store email lookup for {username}: {e}")
        return email

    def _empty_result(self, start_time: datetime) -> EventProcessingResult:
        """Create empty result"""
        return EventProcessingResult(
            stats=TaggingStats(),
            resources=[],
            start_time=start_time,
            end_time=datetime.now(timezone.utc),
            region=self.region,
        )
