#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the haxorof.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import humps

DOCUMENTATION = r"""
---
module: nexus_repository_npm_proxy
short_description: Manage NPM proxy repositories
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
    argument_spec = NexusHelper.nexus_argument_spec()
    argument_spec.update(
        npm=dict(
            type='dict',
            apply_defaults=True,
            options=dict(
                remove_quarantined=dict(type="bool", default=False),
            ),
        ),
        proxy=dict(
            type='dict',
            apply_defaults=True,
            options=dict(
                remote_url=dict(type="str", required=True),
                content_max_age=dict(type="int", default=-1),
                metadata_max_age=dict(type="int", default=0),
                negative_cache=dict(
                    type='dict',
                    apply_defaults=True,
                    options=dict(
                        enabled=dict(type="bool", default=False),
                        time_to_live=dict(type="int", default=0),
                    ),
                ),
            ),
        ),
        http_client=dict(
            type='dict',
            apply_defaults=True,
            options=dict(
                blocked=dict(type="bool", default=False),
                auto_block=dict(type="bool", default=True),
                connection=dict(
                    type='dict',
                    apply_defaults=True,
                    options=dict(
                        retries=dict(type="int", default=0),
                        user_agent_suffix=dict(type="str", required=False, no_log=False),
                        timeout=dict(type="int", default=60),
                        enable_circular_redirects=dict(type="bool", default=False),
                        enable_cookies=dict(type="bool", default=False),
                        use_trust_store=dict(type="bool", default=False),
                    ),
                ),
                authentication=dict(
                    type='dict',
                    apply_defaults=True,
                    options=dict(
                        type=dict(type="str", choices=["username", "ntlm"], default="username"),
                        username=dict(type="str", required=False, no_log=False),
                        password=dict(type="str", required=False, no_log=True),
                        ntlm_host=dict(type="str", required=False, no_log=False),
                        ntlm_domain=dict(type="str", required=False, no_log=False),
                    ),
                ),
            ),
        ),
    )
    argument_spec.update(NexusRepositoryHelper.common_proxy_argument_spec())
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
        endpoint_path = "/npm/proxy"
        additional_data = {
            "npm": NexusHelper.camalize_param(helper, "npm"),
            "proxy": NexusHelper.camalize_param(helper, "proxy"),
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
