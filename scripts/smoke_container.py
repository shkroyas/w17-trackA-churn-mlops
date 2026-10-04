"""Offline container integration: real services and auth, no live LLM quality claim."""

import argparse
import base64
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, choices=["A", "B"])
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    parser.add_argument("--output", type=Path, default=Path("container-smoke.json"))
    args = parser.parse_args()
    password = os.environ["DEMO_PASSWORD"]
    auth = "Basic " + base64.b64encode(("royas:" + password).encode()).decode()

    def request(path, payload=None, authenticated=True):
        headers = {"Authorization": auth} if authenticated else {}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode()
        req = Request(args.base_url + path, headers=headers, data=data)
        try:
            with urlopen(req, timeout=15) as response:
                return response.status, response.read()
        except HTTPError as exc:
            return exc.code, exc.read()

    ready = False
    for _ in range(150):
        try:
            status, body = request("/healthz", authenticated=False)
            if status == 200:
                health = json.loads(body)
                ready = True
                break
        except (URLError, TimeoutError):
            pass
        time.sleep(2)
    assert ready, "Container API did not become ready"
    result = {
        "task": args.task,
        "scope": "Real container runtime integration; no live provider quality evaluation",
        "health": health,
        "checks": [],
    }
    routes = ["/", "/service/docs", "/service/openapi.json", "/tracking/"]
    if args.task == "B":
        assert health["configuration_version"] == "v34"
        routes += ["/assistant/", "/reports/v34/gate.json", "/reports/v34/evidently_judge.html"]
    for route in routes:
        assert request(route)[0] == 200, route + " unavailable"
        assert request(route, authenticated=False)[0] == 401, route + " unprotected"
        result["checks"].append({"path": route, "authenticated": 200, "anonymous": 401})
    if args.task == "A":
        payload = json.loads(Path("reports/deployment_smoke.json").read_text())["request"]
        status, body = request("/service/predict", payload)
        assert status == 200
        prediction = json.loads(body)
        assert 0 <= prediction["churn_probability"] <= 1 and prediction["model_version"]
        assert request("/service/predict", {})[0] == 422
        result.update(prediction=prediction, invalid_input_http_status=422)
    result["status"] = "passed"
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("Container runtime integration passed for Task " + args.task)


if __name__ == "__main__":
    main()
