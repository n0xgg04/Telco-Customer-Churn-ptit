"""Chương 6: OLS, Decision Tree, Logistic Regression + SMOTE.

Mô hình được train với split 80/20 và đánh giá trên test chưa từng được nhìn thấy.
Với hồi quy logistic, SMOTE nằm TRONG pipeline CV để tránh data leakage.
"""
import json
import warnings
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree
from statsmodels.stats.outliers_influence import variance_inflation_factor

from .data import encode_features, target_from_dataframe
from .evaluation import evaluate_classifier
from .schema import (
    LINEAR_SELECTED, LINEAR_REFERENCE_DUMMIES, TREE_SELECTED,
    LOGISTIC_SELECTED,
)


def _as_matrix(X: pd.DataFrame) -> pd.DataFrame:
    return sm.add_constant(X.astype(float), has_constant="add")


def _ols_fit_report(X_train: pd.DataFrame, y_train: pd.Series,
                    X_test: pd.DataFrame, y_test: pd.Series,
                    tag: str, table_dir: Path) -> dict:
    fitted = sm.OLS(y_train.astype(float), _as_matrix(X_train)).fit()
    prediction = fitted.predict(_as_matrix(X_test))
    report = {
        "r2_train": float(fitted.rsquared),
        "r2_test": float(r2_score(y_test, prediction)),
        "mae_test": float(mean_absolute_error(y_test, prediction)),
        "rmse_test": float(np.sqrt(mean_squared_error(y_test, prediction))),
    }
    (table_dir / f"ols_summary_{tag}.txt").write_text(
        fitted.summary().as_text(), encoding="utf-8"
    )
    pd.DataFrame({
        "feature": fitted.params.index,
        "coefficient": fitted.params.values,
        "p_value": fitted.pvalues.values,
    }).to_csv(table_dir / f"ols_coefficients_{tag}.csv", index=False,
              encoding="utf-8-sig")
    return report


def run_linear_regression(df: pd.DataFrame, table_dir: Path) -> dict:
    """OLS giải thích MonthlyCharges, không sử dụng Churn/TotalCharges/ID.

    Loại TotalCharges khỏi đầu vào vì nó chứa thông tin tích lũy từ phí hàng tháng.
    """
    encoded = encode_features(df)
    all_features = encoded.drop(
        columns=["MonthlyCharges", "TotalCharges"] + LINEAR_REFERENCE_DUMMIES,
        errors="ignore",
    )
    missing = sorted(set(LINEAR_SELECTED) - set(encoded.columns))
    if missing:
        raise ValueError(f"Không đủ cột OLS theo báo cáo: {missing}")
    train_idx, test_idx = train_test_split(
        np.arange(len(df)), test_size=0.2, random_state=42
    )
    y = df["MonthlyCharges"].astype(float)
    results = {}
    for tag, X in [("full", all_features), ("selected", encoded[LINEAR_SELECTED])]:
        results[tag] = _ols_fit_report(
            X.iloc[train_idx], y.iloc[train_idx],
            X.iloc[test_idx], y.iloc[test_idx], tag, table_dir,
        )

    # VIF cho mô hình OLS điều chỉnh, để đối chiếu Bảng 5.
    X_vif = _as_matrix(encoded[LINEAR_SELECTED])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        vif_values = [variance_inflation_factor(X_vif.to_numpy(), i)
                      for i in range(X_vif.shape[1])]
    pd.DataFrame({"feature": X_vif.columns, "vif": vif_values}).to_csv(
        table_dir / "ols_selected_vif.csv", index=False, encoding="utf-8-sig"
    )
    return results


def _split_for_churn(X: pd.DataFrame, y: pd.Series):
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


def run_decision_tree(df: pd.DataFrame, figure_dir: Path, table_dir: Path) -> dict:
    encoded = encode_features(df)
    missing = sorted(set(TREE_SELECTED) - set(encoded.columns))
    if missing:
        raise ValueError(f"Không đủ cột Decision Tree: {missing}")
    X = encoded[TREE_SELECTED]
    y = target_from_dataframe(df)
    X_train, X_test, y_train, y_test = _split_for_churn(X, y)
    tree = DecisionTreeClassifier(max_depth=4, criterion="gini", random_state=42)
    tree.fit(X_train, y_train)
    metrics = evaluate_classifier(tree, X_test, y_test, "decision_tree",
                                  figure_dir, table_dir)
    fig, ax = plt.subplots(figsize=(26, 12))
    plot_tree(tree, feature_names=TREE_SELECTED, class_names=["Stay", "Churn"],
              filled=True, rounded=True, fontsize=8, ax=ax)
    ax.set_title("Decision Tree - max_depth=4")
    fig.savefig(figure_dir / "decision_tree.png", bbox_inches="tight", dpi=140)
    plt.close(fig)
    (table_dir / "decision_tree_rules.txt").write_text(
        export_text(tree, feature_names=TREE_SELECTED), encoding="utf-8"
    )
    pd.DataFrame({"feature": TREE_SELECTED,
                  "importance": tree.feature_importances_}).sort_values(
        "importance", ascending=False
    ).to_csv(table_dir / "tree_feature_importance.csv", index=False,
              encoding="utf-8-sig")
    # Mô tả lá theo test để tránh đánh đồng tỷ lệ in-sample với chất lượng dự đoán.
    grouping = pd.DataFrame({
        "leaf_id": tree.apply(X_test), "actual_churn": y_test.to_numpy(),
        "risk_score": tree.predict_proba(X_test)[:, 1],
    })
    groups = grouping.groupby("leaf_id").agg(
        customers=("actual_churn", "size"),
        actual_churn_rate=("actual_churn", "mean"),
        mean_model_score=("risk_score", "mean"),
    ).sort_values("actual_churn_rate", ascending=False)
    groups.to_csv(table_dir / "tree_risk_groups_test.csv", encoding="utf-8-sig")
    return metrics


