import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import yaml
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from churn_mlops.data import load, split


def tracking():
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))


def build(spec, x, seed=42):
    numeric = x.select_dtypes(include="number").columns.tolist()
    categorical = [c for c in x.columns if c not in numeric]
    prep = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
                ),
                numeric,
            ),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )
    if spec["family"] == "logistic":
        estimator = LogisticRegression(C=spec["C"], max_iter=1000, random_state=seed)
    else:
        estimator = RandomForestClassifier(
            max_depth=spec["max_depth"],
            n_estimators=spec["n_estimators"],
            random_state=seed,
            n_jobs=-1,
        )
    return Pipeline([("preprocess", prep), ("classifier", estimator)])


def metrics(model, x, y):
    predicted = model.predict(x)
    probabilities = model.predict_proba(x)[:, 1]
    return {
        "accuracy": accuracy_score(y, predicted),
        "precision": precision_score(y, predicted, zero_division=0),
        "recall": recall_score(y, predicted, zero_division=0),
        "f1": f1_score(y, predicted, zero_division=0),
        "roc_auc": roc_auc_score(y, probabilities),
    }


def train_all():
    tracking()
    mlflow.set_experiment("churn-training")
    config = yaml.safe_load(Path("configs/params.yaml").read_text())
    x_train, x_test, y_train, y_test = split(load(), config["seed"], config["test_size"])
    out = Path("reports")
    out.mkdir(exist_ok=True)
    rows = []
    for spec in config["models"]:
        with mlflow.start_run(run_name=spec["name"]) as run:
            mlflow.log_params(
                {
                    **spec,
                    "seed": config["seed"],
                    "test_size": config["test_size"],
                    "data_sha256": Path("configs/data.sha256").read_text().strip(),
                }
            )
            model = build(spec, x_train, config["seed"]).fit(x_train, y_train)
            scores = metrics(model, x_test, y_test)
            mlflow.log_metrics(scores)
            for label, display in [
                ("confusion_matrix", ConfusionMatrixDisplay.from_estimator),
                ("roc_curve", RocCurveDisplay.from_estimator),
            ]:
                display(model, x_test, y_test)
                filename = out / f"{spec['name']}_{label}.png"
                plt.savefig(filename, bbox_inches="tight")
                plt.close("all")
                mlflow.log_artifact(str(filename))
            info = mlflow.sklearn.log_model(
                model,
                "model",
                signature=infer_signature(x_train, model.predict(x_train)),
                input_example=x_train.head(2),
            )
            rows.append(
                {
                    "name": spec["name"],
                    "run_id": run.info.run_id,
                    "model_uri": info.model_uri,
                    **scores,
                }
            )
    Path("reports/training_runs.json").write_text(json.dumps(rows, indent=2))
    columns = ["name", "accuracy", "precision", "recall", "f1", "roc_auc", "run_id"]
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                f"{row[c]:.4f}" if isinstance(row[c], float) else str(row[c]) for c in columns
            )
            + " |"
        )
    Path("reports/model_comparison.md").write_text("\n".join(lines) + "\n")
    return rows


if __name__ == "__main__":
    train_all()
