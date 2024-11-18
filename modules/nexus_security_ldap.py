#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the hax0sen.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: nexus_security_ldap
short_description: Manage LDAP servers in Nexus
"""

EXAMPLES = r"""

"""
RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.hax0sen.sonatype_nexus.plugins.module_utils.nexus import NexusHelper

def get_ldap_server(helper):
    endpoint = "ldap"
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
            url=helper.module.params["url"],
            name=helper.module.params["ldap_name"],
        ),
        method="GET",
    )
    if info["status"] in [200]:
        content = [content]
    elif info["status"] in [404]:
        content = []
    elif info["status"] == 403:
        helper.module.fail_json(
            msg="Insufficient permissions to read LDAP server '{ldap_name}'.".format(
                ldap_name=helper.module.params["ldap_name"],
            )
        )
    else:
        helper.module.fail_json(
            msg="Failed to read LDAP server '{ldap_name}', http_status={status}.".format(
                ldap_name=helper.module.params["ldap_name"],
                status=info["status"],
            )
        )
    return content

def get_ldap_data(helper):
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
    changed = True
    data = get_ldap_data(helper)
    endpoint = "ldap"
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint]).format(
            url=helper.module.params["url"],
        ),
        method="POST",
        data=data,
    )
    if info["status"] == 403:
        helper.generic_permission_failure_msg()
    elif not helper.is_request_status_ok(info):
        helper.module.fail_json(
            msg="Failed to create LDAP server {name}, http_status={http_status}, error_msg='{error_msg}'.".format(
                error_msg=info["msg"],
                http_status=info["status"],
                name=helper.module.params["ldap_name"],
            )
        )

    return content, changed

def update_ldap_server(helper, existing_ldap):
    changed = True
    data = get_ldap_data(helper)
    endpoint = "ldap"
    if helper.is_json_data_equal(data, existing_ldap):
        return existing_ldap, False

    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
            url=helper.module.params["url"],
            name=helper.module.params["ldap_name"],
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
            msg="Failed to update LDAP server {name}, http_status={http_status}, error_msg='{error_msg}'.".format(
                error_msg=info["msg"],
                http_status=info["status"],
                name=helper.module.params["ldap_name"],
            )
        )

    return content, changed

def delete_ldap_server(helper):
    changed = True
    endpoint = "ldap"
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
            url=helper.module.params["url"],
            name=helper.module.params["ldap_name"],
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
            msg="Failed to delete LDAP server {name}, http_status={http_status}, error_msg='{error_msg}'.".format(
                error_msg=info["msg"],
                http_status=info["status"],
                name=helper.module.params["ldap_name"],
            )
        )

    return content, changed

def manage_ldap_server(helper):
    method = helper.module.params["method"]
    content = {}
    changed = True

    if method == "GET":
        content = get_ldap_server(helper)
        changed = False
    elif method == "POST":
        existing_ldap = get_ldap_server(helper)
        if existing_ldap:
            helper.module.log(msg="LDAP server already exists, no changes made.")
            content = existing_ldap
            changed = False
        else:
            content, changed = create_ldap_server(helper)
    elif method == "DELETE":
        content, changed = delete_ldap_server(helper)
    elif method == "PUT":
        existing_ldap = get_ldap_server(helper)
        if existing_ldap:
            content, changed = update_ldap_server(helper, existing_ldap)
        else:
            content, changed = create_ldap_server(helper)
    else:
        helper.module.fail_json(msg="Unsupported method: {method}".format(method=method))

    return content, changed
           
def main():
    argument_spec = NexusHelper.nexus_argument_spec()
    argument_spec.update(
        method=dict(type="str", choices=["GET", "POST", "PUT", "DELETE"], required=True),
        
        # Required parameters from API documentation
        ldap_name=dict(type="str", required=True),
        ldap_protocol=dict(type="str", choices=["LDAP", "LDAPS"], required=True),
        ldap_host=dict(type="str", required=True),
        ldap_port=dict(type="int", required=True),
        ldap_searchBase=dict(type="str", required=True),
        ldap_authScheme=dict(type="str", choices=["NONE", "SIMPLE", "DIGEST_MD5", "CRAM_MD5"], required=True),
        ldap_connectionTimeoutSeconds=dict(type="int", required=True),
        ldap_connectionRetryDelaySeconds=dict(type="int", required=True),
        ldap_maxIncidentsCount=dict(type="int", required=True),
        ldap_authPassword=dict(type="str", required=True, no_log=True),
        
        # Conditional required parameters
        ldap_groupType=dict(type="str", choices=["STATIC", "DYNAMIC"], required=False), # Required if ldapGroupsAsRoles is True
        ldap_authRealm=dict(type="str", required=False), # Required if authScheme is CRAM_MD5 or DIGEST_MD5
        ldap_authUsername=dict(type="str", required=False), # Required if authScheme other than NONE
        ldap_userMemberOfAttribute=dict(type="str", required=False), # Required if groupType is dynamic
        
        # Optional LDAP and user-specific fields
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

        # Optional group-specific fields
        ldap_groupBaseDn=dict(type="str", required=False),
        ldap_groupSubtree=dict(type="bool", required=False, default=False),
        ldap_groupObjectClass=dict(type="str", required=False), # Required if groupType is static
        ldap_groupIdAttribute=dict(type="str", required=False), # Required if groupType is static
        ldap_groupMemberAttribute=dict(type="str", required=False), # Required if groupType is static
        ldap_groupMemberFormat=dict(type="str", required=False), # Required if groupType is static
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

    content, changed = manage_ldap_server(helper)

    result["json"] = content
    result["changed"] = changed

    module.exit_json(**result)

if __name__ == "__main__":
    main()
