# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

""" srlinux module utils """
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

# pylint: disable=invalid-name
__metaclass__ = type

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection
from ansible.module_utils.urls import CertificateError


class JSONRPCClient:
    """SRLinux JSON-RPC client"""

    def __init__(self, module=None, connection=None):
        self.module = module
        if module:
            self.connection = Connection(self.module._socket_path)
        elif connection:
            self.connection = connection
            self.connection.load_platform_plugins("nokia.srl.srlinux")

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

            if not (code >= 200 and code < 300):
                responsestr = response.decode("utf-8")
                self.module.fail_json(
                    msg=f"srlinux httpapi returned error {code} with message {responsestr}"
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
        """SRL JsonRPC Post function"""
        return self._httpapi_error_handle("POST", url, payload=payload, **kwargs)
