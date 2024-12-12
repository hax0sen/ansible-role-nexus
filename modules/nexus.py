#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the haxorof.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import time
import os
import stat
import humps
from os import close
from tempfile import mkstemp
from traceback import format_exc

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import fetch_url, basic_auth_header


class NexusHelper:
    NEXUS_API_URL = "http://localhost:8081"
    NEXUS_API_BASE_PATH = "/service/rest"

    NEXUS_API_ENDPOINTS = {
        "anonymous": "{url}" + NEXUS_API_BASE_PATH + "/v1/security/anonymous",
        # "assets": "{url}" + NEXUS_API_BASE_PATH + "/v1/assets",
        # "azureblobstore": "{url}" + NEXUS_API_BASE_PATH + "/v1/azureblobstore",
        "blobstores": "{url}" + NEXUS_API_BASE_PATH + "/v1/blobstores",
        # "certificates": "{url}" + NEXUS_API_BASE_PATH + "/v1/ssl",
        # "components": "{url}" + NEXUS_API_BASE_PATH + "/v1/components",
        # "content-selectors": "{url}" + NEXUS_API_BASE_PATH + "/v1/security/content-selectors",
        # "email": "{url}" + NEXUS_API_BASE_PATH + "/v1/email",
        # "formats": "{url}" + NEXUS_API_BASE_PATH + "/v1/formats",
        # "iq": "{url}" + NEXUS_API_BASE_PATH + "/v1/iq",
        "ldap": "{url}" + NEXUS_API_BASE_PATH + "/v1/security/ldap",
        # "lifecycle": "{url}" + NEXUS_API_BASE_PATH + "/v1/lifecycle",
        # "privileges": "{url}" + NEXUS_API_BASE_PATH + "/v1/security/privileges",
        "read-only": "{url}" + NEXUS_API_BASE_PATH + "/v1/read-only",
        # "realms": "{url}" + NEXUS_API_BASE_PATH + "/v1/security/realms",
        "repositories": "{url}" + NEXUS_API_BASE_PATH + "/v1/repositories",
        "repository-settings": "{url}" + NEXUS_API_BASE_PATH + "/v1/repositorySettings",
        "roles": "{url}" + NEXUS_API_BASE_PATH + "/v1/security/roles",
        "routing-rules": "{url}" + NEXUS_API_BASE_PATH + "/v1/routing-rules",
        "script": "{url}" + NEXUS_API_BASE_PATH + "/v1/script",
        # "search": "{url}" + NEXUS_API_BASE_PATH + "/v1/search",
        "status": "{url}" + NEXUS_API_BASE_PATH + "/v1/status",
        # "support": "{url}" + NEXUS_API_BASE_PATH + "/v1/support",
        # "system": "{url}" + NEXUS_API_BASE_PATH + "/v1/system",
        # "tasks": "{url}" + NEXUS_API_BASE_PATH + "/v1/tasks",
        "user-sources": "{url}" + NEXUS_API_BASE_PATH + "/v1/security/user-sources",
        "users": "{url}" + NEXUS_API_BASE_PATH + "/v1/security/users",
        "user-tokens": "{url}" + NEXUS_API_BASE_PATH + "/v1/security/user-tokens",
    }

    def __init__(self, module):
        self.module = module
        self.module.params["url_username"] = self.module.params["username"]
        self.module.params["url_password"] = self.module.params["password"]
        if self.module.params["url"] is None:
            self.module.params["url"] = self.NEXUS_API_URL

    def nexus_argument_spec():
        return dict(
            url=dict(type="str", no_log=False, required=False),
            username=dict(
                type="str",
                no_log=False,
                required=False,
                default=None,
                aliases=["user"],
                fallback=(env_fallback, ["NEXUS_USERNAME"]),
            ),
            password=dict(
                type="str",
                no_log=True,
                required=False,
                default=None,
                fallback=(env_fallback, ["NEXUS_PASSWORD"]),
            ),
            validate_certs=dict(type="bool", default=True),
            use_proxy=dict(type="bool", default=True),
            return_content=dict(type="bool", default=True),
            sleep=dict(type="int", default=5),
            retries=dict(type="int", default=3),
        )

    def generic_permission_failure_msg(self):
        self.module.fail_json(
            msg="The user does not have permission to perform the operation."
        )

    def generic_failure_msg(self, message, request_info):
        self.module.fail_json(
            msg=message + ", http_status={http_status}, error_msg={error_msg}, body={body}.".format(
                http_status=request_info["status"],
                error_msg=request_info["msg"],
                body=request_info["body"],
            )
        )

    def request(self, api_url, method, data=None, headers=None):
        headers = headers or {}

        headers.update(
            {
                "Authorization": basic_auth_header(
                    self.module.params["username"], self.module.params["password"]
                )
            }
        )

        if isinstance(data, dict):
            data = self.module.jsonify(data)
            if not ("Content-type" in headers):
                headers.update(
                    {
                        "Content-type": "application/json",
                    }
                )

        retries = 1
        while retries <= self.module.params["retries"]:
            response, info = fetch_url(
                module=self.module,
                url=api_url,
                method=method,
                headers=headers,
                data=data,
                force=True,
                use_proxy=self.module.params["use_proxy"],
            )
            if (info is not None) and (info["status"] != -1):
                break
            time.sleep(self.module.params["sleep"])
            retries += 1

        content = {}

        if response is not None:
            body = to_text(response.read())
            if body:
                try:
                    js = json.loads(body)
                    if isinstance(js, dict):
                        content = js
                    else:
                        content["json"] = js
                except ValueError as e:
                    content["content"] = body

        if not self.is_request_status_ok(info):
            content["fetch_url_retries"] = retries

        if info["status"] == 401:
            self.module.fail_json(
                msg="Authentication required."
            )
        elif info["status"] in [503]:
            self.module.fail_json(
                msg="Unavailable to service requests."
            )

        # For debugging
        # if info["status"] not in [200]:
        #     self.module.fail_json(msg="{info} # {content}".format(info=info, content=content))
        return info, content

    def is_request_status_ok(self, info):
        return info["status"] in [200, 201, 204]

    def generate_url_query(self, params: dict):
        """Generates a complete URL query including question mark.

        Args:
            params (dict): A dictionary with query parameter key and what module parameter to map it with

        Returns:
            string: Returns a query as a string including question mark in front.
        """
        query_params = []
        for k, v in params.items():
            if self.module.params[v] != None:
                query_params.append(
                    "{key}={value}".format(key=k, value=self.module.params[v])
                )
        query = "&".join(query_params)
        return "?" + query if len(query) > 0 else ""

    def is_json_data_equal(self, new_data, existing_data):
        """ Compares JSON data and is considered equal if all keys and its values in new_data exists in existing_data.

        Args:
            new_data (_type_): new data.
            existing_data (_type_): existing data.

        Returns:
            _type_: Returns true if all keys and its values in new_data exists in existing_data.
        """
        return all(
            existing_data[k] == v for k, v in new_data.items() if k in existing_data
        )

    def camalize_param(helper, param_name):
        ret_value = None if helper.module.params[param_name] is None else humps.camelize(helper.module.params[param_name])
        return ret_value


