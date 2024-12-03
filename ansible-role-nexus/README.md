error 

"Unsupported parameters for (haxorof.sonatype_nexus.nexus_repository_docker_hosted) module: storage.latest_policy, storage.write_policy


perhaps setup storage function for hosted or handler different 
   def storage_argument_hosted():
        """
        Returns the argument specification for storage fields specific to hosted Docker repositories.
        """
        return dict(
            type='dict',
            options=dict(
                blob_store_name=dict(type="str", required=False),  # Required for create
                strict_content_type_validation=dict(type="bool", default=True),
                write_policy=dict(
                    type="str", 
                    choices=["allow", "allow_once", "deny"], 
                    default="allow_once"
                ),
                latest_policy=dict(type="bool", default=True),  # Hosted repository specific
            ),
        )

api endpoint
hosted
{
  "name": "internal",
  "online": true,
  "storage": {
    "blobStoreName": "default",
    "strictContentTypeValidation": true,
    "writePolicy": "allow_once",
    "latestPolicy": true
  },
  "cleanup": {
    "policyNames": [
      "string"
    ]
  },
  "component": {
    "proprietaryComponents": true
  },
  "docker": {
    "v1Enabled": false,
    "forceBasicAuth": true,
    "httpPort": 8082,
    "httpsPort": 8083,
    "subdomain": "docker-a"
  }
}
proxy
{
  "name": "internal",
  "online": true,
  "storage": {
    "blobStoreName": "default",
    "strictContentTypeValidation": true
  },
  "cleanup": {
    "policyNames": [
      "string"
    ]
  },
  "proxy": {
    "remoteUrl": "https://remote.repository.com",
    "contentMaxAge": 1440,
    "metadataMaxAge": 1440
  },
  "negativeCache": {
    "enabled": true,
    "timeToLive": 1440
  },
  "httpClient": {
    "blocked": false,
    "autoBlock": true,
    "connection": {
      "retries": 0,
      "userAgentSuffix": "string",
      "timeout": 60,
      "enableCircularRedirects": false,
      "enableCookies": false,
      "useTrustStore": false
    },
    "authentication": {
      "type": "username",
      "username": "string",
      "password": "string",
      "ntlmHost": "string",
      "ntlmDomain": "string"
    }
  },
  "routingRule": "string",
  "replication": {
    "preemptivePullEnabled": false,
    "assetPathRegex": "string"
  },
  "docker": {
    "v1Enabled": false,
    "forceBasicAuth": true,
    "httpPort": 8082,
    "httpsPort": 8083,
    "subdomain": "docker-a"
  },
  "dockerProxy": {
    "indexType": "HUB",
    "indexUrl": "string",
    "cacheForeignLayers": true,
    "foreignLayerUrlWhitelist": [
      "string"
    ]
  }
}