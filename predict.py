"""python predict.py --input data/new_customers_example.csv"""
import argparse
from pathlib import Path

import joblib
import pandas as pd

from src.data import prepare_prediction_features
from src.retrain import active_model_path

ROOT = Path(__file__).resolve().parent


def predict_dataframe(df: pd.DataFrame,
                      model_path: Path | None = None) -> pd.DataFrame:
    model_path = model_path or active_model_path(ROOT / "outputs")[0]
    if not model_path.is_file():
        raise FileNotFoundError("Chưa có model. Chạy python run_pipeline.py trước.")
    # Chỉ load model do chính bạn tạo; không load joblib từ nguồn không đáng tin.
    saved = joblib.load(model_path)
    X = prepare_prediction_features(df, saved["feature_names"], saved.get("required_raw"))
    scores = saved["model"].predict_proba(X)[:, 1]
    result = df.copy()
    result["churn_risk_score"] = scores.round(4)
    result["predicted_churn"] = ["Yes" if v >= saved["threshold"] else "No"
                                 for v in scores]
    result["risk_group"] = pd.cut(
        scores, bins=[-0.001, 0.3, 0.6, 1.0],
        labels=["Low", "Medium", "High"], include_lowest=True,
    ).astype(str)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Đường dẫn CSV đầu vào")
    parser.add_argument("--output", default=str(ROOT / "outputs/predictions.csv"))
    args = parser.parse_args()
    df = pd.read_csv(args.input)
    result = predict_dataframe(df)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"Đã dự đoán {len(result)} khách hàng: {output}")
    print(result[["churn_risk_score", "predicted_churn", "risk_group"]].head(10))


if __name__ == "__main__":
    main()
