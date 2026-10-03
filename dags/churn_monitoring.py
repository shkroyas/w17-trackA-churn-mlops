"""Assignment demo: daily synthetic drift check and holdout-gated retraining."""

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator

ROOT = Path(os.getenv("PROJECT_DIR", "/opt/project"))


def drift_branch():
    subprocess.run(
        [str(ROOT / ".venv/bin/python"), "-m", "churn_mlops.drift"],
        cwd=ROOT,
        check=True,
        timeout=600,
    )
    verdict = json.loads((ROOT / "reports/drift_verdict.json").read_text())
    return "evaluate_challenger" if verdict["drifted"]["significant"] else "no_retrain"


def retrain():
    subprocess.run(
        [str(ROOT / ".venv/bin/python"), "-m", "churn_mlops.registry", "challenge"],
        cwd=ROOT,
        check=True,
        timeout=900,
    )


with DAG(
    "churn_daily_monitoring",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "royas", "retries": 1, "retry_delay": timedelta(minutes=2)},
    dagrun_timeout=timedelta(minutes=30),
) as dag:
    check = BranchPythonOperator(task_id="check_drift", python_callable=drift_branch)
    challenge = PythonOperator(task_id="evaluate_challenger", python_callable=retrain)
    no_retrain = EmptyOperator(task_id="no_retrain")
    done = EmptyOperator(task_id="done", trigger_rule="none_failed_min_one_success")
    check >> [challenge, no_retrain]
    challenge >> done
    no_retrain >> done
