package com.artin.reconciliation.application;

import com.artin.reconciliation.domain.*;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

public final class ReconciliationEngine {
    public ReconciliationSummary reconcile(List<Transaction> ledger, List<Transaction> provider) {
        Objects.requireNonNull(ledger);
        Objects.requireNonNull(provider);
        Instant started = Instant.now();

        Map<String, Transaction> ledgerById = uniqueIndex(ledger, "ledger");
        Map<String, List<Transaction>> providerGroups = provider.stream()
                .collect(Collectors.groupingBy(Transaction::transactionId, LinkedHashMap::new, Collectors.toList()));

        List<ReconciliationRecord> result = new ArrayList<>();
        Set<String> providerIds = new HashSet<>();

        providerGroups.forEach((id, entries) -> {
            providerIds.add(id);
            if (entries.size() > 1) {
                result.add(new ReconciliationRecord(id, MatchStatus.DUPLICATE_PROVIDER,
                        ledgerById.get(id) == null ? null : ledgerById.get(id).amount(),
                        entries.get(0).amount(),
                        ledgerById.get(id) == null ? null : ledgerById.get(id).currency(),
                        entries.get(0).currency(), null));
                return;
            }
            Transaction p = entries.get(0);
            Transaction l = ledgerById.get(id);
            if (l == null) {
                result.add(new ReconciliationRecord(id, MatchStatus.PROVIDER_ONLY, null, p.amount(), null, p.currency(), null));
            } else if (!l.currency().equals(p.currency())) {
                result.add(new ReconciliationRecord(id, MatchStatus.CURRENCY_MISMATCH,
                        l.amount(), p.amount(), l.currency(), p.currency(), p.amount().subtract(l.amount())));
            } else if (l.amount().compareTo(p.amount()) != 0) {
                result.add(new ReconciliationRecord(id, MatchStatus.AMOUNT_MISMATCH,
                        l.amount(), p.amount(), l.currency(), p.currency(), p.amount().subtract(l.amount())));
            } else {
                result.add(new ReconciliationRecord(id, MatchStatus.MATCHED,
                        l.amount(), p.amount(), l.currency(), p.currency(), BigDecimal.ZERO.setScale(2)));
            }
        });

        ledgerById.forEach((id, l) -> {
            if (!providerIds.contains(id)) {
                result.add(new ReconciliationRecord(id, MatchStatus.LEDGER_ONLY, l.amount(), null, l.currency(), null, null));
            }
        });

        result.sort(Comparator.comparing(ReconciliationRecord::transactionId));
        return new ReconciliationSummary(UUID.randomUUID(), result, Duration.between(started, Instant.now()));
    }

    private static Map<String, Transaction> uniqueIndex(List<Transaction> transactions, String side) {
        Map<String, Transaction> result = new LinkedHashMap<>();
        for (Transaction t : transactions) {
            Transaction previous = result.putIfAbsent(t.transactionId(), t);
            if (previous != null) {
                throw new IllegalArgumentException("Duplicate transaction_id in " + side + ": " + t.transactionId());
            }
        }
        return result;
    }
}
