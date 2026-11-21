"""Nhãn hiển thị và các phép tổng hợp dùng riêng cho dashboard."""
import re

import numpy as np
import pandas as pd

from .schema import PREDICT_REQUIRED


FIELD_LABELS = {
    "customerID": "Mã khách hàng", "gender": "Giới tính",
    "SeniorCitizen": "Khách hàng cao tuổi", "Partner": "Có bạn đời",
    "Dependents": "Có người phụ thuộc", "tenure": "Thời gian sử dụng (tháng)",
    "PhoneService": "Dịch vụ điện thoại", "MultipleLines": "Nhiều đường dây",
    "InternetService": "Loại Internet", "OnlineSecurity": "Bảo mật trực tuyến",
    "OnlineBackup": "Sao lưu trực tuyến", "DeviceProtection": "Bảo vệ thiết bị",
    "TechSupport": "Hỗ trợ kỹ thuật", "StreamingTV": "Truyền hình trực tuyến",
    "StreamingMovies": "Phim trực tuyến", "Contract": "Loại hợp đồng",
    "PaperlessBilling": "Hóa đơn điện tử", "PaymentMethod": "Thanh toán",
    "MonthlyCharges": "Phí hàng tháng", "TotalCharges": "Tổng phí tích lũy",
    "Churn": "Churn",
}

VALUE_LABELS = {
    "Yes": "Có", "No": "Không", "Female": "Nữ", "Male": "Nam",
    "Month-to-month": "Theo tháng", "One year": "Một năm", "Two year": "Hai năm",
    "Fiber optic": "Cáp quang", "DSL": "DSL",
    "Electronic check": "Séc điện tử", "Mailed check": "Séc gửi thư",
    "Bank transfer (automatic)": "Chuyển khoản tự động",
    "Credit card (automatic)": "Thẻ tín dụng tự động",
    "No internet service": "Không có Internet",
    "No phone service": "Không có điện thoại",
}

RISK_LABELS = {"Low": "Thấp", "Medium": "Trung bình", "High": "Cao"}

METRIC_LABELS = {
    "accuracy": "Accuracy",
    "precision_churn_1": "Precision (lớp 1)",
    "recall_churn_1": "Recall (lớp 1)",
    "f1_churn_1": "F1-score (lớp 1)",
    "roc_auc": "ROC AUC",
}

METRIC_HELP = {
    "accuracy": "Số dự đoán đúng / tổng số khách hàng kiểm tra. Có thể cao dù bỏ sót nhiều khách rời bỏ.",
    "precision_churn_1": "Trong các khách hàng được cảnh báo rời bỏ, tỷ lệ thực sự đã rời bỏ. Precision thấp nghĩa là có nhiều cảnh báo sai.",
    "recall_churn_1": "Trong các khách hàng thực sự đã rời bỏ, tỷ lệ được mô hình phát hiện. Recall thấp nghĩa là bỏ sót nhiều người.",
    "f1_churn_1": "Trung bình điều hòa của Precision và Recall: 2 × Precision × Recall / (Precision + Recall).",
    "roc_auc": "Khả năng xếp khách rời bỏ cao điểm hơn khách ở lại khi xét nhiều ngưỡng. 0,5 tương đương ngẫu nhiên; 1 là phân biệt hoàn hảo.",
}


def value_label(value) -> str:
    return VALUE_LABELS.get(str(value), str(value))


def feature_label(feature: str) -> str:
    for prefix in ("InternetService", "Contract", "PaymentMethod"):
        if feature.startswith(prefix + "_"):
            return f"{FIELD_LABELS[prefix]}: {value_label(feature[len(prefix) + 1:])}"
    return FIELD_LABELS.get(feature, feature)


def group_summary(df: pd.DataFrame, feature: str) -> pd.DataFrame:
    """Tỷ lệ theo mẫu số riêng từng nhóm, luôn giữ kèm số lượng quan sát."""
    grouped = (df.assign(_churn=df["Churn"].eq("Yes"))
               .groupby(feature, observed=True, dropna=False)
               .agg(customers=("_churn", "size"), churned=("_churn", "sum"))
               .reset_index())
    grouped["rate"] = grouped["churned"] / grouped["customers"]
    if feature == "SeniorCitizen":
        grouped["group"] = grouped[feature].map({0: "Không cao tuổi", 1: "Cao tuổi"})
    else:
        grouped["group"] = grouped[feature].map(value_label)
    return grouped.sort_values("rate", ascending=False).reset_index(drop=True)


