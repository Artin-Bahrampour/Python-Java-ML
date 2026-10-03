package com.artin.reconciliation;

import com.artin.reconciliation.api.OperationalServer;
import com.artin.reconciliation.application.ReconciliationApplication;
import com.artin.reconciliation.application.ReconciliationEngine;
import com.artin.reconciliation.infrastructure.CsvTransactionReader;
import com.artin.reconciliation.infrastructure.ReconciliationReportWriter;
import com.artin.reconciliation.observability.Metrics;
import com.artin.reconciliation.observability.StructuredLogger;

import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.CountDownLatch;

public final class Main {
    public static void main(String[] args) throws Exception {
        if (args.length == 0) { usage(); System.exit(2); }
        var app = new ReconciliationApplication(new CsvTransactionReader(), new ReconciliationEngine(),
                new ReconciliationReportWriter(), new Metrics(), new StructuredLogger());
        switch (args[0]) {
            case "reconcile" -> reconcile(app, Arrays.copyOfRange(args, 1, args.length));
            case "serve" -> serve(app, Arrays.copyOfRange(args, 1, args.length));
            default -> { usage(); System.exit(2); }
        }
    }

    private static void reconcile(ReconciliationApplication app, String[] args) throws Exception {
        Map<String, String> p = parse(args);
        Path ledger = required(p, "ledger"), provider = required(p, "provider"), output = required(p, "output");
        Path audit = p.containsKey("audit") ? Path.of(p.get("audit")) : output.resolveSibling("audit.jsonl");
        var s = app.reconcile(ledger, provider, output, audit);
        System.out.printf("run_id=%s matched=%d amount_mismatch=%d currency_mismatch=%d duplicate_provider=%d provider_only=%d ledger_only=%d%n",
                s.runId(), s.count(com.artin.reconciliation.domain.MatchStatus.MATCHED), s.count(com.artin.reconciliation.domain.MatchStatus.AMOUNT_MISMATCH),
                s.count(com.artin.reconciliation.domain.MatchStatus.CURRENCY_MISMATCH), s.count(com.artin.reconciliation.domain.MatchStatus.DUPLICATE_PROVIDER),
                s.count(com.artin.reconciliation.domain.MatchStatus.PROVIDER_ONLY), s.count(com.artin.reconciliation.domain.MatchStatus.LEDGER_ONLY));
    }

    private static void serve(ReconciliationApplication app, String[] args) throws Exception {
        Map<String, String> p = parse(args);
        int port = Integer.parseInt(p.getOrDefault("port", "8080"));
        try (OperationalServer server = new OperationalServer(port, app)) {
            server.start();
            System.out.println("Operational API listening on http://localhost:" + port);
            new CountDownLatch(1).await();
        }
    }

    private static Map<String, String> parse(String[] args) {
        Map<String, String> p = new LinkedHashMap<>();
        for (int i = 0; i < args.length; i++) {
            if (!args[i].startsWith("--") || i + 1 >= args.length) throw new IllegalArgumentException("Expected --key value");
            p.put(args[i].substring(2), args[++i]);
        }
        return p;
    }
    private static Path required(Map<String, String> p, String key) { if (!p.containsKey(key)) throw new IllegalArgumentException("Missing --" + key); return Path.of(p.get(key)); }
    private static void usage() { System.err.println("Usage: reconcile --ledger <csv> --provider <csv> --output <csv> [--audit <jsonl>] | serve [--port <port>]"); }
}
