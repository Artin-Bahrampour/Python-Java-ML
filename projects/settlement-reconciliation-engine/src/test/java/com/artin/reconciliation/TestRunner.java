package com.artin.reconciliation;

import com.artin.reconciliation.api.OperationalServerTest;
import com.artin.reconciliation.domain.ReconciliationEngineTest;
import com.artin.reconciliation.infrastructure.CsvTransactionReaderTest;

public final class TestRunner {
    public static void main(String[] args) throws Exception {
        ReconciliationEngineTest.run();
        CsvTransactionReaderTest.run();
        OperationalServerTest.run();
        System.out.println("All tests passed.");
    }
}
