from __future__ import annotations

import os
from http import HTTPStatus
from typing import Optional

import botocore.exceptions
from requests import Response


class FormattingError(RuntimeError):
    pass


class TableAssetNotFoundError(RuntimeError):
    def __init__(self, asset_name: str, table_name: str):
        super().__init__(f"{asset_name} not found in the {table_name} table")


class StateFileNotFoundError(FileNotFoundError):
    def __init__(self, state_path: str, extra_info: Optional[str] = None):
        super().__init__(f"State path {state_path} not found" + f" {extra_info}" if extra_info else "")


class FailedResponseError(RuntimeError):
    def __init__(
        self,
        response: Response | botocore.exceptions.ClientError,
        additional_information: Optional[str] = None,
    ):
        if isinstance(response, botocore.exceptions.ClientError):
            self.response = response.response
        else:
            self.response = response

        status_code = response.status_code

        blocks = {
            "Status code": status_code,
            "Reason": response.reason,
            "History": response.history,
            "Headers": response.headers,
        }

        text = response.text

        if text:
            tabbed_text = [f"\t{line}" for line in text.splitlines()]

            blocks["Content"] = os.linesep.join(tabbed_text)

        phrase = HTTPStatus(status_code).phrase
        msg = [f"[{phrase}] Request from {response.url} failed:"]

        if additional_information:
            msg.append(f"\n\tAdditional information: {additional_information}\n")

        for block_key, block_contents in blocks.items():
            msg.append(f"{block_key}:\n\n{block_contents}\n")

        super().__init__(os.linesep.join(msg))


class RequestRateLimitedError(RuntimeError):
    def __init__(
        self,
        response: Response,
        retry_after: Optional[int] = None,
        additional_information: Optional[str] = None,
    ):
        """
        Error for rate-limited API requests.

        Args:
            response (Response): The HTTP response object.
            retry_after (Optional[int]): Suggested backoff delay in seconds, if provided.
            additional_information (Optional[str]): Additional debugging or context information.
        """
        self.response = response
        self.retry_after = retry_after

        status_code = response.status_code
        blocks = {
            "Status code": status_code,
            "Reason": response.reason,
            "Headers": response.headers,
        }

        text = response.text

        if text:
            tabbed_text = [f"\t{line}" for line in text.splitlines()]
            blocks["Content"] = os.linesep.join(tabbed_text)

        phrase = HTTPStatus(status_code).phrase
        msg = [f"[{phrase}] Request from {response.url} failed due to rate limiting:"]

        if retry_after:
            msg.append(f"\n\tSuggested retry after {retry_after} seconds.\n")

        if additional_information:
            msg.append(f"\n\tAdditional information: {additional_information}\n")

        for block_key, block_contents in blocks.items():
            msg.append(f"{block_key}:\n\n{block_contents}\n")

        super().__init__(os.linesep.join(msg))
