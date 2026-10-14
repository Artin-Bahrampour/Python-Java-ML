# Model Card: Customer Churn Risk

## Intended use
Portfolio demonstration of binary churn-risk modeling and repeatable ML evaluation.

## Out of scope
Automated cancellation, pricing, denial of service, or treating predictions as causal explanations.

## Data and models
Synthetic account tenure, spend, support, payment, usage, plan, contract, and autopay features. Logistic regression is the transparent baseline; random forest is the nonlinear candidate. Both share preprocessing pipelines.

## Evaluation
Stratified held-out test set; ROC-AUC, average precision, precision, recall, F1, Brier score, and confusion matrix. The threshold of 0.5 is illustrative.

## Risks
Synthetic-to-real shift, possible subgroup disparities, no temporal validation, and no causal uplift model. Before real use, validate on governed data, backtest temporally, assess calibration and subgroup errors, and establish monitoring and rollback.
