#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the hax0sen.sonatype_nexus project
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
  hax0sen.sonatype_nexus.nexus_script:
    url: "http://172.18.0.2:8081/service/rest/v1/script"
    user: admin
    password: admin123
    method: POST
    name: "change_admin_password"
    content: "{{ lookup('file', '/path/to/change_admin_password.groovy') }}"
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.hax0sen.sonatype_nexus.plugins.module_utils.nexus import NexusHelper

def list_scripts(helper):
    endpoint = "script"
    info, content = helper.request(
        api_url=helper.NEXUS_API_ENDPOINTS[endpoint].format(url=helper.module.params["url"]),
        method="GET",
    )
    if info["status"] in [200]:
        content = content["json"]
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    else:
        helper.module.fail_json(
            msg="Failed to fetch scripts, http_status={status}.".format(status=info["status"])
        )
    return content

def create_script(helper):
    changed = True
    data = {
        "name": helper.module.params["name"],
        "type": "groovy",
        "content": helper.module.params["content"],
    }
    endpoint = "script"
    info, content = helper.request(
        api_url=helper.NEXUS_API_ENDPOINTS[endpoint].format(url=helper.module.params["url"]),
        method="POST",
        data=data,
    )

    if info["status"] == 403:
        helper.generic_permission_failure_msg()
    elif not helper.is_request_status_ok(info):
        helper.module.fail_json(
            msg="Failed to create script {name}, http_status={http_status}, error_msg='{error_msg}'.".format(
                error_msg=info["msg"],
                http_status=info["status"],
                name=helper.module.params["name"],
            )
        )

    return content, changed

def delete_script(helper):
    changed = True
    endpoint = "script"
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
            url=helper.module.params["url"],
            name=helper.module.params["name"],
        ),
        method="DELETE",
    )

    if info["status"] in [404]:
        content.pop("fetch_url_retries", None)
        changed = False
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    elif not helper.is_request_status_ok(info):
        helper.module.fail_json(
            msg="Failed to delete script {name}, http_status={http_status}, error_msg='{error_msg}'.".format(
                error_msg=info["msg"],
                http_status=info["status"],
                name=helper.module.params["name"],
            )
        )

    return content, changed

def update_script(helper, existing_script):
    changed = True
    data = {
        "name": existing_script["name"],
        "type": "groovy",
        "content": helper.module.params["content"],
    }
    endpoint = "script"
    if helper.is_json_data_equal(data, existing_script):
        return existing_script, False

    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
            url=helper.module.params["url"],
            name=helper.module.params["name"],
        ),
        method="PUT",
        data=data,
    )

    if info["status"] in [204]:
        content = data
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    else:
        helper.module.fail_json(
            msg="Failed to update script {name}, http_status={http_status}, error_msg='{error_msg}'.".format(
                error_msg=info["msg"],
                http_status=info["status"],
                name=helper.module.params["name"],
            )
        )

    return content, changed

def manage_script(helper):
    method = helper.module.params["method"]
    content = {}
    changed = True

    if method == "GET":
        content = list_scripts(helper)
        changed = False
    elif method == "POST":
        existing_scripts = list_scripts(helper)
        existing_script = next((script for script in existing_scripts if script["name"] == helper.module.params["name"]), None)
        if existing_script:
            content, changed = update_script(helper, existing_script)
        else:
            content, changed = create_script(helper)
    elif method == "DELETE":
        content, changed = delete_script(helper)
    elif method == "PUT":
        existing_scripts = list_scripts(helper)
        existing_script = next((script for script in existing_scripts if script["name"] == helper.module.params["name"]), None)
        if existing_script:
            content, changed = update_script(helper, existing_script)
        else:
            content, changed = create_script(helper)
    else:
        helper.module.fail_json(msg="Unsupported method: {method}".format(method=method))

    return content, changed

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

    # Seed the result dictionary
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
