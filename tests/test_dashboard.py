"""Kiểm tra luồng dashboard, số đếm đánh giá và lỗi dữ liệu dự đoán."""
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.dashboard import confusion_from_report, group_summary, validate_prediction_data

ROOT = Path(__file__).resolve().parents[1]
HAS_ARTIFACTS = (ROOT / "outputs" / "metrics.json").exists()


def test_group_rates_use_each_group_denominator():
    data = pd.DataFrame({"Contract": ["One year", "One year", "Two year"],
                         "Churn": ["Yes", "No", "No"]})
    result = group_summary(data, "Contract").set_index("Contract")
    assert result.loc["One year", "rate"] == .5
    assert result.loc["Two year", "rate"] == 0
    assert result.customers.sum() == 3


def test_confusion_uses_json_precision_not_rounded_report():
    report = "0  0.89  0.73  0.80  1033\n1  0.51  0.76  0.61  374\n"
    result = confusion_from_report({"recall_churn_1": 284 / 374,
                                    "accuracy": 1040 / 1407}, report)
    assert result == {"tn": 756, "fp": 277, "fn": 90, "tp": 284}


def test_prediction_validation_rejects_silent_encoding_errors():
    data = pd.read_csv(ROOT / "data" / "new_customers_example.csv")
    validate_prediction_data(data)
    for column, value, message in [
        ("Contract", "Hop dong thang", "Contract"),
        ("tenure", -1, "tenure"),
        ("tenure", 2.5, "tenure"),
        ("gender", "", "gender"),
    ]:
        invalid = data.copy()
        if column == "tenure":
            invalid[column] = invalid[column].astype(float)
        invalid.loc[0, column] = value
        with pytest.raises(ValueError, match=message):
            validate_prediction_data(invalid)
    invalid = data.copy()
    invalid.loc[0, "InternetService"] = "No"
    invalid.loc[0, "TechSupport"] = "Yes"
    with pytest.raises(ValueError, match="không nhất quán"):
        validate_prediction_data(invalid)
    with pytest.raises(ValueError, match="Thiếu cột"):
        validate_prediction_data(data.drop(columns="Contract"))
    with pytest.raises(ValueError, match="chưa có khách hàng"):
        validate_prediction_data(data.iloc[:0])


@pytest.fixture
def dashboard():
    if not HAS_ARTIFACTS:
        pytest.skip("Chạy pipeline để tạo dữ liệu cho kiểm thử giao diện.")
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
    assert not app.exception
    return app


def assert_healthy(app):
    assert not app.exception, [error.message for error in app.exception]
    assert not app.error, [error.value for error in app.error]


def click_label(app, label):
    next(button for button in app.button if button.label == label).click().run()


def test_all_pages_and_model_details(dashboard):
    app = dashboard
    for page in ["Thống kê mô tả", "Kỹ thuật khai phá", "1. Dữ liệu", "2. Tiền xử lý", "3. Huấn luyện", "4. So sánh", "5. Dự đoán", "Hướng dẫn sử dụng"]:
        app.radio(key="navigation").set_value(page).run()
        assert_healthy(app)
    for topic in app.selectbox(key="guide_topic").options:
        app.selectbox(key="guide_topic").select(topic).run()
        assert_healthy(app)
    app.radio(key="navigation").set_value("Kỹ thuật khai phá").run()
    for name in ["Hồi quy logistic (sau điều chỉnh)", "Hồi quy logistic (ban đầu)", "Cây quyết định"]:
        next(box for box in app.selectbox if box.label == "Mô hình").select(name).run()
        assert_healthy(app)


def test_empty_filters_reset_and_search(dashboard):
    app = dashboard
    app.radio(key="navigation").set_value("Thống kê mô tả").run()
    app.multiselect(key="filter_contract").set_value([]).run()
    assert_healthy(app)
    assert any("Không có khách hàng" in warning.value for warning in app.warning)
    click_label(app, "Đặt lại bộ lọc")
    assert_healthy(app)
    assert len(app.multiselect(key="filter_contract").value) == 3
    app.text_input(key="data_search").set_value("NOT_A_CUSTOMER").run()
    assert_healthy(app)
    assert app.dataframe[-1].value.empty


def test_single_and_batch_predictions(dashboard):
    app = dashboard
    app.radio(key="navigation").set_value("5. Dự đoán").run()
    click_label(app, "Dự đoán nguy cơ")
    assert_healthy(app)
    assert next(metric for metric in app.metric if metric.label == "Nhãn dự đoán").value == "Rời bỏ"
    app.selectbox(key="scenario").select("DEMO002 · hợp đồng dài hạn").run()
    click_label(app, "Dự đoán nguy cơ")
    assert_healthy(app)
    assert next(metric for metric in app.metric if metric.label == "Nhãn dự đoán").value == "Không rời bỏ"
    app.radio(key="prediction_mode").set_value("Hàng loạt qua CSV").run()
    click_label(app, "Chạy thử 3 khách hàng mẫu")
    assert_healthy(app)
    assert len(app.dataframe[0].value) == 3
    assert next(metric for metric in app.metric if metric.label == "Đã chấm điểm").value == "3"
    app.text_input(key="prediction_search").set_value("DEMO002").run()
    assert_healthy(app)
    assert len(app.dataframe[0].value) == 1
    assert next(metric for metric in app.metric if metric.label == "Đã chấm điểm").value == "3"


def test_retrain_flow(dashboard, tmp_path, monkeypatch):
    monkeypatch.setenv("TELCO_RUNS_DIR", str(tmp_path))
    app = dashboard
    app.radio(key="navigation").set_value("2. Tiền xử lý").run()
    for method in ["smote", "undersample", "none"]:
        app.selectbox(key="pp_bal").set_value(method).run()
        assert_healthy(app)
    for view in ["removed", "kept", "all"]:
        app.button(key=f"clean_card_{view}").click().run()
        assert_healthy(app)
        assert app.session_state["clean_view"] == view
    app.radio(key="navigation").set_value("3. Huấn luyện").run()
    app.radio(key="rt_seed_mode").set_value("fixed").run()
    click_label(app, "Huấn luyện")
    assert_healthy(app)
    assert len(list(tmp_path.glob("*/run.json"))) == 1
    assert any(button.label == "Dùng mô hình này để dự đoán" for button in app.button)
    assert app.selectbox(key="rt_logit_solver").disabled and app.selectbox(key="rt_lin_algo").disabled
    app.selectbox(key="rt_logit_bal").set_value("class_weight").run()
    click_label(app, "Huấn luyện")
    assert_healthy(app)
    assert len(list(tmp_path.glob("*/run.json"))) == 2
    app.radio(key="navigation").set_value("4. So sánh").run()
    assert_healthy(app)
    app.radio(key="cmp_metric").set_value("f1_churn_1").run()
    assert_healthy(app)
    app.button(key="to_step5").click().run()
    assert app.radio(key="navigation").value == "5. Dự đoán"
