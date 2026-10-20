import json

from src.data import Settings, TaggingConfig
from src.tagger import CloudTrailTagger


class StubIam:
    def __init__(self, tags=None, error=None):
        self.tags, self.error, self.calls = tags or [], error, 0

    def list_user_tags(self, UserName):
        self.calls += 1
        if self.error:
            raise self.error
        return {"Tags": self.tags}


def make_tagger(iam, identity_store_id=""):
    t = CloudTrailTagger.__new__(CloudTrailTagger)  # skip real AWS client setup
    t.config, t.clients, t._email_cache = TaggingConfig(), {"iam": iam}, {}
    t.settings = Settings(identity_store_id=identity_store_id)
    return t


def identity(type_, name):
    if type_ == "IAMUser":
        return {"type": type_, "userName": name, "arn": f"arn:aws:iam::1:user/{name}"}
    return {"type": type_}


def test_owner_email():
    iam = StubIam()
    assert make_tagger(iam)._owner_email(identity("IAMUser", "a@b.com")) == "a@b.com"
    assert iam.calls == 0

    iam = StubIam(tags=[{"Key": "EMAIL_ID", "Value": "x@y.io"}])
    t = make_tagger(iam)
    assert t._owner_email(identity("IAMUser", "bob")) == "x@y.io"
    assert t._owner_email(identity("IAMUser", "bob")) == "x@y.io"
    assert iam.calls == 1  # cached
    assert list(t._email_cache) == ["arn:aws:iam::1:user/bob"]  # keyed by ARN

    # invalid tag value, missing tag, IAM error -> Unknown
    bad = StubIam(tags=[{"Key": "EMAIL_ID", "Value": "bob"}])
    assert make_tagger(bad)._owner_email(identity("IAMUser", "bob")) == "Unknown"
    assert make_tagger(StubIam())._owner_email(identity("IAMUser", "bob")) == "Unknown"
    err = StubIam(error=Exception("NoSuchEntity"))
    assert make_tagger(err)._owner_email(identity("IAMUser", "bob")) == "Unknown"


def sso(session, issuer="role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_Admin_ab"):
    return {
        "type": "AssumedRole",
        "arn": f"arn:aws:sts::1:assumed-role/AWSReservedSSO_Admin_ab/{session}",
        "sessionContext": {"sessionIssuer": {"arn": f"arn:aws:iam::1:{issuer}"}},
    }


class StubIdentityStore:
    def __init__(self, emails=None, error=None):
        self.emails, self.error, self.calls = emails or [], error, 0

    def get_user_id(self, IdentityStoreId, AlternateIdentifier):
        self.calls += 1
        if self.error:
            raise self.error
        return {"UserId": "u-1"}

    def describe_user(self, IdentityStoreId, UserId):
        return {"Emails": self.emails}


def sso_tagger(ids):
    t = make_tagger(StubIam(), identity_store_id="d-123")
    t.clients["identitystore"] = ids
    return t


def test_owner_email_sso_profile():
    emails = [
        {"Value": "old@corp.com"},
        {"Value": "alice@corp.com", "Primary": True},
    ]
    ids = StubIdentityStore(emails=emails)
    t = sso_tagger(ids)
    assert t._owner_email(sso("alice")) == "alice@corp.com"  # primary wins
    assert t._owner_email(sso("alice")) == "alice@corp.com"
    assert ids.calls == 1  # cached

    # no valid email in profile / lookup fails -> email-shaped session name, else Unknown
    t = sso_tagger(StubIdentityStore(emails=[{"Value": "nope", "Primary": True}]))
    assert t._owner_email(sso("alice")) == "Unknown"
    t = sso_tagger(StubIdentityStore(error=Exception("ResourceNotFound")))
    assert t._owner_email(sso("a@b.com")) == "a@b.com"
    assert t._owner_email(sso("bob")) == "Unknown"


def test_owner_email_sso():
    # no IDENTITY_STORE_ID configured: email-shaped session name only
    t = make_tagger(StubIam())
    assert t._owner_email(sso("alice@corp.com")) == "alice@corp.com"
    assert t._owner_email(sso("alice")) == "Unknown"  # not an email
    # regional reserved path still counts as SSO
    regional = "role/aws-reserved/sso.amazonaws.com/eu-west-1/AWSReservedSSO_A_ab"
    assert t._owner_email(sso("a@b.com", regional)) == "a@b.com"


def test_owner_email_ignores_session_names():
    # caller-chosen session names must not be trusted or looked up
    iam = StubIam(tags=[{"Key": "EMAIL_ID", "Value": "x@y.io"}])
    t = make_tagger(iam)
    assert t._owner_email(sso("alice@corp.com", "role/my-role")) == "Unknown"
    # reserved path must be at the start, and the role name must be AWSReservedSSO_*
    nested = "role/x/role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_A_ab"
    assert t._owner_email(sso("alice@corp.com", nested)) == "Unknown"
    fake = "role/aws-reserved/sso.amazonaws.com/MyRole"
    assert t._owner_email(sso("alice@corp.com", fake)) == "Unknown"
    assert t._owner_email(identity("AssumedRole", "bob")) == "Unknown"
    assert t._owner_email({"type": "IAMUser"}) == "Unknown"  # no userName
    assert t._owner_email({}) == "Unknown"
    assert iam.calls == 0


def test_owner_email_account_setups():
    # IAM-only account, SSO not configured: no Identity Store client is ever created
    t = make_tagger(StubIam(tags=[{"Key": "EMAIL_ID", "Value": "x@y.io"}]))
    assert t._owner_email(identity("IAMUser", "bob")) == "x@y.io"
    assert "identitystore" not in t.clients

    # IAM + SSO in the same account and run: each resolves through its own path
    ids = StubIdentityStore(emails=[{"Value": "alice@corp.com", "Primary": True}])
    t = sso_tagger(ids)
    t.clients["iam"] = iam = StubIam(tags=[{"Key": "EMAIL_ID", "Value": "x@y.io"}])
    assert t._owner_email(identity("IAMUser", "bob")) == "x@y.io"
    assert t._owner_email(sso("alice")) == "alice@corp.com"
    assert (iam.calls, ids.calls) == (1, 1)


def test_settings_read_env_at_instantiation(monkeypatch):
    monkeypatch.setenv("IDENTITY_STORE_ID", "d-999")
    monkeypatch.delenv("AWS_REGION", raising=False)
    s = Settings()
    assert (s.identity_store_id, s.identity_store_region, s.aws_region) == (
        "d-999",
        "",
        "us-east-1",
    )


def test_run_skips_failed_events(monkeypatch):
    # a failed CreateLogGroup on an existing name must not re-tag that log group
    t = make_tagger(StubIam())
    t.region = "us-east-1"

    def event(error=None):
        detail = {"requestParameters": {"logGroupName": "victim"}, "userIdentity": {}}
        if error:
            detail["errorCode"] = error
        return {
            "EventName": "CreateLogGroup",
            "EventSource": "logs.amazonaws.com",
            "Username": "mallory",
            "CloudTrailEvent": json.dumps(detail),
        }

    tagged = []
    monkeypatch.setattr(
        "src.tagger.tag_resource", lambda *a, **k: tagged.append(a[2]) or True
    )
    t._get_events = lambda hours: [
        event("ResourceAlreadyExistsException"),
        event(),
    ]
    result = t.run()
    assert tagged == ["victim"]  # only the successful call
    assert result.stats.tagged == 1
