import argparse
import json
from pathlib import Path

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="http://localhost:8001")
args = parser.parse_args()
sample = json.loads(Path("reports/api_demo.json").read_text())["request"]
health = httpx.get(args.base_url + "/health", timeout=10)
health.raise_for_status()
prediction = httpx.post(args.base_url + "/predict", json=sample, timeout=30)
prediction.raise_for_status()
assert 0 <= prediction.json()["churn_probability"] <= 1
assert prediction.json()["model_version"] == health.json()["version"]
invalid = httpx.post(args.base_url + "/predict", json={"tenure": -1}, timeout=10)
assert invalid.status_code == 422
record = {
    "health": health.json(),
    "request": sample,
    "prediction": prediction.json(),
    "invalid_request_status": invalid.status_code,
    "base_url": args.base_url,
}
Path("reports/deployment_smoke.json").write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2))
