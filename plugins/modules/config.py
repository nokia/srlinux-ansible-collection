#!/usr/bin/python
# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

# -*- coding: utf-8 -*-
"""Ansible module for configuring SR Linux devices"""

from __future__ import absolute_import, division, print_function

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nokia.srlinux.plugins.module_utils.const import (
    JSON_RPC_VERSION,
    SAVE_CONFIG_PATH,
    TEXT_FORMAT,
    TOOLS_DATASTORE,
)
from ansible_collections.nokia.srlinux.plugins.module_utils.srlinux import (
    JSONRPCClient,
    convertResponseKeys,
    rpcID,
)

# pylint: disable=invalid-name
__metaclass__ = type

DOCUMENTATION = """
---
module: config
short_description: "Update, replace and delete configuration on SR Linux devices."
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
        type: raw
        description:
          - values to update
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
        type: raw
  datastore:
    type: str
    description:
      - The datastore to use
    choices:
      - candidate
      - tools
    required: false
    default: candidate
  yang_models:
    type: str
    description:
      - YANG models to use for the get operation.
    choices:
      - srl
      - oc
    default: srl
  confirm_timeout:
    type: int
    description:
      - The number of seconds to wait for a confirmation before reverting the commit.
author:
  - Patrick Dumais (@Nokia)
  - Roman Dodin (@Nokia)
  - Walter De Smedt (@Nokia)
"""

EXAMPLES = """
- name: Set system information with values
  nokia.srlinux.config:
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
                "value": {"type": "raw"},
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
                "value": {"type": "raw", "required": True},
            },
        },
        "save_when": {"choices": ["always", "never", "changed"], "default": "never"},
        "datastore": {"choices": ["candidate", "tools"], "default": "candidate"},
        "yang_models": {"choices": ["srl", "oc"], "default": "srl"},
        "confirm_timeout": {"type": "int"},
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
    datastore = module.params.get("datastore")
    yang_models = module.params.get("yang_models")
    confirm_timeout = module.params.get("confirm_timeout")

    commands = []
    for obj in updates:
        obj["action"] = "update"
        commands += [obj]
    for obj in replaces:
        obj["action"] = "replace"
        commands += [obj]
    for obj in deletes:
        obj["action"] = "delete"
        commands += [obj]

    diff_resp = {}
    # if datastore is tools, collecting diff is a noop, as well as check and diff modes
    if datastore != TOOLS_DATASTORE:
        # collecting the diff
        data = {
            "jsonrpc": JSON_RPC_VERSION,
            "id": rpcID(),
            "method": "diff",
            "params": {
                "commands": commands,
                "output-format": TEXT_FORMAT,
                "yang-models": yang_models,
            },
        }

        diff_resp = client.post(payload=json.dumps(data))
        convertResponseKeys(diff_resp)

        # we should fail the module if no diff response is returned
        # or any errors were reported by it
        if not diff_resp or diff_resp.get("error"):
            diff_resp["failed"] = True
            msg = diff_resp.get("error", {}).get("message", "No diff response")
            module.fail_json(msg=msg, method="diff", id=diff_resp["jsonrpc_req_id"])

    # if diff response is not empty, we have a diff
    # we need to set the changed flag to True
    # and save the diff response result in the json_output
    if diff_resp.get("result"):
        res = diff_resp["result"]
        # remove empty lines from the diff output
        res = [x for x in res if x != ""]
        if len(res):
            # save successful diff in the json_output
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
        "id": rpcID(),
        "method": "set",
        "params": {
            "commands": commands,
            "datastore": datastore,
            "yang-models": yang_models,
            # "confirm-timeout": confirm_timeout,
        },
    }
    set_resp = client.post(payload=json.dumps(data))
    convertResponseKeys(set_resp)

    # failed to get set response means something went wrong
    # we have to fail the module
    if not set_resp:
        json_output["failed"] = True
        module.fail_json(**json_output)

    # we have a successful operation
    if set_resp.get("result"):
        # if diff mode was set without check mode,
        # we add the prepared diff to the output if diff response is not empty
        if module._diff and changed:  # pylint: disable=protected-access
            json_output.update({"diff": {"prepared": diff_resp.get("result")[0]}})
        json_output["changed"] = changed
        json_output["jsonrpc_req_id"] = set_resp["jsonrpc_req_id"]

        # saving configuration if needed
        if not module.check_mode and (
            save_when == "always" or (save_when == "changed" and changed)
        ):
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
            set_resp = client.post(payload=json.dumps(data))

            if set_resp and set_resp.get("result"):
                json_output["saved"] = True

        module.exit_json(**json_output)

    # we have an error
    if set_resp.get("error"):
        json_output["failed"] = True
        module.fail_json(
            msg=set_resp["error"]["message"], id=set_resp["jsonrpc_req_id"]
        )


if __name__ == "__main__":
    main()
