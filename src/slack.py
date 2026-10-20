"""
Slack implementation of the reminder Notifier.

ponytail: stdlib urllib on purpose, the Lambda package has no dependency bundling (no slack_sdk).
"""

import json
import time
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
        user_id = self.user_id_for_email(email)
        if user_id is None:
            return False
        self.post_message(user_id, text)  # a user ID as channel = DM from the app
        return True

    def send_fallback(self, text: str) -> None:
        if not self.fallback_channel:
            logger.info(f"No SLACK_FALLBACK_CHANNEL set, not posting:\n{text}")
            return
        self.post_message(self.fallback_channel, text)

    def user_id_for_email(self, email: str) -> str | None:
        """Slack user ID for an email, or None if no such user"""
        try:
            return self.call("users.lookupByEmail", email=email)["user"]["id"]
        except SlackError as e:
            if e.args[1] == "users_not_found":
                return None
            raise

    def post_message(self, channel: str, text: str) -> None:
        self.call("chat.postMessage", channel=channel, text=escape(text))

    def call(self, method: str, **params) -> dict:
        """POST a Web API method; retries once on HTTP 429, raises SlackError unless ok"""
        request = urllib.request.Request(
            self.API_URL + method,
            data=urllib.parse.urlencode(params).encode(),
            headers={"Authorization": f"Bearer {self.token}"},
        )
        for attempt in (1, 2):
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    body = json.load(response)
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt == 1:
                    time.sleep(int(e.headers.get("Retry-After", "1")))
                    continue
                raise SlackError(method, f"http_{e.code}") from e
            if not body.get("ok"):
                raise SlackError(method, body.get("error", "unknown_error"))
            return body
        raise SlackError(method, "ratelimited")


def escape(text: str) -> str:
    """Escape Slack mrkdwn control characters (keeps *bold* markup working)"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
