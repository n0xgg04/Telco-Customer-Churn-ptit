"""Huấn luyện lại từ dữ liệu gốc + dữ liệu mới, lưu từng lần chạy để so sánh.

Mỗi lần chạy: gộp → làm sạch → mã hóa → chia train/test → cân bằng (chỉ train)
→ chuẩn hóa → huấn luyện → đánh giá trên test. Kết quả và mô hình nằm trong
outputs/runs/<run_id>/.
"""
import json
import secrets
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE, RandomOverSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.under_sampling import RandomUnderSampler
from sklearn.linear_model import Lasso, LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, mean_absolute_error,
                             mean_squared_error, precision_score, r2_score, recall_score,
                             roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from .data import clean_dataset, encode_features, target_from_dataframe
from .schema import (BINARY_COLS, CATEGORICAL_COLS, LINEAR_REFERENCE_DUMMIES, LINEAR_SELECTED,
                     LOGISTIC_SELECTED, RAW_COLUMNS, TREE_SELECTED)

BALANCING = {
    "smote": "SMOTE",
    "oversample": "Random oversampling",
    "undersample": "Random undersampling",
    "class_weight": "Class weight (trọng số lớp)",
    "none": "Không cân bằng",
}
MODEL_NAMES = {"decision_tree": "Cây quyết định", "logistic": "Hồi quy logistic",
               "linear": "Hồi quy tuyến tính"}
CLASSIFIERS = ("decision_tree", "logistic")


def combine_sources(base: pd.DataFrame, new: pd.DataFrame | None) -> tuple[pd.DataFrame, dict]:
    """Ghép dữ liệu mới vào sau dữ liệu gốc. Trùng customerID thì giữ bản mới."""
    if new is None or new.empty:
        return base.copy(), {"base_rows": len(base), "new_rows": 0, "replaced": 0, "rows": len(base)}
    missing = sorted(set(RAW_COLUMNS) - set(new.columns))
    if missing:
        raise ValueError(f"Dữ liệu mới thiếu cột: {', '.join(missing)}")
    replaced = int(base["customerID"].astype(str).isin(set(new["customerID"].astype(str))).sum())
    combined = pd.concat([base[RAW_COLUMNS], new[RAW_COLUMNS]], ignore_index=True)
    combined["customerID"] = combined["customerID"].astype(str)
    combined = combined.drop_duplicates("customerID", keep="last").reset_index(drop=True)
    return combined, {"base_rows": len(base), "new_rows": len(new), "replaced": replaced,
                      "rows": len(combined)}


def required_raw_columns(features: list[str]) -> list[str]:
    """Cột CSV gốc mà một tập đặc trưng đã mã hóa cần đến."""
    cols = []
    for f in features:
        raw = next((c for c in CATEGORICAL_COLS if f.startswith(c + "_")), f)
        if raw not in cols:
            cols.append(raw)
    return cols


def feature_sets(encoded: pd.DataFrame) -> dict:
    full_cls = list(encoded.drop(columns=LINEAR_REFERENCE_DUMMIES, errors="ignore").columns)
    full_lin = [c for c in full_cls if c not in ("MonthlyCharges", "TotalCharges")]
    return {
        "decision_tree": {"report": TREE_SELECTED, "all": full_cls},
        "logistic": {"report": LOGISTIC_SELECTED, "all": full_cls},
        "linear": {"report": LINEAR_SELECTED, "all": full_lin},
    }


def _sampler(method: str, seed: int):
    return {"smote": lambda: SMOTE(random_state=seed, k_neighbors=5),
            "oversample": lambda: RandomOverSampler(random_state=seed),
            "undersample": lambda: RandomUnderSampler(random_state=seed)}.get(method, lambda: None)()


def _counts(y) -> dict:
    y = pd.Series(y)
    return {"stay": int((y == 0).sum()), "churn": int((y == 1).sum())}


