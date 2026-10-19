package com.example.churn;

/** Run manually with assertions enabled after compiling source and this class. */
public final class ChurnClientTest {
    public static void main(String[] args) {
        var customer = new ChurnClient.Customer("a\"b", 1, 12.5, 0, 3, "one_year", "card", true);
        assert customer.toJson().contains("a\\\"b");
        assert customer.toJson().contains("\"autopay_enabled\":true");
        System.out.println("Java client serialization tests passed.");
    }
}
