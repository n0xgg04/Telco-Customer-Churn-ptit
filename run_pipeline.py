"""Chạy toàn bộ 7 chương của bài thực hành: python run_pipeline.py"""
import argparse
import json
from pathlib import Path

from src.data import clean_dataset, load_dataset
from src.eda import run_eda
from src.feature_tests import run_feature_tests
from src.models import (
    run_decision_tree, run_linear_regression, run_logistic_regression,
)

ROOT = Path(__file__).resolve().parent


def main(input_csv: Path, output_dir: Path) -> dict:
    figure_dir = output_dir / "figures"
    table_dir = output_dir / "tables"
    model_dir = output_dir / "models"
    for p in [figure_dir, table_dir, model_dir]:
        p.mkdir(parents=True, exist_ok=True)

    raw = load_dataset(input_csv)
    clean, quality = clean_dataset(raw)
    processed_dir = ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    clean.to_csv(processed_dir / "telco_clean.csv", index=False,
                 encoding="utf-8-sig")
    print(f"[1/4] Data: {quality['so_dong_ban_dau']} -> "
          f"{quality['so_dong_sau_lam_sach']} khách hàng")
    run_eda(clean, figure_dir, table_dir)
    run_feature_tests(clean, table_dir)
    print("[2/4] EDA hoàn tất")
    linear = run_linear_regression(clean, table_dir)
    tree = run_decision_tree(clean, figure_dir, table_dir)
    print("[3/4] OLS và Decision Tree hoàn tất")
    logistic = run_logistic_regression(clean, figure_dir, table_dir, model_dir)
    print("[4/4] Logistic Regression hoàn tất")

    report = {"data_quality": quality, "linear_regression": linear,
              "decision_tree": tree, "logistic_regression": logistic}
    (output_dir / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\n=== KẾT QUẢ MÔ HÌNH LOGISTIC ĐIỀU CHỈNH ===")
    for key, val in logistic["selected"].items():
        if isinstance(val, (float, int)):
            print(f"  {key}: {val:.4f}")
    print(f"\nXem artifacts: {output_dir}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Customer Churn Data Mining")
    parser.add_argument("--data", default=str(ROOT / "data/raw/Telco-Customer-Churn.csv"))
    parser.add_argument("--output", default=str(ROOT / "outputs"))
    args = parser.parse_args()
    main(Path(args.data), Path(args.output))
