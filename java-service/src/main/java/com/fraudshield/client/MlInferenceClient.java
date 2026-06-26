package com.fraudshield.client;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fraudshield.model.Transaction;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Thin client that calls the Python ML inference service over HTTP to obtain a
 * fraud probability for a given transaction. Feature names are mapped to the
 * snake_case contract expected by the FastAPI service.
 */
@Component
public class MlInferenceClient {

    private static final Logger log = LoggerFactory.getLogger(MlInferenceClient.class);

    private final RestClient restClient;

    public MlInferenceClient(@Value("${ml.service.url}") String mlServiceUrl) {
        this.restClient = RestClient.builder()
                .baseUrl(mlServiceUrl)
                .build();
    }

    /**
     * Sends the transaction features to the ML service and returns the fraud
     * probability. On any client error the call fails closed (returns 1.0) so
     * that scoring failures route to BLOCK rather than silently approving a
     * transaction we were unable to score.
     */
    public double predictFraudProbability(Transaction txn) {
        Map<String, Object> features = new LinkedHashMap<>();
        features.put("amount", txn.amount());
        features.put("merchant_category", txn.merchantCategory());
        features.put("hour_of_day", txn.hourOfDay());
        features.put("days_since_last_txn", txn.daysSinceLastTxn());
        features.put("num_txns_24h", txn.numTxns24h());
        features.put("is_foreign", txn.isForeign() ? 1 : 0);
        features.put("account_age_days", txn.accountAgeDays());

        try {
            PredictionResponse response = restClient.post()
                    .uri("/predict")
                    .body(features)
                    .retrieve()
                    .body(PredictionResponse.class);

            return response != null ? response.fraudProbability() : 1.0;
        } catch (RestClientException e) {
            log.error("ML inference call failed for txn {}, failing closed to REVIEW",
                    txn.transactionId(), e);
            return 1.0;
        }
    }

    private record PredictionResponse(
            @JsonProperty("fraud_probability") double fraudProbability
    ) {
    }
}
