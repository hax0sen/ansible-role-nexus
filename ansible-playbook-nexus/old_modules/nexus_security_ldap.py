#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the haxorof.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: nexus_security_ldap
short_description: Manage LDAP servers in Nexus
"""

EXAMPLES = r"""
- name: Ensure LDAP server is present
nexus_security_ldap:
    state: present
    url: "http://nexus.example.com"
    username: "admin"
    password: "admin123"
    ldap_name: "MyLDAPServer"
    ldap_protocol: "LDAP"
    ldap_host: "ldap.example.com"
    ldap_port: 389
    ldap_searchBase: "dc=example,dc=com"
    ldap_authScheme: "SIMPLE"
    ldap_connectionTimeoutSeconds: 30
    ldap_connectionRetryDelaySeconds: 5
    ldap_maxIncidentsCount: 3
    ldap_authPassword: "ldap_password"

- name: Ensure LDAP server is absent
nexus_security_ldap:
    state: absent
    url: "http://nexus.example.com"
    username: "admin"
    password: "admin123"
    ldap_name: "MyLDAPServer"
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.haxorof.sonatype_nexus.plugins.module_utils.nexus import NexusHelper

def get_ldap_server(helper):
    """Retrieve the LDAP server configuration by name."""
    ldap_name = helper.module.params.get("current_ldap_name") or helper.module.params["ldap_name"]  # Use current_ldap_name if specified
    endpoint = "ldap"
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
            url=helper.module.params["url"],
            name=ldap_name,
        ),
        method="GET",
    )
    if info["status"] == 200:
        return content
    elif info["status"] == 404:
        return None  # Return None if not found
    elif info["status"] == 403:
        helper.module.fail_json(
            msg=f"Insufficient permissions to read LDAP server '{ldap_name}'."
        )
    else:
        helper.module.fail_json(
            msg=f"Failed to read LDAP server '{ldap_name}', http_status={info['status']}."
        )
    return content

def get_ldap_data(helper):
    """Assemble the data structure for LDAP server configuration."""
    return {
        "name": helper.module.params["ldap_name"],
        "protocol": helper.module.params["ldap_protocol"],
        "useTrustStore": helper.module.params["ldap_useTrustStore"],
        "host": helper.module.params["ldap_host"],
        "port": helper.module.params["ldap_port"],
        "searchBase": helper.module.params["ldap_searchBase"],
        "authScheme": helper.module.params["ldap_authScheme"],
        "authRealm": helper.module.params["ldap_authRealm"],
        "authUsername": helper.module.params["ldap_authUsername"],
        "authPassword": helper.module.params["ldap_authPassword"],
        "connectionTimeoutSeconds": helper.module.params["ldap_connectionTimeoutSeconds"],
        "connectionRetryDelaySeconds": helper.module.params["ldap_connectionRetryDelaySeconds"],
        "maxIncidentsCount": helper.module.params["ldap_maxIncidentsCount"],
        "userBaseDn": helper.module.params["ldap_userBaseDn"],
        "userSubtree": helper.module.params["ldap_userSubtree"],
        "userObjectClass": helper.module.params["ldap_userObjectClass"],
        "userLdapFilter": helper.module.params["ldap_userLdapFilter"],
        "userIdAttribute": helper.module.params["ldap_userIdAttribute"],
        "userRealNameAttribute": helper.module.params["ldap_userRealNameAttribute"],
        "userEmailAddressAttribute": helper.module.params["ldap_userEmailAddressAttribute"],
        "userPasswordAttribute": helper.module.params["ldap_userPasswordAttribute"],
        "ldapGroupsAsRoles": helper.module.params["ldap_ldapGroupsAsRoles"],
        "groupType": helper.module.params["ldap_groupType"],
        "groupBaseDn": helper.module.params["ldap_groupBaseDn"],
        "groupSubtree": helper.module.params["ldap_groupSubtree"],
        "groupObjectClass": helper.module.params["ldap_groupObjectClass"],
        "groupIdAttribute": helper.module.params["ldap_groupIdAttribute"],
        "groupMemberAttribute": helper.module.params["ldap_groupMemberAttribute"],
        "groupMemberFormat": helper.module.params["ldap_groupMemberFormat"],
        "userMemberOfAttribute": helper.module.params["ldap_userMemberOfAttribute"],
    }

def create_ldap_server(helper):
    """Create a new LDAP server."""
    data = get_ldap_data(helper)
    endpoint = "ldap"

    # Check if the LDAP server already exists
    existing_ldap = get_ldap_server(helper)
    if existing_ldap:
        return existing_ldap, False

    # Create the LDAP server
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint]).format(url=helper.module.params["url"]),
        method="POST",
        data=data,
    )

    # Handle API response
    if info["status"] == 201:
        content = {
            "msg": f"LDAP server '{helper.module.params['ldap_name']}' created successfully"
        }
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    elif not helper.is_request_status_ok(info):
        helper.module.fail_json(
            msg=f"Failed to create LDAP server {helper.module.params['ldap_name']}, http_status={info['status']}, error_msg='{info['msg']}'."
        )
    return content, True

