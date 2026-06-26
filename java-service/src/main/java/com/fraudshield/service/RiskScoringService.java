package com.fraudshield.service;

import com.fraudshield.client.MlInferenceClient;
import com.fraudshield.model.RiskAssessment;
import com.fraudshield.model.Transaction;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * Applies the business decision layer on top of the ML fraud probability.
 *
 * <p>Thresholds are externalized so risk policy can be tuned per environment
 * without recompiling. Transactions are routed to one of three tiers:
 * <ul>
 *   <li>BLOCK   - probability at or above the block threshold</li>
 *   <li>REVIEW  - probability at or above the review threshold</li>
 *   <li>APPROVE - everything below the review threshold</li>
 * </ul>
 */
@Service
public class RiskScoringService {

    private final MlInferenceClient mlClient;
    private final double blockThreshold;
    private final double reviewThreshold;

    public RiskScoringService(
            MlInferenceClient mlClient,
            @Value("${risk.threshold.block:0.80}") double blockThreshold,
            @Value("${risk.threshold.review:0.50}") double reviewThreshold) {
        this.mlClient = mlClient;
        this.blockThreshold = blockThreshold;
        this.reviewThreshold = reviewThreshold;
    }

    public RiskAssessment assess(Transaction txn) {
        double probability = mlClient.predictFraudProbability(txn);

        String decision;
        String reason;

        if (probability >= blockThreshold) {
            decision = "BLOCK";
            reason = "Fraud probability exceeds block threshold";
        } else if (probability >= reviewThreshold) {
            decision = "REVIEW";
            reason = "Fraud probability flagged for manual review";
        } else {
            decision = "APPROVE";
            reason = "Fraud probability within acceptable range";
        }

        return new RiskAssessment(txn.transactionId(), probability, decision, reason);
    }
}
