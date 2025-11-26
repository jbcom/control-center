from collections.abc import Mapping, Sequence
from itertools import batched
from time import sleep
from typing import Any, List, Optional, Union

from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

from cloud_connectors.base import settings, utils
from cloud_connectors.base.errors import FailedResponseError
from cloud_connectors.base.utils import Utils


def get_divider():
    return {"type": "divider"}


def get_header_block(field_title: str):
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": field_title,
            },
        },
        get_divider(),
    ]


def get_field_context_message_blocks(field_name: str, context_data: Mapping):
    field_title = field_name.title()

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": field_title,
            },
        },
        get_divider(),
    ]

    for field_keys in batched(context_data.keys(), 10):  # Max supported by Slack context blocks
        context_elements = []

        for field_key in field_keys:
            field_value = context_data.get(field_key)
            if utils.is_nothing(field_value):
                continue

            if isinstance(field_value, Mapping):
                field_value = utils.wrap_raw_data_for_export(field_value, allow_encoding=True)

            field_value = str(field_value)

            context_elements.append(
                {
                    "type": "mrkdwn",
                    "text": f"{field_key}: {field_value}",
                }
            )

        blocks.extend(
            [
                {
                    "type": "context",
                    "elements": context_elements,
                },
                get_divider(),
            ]
        )

    return blocks


def get_key_value_blocks(k: str, v: Any):
    k = k.title()

    if isinstance(v, Mapping):
        v = utils.wrap_raw_data_for_export(v, allow_encoding=True)

    if not isinstance(v, str):
        v = str(v)

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{k}*: {v}",
            },
        },
        get_divider(),
    ]


def get_rich_text_blocks(
    lines: list[str],
    bold: bool = False,
    italic: bool = False,
    strike: bool = False,
):
    style = {}

    if bold:
        style["bold"] = True

    if italic:
        style["italic"] = True

    if strike:
        style["strike"] = True

    elements = []

    for line in lines:
        element = {
            "type": "text",
            "text": line,
        }

        if not utils.is_nothing(style):
            element["style"] = style

        elements.append(element)

    return [
        {
            "type": "rich_text",
            "elements": elements,
        },
        get_divider(),
    ]


