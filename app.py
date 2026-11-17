"""Dashboard tiếng Việt: .venv/Scripts/python.exe -m streamlit run app.py."""
import json
import re
from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from predict import predict_dataframe
from src.dashboard import (
    FIELD_LABELS, METRIC_HELP, METRIC_LABELS, RISK_LABELS,
    confusion_from_report, feature_label, group_summary, prediction_display,
    validate_prediction_data, value_label,
)

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
GUIDE = ROOT / "HUONG_DAN_GIAO_DIEN.md"
TEAL, BLUE, RED = "#087F8C", "#5067B2", "#D85D65"
NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges"]
MODEL_NAMES = {
    "Logistic điều chỉnh": ("logistic_regression", "selected", "logistic_selected"),
    "Logistic đầy đủ": ("logistic_regression", "full", "logistic_full"),
    "Cây quyết định": ("decision_tree", None, "decision_tree"),
}
PAGES = ["Tổng quan", "Khám phá dữ liệu", "Đánh giá mô hình", "Dự đoán Churn", "Hướng dẫn sử dụng"]

st.set_page_config(page_title="Telco Churn · PTIT", page_icon="📊", layout="wide")
alt.data_transformers.disable_max_rows()
st.markdown("""
<style>
.stApp {background:#f5f7fb; color:#172b4d;}
.block-container {max-width:1440px; padding-top:2rem; padding-bottom:3rem;}
[data-testid="stSidebar"] {background:#fff; border-right:1px solid #e2e8f0;}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] {gap:.5rem;}
[data-testid="stSidebar"] .stRadio label {padding:.5rem .35rem;}
[data-testid="stMetric"] {background:#fff; border:1px solid #e2e8f0;
 border-radius:14px; padding:1.1rem 1.2rem; min-height:112px;}
[data-testid="stMetricLabel"] {font-size:.88rem; color:#52637b;}
[data-testid="stMetricValue"] {font-weight:750; color:#172b4d;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;}
h1,h2,h3 {letter-spacing:-.025em;}
h1 {font-size:2rem !important;} h2 {font-size:1.5rem !important;}
h3 {font-size:1.15rem !important;}
.hero {background:linear-gradient(120deg,#142c49,#183d59 65%,#0d626b);
 border-radius:20px; padding:2rem 2.2rem; margin:.2rem 0 1.4rem; color:white;}
.hero .eyebrow {color:#a3e6df; font-size:.76rem; font-weight:700;
 letter-spacing:.14em; margin-bottom:.7rem;}
.hero h1 {color:white; margin:0 0 .6rem; font-size:2rem !important;}
.hero p {color:#deebf5; margin:0; max-width:850px; line-height:1.6;}
.brand {font-size:1.4rem; font-weight:800; color:#172b4d; margin-bottom:.2rem;}
.brand span {color:#087f8c;}
.brand-note {color:#61748b; font-size:.85rem; margin-bottom:1.5rem;}
.section-note {color:#52637b; margin:-.3rem 0 1rem; line-height:1.6;}
.status {background:#e9f6f4; color:#17645e; border-radius:10px;
 padding:.8rem 1rem; font-size:.85rem; line-height:1.6;}
.result-card {padding:1.3rem; background:#fff; border:1px solid #d9e5ef;
 border-left:5px solid #087f8c; border-radius:12px; margin:.6rem 0 1rem;}
.result-card strong {font-size:1.25rem;}
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"]
 {border-radius:9px; font-weight:650;}
@media (max-width:700px) {
 .block-container {padding-left:1rem; padding-right:1rem;}
 .hero {padding:1.3rem;} .hero h1 {font-size:1.55rem !important;}
}
</style>
""", unsafe_allow_html=True)


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


def hero(title: str, description: str, eyebrow: str) -> None:
    st.markdown(f'<div class="hero"><div class="eyebrow">{escape(eyebrow)}</div>'
                f'<h1>{escape(title)}</h1><p>{escape(description)}</p></div>', unsafe_allow_html=True)


def section(title: str, description: str = "") -> None:
    st.subheader(title)
    if description:
        st.markdown(f'<p class="section-note">{escape(description)}</p>', unsafe_allow_html=True)


def chart_theme(chart):
    return (chart.configure_view(strokeOpacity=0)
            .configure_axis(labelColor="#52637b", titleColor="#52637b", gridColor="#e9eef5", labelFontSize=12, titleFontSize=12)
            .configure_legend(labelColor="#52637b", titleColor="#52637b"))


def show_chart(chart, description: str) -> None:
    st.altair_chart(chart_theme(chart), width="stretch", alt=description)


