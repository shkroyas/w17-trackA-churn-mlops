"""Short-lived HTTPS demo supervisor; original application packages remain independent."""

import os
import signal
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

children = []


def start(args):
    process = subprocess.Popen(args)
    children.append(process)
    return process


def stop(*_):
    for process in children:
        process.terminate()
    for process in children:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def handle_signal(*_):
    stop()
    raise SystemExit(0)


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)
password = os.environ.pop("DEMO_PASSWORD")
# The password is fed over stdin; it never appears in process arguments or output.
subprocess.run(
    ["htpasswd", "-ci", "/etc/nginx/demo.htpasswd", "royas"],
    input=password + "\n",
    text=True,
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
os.environ["MLFLOW_TRACKING_URI"] = "http://127.0.0.1:5000"
Path("/tracking").mkdir(exist_ok=True)
start(
    [
        "mlflow",
        "server",
        "--host",
        "127.0.0.1",
        "--port",
        "5000",
        "--workers",
        "1",
        "--backend-store-uri",
        "sqlite:////tracking/mlflow.db",
        "--serve-artifacts",
        "--artifacts-destination",
        "/tracking/artifacts",
        "--default-artifact-root",
        "mlflow-artifacts:/",
        "--static-prefix",
        "/tracking",
    ]
)
for attempt in range(90):
    try:
        with urlopen("http://127.0.0.1:5000/health", timeout=2):
            break
    except OSError:
        time.sleep(2)
else:
    raise RuntimeError("Demo tracking service did not become ready")
os.environ["BACKEND_URL"] = "http://127.0.0.1:8000"
task = os.environ["DEMO_TASK"]
if task == "A":
    subprocess.run(["python", "scripts/run_pipeline.py"], check=True)
    package = "churn_mlops"
else:
    package = "assistant_mlops"
    start(
        [
            "streamlit",
            "run",
            "src/assistant_mlops/ui.py",
            "--server.address",
            "127.0.0.1",
            "--server.port",
            "8501",
            "--server.baseUrlPath",
            "assistant",
            "--server.headless",
            "true",
        ]
    )
    os.environ["BACKEND_URL"] = "http://127.0.0.1:8000"
start(
    [
        "uvicorn",
        package + (".serve:app" if task == "A" else ".api:app"),
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--root-path",
        "/service",
    ]
)
start(["nginx", "-g", "daemon off;"])
try:
    while True:
        if any(process.poll() is not None for process in children):
            raise RuntimeError("A demo service exited")
        time.sleep(2)
finally:
    stop()
