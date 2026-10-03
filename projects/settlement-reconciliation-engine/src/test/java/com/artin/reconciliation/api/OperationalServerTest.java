package com.artin.reconciliation.api;

import com.artin.reconciliation.application.*;
import com.artin.reconciliation.infrastructure.*;
import com.artin.reconciliation.observability.*;
import java.net.URI;
import java.net.http.*;

public final class OperationalServerTest {
    public static void run() throws Exception {
        var app = new ReconciliationApplication(new CsvTransactionReader(), new ReconciliationEngine(), new ReconciliationReportWriter(), new Metrics(), new StructuredLogger());
        try (var server = new OperationalServer(0, app)) {
            server.start();
            var client = HttpClient.newHttpClient();
            var response = client.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + server.port() + "/health")).GET().build(), HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200 || !response.body().contains("OK")) throw new AssertionError("health endpoint");
            var latest = client.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + server.port() + "/latest")).GET().build(), HttpResponse.BodyHandlers.ofString());
            if (latest.statusCode() != 404) throw new AssertionError("latest before run");
        }
    }
}
