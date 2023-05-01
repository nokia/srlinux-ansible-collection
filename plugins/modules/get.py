#!/usr/bin/python
# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

"""Ansible module for retrieving configuration and state from SR Linux devices"""

from __future__ import absolute_import, division, print_function

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nokia.srlinux.plugins.module_utils.const import (
    JSON_RPC_VERSION,
)
from ansible_collections.nokia.srlinux.plugins.module_utils.srlinux import (
    JSONRPCClient,
    convertIdentifiers,
    convertResponseKeys,
    rpcID,
)

# pylint: disable=invalid-name
__metaclass__ = type

DOCUMENTATION = """
---
module: get
short_description: "Retrieve configuration or state element from Nokia SR Linux devices."
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
          - baseline
          - candidate
          - running
          - state
          - tools
        default: state
        required: true
      path:
        description:
          - the YANG path of a datastore node
        type: str
        required: true
      yang_models:
        type: str
        description:
          - YANG models to use for the get operation.
        choices:
          - srl
          - oc

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
                    "choices": ["baseline", "candidate", "running", "state", "tools"],
                    "default": "state",
                    "required": True,
                },
                "yang_models": {
                    "type": "str",
                    "choices": ["srl", "oc"],
                },
            },
        },
    }

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    client = JSONRPCClient(module)

    paths = module.params.get("paths")
    convertIdentifiers(paths)

    data = {
        "jsonrpc": JSON_RPC_VERSION,
        "id": rpcID(),
        "method": "get",
        "params": {
            "commands": paths,
        },
    }

    response = client.post(payload=json.dumps(data))
    convertResponseKeys(response)

    if response and response.get("result"):
        module.exit_json(**response)

    # handling error case
    response["failed"] = True
    module.fail_json(
        msg=response["error"]["message"],
        jsonrpc_req_id=response["jsonrpc_req_id"],
    )


if __name__ == "__main__":
    main()
