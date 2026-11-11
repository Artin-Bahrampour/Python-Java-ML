package com.example.claims;
import java.net.URI; import java.net.http.*;
public final class ClaimsClient {
  public static void main(String[] args) throws Exception {
    String body="{\"claim_amount\":80000,\"policy_age_days\":20,\"prior_claims\":4,\"incident_delay_days\":35,\"risk_region\":1}";
    HttpRequest request=HttpRequest.newBuilder(URI.create("http://localhost:8000/v1/triage")).header("Content-Type","application/json").POST(HttpRequest.BodyPublishers.ofString(body)).build();
    HttpResponse<String> response=HttpClient.newHttpClient().send(request,HttpResponse.BodyHandlers.ofString());
    if(response.statusCode()!=200) throw new IllegalStateException("triage failed: "+response.statusCode());
    System.out.println(response.body());
  }
}
