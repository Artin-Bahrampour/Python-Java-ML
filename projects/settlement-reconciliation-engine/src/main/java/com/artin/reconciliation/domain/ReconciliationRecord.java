package com.artin.reconciliation.domain;

import java.math.BigDecimal;

public record ReconciliationRecord(
        String transactionId,
        MatchStatus status,
        BigDecimal ledgerAmount,
        BigDecimal providerAmount,
        String ledgerCurrency,
        String providerCurrency,
        BigDecimal difference) {
}
