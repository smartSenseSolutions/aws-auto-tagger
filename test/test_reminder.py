from datetime import datetime, timezone

import pytest

from src import reminder as reminder_module
from src.data import Settings
from src.notifier import LogNotifier, Notifier
from src.reminder import Reminder
from src.slack import Slack, SlackError
from src.utils import arn_type_and_name

NOW = datetime(2026, 1, 31, tzinfo=timezone.utc)


def resource(arn, created_at=None, owner="alice", email="alice@corp.com"):
    tags = {"owner": owner}
    if created_at:
        tags["created_at"] = created_at
    if email is not None:
        tags["owner_email"] = email
    return {
        "ResourceARN": arn,
        "Tags": [{"Key": k, "Value": v} for k, v in tags.items()],
    }


class StubTagging:
    def __init__(self, resources):
        self.resources, self.filters = resources, None

    def get_paginator(self, name):
        assert name == "get_resources"
        return self

    def paginate(self, TagFilters):
        self.filters = TagFilters
        yield {"ResourceTagMappingList": self.resources}


class RecordingNotifier(Notifier):
    def __init__(self, reachable=()):
        self.reachable, self.sent, self.fallback = set(reachable), {}, []

    def send_to_owner(self, email, text):
        if email not in self.reachable:
            return False
        self.sent[email] = text
        return True

    def send_fallback(self, text):
        self.fallback.append(text)


def stale(arn, age, email="alice@corp.com", owner="alice", region="us-east-1"):
    return {"arn": arn, "region": region, "age": age, "owner": owner, "email": email}


def test_find_stale_filters_by_age_and_tag_format():
    tagging = StubTagging(
        [
            resource(
                "arn:aws:ec2:us-east-1:1:instance/i-old", "2026-01-01 10:00:00 UTC"
            ),
            resource(
                "arn:aws:ec2:us-east-1:1:instance/i-new", "2026-01-30 10:00:00 UTC"
            ),
            resource("arn:aws:s3:::not-ours", "yesterday"),  # foreign created_at format
            resource("arn:aws:s3:::untagged"),  # no created_at at all
        ]
    )
    found = Reminder(LogNotifier(), 7, "", now=NOW).find_stale(tagging, "us-east-1")
    assert tagging.filters == [{"Key": "created_at"}]
    assert found == [stale("arn:aws:ec2:us-east-1:1:instance/i-old", 29)]


def test_notify_dms_owners_and_falls_back():
    notifier = RecordingNotifier(reachable={"alice@corp.com"})
    resources = [
        stale("arn:aws:ec2:us-east-1:1:instance/i-1", 9),
        stale("arn:aws:rds:eu-west-1:1:db:test-db", 42, region="eu-west-1"),
        stale(
            "arn:aws:s3:::bob-bucket", 10, email="bob@corp.com", owner="bob"
        ),  # not in Slack
        stale("arn:aws:s3:::role-bucket", 8, email="Unknown", owner="deploy-role"),
        stale(
            "arn:aws:s3:::old-bucket", 30, email="", owner="carol"
        ),  # tagged pre owner_email
    ]
    template = "You have {count} resources older than {days} days:"
    stats = Reminder(notifier, 7, template, now=NOW).notify(resources)

    assert notifier.sent["alice@corp.com"].splitlines() == [
        "You have 2 resources older than 7 days:",
        "• 42d · eu-west-1 · rds:db · `test-db`",  # oldest first
        "• 9d · us-east-1 · ec2:instance · `i-1`",
    ]
    (fallback,) = notifier.fallback
    assert "*bob* (bob@corp.com)" in fallback
    assert "*deploy-role* (Unknown)" in fallback
    assert "*carol* (no owner_email)" in fallback
    assert "• 30d · us-east-1 · s3 · `old-bucket`" in fallback
    assert stats == {"resources": 5, "owners_notified": 1, "fallback": 3, "errors": 0}


def test_notify_counts_errors_and_continues():
    class Broken(RecordingNotifier):
        def send_to_owner(self, email, text):
            raise SlackError("chat.postMessage", "channel_not_found")

    stats = Reminder(Broken(), 7, "{count}", now=NOW).notify(
        [stale("arn:aws:s3:::b", 9)]
    )
    assert stats["errors"] == 1 and stats["owners_notified"] == 0


def test_lines_cap():
    resources = [stale(f"arn:aws:s3:::b{i}", 10 + i) for i in range(55)]
    lines = Reminder(LogNotifier(), 7, "", now=NOW).lines(resources)
    assert len(lines) == Reminder.MAX_ITEMS + 1
    assert lines[0].startswith("• 64d") and lines[-1] == "…and 5 more"


