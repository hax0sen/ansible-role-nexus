#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the haxorof.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: nexus_script
short_description: Manage scripts in Nexus
"""

EXAMPLES = r"""
- name: Upload Nexus script to change admin password
  haxorof.sonatype_nexus.nexus_script:
    url: "http://172.18.0.2:8081/service/rest/v1/script"
    user: admin
    password: admin123
    method: POST
    name: "change_admin_password"
    content: "{{ lookup('file', '/home/hax0sen/.ansible/collections/ansible_collections/haxorof/sonatype_nexus/files/change_admin_password.groovy') }}"
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.haxorof.sonatype_nexus.plugins.module_utils.nexus import NexusHelper

def manage_script(helper):
    method = helper.module.params["method"]
    endpoint = "script"
    data = {
        "name": helper.module.params["name"],
        "type": "groovy",
        "content": helper.module.params["content"],
    }

    if method == "GET":
        info, content = helper.request(
            api_url=helper.NEXUS_API_ENDPOINTS[endpoint].format(url=helper.module.params["url"]),
            method=method,
        )
    elif method in ["POST", "PUT"]:
        info, content = helper.request(
            api_url=helper.NEXUS_API_ENDPOINTS[endpoint].format(url=helper.module.params["url"]),
            method=method,
            data=data,
        )
    elif method == "DELETE":
        info, content = helper.request(
            api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
                url=helper.module.params["url"],
                name=helper.module.params["name"],
            ),
            method=method,
        )
    else:
        helper.module.fail_json(msg="Unsupported method: {method}".format(method=method))

    if info["status"] in [200, 201, 204]:
        return content, True
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    else:
        helper.module.fail_json(
            msg="Failed to {method} script {name}, http_status={http_status}, error_msg='{error_msg}'.".format(
                method=method,
                name=helper.module.params["name"],
                http_status=info["status"],
                error_msg=info["msg"],
            )
        )

def main():
    argument_spec = NexusHelper.nexus_argument_spec()
    argument_spec.update(
        name=dict(type="str", required=True, no_log=False),
        content=dict(type="str", required=False, no_log=False),
        method=dict(type="str", choices=["GET", "POST", "PUT", "DELETE"], required=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_together=[("username", "password")],
    )

    helper = NexusHelper(module)

    result = dict(
        changed=False,
        messages=[],
        json={},
    )

    content, changed = manage_script(helper)

    result["json"] = content
    result["changed"] = changed

    module.exit_json(**result)

if __name__ == "__main__":
    main()
