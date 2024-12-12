#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the haxorof.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import humps

DOCUMENTATION = r"""
---
module: nexus_repository_docker_proxy
short_description: Manage Docker proxy repositories
"""

EXAMPLES = r"""
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.haxorof.sonatype_nexus.plugins.module_utils.nexus import (
    NexusHelper,
    NexusRepositoryHelper,
)

def repository_filter(item, helper):
    return item["name"] == helper.module.params["name"]

# def adjust_proxy_repository_data(existing_data):
#     """
#     Adjust the existing data for proxy repositories to align with expected input data.
#     """
#     # Remove writePolicy for proxy repositories if present.
#     if "writePolicy" in existing_data.get("storage", {}):
#         existing_data["storage"].pop("writePolicy")
    
#     # Handle the discrepancy between routingRuleName and routingRule.
#     if "routingRuleName" in existing_data:
#         existing_data.update({"routingRule": existing_data.pop("routingRuleName")})
    
#     return existing_data

def main():
    endpoint_path_to_use = "/docker/proxy"
    argument_spec = NexusHelper.nexus_argument_spec()
    argument_spec.update(
        docker=dict(
            type='dict',
            apply_defaults=True,
            options=dict(
                v1_enabled=dict(type="bool", default=False),
                force_basic_auth=dict(type="bool", default=True),
                http_port=dict(type="int"),
                https_port=dict(type="int"),
                subdomain=dict(type="str", required=False, no_log=False),
            ),
        ),
        docker_proxy=dict(
            type='dict',
            apply_defaults=True,
            options=dict(
                index_type=dict(type="str", choices=["HUB", "REGISTRY", "CUSTOM"], default="REGISTRY"),
                index_url=dict(type="str", required=False, no_log=False),
                cache_foreign_layers=dict(type="bool", default=True),
                foreign_layer_url_whitelist=dict(type="list", elements="str", required=False, no_log=False, default=list()),
            ),
        ),
    )
    argument_spec.update(NexusRepositoryHelper.common_proxy_argument_spec(endpoint_path_to_use))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[("username", "password")],
    )

    helper = NexusHelper(module)

    # Seed the result dict in the object
    result = dict(
        changed=False,
        messages=[],
        json={},
    )

    changed, content = True, {}
    existing_data = NexusRepositoryHelper.list_filtered_repositories(helper, repository_filter)
    if module.params["state"] == "present":
        endpoint_path = endpoint_path_to_use
        additional_data = {
 #           "storage": NexusHelper.camalize_param(helper, "storage"),
            "docker": NexusHelper.camalize_param(helper, "docker"),
            "dockerProxy": NexusHelper.camalize_param(helper, "docker_proxy"),
        }
        if len(existing_data) > 0:
            content, changed = NexusRepositoryHelper.update_repository(helper, endpoint_path, additional_data, existing_data[0])
        else:
            content, changed = NexusRepositoryHelper.create_repository(helper, endpoint_path, additional_data)
    else:
        if len(existing_data) > 0:
            content, changed = NexusRepositoryHelper.delete_repository(helper)
        else:
            changed = False
    result["json"] = content
    result["changed"] = changed

    module.exit_json(**result)


if __name__ == "__main__":
    main()