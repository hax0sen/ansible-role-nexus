#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the hax0sen.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: nexus_script_run
short_description: Run a script in Nexus
"""

EXAMPLES = r"""
- name: Trigger script
  hax0sen.sonatype_nexus.nexus_script_run:
    url: "http://172.18.0.3:8081"
    user: admin
    password: admin123
    name: "change_admin_password"
    body: "{{ {'new_password': nexus_admin_password} | to_json }}"
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.hax0sen.sonatype_nexus.plugins.module_utils.nexus import NexusHelper

def run_script(helper):
    endpoint = "script"
    headers = {
        "Content-Type": "application/json"
    }
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}/run").format(
            url=helper.module.params["url"],
            name=helper.module.params["name"],
        ),
        method="POST",
        headers=headers,
        data=helper.module.params["body"]
    )
    if info["status"] in [200, 204]:
        return content, True
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    else:
        helper.module.fail_json(
            msg="Failed to run script {name}, http_status={status}, error_msg='{error_msg}'.".format(
                name=helper.module.params["name"],
                status=info["status"],
                error_msg=info["msg"],
            )
        )

def main():
    argument_spec = NexusHelper.nexus_argument_spec()
    argument_spec.update(
        name=dict(type="str", required=True, no_log=False),
        body=dict(type="str", required=True, no_log=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_together=[("username", "password")],
    )

    helper = NexusHelper(module)

    # Seed the result dictionary
    result = dict(
        changed=False,
        messages=[],
        json={},
    )

    content, changed = run_script(helper)

    result["json"] = content
    result["changed"] = changed

    module.exit_json(**result)

if __name__ == "__main__":
    main()
