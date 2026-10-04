# Week 17 submission report — Task A: Telco Churn MLOps

Author: Royas Shakya. Handoff audit: 2026-10-04. This is a standalone CPU project built from the assignment PDFs. The implementation plan guided requirements and workflow; its scaffold code and illustrative results were not reused. This report describes measured implementation, including development failures, rather than copying expected plan numbers.

[Task A README](../README.md) · [Task B README](https://github.com/shkroyas/Ai_Assistant_MLops#readme) · [Task B detailed report](https://github.com/shkroyas/Ai_Assistant_MLops/blob/main/docs/week17-submission-report.md) · [Task A final release](https://github.com/shkroyas/w17-trackA-churn-mlops/releases/tag/w17-trackA-final)

A [complete file inventory](deliverable-manifest.tsv) lists every committed deliverable with byte size and SHA-256. The inventory excludes itself to avoid a recursive checksum.

## Submission and file map

Submit **https://github.com/shkroyas/w17-trackA-churn-mlops** as Task A. The implementation release is `w17-trackA-final`; subsequent documentation commits do not move that tag. All locations below are relative to this repository. Committed reports can be assessed without launching services. Download HTML reports and open locally; GitHub's source viewer does not execute them.

| Deliverable | Location | What it establishes |
|---|---|---|
| Assessed README sections a–d | [README](../README.md) | Project-specific reproducibility, selection, monitoring, orchestration |
| Locked application environment | [pyproject.toml](../pyproject.toml), [uv.lock](../uv.lock), `.python-version` | Python 3.12 dependencies and locked setup |
| Dataset integrity and experiment rules | [data.sha256](../configs/data.sha256), [params.yaml](../configs/params.yaml) | Immutable download bytes, splits, five model settings and quality floors |
| Data preparation | [data.py](../src/churn_mlops/data.py), [download script](../scripts/download_data.py) | Checksum validation, target encoding and train/holdout splits |
| Training and tracking | [train.py](../src/churn_mlops/train.py) | Five actual model runs; metrics, serialized model, confusion matrix, ROC curve logged per run |
| Complete initial comparison | [model_comparison.md](../reports/model_comparison.md), [training_runs.json](../reports/training_runs.json) | Every original model, metric and MLflow run ID |
| Plots | `reports/*_confusion_matrix.png`, `reports/*_roc_curve.png` | Five confusion matrices and five ROC curves |
| Registry transitions and rollback | [registry.py](../src/churn_mlops/registry.py), [registry.json](../reports/registry.json) | Initial winning run and None → Staging → Production transition; aliases and rollback implementation |
| Registry-backed API | [serve.py](../src/churn_mlops/serve.py), [api_demo.json](../reports/api_demo.json) | Prediction against the registered production model and invalid-input rejection |
| Feature monitoring | [control HTML](../reports/control_data_drift.html), [drifted HTML](../reports/drifted_data_drift.html) | Native Evidently feature drift reports with JSON counterparts |
| Target monitoring | [control HTML](../reports/control_target_drift.html), [drifted HTML](../reports/drifted_target_drift.html) | Native categorical Churn drift, with JSON counterparts |
| Custom metric | [custom_metrics.py](../src/churn_mlops/custom_metrics.py), [control HTML](../reports/control_custom_drift.html), [drifted HTML](../reports/drifted_custom_drift.html) | Native mean-charge metric and threshold test, with JSON counterparts |
| Drift decision | [drift.py](../src/churn_mlops/drift.py), [drift_verdict.json](../reports/drift_verdict.json) | Control versus injected distributions and retraining signal |
| Challenger decisions | [initial_challenge_result.json](../reports/initial_challenge_result.json), [challenge_result.json](../reports/challenge_result.json) | First successful promotion and later no-improvement rejection |
| Airflow bonus | [churn_monitoring.py](../dags/churn_monitoring.py), [airflow_run.txt](../reports/airflow_run.txt) | Actual positive drift branch and gated challenger execution |
| Containers and independent reproduction | [compose.yaml](../compose.yaml), [Dockerfile](../Dockerfile), [Dockerfile.airflow](../Dockerfile.airflow), [container comparison](../reports/container_validation/model_comparison.md), [container status](../reports/container_validation/status.json), [deployment_smoke.json](../reports/deployment_smoke.json) | Separate container MLflow run, actual API prediction and HTTP 422 |
| Verification | [deliverables.md](../reports/deliverables.md), [engineering_validation.md](../reports/engineering_validation.md), [tests](../tests/test_pipeline.py), [CI](../.github/workflows/ci.yml) | Recorded 20/20 core checks and four tests; CI reproduces the pipeline |
| Cloud handoff | [deploy/cloud.md](../deploy/cloud.md) | Future CPU deployment steps; no cloud execution claimed |

## What was implemented

The workflow is data → training → MLflow comparison → registry → serving → monitoring → conditional challenger evaluation. The IBM Telco dataset has 7,043 customers and approximately 26.5% churn. Eleven blank `TotalCharges` entries are treated as missing. The sklearn pipeline fits imputation, categorical encoding and numeric scaling on training rows only. A stratified 80/20 predictive split uses seed 42. Monitoring uses a separate stratified 70/30 reference/current split.

The training script fits two logistic regressions and three random forests. Each real MLflow run includes five classification metrics and the required artifacts. Registry selection uses a declared F1 floor, highest F1, then ROC-AUC to break ties. The API loads the registry production alias and holds one immutable model version for its process lifetime. Restart it after promotion. Input validation produces HTTP 422 rather than silently accepting a malformed customer.

## a. Environment and reproducibility

Python 3.12, uv, pandas 2.2.3, scikit-learn 1.6.1, matplotlib 3.10.1, FastAPI 0.115.12, MLflow 2.22.2, SQLAlchemy 2.0.41 and Evidently 0.7.23 are pinned in the application project. pytest and Ruff are development dependencies. `uv.lock` fixes transitive resolution. The first MLflow setup encountered an internal pool-class incompatibility with SQLAlchemy 2.1; the explicit 2.0.41 pin fixes the observed failure. Native Evidently custom calculations use the pinned API. Airflow gets an independent project environment inside its image to avoid replacing scheduler dependencies.

From a new clone, execute:

```bash
uv sync --locked
uv run python scripts/run_pipeline.py
uv run pytest -q
uv run python scripts/check_deliverables.py
uv run uvicorn churn_mlops.serve:app --host 127.0.0.1 --port 8001
```

Dependency setup is one command; data download, training and reporting are the next command. Network access is needed for dependency and dataset downloads. This path was exercised locally and in the independent Docker pipeline; required CI runs the locked setup, full pipeline, tests and runtime scorecard. The original local and container run IDs are separate and explicitly retained.

Raw data, MLflow databases, artifact stores and serialized model files are ignored runtime state, rather than committed binaries. A clean clone regenerates them. Submitted run UUIDs describe the original evidence; a new pipeline run receives new UUIDs. Copying the repository alone does not copy a live registry. The exported table and six HTML reports remain assessable offline.

## b. Experiments, result and model-selection decisions

| Configuration | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic, C=0.1 | 0.7999 | 0.6456 | 0.5455 | 0.5913 | 0.8409 |
| Logistic, C=1.0 | 0.8055 | 0.6572 | 0.5588 | **0.6040** | **0.8419** |
| Forest, depth 8, 300 trees | 0.8055 | 0.6761 | 0.5134 | 0.5836 | 0.8417 |
| Forest, depth 16, 300 trees | 0.7793 | 0.6061 | 0.4813 | 0.5365 | 0.8268 |
| Forest, unlimited depth, 500 trees | 0.7771 | 0.6020 | 0.4733 | 0.5299 | 0.8189 |

**Initial registered winner:** `lr_c1`, run `8d101cc2c9714284a872d869e660a00f`, registry `churn-classifier` version 1. The shallow forest ties accuracy but misses more churners: recall 0.5134 versus 0.5588 and F1 0.5836 versus 0.6040. This is why accuracy alone did not select the model. The winner clears the F1 ≥0.55 floor. Deeper forests were worse on this holdout; extra trees did not imply better generalization.

The later retraining demonstration is a separate comparison. Independently shifted training rows use seed 43, and the reserved shifted holdout uses seed 44. Champion F1 fell to 0.4109 under this shift; challenger F1 was 0.6322. ROC-AUC rose from 0.7915 to 0.7988. The declared gate requires F1 improvement ≥0.005 and ROC-AUC loss ≤0.01, so the first challenger was promoted. The later Airflow repeat obtained no improvement over the now-promoted champion and correctly retained production.

A development NumPy boolean serialization error happened after a promotion. Serialization was fixed, initial version 1 restored, and the comparison rerun. Registry version numbers include that attempt; they should not be interpreted as increasing model quality. The independent Docker smoke test served container registry version 4. Its identities are stored under `reports/container_validation/`, rather than substituted for original run IDs. The supplied plan's example forest winner and expected drift counts do not match this independently implemented project; the measured results above are authoritative.

## c. Monitoring, interpretation and response

Two batches make false-alarm behavior visible: a clean control and a deliberately shifted current batch. Month-to-month customers receive 5× sampling weight, `MonthlyCharges` gets normal offsets with mean 35 and SD 6 USD, and 5% of monitoring target labels are flipped.

Control flagged zero columns. The injected batch flagged `MonthlyCharges` and `Contract`, plus correlated `tenure`, `DeviceProtection`, `TechSupport`, `StreamingTV` and `TotalCharges`. Mean charges moved by **34.4311 USD**, compared with **0.6279 USD** for control. Churn rate moved from **0.2653 to 0.3928**, an absolute shift of **0.1275**.

Native Evidently uses numeric Wasserstein threshold 0.15 and categorical Jensen–Shannon threshold 0.10. Churn is explicitly categorical. The custom `MeanChargeShift` calculation has a <15 USD test; an additional absolute churn-rate threshold of 0.05 participates in the significant-drift decision. Six HTML reports, six JSON snapshots and verdicts are stored in the repository and logged to MLflow.

Drift triggers investigation and challenger evaluation. It does not authorize immediate replacement. Production action should first verify data integrity and newly available labels, then compare the challenger on a reserved holdout and apply the declared gate. Synthetic drift and flipped labels demonstrate the mechanism; they do not establish performance on future real customers.

## d. Airflow bonus and operational evidence

`churn_daily_monitoring` runs `@daily`, without catchup, with one active run. `check_drift` branches to `evaluate_challenger` or `no_retrain`, then joins at `done`. The demo injects drift, so its positive path is reproducible. The actual `airflow dags test` execution completed check → challenger → done; `no_retrain` was skipped. A no-improvement challenger was rejected. This proves native DAG execution, rather than a historical daily scheduling campaign.

Compose provides MLflow on localhost:5001, API on localhost:8001 by default, and optional Airflow on localhost:8081. The recorded container API test used port 18001. At the 2026-10-04 handoff audit, Task A containers were stopped; those URLs are configuration and historical evidence, not a claim of present uptime. Start them using the README before assessing live service behavior.

## Repository management, limitations and cloud handoff

The repository is separate from Task B, with its own dependencies, tests, CI, issues and milestone. GitHub uses squash-only PR merges, automatic feature-branch deletion and protected `main`: required `ci`, linear history, no force pushes, no main deletion. Zero mandatory approving reviews supports solo work while preserving PR/CI checks. The completed milestone and final release remain available. No unresolved Task A issues or remote feature branches were present at audit. This documentation follows the same PR workflow.

Core evidence is complete: **20/20 checks, four tests, five training runs, six reports, registry/API and Airflow execution**. The assignment permits exported run tables in place of UI screenshots; Task A supplies the complete table and plots. At the original core audit no public deployment was claimed; the later verified Azure demo is documented below. Development Airflow and MLflow should remain private; cloud deployment needs a target, resource budget, persistent storage, HTTPS/access control and a fresh smoke test. Preserve the original reports before rerunning a pipeline, because generated report paths can be overwritten by a new execution.


## Post-submission temporary Azure demo preparation

The owner requested a short cloud demonstration, authorized US$5 and four hours, and supplied an Azure for Students subscription. Azure device authentication succeeded. Qwen access remains HTTPS through the authenticated Jupyter server proxy; SSH tunneling is unnecessary. This follow-up does not change the assignment’s original measured results, gates or immutable release tag.

The [Azure deployment guide](azure-demo.md) explains the added wrapper image, authenticated Nginx routes, actual FastAPI/MLflow services, independent runtime stores and scoped scheduled resource-group cleanup. Task A runs its actual pipeline at startup. Task B's wrapper copies the approved v34 configuration and prompts over the older base image, which otherwise selected v1. Local checks establish gateway operation; they do not establish a public Azure deployment. The real provider preflight confirms Qwen3-14B-AWQ supports completions and native tools through the refreshed proxy authentication. The corrected v34 local gateway also completed a sourced query and zero-new-token cached reuse.

Azure setup encountered region policy restrictions, Express-environment incompatibility with scheduled jobs, a transient job creation failure, environment quota errors during pending deletion, and a failed cleanup execution precondition. The launcher now explicitly requests WorkloadProfiles with Consumption only, uses stable ARM job APIs, waits for explicit provisioning success, handles asynchronous execution responses, and rounds the UTC expiration down to match the scheduled cron minute. Application launch remains gated on a successful managed-identity cleanup preflight. Failed attempts request deletion of only their isolated resource groups. Pending deletion can continue holding the subscription's single-environment quota; do not infer cleanup completion from an accepted request.

Task A's existing four tests and Task B's existing 78 tests passed again. Two additional Task B deployment tests cover cleanup failure gating, ownership checks and exact deadline alignment. Deployment Python is included in CI. The later Azure deployment passed the cleanup preflight and both applications were created. Actual Task A public prediction/invalid-input checks passed. Task B initially encountered blocked Jupyter proxy access; its real safe-abstention response is preserved separately. Browser loading exposed a WebSocket origin issue, fixed by explicitly forwarding Host in the Nginx upgrade location. The final report files are copied into the Task B wrapper to prevent older base-image evidence from replacing the current submission. The owner subsequently refreshed proxy credentials. Task B restarted with those values and passed actual public sourced Qwen inference and zero-new-token cache reuse; the original outage evidence remains retained. The complete 9-minute-32-second narration includes actual local services and successful Azure browser footage, delivered separately in the workspace video folder with captions, transcript, chapter index and checksum; combined footage remains private because it includes Task A's private project.

The final cloud evidence is in `reports/cloud_demo/azure_deployment.json` and `azure_https_smoke.json`. Both applications passed authenticated HTTPS checks, with anonymous access rejected. Task B also passed an actual Streamlit browser query after the Host forwarding fix. The fixed resource-group deletion deadline is **2026-10-04 11:15 UTC / 17:00 Nepal**. The conservative four-hour estimate is **US$2.52**; it is not an invoice or enforceable spending cap. Scheduled deletion has not yet executed at this report time. Original final tags and submission archives remain unchanged.
