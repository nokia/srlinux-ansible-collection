#!/usr/bin/python
# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

"""Ansible module for executing CLI commands to SR Linux devices"""

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
module: cli
short_description: "Execute CLI commands on SR Linux devices."
description:
  - This module allows CLI commands to be executed in Nokia SR Linux using JSON-RPC interface.
version_added: "0.1.0"
options:
  commands:
    description:
      - List of commands to run.
    type: list
    elements: str
    required: true
  output_format:
    description:
      - Output format.
    type: str
    choices: ["json", "text", "table"]
    default: json
    required: false

author:
  - Patrick Dumais (@Nokia)
  - Roman Dodin (@Nokia)
  - Walter De Smedt (@Nokia)
"""

EXAMPLES = """
- name: Run \"show version\" CLI command
  nokia.srlinux.cli:
    commands:
      - show version
  register: response
"""


def main():
    """Main function"""
    argspec = {
        "commands": {
            "type": "list",
            "elements": "str",
            "required": True,
        },
        "output_format": {
            "type": "str",
            "choices": ["json", "text", "table"],
            "default": "json",
        },
    }

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    client = JSONRPCClient(module)

    json_output = {}
    json_output["changed"] = False

    commands = module.params.get("commands")
    out_format = module.params.get("output_format")

    data = {
        "jsonrpc": JSON_RPC_VERSION,
        "id": random.randint(0, 65535),
        "method": "cli",
        "params": {"commands": commands, "output-format": out_format},
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
