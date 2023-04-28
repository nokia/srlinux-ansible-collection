# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

""" srlinux module utils """
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

# pylint: disable=invalid-name
__metaclass__ = type
from datetime import datetime

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection
from ansible.module_utils.urls import CertificateError


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
        except CertificateError as e:
            self.module.fail_json(
                msg=f"certificate error occurred: {e}",
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
    """Converts keys in the reponse object in the following manner:
    `jsonrpc` -> `jsonrpc_version
    `id` -> `jsonrpc_req_id`"""
    if "jsonrpc" in response:
        response["jsonrpc_version"] = response.pop("jsonrpc")
    if "id" in response:
        response["jsonrpc_req_id"] = response.pop("id")


def rpcID():
    """Generates an id for the JSON-RPC request
    which follows the UTC datetime"""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S:%f")