def confusion_from_report(scores: dict, report: str) -> dict[str, int]:
    """Khôi phục số đếm từ support trong báo cáo và metrics JSON đủ độ chính xác.

    Các báo cáo TXT làm tròn precision/recall nên chỉ lấy support từ TXT.
    Accuracy và recall được lấy từ JSON do pipeline lưu, không hard-code số đếm.
    """
    supports = {}
    for line in report.splitlines():
        match = re.fullmatch(r"\s*([01])\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+(\d+)\s*", line)
        if match:
            supports[int(match[1])] = int(match[2])
    if set(supports) != {0, 1}:
        raise ValueError("Báo cáo chưa có đủ số khách kiểm tra của hai lớp.")
    tp = round(scores["recall_churn_1"] * supports[1])
    correct = round(scores["accuracy"] * sum(supports.values()))
    tn = correct - tp
    result = {"tn": tn, "fp": supports[0] - tn,
              "fn": supports[1] - tp, "tp": tp}
    if min(result.values()) < 0:
        raise ValueError("Số liệu metrics và báo cáo không khớp nhau.")
    return result


def validate_prediction_data(df: pd.DataFrame, required: list[str] | None = None) -> None:
    """Bắt các lỗi CSV thường gặp trước khi gọi mô hình; không sửa dữ liệu ngầm.

    required: cột gốc mà mô hình đang dùng cần đến (mặc định: Logistic theo báo cáo).
    """
    required = list(required or PREDICT_REQUIRED)
    if df.empty:
        raise ValueError("CSV chưa có khách hàng nào. Hãy thêm ít nhất một dòng dữ liệu.")
    missing = [col for col in required if col not in df]
    if missing:
        raise ValueError("Thiếu cột bắt buộc: " + ", ".join(missing)
                         + ". Hãy tải CSV mẫu và giữ nguyên dòng tiêu đề.")
    if df[required].isna().any().any():
        cols = df[required].columns[df[required].isna().any()]
        raise ValueError("Có ô trống trong các cột: " + ", ".join(cols) + ".")
    numeric = {"tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"}
    allowed = {
        "gender": {"Male", "Female"},
        "InternetService": {"DSL", "Fiber optic", "No"},
        "Contract": {"Month-to-month", "One year", "Two year"},
        "PaymentMethod": {"Electronic check", "Mailed check",
                          "Bank transfer (automatic)", "Credit card (automatic)"},
    }
    services = {"OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
                "StreamingTV", "StreamingMovies"}
    for col in required:
        if col not in allowed and col not in numeric:
            allowed[col] = {"Yes", "No"}
            if col in services:
                allowed[col].add("No internet service")
            if col == "MultipleLines":
                allowed[col].add("No phone service")
    for col, choices in allowed.items():
        if col not in required:
            continue
        values = df[col].astype(str).str.strip()
        invalid = ~values.isin(choices)
        if invalid.any():
            examples = ", ".join(values[invalid].unique()[:3])
            raise ValueError(f"Cột {col} có giá trị không hợp lệ: {examples}. "
                             "Xem bảng định dạng trong phần Hướng dẫn sử dụng.")
    if "tenure" in required:
        tenure = pd.to_numeric(df["tenure"], errors="coerce")
        if (tenure.isna() | ~np.isfinite(tenure) | (tenure < 0) | (tenure % 1 != 0)).any():
            raise ValueError("tenure phải là số tháng nguyên, không âm và không được để trống.")
    for col in {"MonthlyCharges", "TotalCharges"} & set(required):
        values = pd.to_numeric(df[col], errors="coerce")
        if (values.isna() | (values < 0)).any():
            raise ValueError(f"{col} phải là số không âm.")
    if "InternetService" in required:
        no_internet = df["InternetService"].astype(str).str.strip().eq("No")
        for col in services & set(required):
            if (no_internet & df[col].astype(str).str.strip().eq("Yes")).any():
                raise ValueError(f"Hồ sơ không nhất quán: InternetService=No nhưng {col}=Yes. "
                                 "Hãy kiểm tra lại dịch vụ của khách hàng.")


def prediction_display(df: pd.DataFrame) -> pd.DataFrame:
    """Bảng xem tiếng Việt; file xuất vẫn giữ đúng tên cột CSV gốc."""
    result = df.copy()
    for col in result.columns:
        if col == "predicted_churn":
            result[col] = result[col].map({"Yes": "Rời bỏ", "No": "Không rời bỏ"})
        elif col == "risk_group":
            result[col] = result[col].map(RISK_LABELS)
        elif col == "Churn":
            result[col] = result[col].map({"Yes": "Rời bỏ", "No": "Không rời bỏ"})
        elif col in FIELD_LABELS and result[col].dtype.kind in "OUS":
            result[col] = result[col].map(value_label)
    return result.rename(columns={**FIELD_LABELS, "churn_risk_score": "Điểm rủi ro",
                                  "predicted_churn": "Dự đoán", "risk_group": "Mức rủi ro"})
