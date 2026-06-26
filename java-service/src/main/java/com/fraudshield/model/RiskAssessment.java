package com.fraudshield.model;

/**
 * Outbound risk decision returned to the caller.
 *
 * @param transactionId    echo of the scored transaction id
 * @param fraudProbability  model-produced fraud probability in [0, 1]
 * @param decision         business decision: BLOCK, REVIEW, or APPROVE
 * @param reason           human-readable rationale for the decision
 */
public record RiskAssessment(
        String transactionId,
        double fraudProbability,
        String decision,
        String reason
) {
}
