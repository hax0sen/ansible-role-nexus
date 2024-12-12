import groovy.json.JsonSlurper
import org.sonatype.nexus.capability.CapabilityReference
import org.sonatype.nexus.capability.CapabilityType
import org.sonatype.nexus.internal.capability.DefaultCapabilityReference
import org.sonatype.nexus.internal.capability.DefaultCapabilityRegistry

// Parse input arguments
def parsed_args = new JsonSlurper().parseText(args)

// Hardcoded values for the Audit capability
def CAPABILITY_TYPE_ID = parsed_args.get('capability_name')
def CAPABILITY_NOTES = "Audit capability configured through script and Ansible"
def CAPABILITY_PROPERTIES = [:] // Hardcoded to be empty

// Resolve dynamic or default parameters
def CAPABILITY_ENABLED = Boolean.valueOf(parsed_args.get('capability_enabled', true))

def capabilityRegistry = container.lookup(DefaultCapabilityRegistry.class.getName())
def capabilityType = CapabilityType.capabilityType(CAPABILITY_TYPE_ID)

// Check if the capability already exists
DefaultCapabilityReference existing = capabilityRegistry.all.find { CapabilityReference capabilityReference ->
    capabilityReference.context().descriptor().type() == capabilityType
}

if (existing) {
    log.info("{} capability updated with ID: {}", CAPABILITY_TYPE_ID,
            capabilityRegistry.update(existing.id(), CAPABILITY_ENABLED, existing.notes(), CAPABILITY_PROPERTIES).toString()
    )
} else {
    log.info("{} capability created with ID: {}", CAPABILITY_TYPE_ID,
            capabilityRegistry.add(capabilityType, CAPABILITY_ENABLED, CAPABILITY_NOTES, CAPABILITY_PROPERTIES).toString()
    )
}
