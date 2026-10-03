import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from churn_mlops.data import load, monitoring_split, split
from churn_mlops.drift import inject_drift
from churn_mlops.serve import app
from churn_mlops.train import build


def test_data_identity_and_holdout():
    frame = load()
    assert len(frame) == 7043 and frame.TotalCharges.isna().sum() == 11
    x_train, x_test, y_train, y_test = split(frame)
    assert not set(x_train.index) & set(x_test.index)
    assert abs(y_train.mean() - y_test.mean()) < 0.001


def test_preprocessor_learns_only_training_rows():
    x = pd.DataFrame({"TotalCharges": [1.0, 3.0, None, 9.0], "Contract": ["a", "a", "b", "b"]})
    model = build({"family": "logistic", "C": 1}, x)
    model.fit(x, [0, 1, 0, 1])
    numeric = model.named_steps["preprocess"].named_transformers_["numeric"]
    assert numeric.named_steps["impute"].statistics_[0] == 3
    assert model.predict(pd.DataFrame({"TotalCharges": [1e9], "Contract": ["unseen"]})).shape == (
        1,
    )


def test_engineered_drift_is_reproducible():
    reference, current = monitoring_split(load())
    drifted = inject_drift(current)
    assert drifted.equals(inject_drift(current))
    assert drifted.MonthlyCharges.mean() > current.MonthlyCharges.mean() + 25
    assert (drifted.Contract == "Month-to-month").mean() > (
        current.Contract == "Month-to-month"
    ).mean() + 0.2


def test_registry_api_and_input_contract():
    if not Path("reports/registry.json").exists():
        pytest.skip("Run training and promotion for registry integration test")
    sample = load().drop(columns="Churn").dropna().iloc[0].to_dict()
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        result = client.post("/predict", json=sample)
        assert result.status_code == 200
        assert 0 <= result.json()["churn_probability"] <= 1
        assert result.json()["model_version"] == health.json()["version"]
        assert client.post("/predict", json={"tenure": -1}).status_code == 422
        invalid = {**sample, "Contract": "unknown"}
        assert client.post("/predict", json=invalid).status_code == 422
        Path("reports/api_demo.json").write_text(
            json.dumps(
                {
                    "health": health.json(),
                    "request": sample,
                    "prediction": result.json(),
                    "invalid_request_status": 422,
                },
                indent=2,
            )
        )
