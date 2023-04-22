# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

"""Module for http api base functionality."""
from __future__ import absolute_import, division, print_function

import json

__metaclass__ = type  # pylint: disable=invalid-name

from json.decoder import JSONDecodeError
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

    # pylint: disable=arguments-differ
    def send_request(self, data, method="POST", path="/jsonrpc"):
        try:
            self._display_request(data)
            response, response_data = self.connection.send(
                path,
                data,
                method=method,
                headers=BASE_HEADERS,
                force_basic_auth=True,
            )

            return response.getcode(), self._response_to_json(
                to_text(response_data.getvalue())
            )
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

    def _display_request(self, data):
        self.connection.queue_message("vvvv", f"HTTP Request data: {data}")

    def _response_to_json(self, response_text):
        try:
            return json.loads(response_text) if response_text else {}

        except JSONDecodeError as exc:
            raise ConnectionError(f"Invalid JSON response: {response_text}") from exc
