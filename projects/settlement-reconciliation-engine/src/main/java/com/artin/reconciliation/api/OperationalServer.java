package com.artin.reconciliation.api;

import com.artin.reconciliation.application.ReconciliationApplication;
import com.artin.reconciliation.domain.ReconciliationRecord;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.concurrent.Executors;

public final class OperationalServer implements AutoCloseable {
    private final HttpServer server;
    private final ReconciliationApplication application;

    public OperationalServer(int port, ReconciliationApplication application) throws IOException {
        if (port < 0 || port > 65535) throw new IllegalArgumentException("Invalid port: " + port);
        this.application = application;
        server = HttpServer.create(new InetSocketAddress("0.0.0.0", port), 50);
        server.createContext("/health", this::health);
        server.createContext("/metrics", this::metrics);
        server.createContext("/latest", this::latest);
        server.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
    }

    public void start() { server.start(); }
    public int port() { return server.getAddress().getPort(); }

    private void health(HttpExchange exchange) throws IOException { respond(exchange, 200, "OK\n", "text/plain"); }
    private void metrics(HttpExchange exchange) throws IOException { respond(exchange, 200, application.metrics().prometheus(), "text/plain; version=0.0.4"); }

    private void latest(HttpExchange exchange) throws IOException {
        if (application.latestSummary() == null) { respond(exchange, 404, "{\"error\":\"no reconciliation run\"}\n", "application/json"); return; }
        var s = application.latestSummary();
        StringBuilder json = new StringBuilder("{\"run_id\":\"").append(s.runId()).append("\",\"records\":[");
        for (int i = 0; i < s.records().size(); i++) {
            ReconciliationRecord r = s.records().get(i);
            if (i > 0) json.append(',');
            json.append("{\"transaction_id\":\"").append(escape(r.transactionId())).append("\",\"status\":\"").append(r.status()).append("\"}");
        }
        json.append("]}\n");
        respond(exchange, 200, json.toString(), "application/json");
    }

    private static void respond(HttpExchange exchange, int status, String body, String type) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", type + "; charset=utf-8");
        exchange.getResponseHeaders().set("Cache-Control", "no-store");
        exchange.sendResponseHeaders(status, bytes.length);
        try (var out = exchange.getResponseBody()) { out.write(bytes); }
    }
    private static String escape(String value) { return value.replace("\\", "\\\\").replace("\"", "\\\""); }

    @Override public void close() { server.stop(0); }
}
