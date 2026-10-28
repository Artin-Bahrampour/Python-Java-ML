# Operations and governance

The service supports shipment prioritization only; it does not automatically cancel, reroute, or price deliveries. Use human review for `requires_attention` outputs.

Train with a time-based production split: all events for a shipment must precede its promised-window outcome. Monitor AUC/average precision on labelled outcomes plus request rate, latency, invalid inputs, mean probability, and feature drift against the artifact baseline. Roll back to the prior version if online quality materially degrades. Deploy behind TLS with service authentication; avoid logging customer addresses or raw shipment payloads.
