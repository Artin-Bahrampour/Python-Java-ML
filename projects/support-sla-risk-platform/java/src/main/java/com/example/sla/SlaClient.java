package com.example.sla;
import java.net.URI;
import java.net.http.*;
import java.time.Duration;

/** Minimal Java 17 integration client for a human-reviewed triage queue. */
public final class SlaClient {
  private final String base; private final HttpClient http=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
  public SlaClient(String base){this.base=base.replaceAll("/$","");}
  public String score(Ticket t) throws Exception {
    var req=HttpRequest.newBuilder(URI.create(base+"/v1/risk")).timeout(Duration.ofSeconds(10)).header("Content-Type","application/json").POST(HttpRequest.BodyPublishers.ofString(t.json())).build();
    var response=http.send(req,HttpResponse.BodyHandlers.ofString());
    if(response.statusCode()/100!=2) throw new IllegalStateException("SLA API "+response.statusCode()+": "+response.body());
    return response.body();
  }
  public static void main(String[] args)throws Exception{
    String base=args.length==1?args[0]:"http://127.0.0.1:8000";
    System.out.println(new SlaClient(base).score(new Ticket("T-DEMO","urgent","email",120,5,"enterprise",20)));
    System.out.println("Use prioritize=true only to route a ticket for human review.");
  }
  public record Ticket(String id,String priority,String channel,int age,int messages,String tier,int queue){
    String json(){return String.format("{\"ticket_id\":\"%s\",\"priority\":\"%s\",\"channel\":\"%s\",\"age_minutes\":%d,\"messages_count\":%d,\"customer_tier\":\"%s\",\"agent_queue_depth\":%d}",e(id),e(priority),e(channel),age,messages,e(tier),queue);}
    static String e(String s){return s.replace("\\","\\\\").replace("\"","\\\"");}
  }
}
