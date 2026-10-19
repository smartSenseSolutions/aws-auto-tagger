from src.data import TaggingConfig
from src.tagger import CloudTrailTagger


class StubIam:
    def __init__(self, tags=None, error=None):
        self.tags, self.error, self.calls = tags or [], error, 0

    def list_user_tags(self, UserName):
        self.calls += 1
        if self.error:
            raise self.error
        return {"Tags": self.tags}


def make_tagger(iam):
    t = CloudTrailTagger.__new__(CloudTrailTagger)  # skip real AWS client setup
    t.config, t.clients, t._email_cache = TaggingConfig(), {"iam": iam}, {}
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


def test_owner_email_ignores_session_names():
    # caller-chosen session names must not be trusted or looked up
    iam = StubIam(tags=[{"Key": "EMAIL_ID", "Value": "x@y.io"}])
    t = make_tagger(iam)
    assert t._owner_email(identity("AssumedRole", "alice@corp.com")) == "Unknown"
    assert t._owner_email(identity("AssumedRole", "bob")) == "Unknown"
    assert t._owner_email({}) == "Unknown"
    assert iam.calls == 0
