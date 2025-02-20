#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the haxorof.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: nexus_roles
short_description: Create/Update/Delete Nexus roles
"""

EXAMPLES = r"""
- name: Setup Nexus roles
  haxorof.sonatype_nexus.nexus_roles:
    url: "http://172.18.0.2:8081"
    user: admin
    password: admin123
    id: "{{ item.id }}"
    name: "{{ item.name }}"
    description: "{{ item.description }}"
    privileges: "{{ item.privileges }}"
    roles: "{{ item.roles }}"
  loop: "{{ nexus_roles }}"
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.haxorof.sonatype_nexus.plugins.module_utils.nexus import (
    NexusHelper,
)

def list_role(helper, role_id):
    """Fetch a role's details from Nexus, ensuring source=default is included."""
    endpoint = "roles"
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{id}?source=default").format(
            url=helper.module.params["url"],
            id=role_id
        ),
        method="GET",
    )

    if info["status"] == 200:
        return content.get("json", content)
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    elif info["status"] == 404:
        return None  # Role does not exist
    else:
        helper.module.fail_json(
            msg="Failed to fetch role {role_id}, http_status={status}.".format(
                role_id=role_id,
                status=info["status"],
            )
        )

    return None

def create_role(helper):
    """Create a new role in Nexus."""
    changed = True
    data = {
        "id": helper.module.params["id"],
        "name": helper.module.params["name"],
        "description": helper.module.params["description"],
        "privileges": helper.module.params["privileges"],
        "roles": helper.module.params["roles"],
    }
    endpoint = "roles"
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint]).format(
            url=helper.module.params["url"]
        ),
        method="POST",
        data=data,
    )

    if info["status"] == 403:
        helper.generic_permission_failure_msg()
    elif not helper.is_request_status_ok(info):
        helper.module.fail_json(
            msg="Failed to create role {role}, http_status={http_status}, error_msg='{error_msg}'.".format(
                error_msg=info["msg"],
                http_status=info["status"],
                role=helper.module.params["id"],
            )
        )

    return content, changed

def delete_role(helper):
    """Delete an existing role from Nexus."""
    changed = True
    endpoint = "roles"
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{id}").format(
            url=helper.module.params["url"],
            id=helper.module.params["id"],
        ),
        method="DELETE",
    )

    if info["status"] == 404:
        content.pop("fetch_url_retries", None)
        changed = False
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    elif not helper.is_request_status_ok(info):
        helper.module.fail_json(
            msg="Failed to delete role {role}, http_status={http_status}, error_msg='{error_msg}'.".format(
                error_msg=info["msg"],
                http_status=info["status"],
                role=helper.module.params["id"],
            )
        )

    return content, changed


def update_role(helper, existing_role):
    """Update an existing role in Nexus if changes are required."""
    changed = True
    data = {
        "id": existing_role["id"],
        "name": existing_role["name"],
        "description": existing_role["description"],
        "privileges": existing_role["privileges"],
        "roles": existing_role["roles"],
    }

    if helper.module.params["name"]:
        data["name"] = helper.module.params["name"]
    if helper.module.params["description"]:
        data["description"] = helper.module.params["description"]
    if helper.module.params["privileges"]:
        data["privileges"] = helper.module.params["privileges"]
    if helper.module.params["roles"]:
        data["roles"] = helper.module.params["roles"]

    endpoint = "roles"

    if helper.is_json_data_equal(data, existing_role):
        return existing_role, False  # No change needed

    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{id}").format(
            url=helper.module.params["url"],
            id=helper.module.params["id"],
        ),
        method="PUT",
        data=data,
    )

    if info["status"] == 204:
        content = data
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    else:
        helper.module.fail_json(
            msg="Failed to update role {role}, http_status={http_status}, error_msg='{error_msg}'.".format(
                error_msg=info["msg"],
                http_status=info["status"],
                role=helper.module.params["id"],
            )
        )

    return content, changed


def main():
    """Main function for the Ansible module."""
    argument_spec = NexusHelper.nexus_argument_spec()
    argument_spec.update(
        id=dict(type="str", required=True, no_log=False),
        name=dict(type="str", required=True, no_log=False),
        description=dict(type="str", required=False, no_log=False),
        privileges=dict(
            type="list", elements="str", required=False, no_log=False, default=list()
        ),
        roles=dict(
            type="list", elements="str", required=False, no_log=False, default=list()
        ),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_together=[("username", "password")],
    )

    helper = NexusHelper(module)

    # Seed the result dict in the object
    result = dict(
        changed=False,
        messages=[],
        json={},
    )

    content = {}
    changed = False
    role_id = module.params["id"]

    existing_role = list_role(helper, role_id)

    if existing_role is not None:
        if module.params["state"] == "present":
            content, changed = update_role(helper, existing_role)
        else:
            content, changed = delete_role(helper)
    else:
        if module.params["state"] == "present":
            content, changed = create_role(helper)
        else:
            module.fail_json(
                msg="Role {role_id} does not exist and cannot be deleted.".format(
                    role_id=role_id,
                )
            )

    result["json"] = content
    result["changed"] = changed
    module.exit_json(**result)


if __name__ == "__main__":
    main()