@pytest.mark.parametrize(
    "arn,expected",
    [
        ("arn:aws:ec2:us-east-1:1:instance/i-0abc", ("ec2:instance", "i-0abc")),
        ("arn:aws:s3:::my-bucket", ("s3", "my-bucket")),
        ("arn:aws:rds:us-east-1:1:db:test-db", ("rds:db", "test-db")),
        (
            "arn:aws:logs:us-east-1:1:log-group:/aws/lambda/x",
            ("logs:log-group", "/aws/lambda/x"),
        ),
    ],
)
def test_arn_type_and_name(arn, expected):
    assert arn_type_and_name(arn) == expected


def test_slack_notifier(monkeypatch):
    calls = []

    def fake_call(self, method, **params):
        calls.append((method, params))
        if method == "users.lookupByEmail":
            if params["email"] == "ghost@corp.com":
                raise SlackError(method, "users_not_found")
            return {"ok": True, "user": {"id": "U123"}}
        return {"ok": True}

    monkeypatch.setattr(Slack, "call", fake_call)
    slack = Slack("xoxb-test")
    assert isinstance(slack, Notifier)
    assert slack.send_to_owner("alice@corp.com", "a <b> & c") is True
    assert calls[-1] == (
        "chat.postMessage",
        {"channel": "U123", "text": "a &lt;b&gt; &amp; c"},
    )
    assert slack.send_to_owner("ghost@corp.com", "x") is False

    calls.clear()
    slack.send_fallback("nobody")  # no fallback channel: logged, not posted
    assert calls == []
    Slack("xoxb-test", "#aws-cleanup").send_fallback("list")
    assert calls == [("chat.postMessage", {"channel": "#aws-cleanup", "text": "list"})]


def test_handler_disabled_without_token_param(monkeypatch):
    monkeypatch.delenv("SLACK_TOKEN_PARAM", raising=False)
    monkeypatch.setattr(reminder_module.boto3, "client", pytest.fail)  # no AWS calls
    assert reminder_module.handler({}, None) == {"statusCode": 200, "disabled": True}


def test_handler_dry_run(monkeypatch):
    monkeypatch.setenv("SLACK_TOKEN_PARAM", "/aws-tagger/slack-bot-token")
    monkeypatch.setenv("SLACK_REGIONS", "us-east-1, eu-west-1")
    created = []

    def fake_client(service, region_name):
        assert (
            service == "resourcegroupstaggingapi"
        )  # dry run never reads the SSM token
        created.append(region_name)
        return StubTagging(
            [resource(f"arn:aws:s3:::b-{region_name}", "2020-01-01 00:00:00 UTC")]
        )

    monkeypatch.setattr(reminder_module.boto3, "client", fake_client)
    result = reminder_module.handler({"dry_run": True}, None)
    assert created == ["us-east-1", "eu-west-1"]
    assert result["resources"] == 2 and result["owners_notified"] == 1


def test_settings_empty_env_uses_default(monkeypatch):
    monkeypatch.setenv("SLACK_MIN_AGE_DAYS", "")  # serverless passes unset vars as ''
    monkeypatch.setenv("SLACK_MESSAGE_TEMPLATE", "")
    s = Settings()
    assert s.slack_min_age_days == "7"
    assert "{count}" in s.slack_message_template


def test_slack_call_transport(monkeypatch):
    import io
    import json
    import urllib.error

    import src.slack as slack_module

    responses = [
        io.BytesIO(json.dumps({"ok": True, "user": {"id": "U1"}}).encode()),
        io.BytesIO(json.dumps({"ok": False, "error": "invalid_auth"}).encode()),
        urllib.error.HTTPError("u", 429, "slow down", {}, None),
    ]
    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        r = responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(slack_module.urllib.request, "urlopen", fake_urlopen)
    slack = Slack("xoxb-test")
    assert slack.call("users.lookupByEmail", email="a@b.com")["user"]["id"] == "U1"
    assert requests[0].headers["Authorization"] == "Bearer xoxb-test"
    with pytest.raises(SlackError, match="invalid_auth"):
        slack.call("chat.postMessage", channel="C1", text="x")
    with pytest.raises(SlackError, match="http_429"):
        slack.call("chat.postMessage", channel="C1", text="x")


def test_names_are_inline_code_so_urls_dont_link():
    # a bare domain in a name would be auto-linked by Slack; backticks can't break out
    r = stale("arn:aws:logs:us-east-1:1:log-group:a`phish.example.com", 9)
    (line,) = Reminder(LogNotifier(), 7, "", now=NOW).lines([r])
    assert line == "• 9d · us-east-1 · logs:log-group · `a'phish.example.com`"