def update_ldap_server(helper, existing_ldap):
    """Update an existing LDAP server if differences are found."""
    data = get_ldap_data(helper)  # Get the desired configuration
    endpoint = "ldap"

    # Use current_ldap_name if specified; otherwise, use the desired ldap_name
    ldap_name = helper.module.params.get("current_ldap_name") or helper.module.params["ldap_name"]

    # Copy the existing LDAP configuration to compare and modify
    updated_ldap = existing_ldap.copy()
    changes_detected = False

    # Compare existing LDAP settings with the desired state
    for key, value in data.items():
        if key != "authPassword" and existing_ldap.get(key) != value:
            updated_ldap[key] = value
            changes_detected = True

    # If no changes detected, return existing LDAP configuration
    if not changes_detected:
        return existing_ldap, False

    # Always include authPassword in the payload if provided in the input
    if "authPassword" in data:
        updated_ldap["authPassword"] = data["authPassword"]

    # Make a PUT request using the current or original ldap_name
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
            url=helper.module.params["url"],
            name=ldap_name,
        ),
        method="PUT",
        data=updated_ldap,
    )

    # Handle API response
    if info["status"] in [204]:  # Successful update
        return updated_ldap, True
    elif info["status"] == 403:  # Permission error
        helper.generic_permission_failure_msg()
    else:  # Other errors
        helper.module.fail_json(
            msg=f"Failed to update LDAP server {ldap_name}, http_status={info['status']}, error_msg='{info.get('msg', 'Unknown error')}'."
        )

    return content, True

def delete_ldap_server(helper):
    """Delete an existing LDAP server."""
    endpoint = "ldap"
    changed = True
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
            url=helper.module.params["url"],
            name=helper.module.params["ldap_name"],
        ),
        method="DELETE",
    )
    if info["status"] in [404]:
        return {}, False
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    elif not helper.is_request_status_ok(info):
        helper.module.fail_json(
            msg=f"Failed to delete LDAP server {helper.module.params['ldap_name']}, http_status={info['status']}, error_msg='{info['msg']}'."
        )
    elif info["status"] == 204:
        content = {
            "msg": f"LDAP server '{helper.module.params['ldap_name']}' deleted successfully"
        }
    return content, changed

def main():
    argument_spec = NexusHelper.nexus_argument_spec()
    argument_spec.update(
        method=dict(type="str", choices=["GET"], required=False),
        state=dict(type="str", choices=["present", "absent"], required=False),
        current_ldap_name=dict(type="str", required=False),
        ldap_name=dict(type="str", required=True),
        url=dict(type="str", required=True),
        ldap_protocol=dict(type="str", choices=["LDAP", "LDAPS"], required=False),
        ldap_host=dict(type="str", required=False),
        ldap_port=dict(type="int", required=False),
        ldap_searchBase=dict(type="str", required=False),
        ldap_authScheme=dict(type="str", choices=["NONE", "SIMPLE", "DIGEST_MD5", "CRAM_MD5"], required=False),
        ldap_connectionTimeoutSeconds=dict(type="int", required=False),
        ldap_connectionRetryDelaySeconds=dict(type="int", required=False),
        ldap_maxIncidentsCount=dict(type="int", required=False),
        ldap_authPassword=dict(type="str", required=False, no_log=True),
        ldap_groupType=dict(type="str", choices=["STATIC", "DYNAMIC"], required=False),
        ldap_authRealm=dict(type="str", required=False),
        ldap_authUsername=dict(type="str", required=False),
        ldap_userMemberOfAttribute=dict(type="str", required=False),
        ldap_useTrustStore=dict(type="bool", required=False, default=False),
        ldap_userBaseDn=dict(type="str", required=False),
        ldap_userSubtree=dict(type="bool", required=False, default=False),
        ldap_userObjectClass=dict(type="str", required=False),
        ldap_userLdapFilter=dict(type="str", required=False),
        ldap_userIdAttribute=dict(type="str", required=False),
        ldap_userRealNameAttribute=dict(type="str", required=False),
        ldap_userEmailAddressAttribute=dict(type="str", required=False),
        ldap_userPasswordAttribute=dict(type="str", required=False),
        ldap_ldapGroupsAsRoles=dict(type="bool", required=False, default=False),
        ldap_groupBaseDn=dict(type="str", required=False),
        ldap_groupSubtree=dict(type="bool", required=False, default=False),
        ldap_groupObjectClass=dict(type="str", required=False),
        ldap_groupIdAttribute=dict(type="str", required=False),
        ldap_groupMemberAttribute=dict(type="str", required=False),
        ldap_groupMemberFormat=dict(type="str", required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
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

    # Main logic for managing LDAP server
    if module.params["method"] == "GET":
        content = get_ldap_server(helper)
    else:
        existing_ldap = get_ldap_server(helper)
        if module.params["state"] == "present":
            if existing_ldap:
                content, changed = update_ldap_server(helper, existing_ldap)
            else:
                content, changed = create_ldap_server(helper)
        else:  # state == "absent"
            if existing_ldap:
                content, changed = delete_ldap_server(helper)
                module.params["state"] = "absent"  # Ensure state is set to absent
            else:
                changed = False  # Already absent

    # Final result
    result["json"] = content
    result["changed"] = changed
    module.exit_json(**result)

if __name__ == "__main__":
    main()

