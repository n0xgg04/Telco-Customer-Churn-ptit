import pandas as pd
import pytest

from predict import predict_dataframe
from src.dashboard import validate_prediction_data
from src.retrain import (active_model_path, combine_sources, comparison_table, load_runs,
                         required_raw_columns, run_retrain, set_active_model)

CONFIG = {"seed": 7, "test_size": 0.25, "models": {
    "decision_tree": {"features": "report", "criterion": "entropy", "max_depth": 3,
                      "min_samples_leaf": 5, "balancing": "undersample"},
    "logistic": {"features": "report", "solver": "liblinear", "penalty": "l1", "C": 1.0,
                 "balancing": "smote"},
    "linear": {"features": "report", "algorithm": "ridge", "alpha": 1.0},
}}


def test_new_rows_replace_same_customer(fake_telco):
    new = fake_telco.head(3).assign(Churn="Yes")
    combined, info = combine_sources(fake_telco, new)
    assert info == {"base_rows": 250, "new_rows": 3, "replaced": 3, "rows": 250}
    assert combined.set_index("customerID").loc[new.customerID, "Churn"].eq("Yes").all()
    with pytest.raises(ValueError, match="thiếu cột"):
        combine_sources(fake_telco, new.drop(columns="Churn"))


def test_balancing_touches_train_only_and_run_is_saved(fake_telco, tmp_path):
    new = fake_telco.sample(40, random_state=0).assign(customerID=lambda d: "N" + d.customerID)
    run = run_retrain(fake_telco, new, CONFIG, tmp_path / "runs", {"label": "test"})
    tree, logit = run["models"]["decision_tree"], run["models"]["logistic"]
    after = tree["balance"]["after"]
    assert after["stay"] == after["churn"] == tree["balance"]["before"]["churn"]
    assert logit["balance"]["after"]["churn"] == logit["balance"]["before"]["stay"]
    # Test set keeps the real class ratio, whatever the balancing.
    assert tree["split"]["test_counts"] == logit["split"]["test_counts"]
    assert run["merge"]["rows"] == 290 and run["seed"] == 7
    assert len(comparison_table(load_runs(tmp_path / "runs"))) == 3


def test_active_model_drives_prediction(fake_telco, tmp_path):
    run = run_retrain(fake_telco, None, CONFIG, tmp_path / "runs", {"label": "test"})
    set_active_model(tmp_path / "models", run["run_id"], "decision_tree")
    path, active = active_model_path(tmp_path)
    assert active["model"] == "decision_tree" and path.is_file()
    with pytest.raises(ValueError):
        set_active_model(tmp_path / "models", run["run_id"], "linear")
    needed = required_raw_columns(["tenure", "Contract_Two year", "MonthlyCharges"])
    assert needed == ["tenure", "Contract", "MonthlyCharges"]
    sample = fake_telco.head(5)[["customerID", "tenure", "Contract", "InternetService",
                                 "MonthlyCharges", "PaymentMethod"]]
    validate_prediction_data(sample, ["tenure", "Contract", "InternetService", "MonthlyCharges", "PaymentMethod"])
    result = predict_dataframe(sample, path)
    assert result.predicted_churn.isin(["Yes", "No"]).all()
    with pytest.raises(ValueError, match="MonthlyCharges"):
        validate_prediction_data(sample.assign(MonthlyCharges=-1), ["MonthlyCharges"])
