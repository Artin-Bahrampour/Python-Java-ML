package com.artin.reconciliation.domain;

import com.artin.reconciliation.application.ReconciliationEngine;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

public final class ReconciliationEngineTest {
    public static void run() {
        var engine = new ReconciliationEngine();
        var ledger = List.of(
                tx("A-1", "10.00", "NOK"), tx("A-2", "20.00", "EUR"), tx("A-3", "30.00", "NOK"), tx("L-1", "40.00", "NOK"));
        var provider = List.of(
                tx("A-1", "10.00", "NOK"), tx("A-2", "21.00", "EUR"), tx("A-3", "30.00", "EUR"), tx("P-1", "5.00", "NOK"));
        var s = engine.reconcile(ledger, provider);
        check(s.count(MatchStatus.MATCHED) == 1, "matched");
        check(s.count(MatchStatus.AMOUNT_MISMATCH) == 1, "amount mismatch");
        check(s.count(MatchStatus.PROVIDER_ONLY) == 1, "provider only");
        check(s.count(MatchStatus.CURRENCY_MISMATCH) == 1, "currency mismatch");
        check(s.count(MatchStatus.LEDGER_ONLY) == 1, "ledger only");
        check(s.records().get(1).difference().compareTo(new BigDecimal("1.00")) == 0, "difference");

        var duplicate = List.of(tx("A-1", "10.00", "NOK"), tx("A-1", "10.00", "NOK"));
        var d = engine.reconcile(ledger, duplicate);
        check(d.count(MatchStatus.DUPLICATE_PROVIDER) == 1, "duplicate provider");
    }

    private static Transaction tx(String id, String amount, String currency) { return new Transaction(id, new BigDecimal(amount), currency, Instant.parse("2026-09-29T10:00:00Z")); }
    private static void check(boolean ok, String name) { if (!ok) throw new AssertionError(name); }
}
