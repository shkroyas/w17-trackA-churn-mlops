# Optional Task A cloud deployment handoff

No cloud deployment or billable resource is claimed. Task A is a CPU-only churn service; Task B is hosted independently in its [own repository](https://github.com/shkroyas/Ai_Assistant_MLops).

Choose a Docker-capable VM with adequate CPU, RAM and persistent disk for the pinned pipeline and MLflow artifacts. Copy the tracked source, configure private environment values on the host, and run the README commands in order: start MLflow, run the pipeline profile to populate the registry, then start the API. Start the optional Airflow profile after validating the pipeline. A repository clone does not contain a live registry or original model binaries.

Place authenticated HTTPS in front of the API. Keep MLflow and Airflow private via SSH forwarding or a protected internal network. Persist their volumes, back up metadata and artifacts, and restart the API after registry promotion. Validate `/health`, a real `/predict` call and malformed-input HTTP 422 before documenting availability. Record provider, region, deployment URL, timestamp, registry version and actual smoke results in `reports/cloud_deployment.md`.

The target account, region, hostname and resource budget must be specified before creating resources. These steps are a future deployment handoff, not evidence of cloud execution.
