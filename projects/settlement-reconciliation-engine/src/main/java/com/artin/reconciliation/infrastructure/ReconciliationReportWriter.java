package com.artin.reconciliation.infrastructure;

import com.artin.reconciliation.domain.ReconciliationRecord;
import com.artin.reconciliation.domain.ReconciliationSummary;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.List;

public final class ReconciliationReportWriter {
    public void write(Path output, ReconciliationSummary summary) throws IOException {
        Path parent = output.toAbsolutePath().getParent();
        if (parent != null) Files.createDirectories(parent);
        Path temp = output.resolveSibling(output.getFileName() + ".tmp-" + summary.runId());
        try {
            Files.writeString(temp, toCsv(summary.records()), StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            try {
                Files.move(temp, output, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            } catch (AtomicMoveNotSupportedException e) {
                Files.move(temp, output, StandardCopyOption.REPLACE_EXISTING);
            }
        } finally {
            Files.deleteIfExists(temp);
        }
    }

    private String toCsv(List<ReconciliationRecord> records) {
        StringBuilder out = new StringBuilder("transaction_id,status,ledger_amount,provider_amount,ledger_currency,provider_currency,difference\n");
        for (ReconciliationRecord r : records) {
            out.append(csv(r.transactionId())).append(',')
                    .append(r.status()).append(',')
                    .append(value(r.ledgerAmount())).append(',')
                    .append(value(r.providerAmount())).append(',')
                    .append(value(r.ledgerCurrency())).append(',')
                    .append(value(r.providerCurrency())).append(',')
                    .append(value(r.difference())).append('\n');
        }
        return out.toString();
    }

    private static String value(Object value) { return value == null ? "" : csv(value.toString()); }
    private static String csv(String value) { return value.contains(",") || value.contains("\"") ? "\"" + value.replace("\"", "\"\"") + "\"" : value; }
}