def _classifier(name: str, params: dict, seed: int):
    weight = "balanced" if params["balancing"] == "class_weight" else None
    if name == "decision_tree":
        return DecisionTreeClassifier(criterion=params["criterion"], max_depth=params["max_depth"],
                                      min_samples_leaf=params["min_samples_leaf"],
                                      class_weight=weight, random_state=seed)
    penalty = params["penalty"]
    return LogisticRegression(solver=params["solver"], C=params["C"], max_iter=3000,
                              class_weight=weight, random_state=seed,
                              **({"l1_ratio": 1.0} if penalty == "l1" else {}))


def _classification_scores(model, X_test, y_test) -> dict:
    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[0, 1]).ravel()
    return {"accuracy": float(accuracy_score(y_test, pred)),
            "precision_churn_1": float(precision_score(y_test, pred, zero_division=0)),
            "recall_churn_1": float(recall_score(y_test, pred, zero_division=0)),
            "f1_churn_1": float(f1_score(y_test, pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_test, proba)),
            "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}}


def train_classifier(name: str, X: pd.DataFrame, y: pd.Series, params: dict, seed: int,
                     test_size: float) -> tuple[dict, object]:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y)
    steps = []
    sampler = _sampler(params["balancing"], seed)
    after = _counts(y_train)
    if sampler is not None:
        steps.append(("balance", sampler))
        _, y_res = sampler.fit_resample(X_train, y_train)  # chỉ để báo cáo số mẫu
        after = _counts(y_res)
    if name == "logistic":
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", _classifier(name, params, seed)))
    model = ImbPipeline(steps)
    # Sampler nằm trong pipeline nên được fit lại trong từng fold, không rò rỉ sang fold kiểm tra.
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    cv_recall = cross_val_score(model, X_train, y_train, cv=cv, scoring="recall")
    model.fit(X_train, y_train)
    scores = _classification_scores(model, X_test, y_test)
    scores["cv_recall_each_fold"] = [float(v) for v in cv_recall]
    scores["cv_recall_mean"] = float(cv_recall.mean())
    return {"metrics": scores,
            "split": {"train": len(X_train), "test": len(X_test),
                      "train_counts": _counts(y_train), "test_counts": _counts(y_test)},
            "balance": {"method": params["balancing"], "before": _counts(y_train), "after": after},
            "scaled": name == "logistic"}, model


def train_linear(X: pd.DataFrame, y: pd.Series, params: dict, seed: int,
                 test_size: float) -> tuple[dict, object]:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=seed)
    algo = params["algorithm"]
    if algo == "ols":
        model = ImbPipeline([("model", LinearRegression())])
    else:
        est = Ridge(alpha=params["alpha"]) if algo == "ridge" else Lasso(alpha=params["alpha"], max_iter=10000)
        model = ImbPipeline([("scaler", StandardScaler()), ("model", est)])
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    return {"metrics": {"r2_train": float(r2_score(y_train, model.predict(X_train))),
                        "r2_test": float(r2_score(y_test, pred)),
                        "mae_test": float(mean_absolute_error(y_test, pred)),
                        "rmse_test": float(np.sqrt(mean_squared_error(y_test, pred)))},
            "split": {"train": len(X_train), "test": len(X_test)},
            "scaled": algo != "ols"}, model


def preprocessing_report(raw: pd.DataFrame, clean: pd.DataFrame, quality: dict,
                         encoded: pd.DataFrame) -> dict:
    blank_total = int(raw["TotalCharges"].astype(str).str.strip().eq("").sum())
    service_cols = [c for c in BINARY_COLS if c in raw]
    replaced = int(raw[service_cols].isin(["No internet service", "No phone service"]).sum().sum())
    dummies = {c: sorted(clean[c].unique().tolist()) for c in CATEGORICAL_COLS}
    numeric = ["tenure", "MonthlyCharges", "TotalCharges"]
    return {
        "clean": {**quality, "blank_total_charges": blank_total},
        "encode": {"raw_columns": len(RAW_COLUMNS) - 2, "encoded_columns": encoded.shape[1],
                   "service_values_to_no": replaced, "binary_columns": len(BINARY_COLS) + 1,
                   "dummies": dummies},
        "numeric": {c: {"mean": float(clean[c].mean()), "std": float(clean[c].std())} for c in numeric},
        "churn_rate": float(clean["Churn"].eq("Yes").mean()),
    }


