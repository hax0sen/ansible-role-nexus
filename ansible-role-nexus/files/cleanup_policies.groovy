import com.google.common.collect.Maps
import groovy.json.JsonOutput
import groovy.json.JsonSlurper
import java.util.concurrent.TimeUnit

import org.sonatype.nexus.cleanup.storage.CleanupPolicy
import org.sonatype.nexus.cleanup.storage.CleanupPolicyStorage

CleanupPolicyStorage cleanupPolicyStorage = container.lookup(CleanupPolicyStorage.class.getName())
parsed_args = new JsonSlurper().parseText(args)

List<Map<String, String>> actionDetails = []
Map scriptResults = [changed: false, error: false, action_details: actionDetails]

parsed_args.each { currentPolicy ->
    Map<String, String> currentResult = [
        name  : currentPolicy.name,
        format: currentPolicy.format,
        mode  : currentPolicy.mode
    ]

    try {
        if (!currentPolicy.name) throw new Exception("Missing mandatory argument: name")

        Map<String, String> criteriaMap = createCriteria(currentPolicy)

        if (cleanupPolicyStorage.exists(currentPolicy.name)) {
            updatePolicyIfNeeded(cleanupPolicyStorage, currentPolicy, criteriaMap, scriptResults, currentResult)
        } else {
            createPolicy(cleanupPolicyStorage, currentPolicy, criteriaMap, scriptResults, currentResult)
        }
    } catch (Exception e) {
        handleException(e, currentPolicy, scriptResults, currentResult)
    }

    actionDetails.add(currentResult)
}

return JsonOutput.toJson(scriptResults)

def void updatePolicyIfNeeded(CleanupPolicyStorage storage, def policy, Map<String, String> criteria, Map results, Map result) {
    CleanupPolicy existingPolicy = storage.get(policy.name)
    if (isPolicyEqual(existingPolicy, policy)) {
        log.info("No change Cleanup Policy <name=${policy.name}>")
    } else {
        log.info("Update Cleanup Policy <name=${policy.name}, format=${policy.format}, criteria=${policy.criteria}>")
        existingPolicy.setNotes(policy.notes)
        existingPolicy.setCriteria(criteria)
        storage.update(existingPolicy)

        result.put('status', 'updated')
        results['changed'] = true
    }
}

def void createPolicy(CleanupPolicyStorage storage, def policy, Map<String, String> criteria, Map results, Map result) {
    log.info("Creating Cleanup Policy <name=${policy.name}, format=${policy.format}, criteria=${policy.criteria}>")

    CleanupPolicy newPolicy = storage.newCleanupPolicy()
    newPolicy.with {
        setName(policy.name)
        setNotes(policy.notes)
        setFormat(policy.format == "all" ? "ALL_FORMATS" : policy.format)
        setMode('deletion')
        setCriteria(criteria)
    }
    storage.add(newPolicy)

    result.put('status', 'created')
    results['changed'] = true
}

def void handleException(Exception e, def policy, Map results, Map result) {
    result.put('status', 'error')
    result.put('error_msg', e.toString())
    results['error'] = true
    log.error("Configuration for repo ${policy.name} could not be saved: ${e}")
}

def Map<String, String> createCriteria(def policy) {
    Map<String, String> criteriaMap = Maps.newHashMap()

    criteriaMap.put('lastBlobUpdated', policy.criteria.lastBlobUpdated ? asStringSeconds(policy.criteria.lastBlobUpdated) : null)
    criteriaMap.put('lastDownloaded', policy.criteria.lastDownloaded ? asStringSeconds(policy.criteria.lastDownloaded) : null)
    criteriaMap.put('isPrerelease', policy.criteria.isPrerelease ? Boolean.toString(policy.criteria.isPrerelease == "PRERELEASES") : null)
    criteriaMap.put('regex', policy.criteria.regexKey ?: null)

    log.info("Using criteriaMap: ${criteriaMap}")
    return criteriaMap.findAll { it.value != null }
}

def Boolean isPolicyEqual(CleanupPolicy existingPolicy, def policy) {
    Map<String, String> currentCriteria = createCriteria(policy)

    return existingPolicy.getNotes() == policy.notes &&
           existingPolicy.getFormat() == policy.format &&
           criteriaMatch(existingPolicy.getCriteria(), currentCriteria)
}

def Boolean criteriaMatch(Map<String, String> existing, Map<String, String> current) {
    return ['lastBlobUpdated', 'lastDownloaded', 'isPrerelease', 'regex'].every {
        existing[it] == current[it]
    }
}

def Integer asSeconds(int days) {
    return days * TimeUnit.DAYS.toSeconds(1)
}

def String asStringSeconds(int days) {
    return asSeconds(days).toString()
}