def rate_chart(summary: pd.DataFrame, height: int = 260):
    base = alt.Chart(summary).encode(
        y=alt.Y("group:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
        x=alt.X("rate:Q", title="Tỷ lệ rời bỏ trong nhóm", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%")),
        tooltip=[alt.Tooltip("group:N", title="Nhóm"), alt.Tooltip("customers:Q", title="Khách hàng", format=","),
                 alt.Tooltip("churned:Q", title="Đã rời bỏ", format=","), alt.Tooltip("rate:Q", title="Tỷ lệ", format=".1%")])
    return (base.mark_bar(color=TEAL, cornerRadiusEnd=5, size=25)
            + base.mark_text(align="left", dx=6, color="#172b4d").encode(text=alt.Text("rate:Q", format=".1%"))).properties(height=height)


def scores_for(name: str) -> dict:
    group, variant, _ = MODEL_NAMES[name]
    return metrics[group][variant] if variant else metrics[group]


def display_stats(frame: pd.DataFrame) -> None:
    cols = st.columns(4)
    values = [
        ("Khách hàng đang xem", f"{len(frame):,}", "Số khách sau các bộ lọc trên trang này."),
        ("Tỷ lệ rời bỏ thực tế", f"{frame.Churn.eq('Yes').mean():.1%}", "Số nhãn Yes / số khách đang xem."),
        ("Thời gian sử dụng TB", f"{frame.tenure.mean():.1f} tháng", "Trung bình tenure của tập đang xem."),
        ("Phí hàng tháng TB", f"{frame.MonthlyCharges.mean():.2f}", "Đơn vị tiền gốc trong dữ liệu IBM; không quy đổi sang VND.")]
    for col, (label, value, help_text) in zip(cols, values):
        col.metric(label, value, help=help_text)


def overview() -> None:
    hero("Hiểu dữ liệu. Nhận diện nguy cơ rời bỏ.",
         "Theo dõi hiện trạng khách hàng, kiểm tra chất lượng mô hình và thử dự đoán trên một hồ sơ mới. "
         "Bắt đầu từ bức tranh chung, sau đó dùng menu bên trái để đi sâu vào từng phần.", "TELCO CUSTOMER CHURN / TỔNG QUAN")
    churned = int(df.Churn.eq("Yes").sum())
    cards = [
        ("Khách hàng hợp lệ", f"{len(df):,}", "Số khách còn lại sau làm sạch, trên toàn bộ dữ liệu."),
        ("Đã rời bỏ", f"{churned:,}", "Số khách có nhãn thực tế Churn=Yes, không phải dự đoán."),
        ("Tỷ lệ rời bỏ thực tế", f"{churned / len(df):.1%}", "Số khách đã rời bỏ / tổng số khách hợp lệ."),
        ("Recall mô hình · test", f"{scores_for('Logistic điều chỉnh')['recall_churn_1']:.1%}", METRIC_HELP["recall_churn_1"])]
    for col, (label, value, help_text) in zip(st.columns(4), cards):
        col.metric(label, value, help=help_text)
    quality = metrics["data_quality"]
    st.caption(f"Phạm vi: toàn bộ dữ liệu IBM đã làm sạch · {quality['so_dong_ban_dau']:,} dòng gốc "
               f"→ {len(df):,} dòng hợp lệ · Loại {quality['so_dong_bi_loai']:,} dòng.")
    left, right = st.columns([.9, 1.35], gap="large")
    with left, st.container(border=True):
        section("Khách hàng đang ở đâu?", "Cơ cấu nhãn thực tế trong bộ dữ liệu.")
        counts = pd.DataFrame({"Trạng thái": ["Ở lại", "Đã rời bỏ"], "Số khách": [len(df) - churned, churned]})
        counts["Tỷ lệ"] = counts["Số khách"] / len(df)
        donut = (alt.Chart(counts).mark_arc(innerRadius=75, outerRadius=110, cornerRadius=3)
                 .encode(theta=alt.Theta("Số khách:Q"), color=alt.Color("Trạng thái:N", scale=alt.Scale(
                     domain=["Ở lại", "Đã rời bỏ"], range=[BLUE, RED]), legend=alt.Legend(orient="bottom", title=None)),
                     tooltip=["Trạng thái:N", alt.Tooltip("Số khách:Q", format=","), alt.Tooltip("Tỷ lệ:Q", format=".1%")]).properties(height=260))
        show_chart(donut, "Cơ cấu khách ở lại và đã rời bỏ.")
        st.caption("Rê chuột lên biểu đồ để xem số khách và tỷ lệ của từng nhóm.")
    with right, st.container(border=True):
        section("Tỷ lệ rời bỏ theo hợp đồng", "So sánh tỷ lệ trong từng nhóm, luôn đọc kèm số lượng khách.")
        summary = group_summary(df, "Contract")
        show_chart(rate_chart(summary), "Tỷ lệ Churn theo ba loại hợp đồng.")
        highest = summary.iloc[0]
        st.info(f"Nhóm {highest['group'].lower()} có tỷ lệ rời bỏ quan sát cao nhất: "
                f"{highest['rate']:.1%}, trên {int(highest['customers']):,} khách.")
    a, b = st.columns(2, gap="large")
    with a, st.container(border=True):
        section("Dữ liệu đã được xử lý thế nào?")
        st.write("Chuyển các cột số về đúng kiểu, xử lý phí tích lũy trống và kiểm tra mã khách trùng trước khi phân tích.")
        missing = quality.get("missing_theo_cot_ban_dau", {})
        st.markdown(f"**Giá trị thiếu:** {', '.join(f'{k}: {v}' for k, v in missing.items()) or 'Không có'}  \n"
                    f"**Mã khách trùng:** {quality.get('so_customerID_trung', 0):,}  \n**Một dòng dữ liệu:** một khách hàng.")
    with b, st.container(border=True):
        section("Cách đọc dashboard")
        st.markdown("**1. Khám phá dữ liệu:** lọc khách hàng và so sánh các nhóm.  \n"
                    "**2. Đánh giá mô hình:** xem cảnh báo đúng, cảnh báo sai và bỏ sót.  \n"
                    "**3. Dự đoán Churn:** nhập hồ sơ hoặc tải CSV để chấm điểm.")
        st.caption("Thống kê lịch sử và dự đoán là hai loại thông tin khác nhau. Mối liên hệ quan sát chưa chứng minh quan hệ nhân quả.")


def exploration() -> None:
    hero("Khám phá từng nhóm khách hàng", "Bộ lọc chỉ áp dụng cho thống kê trên trang này. "
         "Mô hình và các kết quả đánh giá đã lưu không thay đổi theo bộ lọc.", "DỮ LIỆU / PHÂN TÍCH TƯƠNG TÁC")
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
    with st.container(border=True):
        section("Chọn phạm vi dữ liệu")
        a, b = st.columns(2)
        contract = a.multiselect("Loại hợp đồng", all_contracts, format_func=value_label, key="filter_contract")
        internet = b.multiselect("Loại Internet", all_internet, format_func=lambda x: "Không có Internet" if x == "No" else value_label(x), key="filter_internet")
        churn = a.multiselect("Trạng thái thực tế", ["No", "Yes"], format_func=lambda x: "Đã rời bỏ" if x == "Yes" else "Ở lại", key="filter_churn")
        tenure = b.slider("Thời gian sử dụng (tháng)", min_tenure, max_tenure, key="filter_tenure") if min_tenure < max_tenure else (min_tenure, max_tenure)
        st.button("Đặt lại bộ lọc", on_click=reset_filters)
    filtered = df.loc[df.Contract.isin(contract) & df.InternetService.isin(internet)
                      & df.Churn.isin(churn) & df.tenure.between(*tenure)].copy()
    if filtered.empty:
        st.warning("Không có khách hàng phù hợp. Hãy chọn thêm nhóm hoặc bấm Đặt lại bộ lọc.")
        return
    display_stats(filtered)
    st.caption(f"Đang xem {len(filtered):,}/{len(df):,} khách hàng. Biểu đồ dưới đây được tính lại từ tập này.")
    groups, distributions, details = st.tabs(["Nhóm khách hàng", "Phân bố & tương quan", "Dữ liệu chi tiết"])
    with groups:
        feature = st.selectbox("So sánh theo thuộc tính", ["Contract", "InternetService", "PaymentMethod", "TechSupport", "OnlineSecurity", "SeniorCitizen", "Dependents", "PaperlessBilling"], format_func=lambda x: FIELD_LABELS[x])
        summary = group_summary(filtered, feature)
        a, b = st.columns([1.3, 1], gap="large")
        with a:
            show_chart(rate_chart(summary, max(230, len(summary) * 55)), "Tỷ lệ rời bỏ theo thuộc tính đang chọn.")
        with b:
            shown = summary[["group", "customers", "churned", "rate"]].rename(columns={"group": "Nhóm", "customers": "Số khách", "churned": "Đã rời bỏ", "rate": "Tỷ lệ rời bỏ"})
            st.dataframe(shown.style.format({"Tỷ lệ rời bỏ": "{:.1%}"}), hide_index=True, width="stretch")
            st.caption("Tỷ lệ = số người rời bỏ / số khách của chính nhóm đó. Nhóm ít khách có thể cho tỷ lệ dao động lớn.")
    with distributions:
        numeric = st.selectbox("Biến số muốn quan sát", NUMERIC, format_func=lambda x: FIELD_LABELS[x])
        plot_data = filtered[[numeric, "Churn"]].copy()
        plot_data["Trạng thái"] = plot_data.Churn.map({"No": "Ở lại", "Yes": "Đã rời bỏ"})
        color = alt.Color("Trạng thái:N", scale=alt.Scale(domain=["Ở lại", "Đã rời bỏ"], range=[BLUE, RED]), legend=alt.Legend(orient="bottom", title=None))
        a, b = st.columns(2, gap="large")
        with a, st.container(border=True):
            section("Phân bố giá trị", "Mỗi cột đếm số khách trong một khoảng giá trị.")
            hist = alt.Chart(plot_data).mark_bar(opacity=.7, binSpacing=1).encode(
                x=alt.X(f"{numeric}:Q", bin=alt.Bin(maxbins=24), title=FIELD_LABELS[numeric]), y=alt.Y("count():Q", title="Số khách", stack=None), color=color,
                tooltip=["Trạng thái:N", alt.Tooltip("count():Q", title="Số khách")]).properties(height=280)
            show_chart(hist, "Histogram so sánh phân bố giữa khách ở lại và đã rời bỏ.")
        with b, st.container(border=True):
            section("So sánh trung vị & độ phân tán", "Hộp bao phủ 50% quan sát ở giữa; đường trong hộp là trung vị.")
            box = alt.Chart(plot_data).mark_boxplot(extent=1.5, size=50).encode(x=alt.X("Trạng thái:N", title=None), y=alt.Y(f"{numeric}:Q", title=FIELD_LABELS[numeric]), color=color).properties(height=280)
            show_chart(box, "Boxplot theo nhãn Churn.")
        section("Tương quan giữa ba biến số", "Pearson đo liên hệ tuyến tính từ −1 đến +1; không chứng minh quan hệ nhân quả.")
        corr = filtered[NUMERIC].corr().rename(index=FIELD_LABELS, columns=FIELD_LABELS)
        corr_data = corr.rename_axis("Biến hàng").reset_index().melt("Biến hàng", var_name="Biến cột", value_name="Hệ số")
        heat = alt.Chart(corr_data).encode(x=alt.X("Biến cột:N", title=None, axis=alt.Axis(labelAngle=0, labelLimit=180)), y=alt.Y("Biến hàng:N", title=None))
        heatmap = heat.mark_rect().encode(color=alt.Color("Hệ số:Q", scale=alt.Scale(domain=[-1, 1], scheme="redblue")), tooltip=["Biến hàng:N", "Biến cột:N", alt.Tooltip("Hệ số:Q", format=".3f")])
        labels = heat.mark_text(fontSize=15, color="#172b4d").encode(text=alt.Text("Hệ số:Q", format=".2f"))
        show_chart((heatmap + labels).properties(height=240), "Ma trận Pearson trên tập dữ liệu đang lọc.")
        if filtered[NUMERIC].nunique().lt(2).any() or len(filtered) < 3:
            st.caption("Một số hệ số có thể không xác định vì quá ít quan sát hoặc biến không thay đổi.")
        with st.expander("Xem hình EDA và kiểm định đã lưu trên toàn bộ dữ liệu"):
            st.info("Các kết quả trong phần mở rộng này thuộc toàn bộ dữ liệu của lần chạy pipeline; không thay đổi theo bộ lọc phía trên.")
            figures = {"Tương quan Spearman với Churn": "06_spearman_churn.png", "Histogram ba biến số": "02_numeric_histograms.png", "Boxplot ba biến theo Churn": "03_boxplots_by_churn.png", "Ma trận Pearson gốc": "04_numeric_correlation.png"}
            artifact = st.selectbox("Hình phân tích", list(figures))
            image_path = OUTPUT / "figures" / figures[artifact]
            if image_path.exists():
                st.image(str(image_path), width="stretch")
            st.caption("Spearman dương: đặc trưng tăng/hiện diện đi cùng Churn nhiều hơn; âm: chiều ngược lại. Dấu phụ thuộc cách mã hóa.")
            method = st.selectbox("Kiểm định / thước đo", ["ANOVA F", "Chi-square", "Mutual Information"])
            filename, explanation = {
                "ANOVA F": ("feature_anova.csv", "Kiểm tra sự khác biệt trung bình của biến số giữa hai nhóm Churn. P-value nhỏ là bằng chứng về khác biệt theo giả thuyết của kiểm định."),
                "Chi-square": ("feature_chi_square.csv", "Đo liên hệ giữa đặc trưng mã hóa không âm và Churn bằng sklearn chi2. P-value không phải xác suất một biến gây ra Churn."),
                "Mutual Information": ("feature_mutual_information.csv", "Ước lượng thông tin của một biến về nhãn; có thể bắt liên hệ phi tuyến. MI không có dấu và không phải tỷ lệ phần trăm.")}[method]
            st.write(explanation)
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
        st.caption(f"Bảng đang hiển thị {len(preview):,}/{len(searched):,} kết quả sau bộ lọc và tìm kiếm. CSV giữ tên cột gốc.")
        st.download_button("Tải dữ liệu đã lọc CSV", csv_bytes(searched), "telco_filtered.csv", "text/csv")


def model_evaluation() -> None:
    hero("Đọc đúng chất lượng mô hình", "So sánh trên tập kiểm tra, xem số khách bị bỏ sót và số cảnh báo sai. "
         "Chỉ số dưới đây thuộc lần huấn luyện đã lưu, không thay đổi theo bộ lọc dữ liệu.", "MÔ HÌNH / ĐÁNH GIÁ")
    comparison = pd.DataFrame({name: scores_for(name) for name in MODEL_NAMES}).T[list(METRIC_LABELS)]
    left, right = st.columns([1, 1.2], gap="large")
    with left:
        criterion = st.selectbox("Chỉ số so sánh", list(METRIC_LABELS), format_func=lambda x: METRIC_LABELS[x])
        st.caption(METRIC_HELP[criterion])
        comparison_plot = comparison[criterion].rename("value").rename_axis("model").reset_index()
        base = alt.Chart(comparison_plot).encode(y=alt.Y("model:N", title=None, sort="-x"),
            x=alt.X("value:Q", title=None, scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%" if criterion != "roc_auc" else ".1f")),
            tooltip=[alt.Tooltip("model:N", title="Mô hình"), alt.Tooltip("value:Q", title="Chỉ số", format=".3f")])
        show_chart((base.mark_bar(color=TEAL, cornerRadiusEnd=5, size=28) + base.mark_text(align="left", dx=5).encode(text=alt.Text("value:Q", format=".1%" if criterion != "roc_auc" else ".3f"))).properties(height=220), "So sánh ba mô hình theo chỉ số đang chọn.")
    with right, st.container(border=True):
        section("Chọn chỉ số theo câu hỏi cần trả lời")
        st.markdown("**Accuracy:** tổng thể dự đoán đúng bao nhiêu?  \n"
                    "**Precision:** cảnh báo rời bỏ đáng tin đến mức nào?  \n"
                    "**Recall:** đã phát hiện được bao nhiêu khách rời bỏ?  \n"
                    "**F1:** Precision và Recall cân bằng ra sao?  \n"
                    "**ROC AUC:** mô hình phân biệt hai nhóm tốt đến đâu?")
        st.caption("Dự đoán khách hàng mới dùng Logistic điều chỉnh theo thiết kế dự án. Mô hình này không nhất thiết cao nhất ở mọi chỉ số.")
    section("Bảng so sánh trên tập test", "Bốn chỉ số đầu hiển thị theo %; ROC AUC hiển thị trên thang 0–1.")
    short_names = {key: label.split(" · ")[0] for key, label in METRIC_LABELS.items()}
    formats = {name: "{:.1%}" if key != "roc_auc" else "{:.3f}" for key, name in short_names.items()}
    st.dataframe(comparison.rename(columns=short_names).style.format(formats), width="stretch")
    selected = st.selectbox("Xem chi tiết mô hình", list(MODEL_NAMES))
    selected_scores = scores_for(selected)
    for col, (key, label) in zip(st.columns(5), METRIC_LABELS.items()):
        col.metric(label.split(" · ")[0], f"{selected_scores[key]:.3f}" if key == "roc_auc" else f"{selected_scores[key]:.1%}", help=METRIC_HELP[key])
    results, interpretation = st.tabs(["Ma trận nhầm lẫn & CV", "Đặc trưng & phương pháp"])
    with results:
        tag = MODEL_NAMES[selected][2]
        report_path = OUTPUT / "tables" / f"classification_report_{tag}.txt"
        if report_path.exists():
            try:
                counts = confusion_from_report(selected_scores, report_path.read_text(encoding="utf-8"))
            except ValueError as exc:
                st.warning(str(exc))
            else:
                a, b = st.columns([1, 1.05], gap="large")
                with a, st.container(border=True):
                    section("Ma trận nhầm lẫn", "Hàng: thực tế. Cột: dự đoán. Mỗi ô là số khách hàng.")
                    matrix = pd.DataFrame([{"Thực tế": actual, "Dự đoán": predicted, "Số khách": counts[key], "Loại": key.upper()}
                        for actual, predicted, key in [("Ở lại", "Ở lại", "tn"), ("Ở lại", "Rời bỏ", "fp"), ("Rời bỏ", "Ở lại", "fn"), ("Rời bỏ", "Rời bỏ", "tp")]])
                    base = alt.Chart(matrix).encode(x=alt.X("Dự đoán:N", sort=["Ở lại", "Rời bỏ"], title="Dự đoán"), y=alt.Y("Thực tế:N", sort=["Ở lại", "Rời bỏ"], title="Thực tế"))
                    cells = base.mark_rect(cornerRadius=8, stroke="white", strokeWidth=5).encode(color=alt.Color("Số khách:Q", scale=alt.Scale(range=["#edf4f6", "#63b6b5"]), legend=None), tooltip=["Thực tế:N", "Dự đoán:N", "Số khách:Q", "Loại:N"])
                    numbers = base.mark_text(fontSize=29, fontWeight=700, color="#172b4d").encode(text="Số khách:Q")
                    show_chart((cells + numbers).properties(height=270), "Ma trận nhầm lẫn hai lớp ở lại và rời bỏ.")
                with b:
                    section("Bốn kết quả cần hiểu")
                    c1, c2 = st.columns(2)
                    c1.metric("TP · Phát hiện đúng rời bỏ", f"{counts['tp']:,}")
                    c2.metric("FN · Bỏ sót khách rời bỏ", f"{counts['fn']:,}")
                    c1.metric("FP · Cảnh báo sai", f"{counts['fp']:,}")
                    c2.metric("TN · Nhận diện đúng ở lại", f"{counts['tn']:,}")
                    positives, alerts = counts["tp"] + counts["fn"], counts["tp"] + counts["fp"]
                    st.write(f"Trong **{positives:,} khách thực sự rời bỏ**, mô hình phát hiện **{counts['tp']:,}** và bỏ sót **{counts['fn']:,}**. Có **{alerts:,} cảnh báo**, trong đó **{counts['fp']:,}** là cảnh báo sai.")
                    st.caption(f"Tổng cộng {sum(counts.values()):,} khách kiểm tra. Số đếm được khôi phục từ support trong báo cáo và metrics JSON của cùng lần chạy.")
        else:
            st.info("Chưa có báo cáo phân loại chi tiết. Chạy lại pipeline để tạo bảng và ma trận.")
        if "cv_recall_each_fold" in selected_scores:
            with st.container(border=True):
                section("Độ ổn định qua 5 lần kiểm tra chéo", "CV chỉ dùng tập train; mỗi fold giữ riêng một phần để đánh giá. Đây không phải năm lần đánh giá trên tập test.")
                folds = pd.DataFrame({"Fold": [f"Fold {i + 1}" for i in range(len(selected_scores['cv_recall_each_fold']))], "Recall": selected_scores["cv_recall_each_fold"]})
                a, b = st.columns([1.5, 1])
                with a:
                    cv = alt.Chart(folds).mark_bar(color=BLUE, cornerRadiusEnd=4).encode(x=alt.X("Fold:N", title=None, axis=alt.Axis(labelAngle=0)), y=alt.Y("Recall:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%")), tooltip=["Fold:N", alt.Tooltip("Recall:Q", format=".1%")]).properties(height=200)
                    show_chart(cv, "Recall của năm fold cross-validation.")
                with b:
                    st.metric("Recall CV trung bình", f"{selected_scores['cv_recall_mean']:.1%}")
                    st.metric("Accuracy CV trung bình", f"{selected_scores['cv_accuracy_mean']:.1%}")
        else:
            st.caption("Pipeline hiện tại không tính CV cho cây quyết định; kết quả phía trên là trên tập test holdout.")
    with interpretation:
        section("Mô hình đang học theo quy trình nào?")
        st.info("Chia dữ liệu 80% train / 20% test, phân tầng theo Churn và dùng random_state=42. Với Logistic: SMOTE → chuẩn hóa → huấn luyện, tất cả nằm trong pipeline của từng fold. Tập test giữ nguyên, không SMOTE.")
        st.write("SMOTE sinh mẫu nội suy để cân bằng lớp trên dữ liệu huấn luyện. Vì phân bố lớp khi học đã thay đổi, điểm đầu ra chưa được hiệu chuẩn thành xác suất rời bỏ thực tế.")
        if selected.startswith("Logistic"):
            filename = "logistic_selected_coefficients.csv" if selected == "Logistic điều chỉnh" else "logistic_full_coefficients.csv"
            coefficients = table(filename)
            if not coefficients.empty:
                coefficients["Đặc trưng"] = coefficients.feature.map(feature_label)
                coefficients["Chiều tác động"] = coefficients.coefficient_scaled.map(lambda x: "Tăng điểm" if x >= 0 else "Giảm điểm")
                section("Hệ số Logistic đã chuẩn hóa", "Dấu dương đẩy điểm về phía Churn; dấu âm đẩy theo chiều ngược lại khi giữ các đặc trưng khác không đổi.")
                coef = alt.Chart(coefficients).mark_bar(cornerRadiusEnd=3).encode(
                    y=alt.Y("Đặc trưng:N", sort=alt.SortField("coefficient_scaled"), title=None, axis=alt.Axis(labelLimit=260)), x=alt.X("coefficient_scaled:Q", title="Hệ số trên đặc trưng chuẩn hóa"),
                    color=alt.Color("Chiều tác động:N", scale=alt.Scale(domain=["Giảm điểm", "Tăng điểm"], range=[BLUE, RED]), legend=alt.Legend(orient="bottom")), tooltip=["Đặc trưng:N", alt.Tooltip("coefficient_scaled:Q", title="Hệ số", format=".3f")]).properties(height=max(350, len(coefficients) * 25))
                show_chart(coef, "Chiều và độ lớn hệ số của mô hình Logistic đang chọn.")
                st.caption("Đây là giải thích toàn cục, không phải đóng góp riêng cho một hồ sơ. Hệ số không phải phần trăm rủi ro và không chứng minh quan hệ nhân quả.")
            if selected == "Logistic điều chỉnh":
                st.write("Mô hình dùng **16 đặc trưng mã hóa từ 12 cột gốc**. Các nhóm tham chiếu: Internet DSL, hợp đồng một năm, thanh toán séc điện tử; biến Yes/No dùng 1/0 và Female/Male dùng 0/1.")
        else:
            section("Cây quyết định sâu tối đa 4")
            tree_image = OUTPUT / "figures" / "decision_tree.png"
            if tree_image.exists():
                st.image(str(tree_image), width="stretch")
                st.download_button("Tải hình cây để phóng to", tree_image.read_bytes(), "decision_tree.png", "image/png")
            st.caption("Nút chứa điều kiện phân nhánh; gini đo độ trộn lớp; samples là số mẫu train. Cách biểu diễn value phụ thuộc phiên bản sklearn.")
            with st.expander("Luật phân nhánh và nhóm lá trên tập test"):
                rules = OUTPUT / "tables" / "decision_tree_rules.txt"
                if rules.exists():
                    st.code(rules.read_text(encoding="utf-8"))
                leaves = table("tree_risk_groups_test.csv")
                if not leaves.empty:
                    st.dataframe(leaves.rename(columns={"leaf_id": "Mã lá", "customers": "Số khách test", "actual_churn_rate": "Tỷ lệ rời bỏ thực tế", "mean_model_score": "Điểm mô hình trung bình"}).style.format({"Tỷ lệ rời bỏ thực tế": "{:.1%}", "Điểm mô hình trung bình": "{:.1%}"}), hide_index=True, width="stretch")
        with st.expander("OLS và thống kê suy diễn: đọc khác với chỉ số Churn"):
            st.write("**OLS giải thích MonthlyCharges (phí hàng tháng)**. Không so sánh R² OLS với Accuracy để chọn mô hình Churn.")
            ols = pd.DataFrame(metrics["linear_regression"]).T.rename(index={"full": "OLS đầy đủ", "selected": "OLS điều chỉnh"})
            st.dataframe(ols.rename(columns={"r2_train": "R² train", "r2_test": "R² test", "mae_test": "MAE test", "rmse_test": "RMSE test"}).style.format("{:.3f}"), width="stretch")
            st.caption("R² đo mức giải thích biến thiên phí; MAE là sai số tuyệt đối trung bình; RMSE phạt sai số lớn mạnh hơn. MAE và RMSE giữ đơn vị phí gốc.")
            pseudo = scores_for("Logistic điều chỉnh").get("mcfadden_pseudo_r2_train")
            if pseudo is not None:
                st.write(f"**McFadden pseudo R² Logistic (train gốc): {pseudo:.3f}.** Đây là so sánh log-likelihood; không diễn giải thành phần trăm phương sai Churn được giải thích.")
            statistical = st.selectbox("Bảng thống kê muốn xem", ["VIF OLS điều chỉnh", "Hệ số / p-value Logit", "VIF Logit"])
            stat_file = {"VIF OLS điều chỉnh": "ols_selected_vif.csv", "Hệ số / p-value Logit": "logit_selected_statsmodels_coefficients.csv", "VIF Logit": "logit_selected_vif.csv"}[statistical]
            stat_data = table(stat_file)
            if not stat_data.empty:
                st.dataframe(stat_data, hide_index=True, width="stretch")
            st.caption("VIF giúp xem đa cộng tuyến. P-value statsmodels được tính trên train gốc không SMOTE, khác classifier sklearn dùng để dự đoán.")


def render_prediction_result(result: pd.DataFrame) -> None:
    row = result.iloc[0]
    score = float(row.churn_risk_score)
    label = "Dự đoán rời bỏ" if row.predicted_churn == "Yes" else "Dự đoán ở lại"
    group = RISK_LABELS[row.risk_group]
    st.markdown(f'<div class="result-card"><strong>{escape(label)}</strong><br>Hồ sơ: {escape(str(row.get("customerID", "Khách hàng vừa nhập")))} · Mức rủi ro {escape(group.lower())}</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.metric("Điểm rủi ro · chưa hiệu chuẩn", f"{score:.1%}", help="Điểm mô hình, không phải xác suất rời bỏ đã được kiểm chứng.")
    b.metric("Mức rủi ro", group, help="Thấp ≤0,3; Trung bình >0,3 đến 0,6; Cao >0,6.")
    c.metric("Nhãn dự đoán", "Yes · Rời bỏ" if row.predicted_churn == "Yes" else "No · Ở lại", help="Ngưỡng phân loại là 0,5 trên điểm chưa làm tròn.")
    st.progress(min(max(score, 0), 1), text="Thang điểm 0 → 1 · Ngưỡng nhãn: 0,5 · Phân nhóm rủi ro: 0,3 / 0,6")
    st.info("Điểm được hiển thị dạng % để dễ đọc. Vì mô hình dùng SMOTE và chưa hiệu chuẩn, điểm này chưa phải xác suất rời bỏ thực tế và không cho biết khách sẽ rời bỏ sau bao lâu.")
    st.caption("Kết quả thuộc hồ sơ ở lần bấm Dự đoán nguy cơ gần nhất. Sau khi sửa biểu mẫu, hãy bấm lại để cập nhật.")
    with st.expander("Kiểm tra hồ sơ vừa gửi"):
        fields = [col for col in result.columns if col in FIELD_LABELS]
        profile = pd.DataFrame({"Thông tin": [FIELD_LABELS[col] for col in fields], "Giá trị": [value_label(row[col]) for col in fields]})
        st.dataframe(profile, hide_index=True, width="stretch")
    st.download_button("Tải kết quả khách hàng CSV", csv_bytes(result), "customer_prediction.csv", "text/csv", key="download_single")


def single_prediction() -> None:
    options = ["Nhập hồ sơ mới", "DEMO001 · thời gian ngắn", "DEMO002 · hợp đồng dài hạn", "DEMO003 · hồ sơ hỗn hợp"]
    scenario = st.selectbox("Bắt đầu từ hồ sơ", options, key="scenario")
    defaults = {"customerID": "KH001", "gender": "Female", "Dependents": "No", "tenure": 6, "PhoneService": "Yes", "InternetService": "Fiber optic", "OnlineSecurity": "No", "OnlineBackup": "No", "DeviceProtection": "No", "TechSupport": "No", "PaperlessBilling": "Yes", "Contract": "Month-to-month", "PaymentMethod": "Electronic check"}
    if scenario != options[0]:
        sample_path = ROOT / "data" / "new_customers_example.csv"
        examples = load_csv(str(sample_path), sample_path.stat().st_mtime_ns)
        defaults = examples.iloc[options.index(scenario) - 1].to_dict()
    if st.session_state.get("last_scenario") != scenario or "customer_gender" not in st.session_state:
        for key, value in defaults.items():
            st.session_state["customer_" + key] = int(value) if key == "tenure" else str(value)
        st.session_state["last_scenario"] = scenario
        st.session_state.pop("single_result", None)
    with st.form("customer"):
        a, b, c = st.columns(3, gap="large")
        with a:
            section("01 · Hồ sơ khách hàng")
            customer_id = st.text_input("Mã khách hàng (tùy chọn)", key="customer_customerID")
            gender = st.selectbox("Giới tính", ["Female", "Male"], format_func=value_label, key="customer_gender")
            dependents = st.selectbox("Có người phụ thuộc", ["No", "Yes"], format_func=value_label, key="customer_Dependents")
            tenure = st.number_input("Thời gian đã sử dụng (tháng)", min_value=0, max_value=120, step=1, key="customer_tenure", help="tenure là số tháng sử dụng, không phải tuổi khách hàng.")
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
        st.caption("Nếu không có Internet, chọn Không cho bảo mật, sao lưu, bảo vệ thiết bị và hỗ trợ kỹ thuật.")
        submitted = st.form_submit_button("Dự đoán nguy cơ", type="primary", width="stretch")
    if submitted:
        sample = pd.DataFrame([{"customerID": customer_id, "gender": gender, "Dependents": dependents, "tenure": tenure, "PhoneService": phone, "InternetService": internet, "OnlineSecurity": security, "OnlineBackup": backup, "DeviceProtection": protection, "TechSupport": support, "PaperlessBilling": billing, "Contract": contract, "PaymentMethod": payment}])
        try:
            validate_prediction_data(sample)
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
        st.info("Điền thông tin hoặc chọn một hồ sơ mẫu, sau đó bấm Dự đoán nguy cơ để xem kết quả tại đây.")


def batch_prediction() -> None:
    sample_path = ROOT / "data" / "new_customers_example.csv"
    a, b = st.columns([1.5, 1], gap="large")
    with a:
        section("Tải danh sách khách hàng", "Dùng CSV phân cách bằng dấu phẩy. Giữ nguyên tên cột tiếng Anh như file mẫu.")
        upload = st.file_uploader("Chọn file CSV", type=["csv"], key="customer_upload")
        analyze = st.button("Phân tích CSV", type="primary", disabled=upload is None)
    with b, st.container(border=True):
        section("Thử nhanh với dữ liệu có sẵn")
        st.write("Ba hồ sơ khác nhau giúp bạn quan sát cách mô hình chấm điểm.")
        run_example = st.button("Chạy thử 3 khách hàng mẫu")
        st.download_button("Tải CSV mẫu", sample_path.read_bytes(), "new_customers_example.csv", "text/csv")
    with st.expander("12 cột bắt buộc và cách nhập"):
        st.code("gender,Dependents,tenure,PhoneService,OnlineSecurity,OnlineBackup,DeviceProtection,TechSupport,PaperlessBilling,InternetService,PaymentMethod,Contract", language="text", wrap_lines=True)
        st.write("Có thể thêm customerID để giữ mã khách. Không cần cột Churn hoặc tự tạo dummy. Xem Hướng dẫn sử dụng → Dự đoán Churn để tra toàn bộ giá trị hợp lệ.")
    if run_example or analyze:
        st.session_state.pop("batch_result", None)
        try:
            new_df = pd.read_csv(sample_path if run_example else upload)
            validate_prediction_data(new_df)
            with st.spinner("Đang chấm điểm khách hàng..."):
                result = predict_dataframe(new_df)
            st.session_state["batch_result"] = result
            st.session_state["batch_source"] = sample_path.name if run_example else upload.name
        except (ValueError, FileNotFoundError, TypeError, UnicodeError) as exc:
            st.error(str(exc))
    if "batch_result" not in st.session_state:
        st.info("Chọn file và bấm Phân tích CSV, hoặc chạy thử ba hồ sơ mẫu.")
        return
    result = st.session_state["batch_result"]
    section("Kết quả lần dự đoán gần nhất", f"Nguồn: {st.session_state['batch_source']}. Thẻ tổng và file tải xuống luôn tính trên toàn bộ lần dự đoán.")
    a, b, c = st.columns(3)
    a.metric("Tổng khách đã chấm điểm", f"{len(result):,}")
    b.metric("Dự đoán rời bỏ · Yes", f"{result.predicted_churn.eq('Yes').sum():,}")
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
    st.caption(f"Hiển thị tối đa 500 dòng · {len(shown):,} khách khớp bộ lọc · Điểm cao được xếp trước. CSV xuất toàn bộ {len(result):,} khách.")
    st.download_button("Tải toàn bộ kết quả CSV", csv_bytes(result), "predictions.csv", "text/csv", type="primary")
    st.info("Điểm chưa hiệu chuẩn sau SMOTE. Nhãn Yes dùng ngưỡng 0,5; mức Cao dùng ngưỡng >0,6, nên hai cách phân loại có thể khác nhau.")


def predictions() -> None:
    hero("Từ hồ sơ khách hàng đến điểm rủi ro", "Chấm điểm bằng Logistic điều chỉnh đã được huấn luyện. Bạn có thể nhập một khách hàng hoặc xử lý một danh sách CSV, sau đó tải kết quả.", "DỰ ĐOÁN / LOGISTIC ĐIỀU CHỈNH")
    if not (OUTPUT / "models" / "logistic_selected.joblib").exists():
        st.error("Chưa có mô hình dự đoán. Chạy run_pipeline.py để tạo mô hình trước.")
        return
    mode = st.radio("Cách nhập dữ liệu", ["Một khách hàng", "Hàng loạt qua CSV"], horizontal=True, key="prediction_mode")
    if mode == "Một khách hàng":
        single_prediction()
    else:
        batch_prediction()


def guide_page() -> None:
    hero("Hiểu từng con số trước khi kết luận", "Tra cứu cách đọc biểu đồ, chỉ số mô hình, quy tắc dự đoán và định dạng dữ liệu. Bạn có thể tải toàn bộ tài liệu để đọc hoặc dùng khi thuyết trình.", "HƯỚNG DẪN / GIẢI THÍCH CHI TIẾT")
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
    with st.container(border=True):
        st.markdown(sections[topic])


with st.sidebar:
    st.markdown('<div class="brand">Telco<span>Churn</span></div><div class="brand-note">Phân tích khách hàng · PTIT</div>', unsafe_allow_html=True)
    page = st.radio("Điều hướng", PAGES, key="navigation", label_visibility="collapsed")
    st.divider()
    st.markdown("**Phạm vi dữ liệu**")
    st.caption("IBM Telco Customer Churn\n\nDữ liệu mẫu phục vụ nghiên cứu và thực hành.")
    if GUIDE.exists():
        st.download_button("Tải tài liệu hướng dẫn", GUIDE.read_bytes(), GUIDE.name, "text/markdown", key="sidebar_guide")

metrics_path = OUTPUT / "metrics.json"
data_path = ROOT / "data" / "processed" / "telco_clean.csv"
if page == "Hướng dẫn sử dụng":
    guide_page()
    st.stop()
if not metrics_path.exists() or not data_path.exists():
    st.error("Chưa có kết quả phân tích. Chạy các lệnh sau trong thư mục telco_churn_project:")
    st.code('.\\.venv\\Scripts\\python.exe download_data.py\n.\\.venv\\Scripts\\python.exe run_pipeline.py', language="powershell")
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
with st.sidebar:
    st.markdown(f'<div class="status">● Dữ liệu sẵn sàng<br><strong>{len(df):,} khách hàng hợp lệ</strong><br>Mô hình: Logistic điều chỉnh</div>', unsafe_allow_html=True)
    st.caption("Điểm mô hình chưa hiệu chuẩn xác suất. Xem hướng dẫn trước khi diễn giải.")

if page == "Tổng quan":
    overview()
elif page == "Khám phá dữ liệu":
    exploration()
elif page == "Đánh giá mô hình":
    model_evaluation()
elif page == "Dự đoán Churn":
    predictions()
