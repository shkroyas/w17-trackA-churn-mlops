"""Checksum-verified IBM Telco data; all preprocessing learned on training rows."""

import hashlib
from pathlib import Path

import httpx
import pandas as pd
from sklearn.model_selection import train_test_split

URL = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
PATH = Path("data/raw/telco.csv")
CHECKSUM = Path("configs/data.sha256")


def download():
    expected = CHECKSUM.read_text().strip()
    if not PATH.exists():
        response = httpx.get(URL, timeout=60, follow_redirects=True)
        response.raise_for_status()
        content = response.content
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError("Dataset checksum mismatch; refusing unverified data")
        PATH.parent.mkdir(parents=True, exist_ok=True)
        PATH.write_bytes(content)
    if hashlib.sha256(PATH.read_bytes()).hexdigest() != expected:
        raise ValueError("Cached dataset checksum mismatch")
    return PATH


def load():
    frame = pd.read_csv(download())
    if len(frame) != 7043 or frame.customerID.duplicated().any():
        raise ValueError("Unexpected dataset identity or row count")
    frame["TotalCharges"] = pd.to_numeric(frame.TotalCharges, errors="coerce")
    frame["Churn"] = frame.Churn.map({"Yes": 1, "No": 0})
    return frame.drop(columns="customerID")


def split(frame, seed=42, test_size=0.2):
    x, y = frame.drop(columns="Churn"), frame.Churn
    return train_test_split(x, y, test_size=test_size, stratify=y, random_state=seed)


def monitoring_split(frame, seed=42):
    return train_test_split(frame, test_size=0.3, stratify=frame.Churn, random_state=seed)
