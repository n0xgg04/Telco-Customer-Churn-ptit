"""Khai báo đặc trưng gốc và các đặc trưng được chọn theo báo cáo."""

RAW_COLUMNS = [
    "customerID", "gender", "SeniorCitizen", "Partner", "Dependents", "tenure",
    "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity",
    "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV",
    "StreamingMovies", "Contract", "PaperlessBilling", "PaymentMethod",
    "MonthlyCharges", "TotalCharges", "Churn",
]

BINARY_COLS = [
    "Partner", "Dependents", "PhoneService", "MultipleLines", "OnlineSecurity",
    "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV",
    "StreamingMovies", "PaperlessBilling",
]
CATEGORICAL_COLS = ["InternetService", "Contract", "PaymentMethod"]
NUMERIC_COLS = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]

# Bảng 5 trong báo cáo (hồi quy tuyến tính sau điều chỉnh).
LINEAR_SELECTED = [
    "MultipleLines", "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies", "InternetService_No",
    "InternetService_Fiber optic", "Contract_Two year",
]

# Chương 6.2: 7 biến dùng cho Decision Tree.
TREE_SELECTED = [
    "Contract_Month-to-month", "tenure", "Contract_Two year",
    "InternetService_Fiber optic", "MonthlyCharges", "InternetService_No",
    "PaymentMethod_Electronic check",
]

# Bảng 8 trong báo cáo: mô hình Logistic Regression sau điều chỉnh.
LOGISTIC_SELECTED = [
    "gender", "Dependents", "tenure", "PhoneService", "OnlineSecurity",
    "OnlineBackup", "DeviceProtection", "TechSupport", "PaperlessBilling",
    "InternetService_No", "InternetService_Fiber optic",
    "PaymentMethod_Bank transfer (automatic)",
    "PaymentMethod_Credit card (automatic)",
    "PaymentMethod_Mailed check", "Contract_Month-to-month", "Contract_Two year",
]

# Dữ liệu tối thiểu cho phiên bản logistic đã lựa chọn (không cần nhãn Churn).
PREDICT_REQUIRED = [
    "gender", "Dependents", "tenure", "PhoneService", "OnlineSecurity",
    "OnlineBackup", "DeviceProtection", "TechSupport", "PaperlessBilling",
    "InternetService", "PaymentMethod", "Contract",
]

# Drop 1 biến trong mỗi nhóm dummy để tránh đa cộng tuyến hoàn hảo khi OLS.
LINEAR_REFERENCE_DUMMIES = [
    "InternetService_DSL", "Contract_One year", "PaymentMethod_Electronic check",
]
