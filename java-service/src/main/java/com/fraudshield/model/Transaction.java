package com.fraudshield.model;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;

/**
 * Inbound transaction payload to be scored for fraud risk.
 *
 * @param transactionId     unique transaction identifier
 * @param amount            transaction amount in account currency
 * @param merchantCategory  pre-encoded merchant category code (0-9)
 * @param hourOfDay         hour the transaction occurred (0-23)
 * @param daysSinceLastTxn  days elapsed since the account's previous transaction
 * @param numTxns24h        number of transactions on the account in the last 24h
 * @param isForeign         whether the transaction is cross-border
 * @param accountAgeDays    age of the originating account in days
 */
public record Transaction(
        @NotNull String transactionId,
        @NotNull @PositiveOrZero Double amount,
        @NotNull @PositiveOrZero Integer merchantCategory,
        @NotNull Integer hourOfDay,
        @NotNull @PositiveOrZero Integer daysSinceLastTxn,
        @NotNull @PositiveOrZero Integer numTxns24h,
        @NotNull Boolean isForeign,
        @NotNull @PositiveOrZero Integer accountAgeDays
) {
}
