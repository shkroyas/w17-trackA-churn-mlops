# Local verification evidence

Executed on 2026-10-03, from independent fresh source implementations.

- Churn: 4 pytest tests passed, including actual registry-backed API predictions and 422 invalid-input rejection.
- Full live MLflow scorecard: 20/20 PASS.
- Five CPU training configurations tracked with metrics, model, confusion matrix, ROC curve.
- Six native Evidently HTML/JSON reports generated and logged to MLflow.
- Actual Airflow DAG executed check_drift → evaluate_challenger → done successfully; repeat challenger did not improve champion and was rejected.
- Application and isolated Airflow Docker images built; Compose validates.
