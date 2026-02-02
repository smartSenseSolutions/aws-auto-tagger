#!/usr/bin/env python3
"""
Test function for tagging specific AWS resources
Usage: python ts.py <service> <resource_id> <username> [region]
"""

import sys
from datetime import datetime, timezone
from src.clients import get_clients
from src.services import tag_resource
from src.utils import logger
from src.data import TaggingConfig


def test_tag_resource(
    service: str,
    username: str = "test-user",
    region: str = "us-east-1",
    hours: int = 24,
):
    """
    Test tagging for resources found in CloudTrail events

    Args:
        service: AWS service name (ec2, lambda, s3, etc.)
        username: Username for owner tag (default: test-user)
        region: AWS region (default: us-east-1)
        hours: Hours to look back in CloudTrail (default: 24)
    """

    try:
        # Get AWS clients
        clients = get_clients(region)

        # Get CloudTrail events for the specified service
        events = _get_cloudtrail_events(clients, service, hours)

        if not events:
            logger.warning(f"No CloudTrail events found for service: {service}")
            return False

        logger.info(f"Found {len(events)} CloudTrail events for {service}")

        # Process each event and extract resource IDs
        resources_found = []

        for event in events:
            event_name = event.get("EventName", "")
            event_username = event.get("Username", username)
            creation_time = _format_creation_time(event.get("EventTime"))

            # Get service config for this event
            from src.services import get_service_config

            service_config = get_service_config(event_name)

            if not service_config:
                logger.debug(f"No service config for event: {event_name}")
                continue

            # Extract resource IDs from the event
            resource_ids = _extract_resource_ids_from_event(event, service_config)

            if resource_ids:
                for resource_id in resource_ids:
                    resources_found.append(
                        {
                            "resource_id": resource_id,
                            "resource_type": service_config["resource_type"],
                            "event_name": event_name,
                            "username": event_username,
                            "creation_time": creation_time,
                        }
                    )

        if not resources_found:
            logger.warning(f"No resources found in CloudTrail events for {service}")
            return False

        logger.info(f"Found {len(resources_found)} resources to tag")

        # Tag each resource found
        success_count = 0
        for resource in resources_found:
            logger.info(
                f"Tagging {resource['resource_type']}:{resource['resource_id']}"
            )

            # Determine the correct eventsource from resource_type
            eventsource_map = {
                "ec2:instance": "ec2",
                "ec2:volume": "ec2",
                "ec2:security-group": "ec2",
                "ec2:vpc": "ec2",
                "ec2:subnet": "ec2",
                "ec2:snapshot": "ec2",
                "ec2:image": "ec2",
                "ec2:elastic-ip": "ec2",
                "lambda:function": "lambda",
                "s3:bucket": "s3",
                "rds:db": "rds",
                "rds:cluster": "rds",
                "eks:cluster": "eks",
                "eks:nodegroup": "eks",
                "elbv2:loadbalancer": "elbv2",
                "elbv2:targetgroup": "elbv2",
                "dynamodb:table": "dynamodb",
                "kms:key": "kms",
                "kms:alias": "kms",
                "secretsmanager:secret": "secretsmanager",
                "sns:topic": "sns",
                "sqs:queue": "sqs",
                "cloudwatch:loggroup": "cloudwatch",
                "cloudwatch:alarm": "cloudwatch",
                "route53:hostedzone": "route53",
                "apigateway:restapi": "apigateway",
                "apigateway:apikey": "apigateway",
                "ecs:cluster": "ecs",
                "ecs:service": "ecs",
                "ecr:repository": "ecr",
                "stepfunctions:statemachine": "stepfunctions",
                "cloudformation:stack": "cloudformation",
                "efs:filesystem": "efs",
                "opensearch:domain": "opensearch",
                "redshift:cluster": "redshift",
                "cognito:userpool": "cognito-idp",
                "cognito:identitypool": "cognito-identity",
                "amplify:app": "amplify",
                "cloudfront:distribution": "cloudfront",
                "glue:database": "glue",
                "glue:table": "glue",
                "bedrock:model": "bedrock",
                "iam:role": "iam",
                "iam:user": "iam",
                "iam:policy": "iam",
            }

            correct_eventsource = eventsource_map.get(
                resource["resource_type"], service
            )

            success = tag_resource(
                eventsource=correct_eventsource,
                resource_type=resource["resource_type"],
                resource_id=resource["resource_id"],
                username=resource["username"],
                creation_time=resource["creation_time"],
                clients=clients,
                config=TaggingConfig(),
            )

            if success:
                success_count += 1
                logger.info(f"✅ Successfully tagged {resource['resource_id']}")
            else:
                logger.error(f"❌ Failed to tag {resource['resource_id']}")

        logger.info(
            f"Tagging test completed: {success_count}/{len(resources_found)} resources tagged successfully"
        )
        return success_count > 0

    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False


def _get_cloudtrail_events(clients, service: str, hours: int):
    """Get CloudTrail events for a specific service"""
    from datetime import datetime, timedelta

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    logger.debug(
        f"Querying CloudTrail events for {service} from {start_time} to {end_time}"
    )

    events = []
    paginator = clients["cloudtrail"].get_paginator("lookup_events")

    try:
        for page in paginator.paginate(
            StartTime=start_time,
            EndTime=end_time,
            LookupAttributes=[
                {"AttributeKey": "ReadOnly", "AttributeValue": "false"},
                {
                    "AttributeKey": "EventSource",
                    "AttributeValue": f"{service}.amazonaws.com",
                },
            ],
        ):
            events.extend(page["Events"])
            logger.debug(f"Retrieved {len(page['Events'])} events from this page")
    except Exception as e:
        logger.error(f"Error fetching CloudTrail events: {e}")
        return []

    return events


def _extract_resource_ids_from_event(event, service_config):
    """Extract resource IDs from CloudTrail event using JMESPath"""
    import json
    import jmespath

    try:
        cloud_trail_event = json.loads(event.get("CloudTrailEvent", "{}"))
        section = cloud_trail_event.get(service_config["section"], {})

        # Use JMESPath for clean extraction
        result = jmespath.search(service_config["jmespath"], section)

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


def _format_creation_time(event_time):
    """Format creation time from CloudTrail event"""
    if not event_time:
        return None

    try:
        if isinstance(event_time, datetime):
            return event_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            # Parse ISO format from CloudTrail
            parsed_time = datetime.fromisoformat(str(event_time).replace("Z", "+00:00"))
            return parsed_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not format creation time {event_time}: {e}")
        return str(event_time)


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python ts.py <service> [username] [region] [hours]")
        print("\nExamples:")
        print("  python ts.py lambda")
        print("  python ts.py ec2 john")
        print("  python ts.py s3 john us-west-2")
        print("  python ts.py lambda john us-east-1 48")
        print("\nSupported services:")
        print("  ec2, lambda, s3, rds, eks, elbv2, dynamodb, kms, secretsmanager")
        print("  sns, sqs, cloudwatch, route53, apigateway, ecs, ecr, stepfunctions")
        print(
            "  cloudformation, efs, opensearch, redshift, cognito-idp, cognito-identity"
        )
        print("  amplify, cloudfront, glue, bedrock, iam")
        sys.exit(1)

    service = sys.argv[1]
    username = sys.argv[2] if len(sys.argv) > 2 else "test-user"
    region = sys.argv[3] if len(sys.argv) > 3 else "us-east-1"
    hours = int(sys.argv[4]) if len(sys.argv) > 4 else 24

    success = test_tag_resource(service, username, region, hours)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
