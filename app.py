"""Dashboard demo cho báo cáo Telco Churn: .venv/bin/python -m streamlit run app.py"""
import json
import os
import re
from html import escape
from pathlib import Path

import altair as alt
import joblib
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from predict import predict_dataframe
from src.retrain import (
    BALANCING, BALANCING_HOW, CLASSIFIERS, MODEL_NAMES, active_model_path, combine_sources,
    comparison_table, load_runs, preprocess_preview, run_retrain, set_active_model,
)
from src.schema import PREDICT_REQUIRED, RAW_COLUMNS
from src.dashboard import (
    FIELD_LABELS, METRIC_HELP, METRIC_LABELS, RISK_LABELS,
    confusion_from_report, feature_label, group_summary, prediction_display,
    validate_prediction_data, value_label,
)

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
GUIDE = ROOT / "HUONG_DAN_GIAO_DIEN.md"
RUNS = Path(os.environ.get("TELCO_RUNS_DIR", OUTPUT / "runs"))
RAW_DATA = ROOT / "data" / "raw" / "Telco-Customer-Churn.csv"
# Bảng màu chuẩn (Tableau 10): xanh = ở lại, cam = rời bỏ.
RETAIN, CHURN, GREEN, RED, TEAL, GOLD = "#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#eeca3b"
TEXT, MUTED, LINE = "#1a1a1a", "#555b65", "#e3e5e9"
SANS = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
CONTRACT_COLORS = {"Month-to-month": CHURN, "One year": RETAIN, "Two year": GREEN}
MODEL_COLORS = {"decision_tree": GREEN, "logistic": RETAIN, "linear": GOLD}
NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges"]
EVAL_MODELS = {
    "Hồi quy logistic (sau điều chỉnh)": ("logistic_regression", "selected", "logistic_selected"),
    "Hồi quy logistic (ban đầu)": ("logistic_regression", "full", "logistic_full"),
    "Cây quyết định": ("decision_tree", None, "decision_tree"),
}
CLS_METRICS = {"recall_churn_1": "Recall", "precision_churn_1": "Precision", "f1_churn_1": "F1-score",
               "roc_auc": "ROC AUC", "accuracy": "Accuracy"}
LIN_METRICS = {"r2_test": "R-squared (kiểm tra)", "rmse_test": "RMSE (kiểm tra)", "mae_test": "MAE (kiểm tra)"}
PAGES = ["Mô tả dữ liệu", "Thống kê mô tả", "Kỹ thuật khai phá",
         "1. Dữ liệu", "2. Tiền xử lý", "3. Huấn luyện", "4. So sánh", "5. Dự đoán",
         "Hướng dẫn sử dụng"]

st.set_page_config(page_title="Telco Churn · PTIT", page_icon="📊", layout="wide")
alt.data_transformers.disable_max_rows()
st.markdown(f"<style>{(ROOT / 'assets' / 'dashboard.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
_numbers = {"Biểu đồ": 0, "Bảng": 0}  # đánh số lại mỗi lần trang chạy


@st.cache_data(show_spinner=False)
def load_csv(path: str, stamp: int) -> pd.DataFrame:
    return pd.read_csv(path)


def table(name: str) -> pd.DataFrame:
    path = OUTPUT / "tables" / name
    if not path.is_file():
        return pd.DataFrame()
    return load_csv(str(path), path.stat().st_mtime_ns).copy()


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")


def required_columns() -> list[str]:
    path, _ = active_model_path(OUTPUT)
    try:
        return joblib.load(path).get("required_raw") or PREDICT_REQUIRED
    except (OSError, ValueError):
        return PREDICT_REQUIRED


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def page_header(title: str, kicker: str = "") -> None:
    html(f'<div class="top"><div class="kicker">{escape(kicker)}</div><h1>{escape(title)}</h1></div>')


def section(title: str, description: str = "") -> None:
    st.subheader(title)
    if description:
        html(f'<p class="section-note">{escape(description)}</p>')


def card():
    return st.container(border=True)


def numbered(kind: str, text: str) -> str:
    _numbers[kind] += 1
    return f"<b>{kind} {_numbers[kind]}.</b> {escape(text)}"


def chart_theme(chart):
    return (chart.configure(background="transparent", font=SANS)
            .configure_view(strokeOpacity=0)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor=LINE, domainColor="#b9bec6",
                            tickColor="#b9bec6", labelFontSize=12, titleFontSize=12, titleFontWeight="normal")
            .configure_legend(labelColor=MUTED, titleColor=MUTED, labelFontSize=12)
            .configure_text(color=TEXT))


def show_chart(chart, caption: str) -> None:
    """Biểu đồ kèm chú thích đánh số bên dưới, như hình trong báo cáo."""
    st.altair_chart(chart_theme(chart), width="stretch", alt=caption)
    html(f'<p class="fig-cap">{numbered("Biểu đồ", caption)}</p>')


def show_table(frame, caption: str, **kwargs) -> None:
    """Bảng kèm chú thích đánh số bên dưới, như trong báo cáo."""
    st.dataframe(frame, width="stretch", **{"hide_index": True, **kwargs})
    html(f'<p class="tab-cap">{numbered("Bảng", caption)}</p>')


def report_table(rows: list[list], header: list[str], caption: str, right: set[int] = frozenset()) -> None:
    """Bảng ba đường kẻ kiểu báo cáo, cho các bảng ngắn."""
    cls = lambda i: ' class="r"' if i in right else ""
    head = "".join(f"<th{cls(i)}>{escape(h)}</th>" for i, h in enumerate(header))
    body = "".join("<tr>" + "".join(f"<td{cls(i)}>{escape(str(v))}</td>" for i, v in enumerate(r)) + "</tr>" for r in rows)
    html(f'<table class="report"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table><p class="tab-cap">{numbered("Bảng", caption)}</p>')


