"""Slack Connector using jbcom ecosystem packages."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from time import sleep
from typing import Any, Iterator, Optional, Union

# batched was added in Python 3.12
if sys.version_info >= (3, 12):
    from itertools import batched
else:
    from itertools import islice

    def batched(iterable, n: int) -> Iterator[tuple]:
        """Batch an iterable into chunks of size n (Python 3.9+ compatible)."""
        it = iter(iterable)
        while batch := tuple(islice(it, n)):
            yield batch


from directed_inputs_class import DirectedInputsClass
from extended_data_types import is_nothing, wrap_raw_data_for_export
from lifecyclelogging import Logging
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

# Settings
MAX_RETRY_TIMEOUT_SECONDS = 30


class SlackAPIError(RuntimeError):
    """Slack API error wrapper."""

    def __init__(self, response):
        self.response = response
        super().__init__(f"Slack API error: {response}")


def get_divider():
    return {"type": "divider"}


def get_header_block(field_title: str):
    return [
        {"type": "header", "text": {"type": "plain_text", "text": field_title}},
        get_divider(),
    ]


def get_field_context_message_blocks(field_name: str, context_data: Mapping):
    field_title = field_name.title()
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": field_title}},
        get_divider(),
    ]

    for field_keys in batched(context_data.keys(), 10):
        context_elements = []
        for field_key in field_keys:
            field_value = context_data.get(field_key)
            if is_nothing(field_value):
                continue
            if isinstance(field_value, Mapping):
                field_value = wrap_raw_data_for_export(field_value, allow_encoding=True)
            field_value = str(field_value)
            context_elements.append({"type": "mrkdwn", "text": f"{field_key}: {field_value}"})

        blocks.extend([{"type": "context", "elements": context_elements}, get_divider()])

    return blocks


def get_key_value_blocks(k: str, v: Any):
    k = k.title()
    if isinstance(v, Mapping):
        v = wrap_raw_data_for_export(v, allow_encoding=True)
    if not isinstance(v, str):
        v = str(v)
    return [{"type": "section", "text": {"type": "mrkdwn", "text": f"*{k}*: {v}"}}, get_divider()]


def get_rich_text_blocks(lines: list[str], bold: bool = False, italic: bool = False, strike: bool = False):
    style = {}
    if bold:
        style["bold"] = True
    if italic:
        style["italic"] = True
    if strike:
        style["strike"] = True

    elements = []
    for line in lines:
        element = {"type": "text", "text": line}
        if not is_nothing(style):
            element["style"] = style
        elements.append(element)

    return [{"type": "rich_text", "elements": elements}, get_divider()]


class SlackConnector(DirectedInputsClass):
    """Slack connector for messaging and channel management."""

    def __init__(
        self,
        token: str,
        bot_token: str,
        logger: Optional[Logging] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.logging = logger or Logging(logger_name="SlackConnector")
        self.logger = self.logging.logger

        self.web_client = WebClient(token)
        self.bot_web_client = WebClient(bot_token)

    def send_message(
        self,
        channel_name: str,
        text: str,
        blocks: Optional[list] = None,
        lines: Optional[list[str]] = None,
        bold: bool = False,
        italic: bool = False,
        strike: bool = False,
        thread_id: Optional[str] = None,
        raise_on_api_error: bool = True,
    ):
        """Send a message to a Slack channel."""
        if blocks is None:
            blocks = []

        if lines and len(lines) > 0:
            blocks.extend(get_rich_text_blocks(lines=lines, bold=bold, italic=italic, strike=strike))

        channels = self.get_bot_channels()
        if channel_name not in channels:
            raise RuntimeError(f"Bot not in channel {channel_name}. Add the bot first.")

        channel_id = channels[channel_name].get("id")
        if is_nothing(channel_id):
            raise RuntimeError(f"{channel_name} does not have a channel ID")

        opts: dict[str, Any] = {"channel": channel_id, "text": text}
        if not is_nothing(blocks):
            opts["blocks"] = blocks
        if not is_nothing(thread_id):
            opts["thread_ts"] = thread_id

        try:
            return self.bot_web_client.chat_postMessage(**opts).get("ts")
        except SlackApiError as exc:
            if raise_on_api_error:
                raise SlackAPIError(exc.response)
            return exc.response

    def get_bot_channels(self):
        """Get channels the bot is a member of."""
        try:
            return {channel["name"]: channel for channel in self.bot_web_client.users_conversations()["channels"]}
        except SlackApiError as exc:
            raise SlackAPIError(exc.response)

    def list_users(
        self,
        include_locale: Optional[bool] = None,
        limit: Optional[int] = None,
        team_id: Optional[str] = None,
        include_deleted: Optional[bool] = None,
        include_bots: Optional[bool] = None,
        include_app_users: Optional[bool] = None,
        **kwargs,
    ):
        """List Slack users with filtering options."""
        if include_locale is None:
            include_locale = self.get_input("include_locale", required=False, is_bool=True)
        if limit is None:
            limit = self.get_input("limit", required=False, is_integer=True)
        if team_id is None:
            team_id = self.get_input("team_id", required=False)
        if include_deleted is None:
            include_deleted = self.get_input("include_deleted", required=False, default=False, is_bool=True)
        if include_bots is None:
            include_bots = self.get_input("include_bots", required=False, default=False, is_bool=True)
        if include_app_users is None:
            include_app_users = self.get_input("include_app_users", required=False, default=False, is_bool=True)

        self.logger.info("Retrieving users from Slack")
        response = self._call_api(
            "users_list", group_by="members", include_locale=include_locale, limit=limit, team_id=team_id, **kwargs
        )

        if include_deleted and include_bots and include_app_users:
            return response

        filtered = {}
        for user_id, user_data in response.items():
            deleted = user_data.get("deleted", False)
            is_bot = user_data.get("is_bot", False) or user_data.get("is_workflow_bot", False)
            is_app_user = user_data.get("is_app_user", False)

            if (
                (deleted and not include_deleted)
                or (is_bot and not include_bots)
                or (is_app_user and not include_app_users)
            ):
                continue
            filtered[user_id] = user_data

        return filtered

    def list_conversations(
        self,
        exclude_archived: Optional[bool] = None,
        limit: Optional[int] = None,
        team_id: Optional[str] = None,
        types: Optional[Union[str, Sequence[str]]] = None,
        get_members: Optional[bool] = None,
        channels_only: Optional[bool] = None,
        **kwargs,
    ):
        """List Slack conversations."""
        if exclude_archived is None:
            exclude_archived = self.get_input("exclude_archived", required=False, is_bool=True)
        if limit is None:
            limit = self.get_input("limit", required=False, is_integer=True)
        if team_id is None:
            team_id = self.get_input("team_id", required=False)
        if get_members is None:
            get_members = self.get_input("get_members", required=False, default=False, is_bool=True)
        if channels_only is None:
            channels_only = self.get_input("channels_only", required=False, default=False, is_bool=True)

        self.logger.info("Getting Slack conversations")
        response = self._call_api(
            "conversations_list",
            group_by="channels",
            exclude_archived=exclude_archived,
            limit=limit,
            team_id=team_id,
            types=types,
            **kwargs,
        )

        if not channels_only:
            return response

        return {cid: cdata for cid, cdata in response.items() if cdata.get("is_channel")}

    def _call_api(
        self,
        method: str,
        group_by: Optional[str] = None,
        id_field_name: str = "id",
        **kwargs,
    ):
        """Call a Slack API method with retry logic."""
        call = getattr(self.web_client, method, None)
        if call is None:
            raise AttributeError(f"{method} is not supported by the Slack WebClient")

        response = None
        attempt = 1
        total_delay = 0

        while not response:
            self.logger.debug(f"[Attempt {attempt}] Calling Slack WebClient {method}...")
            try:
                response = call(**kwargs)
            except SlackApiError as exc:
                if exc.response["error"] == "ratelimited":
                    delay = int(exc.response.headers["Retry-After"])
                    total_delay += delay
                    if total_delay > MAX_RETRY_TIMEOUT_SECONDS:
                        raise TimeoutError(f"Slack WebClient {method} timed out after {total_delay} seconds")
                    self.logger.warning(f"Rate limited. Retrying in {delay} seconds")
                    sleep(delay)
                    attempt += 1
                else:
                    raise SlackAPIError(exc.response)

        if is_nothing(response) or is_nothing(group_by):
            return response

        grouped = {}
        for datum in response.get(group_by, {}):
            datum_id = datum.get(id_field_name)
            if is_nothing(datum_id):
                raise RuntimeError(f"No ID for field {id_field_name} in returned datum: {datum}")
            grouped[datum_id] = datum

        return grouped
