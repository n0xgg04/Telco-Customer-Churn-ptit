"""Đọc, làm sạch và mã hóa IBM Telco Customer Churn (Chương 2, 3 và 5)."""
from pathlib import Path

import numpy as np
import pandas as pd

from .schema import (
    BINARY_COLS, CATEGORICAL_COLS, NUMERIC_COLS, PREDICT_REQUIRED,
    RAW_COLUMNS,
)


def load_dataset(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Không tìm thấy {path}. Chạy: python download_data.py "
            "hoặc chép file Telco-Customer-Churn.csv vào data/raw/."
        )
    return pd.read_csv(path)


def clean_dataset(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Cách làm tương ứng báo cáo: chuyển TotalCharges sang số, bỏ giá trị thiếu.

    Không dùng Churn để sửa dữ liệu. Bỏ ID trùng để không đếm 1 khách hàng nhiều lần.
    """
    absent = set(RAW_COLUMNS).difference(raw.columns)
    if absent:
        raise ValueError(f"Thiếu các trường bắt buộc: {sorted(absent)}")
    df = raw.copy()
    before = len(df)
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace("", pd.NA)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    missing_by_field = {str(k): int(v) for k, v in df.isna().sum().items() if v > 0}
    dupe_rows = int(df.duplicated().sum())
    dupe_ids = int(df["customerID"].duplicated().sum())
    df = df.drop_duplicates(subset=["customerID"], keep="first")
    df = df.dropna(subset=RAW_COLUMNS)
    if not df["Churn"].isin(["Yes", "No"]).all():
        raise ValueError("Churn phải là Yes hoặc No.")
    if df.empty:
        raise ValueError("Không có dòng hợp lệ sau khi làm sạch.")
    report = {
        "so_dong_ban_dau": before,
        "so_dong_sau_lam_sach": len(df),
        "so_dong_bi_loai": before - len(df),
        "missing_theo_cot_ban_dau": missing_by_field,
        "so_dong_trung_hoan_toan": dupe_rows,
        "so_customerID_trung": dupe_ids,
        "ty_le_churn_sau_lam_sach": round(float(df["Churn"].eq("Yes").mean()), 4),
    }
    return df.reset_index(drop=True), report


def target_from_dataframe(df: pd.DataFrame) -> pd.Series:
    if "Churn" not in df:
        raise ValueError("Dữ liệu training phải có nhãn Churn.")
    y = df["Churn"].map({"Yes": 1, "No": 0})
    if y.isna().any():
        raise ValueError("Nhãn Churn chỉ nhận Yes/No.")
    return y.astype(int)


def encode_features(df: pd.DataFrame, required_raw: list[str] | None = None) -> pd.DataFrame:
    """Mã hóa theo Chương 5, đầu ra chỉ có đặc trưng số.

    Có thể dùng cho dữ liệu mới không có nhãn và có ít cột hơn dữ liệu huấn luyện.
    Khi dự đoán, phải kiểm tra required_raw bên ngoài để tránh mặc nhiên coi dữ
    liệu quan trọng bị khuyết là giá trị 0.
    """
    if required_raw:
        missing = [c for c in required_raw if c not in df.columns]
        if missing:
            raise ValueError(f"Thiếu cột dữ liệu dự đoán: {missing}")
        if df[required_raw].isna().any().any():
            raise ValueError("Một số ô trong cột dữ liệu dự đoán bắt buộc đang trống.")

    X = df.drop(columns=["customerID", "Churn"], errors="ignore").copy()
    for col in X.select_dtypes(include=["object", "string"]).columns:
        X[col] = X[col].astype("string").str.strip()

    X = X.replace({"No internet service": "No", "No phone service": "No"})
    # Có thể giữ đúng mã hóa báo cáo với Yes=1, No=0; gender Male=1.
    for col in BINARY_COLS:
        if col in X:
            X[col] = X[col].map({"Yes": 1, "No": 0})
            if X[col].isna().any():
                raise ValueError(f"Cột {col} có giá trị ngoài Yes/No.")
    if "gender" in X:
        X["gender"] = X["gender"].map({"Male": 1, "Female": 0})
        if X["gender"].isna().any():
            raise ValueError("gender chỉ nhận Male/Female.")
    for col in NUMERIC_COLS:
        if col in X:
            X[col] = pd.to_numeric(X[col], errors="coerce")
            if X[col].isna().any():
                raise ValueError(f"Cột {col} không hợp lệ hoặc có giá trị thiếu.")
    cats = [c for c in CATEGORICAL_COLS if c in X]
    for col in cats:
        if X[col].isna().any():
            raise ValueError(f"Cột {col} có giá trị trống.")
    X = pd.get_dummies(X, columns=cats, dtype=int)
    bad_columns = list(X.select_dtypes(exclude=[np.number, "bool"]).columns)
    if bad_columns:
        raise ValueError(f"Chưa mã hóa được cột: {bad_columns}")
    return X.astype(float)


def prepare_prediction_features(df: pd.DataFrame, trained_columns: list[str],
                                required_raw: list[str] | None = None) -> pd.DataFrame:
    """Chỉ dùng cột đầu vào mà mô hình đã huấn luyện cần đến."""
    required = required_raw or PREDICT_REQUIRED
    X = encode_features(df[[c for c in df.columns if c in required or c == "customerID"]],
                        required_raw=required)
    # Các giá trị dummy không xuất hiện trong batch mới phải là 0, không phải lỗi.
    return X.reindex(columns=trained_columns, fill_value=0.0)
