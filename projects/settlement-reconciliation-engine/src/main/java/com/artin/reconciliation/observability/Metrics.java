package com.artin.reconciliation.observability;

import com.artin.reconciliation.domain.MatchStatus;
import com.artin.reconciliation.domain.ReconciliationSummary;

import java.util.EnumMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicLong;

public final class Metrics {
    private final AtomicLong runs = new AtomicLong();
    private final AtomicLong records = new AtomicLong();
    private final Map<MatchStatus, AtomicLong> statuses = new EnumMap<>(MatchStatus.class);

    public Metrics() { for (MatchStatus s : MatchStatus.values()) statuses.put(s, new AtomicLong()); }

    public void record(ReconciliationSummary summary) {
        runs.incrementAndGet();
        records.addAndGet(summary.records().size());
        for (MatchStatus s : MatchStatus.values()) statuses.get(s).addAndGet(summary.count(s));
    }

    public String prometheus() {
        StringBuilder b = new StringBuilder();
        b.append("reconciliation_runs_total ").append(runs.get()).append('\n');
        b.append("reconciliation_records_total ").append(records.get()).append('\n');
        statuses.forEach((s, v) -> b.append("reconciliation_records_by_status_total{status=\"").append(s).append("\"} ").append(v.get()).append('\n'));
        return b.toString();
    }
}
