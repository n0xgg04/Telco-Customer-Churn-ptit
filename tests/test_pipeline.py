import numpy as np
import pandas as pd

from src.data import clean_dataset, encode_features, prepare_prediction_features
from src.models import run_decision_tree, run_linear_regression, run_logistic_regression
from src.schema import LOGISTIC_SELECTED


def test_cleaning_and_encoding(fake_telco):
    df, quality = clean_dataset(fake_telco)
    assert quality["so_dong_ban_dau"] == 250
    assert quality["so_dong_sau_lam_sach"] == 248
    assert len(df) == 248
    X = encode_features(df)
    assert not X.isna().any().any()
    assert "customerID" not in X.columns
    assert "Churn" not in X.columns
    assert all(c in X.columns for c in LOGISTIC_SELECTED)


def test_model_smoke(fake_telco, tmp_path):
    df, _ = clean_dataset(fake_telco)
    fig_dir, table_dir, model_dir = (tmp_path / p for p in ["figures", "tables", "models"])
    for p in [fig_dir, table_dir, model_dir]:
        p.mkdir()
    lin = run_linear_regression(df, table_dir)
    tree = run_decision_tree(df, fig_dir, table_dir)
    logit = run_logistic_regression(df, fig_dir, table_dir, model_dir)
    assert np.isfinite(lin["selected"]["mae_test"])
    assert 0 <= tree["accuracy"] <= 1
    assert 0 <= logit["selected"]["recall_churn_1"] <= 1
    assert (model_dir / "logistic_selected.joblib").is_file()
    sample = pd.DataFrame([{
        "gender": "Female", "Dependents": "No", "tenure": 4,
        "PhoneService": "Yes", "OnlineSecurity": "No", "OnlineBackup": "No",
        "DeviceProtection": "No", "TechSupport": "No",
        "PaperlessBilling": "Yes", "InternetService": "Fiber optic",
        "PaymentMethod": "Electronic check", "Contract": "Month-to-month",
    }])
    prepared = prepare_prediction_features(sample, LOGISTIC_SELECTED)
    assert prepared.shape == (1, len(LOGISTIC_SELECTED))
