"""Assignment scorecard. Static CI checks never pretend runtime evidence exists."""

import argparse
import json
from pathlib import Path


def check(static=False):
    checks = {}
    for name, path in {
        "uv project": "pyproject.toml",
        "committed lockfile": "uv.lock",
        "data integrity pin": "configs/data.sha256",
        "training implementation": "src/churn_mlops/train.py",
        "registry promotion and rollback": "src/churn_mlops/registry.py",
        "registered-model API": "src/churn_mlops/serve.py",
        "native Evidently custom metric": "src/churn_mlops/custom_metrics.py",
        "Airflow DAG": "dags/churn_monitoring.py",
        "documented workflow": "README.md",
    }.items():
        checks[name] = Path(path).is_file() and Path(path).stat().st_size > 0
    if not static:
        from churn_mlops.train import tracking
        from mlflow import MlflowClient

        tracking()
        client = MlflowClient()
        runs = (
            json.loads(Path("reports/training_runs.json").read_text())
            if Path("reports/training_runs.json").exists()
            else []
        )
        live = [client.get_run(row["run_id"]) for row in runs]
        checks["at least three different hyperparameter runs"] = (
            len({r.data.params["name"] for r in live}) >= 3
        )
        checks["five classification metrics per run"] = bool(live) and all(
            {"accuracy", "precision", "recall", "f1", "roc_auc"} <= set(r.data.metrics)
            for r in live
        )
        checks["model, confusion matrix, ROC artifacts per run"] = bool(live) and all(
            {
                "model",
                r.data.params["name"] + "_confusion_matrix.png",
                r.data.params["name"] + "_roc_curve.png",
            }
            <= {a.path for a in client.list_artifacts(r.info.run_id)}
            for r in live
        )
        checks["full exported comparison"] = (
            Path("reports/model_comparison.md").exists() and len(runs) >= 3
        )
        registry = (
            json.loads(Path("reports/registry.json").read_text())
            if Path("reports/registry.json").exists()
            else {}
        )
        checks["Staging to Production evidence"] = registry.get("stages") == [
            "None",
            "Staging",
            "Production",
        ]
        try:
            production = client.get_model_version_by_alias("churn-classifier", "production")
            checks["live registry production model"] = production.current_stage == "Production"
        except Exception:
            checks["live registry production model"] = False
        checks["serving demonstration and validation"] = Path("reports/api_demo.json").exists()
        checks["six Evidently HTML reports"] = len(list(Path("reports").glob("*_drift.html"))) == 6
        verdict = (
            json.loads(Path("reports/drift_verdict.json").read_text())
            if Path("reports/drift_verdict.json").exists()
            else {}
        )
        checks["engineered columns detected, no control alarms"] = {
            "MonthlyCharges",
            "Contract",
        } <= set(verdict.get("drifted", {}).get("drifted_columns", [])) and verdict.get(
            "control", {}
        ).get("drifted_columns") == []
        checks["drift reports logged in MLflow"] = bool(verdict) and all(
            len([a for a in client.list_artifacts(v["run_id"]) if a.path.endswith(".html")]) == 3
            for v in verdict.values()
        )
        checks["retraining challenge decision recorded"] = Path(
            "reports/challenge_result.json"
        ).exists()
    lines = ["| Requirement | Result |", "|---|---|"] + [
        f"| {name} | {'PASS' if passed else 'FAIL'} |" for name, passed in checks.items()
    ]
    lines.append(
        f"\n{sum(checks.values())}/{len(checks)} checks pass."
        + (" Static only; runtime deliverables not evaluated." if static else "")
    )
    print("\n".join(lines))
    if not static:
        Path("reports/deliverables.md").write_text("\n".join(lines) + "\n")
    return all(checks.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", action="store_true")
    raise SystemExit(0 if check(parser.parse_args().static) else 1)