class NexusRepositoryHelper:
    def storage_argument_spec():
        return dict(
            type='dict',
            # apply_defaults=True,
            options=dict(
                blob_store_name=dict(type="str", no_log=False, required=False), # Required for create
                strict_content_type_validation=dict(type="bool", default=True),
            ),
        )
    def storage_argument_spec_hosted():
        return dict(
            type='dict',
            # apply_defaults=True,
            options=dict(
                blob_store_name=dict(type="str", required=False),
                strict_content_type_validation=dict(type="bool", default=False),
                write_policy=dict(type="str", choices=["allow", "allow_once", "deny"], default="allow_once"),
                latest_policy=dict(type="bool", default=False), # New parameter
            ),
        )
    def storage_argument_spec_common():
        return dict(
            type='dict',
            # apply_defaults=True,
            options=dict(
                blob_store_name=dict(type="str", required=False),
                strict_content_type_validation=dict(type="bool", default=False),
                write_policy=dict(type="str", choices=["allow", "allow_once", "deny"], default="allow_once"),
            ),
        )
    def cleanup_policy_argument_spec():
        return  dict(
            type='dict',
            # apply_defaults=True,
            options=dict(
                policy_names=dict(type="list", elements="str", required=False, no_log=False, default=list()),
            ),
        )

    def proxy_argument_spec():
        return dict(
            type='dict',
            # apply_defaults=True,
            options=dict(
                remote_url=dict(type="str", no_log=False, required=False), # Required for create/update
                content_max_age=dict(type="int", default=1440),
                metadata_max_age=dict(type="int", default=1440),
            ),
        )

    def negative_cache_argument_spec():
        return dict(
            type='dict',
            apply_defaults=True,
            options=dict(
                enabled=dict(type="bool", default=True),
                time_to_live=dict(type="int", default=1440),
            ),
        )

    def http_client_argument_spec():
        return dict(
            type='dict',
            apply_defaults=True,
            options=dict(
                blocked=dict(type="bool", default=False),
                auto_block=dict(type="bool", default=True),
                connection=dict(
                    type='dict',
                    apply_defaults=True,
                    options=dict(
                        retries=dict(type="int"),
                        user_agent_suffix=dict(type="str", no_log=False, required=False),
                        timeout=dict(type="int"),
                        enable_circular_redirects=dict(type="bool", default=False),
                        enable_cookies=dict(type="bool", default=False),
                        use_trust_store=dict(type="bool", default=False),
                    ),
                ),
                authentication=dict(
                    type='dict',
                    # apply_defaults=True,
                    options=dict(
                        type=dict(type="str", no_log=False, required=False),
                        username=dict(type="str", no_log=False, required=False),
                        password=dict(type="str", no_log=False, required=False),
                        ntlmHost=dict(type="str", no_log=False, required=False),
                        ntlmDomain=dict(type="str", no_log=False, required=False),
                        preemptive=dict(type="bool", default=True),
                    ),
                ),
            ),
        )

    def replication_argument_spec():
        return dict(
            type='dict',
            # apply_defaults=True,
            options=dict(
                preemptive_pull_enabled=dict(type="bool", default=False),
                asset_path_regex=dict(type="str", no_log=False, required=False),
            ),
        )

    def common_proxy_argument_spec(endpoint_path_to_use):
        if "/docker/hosted" in endpoint_path_to_use:
            storage_spec = NexusRepositoryHelper.storage_argument_spec_hosted()
        elif "/maven/hosted" in endpoint_path_to_use or "/npm/hosted" in endpoint_path_to_use or "/raw/hosted" in endpoint_path_to_use or "/helm/hosted" in endpoint_path_to_use:
        #elif "/maven/hosted" or "/raw/hosted" in endpoint_path_to_use:
            storage_spec = NexusRepositoryHelper.storage_argument_spec_common()
        else:
            storage_spec = NexusRepositoryHelper.storage_argument_spec()
            
        return dict(
            state=dict(type="str", choices=["present", "absent"], default="present"),
            name=dict(type="str", no_log=False, required=True),
            online=dict(type="bool", default=True),
            cleanup=NexusRepositoryHelper.cleanup_policy_argument_spec(),
            proxy=NexusRepositoryHelper.proxy_argument_spec(),
            negative_cache=NexusRepositoryHelper.negative_cache_argument_spec(),
            http_client=NexusRepositoryHelper.http_client_argument_spec(),
            routing_rule=dict(type="str", no_log=False, required=False),
            replication=NexusRepositoryHelper.replication_argument_spec(),
            storage=storage_spec,
        )

    def list_repositories(helper):
        endpoint = "repository-settings"
        info, content = helper.request(
            api_url=(helper.NEXUS_API_ENDPOINTS[endpoint]).format(
                url=helper.module.params["url"],
            ),
            method="GET",
        )
        if info["status"] in [200]:
            content = content["json"]
        else:
            helper.generic_failure_msg("Failed to list repositories", info)
        return content

    def list_filtered_repositories(helper, repository_filter):
        content = NexusRepositoryHelper.list_repositories(helper)
        content = list(filter(lambda item: repository_filter(item, helper), content))
        return content

    def create_repository(helper, endpoint_path, additional_data):
        changed = True
        data = {
            "name": helper.module.params["name"],
            "online": helper.module.params["online"],
            "storage": NexusHelper.camalize_param(helper, "storage"),
            "cleanup": NexusHelper.camalize_param(helper, "cleanup"),
            "proxy": NexusHelper.camalize_param(helper, "proxy"),
            "negativeCache": NexusHelper.camalize_param(helper, "negative_cache"),
            "httpClient": NexusHelper.camalize_param(helper, "http_client"),
            "routingRule": helper.module.params["routing_rule"],
        }
        data.update(additional_data)
        # helper.module.fail_json(
        #     msg="{data}".format(
        #         data=data,
        #     )
        # )
        endpoint = "repositories"
        info, content = helper.request(
            api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + endpoint_path).format(
                url=helper.module.params["url"],
            ),
            method="POST",
            data=data,
        )

        if info["status"] not in [201]:
            if info["status"] == 401:
                helper.module.fail_json(
                    msg="Authentication required."
                )
            elif info["status"] == 403:
                helper.generic_permission_failure_msg()
            else:
                helper.module.fail_json(
                    msg="Failed to create repository {repository}, http_status={http_status}, error_msg='{error_msg}, body={body}'.".format(
                        body=info["body"],
                        error_msg=info["msg"],
                        http_status=info["status"],
                        repository=helper.module.params["name"],
                    )
                )

        return content, changed

    def update_repository(helper, endpoint_path, additional_data, existing_data):
        data = {
            "name": helper.module.params["name"],
            "online": helper.module.params["online"],
            "storage": NexusHelper.camalize_param(helper, "storage"),
            "cleanup": NexusHelper.camalize_param(helper, "cleanup"),
            "proxy": NexusHelper.camalize_param(helper, "proxy"),
            "negativeCache": NexusHelper.camalize_param(helper, "negative_cache"),
            "httpClient": NexusHelper.camalize_param(helper, "http_client"),
            "routingRule": helper.module.params["routing_rule"],
        }
        data.update(additional_data)
        
        
        if "hosted" in endpoint_path:
            # Clean up unwanted fields that should not be updated or are part of Nexus's default config
            existing_data.pop("component", None)
            existing_data.pop("format", None)
            existing_data.pop("type", None)
            existing_data.pop("url", None)
            existing_data.pop("online", None)
            
        elif "/maven/proxy" in endpoint_path:
            # Clean up unwanted fields that should not be updated or are part of Nexus's default config
            existing_data.pop("format", None)
            existing_data.pop("type", None)
            existing_data["storage"].pop("writePolicy", None)
            data["httpClient"]["authentication"].pop("password", None)
            existing_data.update({"routingRule": existing_data.pop("routingRuleName", None)})
            
        else:
             # Does not exist for proxy repos but is still returned from API for proxy repos.
            existing_data["storage"].pop("writePolicy", None)
            existing_data.update({"routingRule": existing_data.pop("routingRuleName", None)})

        if helper.is_json_data_equal(data, existing_data):
            return existing_data, False

        endpoint = "repositories"
        info, content = helper.request(
            api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "{path}/{repository}").format(
                url=helper.module.params["url"],
                path=endpoint_path,
                repository=helper.module.params["name"],
            ),
            method="PUT",
            data=data,
        )

        if info["status"] not in [204]:
            if info["status"] == 401:
                helper.module.fail_json(
                    msg="Authentication required."
                )
            elif info["status"] == 403:
                helper.generic_permission_failure_msg()
            else:
                helper.module.fail_json(
                    msg="Failed to update repository {repository}, http_status={http_status}, error_msg='{error_msg}, body={body}'.".format(
                        body=info["body"],
                        error_msg=info["msg"],
                        http_status=info["status"],
                        repository=helper.module.params["name"],
                    )
                )

        return content, True

    def delete_repository(helper):
        changed = True
        endpoint = "repositories"
        info, content = helper.request(
            api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
                url=helper.module.params["url"],
                name=helper.module.params["name"],
            ),
            method="DELETE",
        )

        if info["status"] not in [204]:
            if info["status"] in [404]:
                content.pop("fetch_url_retries", None)
                changed = False
            elif info["status"] == 401:
                helper.module.fail_json(
                    msg="Authentication required."
                )
            elif info["status"] == 403:
                helper.module.fail_json(
                    msg="The user does not have permission to perform the operation."
                )
            else:
                helper.module.fail_json(
                    msg="Failed to delete {repository}., http_status={http_status}, error_msg='{error_msg}'.".format(
                        error_msg=info["msg"],
                        http_status=info["status"],
                        repository=helper.module.params["name"],
                    )
                )

        return content, changed
    