def run_retrain(base: pd.DataFrame, new: pd.DataFrame | None, config: dict,
                runs_dir: Path, source: dict) -> dict:
    """config = {"seed": int|None, "test_size": float, "models": {name: params}}"""
    seed = config.get("seed")
    seed = secrets.randbelow(100_000) if seed is None else int(seed)
    combined, merge = combine_sources(base, new)
    clean, quality = clean_dataset(combined)
    if clean["Churn"].nunique() < 2:
        raise ValueError("Dữ liệu sau làm sạch chỉ có một lớp Churn, không huấn luyện được.")
    encoded = encode_features(clean)
    y_churn = target_from_dataframe(clean)
    sets = feature_sets(encoded)

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-s{seed}-{secrets.token_hex(2)}"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    if new is not None and not new.empty:
        new.to_csv(run_dir / "new_data.csv", index=False, encoding="utf-8-sig")

    results = {}
    for name, params in config["models"].items():
        features = [f for f in sets[name][params["features"]] if f in encoded.columns]
        X = encoded[features]
        if name == "linear":
            info, model = train_linear(X, clean["MonthlyCharges"].astype(float), params, seed, config["test_size"])
        else:
            info, model = train_classifier(name, X, y_churn, params, seed, config["test_size"])
        info.update(params=params, n_features=len(features))
        joblib.dump({"model": model, "feature_names": features, "threshold": 0.5,
                     "required_raw": required_raw_columns(features), "kind": name,
                     "run_id": run_id},
                    run_dir / f"{name}.joblib")
        results[name] = info

    record = {"run_id": run_id, "created": datetime.now().isoformat(timespec="seconds"),
              "seed": seed, "test_size": config["test_size"], "source": source, "merge": merge,
              "preprocessing": preprocessing_report(combined, clean, quality, encoded),
              "models": results}
    (run_dir / "run.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def load_runs(runs_dir: Path) -> list[dict]:
    runs = []
    for path in sorted(runs_dir.glob("*/run.json"), reverse=True):
        try:
            runs.append(json.loads(path.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            continue  # lần chạy hỏng hoặc đang ghi dở
    return runs


def comparison_table(runs: list[dict]) -> pd.DataFrame:
    rows = []
    for run in runs:
        for name, info in run["models"].items():
            rows.append({"run_id": run["run_id"], "created": run["created"], "seed": run["seed"],
                         "data": run["source"]["label"], "rows": run["merge"]["rows"],
                         "model": name, **{k: v for k, v in info["metrics"].items()
                                           if isinstance(v, float)}})
    return pd.DataFrame(rows)


def set_active_model(models_dir: Path, run_id: str, name: str) -> None:
    if name not in CLASSIFIERS:
        raise ValueError("Chỉ mô hình phân loại Churn mới dùng được cho dự đoán.")
    models_dir.mkdir(parents=True, exist_ok=True)
    (models_dir / "active.json").write_text(json.dumps({"run_id": run_id, "model": name}), encoding="utf-8")


def active_model_path(outputs: Path) -> tuple[Path, dict | None]:
    """Mô hình đang dùng để dự đoán; mặc định là Logistic của pipeline gốc."""
    pointer = outputs / "models" / "active.json"
    if pointer.is_file():
        try:
            active = json.loads(pointer.read_text(encoding="utf-8"))
            path = outputs / "runs" / active["run_id"] / f"{active['model']}.joblib"
            if path.is_file():
                return path, active
        except (ValueError, KeyError, OSError):
            pass
    return outputs / "models" / "logistic_selected.joblib", None


BALANCING_HOW = {
    "smote": "Tạo mẫu rời bỏ mới bằng nội suy giữa một khách rời bỏ và một trong 5 láng giềng gần nhất của nó.",
    "oversample": "Lặp lại ngẫu nhiên các khách rời bỏ có sẵn cho tới khi hai lớp bằng nhau.",
    "undersample": "Bỏ ngẫu nhiên bớt khách ở lại cho tới khi hai lớp bằng nhau.",
    "class_weight": "Giữ nguyên dữ liệu. Khi học, lỗi trên khách rời bỏ bị phạt nặng hơn theo tỷ lệ hai lớp.",
    "none": "Giữ nguyên dữ liệu và tỷ lệ lớp.",
}
NUMERIC_SHOWN = ["tenure", "MonthlyCharges", "TotalCharges"]


def removal_reasons(combined: pd.DataFrame, clean: pd.DataFrame) -> pd.Series:
    """Lý do từng dòng bị loại khi làm sạch; dòng hợp lệ để chuỗi rỗng."""
    reasons = pd.Series("", index=combined.index, dtype=object)
    ids = combined["customerID"].astype(str)
    dupes = ids.duplicated(keep="first")
    gone = ~ids.isin(set(clean["customerID"].astype(str))) | dupes
    blank = combined[RAW_COLUMNS].apply(lambda col: col.isna() | col.astype(str).str.strip().eq(""))
    for idx in combined.index[gone]:
        if dupes[idx]:
            reasons[idx] = "Trùng customerID"
        else:
            cols = [c for c in RAW_COLUMNS if blank.at[idx, c]]
            reasons[idx] = "Thiếu " + ", ".join(cols) if cols else "Giá trị không hợp lệ"
    return reasons


def preprocess_preview(base: pd.DataFrame, new: pd.DataFrame | None, test_size: float,
                       seed: int, method: str) -> dict:
    """Chạy từng bước tiền xử lý và giữ lại dữ liệu trung gian để hiển thị."""
    combined, merge = combine_sources(base, new)
    blank_total = combined["TotalCharges"].astype(str).str.strip().eq("")
    clean, quality = clean_dataset(combined)
    kept = set(clean["customerID"].astype(str))
    removed = combined[~combined["customerID"].astype(str).isin(kept)]
    records = combined[RAW_COLUMNS].copy()
    records.insert(0, "Lý do loại bỏ", removal_reasons(combined, clean))
    encoded = encode_features(clean)
    y = target_from_dataframe(clean)
    # Ví dụ mã hóa: 2 khách đầu + 1 khách không có Internet (nếu có).
    sample_idx = list(clean.index[:2])
    no_net = clean.index[clean["InternetService"].eq("No")]
    if len(no_net):
        sample_idx.append(no_net[0])
    X_train, X_test, y_train, y_test = train_test_split(
        encoded, y, test_size=test_size, random_state=seed, stratify=y)
    sampler = _sampler(method, seed)
    X_bal, y_bal = sampler.fit_resample(X_train, y_train) if sampler is not None else (X_train, y_train)
    synthetic = None
    if method == "smote":
        # imblearn nối mẫu sinh thêm vào cuối, sau các mẫu train gốc.
        synthetic = X_bal.iloc[len(X_train):][NUMERIC_SHOWN[:2]]
    scaler = StandardScaler().fit(X_train[NUMERIC_SHOWN])
    scaled = pd.DataFrame(scaler.transform(X_train[NUMERIC_SHOWN]), columns=NUMERIC_SHOWN)
    stats = pd.DataFrame({
        "before_mean": X_train[NUMERIC_SHOWN].mean(), "before_std": X_train[NUMERIC_SHOWN].std(),
        "after_mean": scaled.mean().round(6).values, "after_std": scaled.std(ddof=0).values,
    })
    return {
        "merge": merge, "quality": quality, "blank_total": int(blank_total.sum()),
        "removed": removed, "records": records, "clean_rows": len(clean), "churn_rate": float(y.mean()),
        "raw_sample": clean.loc[sample_idx], "encoded_sample": encoded.loc[sample_idx],
        "encoded_shape": encoded.shape,
        "split": {"train": _counts(y_train), "test": _counts(y_test)},
        "balance": {"before": _counts(y_train), "after": _counts(y_bal)},
        "train_churn": X_train.loc[y_train == 1, NUMERIC_SHOWN[:2]], "synthetic": synthetic,
        "scale_stats": stats,
    }
