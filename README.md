# Telco Customer Churn – Bài tập lớn Kho dữ liệu & Khai phá dữ liệu

Dự án Python triển khai theo báo cáo **Khai phá dữ liệu về tỷ lệ rời bỏ khách hàng – Nhóm 1** được cung cấp. Đây là bản triển khai thực hành *tham chiếu phương pháp*, không cam kết tái tạo chính xác hệ số và số liệu do báo cáo nêu (vì cách chia tập và xử lý rò rỉ dữ liệu được cải tiến).

Hướng dẫn đầy đủ về từng trang, chỉ số, biểu đồ và định dạng CSV nằm trong [HUONG_DAN_GIAO_DIEN.md](HUONG_DAN_GIAO_DIEN.md). Dashboard mới có menu trái gồm **Mô tả dữ liệu**, **Thống kê mô tả**, **Kỹ thuật khai phá**, năm bước **Demo huấn luyện lại** và **Hướng dẫn sử dụng**. Có thể đọc và tải tài liệu ngay trong ứng dụng.

## 1. Chạy trên Windows 10/11 (VS Code, PowerShell)

Nên dùng **Python 3.11 hoặc 3.12** để giảm vấn đề tương thích gói. Từ terminal VS Code:

```powershell
# Đứng trong thư mục telco_churn_project
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python download_data.py
python run_pipeline.py
python predict.py --input data/new_customers_example.csv
streamlit run app.py
```

> Nếu PowerShell chặn `Activate.ps1`, không nhất thiết phải mở policy. Dùng thẳng `\.venv\Scripts\python.exe -m pip install -r requirements.txt` và `\.venv\Scripts\python.exe run_pipeline.py`. Để chạy Streamlit dùng `\.venv\Scripts\python.exe -m streamlit run app.py`.

Nếu không cài Python 3.12, cài từ python.org rồi lặp lại các lệnh.

## 2. Nguồn dữ liệu

- IBM mẫu Telco Customer Churn: <https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/Telco-Customer-Churn.csv>
- CSV gốc: <https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv>
- Thường có tên khác là `WA_Fn-UseC_-Telco-Customer-Churn.csv` ở Kaggle.
- 7.043 khách hàng, 21 trường, gồm nhãn `Churn`.

Bộ dữ liệu **không nằm trong file ZIP**. Script `download_data.py` tải từ IBM và kiểm tra SHA-256 nhằm xác minh file nguồn. Nếu máy không tải tự động được, tải bằng trình duyệt rồi chép CSV vào `data/raw/Telco-Customer-Churn.csv`.

## 3. Cấu trúc thư mục

```text
telco_churn_project/
├── download_data.py           # Tải và xác minh CSV IBM
├── run_pipeline.py            # Chạy toàn bộ pipeline từ đầu
├── predict.py                 # Dự đoán khách hàng mới từ CSV
├── app.py                     # Dashboard Streamlit
├── requirements.txt
├── src/
│   ├── schema.py              # Danh sách biến được chọn từ báo cáo
│   ├── data.py                # Đọc, làm sạch, mã hóa
│   ├── eda.py                 # Biểu đồ EDA
│   ├── feature_tests.py       # ANOVA F, Chi-square, MI
│   ├── evaluation.py          # Confusion matrix và metrics
│   └── models.py              # OLS, DecisionTree, Logistic + SMOTE
├── data/
│   ├── raw/                   # CSV gốc (tải về)
│   ├── processed/             # CSV sau làm sạch
│   └── new_customers_example.csv
├── outputs/
│   ├── figures/               # Biểu đồ PNG
│   ├── tables/                # Bảng số liệu CSV/TXT/JSON
│   ├── models/                # Model joblib
│   └── metrics.json
└── tests/
    ├── conftest.py            # Synthetic data CHỈ để kiểm thử
    └── test_pipeline.py
```

## 4. Đối chiếu từng chương trong báo cáo

| Báo cáo | Code | Kết quả |
|---|---|---|
| Chương 2 – Dữ liệu | `src/data.py`, `src/schema.py` | CSV sau làm sạch, báo cáo chất lượng |
| Chương 3 – Cleaning | `clean_dataset()` | Chuyển `TotalCharges` sang số, xóa 11 dòng trống theo dữ liệu IBM, kiểm tra trùng |
| Chương 4 – EDA | `src/eda.py`, `src/feature_tests.py` | Churn rate, histogram, boxplot, correlation, ANOVA/Chi2/MI |
| Chương 5 – One-hot encoding | `encode_features()` | Biến Yes/No → 1/0, Male/Female → 1/0, dummy các biến 3/4 mức |
| Chương 6.1 – Linear Regression | `run_linear_regression()` | 2 mô hình OLS, VIF, coefficient, p-value, R² train/test |
| Chương 6.2 – Decision Tree | `run_decision_tree()` | Cây max_depth=4, gini, các nhóm lá, luật phân nhánh, metrics test |
| Chương 6.3 – Logistic Regression | `run_logistic_regression()` | Mô hình đầy đủ / điều chỉnh, SMOTE, CV 5 folds, sklearn & statsmodels |
| Chương 7 – Đề xuất | `app.py` và `predict.py` | Nhận diện nhóm rủi ro; cơ sở cho kế hoạch giữ chân |

### Các đặc trưng quan trọng theo báo cáo

