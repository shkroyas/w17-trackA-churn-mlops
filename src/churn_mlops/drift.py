import json
from pathlib import Path

import mlflow
import numpy as np
import yaml
from evidently import DataDefinition, Dataset, Report
from evidently.metrics import ValueDrift
from evidently.presets import DataDriftPreset

from churn_mlops.custom_metrics import MeanChargeShift
from churn_mlops.data import load, monitoring_split
from churn_mlops.train import tracking


def inject_drift(frame, seed=42, flip_target=False):
    rng = np.random.default_rng(seed)
    weights = np.where(frame.Contract == "Month-to-month", 5.0, 1.0)
    current = frame.sample(
        n=len(frame), replace=True, weights=weights, random_state=seed
    ).reset_index(drop=True)
    current["MonthlyCharges"] += rng.normal(35, 6, len(current))
    if flip_target:
        positions = rng.choice(len(current), int(len(current) * 0.05), replace=False)
        current.loc[positions, "Churn"] = 1 - current.loc[positions, "Churn"]
    return current


def datasets(frame):
    # Binary SeniorCitizen is categorical; target is explicitly categorical.
    numeric = ["tenure", "MonthlyCharges", "TotalCharges"]
    categorical = [c for c in frame.columns if c not in numeric]
    definition = DataDefinition(numerical_columns=numeric, categorical_columns=categorical)
    return Dataset.from_pandas(frame, data_definition=definition)


def monitor():
    tracking()
    mlflow.set_experiment("churn-monitoring")
    config = yaml.safe_load(Path("configs/params.yaml").read_text())
    reference, control = monitoring_split(load())
    results = {}
    for label, current in [
        ("control", control),
        ("drifted", inject_drift(control, flip_target=True)),
    ]:
        with mlflow.start_run(run_name=label) as run:
            cur, ref = datasets(current), datasets(reference)
            reports = {
                "data": Report(
                    [
                        DataDriftPreset(
                            columns=[c for c in current if c != "Churn"],
                            num_method="wasserstein",
                            num_threshold=0.15,
                            cat_method="jensenshannon",
                            cat_threshold=0.1,
                        )
                    ],
                    include_tests=True,
                ),
                "target": Report(
                    [ValueDrift(column="Churn", method="jensenshannon", threshold=0.1)],
                    include_tests=True,
                ),
                "custom": Report([MeanChargeShift()], include_tests=True),
            }
            summaries = {}
            for kind, report in reports.items():
                snapshot = report.run(cur, ref)
                path = Path(f"reports/{label}_{kind}_drift.html")
                snapshot.save_html(str(path))
                summaries[kind] = snapshot.dict()
                Path(f"reports/{label}_{kind}_drift.json").write_text(snapshot.json())
                mlflow.log_artifact(str(path))
                mlflow.log_artifact(f"reports/{label}_{kind}_drift.json")
            # Derive feature flags from Evidently's calculated ValueDrift results.
            flags = []
            for item in summaries["data"]["metrics"]:
                if item["metric_name"].startswith("ValueDrift"):
                    name = item["config"]["column"]
                    threshold = item["config"].get("threshold", 0.1)
                    if item["value"] >= threshold:
                        flags.append(name)
            mean_shift = float(abs(current.MonthlyCharges.mean() - reference.MonthlyCharges.mean()))
            target_shift = float(abs(current.Churn.mean() - reference.Churn.mean()))
            significant = bool(
                flags
                or mean_shift > config["drift_mean_threshold"]
                or target_shift > config["drift_target_threshold"]
            )
            record = {
                "run_id": run.info.run_id,
                "drifted_columns": flags,
                "mean_charge_shift": mean_shift,
                "churn_rate_shift": target_shift,
                "reference_churn_rate": float(reference.Churn.mean()),
                "current_churn_rate": float(current.Churn.mean()),
                "significant": significant,
            }
            mlflow.log_metrics(
                {
                    "drifted_columns": len(flags),
                    "mean_charge_shift": mean_shift,
                    "churn_rate_shift": target_shift,
                }
            )
            results[label] = record
    Path("reports/drift_verdict.json").write_text(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    print(json.dumps(monitor(), indent=2))
