package com.example.maintenance;

public final class MaintenanceClientTest {
    public static void main(String[] args) {
        var payload = new MaintenanceClient.Telemetry("P\"1", "centrifugal_pump", 1, 2, 3, 4, 5, 6).toJson();
        assert payload.contains("P\\\"1");
        assert payload.contains("\"starts_24h\":5");
        System.out.println("Maintenance client serialization tests passed.");
    }
}
