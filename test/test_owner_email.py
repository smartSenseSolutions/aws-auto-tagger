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


def test_owner_email():
    iam = StubIam()
    assert make_tagger(iam)._owner_email("a@b.com") == "a@b.com"
    assert iam.calls == 0

    iam = StubIam(tags=[{"Key": "EMAIL_ID", "Value": "x@y.io"}])
    t = make_tagger(iam)
    assert t._owner_email("bob") == "x@y.io"
    assert t._owner_email("bob") == "x@y.io"
    assert iam.calls == 1  # cached

    assert make_tagger(StubIam(tags=[]))._owner_email("bob") == "Unknown"
    assert (
        make_tagger(StubIam(error=Exception("NoSuchEntity")))._owner_email("root")
        == "Unknown"
    )
