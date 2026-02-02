"""
Simple AWS Client Management
"""

import boto3
from .utils import logger
from .services import SERVICE_CONFIGS


def get_clients(region: str) -> dict:
    """Get all AWS clients - simple and clean"""

    logger.debug(f"Initializing AWS clients for region: {region}")

    try:
        # Get account ID once
        sts = boto3.client("sts")
        account_id = sts.get_caller_identity()["Account"]
        logger.debug(f"Using AWS account: {account_id}")

        client_keys = list(SERVICE_CONFIGS.keys())

        return {
            client_key: boto3.client(client_key, region_name=region)
            for client_key in client_keys
        } | {
            "cloudtrail": boto3.client("cloudtrail", region_name=region),
            # Metadata
            "region": region,
            "account_id": account_id,
        }

    except Exception as e:
        logger.error(f"Failed to initialize AWS clients: {e}")
        raise
