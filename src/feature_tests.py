"""Chương 4.2.3: ANOVA, Chi-square, Mutual Information với Churn."""
import pandas as pd
from sklearn.feature_selection import chi2, f_classif, mutual_info_classif

from .data import encode_features, target_from_dataframe
from .schema import BINARY_COLS


def run_feature_tests(df: pd.DataFrame, table_dir) -> None:
    X = encode_features(df)
    y = target_from_dataframe(df)
    continuous = [c for c in ["tenure", "MonthlyCharges", "TotalCharges"] if c in X]
    binary = [c for c in X if c not in continuous]

    # ANOVA áp dụng cho các biến liên tục, Chi2 cho các biến 0/1 không âm.
    if continuous:
        f_scores, p_values = f_classif(X[continuous], y)
        pd.DataFrame({"feature": continuous, "anova_f": f_scores,
                      "p_value": p_values}).sort_values(
            "anova_f", ascending=False
        ).to_csv(table_dir / "feature_anova.csv", index=False,
                  encoding="utf-8-sig")
    if binary:
        chi_scores, p_values = chi2(X[binary], y)
        pd.DataFrame({"feature": binary, "chi2": chi_scores,
                      "p_value": p_values}).sort_values(
            "chi2", ascending=False
        ).to_csv(table_dir / "feature_chi_square.csv", index=False,
                  encoding="utf-8-sig")

    # MI cần thông tin biến liên tục hay rời rạc.
    is_discrete = [col not in continuous for col in X.columns]
    mutual = mutual_info_classif(X, y, discrete_features=is_discrete,
                                random_state=42)
    pd.DataFrame({"feature": X.columns, "mutual_information": mutual}).sort_values(
        "mutual_information", ascending=False
    ).to_csv(table_dir / "feature_mutual_information.csv", index=False,
              encoding="utf-8-sig")