- **OLS điều chỉnh:** `MultipleLines`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`, `InternetService_No`, `InternetService_Fiber optic`, `Contract_Two year` (Bảng 5).
- **Cây quyết định:** `Contract_Month-to-month`, `tenure`, `Contract_Two year`, `InternetService_Fiber optic`, `MonthlyCharges`, `InternetService_No`, `PaymentMethod_Electronic check` (mục 6.2.2).
- **Hồi quy logistic (sau điều chỉnh):** 16 biến đúng Bảng 8, khai báo trong `src/schema.py`.

## 5. Những khác biệt kỹ thuật có chủ ý với cách viết trong báo cáo

1. **Train/test:** Decision Tree và OLS được đánh giá trên 20% dữ liệu holdout; không chỉ diễn giải trên tập train/toàn bộ dữ liệu.
2. **Không rò rỉ SMOTE:** SMOTE chỉ nằm trên training data và nằm **bên trong** pipeline cho từng fold cross-validation. Tập test không resample.
3. **Dummy trap:** Bỏ một dummy tham chiếu trong mỗi nhóm cho OLS và logistic full. Đối với các biến được lựa chọn, giữ đúng các cột mô hình điều chỉnh của báo cáo.
4. **Hồi quy phí:** `TotalCharges` không dùng để giải thích `MonthlyCharges` vì nó phản ánh tích lũy của chính khoản phí này; tránh liên hệ vòng tròn.
5. **p-value từ statsmodels:** fit trên **train thật, không qua SMOTE** để hạn chế suy diễn thống kê từ mẫu nội suy. Trong khi đó, classifier sklearn dự đoán vẫn dùng SMOTE như báo cáo. Vì vậy hệ số/p-value không nhất thiết bằng Bảng 8.
6. **McFadden pseudo R²** *không phải* phần trăm biến thiên Churn được giải thích như R² OLS. Diễn giải chỉ số theo tương quan likelihood.
7. **Ngưỡng phân loại mặc định = 0.5**. Vì SMOTE thay đổi tỷ lệ lớp khi train, cột `churn_risk_score` là **điểm nguy cơ mô hình chưa hiệu chuẩn**; không được hiểu ngay là xác suất rời bỏ chính xác trong thực tế.
8. Đây là **dữ liệu ảnh chụp một thời điểm**, không dùng để chứng minh rằng một chính sách retention *gây ra* việc giảm churn.

## 6. Kết quả và ý nghĩa

Sau `python run_pipeline.py`, xem:

- `outputs/metrics.json`: Accuracy, Precision, Recall lớp 1, F1 lớp 1, ROC AUC, và chỉ số OLS.
- `outputs/figures/decision_tree.png`: cây ra quyết định dựa theo báo cáo.
- `outputs/figures/confusion_logistic_selected.png`: ma trận nhầm lẫn sau điều chỉnh.
- `outputs/tables/ols_selected_vif.csv`: VIF giải thích biến phí hàng tháng.
- `outputs/tables/logit_selected_statsmodels_coefficients.csv`: hệ số, odds ratio, p-value.
- `outputs/tables/tree_risk_groups_test.csv`: nhóm lá cây trên tập test và tỷ lệ churn thực tế.
- `outputs/models/logistic_selected.joblib`: model học được để dự đoán khách hàng mới.

**Không cố định số lượng dự báo đúng hoặc hệ số OLS vào code**. Mọi số sẽ được tính bằng dữ liệu thật sau khi chạy, do đó có thể khác báo cáo.

## 7. Dự đoán khách hàng mới

```
python predict.py --input data/new_customers_example.csv --output outputs/predictions.csv
```

Cột đầu vào tối thiểu (12 cột):

```
gender,Dependents,tenure,PhoneService,OnlineSecurity,OnlineBackup,
DeviceProtection,TechSupport,PaperlessBilling,InternetService,
PaymentMethod,Contract
```

Có thể thêm `customerID` để giữ mã khách hàng. File kết quả chứa:

- `churn_risk_score`: điểm mô hình 0–1, **chưa hiệu chuẩn xác suất**;
- `predicted_churn`: `Yes` nếu điểm ≥ 0.5;
- `risk_group`: `Low` dưới 0.3, `Medium` từ 0.3 đến dưới 0.6, `High` từ 0.6 trở lên (ngưỡng minh họa kinh doanh, không tối ưu thống kê).

**Lưu ý:** Ba nhãn risk group là nhãn điều hành minh họa. Nếu dùng thật, cần xác định ngưỡng dựa trên ngân sách can thiệp, chi phí false positive/false negative và đánh giá hiệu chuẩn xác suất trên dữ liệu của doanh nghiệp.

## 8. Chạy test

```
python -m pytest tests -q
```

Tests dùng 250 khách hàng **giả lập**, chỉ xác minh chương trình hoạt động, **không thay thế bộ dữ liệu IBM** và không được dùng để viết kết quả nghiên cứu.

## 9. Phân công nhóm / hướng phát triển

- TV1: Cleaning, EDA, tương quan và kiểm định ANOVA/Chi-square/MI.
- TV2: OLS và Decision Tree, thống kê nhóm rủi ro.
- TV3: Logistic Regression, SMOTE, đánh giá, Dashboard, dự đoán.

Có thể mở rộng bằng việc hiệu chỉnh ngưỡng trên tập validation riêng, calibration, giải thích SHAP, cân nhắc SMOTENC với đặc trưng phân loại, quản lý thí nghiệm và triển khai FastAPI/React. Các phần mở rộng **không thuộc nội dung gốc** của báo cáo.
