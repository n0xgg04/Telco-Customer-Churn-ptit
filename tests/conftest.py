"""Bộ dữ liệu GIẢ LẬP riêng cho unit/smoke test, không phải IBM dataset."""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def fake_telco():
    rng = np.random.default_rng(42)
    size = 250
    tenure = rng.integers(0, 72, size=size)
    contract = rng.choice(["Month-to-month", "One year", "Two year"],
                          size=size, p=[0.55, 0.25, 0.20])
    internet = rng.choice(["Fiber optic", "DSL", "No"], size=size,
                          p=[0.45, 0.35, 0.20])
    payment = rng.choice(["Electronic check", "Mailed check",
                          "Bank transfer (automatic)", "Credit card (automatic)"],
                         size=size)
    def yesno(p=0.5):
        return rng.choice(["Yes", "No"], size=size, p=[p, 1-p])
    phone = yesno(0.9)
    multiple = yesno(0.43).astype(object)
    multiple[phone == "No"] = "No phone service"
    df = pd.DataFrame({
        "customerID": [f"FAKE{i:05d}" for i in range(size)],
        "gender": rng.choice(["Male", "Female"], size=size),
        "SeniorCitizen": rng.integers(0, 2, size=size),
        "Partner": yesno(), "Dependents": yesno(0.3), "tenure": tenure,
        "PhoneService": phone, "MultipleLines": multiple,
        "InternetService": internet, "OnlineSecurity": yesno(0.3),
        "OnlineBackup": yesno(0.3), "DeviceProtection": yesno(0.3),
        "TechSupport": yesno(0.3), "StreamingTV": yesno(0.4),
        "StreamingMovies": yesno(0.4), "Contract": contract,
        "PaperlessBilling": yesno(0.6), "PaymentMethod": payment,
    })
    for svc in ["OnlineSecurity", "OnlineBackup", "DeviceProtection",
                "TechSupport", "StreamingTV", "StreamingMovies"]:
        df.loc[df.InternetService == "No", svc] = "No internet service"
    charges = (18 + 22 * (phone == "Yes") + 25 * (internet == "Fiber optic") +
               12 * (internet == "DSL") + 8 * (multiple == "Yes") +
               rng.normal(0, 5, size=size))
    df["MonthlyCharges"] = np.round(np.maximum(18, charges), 2)
    total = np.round(df["MonthlyCharges"] * tenure + rng.normal(0, 15, size), 2)
    df["TotalCharges"] = total.astype(str)
    # Dữ liệu tổng phí trống cho 2 khách hàng tương tự bộ IBM.
    df.loc[0:1, "TotalCharges"] = " "
    logits = (0.9 * (contract == "Month-to-month") +
              0.7 * (internet == "Fiber optic") - 0.025 * tenure - 0.35)
    prob = 1 / (1 + np.exp(-logits))
    df["Churn"] = np.where(rng.random(size) < prob, "Yes", "No")
    return df
