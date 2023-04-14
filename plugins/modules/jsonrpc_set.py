#!/usr/bin/python
# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

# -*- coding: utf-8 -*-
"""Ansible module for jsonrpc set"""

from __future__ import absolute_import, division, print_function

import json
import random

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nokia.srl.plugins.module_utils.srlinux import JSONRPCClient
from ansible_collections.nokia.srl.plugins.module_utils.const import (
    JSON_RPC_VERSION,
    TEXT_FORMAT,
    TOOLS_DATASTORE,
    SAVE_CONFIG_PATH,
)

# pylint: disable=invalid-name
__metaclass__ = type

DOCUMENTATION = """
---
module: jsonrpc_set
short_description: "Implementation of the Nokia SR Linux JSON-RPC's Set method."
description:
  - This module allows to set a configuration or run operational transaction. The set method can be used with the candidate and tools datastores.
version_added: "0.1.0"
options:
  save_when:
    type: str
    description:
      - 'When to save running to startup config.'
    choices: ["always", "never", "changed"]
    default: never
  update:
    description:
      - Update operation.
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
      - Delete operation.
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
      - replace operation.
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
- name: Set system information with values
  nokia.srl.jsonrpc_set:
    update:
      - path: /system/information
        value:
          location: Some location
          contact: Some contact
"""


def main():
    """Main entrypoint for module execution"""
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
        "save_when": {"choices": ["always", "never", "changed"], "default": "never"},
    }

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    client = JSONRPCClient(module)

    # used to track if the module changed anything
    # default state is False
    changed = False

    json_output = {"changed": changed, "saved": False}

    save_when = module.params.get("save_when")
    updates = module.params.get("update") or []
    deletes = module.params.get("delete") or []
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

    # collecting the diff
    data = {
        "jsonrpc": JSON_RPC_VERSION,
        "id": random.randint(0, 65535),
        "method": "diff",
        "params": {
            "commands": commands,
            "output-format": TEXT_FORMAT,
        },
    }
    diff_resp = client.post(payload=json.dumps(data))

    # failed to get diff response means something went wrong
    # we have to fail the module
    if not diff_resp:
        json_output["failed"] = True
        module.fail_json(**json_output)

    # fail the module if an error is reported by diff
    if diff_resp.get("error"):
        json_output["failed"] = True
        module.fail_json(
            msg=diff_resp["error"]["message"], method="diff", id=diff_resp["id"]
        )

    # if diff response is not empty, we have a diff
    # we need to set the changed flag to True
    # and save the diff response result in the json_output
    if diff_resp.get("result"):
        res = diff_resp["result"]
        # remove empty lines from the diff output
        res = [x for x in res if x != ""]
        if len(res):
            # save succesfull diff in the json_output
            # so that it is returned to the user
            json_output["diff"] = diff_resp
            changed = True

    # in check mode we just return the changed status
    if module.check_mode:
        json_output["changed"] = changed
        # prepare on-box diff to be printed for a user
        # see https://github.com/ansible/ansible/blob/stable-2.14/lib/ansible/plugins/callback/__init__.py#L344  # pylint: disable=line-too-long
        # for details on which fields are used
        # diff reports result as a list with one element that contains the full diff for all operations in the diff request
        if changed:
            json_output.update({"diff": {"prepared": diff_resp.get("result")[0]}})
        module.exit_json(**json_output)

    # when not in check mode, we proceed with modifying the configuration
    data = {
        "jsonrpc": JSON_RPC_VERSION,
        "id": random.randint(0, 65535),
        "method": "set",
        "params": {"commands": commands},
    }
    set_resp = client.post(payload=json.dumps(data))

    # failed to get set response means something went wrong
    # we have to fail the module
    if not set_resp:
        json_output["failed"] = True
        module.fail_json(**json_output)

    # we have a successfull operation
    if set_resp.get("result"):
        # if diff mode was set without check mode,
        # we add the prepared diff to the output if diff response is not empty
        if module._diff and changed:  # pylint: disable=protected-access
            json_output.update({"diff": {"prepared": diff_resp.get("result")[0]}})
        json_output["changed"] = changed
        json_output["id"] = set_resp["id"]

        # saving configuration if needed
        if not module.check_mode and (
            save_when == "always" or (save_when == "changed" and changed)
        ):
            data = {
                "jsonrpc": JSON_RPC_VERSION,
                "id": random.randint(0, 65535),
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
            set_resp = client.post(payload=json.dumps(data))

            if set_resp and set_resp.get("result"):
                json_output["saved"] = True

        module.exit_json(**json_output)

    # we have an error
    if set_resp.get("error"):
        json_output["failed"] = True
        module.fail_json(msg=set_resp["error"]["message"], id=set_resp["id"])


if __name__ == "__main__":
    main()
