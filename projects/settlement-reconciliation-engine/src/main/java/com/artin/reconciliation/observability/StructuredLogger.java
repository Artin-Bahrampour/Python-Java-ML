package com.artin.reconciliation.observability;

import java.time.Instant;

public final class StructuredLogger {
    public void info(String event, String message) { log("INFO", event, message); }
    public void error(String event, String message) { log("ERROR", event, message); }

    private void log(String level, String event, String message) {
        System.err.printf("{\"timestamp\":\"%s\",\"level\":\"%s\",\"event\":\"%s\",\"message\":\"%s\"}%n",
                Instant.now(), escape(level), escape(event), escape(message));
    }

    private static String escape(String s) { return s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n"); }
}
