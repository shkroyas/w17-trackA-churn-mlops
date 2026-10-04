# Temporary Azure demonstration — Task A

This wrapper preserves the independently implemented assignment. The companion is [Task B](https://github.com/shkroyas/Ai_Assistant_MLops). Both have separate images, APIs, MLflow stores and HTTPS addresses, sharing only a temporary Azure Container Apps environment to limit cost.

## Components and routes

| Route | Service | Access |
|---|---|---|
| `/` | Demo landing page | HTTP Basic authentication |
| `/service/docs` | Actual FastAPI Swagger interface | Authentication |
| `/service/` | Actual application API | Authentication |
| `/tracking/` | Native MLflow UI | Authentication |
| `/reports/` | Existing measured evidence | Authentication |
| `/healthz` | API readiness | Public, no credentials or configuration |

`deploy/azure/entrypoint.py` supervises the services and terminates the container if a child exits. Secrets are passed through Azure secret references and read from the ignored `.env`, never embedded in the image. Nginx generates its password hash from stdin. Only the gateway listens on the container network. Azure terminates TLS and rejects insecure ingress.

Task A runs the real training/monitoring pipeline at startup and creates its own fresh registry versions. Task B retains the approved production configuration, and calls Qwen3-14B-AWQ through the authenticated Jupyter server proxy. Its hosted MLflow store starts independently; original evaluation runs remain preserved as submission evidence. Runtime stores are ephemeral and deleted with the demo. Original MLflow UUIDs and registry versions are not expected to match a fresh deployment. Airflow demonstration footage comes from the actual local execution records; this small cloud deployment does not host Airflow.

## Build and launch

Build each project's existing Dockerfile, then its wrapper:

```bash
docker build -t churn-mlops:local .
docker build -f deploy/azure/Dockerfile -t w17-task-a-azure:demo .
```

Build both images first. Run the orchestrator from Task B, using its locked Python environment, authenticated Azure CLI, and a private directory outside both repositories:

```bash
uv run python deploy/azure/deploy_demo.py \
  --subscription YOUR_SUBSCRIPTION_ID \
  --location centralindia \
  --private-dir /absolute/private/demo-directory \
  --env-file .env --hours 4 --budget 5
```

Azure CLI must have the Container Apps extension supporting `--environment-mode WorkloadProfiles`. The orchestrator uses the stable ARM API for job creation, start and execution inspection and explicitly selects the Consumption profile. Subscription policy may restrict regions, and student quotas can restrict the entire subscription to one environment. No existing application resources are altered. Each run creates a randomly named resource group and a cleanup identity whose Contributor permission is scoped only to that group. Failed runs attempt to delete their own group. Verify cleanup rather than repeatedly provisioning environments while deletion is pending.

## Budget and automatic deletion

The authorized ceiling is US$5 and four hours, measured from deployment start. Task A receives 1 vCPU/2 GiB and Task B 2 vCPU/4 GiB, each limited to one replica. No dedicated workload profile, GPU VM or Log Analytics workspace is created. An independent scheduled Container Apps job uses managed identity to delete the entire demo resource group, including its registry and identity. The deployment manually executes its permission preflight before creating either application. The UTC cron minute and expiration epoch agree exactly; the deadline is rounded down, never beyond four hours.

The conservative estimate is US$2.52, including four hours of fully active CPU/memory, one Basic registry day, an environment meter reserve and a US$0.50 margin. No free allowances are assumed. This is an estimate, not an enforceable Azure billing cap or an invoice. Rates were checked against the [official Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices); refresh them before another deployment. Failed setup attempts and deletion delays can also consume resources.

The private directory contains `deployment.json`, `demo-access.json`, CLI error details and deployment YAML containing secrets. Keep it outside Git, restrict permissions, and never attach it to the report or video. Public handoff evidence must redact credentials. To end the demo early:

```bash
uv run python deploy/azure/deploy_demo.py \
  --subscription YOUR_SUBSCRIPTION_ID \
  --private-dir /absolute/private/demo-directory --cleanup
```

The cleanup command verifies the matching ownership tag before deleting. Confirm the resource group no longer exists. A successful creation response alone does not establish HTTPS health, model inference or automatic deletion; those require separate recorded checks.

## Verify the public deployment

After provisioning and startup readiness, run Task B's `deploy/azure/smoke_demo.py`:

```bash
uv run python deploy/azure/smoke_demo.py \
  --private-dir /absolute/private/demo-directory \
  --task-a-root /absolute/path/to/w17-trackA-churn-mlops \
  --task-b-root .
```

It requires the cleanup preflight, validates HTTPS routes and anonymous rejection, makes an actual Task A prediction, verifies invalid-input HTTP 422, and asks the hosted v34 assistant for a sourced answer before checking zero-new-token cache reuse. Passing evidence is written separately to each task's `reports/cloud_demo/azure_https_smoke.json`. It makes a real model call; original offline tests and historical evaluations are different evidence. Authenticate browser access with the private `demo-access.json` values, never credentials pasted into a public URL.

## Current deployment and proxy refresh

The 2026-10-04 Azure deployment passed its managed-identity cleanup preflight and created both separate HTTPS applications. Actual Task A prediction and HTTP 422 checks passed. Task B's public routes, sourced inference and v34 configuration passed; its final native evidence reports are copied explicitly into the image. Browser WebSocket forwarding preserves the original Host header, avoiding Streamlit's origin rejection while keeping CORS protection enabled. [Nginx header inheritance](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_set_header) requires repeating these headers in a location that sets Upgrade/Connection.

Earlier, Qwen inference redirected to `/hub/access` from both Azure and the workspace. The safe-abstention failure is retained. After the owner refreshed credentials and Task B restarted, actual sourced Qwen inference and zero-new-token cached reuse passed. If proxy access expires again, refresh the ignored `.env` values and run Task B's helper:

```bash
uv run python deploy/azure/refresh_provider.py \
  --subscription YOUR_SUBSCRIPTION_ID \
  --private-dir /absolute/private/demo-directory --env-file .env
```

It verifies model access first, checks the group's ownership tag, updates secret references through a private YAML file, and restarts Task B to load them. It never extends the cleanup deadline or recreates the environment. A changed model must match the approved v34 model before this helper applies credentials. Blocked proxy access is rejected without changing Azure. Rerun the HTTPS smoke verifier after readiness.

The complete video includes actual local Qwen execution and restored public Azure inference. The earlier outage recording is preserved separately. The scheduled deadline has not yet occurred; successful preflight is evidence of identity access, not proof that the future deletion has executed.
