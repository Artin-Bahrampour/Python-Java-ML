package com.example.churn;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/** Minimal Java 17 integration client; no external JSON library is required. */
public final class ChurnClient {
    private final HttpClient http;
    private final String baseUrl;

    public ChurnClient(String baseUrl) {
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
    }

    public String score(Customer customer) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create(baseUrl + "/v1/predict"))
                .timeout(Duration.ofSeconds(10))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(customer.toJson()))
                .build();
        HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() / 100 != 2) {
            throw new IllegalStateException("Scoring failed (" + response.statusCode() + "): " + response.body());
        }
        return response.body();
    }

    public static void main(String[] args) throws Exception {
        String url = args.length == 1 ? args[0] : "http://127.0.0.1:8000";
        Customer sample = new Customer("demo-001", 3, 104.50, 4, 2, "month_to_month", "invoice", false);
        String result = new ChurnClient(url).score(sample);
        System.out.println("API response: " + result);
        System.out.println("Route records marked requires_review=true to a human retention specialist.");
    }

    public record Customer(String customerId, int tenureMonths, double monthlyCharge,
                           int supportTickets90d, int loginDays30d, String contractType,
                           String paymentMethod, boolean autopayEnabled) {
        String toJson() {
            return String.format("{\"customer_id\":\"%s\",\"tenure_months\":%d,\"monthly_charge\":%.2f,\"support_tickets_90d\":%d,\"login_days_30d\":%d,\"contract_type\":\"%s\",\"payment_method\":\"%s\",\"autopay_enabled\":%s}",
                    escape(customerId), tenureMonths, monthlyCharge, supportTickets90d, loginDays30d,
                    escape(contractType), escape(paymentMethod), autopayEnabled);
        }
        private static String escape(String value) { return value.replace("\\", "\\\\").replace("\"", "\\\""); }
    }
}
