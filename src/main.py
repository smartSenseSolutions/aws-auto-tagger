"""
Simple Main Usage - Clean and Easy

This replaces the complex 200-line main.py with something much simpler.
"""

import os

from .tagger import CloudTrailTagger
from .utils import logger


def main(region="us-east-1", hours=24):
    """Simple main function"""

    # Optional: Configure logging level
    # setup_logger(level=logging.DEBUG)  # For more verbose output

    # Basic usage - just one line!
    logger.info("Starting CloudTrail Resource Tagger v1")
    tagger = CloudTrailTagger(region=region)
    result = tagger.run(hours=hours)

    logger.info(f"Tagging completed! Tagged {result.stats.tagged} resources")
    print(f"Tagged {result.stats.tagged} resources")


def handler(event, context):
    main(
        region=event.get("region", os.getenv("AWS_REGION", "us-east-1")),
        hours=event.get("hours", 24),
    )
    return {
        "statusCode": 200,
    }


if __name__ == "__main__":
    handler({}, {})
