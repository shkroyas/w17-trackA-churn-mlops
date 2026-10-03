# Optional cloud deployment — pending account and target

No billable resources have been created. Choose an AWS EC2 / Azure VM / GCP Compute VM with Docker, at least 8 GB RAM and enough disk for images. The assistant API/UI does not require a GPU; the separate vLLM model host does. Copy this repository without .env/database/cache, create a local .env on the VM through your cloud secret manager, and execute the README Compose commands. For churn run the container pipeline before starting its API.

For a publicly accessible assistant, put an authenticated HTTPS reverse proxy in front of the localhost-bound UI/API. Keep MLflow and Airflow accessible through SSH port forwarding; do not expose their development UIs directly to the internet. Persist Compose volumes and back up MLflow metadata/artifacts. Verify health endpoints, a successful real query, failure fallback, and a concurrent-request benchmark before documenting a deployed endpoint. Record the provider, region, URL, timestamp, and measured evidence in reports/cloud_deployment.md. Cloud account, region, hostname, billing approval/resource limits, and model access must be supplied before a deployment can be executed.

This procedure is a deployment handoff, not evidence that the cloud bonus has been completed.
