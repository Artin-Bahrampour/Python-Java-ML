package com.example.fraud;
import java.net.*;import java.net.http.*;
public class FraudClient{public static void main(String[]x)throws Exception{String j="{\"amount\":900,\"hour\":2,\"merchant_risk\":.9,\"velocity_1h\":4,\"international\":1,\"card_age_days\":8}";var r=HttpRequest.newBuilder(URI.create("http://localhost:8000/v1/score")).header("Content-Type","application/json").POST(HttpRequest.BodyPublishers.ofString(j)).build();System.out.println(HttpClient.newHttpClient().send(r,HttpResponse.BodyHandlers.ofString()).body());}}
