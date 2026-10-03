package com.artin.reconciliation.domain;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Objects;

public record Transaction(String transactionId, BigDecimal amount, String currency, Instant settledAt) {
    public Transaction {
        if (transactionId == null || !transactionId.matches("[A-Za-z0-9_-]{3,64}"))
            throw new IllegalArgumentException("Invalid transaction_id");
        Objects.requireNonNull(amount, "amount");
        if (amount.scale() > 2 || amount.signum() < 0)
            throw new IllegalArgumentException("Amount must be non-negative with at most 2 decimals");
        if (currency == null || !currency.matches("[A-Z]{3}"))
            throw new IllegalArgumentException("Currency must be an ISO-like 3-letter uppercase code");
        Objects.requireNonNull(settledAt, "settledAt");
    }
}
