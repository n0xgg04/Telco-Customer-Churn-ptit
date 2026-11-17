"""Đánh giá phân loại trên test holdout (không chạm vào test khi fit)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    ConfusionMatrixDisplay, accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report,
)


def evaluate_classifier(model, X_test, y_test, tag: str, fig_dir: Path,
                        table_dir: Path) -> dict:
    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    results = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision_churn_1": float(precision_score(y_test, pred, zero_division=0)),
        "recall_churn_1": float(recall_score(y_test, pred, zero_division=0)),
        "f1_churn_1": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, proba)),
    }
    fig, ax = plt.subplots(figsize=(5, 4))
    ConfusionMatrixDisplay.from_predictions(
        y_test, pred, labels=[0, 1], display_labels=["Stay", "Churn"], ax=ax,
        cmap="Blues", colorbar=False,
    )
    ax.set_title(f"Confusion matrix: {tag}")
    fig.savefig(fig_dir / f"confusion_{tag}.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    (table_dir / f"classification_report_{tag}.txt").write_text(
        classification_report(y_test, pred, zero_division=0), encoding="utf-8"
    )
    (table_dir / f"metrics_{tag}.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    return results
