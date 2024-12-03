#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.haxorof.sonatype_nexus.plugins.module_utils.nexus import (
    NexusHelper,
    NexusRepositoryHelper,
)

def repository_filter(item, helper):
    """Filter repositories by name."""
    return item["name"] == helper.module.params["name"]

def main():
    argument_spec = NexusHelper.nexus_argument_spec()
    
    # Use the hosted-specific storage argument spec
    argument_spec.update(
        storage=NexusRepositoryHelper.storage_argument_hosted(),  # Hosted storage spec with writePolicy
        cleanup=dict(
            type="dict",
            options=dict(
                policy_names=dict(type="list", elements="str"),
            ),
        ),
        docker=NexusRepositoryHelper.docker_argument_spec(),  # Docker-specific argument spec
    )
    
    argument_spec.update(NexusRepositoryHelper.common_proxy_argument_spec())

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[("username", "password")],
    )

    helper = NexusHelper()
    result = dict(changed=False, messages=[], json={})
    existing_data = NexusRepositoryHelper.list_filtered_repositories(helper, repository_filter)
    endpoint_path = "/docker/hosted"
    # Prepare the additional data to be passed to the Nexus API
    additional_data = {
        "cleanup": NexusHelper.camalize_param(helper, "cleanup"),
        "docker": NexusHelper.camalize_param(helper, "docker"),
    }

    if module.params["state"] == "present":
        if len(existing_data) > 0:
            content, changed = NexusRepositoryHelper.update_repository(
                helper, endpoint_path, additional_data, existing_data[0]
            )
        else:
            content, changed = NexusRepositoryHelper.create_repository(
                helper, endpoint_path, additional_data
            )
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
