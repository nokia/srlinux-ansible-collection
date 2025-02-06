# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

"""srlinux module utils"""
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from typing import Any

# pylint: disable=invalid-name
__metaclass__ = type
import json
from datetime import datetime
from time import sleep

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection
from ansible_collections.nokia.srlinux.plugins.module_utils.const import (
    JSON_RPC_VERSION,
    SAVE_CONFIG_PATH,
    TOOLS_DATASTORE,
)


class JSONRPCClient:
    """SRLinux JSON-RPC client"""

    def __init__(self, module=None):
        self.module = module
        if module:
            self.connection = Connection(self.module._socket_path)

    def _httpapi_error_handle(self, method="POST", path="/jsonrpc", payload=None):
        try:
            code, response = self.connection.send_request(
                data=payload, method=method, path=path
            )

            if code == 404:
                if to_text("Object not found") in to_text(response) or to_text(
                    "Could not find object"
                ) in to_text(response):
                    return {}

            if not (200 <= code < 300):
                self.module.fail_json(
                    msg=f"srlinux httpapi returned error {code} with message {to_text(response)}"
                )

            return response

        except ConnectionError as e:
            self.module.fail_json(
                msg=f"connection error occurred: {e}",
            )

        except ValueError as e:
            try:
                self.module.fail_json(msg=f"certificate not found: {e}")
            except AttributeError:
                pass

    def post(self, url="/jsonrpc", payload=None, **kwargs):
        """JSON-RPC POST request"""
        return self._httpapi_error_handle("POST", url, payload=payload, **kwargs)


def convertIdentifiers(data):
    """Converts keys in the list of dicts to have dashes instead of underscores.

    This is needed, because the JSON-RPC API uses dashes in the keys, but the ansible linter does not allow them.
    """
    if isinstance(data, list):
        for item in data:
            convertIdentifiers(item)
    elif isinstance(data, dict):
        for key, value in list(data.items()):
            if "_" in key:
                new_key = key.replace("_", "-")
                data[new_key] = data.pop(key)
            convertIdentifiers(value)


def convertResponseKeys(response):
    """Converts keys in the response object in the following manner:
    `jsonrpc` -> `jsonrpc_version
    `id` -> `jsonrpc_req_id`"""
    if "jsonrpc" in response:
        response["jsonrpc_version"] = response.pop("jsonrpc")
    if "id" in response:
        response["jsonrpc_req_id"] = response.pop("id")


def rpcID():
    """Generates an id for the JSON-RPC request
    which follows the UTC datetime"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")


def process_save_when(client, json_output) -> Any:
    """Handle save_when operation"""
    data = {
        "jsonrpc": JSON_RPC_VERSION,
        "id": rpcID(),
        "method": "set",
        "params": {
            "datastore": TOOLS_DATASTORE,
            "commands": [
                {
                    "action": "update",
                    "path": SAVE_CONFIG_PATH,
                },
            ],
        },
    }

    # in case the config changes caused the reload of the json rpc server,
    # we need to retry the save operation, as the first ones might fail due to the ongoing server reload
    retries = 5
    retry_delay = 2  # seconds between retries

    for attempt in range(retries):
        try:
            set_resp = client.post(payload=json.dumps(data))
            if set_resp and set_resp.get("result"):
                json_output["saved"] = True
                break
        except (
            Exception
        ):  # You may want to catch specific exceptions based on what client.post raises
            if attempt < retries - 1:  # Don't sleep on the last attempt
                sleep(retry_delay)
            continue

    return json_output
