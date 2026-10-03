package com.artin.reconciliation.infrastructure;

import java.nio.file.*;

public final class CsvTransactionReaderTest {
    public static void run() throws Exception {
        Path temp = Files.createTempFile("reconciliation", ".csv");
        try {
            Files.writeString(temp, "transaction_id,amount,currency,settled_at\nA-1,12.50,NOK,2026-09-29T10:00:00Z\n");
            var rows = new CsvTransactionReader().read(temp);
            if (rows.size() != 1 || rows.get(0).amount().intValue() != 12) throw new AssertionError("CSV read");
            Files.writeString(temp, "transaction_id,amount,currency,settled_at\nA-1,-1.00,NOK,2026-09-29T10:00:00Z\n");
            try { new CsvTransactionReader().read(temp); throw new AssertionError("negative amount accepted"); }
            catch (java.io.IOException expected) { }
        } finally { Files.deleteIfExists(temp); }
    }
}
