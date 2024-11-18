#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the hax0sen.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: nexus_security_ldap_info
short_description: List LDAP servers in Nexus
"""

EXAMPLES = r"""
- name: Get LDAP servers connected to this Nexus
  hax0sen.sonatype_nexus.nexus_security_ldap_info:
    url: "http://172.18.0.3:8081"
    user: admin
    password: admin123
    method: GET
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.hax0sen.sonatype_nexus.plugins.module_utils.nexus import NexusHelper

def list_ldap_servers(helper):
    endpoint = "ldap"
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
            msg="Failed to fetch LDAP servers, http_status={status}.".format(status=info["status"])
        )
    return content

def main():
    argument_spec = NexusHelper.nexus_argument_spec()
    argument_spec.update(
        method=dict(type="str", choices=["GET"], required=True),
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

    if module.params["method"] == "GET":
        content = list_ldap_servers(helper)
    else:
        helper.module.fail_json(msg="Unsupported method: {method}".format(method=module.params["method"]))

    result["json"] = content
    result["changed"] = False

    module.exit_json(**result)

if __name__ == "__main__":
    main()
