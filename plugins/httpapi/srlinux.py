# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

"""Module for http api base functionality."""
from __future__ import absolute_import, division, print_function

import json

__metaclass__ = type  # pylint: disable=invalid-name

from urllib.error import HTTPError
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.basic import to_text
from ansible_collections.ansible.netcommon.plugins.plugin_utils.httpapi_base import (
    HttpApiBase,
)

DOCUMENTATION = """
---
name: srlinux
short_description: HttpApi Plugin for Nokia SR Linux
description:
  - This HttpApi plugin provides methods to connect to Nokia SR Linux over a HTTP(S)-based API.
version_added: "0.1.0"
author:
  - Patrick Dumais (@Nokia)
  - Roman Dodin (@Nokia)
  - Walter De Smedt (@Nokia)
"""

BASE_HEADERS = {"Content-Type": "application/json"}


class HttpApi(HttpApiBase):
    """HttpApi plugin for Nokia SR Linux"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = BASE_HEADERS
        self.error = None

    # pylint: disable=arguments-differ
    def send_request(self, data, method="POST", path="/jsonrpc"):
        try:
            # return 200, to_text(self.connection)
            self._display_request(method, path)
            response, response_data = self.connection.send(
                path,
                data,
                method=method,
                headers=BASE_HEADERS,
                force_basic_auth=True,
            )
            value = self._get_response_value(response_data)

            return response.getcode(), self._response_to_json(value)
        except AnsibleConnectionFailure as e:
            self.connection.queue_message("vvv", f"AnsibleConnectionFailure: {e}")
            if to_text("Could not connect to") in to_text(e):
                raise
            if to_text("401") in to_text(e):
                return 401, "Authentication failure"
            return 404, "Object not found"
        except HTTPError as e:
            error = e.read()
            return e.code, error

    def _display_request(self, request_method, path):
        self.connection.queue_message("vvvv", f"HTTP Request: {request_method} {path}")

    def _get_response_value(self, response_data):
        return to_text(response_data.getvalue())

    def _response_to_json(self, response_text):
        try:
            return json.loads(response_text) if response_text else {}
        # JSONDecodeError only available on Python 3.5+
        except ValueError as exc:
            raise ConnectionError(f"Invalid JSON response: {response_text}") from exc
