package com.example.energy;
import java.net.URI;import java.net.http.*;import java.time.Duration;
/** Java 17 client for operational energy forecasts. */
public final class EnergyClient{
 private final String base;private final HttpClient http=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
 public EnergyClient(String base){this.base=base.replaceAll("/$","");}
 public String forecast(Request x)throws Exception{var r=HttpRequest.newBuilder(URI.create(base+"/v1/forecast")).timeout(Duration.ofSeconds(10)).header("Content-Type","application/json").POST(HttpRequest.BodyPublishers.ofString(x.json())).build();var out=http.send(r,HttpResponse.BodyHandlers.ofString());if(out.statusCode()/100!=2)throw new IllegalStateException("Forecast API "+out.statusCode()+": "+out.body());return out.body();}
 public static void main(String[]a)throws Exception{String base=a.length==1?a[0]:"http://127.0.0.1:8000";System.out.println(new EnergyClient(base).forecast(new Request("B-01",9,2,4,.8,143)));}
 public record Request(String building,int hour,int day,double temp,double occupancy,double prior){String json(){return String.format("{\"building_id\":\"%s\",\"hour\":%d,\"day_of_week\":%d,\"outside_temp_c\":%.2f,\"occupancy_ratio\":%.3f,\"prior_hour_kwh\":%.2f}",building,hour,day,temp,occupancy,prior);}}
}
