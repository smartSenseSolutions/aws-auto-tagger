"""
Slack implementation of the reminder Notifier.

ponytail: stdlib urllib on purpose, the Lambda package has no dependency bundling (no slack_sdk).
"""

import json
import urllib.error
import urllib.parse
import urllib.request

from .notifier import Notifier
from .utils import logger


class SlackError(Exception):
    """A Slack API call failed; args are (method, error code)"""


class Slack(Notifier):
    """Slack bot. Scopes needed: chat:write, users:read, users:read.email"""

    API_URL = "https://slack.com/api/"

    def __init__(self, token: str, fallback_channel: str = ""):
        self.token = token
        self.fallback_channel = fallback_channel

    def send_to_owner(self, email: str, text: str) -> bool:
        try:
            user_id = self.call("users.lookupByEmail", email=email)["user"]["id"]
        except SlackError as e:
            if e.args[1] == "users_not_found":
                return False
            raise
        self.post_message(user_id, text)  # a user ID as channel = DM from the app
        return True

    def send_fallback(self, text: str) -> None:
        if not self.fallback_channel:
            logger.info(f"No SLACK_FALLBACK_CHANNEL set, not posting:\n{text}")
            return
        self.post_message(self.fallback_channel, text)

    def post_message(self, channel: str, text: str) -> None:
        self.call("chat.postMessage", channel=channel, text=escape(text))

    def call(self, method: str, **params) -> dict:
        """POST a Web API method; raises SlackError unless ok.

        ponytail: no 429 retry, a weekly run sends few DMs; failures are counted in stats.
        """
        request = urllib.request.Request(
            self.API_URL + method,
            data=urllib.parse.urlencode(params).encode(),
            headers={"Authorization": f"Bearer {self.token}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                body = json.load(response)
        except urllib.error.HTTPError as e:
            raise SlackError(method, f"http_{e.code}") from e
        if not body.get("ok"):
            raise SlackError(method, body.get("error", "unknown_error"))
        return body


def escape(text: str) -> str:
    """Escape Slack mrkdwn control characters (keeps *bold* markup working)"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
