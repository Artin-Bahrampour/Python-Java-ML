# Runbook

Use the service only to prioritise analyst review. Monitor API availability, scoring latency, review rate, average score and amount PSI. If PSI is at least 0.2, investigate upstream changes before retraining. Promote a replacement only when it beats the deployed artifact on a later time holdout for PR-AUC, calibration and cost.
