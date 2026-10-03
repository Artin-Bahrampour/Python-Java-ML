package com.artin.reconciliation.application;

import com.artin.reconciliation.domain.ReconciliationSummary;
import com.artin.reconciliation.domain.Transaction;
import com.artin.reconciliation.infrastructure.CsvTransactionReader;
import com.artin.reconciliation.infrastructure.ReconciliationReportWriter;
import com.artin.reconciliation.observability.Metrics;
import com.artin.reconciliation.observability.StructuredLogger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.List;

public final class ReconciliationApplication {
    private final CsvTransactionReader reader;
    private final ReconciliationEngine engine;
    private final ReconciliationReportWriter writer;
    private final Metrics metrics;
    private final StructuredLogger logger;
    private volatile Path latestReport;
    private volatile ReconciliationSummary latestSummary;

    public ReconciliationApplication(CsvTransactionReader reader, ReconciliationEngine engine,
                                     ReconciliationReportWriter writer, Metrics metrics, StructuredLogger logger) {
        this.reader = reader; this.engine = engine; this.writer = writer; this.metrics = metrics; this.logger = logger;
    }

    public synchronized ReconciliationSummary reconcile(Path ledger, Path provider, Path output, Path audit) throws IOException {
        logger.info("reconciliation_started", "ledger=" + ledger + ", provider=" + provider);
        List<Transaction> ledgerRows = reader.read(ledger);
        List<Transaction> providerRows = reader.read(provider);
        ReconciliationSummary summary = engine.reconcile(ledgerRows, providerRows);
        writer.write(output, summary);
        writeAudit(audit, summary);
        metrics.record(summary);
        latestReport = output.toAbsolutePath();
        latestSummary = summary;
        logger.info("reconciliation_completed", "run_id=" + summary.runId() + ", records=" + summary.records().size());
        return summary;
    }

    private void writeAudit(Path audit, ReconciliationSummary summary) throws IOException {
        if (audit == null) return;
        Path parent = audit.toAbsolutePath().getParent();
        if (parent != null) Files.createDirectories(parent);
        String json = String.format("{\"run_id\":\"%s\",\"duration_ms\":%d,\"matched\":%d,\"amount_mismatch\":%d,\"currency_mismatch\":%d,\"duplicate_provider\":%d,\"provider_only\":%d,\"ledger_only\":%d}%n",
                summary.runId(), summary.duration().toMillis(), summary.count(com.artin.reconciliation.domain.MatchStatus.MATCHED),
                summary.count(com.artin.reconciliation.domain.MatchStatus.AMOUNT_MISMATCH),
                summary.count(com.artin.reconciliation.domain.MatchStatus.CURRENCY_MISMATCH),
                summary.count(com.artin.reconciliation.domain.MatchStatus.DUPLICATE_PROVIDER),
                summary.count(com.artin.reconciliation.domain.MatchStatus.PROVIDER_ONLY),
                summary.count(com.artin.reconciliation.domain.MatchStatus.LEDGER_ONLY));
        Files.writeString(audit, json, StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    }

    public ReconciliationSummary latestSummary() { return latestSummary; }
    public Path latestReport() { return latestReport; }
    public Metrics metrics() { return metrics; }
}
