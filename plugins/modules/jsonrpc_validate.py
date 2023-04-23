# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

"""Ansible module for jsonrpc validate"""
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
module: jsonrpc_validate
short_description: "Implementation of the Nokia SR Linux JSON-RPC's Validate method."
description:
  - This module allows to verify that the system accepts a configuration transaction before applying it to the system.
version_added: "0.1.0"
options:
  update:
    description:
      - Update operations to validate.
    required: false
    type: list
    elements: dict
    suboptions:
      path:
        description:
          - targeted path for update operation
        type: str
        required: true
      value:
        type: dict
        description:
          - values to update
        required: true
  delete:
    description:
      - Delete operations to validate.
    required: false
    type: list
    elements: dict
    suboptions:
      path:
        description:
          - targeted path for delete operation
        type: str
        required: true
  replace:
    description:
      - Replace operations to validate.
    required: false
    type: list
    elements: dict
    suboptions:
      path:
        description:
          - targeted path for replace operation
        type: str
        required: true
      value:
        description:
          - values to replace
        required: true
        type: dict

author:
  - Patrick Dumais (@Nokia)
  - Roman Dodin (@Nokia)
  - Walter De Smedt (@Nokia)
"""

EXAMPLES = """
- name: Validate a valid change set
  nokia.srlinux.jsonrpc_validate:
    update:
      - path: /system/information
        value:
          location: Some location
          contact: Some contact
"""


def main():
    """Main function"""
    argspec = {
        "update": {
            "type": "list",
            "elements": "dict",
            "required": False,
            "options": {
                "path": {"type": "str", "required": True},
                "value": {"type": "dict", "required": True},
            },
        },
        "delete": {
            "type": "list",
            "elements": "dict",
            "required": False,
            "options": {
                "path": {"type": "str", "required": True},
            },
        },
        "replace": {
            "type": "list",
            "elements": "dict",
            "required": False,
            "options": {
                "path": {"type": "str", "required": True},
                "value": {"type": "dict", "required": True},
            },
        },
    }

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    client = JSONRPCClient(module)

    json_output = {"changed": False}

    updates = module.params.get("update") or []
    deletes = module.params.get("deletes") or []
    replaces = module.params.get("replace") or []

    commands = []
    for x in updates:
        x["action"] = "update"
        commands += [x]
    for x in deletes:
        x["action"] = "delete"
        commands += [x]
    for x in replaces:
        x["action"] = "replace"
        commands += [x]

    data = {
        "jsonrpc": JSON_RPC_VERSION,
        "id": random.randint(0, 65535),
        "method": "validate",
        "params": {"commands": commands},
    }
    ret = client.post(payload=json.dumps(data))

    # If the request was successful, we return the result
    if ret and not ret.get("error"):
        module.exit_json(**json_output)

    json_output["json"] = ret
    json_output["failed"] = True
    module.exit_json(**json_output)


if __name__ == "__main__":
    main()
