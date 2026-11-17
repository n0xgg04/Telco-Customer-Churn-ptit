"""Chương 4: EDA (đơn biến, đa biến, Churn theo dịch vụ và giao dịch)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import encode_features, target_from_dataframe


NUMS = ["tenure", "MonthlyCharges", "TotalCharges"]
CATS = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "PhoneService",
    "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod",
]


def _save(fig, path: Path) -> None:
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def run_eda(df: pd.DataFrame, figure_dir: Path, table_dir: Path) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    df[NUMS].describe().to_csv(table_dir / "eda_numeric_summary.csv", encoding="utf-8-sig")

    # Phân phối Churn: Biểu đồ 5.
    counts = df["Churn"].value_counts().reindex(["No", "Yes"], fill_value=0)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(counts.index, counts.values)
    ax.set(title="Churn distribution", ylabel="Customers")
    for i, n in enumerate(counts):
        ax.text(i, n + 0.01 * max(counts), f"{n:,}", ha="center")
    _save(fig, figure_dir / "01_churn_distribution.png")

    # Histogram 3 biến liên tục: Biểu đồ 6.
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, col in zip(axes, NUMS):
        ax.hist(df[col], bins=25, edgecolor="white")
        ax.set(title=col, xlabel=col, ylabel="Count")
    fig.tight_layout()
    _save(fig, figure_dir / "02_numeric_histograms.png")

    # Boxplot theo Churn: Biểu đồ 8.
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, col in zip(axes, NUMS):
        ax.boxplot([df.loc[df.Churn == label, col] for label in ["No", "Yes"]],
                   tick_labels=["No", "Yes"])
        ax.set(title=f"{col} by Churn", xlabel="Churn", ylabel=col)
    fig.tight_layout()
    _save(fig, figure_dir / "03_boxplots_by_churn.png")

    # Ma trận Pearson: Biểu đồ 9.
    corr = df[NUMS].corr()
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(3), corr.columns, rotation=35, ha="right")
    ax.set_yticks(range(3), corr.index)
    for (i, j), v in np.ndenumerate(corr.values):
        ax.text(j, i, f"{v:.2f}", ha="center", va="center")
    fig.colorbar(im, ax=ax)
    ax.set_title("Numeric correlation")
    _save(fig, figure_dir / "04_numeric_correlation.png")
    corr.to_csv(table_dir / "eda_correlation.csv", encoding="utf-8-sig")

    # Biểu đồ 10-12: Tỷ lệ churn theo nhóm, không chỉ đếm tần số thô.
    churn_rates = []
    for feature in CATS:
        grouped = (df.groupby(feature, dropna=False, observed=True)["Churn"]
                   .agg(customers="count", churn_rate=lambda s: s.eq("Yes").mean())
                   .reset_index())
        grouped.insert(0, "feature", feature)
        grouped = grouped.rename(columns={feature: "value"})
        churn_rates.append(grouped)
    all_rates = pd.concat(churn_rates, ignore_index=True)
    all_rates.to_csv(table_dir / "eda_churn_by_category.csv", index=False,
                     encoding="utf-8-sig")
    for feature in ["Contract", "InternetService", "PaymentMethod", "TechSupport"]:
        sub = all_rates.loc[all_rates.feature == feature]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(sub.value.astype(str), sub.churn_rate * 100)
        ax.set(title=f"Churn rate by {feature}", ylabel="Churn (%)")
        ax.set_ylim(0, max(10, sub.churn_rate.max() * 110))
        ax.tick_params(axis="x", rotation=15)
        _save(fig, figure_dir / f"05_churn_by_{feature}.png")

    # Chương 4.2.3.2: tương quan Spearman với nhãn Churn.
    encoded = encode_features(df)
    encoded["Churn"] = target_from_dataframe(df)
    values = encoded.corr(method="spearman")["Churn"].drop("Churn").sort_values()
    values.to_csv(table_dir / "eda_spearman.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(10, 8))
    values.plot.barh(ax=ax, fontsize=8)
    ax.set(title="Spearman correlation with Churn", xlabel="Correlation")
    _save(fig, figure_dir / "06_spearman_churn.png")

    # Outliers là thống kê, không tự động xóa như báo cáo.
    q1, q3 = df[NUMS].quantile(0.25), df[NUMS].quantile(0.75)
    iqr = q3 - q1
    outliers = ((df[NUMS] < q1 - 1.5 * iqr) |
                (df[NUMS] > q3 + 1.5 * iqr)).sum().rename("outlier_count")
    outliers.to_csv(table_dir / "eda_outliers.csv", encoding="utf-8-sig")