def _logistic_pipeline() -> ImbPipeline:
    return ImbPipeline([
        ("smote", SMOTE(random_state=42, k_neighbors=5)),
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=2000, random_state=42)),
    ])


def _statsmodels_logit_summary(X_train: pd.DataFrame, y_train: pd.Series,
                                table_dir: Path) -> dict:
    """Ước lượng p-value trên training GỐC (không SMOTE).

    Các quan sát SMOTE là nội suy nên không nên coi là quan sát độc lập khi
    làm thống kê suy diễn. Model dự đoán sklearn vẫn áp dụng SMOTE như báo cáo.
    """
    scaler = StandardScaler()
    scaled = pd.DataFrame(scaler.fit_transform(X_train),
                          columns=X_train.columns, index=X_train.index)
    design = _as_matrix(scaled)
    result = {}
    try:
        fitted = sm.Logit(y_train.astype(float), design).fit(disp=0, maxiter=300)
        pd.DataFrame({
            "feature": fitted.params.index,
            "coefficient_standardized": fitted.params.values,
            "p_value": fitted.pvalues.values,
            "odds_ratio_per_scaled_unit": np.exp(fitted.params.values),
        }).to_csv(table_dir / "logit_selected_statsmodels_coefficients.csv",
                  index=False, encoding="utf-8-sig")
        result["mcfadden_pseudo_r2_train"] = float(fitted.prsquared)
        (table_dir / "logit_selected_statsmodels_summary.txt").write_text(
            fitted.summary().as_text(), encoding="utf-8"
        )
    except (ValueError, np.linalg.LinAlgError) as exc:
        # Dữ liệu nhỏ / hoàn toàn tách biệt có thể làm Logit thất bại.
        (table_dir / "logit_statsmodels_warning.txt").write_text(
            f"Không ước lượng được Logit suy diễn: {exc}", encoding="utf-8"
        )
        result["mcfadden_pseudo_r2_train"] = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        vif = [variance_inflation_factor(design.to_numpy(), i)
               for i in range(design.shape[1])]
    pd.DataFrame({"feature": design.columns, "vif": vif}).to_csv(
        table_dir / "logit_selected_vif.csv", index=False, encoding="utf-8-sig"
    )
    return result


def run_logistic_regression(df: pd.DataFrame, figure_dir: Path,
                            table_dir: Path, model_dir: Path) -> dict:
    encoded = encode_features(df)
    y = target_from_dataframe(df)
    missing = sorted(set(LOGISTIC_SELECTED) - set(encoded.columns))
    if missing:
        raise ValueError(f"Không đủ cột Logistic Regression: {missing}")
    # Giữ 'full' nhưng bỏ một dummy trong mỗi nhóm; full logistic với penalty L2.
    full = encoded.drop(columns=LINEAR_REFERENCE_DUMMIES, errors="ignore")
    selected = encoded[LOGISTIC_SELECTED]
    results = {}
    for tag, X in [("full", full), ("selected", selected)]:
        X_train, X_test, y_train, y_test = _split_for_churn(X, y)
        pipeline = _logistic_pipeline()
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        # Toàn bộ pipeline (kể cả SMOTE) được fit lại bên trong mỗi fold.
        cv_recall = cross_val_score(pipeline, X_train, y_train, cv=cv,
                                   scoring="recall", n_jobs=1)
        cv_accuracy = cross_val_score(pipeline, X_train, y_train, cv=cv,
                                     scoring="accuracy", n_jobs=1)
        pipeline.fit(X_train, y_train)
        scores = evaluate_classifier(pipeline, X_test, y_test,
                                     f"logistic_{tag}", figure_dir, table_dir)
        scores["cv_recall_mean"] = float(cv_recall.mean())
        scores["cv_accuracy_mean"] = float(cv_accuracy.mean())
        scores["cv_recall_each_fold"] = [float(v) for v in cv_recall]
        results[tag] = scores

        coeff = pipeline.named_steps["classifier"].coef_[0]
        pd.DataFrame({"feature": X.columns,
                      "coefficient_scaled": coeff}).sort_values(
            "coefficient_scaled"
        ).to_csv(table_dir / f"logistic_{tag}_coefficients.csv",
                  index=False, encoding="utf-8-sig")
        if tag == "selected":
            model_dir.mkdir(parents=True, exist_ok=True)
            joblib.dump({
                "model": pipeline,
                "feature_names": list(X.columns),
                "threshold": 0.5,
                "note": "Model risk score; probabilities are not calibrated after SMOTE.",
            }, model_dir / "logistic_selected.joblib")
            results[tag].update(_statsmodels_logit_summary(X_train, y_train,
                                                           table_dir))
    return results
