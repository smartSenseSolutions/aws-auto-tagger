"""
Cleanup reminders: tell each owner which of their resources are older than N days.

Optional: the Lambda does nothing while SLACK_TOKEN_PARAM is empty (see data.Settings).
Resources come from the Resource Groups Tagging API (everything carrying the created_at
tag), so no per-service code is needed. IAM principals aren't returned by that API.
"""

import sys
from collections import defaultdict
from datetime import datetime, timezone

import boto3

from .data import Settings, TaggingConfig
from .notifier import LogNotifier, Notifier
from .slack import Slack
from .utils import arn_type_and_name, is_email, logger


class Reminder:
    """Finds stale tagged resources and sends each owner their list via a Notifier"""

    MAX_ITEMS = 50  # per owner, keeps messages readable and well inside Slack limits

    def __init__(
        self,
        notifier: Notifier,
        min_age_days: int,
        template: str,
        config: TaggingConfig | None = None,
        now: datetime | None = None,
    ):
        self.notifier = notifier
        self.min_age_days = min_age_days
        self.template = template
        self.config = config or TaggingConfig()
        self.now = now or datetime.now(timezone.utc)

    def run(self, regions: list[str]) -> dict:
        resources = []
        for region in regions:
            tagging = boto3.client("resourcegroupstaggingapi", region_name=region)
            resources += self.find_stale(tagging, region)
        return self.notify(resources)

    def find_stale(self, tagging, region: str) -> list[dict]:
        """Resources in one region whose created_at tag is at least min_age_days old"""
        cfg, stale = self.config, []
        paginator = tagging.get_paginator("get_resources")
        for page in paginator.paginate(
            TagFilters=[{"Key": cfg.creation_time_tag_name}]
        ):
            for resource in page["ResourceTagMappingList"]:
                tags = {t["Key"]: t["Value"] for t in resource.get("Tags", [])}
                try:
                    created = datetime.strptime(
                        tags[cfg.creation_time_tag_name], cfg.creation_time_format
                    ).replace(tzinfo=timezone.utc)
                except (KeyError, ValueError):
                    continue  # created_at not written by the tagger
                age = (self.now - created).days
                if age >= self.min_age_days:
                    stale.append(
                        {
                            "arn": resource["ResourceARN"],
                            "region": region,
                            "age": age,
                            "owner": tags.get(cfg.owner_tag_name, "Unknown"),
                            "email": tags.get(cfg.owner_email_tag_name, ""),
                        }
                    )
        return stale

    def notify(self, resources: list[dict]) -> dict:
        """Send each owner (by owner_email) their resources; the rest go to the fallback"""
        stats = {
            "resources": len(resources),
            "owners_notified": 0,
            "fallback": 0,
            "errors": 0,
        }
        by_email, fallback = defaultdict(list), []
        for r in resources:
            (by_email[r["email"]] if is_email(r["email"]) else fallback).append(r)

        for email, items in by_email.items():
            header = self.template.format(count=len(items), days=self.min_age_days)
            try:
                if self.notifier.send_to_owner(
                    email, "\n".join([header, *self.lines(items)])
                ):
                    stats["owners_notified"] += 1
                else:
                    fallback.extend(items)  # not reachable on this channel
            except Exception as e:
                logger.error(f"Reminder to {email} failed: {e}")
                stats["errors"] += 1

        if fallback:
            stats["fallback"] = len(fallback)
            groups = defaultdict(list)
            for r in fallback:
                groups[(r["owner"], r["email"] or "no owner_email")].append(r)
            text = [
                f"AWS resources older than {self.min_age_days} days whose owner couldn't be reached:"
            ]
            for (owner, email), items in sorted(groups.items()):
                text += [f"*{owner}* ({email})", *self.lines(items)]
            try:
                self.notifier.send_fallback("\n".join(text))
            except Exception as e:
                logger.error(f"Fallback reminder failed: {e}")
                stats["errors"] += 1
        return stats

    def lines(self, resources: list[dict]) -> list[str]:
        """One bullet per resource, oldest first: days · region · type · name"""
        rows = sorted(resources, key=lambda r: -r["age"])
        out = []
        for r in rows[: self.MAX_ITEMS]:
            kind, name = arn_type_and_name(r["arn"])
            out.append(f"• {r['age']}d · {r['region']} · {kind} · {name}")
        if len(rows) > self.MAX_ITEMS:
            out.append(f"…and {len(rows) - self.MAX_ITEMS} more")
        return out


def handler(event, context):
    """Weekly Lambda entry point. event: {"dry_run": bool, "regions": "us-east-1,eu-west-1"}"""
    settings = Settings()
    if not settings.slack_token_param:
        logger.info("Slack reminders disabled (SLACK_TOKEN_PARAM not set)")
        return {"statusCode": 200, "disabled": True}

    if event.get("dry_run"):
        notifier = LogNotifier()
    else:
        ssm = boto3.client("ssm", region_name=settings.aws_region)
        param = ssm.get_parameter(Name=settings.slack_token_param, WithDecryption=True)
        notifier = Slack(param["Parameter"]["Value"], settings.slack_fallback_channel)

    regions = event.get("regions") or settings.slack_regions or settings.aws_region
    reminder = Reminder(
        notifier, int(settings.slack_min_age_days), settings.slack_message_template
    )
    stats = reminder.run([r.strip() for r in regions.split(",") if r.strip()])
    logger.info(f"Cleanup reminders: {stats}")
    return {"statusCode": 200, **stats}


if __name__ == "__main__":
    # local run: dry run unless --send is passed
    handler({"dry_run": "--send" not in sys.argv}, None)
