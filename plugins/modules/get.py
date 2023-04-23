#!/usr/bin/python
# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

"""Ansible module for jsonrpc get"""

from __future__ import absolute_import, division, print_function

import json
import random

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nokia.srlinux.plugins.module_utils.srlinux import JSONRPCClient
from ansible_collections.nokia.srlinux.plugins.module_utils.const import (
    JSON_RPC_VERSION,
)

# pylint: disable=invalid-name
__metaclass__ = type

DOCUMENTATION = """
---
module: jsonrpc_get
short_description: "Implementation of the Nokia SR Linux JSON-RPC's Get method."
description:
  - >-
    This module allows to retrieve configuration and state details from the system.
    The get method can be used with candidate, running, and state datastores, but cannot be used with the tools datastore.
version_added: "0.1.0"
options:
  paths:
    type: list
    elements: dict
    description:
      - List of paths to get data from.
    suboptions:
      datastore:
        type: str
        description:
          - The datastore to query
        choices:
          - candidate
          - running
          - state
          - tools
        required: true
      path:
        description:
          - the YANG path of a datastore node
        type: str
        required: true

author:
  - Patrick Dumais (@Nokia)
  - Roman Dodin (@Nokia)
  - Walter De Smedt (@Nokia)
"""

EXAMPLES = """
- name: Get /system/information container
  nokia.srlinux.get:
    paths:
      - path: /system/information
        datastore: state
"""


def main():
    """Main entrypoint for module execution"""

    argspec = {
        "paths": {
            "type": "list",
            "elements": "dict",
            "options": {
                "path": {"type": "str", "required": True},
                "datastore": {
                    "type": "str",
                    "choices": ["candidate", "running", "state", "tools"],
                    "required": True,
                },
            },
        }
    }

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    client = JSONRPCClient(module)

    json_output = {}

    paths = module.params.get("paths")
    data = {
        "jsonrpc": JSON_RPC_VERSION,
        "id": random.randint(1, 65535),
        "method": "get",
        "params": {"commands": paths},
    }

    ret = client.post(payload=json.dumps(data))
    # populate the output using custom keys
    json_output["jsonrpc_req_id"] = ret["id"]
    json_output["jsonrpc_version"] = ret["jsonrpc"]
    json_output["result"] = ret.get("result")
    err = ret.get("error")
    if err:
        json_output["error"] = err

    if ret and ret.get("result"):
        module.exit_json(**json_output)

    # handling error case
    json_output["failed"] = True
    module.fail_json(
        msg=json_output["error"]["message"],
        jsonrpc_req_id=json_output["jsonrpc_req_id"],
    )


if __name__ == "__main__":
    main()
