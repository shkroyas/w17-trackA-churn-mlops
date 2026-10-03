import asyncio
from contextlib import asynccontextmanager

import mlflow.sklearn
import pandas as pd
from fastapi import FastAPI, HTTPException
from mlflow import MlflowClient
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from churn_mlops.train import tracking

YesNo = Literal["Yes", "No"]
InternetFlag = Literal["Yes", "No", "No internet service"]


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gender: Literal["Male", "Female"]
    SeniorCitizen: Literal[0, 1]
    Partner: YesNo
    Dependents: YesNo
    tenure: int = Field(ge=0, le=120)
    PhoneService: YesNo
    MultipleLines: Literal["Yes", "No", "No phone service"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: InternetFlag
    OnlineBackup: InternetFlag
    DeviceProtection: InternetFlag
    TechSupport: InternetFlag
    StreamingTV: InternetFlag
    StreamingMovies: InternetFlag
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: YesNo
    PaymentMethod: Literal[
        "Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"
    ]
    MonthlyCharges: float = Field(ge=0, le=1000, allow_inf_nan=False)
    TotalCharges: float = Field(ge=0, le=100000, allow_inf_nan=False)


@asynccontextmanager
async def lifespan(app):
    tracking()
    try:
        version = MlflowClient().get_model_version_by_alias("churn-classifier", "production")
        app.state.model = await asyncio.to_thread(
            mlflow.sklearn.load_model, f"models:/churn-classifier/{version.version}"
        )
        app.state.version = version.version
    except Exception:
        app.state.model = None
        app.state.version = None
    yield


app = FastAPI(title="Telco Churn Prediction", lifespan=lifespan)


@app.get("/health")
def health():
    if app.state.model is None:
        raise HTTPException(503, "No production model available")
    return {"status": "healthy", "model": "churn-classifier", "version": app.state.version}


@app.post("/predict")
async def predict(customer: Customer):
    if app.state.model is None:
        raise HTTPException(503, "No production model available")
    frame = pd.DataFrame([customer.model_dump()])
    probabilities = await asyncio.to_thread(app.state.model.predict_proba, frame)
    probability = float(probabilities[0, 1])
    return {
        "churn_probability": probability,
        "churn": probability >= 0.5,
        "model_version": app.state.version,
    }