class NexusBlobstoreHelper:

    def common_argument_spec():
        return dict(
            state=dict(type="str", choices=["present", "absent"], default="present"),
            name=dict(type="str", no_log=False, required=True),
            soft_quota=NexusBlobstoreHelper.soft_quota_argument_spec(),
        )

    def soft_quota_argument_spec():
        return dict(
            type='dict',
            apply_defaults=False,
            options=dict(
                type=dict(type="str", choices=["spaceRemainingQuota", "spaceUsedQuota "], default="spaceRemainingQuota"),
                limit=dict(type="int", default=0),
            ),
        )

    def get_blobstore(helper, blobstore_type):
        endpoint = "blobstores"
        info, content = helper.request(
            api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/" + blobstore_type + "/{name}").format(
                url=helper.module.params["url"],
                name=helper.module.params["name"],
            ),
            method="GET",
        )
        if info["status"] in [200]:
            content = [content]
        elif info["status"] in [404]:
            content = []
        elif info["status"] == 403:
            helper.module.fail_json(
                msg="Insufficient permissions to read configuration for blob store '{name}' of type '{type}'.".format(
                    name=helper.module.params["name"],
                    type=blobstore_type,
                )
            )
        else:
            helper.module.fail_json(
                msg="Failed to read configration for blob store '{name}' of type '{type}', http_status={status}, error_msg='{error_msg}.".format(
                    name=helper.module.params["name"],
                    type=blobstore_type,
                    status=info["status"],
                    error_msg=info["msg"],
                )
            )
        return content

    def delete_blobstore(helper):
        changed = True
        endpoint = "blobstores"
        info, content = helper.request(
            api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
                url=helper.module.params["url"],
                name=helper.module.params["name"],
            ),
            method="DELETE",
        )
        if info["status"] not in [204]:
            if info["status"] in [404]:
                changed = False
            elif info["status"] == 403:
                helper.module.fail_json(
                    msg="Insufficient permissions to delete blob store '{name}'.".format(
                        name=helper.module.params["name"],
                    )
                )
            else:
                helper.module.fail_json(
                    msg="Failed to delete blob store '{name}', http_status={status}, error_msg='{error_msg}.".format(
                        name=helper.module.params["name"],
                        status=info["status"],
                        error_msg=info["msg"],
                    )
                )

        return content, changed