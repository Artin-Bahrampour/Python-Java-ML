package com.example.maintenance;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/** Java 17 client for the maintenance-risk API. */
public final class MaintenanceClient {
    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
    private final String baseUrl;

    public MaintenanceClient(String baseUrl) { this.baseUrl = baseUrl.replaceAll("/$", ""); }

    public String assess(Telemetry telemetry) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create(baseUrl + "/v1/risk"))
                .timeout(Duration.ofSeconds(10)).header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(telemetry.toJson())).build();
        HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() / 100 != 2) throw new IllegalStateException("Risk API returned " + response.statusCode() + ": " + response.body());
        return response.body();
    }

    public static void main(String[] args) throws Exception {
        String api = args.length == 1 ? args[0] : "http://127.0.0.1:8000";
        Telemetry sample = new Telemetry("PUMP-208", "centrifugal_pump", 5420.0, 5.7, 79.3, 8.4, 7, 92);
        String response = new MaintenanceClient(api).assess(sample);
        System.out.println("Risk response: " + response);
        System.out.println("Only route schedule_inspection=true to a qualified maintenance planner; never use this output as a safety interlock.");
    }

    public record Telemetry(String assetId, String assetType, double operatingHours, double meanVibrationMmS,
                            double temperatureC, double pressureBar, int starts24h, int lubricantAgeDays) {
        String toJson() {
            return String.format("{\"asset_id\":\"%s\",\"asset_type\":\"%s\",\"operating_hours\":%.1f,\"mean_vibration_mm_s\":%.3f,\"temperature_c\":%.2f,\"pressure_bar\":%.2f,\"starts_24h\":%d,\"lubricant_age_days\":%d}", escape(assetId), escape(assetType), operatingHours, meanVibrationMmS, temperatureC, pressureBar, starts24h, lubricantAgeDays);
        }
        private static String escape(String value) { return value.replace("\\", "\\\\").replace("\"", "\\\""); }
    }
}
