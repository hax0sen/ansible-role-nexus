#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the haxorof.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: nexus_security_ldap_order
short_description: Change LDAP server order in Nexus
"""

EXAMPLES = r"""
- name: Set LDAP server order in Nexus
  haxorof.sonatype_nexus.nexus_security_ldap_order:
    url: "http://172.18.0.3:8081"
    user: admin
    password: admin123
    order_list:
      - secondary
      - my-ldap-server
      - my-ldap-server2
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.haxorof.sonatype_nexus.plugins.module_utils.nexus import NexusHelper
import json

def get_current_ldap_order(helper):
    endpoint = "ldap"
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint]).format(
            url=helper.module.params["url"]
        ),
        method="GET",
        headers={'Content-Type': 'application/json'}
    )
    if info["status"] in [200]:
        current_ldap = content["json"]
        current_order = [ldap["name"] for ldap in current_ldap]
        return current_order
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    else:
        helper.module.fail_json(
            msg="Failed to fetch current LDAP order, http_status={status}, response={response}".format(
                status=info["status"], response=content
            )
        )
    return []

def change_ldap_order(helper, order_list):
    current_order = get_current_ldap_order(helper)
    if current_order == order_list:
        return False, current_order

    endpoint = "ldap"
    data = json.dumps(order_list)
    info, content = helper.request(
    api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/change-order").format(            
        url=helper.module.params["url"]
        ),
        method="POST",
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    if info["status"] in [200, 204]:
        content = content["json"] if info["status"] == 200 else {}
    elif info["status"] == 403:
        helper.generic_permission_failure_msg()
    else:
        helper.module.fail_json(
            msg="Failed to change LDAP order, http_status={status}, response={response}".format(
                status=info["status"], response=content
            )
        )
    return True, content

def main():
    argument_spec = NexusHelper.nexus_argument_spec()
    argument_spec.update(
        order_list=dict(type="list", required=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[("username", "password")],
    )

    helper = NexusHelper(module)
    result = dict(
        changed=False,
        messages=[],
        json={},
    )

    changed, content = change_ldap_order(helper, module.params["order_list"])

    result["json"] = content
    result["changed"] = changed

    module.exit_json(**result)

if __name__ == "__main__":
    main()
