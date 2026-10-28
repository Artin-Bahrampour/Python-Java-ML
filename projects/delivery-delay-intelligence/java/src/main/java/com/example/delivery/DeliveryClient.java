package com.example.delivery;
import java.net.URI;import java.net.http.*;import java.time.Duration;
/** Java 17 OMS integration client. Route requires_attention=true to human operations review. */
public final class DeliveryClient{
 private final String base;private final HttpClient http=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
 public DeliveryClient(String b){base=b.replaceAll("/$","");}
 public String predict(Shipment s)throws Exception{var r=HttpRequest.newBuilder(URI.create(base+"/v1/predict")).timeout(Duration.ofSeconds(10)).header("Content-Type","application/json").POST(HttpRequest.BodyPublishers.ofString(s.json())).build();var o=http.send(r,HttpResponse.BodyHandlers.ofString());if(o.statusCode()/100!=2)throw new IllegalStateException("API "+o.statusCode()+": "+o.body());return o.body();}
 public static void main(String[]a)throws Exception{System.out.println(new DeliveryClient(a.length>0?a[0]:"http://127.0.0.1:8000").predict(new Shipment("S-DEMO","road",350,4,.2,3,15)));}
 public record Shipment(String id,String carrier,double route,double kg,double weather,int weekday,double backlog){String json(){return String.format("{\"shipment_id\":\"%s\",\"carrier\":\"%s\",\"route_km\":%.1f,\"package_kg\":%.1f,\"weather_risk\":%.3f,\"weekday\":%d,\"hub_backlog\":%.1f}",id,carrier,route,kg,weather,weekday,backlog);}}
}
