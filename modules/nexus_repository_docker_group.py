#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the haxorof.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import humps

DOCUMENTATION = r"""
---
module: nexus_repository_docker_group
short_description: Manage Docker group repositories
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

def main():
    endpoint_path_to_use = "/docker/group"
    argument_spec = NexusHelper.nexus_argument_spec()
    argument_spec.update(
        member_repos=dict(type="list", elements="str", required=False),
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
            "docker": NexusHelper.camalize_param(helper, "docker"),
            "group": {
                "memberNames": module.params["member_repos"],
            },
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