class SlackConnector(Utils):
    def __init__(self, token: str, bot_token: str, **kwargs):
        super().__init__(**kwargs)

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
        if lines is None:
            lines = []

        if len(lines) > 0:
            blocks.extend(get_rich_text_blocks(lines=lines, bold=bold, italic=italic, strike=strike))

        channels = self.get_bot_channels()
        if channel_name not in channels:
            raise RuntimeError(
                f"Please add the Internal Tooling Bot to the {channel_name} Slack channel first so it can send a message in this channel"
            )

        channel_id = channels[channel_name].get("id")
        if utils.is_nothing(channel_id):
            raise RuntimeError(f"{channel_name} does not have a channel ID")

        opts = {
            "channel": channel_id,
            "text": text,
        }

        if not utils.is_nothing(blocks):
            opts["blocks"] = blocks

        if not utils.is_nothing(thread_id):
            opts["thread_ts"] = thread_id

        try:
            return self.bot_web_client.chat_postMessage(**opts).get("ts")
        except SlackApiError as exc:
            if raise_on_api_error:
                raise FailedResponseError(exc.response)

            return exc.response

    def get_bot_channels(self):
        try:
            return {channel["name"]: channel for channel in self.bot_web_client.users_conversations()["channels"]}
        except SlackApiError as exc:
            raise FailedResponseError(exc.response)

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
        if include_locale is None:
            include_locale = self.get_input("include_locale", required=False, is_bool=True)

        if limit is None:
            limit = self.get_input("limit", required=False)

        if team_id is None:
            team_id = self.get_input("team_id", required=False)

        if include_deleted is None:
            include_deleted = self.get_input("include_deleted", required=False, default=False, is_bool=True)

        if include_bots is None:
            include_bots = self.get_input("include_bots", required=False, default=False, is_bool=True)

        if include_app_users is None:
            include_app_users = self.get_input("include_app_users", required=False, default=False, is_bool=True)
        self.logger.info("Retrieving users from Slack")

        response = self.users_list(
            group_by="members",
            include_locale=include_locale,
            limit=limit,
            team_id=team_id,
            **kwargs,
        )

        if include_deleted and include_bots and include_app_users:
            self.logger.info("Including all users")
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
                self.logged_statement(f"Skipping user {user_id}", json_data=user_data, verbose=True, verbosity=2)
                continue

            filtered[user_id] = user_data

        return filtered

    def list_usergroups(
        self,
        include_count: Optional[bool] = None,
        include_disabled: Optional[bool] = None,
        include_users: Optional[bool] = None,
        expand_users: Optional[bool] = None,
        team_id: Optional[str] = None,
        **kwargs,
    ):
        if include_count is None:
            include_count = self.get_input("include_count", required=False, is_bool=True)

        if include_disabled is None:
            include_disabled = self.get_input("include_disabled", required=False, is_bool=True)

        if include_users is None:
            include_users = self.get_input("include_users", required=False, is_bool=True)

        if expand_users is None:
            expand_users = self.get_input("expand_users", required=False, default=False, is_bool=True)

        if team_id is None:
            team_id = self.get_input("team_id", required=False)

        self.logger.info("Getting Slack usergroups")

        if expand_users:
            include_users = True

        response = self.usergroups_list(
            group_by="usergroups",
            include_count=include_count,
            include_disabled=include_disabled,
            include_users=include_users,
            team_id=team_id,
            **kwargs,
        )

        if not expand_users:
            return response

        # Fetch users to expand usergroup user IDs
        users = self.list_users(**kwargs)

        expanded = {}

        for usergroup_id, usergroup_data in response.items():
            usergroup_users = usergroup_data.pop("users", [])

            usergroup_data["users"] = {}

            for user_id in usergroup_users:
                usergroup_data["users"][user_id] = users.get(user_id, {})

            expanded[usergroup_id] = usergroup_data

        return expanded

    def list_conversation_members(
        self,
        channel: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs,
    ):
        if channel is None:
            channel = self.get_input("channel", required=True)

        if limit is None:
            limit = self.get_input("limit", required=False)

        self.logger.info(f"Getting Slack members for conversation {channel}")

        response = self.conversations_members(channel=channel, limit=limit, **kwargs)

        return (response.get("members", []),)

    def update_channel_members(
        self,
        channel_name: Optional[str] = None,
        user_ids: Optional[list[str]] = None,
        is_private: Optional[bool] = None,
        remove_other_users: Optional[bool] = None,
        raise_on_api_error: bool = True,
        **kwargs,
    ):
        """
        Ensures that the specified channel exists and has the specified members.

        :param channel_name: Name of the channel to update.
        :param user_ids: List of user IDs to be members of the channel.
        :param is_private: Whether the channel is private (used if channel needs to be created).
        :param remove_other_users: Whether other users should be removed from the channel.
        :param raise_on_api_error: Whether to raise an exception on API error.
        :param kwargs: Additional arguments to pass to API calls.
        """

        if channel_name is None:
            channel_name = self.get_input("channel_name", required=True)

        if user_ids is None:
            user_ids = self.get_input("user_ids", required=True)
            if isinstance(user_ids, str):
                user_ids = user_ids.split(",")  # Assuming comma-separated string
            elif not isinstance(user_ids, list):
                raise ValueError("user_ids must be a list of user IDs or a comma-separated string")

        if is_private is None:
            is_private = self.get_input("is_private", required=False, default=False, is_bool=True)

        if remove_other_users is None:
            remove_other_users = self.get_input("remove_other_users", required=False, default=False, is_bool=True)

        # First, check if the channel exists
        channel = self.get_channel(channel_name)
        if channel is None:
            # Channel does not exist, create it
            self.logger.info(f"Channel '{channel_name}' does not exist. Creating it.")
            channel = self.create_channel(
                name=channel_name,
                is_private=is_private,
                user_ids=user_ids,
                raise_on_api_error=raise_on_api_error,
                **kwargs,
            )
            channel_id = channel.get("id")
            self.logger.info(f"Channel '{channel_name}' created with ID {channel_id}")

            # Since the channel is newly created and users are already invited, we can return here
            return channel
        else:
            # Channel exists
            channel_id = channel.get("id")
            self.logger.info(f"Channel '{channel_name}' exists with ID {channel_id}")

        # Proceed to update members only if the channel was not newly created
        # Get current members
        current_member_ids = self.list_conversation_members(channel=channel_id)

        # Ensure bot is a member of the channel
        bot_user_id = self.bot_user_id
        if bot_user_id not in current_member_ids:
            self.logger.info(f"Bot user is not a member of channel '{channel_name}'. Joining the channel.")
            try:
                self.bot_web_client.conversations_join(channel=channel_id)
                current_member_ids.append(bot_user_id)
            except SlackApiError as e:
                error = e.response["error"]
                self.logger.error(f"Error joining channel '{channel_name}': {error}")
                if raise_on_api_error:
                    raise FailedResponseError(e.response)
                else:
                    pass  # Or handle accordingly

        # Get channel creator to avoid removing them
        try:
            channel_info = self.bot_web_client.conversations_info(channel=channel_id)
            channel_creator = channel_info["channel"].get("creator")
        except SlackApiError as e:
            error = e.response["error"]
            self.logger.error(f"Error retrieving channel info for '{channel_name}': {error}")
            if raise_on_api_error:
                raise FailedResponseError(e.response)
            else:
                channel_creator = None

        # Update the member lists
        user_ids_set = set(user_ids)
        current_member_ids_set = set(current_member_ids)

        # Do not attempt to remove the bot itself or the channel creator
        protected_users = {bot_user_id}
        if channel_creator:
            protected_users.add(channel_creator)

        # Users to invite: in user_ids but not in current members
        users_to_invite = user_ids_set - current_member_ids_set

        # Invite missing users
        if users_to_invite:
            self.logger.info(f"Inviting users {list(users_to_invite)} to channel '{channel_name}'")
            # Slack API allows inviting up to 1000 users at a time
            try:
                self.bot_web_client.conversations_invite(channel=channel_id, users=list(users_to_invite))
            except SlackApiError as e:
                error = e.response["error"]
                self.logger.error(f"Error inviting users to channel '{channel_name}': {error}")
                if raise_on_api_error:
                    raise FailedResponseError(e.response)
                else:
                    pass  # Or handle accordingly

        if not remove_other_users:
            return channel

        # Users to remove: in current members but not in user_ids
        users_to_remove = current_member_ids_set - user_ids_set - protected_users

        # Remove extra users
        for user_id in users_to_remove:
            self.logger.info(f"Removing user {user_id} from channel '{channel_name}'")
            try:
                self.bot_web_client.conversations_kick(channel=channel_id, user=user_id)
            except SlackApiError as e:
                error = e.response["error"]
                self.logger.error(f"Error removing user {user_id} from channel '{channel_name}': {error}")
                if raise_on_api_error:
                    raise FailedResponseError(e.response)
                else:
                    pass  # Or handle accordingly

        return channel

    def get_channel(self, channel_name: str):
        channels = self.list_conversations(
            channels_only=True,
            get_members=False,
            types="public_channel,private_channel",
        )

        for channel_id, channel_data in channels.items():
            if channel_data.get("name") == channel_name:
                return channel_data

            self.logged_statement(f"{channel_id} not a match", json_data=channel_data, verbose=True, verbosity=2)

        return None

    def create_channel(
        self,
        name: Optional[str] = None,
        is_private: Optional[bool] = None,
        user_ids: Optional[Union[str, list[str]]] = None,
        raise_on_api_error: bool = True,
        **kwargs,
    ):
        """
        Creates a Slack channel.

        :param name: The name of the channel to be created.
        :param is_private: Whether the channel is private. Defaults to False (public channel).
        :param user_ids: A list of user IDs to be invited to the channel.
        :param raise_on_api_error: Whether to raise an exception on API error.
        :param kwargs: Additional arguments to pass to the API call.
        """
        if name is None:
            name = self.get_input("name", required=True)

        if is_private is None:
            is_private = self.get_input("is_private", required=False, default=False, is_bool=True)

        if user_ids is None:
            user_ids = self.get_input("user_ids", required=False)
            if user_ids:
                if isinstance(user_ids, str):
                    user_ids = user_ids.split(",")  # Assuming comma-separated string
                elif not isinstance(user_ids, list):
                    raise ValueError("user_ids must be a list of user IDs or a comma-separated string")

        self.logger.info(f"Creating Slack channel '{name}' (private: {is_private})")

        try:
            response = self.bot_web_client.conversations_create(name=name, is_private=is_private, **kwargs)
            channel = response.get("channel")
            channel_id = channel.get("id")
            self.logger.info(f"Channel '{name}' created with ID {channel_id}")

            if user_ids:
                self.logger.info(f"Inviting users {user_ids} to channel '{name}'")
                self.bot_web_client.conversations_invite(
                    channel=channel_id, users=user_ids if isinstance(user_ids, list) else [user_ids]
                )

            return channel

        except SlackApiError as e:
            error = e.response["error"]
            self.logger.error(f"Error creating channel '{name}': {error}")
            if raise_on_api_error:
                raise FailedResponseError(e.response)
            else:
                return e.response

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
        if exclude_archived is None:
            exclude_archived = self.get_input("exclude_archived", required=False, is_bool=True)

        if limit is None:
            limit = self.get_input("limit", required=False)

        if team_id is None:
            team_id = self.get_input("team_id", required=False)

        if types is None:
            types = self.decode_input("types", required=False)

        if get_members is None:
            get_members = self.get_input("get_members", required=False, default=False, is_bool=True)

        if channels_only is None:
            channels_only = self.get_input("channels_only", required=False, default=False, is_bool=True)

        self.logger.info("Getting Slack conversations")

        response = self.conversations_list(
            group_by="channels",
            exclude_archived=exclude_archived,
            limit=limit,
            team_id=team_id,
            types=types,
            **kwargs,
        )

        if get_members:
            for conversation_id in response.keys():
                response[conversation_id]["members"] = self.list_conversation_members(
                    channel=conversation_id, exit_on_completion=False
                )

        if not channels_only:
            return response

        channels = {}

        for conversation_id, conversation_data in response.items():
            is_channel = conversation_data.get("is_channel")

            if not is_channel:
                self.logged_statement(
                    f"Returned conversation {conversation_id} is not a channel",
                    json_data=conversation_data,
                    verbose=True,
                    verbosity=2,
                )
                continue

            channels[conversation_id] = conversation_data

        return channels

    def __getattr__(self, method):
        call = getattr(self.web_client, method, None)

        if utils.is_nothing(call):
            raise AttributeError(f"{method} is not supported by the Slack WebClient")

        def caller(
            group_by: Optional[str] = None,
            id_field_name: Optional[str] = "id",
            *args,
            **kwargs,
        ):
            response = None
            attempt = 1
            total_delay = 0

            while not response:
                self.logged_statement(
                    f"[Attempt {attempt}] Calling Slack WebClient {method}...",
                    verbose=True,
                    verbosity=2,
                )

                try:
                    response = call(*args, **kwargs)
                except SlackApiError as exc:
                    if exc.response["error"] == "ratelimited":
                        delay = int(exc.response.headers["Retry-After"])
                        total_delay += delay

                        if total_delay > settings.MAX_PROC_RUN_TIME:
                            raise TimeoutError(f"Slack WebClient {method} timed out after {total_delay} seconds")

                        self.logger.warning(f"Rate limited. Retrying Slack WebClient {method} in {delay} seconds")
                        sleep(delay)
                        attempt += 1
                    else:
                        raise FailedResponseError(exc.response)

            if utils.is_nothing(response) or utils.is_nothing(group_by):
                return response

            grouped = {}

            for datum in response.get(group_by, {}):
                datum_id = datum.get(id_field_name)
                if utils.is_nothing(datum_id):
                    raise RuntimeError(f"No ID for field {id_field_name} in returned Slack WebClient datum: {datum}")

                grouped[datum_id] = datum

            return grouped

        return caller
