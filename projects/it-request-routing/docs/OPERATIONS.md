# Operations

The output is a routing recommendation, not an authorization or access-control decision. Low-confidence requests remain in `manual_review`. Train only on privacy-reviewed, redacted ticket text; never log raw ticket bodies in production. Monitor class distribution, confidence distribution, manual-review rate, schema errors, latency, and corrected routing outcomes. Review evaluation by language and department before deploying a new model version.