def rate_chart(summary: pd.DataFrame, height: int = 260):
    base = alt.Chart(summary).encode(
        y=alt.Y("group:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
        x=alt.X("rate:Q", title="Tỷ lệ rời bỏ trong nhóm", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%", tickCount=5)),
        tooltip=[alt.Tooltip("group:N", title="Nhóm"), alt.Tooltip("customers:Q", title="Khách hàng", format=","),
                 alt.Tooltip("churned:Q", title="Đã rời bỏ", format=","), alt.Tooltip("rate:Q", title="Tỷ lệ", format=".1%")])
    return (base.mark_bar(color=CHURN, size=20)
            + base.mark_text(align="left", dx=6, fontSize=12).encode(text=alt.Text("rate:Q", format=".1%"))).properties(height=height)


def parse_report(text: str) -> list[list[str]]:
    """Dòng của classification_report sklearn → hàng bảng (giống Bảng 7, 9 trong báo cáo)."""
    names = {"0": "0", "1": "1", "accuracy": "Accuracy", "macro avg": "Macro avg", "weighted avg": "Weighted avg"}
    rows = []
    for line in text.splitlines():
        parts = line.split()
        for key, name in names.items():
            if parts and " ".join(parts[:len(key.split())]) == key:
                values = parts[len(key.split()):]
                if key == "accuracy":
                    values = ["", "", *values]
                rows.append([name, *values])
    return rows


def scores_for(name: str) -> dict:
    group, variant, _ = EVAL_MODELS[name]
    return metrics[group][variant] if variant else metrics[group]


def display_stats(frame: pd.DataFrame) -> None:
    cols = st.columns(4)
    values = [
        ("Khách hàng đang xem", f"{len(frame):,}", "Số khách sau các bộ lọc trên trang này."),
        ("Tỷ lệ rời bỏ thực tế", f"{frame.Churn.eq('Yes').mean():.1%}", "Số nhãn Yes / số khách đang xem."),
        ("Thời gian sử dụng TB", f"{frame.tenure.mean():.1f} tháng", "Trung bình tenure của tập đang xem."),
        ("Phí hàng tháng TB", f"{frame.MonthlyCharges.mean():.2f}", "Đơn vị tiền gốc trong dữ liệu IBM.")]
    for col, (label, value, help_text) in zip(cols, values):
        col.metric(label, value, help=help_text)


def overview() -> None:
    churned = int(df.Churn.eq("Yes").sum())
    churn_rate = churned / len(df)
    selected_scores = scores_for("Hồi quy logistic (sau điều chỉnh)")
    page_header("Mô tả dữ liệu", "Báo cáo · Chương 2–3")
    for col, (label, value, help_text) in zip(st.columns(4), [
            ("Số quan sát sau làm sạch", f"{len(df):,}", "Số khách còn lại sau làm sạch."),
            ("Khách đã rời bỏ", f"{churned:,}", "Số khách đã rời bỏ."),
            ("Tỷ lệ rời bỏ", f"{churn_rate:.1%}", "Số khách rời bỏ / tổng số quan sát."),
            ("Độ nhạy lớp rời bỏ, hồi quy logistic", f"{selected_scores['recall_churn_1']:.1%}", METRIC_HELP["recall_churn_1"])]):
        col.metric(label, value, help=help_text)

    quality = metrics["data_quality"]
    outliers = table("eda_outliers.csv")
    n_outliers = int(outliers["outlier_count"].sum()) if "outlier_count" in outliers else 0
    missing = quality.get("missing_theo_cot_ban_dau", {})
    section("Chất lượng dữ liệu")
    report_table([
        ["Tổng quan bộ dữ liệu", f"{quality['so_dong_ban_dau']:,} quan sát, 21 trường"],
        ["Giá trị thiếu", ", ".join(f"{FIELD_LABELS.get(k, k)}: {v}" for k, v in missing.items()) + " → loại bỏ" if missing else "Không có"],
        ["Giá trị ngoại lai theo khoảng tứ phân vị × 1,5", f"{n_outliers}"],
        ["Dòng bị trùng lặp", f"{quality.get('so_dong_trung_hoan_toan', 0):,}"],
        ["Sau làm sạch", f"{len(df):,} quan sát"]],
        ["Kiểm tra", "Kết quả"], "Chất lượng dữ liệu.")
    section("Thời gian sử dụng và rời bỏ theo loại hợp đồng")
    views = {"Số khách": "customers", "Đã rời bỏ": "churned", "Tỷ lệ rời bỏ": "rate"}
    view = st.radio("Chỉ số", list(views), horizontal=True, key="overview_view", label_visibility="collapsed")
    field = views[view]
    trend = (df.assign(month=df.tenure // 3 * 3, churn=df.Churn.eq("Yes"))
             .groupby(["month", "Contract"]).agg(customers=("churn", "size"), churned=("churn", "sum"))
             .unstack(fill_value=0).stack(future_stack=True).reset_index())
    trend["rate"] = trend.churned / trend.customers.where(trend.customers > 0)
    trend["Hợp đồng"] = trend.Contract.map(value_label)
    contracts = [c for c in CONTRACT_COLORS if c in set(trend.Contract)]
    color = alt.Color("Hợp đồng:N", legend=alt.Legend(orient="bottom", title=None),
                      scale=alt.Scale(domain=[value_label(c) for c in contracts], range=[CONTRACT_COLORS[c] for c in contracts]))
    fmt = ".0%" if field == "rate" else ",.0f"
    base = alt.Chart(trend.dropna(subset=[field])).encode(
        x=alt.X("month:Q", title="Thời gian sử dụng (tháng)", scale=alt.Scale(nice=False), axis=alt.Axis(tickCount=12)),
        y=alt.Y(f"{field}:Q", title=view, stack=None if field == "rate" else "zero", axis=alt.Axis(format=fmt, tickCount=5)),
        color=color, order=alt.Order("Hợp đồng:N"),
        tooltip=["Hợp đồng:N", alt.Tooltip("month:Q", title="Từ tháng"), alt.Tooltip(f"{field}:Q", title=view, format=".1%" if field == "rate" else ",d")])
    mark = base.mark_line(strokeWidth=2) if field == "rate" else base.mark_area(opacity=.85)
    show_chart(mark.properties(height=290), f"{view} theo thời gian sử dụng và loại hợp đồng.")

    left, right = st.columns([1.2, 1], gap="large")
    with left:
        section("Biến phân loại và tình trạng rời bỏ")
        features = ["Contract", "InternetService", "PaymentMethod", "TechSupport", "OnlineSecurity"]
        groups = pd.concat([group_summary(df, f).assign(feature=f) for f in features]).sort_values("rate", ascending=False)
        top = groups.head(10).assign(feature=lambda d: d.feature.map(FIELD_LABELS))
        show_table(top[["feature", "group", "customers", "churned", "rate"]].rename(columns={
            "feature": "Thuộc tính", "group": "Nhóm", "customers": "Số khách", "churned": "Rời bỏ", "rate": "Tỷ lệ"}),
            "10 nhóm khách hàng có tỷ lệ rời bỏ cao nhất.",
            column_config={"Tỷ lệ": st.column_config.ProgressColumn("Tỷ lệ", min_value=0, max_value=1, format="percent", width="medium")})
    with right:
        section("Thời gian sử dụng × phí hàng tháng")
        tenure_bins = [0, 6, 12, 24, 36, 48, 60, 73]
        tenure_names = ["0–5", "6–11", "12–23", "24–35", "36–47", "48–59", "60–72"]
        grid = df.assign(t=pd.cut(df.tenure, tenure_bins, right=False, labels=tenure_names),
                         m=(df.MonthlyCharges // 10 * 10).clip(upper=110).astype(int), churn=df.Churn.eq("Yes"))
        grid = grid.groupby(["t", "m"], observed=True).agg(n=("churn", "size"), rate=("churn", "mean")).reset_index()
        grid["Tỷ lệ"] = grid.rate.where(grid.n >= 10)  # nhóm dưới 10 khách: không đọc tỷ lệ
        heat = alt.Chart(grid).mark_rect(stroke="#ffffff", strokeWidth=1).encode(
            x=alt.X("m:O", title="Phí hàng tháng (từ)", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("t:O", title="Thời gian dùng (tháng)", sort=tenure_names),
            color=alt.condition("isValid(datum['Tỷ lệ'])",
                                alt.Color("Tỷ lệ:Q", scale=alt.Scale(scheme="oranges", domain=[0, .7], clamp=True),
                                          legend=alt.Legend(format=".0%", title="Tỷ lệ rời bỏ", orient="bottom")),
                                alt.value("#f4f5f7")),
            tooltip=[alt.Tooltip("t:O", title="Tháng dùng"), alt.Tooltip("m:O", title="Phí từ"),
                     alt.Tooltip("n:Q", title="Khách"), alt.Tooltip("rate:Q", title="Tỷ lệ", format=".1%")])
        show_chart(heat.properties(height=260), "Tỷ lệ rời bỏ theo thời gian sử dụng và phí hàng tháng.")


def exploration() -> None:
    page_header("Thống kê mô tả", "Báo cáo · Chương 4")
    all_contracts, all_internet = sorted(df.Contract.unique()), sorted(df.InternetService.unique())
    min_tenure, max_tenure = int(df.tenure.min()), int(df.tenure.max())
    defaults = {"filter_contract": all_contracts, "filter_internet": all_internet,
                "filter_churn": ["No", "Yes"], "filter_tenure": (min_tenure, max_tenure)}

    def reset_filters():
        for key, value in defaults.items():
            st.session_state[key] = value

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    with card():
        section("Lọc dữ liệu")
        a, b = st.columns(2)
        contract = a.multiselect("Loại hợp đồng", all_contracts, format_func=value_label, key="filter_contract")
        internet = b.multiselect("Loại Internet", all_internet, format_func=lambda x: "Không có Internet" if x == "No" else value_label(x), key="filter_internet")
        churn = a.multiselect("Churn", ["No", "Yes"], format_func=lambda x: "Yes · Rời bỏ" if x == "Yes" else "No · Không rời bỏ", key="filter_churn")
        tenure = b.slider("Thời gian sử dụng (tháng)", min_tenure, max_tenure, key="filter_tenure") if min_tenure < max_tenure else (min_tenure, max_tenure)
        st.button("Đặt lại bộ lọc", on_click=reset_filters)
    filtered = df.loc[df.Contract.isin(contract) & df.InternetService.isin(internet)
                      & df.Churn.isin(churn) & df.tenure.between(*tenure)].copy()
    if filtered.empty:
        st.warning("Không có khách hàng phù hợp. Hãy chọn thêm nhóm hoặc bấm Đặt lại bộ lọc.")
        return
    display_stats(filtered)
    groups, distributions, details = st.tabs(["Biến phân loại và Churn", "Biến liên tục và Churn", "Dữ liệu chi tiết"])
    with groups:
        feature = st.selectbox("Biến phân loại", ["Contract", "InternetService", "PaymentMethod", "TechSupport", "OnlineSecurity", "SeniorCitizen", "Dependents", "PaperlessBilling"], format_func=lambda x: FIELD_LABELS[x])
        summary = group_summary(filtered, feature)
        a, b = st.columns([1.3, 1], gap="large")
        with a:
            show_chart(rate_chart(summary, max(230, len(summary) * 55)), f"Tác động của {FIELD_LABELS[feature]} đến Churn.")
        with b:
            shown = summary[["group", "customers", "churned", "rate"]].rename(columns={"group": "Nhóm", "customers": "Số khách", "churned": "Đã rời bỏ", "rate": "Tỷ lệ rời bỏ"})
            st.dataframe(shown.style.format({"Tỷ lệ rời bỏ": "{:.1%}"}), hide_index=True, width="stretch")
    with distributions:
        numeric = st.selectbox("Biến liên tục", NUMERIC, format_func=lambda x: FIELD_LABELS[x])
        plot_data = filtered[[numeric, "Churn"]].copy()
        plot_data["Trạng thái"] = plot_data.Churn.map({"No": "Không rời bỏ", "Yes": "Rời bỏ"})
        color = alt.Color("Trạng thái:N", scale=alt.Scale(domain=["Không rời bỏ", "Rời bỏ"], range=[RETAIN, CHURN]), legend=alt.Legend(orient="bottom", title=None))
        a, b = st.columns(2, gap="large")
        with a, card():
            section("Tần số (Histogram)")
            hist = alt.Chart(plot_data).mark_bar(opacity=.7, binSpacing=1).encode(
                x=alt.X(f"{numeric}:Q", bin=alt.Bin(maxbins=24), title=FIELD_LABELS[numeric]), y=alt.Y("count():Q", title="Số khách", stack=None), color=color,
                tooltip=["Trạng thái:N", alt.Tooltip("count():Q", title="Số khách")]).properties(height=280)
            show_chart(hist, f"Histogram {FIELD_LABELS[numeric]} theo Churn.")
        with b, card():
            section("Vị trí và độ phân tán (Boxplot)")
            box = alt.Chart(plot_data).mark_boxplot(extent=1.5, size=50, median={"color": TEXT}, outliers={"size": 12, "opacity": .5}).encode(x=alt.X("Trạng thái:N", title=None), y=alt.Y(f"{numeric}:Q", title=FIELD_LABELS[numeric]), color=color).properties(height=280)
            show_chart(box, f"Boxplot Churn và {FIELD_LABELS[numeric]}.")
        section("Biến liên tục và biến liên tục")
        corr = filtered[NUMERIC].corr().rename(index=FIELD_LABELS, columns=FIELD_LABELS)
        corr_data = corr.rename_axis("Biến hàng").reset_index().melt("Biến hàng", var_name="Biến cột", value_name="Hệ số")
        heat = alt.Chart(corr_data).encode(x=alt.X("Biến cột:N", title=None, axis=alt.Axis(labelAngle=0, labelLimit=180)), y=alt.Y("Biến hàng:N", title=None))
        heatmap = heat.mark_rect().encode(color=alt.Color("Hệ số:Q", scale=alt.Scale(domain=[-1, 0, 1], range=[RED, "#f7f7f7", RETAIN])), tooltip=["Biến hàng:N", "Biến cột:N", alt.Tooltip("Hệ số:Q", format=".3f")])
        labels = heat.mark_text(fontSize=14).encode(text=alt.Text("Hệ số:Q", format=".2f"))
        show_chart((heatmap + labels).properties(height=240), "Ma trận tương quan tenure, MonthlyCharges, TotalCharges.")
        if filtered[NUMERIC].nunique().lt(2).any() or len(filtered) < 3:
            st.caption("Quá ít quan sát để tính đủ hệ số.")
        with st.expander("Tương quan với Churn trên toàn bộ dữ liệu"):
            figures = {"Tương quan Spearman của Churn với các biến còn lại": "06_spearman_churn.png", "Histogram các biến liên tục": "02_numeric_histograms.png", "Boxplot Churn và các biến liên tục": "03_boxplots_by_churn.png", "Ma trận tương quan tenure, MonthlyCharges, TotalCharges": "04_numeric_correlation.png"}
            artifact = st.selectbox("Biểu đồ", list(figures))
            image_path = OUTPUT / "figures" / figures[artifact]
            if image_path.exists():
                st.image(str(image_path), width="stretch")
            method = st.selectbox("ANOVA F-test, Chi-square test, Mutual Information", ["ANOVA F-test", "Chi-square test", "Mutual Information"])
            filename = {"ANOVA F-test": "feature_anova.csv", "Chi-square test": "feature_chi_square.csv",
                        "Mutual Information": "feature_mutual_information.csv"}[method]
            test_table = table(filename)
            if not test_table.empty:
                test_table["feature"] = test_table.feature.map(feature_label)
                formats = {col: ("{:.2e}" if col == "p_value" else "{:.4f}") for col in test_table.select_dtypes("number").columns}
                st.dataframe(test_table.rename(columns={"feature": "Đặc trưng"}).style.format(formats), hide_index=True, width="stretch")
    with details:
        search = st.text_input("Tìm theo mã khách hàng", placeholder="Ví dụ: 7590", key="data_search")
        searched = filtered.loc[filtered.customerID.astype(str).str.contains(search.strip(), case=False, regex=False)]
        limit = st.selectbox("Số dòng hiển thị", [30, 100, 500, "Tất cả"], key="data_limit")
        preview = searched if limit == "Tất cả" else searched.head(limit)
        st.dataframe(prediction_display(preview), hide_index=True, width="stretch", height=420)
        st.download_button("Tải dữ liệu đã lọc CSV", csv_bytes(searched), "telco_filtered.csv", "text/csv")


def model_evaluation() -> None:
    page_header("Kỹ thuật khai phá", "Báo cáo · Chương 6")
    comparison = pd.DataFrame({name: scores_for(name) for name in EVAL_MODELS}).T[list(METRIC_LABELS)]
    left, _ = st.columns([1, 1.2], gap="large")
    with left:
        criterion = st.selectbox("Chỉ số so sánh", list(METRIC_LABELS), format_func=lambda x: METRIC_LABELS[x])
        comparison_plot = comparison[criterion].rename("value").rename_axis("model").reset_index()
        base = alt.Chart(comparison_plot).encode(y=alt.Y("model:N", title=None, sort="-x", axis=alt.Axis(labelLimit=260)),
            x=alt.X("value:Q", title=None, scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%" if criterion != "roc_auc" else ".1f")),
            tooltip=[alt.Tooltip("model:N", title="Mô hình"), alt.Tooltip("value:Q", title="Chỉ số", format=".3f")])
        show_chart((base.mark_bar(color=RETAIN, size=26) + base.mark_text(align="left", dx=8, fontSize=12).encode(text=alt.Text("value:Q", format=".1%" if criterion != "roc_auc" else ".3f"))).properties(height=220), "So sánh các mô hình phân loại trên tập kiểm tra.")
    section("So sánh các mô hình trên tập kiểm tra")
    short_names = {key: label.split(" · ")[0] for key, label in METRIC_LABELS.items()}
    formats = {name: "{:.1%}" if key != "roc_auc" else "{:.3f}" for key, name in short_names.items()}
    st.dataframe(comparison.rename(columns=short_names).style.format(formats), width="stretch")
    selected = st.selectbox("Mô hình", list(EVAL_MODELS))
    selected_scores = scores_for(selected)
    for col, (key, label) in zip(st.columns(5), METRIC_LABELS.items()):
        col.metric(label.split(" · ")[0], f"{selected_scores[key]:.3f}" if key == "roc_auc" else f"{selected_scores[key]:.1%}", help=METRIC_HELP[key])
    results, interpretation = st.tabs(["Báo cáo phân loại", "Diễn giải kết quả"])
    with results:
        tag = EVAL_MODELS[selected][2]
        report_path = OUTPUT / "tables" / f"classification_report_{tag}.txt"
        if report_path.exists():
            try:
                counts = confusion_from_report(selected_scores, report_path.read_text(encoding="utf-8"))
            except ValueError as exc:
                st.warning(str(exc))
            else:
                report_table(parse_report(report_path.read_text(encoding="utf-8")),
                             ["", "Precision", "Recall", "F1-score", "Support"], f"Báo cáo phân loại · {selected}.", {1, 2, 3, 4})
                a, b = st.columns([1, 1.05], gap="large")
                with a, card():
                    section("Ma trận nhầm lẫn")
                    matrix = pd.DataFrame([{"Thực tế": actual, "Dự đoán": predicted, "Số khách": counts[key], "Loại": key.upper()}
                        for actual, predicted, key in [("0 · Không rời bỏ", "0 · Không rời bỏ", "tn"), ("0 · Không rời bỏ", "1 · Rời bỏ", "fp"), ("1 · Rời bỏ", "0 · Không rời bỏ", "fn"), ("1 · Rời bỏ", "1 · Rời bỏ", "tp")]])
                    base = alt.Chart(matrix).encode(x=alt.X("Dự đoán:N", sort=["0 · Không rời bỏ", "1 · Rời bỏ"], title="Predicted label", axis=alt.Axis(labelAngle=0, orient="top")), y=alt.Y("Thực tế:N", sort=["0 · Không rời bỏ", "1 · Rời bỏ"], title="True label"))
                    cells = base.mark_rect(stroke="#ffffff", strokeWidth=3).encode(color=alt.Color("Số khách:Q", scale=alt.Scale(range=["#eef2f7", "#7aa2cc"], interpolate="rgb"), legend=None), tooltip=["Thực tế:N", "Dự đoán:N", "Số khách:Q", "Loại:N"])
                    numbers = base.mark_text(fontSize=28, fontWeight=600).encode(text="Số khách:Q")
                    show_chart((cells + numbers).properties(height=270), f"Ma trận nhầm lẫn · {selected}.")
                with b:
                    section("Bốn ô của ma trận")
                    c1, c2 = st.columns(2)
                    c1.metric("TP · Dự đoán đúng lớp 1", f"{counts['tp']:,}")
                    c2.metric("FN · Bỏ sót lớp 1", f"{counts['fn']:,}")
                    c1.metric("FP · Dự đoán sai lớp 1", f"{counts['fp']:,}")
                    c2.metric("TN · Dự đoán đúng lớp 0", f"{counts['tn']:,}")
        else:
            st.info("Chưa có báo cáo phân loại. Chạy lại pipeline.")
        if "cv_recall_each_fold" in selected_scores:
            with card():
                section("Stratified K-Fold Cross-Validation (5 fold)")
                folds = pd.DataFrame({"Fold": [f"Fold {i + 1}" for i in range(len(selected_scores['cv_recall_each_fold']))], "Recall": selected_scores["cv_recall_each_fold"]})
                a, b = st.columns([1.5, 1])
                with a:
                    cv = alt.Chart(folds).mark_bar(color=RETAIN, size=36).encode(x=alt.X("Fold:N", title=None, axis=alt.Axis(labelAngle=0)), y=alt.Y("Recall:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%", tickCount=4), title=None), tooltip=["Fold:N", alt.Tooltip("Recall:Q", format=".1%")]).properties(height=200)
                    show_chart(cv, "Recall lớp 1 qua từng fold.")
                with b:
                    st.metric("Recall trung bình qua các fold", f"{selected_scores['cv_recall_mean']:.1%}")
                    st.metric("Độ chính xác trung bình qua các fold", f"{selected_scores['cv_accuracy_mean']:.1%}")
        else:
            st.caption("Không chạy CV cho cây quyết định.")
    with interpretation:
        if selected.startswith("Hồi quy logistic"):
            filename = "logistic_selected_coefficients.csv" if selected == "Hồi quy logistic (sau điều chỉnh)" else "logistic_full_coefficients.csv"
            coefficients = table(filename)
            if not coefficients.empty:
                coefficients["Đặc trưng"] = coefficients.feature.map(feature_label)
                coefficients["Chiều tác động"] = coefficients.coefficient_scaled.map(lambda x: "Tăng điểm" if x >= 0 else "Giảm điểm")
                section("Hệ số hồi quy (đặc trưng đã chuẩn hóa)")
                coef = alt.Chart(coefficients).mark_bar().encode(
                    y=alt.Y("Đặc trưng:N", sort=alt.SortField("coefficient_scaled"), title=None, axis=alt.Axis(labelLimit=260)), x=alt.X("coefficient_scaled:Q", title="Hệ số trên đặc trưng chuẩn hóa"),
                    color=alt.Color("Chiều tác động:N", scale=alt.Scale(domain=["Giảm điểm", "Tăng điểm"], range=[RETAIN, CHURN]), legend=alt.Legend(orient="bottom")), tooltip=["Đặc trưng:N", alt.Tooltip("coefficient_scaled:Q", title="Hệ số", format=".3f")]).properties(height=max(350, len(coefficients) * 25))
                show_chart(coef, f"Hệ số {selected.lower()}.")
        else:
            section("Cây quyết định (max_depth = 4, criterion = gini)")
            tree_image = OUTPUT / "figures" / "decision_tree.png"
            if tree_image.exists():
                st.image(str(tree_image), width="stretch")
                st.download_button("Tải hình cây để phóng to", tree_image.read_bytes(), "decision_tree.png", "image/png")
            with st.expander("Các nhánh quan trọng"):
                rules = OUTPUT / "tables" / "decision_tree_rules.txt"
                if rules.exists():
                    st.code(rules.read_text(encoding="utf-8"))
                leaves = table("tree_risk_groups_test.csv")
                if not leaves.empty:
                    st.dataframe(leaves.rename(columns={"leaf_id": "Mã lá", "customers": "Số khách test", "actual_churn_rate": "Tỷ lệ rời bỏ thực tế", "mean_model_score": "Điểm mô hình trung bình"}).style.format({"Tỷ lệ rời bỏ thực tế": "{:.1%}", "Điểm mô hình trung bình": "{:.1%}"}), hide_index=True, width="stretch")
        with st.expander("Hồi quy tuyến tính (MonthlyCharges) và thống kê"):
            ols = pd.DataFrame(metrics["linear_regression"]).T.rename(index={"full": "Mô hình ban đầu", "selected": "Mô hình sau khi điều chỉnh"})
            st.dataframe(ols.rename(columns={"r2_train": "R-squared (huấn luyện)", "r2_test": "R-squared (kiểm tra)", "mae_test": "MAE", "rmse_test": "RMSE"}).style.format("{:.3f}"), width="stretch")
            pseudo = scores_for("Hồi quy logistic (sau điều chỉnh)").get("mcfadden_pseudo_r2_train")
            if pseudo is not None:
                st.metric("McFadden's R-squared (hồi quy logistic)", f"{pseudo:.3f}")
            statistical = st.selectbox("Bảng thống kê", ["VIF · hồi quy tuyến tính sau điều chỉnh", "Hệ số và p-value · hồi quy logistic", "VIF · hồi quy logistic"])
            stat_file = {"VIF · hồi quy tuyến tính sau điều chỉnh": "ols_selected_vif.csv", "Hệ số và p-value · hồi quy logistic": "logit_selected_statsmodels_coefficients.csv", "VIF · hồi quy logistic": "logit_selected_vif.csv"}[statistical]
            stat_data = table(stat_file)
            if not stat_data.empty:
                st.dataframe(stat_data, hide_index=True, width="stretch")


def read_csvs(files) -> pd.DataFrame | None:
    if not files:
        return None
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def run_label(run: dict) -> str:
    return f"{run['created'].replace('T', ' ')[5:16]} · {run['source']['label']} · seed {run['seed']}"


def fmt_metric(key: str, value: float) -> str:
    if key in ("roc_auc", "r2_test", "r2_train"):
        return f"{value:.3f}"
    return f"{value:.2f}" if key in ("rmse_test", "mae_test") else f"{value:.1%}"


def go(page_name: str) -> None:
    st.session_state["navigation"] = page_name


def current_data() -> tuple[pd.DataFrame, pd.DataFrame | None, str]:
    """Dữ liệu đã chọn ở Bước 1; chưa chọn thì dùng dữ liệu IBM gốc."""
    chosen = st.session_state.get("demo_data")
    if chosen:
        return chosen["base"], chosen["new"], chosen["label"]
    return load_csv(str(RAW_DATA), RAW_DATA.stat().st_mtime_ns), None, "IBM Telco (mặc định)"


def data_status(label: str) -> None:
    html(f'<div class="status">Dữ liệu: <b>{escape(label)}</b></div>')


def step(n: str, title: str) -> None:
    html(f'<div class="step"><span class="step-n">{escape(n)}</span><h3>{escape(title)}</h3></div>')


def counts_row(name: str, c: dict) -> list:
    total = c["stay"] + c["churn"]
    return [name, f"{total:,}", f"{c['stay']:,}", f"{c['churn']:,}", f"{c['churn'] / total:.1%}"]


# Tăng số này khi preprocess_preview trả thêm khóa mới, để bỏ cache của bản cũ.
PREVIEW_VERSION = 2
PREVIEW_KEYS = ("records", "removed", "split", "balance", "scale_stats")


@st.cache_data(show_spinner=False, max_entries=8)
def _cached_preview(base: pd.DataFrame, new: pd.DataFrame | None, test_size: float, seed: int, method: str,
                    version: int) -> dict:
    return preprocess_preview(base, new, test_size, seed, method)


def cached_preview(base: pd.DataFrame, new: pd.DataFrame | None, test_size: float, seed: int, method: str) -> dict:
    p = _cached_preview(base, new, test_size, seed, method, PREVIEW_VERSION)
    if not all(k in p for k in PREVIEW_KEYS):  # cache cũ còn sót sau khi cập nhật code
        _cached_preview.clear()
        p = _cached_preview(base, new, test_size, seed, method, PREVIEW_VERSION)
    return p


RECORD_VIEWS = {"all": "Tất cả record", "removed": "Bị loại bỏ", "kept": "Còn lại (hợp lệ)"}
RECORD_CAPTIONS = {"all": "Toàn bộ record sau khi gộp; hàng đỏ là hàng bị loại.",
                   "removed": "Các record bị loại khi làm sạch.", "kept": "Các record hợp lệ dùng cho bước sau."}


def set_record_view(view: str) -> None:
    st.session_state["clean_view"] = view


def clean_records(records: pd.DataFrame) -> None:
    """Ba thẻ bấm được (tất cả / bị loại / còn lại) và bảng record tương ứng."""
    bad = records["Lý do loại bỏ"].ne("")
    counts = {"all": len(records), "removed": int(bad.sum()), "kept": int((~bad).sum())}
    view = st.session_state.get("clean_view", "all")
    for col, key in zip(st.columns(3), RECORD_VIEWS):
        col.button(f"{RECORD_VIEWS[key]} **{counts[key]:,}**", key=f"clean_card_{key}", width="stretch",
                   type="primary" if key == view else "secondary", on_click=set_record_view, args=(key,))
    shown = {"all": records, "removed": records[bad], "kept": records[~bad]}[view]
    record_table(shown, navigate=view == "all")
    html(f'<p class="tab-cap">{numbered("Bảng", RECORD_CAPTIONS[view])}</p>')


def record_table(frame: pd.DataFrame, navigate: bool) -> None:
    """Bảng HTML cuộn được: tô đỏ hàng bị loại, có nút cuộn tới từng hàng bị loại."""
    cols = list(frame.columns)
    rows = [[int(i) + 1, *("" if pd.isna(v) else str(v) for v in r)] for i, r in zip(frame.index, frame.itertuples(index=False))]
    payload = json.dumps({"cols": cols, "rows": rows, "nav": navigate}, ensure_ascii=False).replace("</", "<\\/")
    components.html(RECORD_TABLE_HTML.replace("__DATA__", payload), height=500 if navigate else 440)


RECORD_TABLE_HTML = """
<style>
  body { margin: 0; font: 13px Inter, -apple-system, BlinkMacSystemFont, sans-serif; color: #1a1a1a; background: #fff; }
  .nav { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; padding: 0 0 8px; }
  .nav b { font-weight: 600; margin-right: 4px; }
  .nav button { font: inherit; font-size: 12px; border: 1px solid #e3a6a6; background: #fdf1f1; color: #9b1c1c;
                border-radius: 4px; padding: 3px 8px; cursor: pointer; }
  .nav button:hover { background: #fbe0e0; }
  .nav .step { border-color: #d9dce1; background: #fff; color: #1a1a1a; }
  .nav .pos { color: #555b65; margin-left: 4px; }
  .wrap { position: relative; overflow: auto; border: 1px solid #d9dce1; border-radius: 4px; }
  table { border-collapse: collapse; white-space: nowrap; }
  th, td { padding: 4px 10px; border-bottom: 1px solid #eceef1; text-align: left; }
  th { position: sticky; top: 0; background: #f4f5f7; font-weight: 600; z-index: 1; border-bottom: 1px solid #c9cdd3; }
  td.n { color: #8a9099; text-align: right; }
  .pin { position: sticky; background: #fff; z-index: 2; }
  th.pin { z-index: 3; background: #f4f5f7; }
  .pin.last { box-shadow: 1px 0 0 #c9cdd3; }
  tr.bad td, tr.bad td.pin { background: #fdecec; color: #8c1d1d; }
  tr.bad td.reason { font-weight: 600; }
  tr.bad td.empty { outline: 2px solid #d64545; outline-offset: -2px; }
  td.empty::after { content: "(trống)"; font-style: italic; color: #c0392b; }
  tr.flash td { animation: flash 1.4s ease-out; }
  @keyframes flash { 0%, 40% { background: #f8c4c4; } 100% { background: #fdecec; } }
</style>
<div class="nav" id="nav"></div>
<div class="wrap" id="wrap"><table><thead id="head"></thead><tbody id="body"></tbody></table></div>
<script>
const data = __DATA__;
const wrap = document.getElementById("wrap");
wrap.style.height = (data.nav ? 440 : 420) + "px";
document.getElementById("head").innerHTML =
  "<tr><th>#</th>" + data.cols.map(c => "<th></th>").join("") + "</tr>";
document.querySelectorAll("#head th").forEach((th, i) => { if (i) th.textContent = data.cols[i - 1]; });
const esc = v => v.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const bad = [];
const html = data.rows.map((r, i) => {
  const isBad = r[1] !== "";
  if (isBad) bad.push(i);
  const cells = r.slice(1).map((v, j) => {
    const cls = j === 0 ? "reason" : (isBad && v.trim() === "" ? "empty" : "");
    return `<td class="${cls}">${esc(v)}</td>`;
  }).join("");
  return `<tr id="r${i}" class="${isBad ? "bad" : ""}"><td class="n">${r[0]}</td>${cells}</tr>`;
}).join("");
document.getElementById("body").innerHTML = html;
if (!data.rows.length) document.getElementById("body").innerHTML = "<tr><td>Không có record.</td></tr>";
// Ghim 3 cột đầu (#, lý do, customerID) khi cuộn ngang.
const firstRow = document.querySelector("#head tr");
let left = 0;
[0, 1, 2].forEach(c => {
  const width = firstRow.children[c] ? firstRow.children[c].offsetWidth : 0;
  document.querySelectorAll(`#head tr > :nth-child(${c + 1}), #body tr > :nth-child(${c + 1})`).forEach(el => {
    el.classList.add("pin"); if (c === 2) el.classList.add("last"); el.style.left = left + "px";
  });
  left += width;
});
let at = -1;
function go(k) {
  if (!bad.length) return;
  at = (k + bad.length) % bad.length;
  const row = document.getElementById("r" + bad[at]);
  wrap.scrollTop = row.offsetTop - wrap.clientHeight / 2;
  const empty = row.querySelector("td.empty");
  wrap.scrollLeft = empty ? empty.offsetLeft - left - 40 : 0;
  row.classList.remove("flash"); void row.offsetWidth; row.classList.add("flash");
  document.getElementById("pos").textContent = `${at + 1}/${bad.length}`;
}
if (data.nav) {
  const nav = document.getElementById("nav");
  if (!bad.length) { nav.textContent = "Không có hàng nào bị loại."; }
  else {
    nav.innerHTML = '<b>Tới hàng bị loại:</b><button class="step" id="prev">↑ Trước</button>' +
      '<button class="step" id="next">Tiếp ↓</button><span class="pos" id="pos"></span>';
    document.getElementById("prev").onclick = () => go(at - 1);
    document.getElementById("next").onclick = () => go(at + 1);
    bad.slice(0, 40).forEach((i, k) => {
      const b = document.createElement("button");
      b.textContent = `#${data.rows[i][0]} · ${data.rows[i][2]}`;
      b.title = data.rows[i][1];
      b.onclick = () => go(k);
      nav.appendChild(b);
    });
  }
}
</script>
"""


# ---------- Bước 1 ----------
def page_data() -> None:
    page_header("Bước 1 · Dữ liệu", "Demo · 1/5")
    a, b = st.columns(2, gap="large")
    with a:
        section("Dữ liệu ban đầu")
        base_mode = st.radio("Nguồn", ["ibm", "upload", "none"], key="rt_base", label_visibility="collapsed",
                             format_func={"ibm": "IBM Telco (data/raw)", "upload": "Tải file khác", "none": "Không dùng"}.get)
        base_file = st.file_uploader("File dữ liệu ban đầu (CSV)", type=["csv"], key="rt_base_file") if base_mode == "upload" else None
    with b:
        section("Dữ liệu mới")
        new_files = st.file_uploader("File CSV (có cột Churn)",
                                     type=["csv"], accept_multiple_files=True, key="rt_new")
        if RAW_DATA.is_file():
            st.download_button("Tải file mẫu (20 dòng)", csv_bytes(load_csv(str(RAW_DATA), RAW_DATA.stat().st_mtime_ns).head(20)),
                               "du_lieu_moi_mau.csv", "text/csv")
    if st.button("Dùng dữ liệu này", type="primary", key="data_confirm"):
        try:
            if base_mode == "ibm":
                base, label = load_csv(str(RAW_DATA), RAW_DATA.stat().st_mtime_ns), "IBM Telco"
            elif base_mode == "upload":
                if base_file is None:
                    raise ValueError("Chưa chọn file dữ liệu ban đầu.")
                base, label = pd.read_csv(base_file), base_file.name
            else:
                base, label = None, ""
            new = read_csvs(new_files)
            if base is None and new is None:
                raise ValueError("Cần ít nhất một nguồn dữ liệu.")
            if base is None:
                base, new, label = new, None, "Chỉ dữ liệu mới"
            missing = sorted(set(RAW_COLUMNS) - set(base.columns))
            if missing:
                raise ValueError(f"Dữ liệu ban đầu thiếu cột: {', '.join(missing)}")
            combine_sources(base, new)  # kiểm tra cột của dữ liệu mới
            if new is not None:
                label += f" + {len(new):,} dòng mới ({', '.join(f.name for f in new_files)})"
            st.session_state["demo_data"] = {"base": base, "new": new, "label": label}
        except (ValueError, UnicodeError, pd.errors.ParserError) as exc:
            st.error(str(exc))
    base, new, label = current_data()
    data_status(label)
    rows = [["Dữ liệu ban đầu", f"{len(base):,}", f"{base['Churn'].eq('Yes').sum():,}", f"{base['Churn'].eq('Yes').mean():.1%}"]]
    if new is not None:
        rows.append(["Dữ liệu mới", f"{len(new):,}", f"{new['Churn'].eq('Yes').sum():,}", f"{new['Churn'].eq('Yes').mean():.1%}"])
    report_table(rows, ["Nguồn", "Số dòng", "Churn = Yes", "Tỷ lệ rời bỏ"], "Quy mô các nguồn dữ liệu.", {1, 2, 3})
    show_table(base.head(5), "Dữ liệu ban đầu.")
    if new is not None:
        show_table(new.head(5), "Dữ liệu mới.")
    st.button("Sang Bước 2 · Tiền xử lý", on_click=go, args=("2. Tiền xử lý",), key="to_step2")


# ---------- Bước 2 ----------
def page_preprocess() -> None:
    page_header("Bước 2 · Tiền xử lý", "Demo · 2/5")
    base, new, label = current_data()
    data_status(label)
    cfg = st.session_state.get("cfg", {"test_size": 0.2, "seed": 42, "method": "smote"})
    a, b, c = st.columns(3)
    test_size = a.slider("Tỷ lệ tập kiểm tra", 0.1, 0.4, cfg["test_size"], 0.05, key="pp_test")
    seed = b.number_input("Seed chia dữ liệu", 0, 99_999, cfg["seed"], key="pp_seed")
    method = c.selectbox("Phương pháp cân bằng lớp", list(BALANCING), index=list(BALANCING).index(cfg["method"]),
                         format_func=BALANCING.get, key="pp_bal")
    st.session_state["cfg"] = {"test_size": test_size, "seed": int(seed), "method": method}
    try:
        p = cached_preview(base, new, test_size, int(seed), method)
    except ValueError as exc:
        st.error(str(exc))
        return
    merge, quality = p["merge"], p["quality"]

    step("2.1", "Gộp dữ liệu")
    report_table([["Dữ liệu ban đầu", f"{merge['base_rows']:,}"], ["Dữ liệu mới", f"{merge['new_rows']:,}"],
                  ["Trùng mã khách (thay bằng bản mới)", f"{merge['replaced']:,}"], ["Sau khi gộp", f"{merge['rows']:,}"]],
                 ["", "Số dòng"], "Kết quả gộp dữ liệu.", {1})

    step("2.2", "Làm sạch dữ liệu")
    clean_records(p["records"])

    step("2.3", "Mã hóa dữ liệu (one-hot encoding)")
    shown_raw = ["customerID", "gender", "Partner", "tenure", "InternetService", "OnlineSecurity", "Contract", "PaymentMethod", "MonthlyCharges"]
    show_table(p["raw_sample"][shown_raw], "Trước mã hóa.")
    show_table(p["encoded_sample"].astype({c: int for c in p["encoded_sample"].columns
                                           if c not in ("tenure", "MonthlyCharges", "TotalCharges")}),
               f"Sau mã hóa ({p['encoded_shape'][1]} cột).")

    step("2.4", "Chia tập huấn luyện và tập kiểm tra")
    report_table([counts_row("Tập huấn luyện", p["split"]["train"]), counts_row("Tập kiểm tra", p["split"]["test"])],
                 ["Tập", "Số quan sát", "Lớp 0", "Lớp 1", "Tỷ lệ rời bỏ"], "Tập huấn luyện và tập kiểm tra.", {1, 2, 3, 4})

    step("2.5", f"Xử lý mất cân bằng lớp · {BALANCING[method]}")
    bal = p["balance"]
    rows = [{"Giai đoạn": phase, "Lớp": name, "Số mẫu": bal[key][cls]}
            for phase, key in [("Trước", "before"), ("Sau", "after")] for cls, name in [("stay", "0 · Không rời bỏ"), ("churn", "1 · Rời bỏ")]]
    a, b = st.columns([1, 1], gap="large")
    with a:
        bars = alt.Chart(pd.DataFrame(rows)).mark_bar().encode(
            x=alt.X("Giai đoạn:N", sort=["Trước", "Sau"], title=None, axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("Lớp:N", sort=["0 · Không rời bỏ", "1 · Rời bỏ"]),
            y=alt.Y("Số mẫu:Q", title="Số lượng", axis=alt.Axis(format=",d")),
            color=alt.Color("Lớp:N", scale=alt.Scale(domain=["0 · Không rời bỏ", "1 · Rời bỏ"], range=[RETAIN, CHURN]), legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["Giai đoạn:N", "Lớp:N", alt.Tooltip("Số mẫu:Q", format=",d")]).properties(height=280)
        show_chart(bars, "Phân bố các lớp trong tập huấn luyện.")
    with b:
        report_table([counts_row("Huấn luyện (trước)", bal["before"]), counts_row("Huấn luyện (sau)", bal["after"]), counts_row("Kiểm tra (giữ nguyên)", p["split"]["test"])],
                     ["", "Tổng", "Lớp 0", "Lớp 1", "Tỷ lệ rời bỏ"], "Phân bố lớp trước và sau xử lý.", {1, 2, 3, 4})
    if p["synthetic"] is not None:
        real = p["train_churn"].sample(min(600, len(p["train_churn"])), random_state=0).assign(Loại="Khách rời bỏ thật")
        fake = p["synthetic"].sample(min(600, len(p["synthetic"])), random_state=0).assign(Loại="Mẫu SMOTE sinh thêm")
        scatter = alt.Chart(pd.concat([real, fake])).mark_circle(size=22, opacity=.6).encode(
            x=alt.X("tenure:Q", title="Thời gian sử dụng (tháng)"), y=alt.Y("MonthlyCharges:Q", title="Phí hàng tháng"),
            color=alt.Color("Loại:N", scale=alt.Scale(domain=["Khách rời bỏ thật", "Mẫu SMOTE sinh thêm"], range=[CHURN, "#7f7f7f"]),
                            legend=alt.Legend(orient="bottom", title=None))).properties(height=300)
        show_chart(scatter, "Mẫu SMOTE và khách rời bỏ thật.")

    step("2.6", "Chuẩn hóa (StandardScaler)")
    stats = p["scale_stats"]
    report_table([[FIELD_LABELS[c], f"{r.before_mean:,.2f}", f"{r.before_std:,.2f}", f"{round(r.after_mean, 2) or 0:.2f}", f"{r.after_std:.2f}"]
                  for c, r in stats.iterrows()],
                 ["Biến", "TB trước", "ĐLC trước", "TB sau", "ĐLC sau"], "Các biến liên tục trên tập huấn luyện trước và sau chuẩn hóa.", {1, 2, 3, 4})
    st.button("Sang Bước 3 · Huấn luyện", on_click=go, args=("3. Huấn luyện",), key="to_step3", type="primary")


# ---------- Bước 3 ----------
def model_params(default_balancing: str) -> dict:
    """Ba cột cấu hình; mỗi mô hình có bộ thuật toán riêng."""
    chosen = {}
    tree_col, logit_col, lin_col = st.columns(3, gap="medium")
    with tree_col, card():
        if st.checkbox("**Cây quyết định (Decision Tree)**", value=True, key="rt_use_tree"):
            chosen["decision_tree"] = {
                "criterion": st.selectbox("Tiêu chí chia nhánh", ["gini", "entropy", "log_loss"], key="rt_tree_criterion"),
                "max_depth": st.slider("Độ sâu tối đa", 2, 12, 4, key="rt_tree_depth"),
                "min_samples_leaf": st.number_input("Số mẫu tối thiểu ở lá", 1, 200, 1, key="rt_tree_leaf"),
                "balancing": st.selectbox("Cân bằng lớp", list(BALANCING), index=4, format_func=BALANCING.get, key="rt_tree_bal"),
                "features": st.radio("Đặc trưng", ["report", "all"], format_func={"report": "7 biến theo báo cáo", "all": "Tất cả"}.get, key="rt_tree_feat"),
            }
    with logit_col, card():
        if st.checkbox("**Hồi quy logistic (Logistic Regression)**", value=True, key="rt_use_logit"):
            solver = st.selectbox("Solver", ["lbfgs", "liblinear", "newton-cg", "saga"], key="rt_logit_solver")
            l1_ok = solver in ("liblinear", "saga")
            penalty = st.radio("Regularization", ["l2", "l1"] if l1_ok else ["l2"], horizontal=True, key=f"rt_logit_pen_{l1_ok}",
                               )
            chosen["logistic"] = {
                "solver": solver, "penalty": penalty,
                "C": st.select_slider("C (nghịch đảo mức phạt)", [0.01, 0.1, 1.0, 10.0, 100.0], value=1.0, key="rt_logit_c"),
                "balancing": st.selectbox("Cân bằng lớp", list(BALANCING), index=list(BALANCING).index(default_balancing),
                                          format_func=BALANCING.get, key="rt_logit_bal"),
                "features": st.radio("Đặc trưng", ["report", "all"], format_func={"report": "16 biến theo báo cáo", "all": "Tất cả"}.get, key="rt_logit_feat"),
            }
    with lin_col, card():
        if st.checkbox("**Hồi quy tuyến tính (Linear Regression)**", value=True, key="rt_use_lin"):
            algo = st.selectbox("Thuật toán", ["ols", "ridge", "lasso"], format_func={"ols": "OLS", "ridge": "Ridge (L2)", "lasso": "Lasso (L1)"}.get, key="rt_lin_algo")
            chosen["linear"] = {
                "algorithm": algo,
                "alpha": st.select_slider("Alpha", [0.01, 0.1, 0.5, 1.0, 10.0], value=1.0, key="rt_lin_alpha", disabled=algo == "ols"),
                "features": st.radio("Đặc trưng", ["report", "all"], format_func={"report": "10 biến theo báo cáo", "all": "Tất cả"}.get, key="rt_lin_feat"),
            }
            st.caption("Mục tiêu: MonthlyCharges")
    return chosen


def activate(run_id: str, name: str) -> None:
    set_active_model(OUTPUT / "models", run_id, name)
    st.toast(f"Đã chọn {MODEL_NAMES[name]} ({run_id}) cho Bước 5 · Dự đoán.")


def render_run_results(run: dict) -> None:
    models = run["models"]
    section("Kết quả lần huấn luyện", run_label(run))
    cls = {k: v for k, v in models.items() if k in CLASSIFIERS}
    if cls:
        report_table([[MODEL_NAMES[k]] + [fmt_metric(m, v["metrics"][m]) for m in CLS_METRICS] + [f"{v['metrics']['cv_recall_mean']:.1%}"]
                      for k, v in cls.items()],
                     ["Mô hình", *CLS_METRICS.values(), "Recall CV (5 fold)"], "Báo cáo phân loại trên tập kiểm tra (lớp 1 = rời bỏ).", set(range(1, 7)))
        cols = st.columns(len(cls))
        for col, (name, info) in zip(cols, cls.items()):
            c = info["metrics"]["confusion"]
            with col:
                report_table([["0 · Không rời bỏ", f"{c['tn']:,}", f"{c['fp']:,}"], ["1 · Rời bỏ", f"{c['fn']:,}", f"{c['tp']:,}"]],
                             ["True \\ Predicted", "0", "1"], f"Ma trận nhầm lẫn · {MODEL_NAMES[name]}.", {1, 2})
                st.button("Dùng mô hình này để dự đoán", key=f"use_{run['run_id']}_{name}", on_click=activate, args=(run["run_id"], name))
    if "linear" in models:
        m = models["linear"]["metrics"]
        report_table([["Hồi quy tuyến tính"] + [fmt_metric(k, m[k]) for k in ("r2_train", *LIN_METRICS)]],
                     ["Mô hình", "R-squared (huấn luyện)", *LIN_METRICS.values()], "Hồi quy tuyến tính MonthlyCharges.", {1, 2, 3, 4})


def page_train() -> None:
    page_header("Bước 3 · Huấn luyện", "Demo · 3/5")
    base, new, label = current_data()
    data_status(label)
    cfg = st.session_state.get("cfg", {"test_size": 0.2, "seed": 42, "method": "smote"})
    params = model_params(cfg["method"])
    a, b, c = st.columns(3, gap="medium")
    test_size = a.slider("Tỷ lệ tập kiểm tra", 0.1, 0.4, cfg["test_size"], 0.05, key="rt_test")
    seed_mode = b.radio("Seed", ["random", "fixed"], format_func={"random": "Ngẫu nhiên mỗi lần", "fixed": "Cố định"}.get,
                        horizontal=True, key="rt_seed_mode")
    seed = c.number_input("Giá trị seed", 0, 99_999, cfg["seed"], key="rt_seed", disabled=seed_mode == "random")
    if st.button("Huấn luyện", type="primary", disabled=not params, key="rt_go"):
        try:
            with st.spinner("Đang huấn luyện..."):
                record = run_retrain(base, new, {"seed": None if seed_mode == "random" else int(seed), "test_size": test_size,
                                                 "models": params}, RUNS, {"label": label})
            st.session_state["last_run"] = record
        except ValueError as exc:
            st.error(str(exc))
    if "last_run" in st.session_state:
        render_run_results(st.session_state["last_run"])
        st.button("Sang Bước 4 · So sánh", on_click=go, args=("4. So sánh",), key="to_step4")


# ---------- Bước 4 ----------
def page_compare() -> None:
    page_header("Bước 4 · So sánh", "Demo · 4/5")
    runs = load_runs(RUNS)
    if not runs:
        st.info("Chưa có lần huấn luyện nào.")
        st.button("Sang Bước 5 · Dự đoán", on_click=go, args=("5. Dự đoán",), key="to_step5_empty")
        return
    table_ = comparison_table(runs)
    labels = {r["run_id"]: run_label(r) for r in runs}
    table_["Lần chạy"] = table_.run_id.map(labels)
    table_["Mô hình"] = table_.model.map(MODEL_NAMES)
    _, active = active_model_path(OUTPUT)
    current = f"{MODEL_NAMES[active['model']]} · {labels.get(active['run_id'], active['run_id'])}" if active else "Hồi quy logistic (sau điều chỉnh)"
    html(f'<div class="status">{len(runs)} lần chạy · Mô hình đang dùng: <b>{escape(current)}</b></div>')

    cls = table_[table_.model.isin(CLASSIFIERS)]
    if not cls.empty:
        section("Mô hình phân loại (Churn)")
        metric = st.selectbox("Chọn mô hình tốt nhất theo", list(CLS_METRICS), format_func=CLS_METRICS.get, key="cmp_metric")
        best = cls.loc[cls[metric].idxmax()]
        html(f'<div class="result" style="--k:{GREEN}"><div class="note">Tốt nhất theo {CLS_METRICS[metric]}</div>'
             f'<div class="big">{fmt_metric(metric, best[metric])}</div>'
             f'<div class="note">{escape(best["Mô hình"])} · {escape(best["Lần chạy"])}</div></div>')
        st.button("Dùng mô hình tốt nhất để dự đoán", type="primary", on_click=activate, args=(best.run_id, best.model), key="use_best")
        recent = cls[cls.run_id.isin([r["run_id"] for r in runs[:10]])]
        chart = alt.Chart(recent).mark_bar().encode(
            y=alt.Y("Lần chạy:N", title=None, sort=[labels[r["run_id"]] for r in runs], axis=alt.Axis(labelLimit=340)),
            yOffset=alt.YOffset("Mô hình:N"),
            x=alt.X(f"{metric}:Q", title=CLS_METRICS[metric], scale=alt.Scale(domain=[0, 1]),
                    axis=alt.Axis(format=".0%" if metric != "roc_auc" else ".1f", tickCount=5)),
            color=alt.Color("Mô hình:N", scale=alt.Scale(domain=[MODEL_NAMES[k] for k in CLASSIFIERS], range=[GREEN, RETAIN]),
                            legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["Lần chạy:N", "Mô hình:N", alt.Tooltip(f"{metric}:Q", format=".3f")]).properties(height=alt.Step(20))
        show_chart(chart, f"{CLS_METRICS[metric]} của 10 lần chạy gần nhất.")
        show_table(cls[["Lần chạy", "Mô hình", "rows", *CLS_METRICS]].rename(columns={"rows": "Số dòng", **CLS_METRICS})
                   .style.format({v: "{:.1%}" for k, v in CLS_METRICS.items() if k != "roc_auc"} | {"ROC AUC": "{:.3f}", "Số dòng": "{:,}"}),
                   "Báo cáo phân loại theo lần chạy.")
        options = list(cls[["run_id", "model"]].itertuples(index=False, name=None))
        pick = st.selectbox("Hoặc chọn một mô hình cụ thể", options, key="cmp_pick",
                            format_func=lambda o: f"{MODEL_NAMES[o[1]]} · {labels[o[0]]}")
        st.button("Dùng mô hình đã chọn", on_click=activate, args=pick, key="use_pick")
    lin = table_[table_.model == "linear"]
    if not lin.empty:
        section("Hồi quy tuyến tính (MonthlyCharges)")
        show_table(lin[["Lần chạy", "rows", *LIN_METRICS]].rename(columns={"rows": "Số dòng", **LIN_METRICS})
                   .style.format({"R² test": "{:.3f}", "RMSE test": "{:.2f}", "MAE test": "{:.2f}", "Số dòng": "{:,}"}),
                   "Kết quả hồi quy tuyến tính theo lần chạy.")
    st.download_button("Tải bảng so sánh (CSV)", csv_bytes(table_.drop(columns=["Lần chạy", "Mô hình"])), "so_sanh_lan_chay.csv", "text/csv")
    st.button("Sang Bước 5 · Dự đoán", on_click=go, args=("5. Dự đoán",), key="to_step5", type="primary")


def render_prediction_result(result: pd.DataFrame) -> None:
    row = result.iloc[0]
    score = float(row.churn_risk_score)
    label = "Dự đoán rời bỏ" if row.predicted_churn == "Yes" else "Dự đoán không rời bỏ"
    group = RISK_LABELS[row.risk_group]
    tone = CHURN if row.predicted_churn == "Yes" else GREEN
    html(f'<div class="result" style="--k:{tone}"><div class="note">{escape(label)} · mức rủi ro {escape(group.lower())}</div>'
         f'<div class="big">{score:.1%}</div><div class="note">Hồ sơ {escape(str(row.get("customerID", "khách hàng vừa nhập")))}</div></div>')
    a, b, c = st.columns(3)
    a.metric("Điểm rủi ro", f"{score:.1%}", help="Điểm của mô hình, không phải xác suất đã hiệu chuẩn.")
    b.metric("Mức rủi ro", group, help="Thấp ≤ 0,3 · Trung bình ≤ 0,6 · Cao > 0,6")
    c.metric("Nhãn dự đoán", "Rời bỏ" if row.predicted_churn == "Yes" else "Không rời bỏ", help="Ngưỡng 0,5.")
    st.progress(min(max(score, 0), 1))
    with st.expander("Kiểm tra hồ sơ vừa gửi"):
        fields = [col for col in result.columns if col in FIELD_LABELS]
        profile = pd.DataFrame({"Thông tin": [FIELD_LABELS[col] for col in fields], "Giá trị": [value_label(row[col]) for col in fields]})
        st.dataframe(profile, hide_index=True, width="stretch")
    st.download_button("Tải kết quả khách hàng CSV", csv_bytes(result), "customer_prediction.csv", "text/csv", key="download_single")


def single_prediction() -> None:
    options = ["Nhập hồ sơ mới", "DEMO001 · thời gian ngắn", "DEMO002 · hợp đồng dài hạn", "DEMO003 · hồ sơ hỗn hợp"]
    scenario = st.selectbox("Bắt đầu từ hồ sơ", options, key="scenario")
    defaults = {"customerID": "KH001", "gender": "Female", "Dependents": "No", "tenure": 6, "PhoneService": "Yes", "InternetService": "Fiber optic", "OnlineSecurity": "No", "OnlineBackup": "No", "DeviceProtection": "No", "TechSupport": "No", "PaperlessBilling": "Yes", "Contract": "Month-to-month", "PaymentMethod": "Electronic check", "MonthlyCharges": 70.0}
    if scenario != options[0]:
        sample_path = ROOT / "data" / "new_customers_example.csv"
        examples = load_csv(str(sample_path), sample_path.stat().st_mtime_ns)
        defaults = examples.iloc[options.index(scenario) - 1].to_dict()
    if st.session_state.get("last_scenario") != scenario or "customer_gender" not in st.session_state:
        for key, value in defaults.items():
            st.session_state["customer_" + key] = int(value) if key == "tenure" else float(value) if key == "MonthlyCharges" else str(value)
        st.session_state["last_scenario"] = scenario
        st.session_state.pop("single_result", None)
    with st.form("customer"):
        a, b, c = st.columns(3, gap="large")
        with a:
            section("01 · Hồ sơ khách hàng")
            customer_id = st.text_input("Mã khách hàng (tùy chọn)", key="customer_customerID")
            gender = st.selectbox("Giới tính", ["Female", "Male"], format_func=value_label, key="customer_gender")
            dependents = st.selectbox("Có người phụ thuộc", ["No", "Yes"], format_func=value_label, key="customer_Dependents")
            tenure = st.number_input("Thời gian đã sử dụng (tháng)", min_value=0, max_value=120, step=1, key="customer_tenure")
            monthly = st.number_input("Phí hàng tháng", min_value=0.0, max_value=500.0, step=0.5, key="customer_MonthlyCharges")
        with b:
            section("02 · Dịch vụ đăng ký")
            phone = st.selectbox("Dịch vụ điện thoại", ["Yes", "No"], format_func=value_label, key="customer_PhoneService")
            internet = st.selectbox("Loại Internet", ["Fiber optic", "DSL", "No"], format_func=lambda x: "Không có Internet" if x == "No" else value_label(x), key="customer_InternetService")
            security = st.selectbox("Bảo mật trực tuyến", ["No", "Yes"], format_func=value_label, key="customer_OnlineSecurity")
            backup = st.selectbox("Sao lưu trực tuyến", ["No", "Yes"], format_func=value_label, key="customer_OnlineBackup")
        with c:
            section("03 · Dịch vụ & thanh toán")
            protection = st.selectbox("Bảo vệ thiết bị", ["No", "Yes"], format_func=value_label, key="customer_DeviceProtection")
            support = st.selectbox("Hỗ trợ kỹ thuật", ["No", "Yes"], format_func=value_label, key="customer_TechSupport")
            billing = st.selectbox("Hóa đơn điện tử", ["Yes", "No"], format_func=value_label, key="customer_PaperlessBilling")
            contract = st.selectbox("Loại hợp đồng", ["Month-to-month", "One year", "Two year"], format_func=value_label, key="customer_Contract")
            payment = st.selectbox("Phương thức thanh toán", ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"], format_func=value_label, key="customer_PaymentMethod")
        submitted = st.form_submit_button("Dự đoán nguy cơ", type="primary", width="stretch")
    if submitted:
        sample = pd.DataFrame([{"customerID": customer_id, "gender": gender, "Dependents": dependents, "tenure": tenure, "PhoneService": phone, "InternetService": internet, "OnlineSecurity": security, "OnlineBackup": backup, "DeviceProtection": protection, "TechSupport": support, "PaperlessBilling": billing, "Contract": contract, "PaymentMethod": payment, "MonthlyCharges": monthly}])
        try:
            validate_prediction_data(sample, required_columns())
            st.session_state["single_result"] = predict_dataframe(sample)
        except (ValueError, FileNotFoundError, TypeError) as exc:
            st.session_state.pop("single_result", None)
            st.error(str(exc))
        else:
            if tenure > df.tenure.max():
                st.warning(f"Thời gian sử dụng vượt mức lớn nhất trong dữ liệu mẫu ({int(df.tenure.max())} tháng). Mô hình đang ngoại suy ở biến này.")
    if "single_result" in st.session_state:
        render_prediction_result(st.session_state["single_result"])
    else:
        st.caption("Chưa có kết quả.")


def batch_prediction() -> None:
    sample_path = ROOT / "data" / "new_customers_example.csv"
    a, b = st.columns([1.5, 1], gap="large")
    with a:
        section("Tải danh sách khách hàng")
        upload = st.file_uploader("Chọn file CSV", type=["csv"], key="customer_upload")
        analyze = st.button("Phân tích CSV", type="primary", disabled=upload is None)
    with b, card():
        section("Dữ liệu mẫu")
        run_example = st.button("Chạy thử 3 khách hàng mẫu")
        st.download_button("Tải CSV mẫu", sample_path.read_bytes(), "new_customers_example.csv", "text/csv")
    with st.expander("Cột mô hình hiện tại cần"):
        st.code(",".join(required_columns()), language="text", wrap_lines=True)
    if run_example or analyze:
        st.session_state.pop("batch_result", None)
        try:
            new_df = pd.read_csv(sample_path if run_example else upload)
            validate_prediction_data(new_df, required_columns())
            with st.spinner("Đang chấm điểm khách hàng..."):
                result = predict_dataframe(new_df)
            st.session_state["batch_result"] = result
            st.session_state["batch_source"] = sample_path.name if run_example else upload.name
        except (ValueError, FileNotFoundError, TypeError, UnicodeError) as exc:
            st.error(str(exc))
    if "batch_result" not in st.session_state:
        return
    result = st.session_state["batch_result"]
    section("Kết quả", f"Nguồn: {st.session_state['batch_source']}")
    a, b, c = st.columns(3)
    a.metric("Đã chấm điểm", f"{len(result):,}")
    b.metric("Dự đoán rời bỏ", f"{result.predicted_churn.eq('Yes').sum():,}")
    c.metric("Mức rủi ro cao", f"{result.risk_group.eq('High').sum():,}")
    a, b = st.columns(2)
    levels = a.multiselect("Lọc bảng theo mức rủi ro", ["High", "Medium", "Low"], default=["High", "Medium", "Low"], format_func=lambda x: RISK_LABELS[x])
    search = b.text_input("Tìm mã khách trong kết quả", key="prediction_search")
    shown = result.loc[result.risk_group.isin(levels)].copy()
    if search.strip():
        if "customerID" in shown:
            shown = shown.loc[shown.customerID.astype(str).str.contains(search.strip(), case=False, regex=False)]
        else:
            st.caption("File này không có customerID nên chưa thể tìm theo mã khách.")
    shown = shown.sort_values("churn_risk_score", ascending=False)
    ordered = [col for col in ["customerID", "churn_risk_score", "predicted_churn", "risk_group"] if col in shown]
    ordered += [col for col in shown if col not in ordered]
    displayed = prediction_display(shown[ordered].head(500))
    st.dataframe(displayed, hide_index=True, width="stretch", height=360, column_config={"Điểm rủi ro": st.column_config.ProgressColumn("Điểm rủi ro", min_value=0, max_value=1, format="percent")})
    st.caption(f"{len(shown):,} khách")
    st.download_button("Tải toàn bộ kết quả CSV", csv_bytes(result), "predictions.csv", "text/csv", type="primary")


def predictions() -> None:
    path, active = active_model_path(OUTPUT)
    name = f"{MODEL_NAMES[active['model']]}, lần chạy {active['run_id']}" if active else "Hồi quy logistic (sau điều chỉnh)"
    page_header("Bước 5 · Dự đoán", "Demo · 5/5")
    html(f'<div class="status">Mô hình: <b>{escape(name)}</b></div>')
    if not path.exists():
        st.error("Chưa có mô hình. Chạy run_pipeline.py hoặc huấn luyện ở Bước 3.")
        return
    mode = st.radio("Cách nhập dữ liệu", ["Một khách hàng", "Hàng loạt qua CSV"], horizontal=True, key="prediction_mode")
    if mode == "Một khách hàng":
        single_prediction()
    else:
        batch_prediction()


def guide_page() -> None:
    page_header("Hướng dẫn sử dụng", "Tài liệu")
    if not GUIDE.exists():
        st.info("Chưa có tài liệu hướng dẫn trong thư mục dự án.")
        return
    guide = GUIDE.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^## ", guide)
    sections = {"Bắt đầu từ đâu?": "\n".join(parts[0].splitlines()[1:])}
    for part in parts[1:]:
        title, _, content = part.partition("\n")
        sections[title] = content
    topic = st.selectbox("Chọn nội dung cần giải thích", list(sections), key="guide_topic")
    st.download_button("Tải hướng dẫn đầy đủ (.md)", guide.encode("utf-8-sig"), GUIDE.name, "text/markdown")
    with card():
        st.markdown(sections[topic])


with st.sidebar:
    page = st.radio("Điều hướng", PAGES, key="navigation", label_visibility="collapsed")
    st.divider()
    if GUIDE.exists():
        st.download_button("Tải tài liệu hướng dẫn", GUIDE.read_bytes(), GUIDE.name, "text/markdown", key="sidebar_guide")

metrics_path = OUTPUT / "metrics.json"
data_path = ROOT / "data" / "processed" / "telco_clean.csv"
if page == "Hướng dẫn sử dụng":
    guide_page()
    st.stop()
if not metrics_path.exists() or not data_path.exists():
    st.error("Chưa có kết quả phân tích. Chạy các lệnh sau trong thư mục dự án:")
    st.code("python download_data.py\npython run_pipeline.py", language="bash")
    st.stop()
try:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    df = load_csv(str(data_path), data_path.stat().st_mtime_ns)
except (ValueError, OSError) as exc:
    st.error(f"Chưa đọc được kết quả phân tích: {exc}. Nếu pipeline đang chạy, chờ hoàn tất rồi tải lại trang.")
    st.stop()
if df.empty:
    st.error("Dữ liệu sau làm sạch đang rỗng. Hãy kiểm tra dữ liệu và chạy lại pipeline.")
    st.stop()

{
    "Mô tả dữ liệu": overview, "Thống kê mô tả": exploration, "Kỹ thuật khai phá": model_evaluation,
    "1. Dữ liệu": page_data, "2. Tiền xử lý": page_preprocess, "3. Huấn luyện": page_train,
    "4. So sánh": page_compare, "5. Dự đoán": predictions,
}[page]()
