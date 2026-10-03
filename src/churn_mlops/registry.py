import argparse
import json
from pathlib import Path

import mlflow
import mlflow.sklearn
import yaml
from mlflow import MlflowClient

from churn_mlops.data import load, split
from churn_mlops.train import build, metrics, tracking


def promote():
    tracking()
    config = yaml.safe_load(Path("configs/params.yaml").read_text())
    rows = json.loads(Path("reports/training_runs.json").read_text())
    winner = max(rows, key=lambda row: (row["f1"], row["roc_auc"]))
    if winner["f1"] < config["f1_floor"]:
        raise RuntimeError("No model meets the predeclared F1 floor")
    client = MlflowClient()
    version = mlflow.register_model(winner["model_uri"], config["model_name"])
    client.transition_model_version_stage(config["model_name"], version.version, "Staging")
    client.set_registered_model_alias(config["model_name"], "staging", version.version)
    client.transition_model_version_stage(
        config["model_name"], version.version, "Production", archive_existing_versions=True
    )
    client.set_registered_model_alias(config["model_name"], "production", version.version)
    record = {
        **winner,
        "model_name": config["model_name"],
        "version": version.version,
        "stages": ["None", "Staging", "Production"],
    }
    Path("reports/registry.json").write_text(json.dumps(record, indent=2))
    client.log_artifact(winner["run_id"], "reports/registry.json")
    return record


def challenge():
    """Drift is a trigger to evaluate, never automatic evidence for promotion."""
    from churn_mlops.drift import inject_drift

    tracking()
    registry = json.loads(Path("reports/registry.json").read_text())
    config = yaml.safe_load(Path("configs/params.yaml").read_text())
    spec = next(s for s in config["models"] if s["name"] == registry["name"])
    # Reserve the original untouched holdout; perturb independently with different seeds.
    x_train, x_test, y_train, y_test = split(load())
    train = inject_drift(x_train.assign(Churn=y_train), seed=43)
    test = inject_drift(x_test.assign(Churn=y_test), seed=44)
    challenger = build(spec, x_train).fit(train.drop(columns="Churn"), train.Churn)
    champion = mlflow.sklearn.load_model(f"models:/{registry['model_name']}@production")
    x, y = test.drop(columns="Churn"), test.Churn
    a, b = metrics(champion, x, y), metrics(challenger, x, y)
    accepted = bool(b["f1"] > a["f1"] + 0.005 and b["roc_auc"] >= a["roc_auc"] - 0.01)
    mlflow.set_experiment("churn-challenge")
    with mlflow.start_run(run_name="drift-challenger") as run:
        mlflow.log_metrics(
            {
                **{"champion_" + k: v for k, v in a.items()},
                **{"challenger_" + k: v for k, v in b.items()},
            }
        )
        info = mlflow.sklearn.log_model(
            challenger,
            "model",
            signature=mlflow.models.infer_signature(x, challenger.predict(x)),
            input_example=x.head(2),
        )
        result = {
            "champion": a,
            "challenger": b,
            "promoted": accepted,
            "run_id": run.info.run_id,
            "evaluation_seed": 44,
        }
        if accepted:
            version = mlflow.register_model(info.model_uri, registry["model_name"])
            client = MlflowClient()
            client.transition_model_version_stage(
                registry["model_name"], version.version, "Staging"
            )
            client.transition_model_version_stage(
                registry["model_name"],
                version.version,
                "Production",
                archive_existing_versions=True,
            )
            client.set_registered_model_alias(registry["model_name"], "production", version.version)
        Path("reports/challenge_result.json").write_text(json.dumps(result, indent=2))
        mlflow.log_artifact("reports/challenge_result.json")
    return result


def rollback(version):
    tracking()
    client = MlflowClient()
    candidate = client.get_model_version("churn-classifier", version)
    if candidate.status != "READY":
        raise ValueError("Rollback version is not ready")
    client.transition_model_version_stage(
        "churn-classifier", version, "Production", archive_existing_versions=True
    )
    client.set_registered_model_alias("churn-classifier", "production", version)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["promote", "challenge", "rollback"])
    parser.add_argument("--version")
    args = parser.parse_args()
    if args.action == "rollback":
        if not args.version:
            parser.error("--version is required for rollback")
        rollback(args.version)
    else:
        print(json.dumps(globals()[args.action](), indent=2))
