package com.artin.reconciliation.domain;

import java.time.Duration;
import java.util.List;
import java.util.UUID;

public record ReconciliationSummary(
        UUID runId,
        List<ReconciliationRecord> records,
        Duration duration) {
    public ReconciliationSummary {
        records = List.copyOf(records);
    }

    public long count(MatchStatus status) {
        return records.stream().filter(r -> r.status() == status).count();
    }
}
