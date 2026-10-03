package com.artin.reconciliation.domain;

public enum MatchStatus {
    MATCHED,
    AMOUNT_MISMATCH,
    CURRENCY_MISMATCH,
    DUPLICATE_PROVIDER,
    PROVIDER_ONLY,
    LEDGER_ONLY
}
