import boto3
import pytest
from botocore.awsrequest import AWSResponse

from src.data import TaggingConfig
from src.services import (
    CLOUDTRAIL_SOURCES,
    SERVICE_CONFIGS,
    get_service_config,
    tag_resource,
)

EVENTS = [
    (key, name, cfg)
    for key, events in SERVICE_CONFIGS.items()
    for name, cfg in events.items()
]
IDS = [f"{key}:{name}" for key, name, _ in EVENTS]


def cloudtrail_source(key):
    return f"{CLOUDTRAIL_SOURCES.get(key, key)}.amazonaws.com"


@pytest.mark.parametrize("key,name,cfg", EVENTS, ids=IDS)
def test_event_resolves_to_its_own_service(key, name, cfg):
    assert get_service_config(name, cloudtrail_source(key)) is cfg


def test_shared_event_names_use_event_source():
    # CreateCluster exists for eks, ecs, redshift, kafka and memorydb
    for key in ["eks", "ecs", "redshift", "kafka", "memorydb"]:
        cfg = get_service_config("CreateCluster", cloudtrail_source(key))
        assert cfg["eventsource"] == key
    assert (
        get_service_config("CreateTable", "glue.amazonaws.com")["eventsource"] == "glue"
    )
    assert get_service_config("CreateCluster", "other.amazonaws.com") is None


@pytest.fixture(scope="module")
def aws():
    """Real boto3 clients whose calls stop right after botocore validates the params."""
    calls = []

    def short_circuit(model, **_):
        calls.append(model.name)
        return AWSResponse("https://test", 200, {}, None), {}

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("AWS_ACCESS_KEY_ID", "test")
        mp.setenv("AWS_SECRET_ACCESS_KEY", "test")
        clients = {}
        for key in SERVICE_CONFIGS:
            clients[key] = boto3.client(key, region_name="us-east-1")
            clients[key].meta.events.register("before-call", short_circuit)
        clients |= {"region": "us-east-1", "account_id": "123456789012"}
        yield clients, calls


@pytest.mark.parametrize("key,name,cfg", EVENTS, ids=IDS)
def test_tag_resource_calls_a_valid_api(key, name, cfg, aws):
    # catches missing match/case branches, wrong client names, methods and params
    clients, calls = aws
    calls.clear()
    # botocore validates S3 bucket names; everything else accepts an ARN-shaped id
    resource_id = (
        "test-bucket"
        if key == "s3"
        else "arn:aws:svc:us-east-1:123456789012:thing/test-resource"
    )
    ok = tag_resource(
        cfg["eventsource"],
        cfg["resource_type"],
        resource_id,
        "alice",
        "2026-01-01 00:00:00 UTC",
        TaggingConfig(),
        clients,
        owner_email="alice@corp.com",
    )
    assert ok and calls
