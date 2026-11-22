# Nội dung slide chi tiết về dự đoán khách hàng rời bỏ dịch vụ viễn thông

Tài liệu dùng để xây dựng slide báo cáo bài tập lớn, bám vào mã nguồn và các kết quả đang lưu trong dự án tại thời điểm đối chiếu ngày 22/11/2026. Nội dung đi theo tiến trình của slide tham khảo: giới thiệu, dữ liệu, tiền xử lý, thuật toán, huấn luyện, đánh giá, cập nhật mô hình và demo.

Bản chi tiết gồm 24 slide. Mỗi slide tách phần đưa lên màn hình với phần giải thích cho người trình bày. Phụ lục cuối tài liệu cung cấp cách rút xuống 15 slide và các câu trả lời phản biện.

## 1 Phạm vi thực tế cần thống nhất trước khi dựng slide

### 1.1 Những điểm khác nhau giữa đề cương và chương trình

| Nội dung trong đề cương | Chương trình hiện tại | Cách trình bày chính xác |
|---|---|---|
| Dự đoán khách rời bỏ và điểm nguy cơ | Có Decision Tree và Logistic Regression phân loại `Churn`; ứng dụng xuất điểm, nhãn và nhóm rủi ro | Đã triển khai phân loại Churn và chấm điểm nguy cơ |
| Thử ba mô hình phân loại gồm Decision Tree, Logistic Regression, Linear Regression | Có ba họ mô hình, nhưng Linear Regression dự đoán `MonthlyCharges` | Hai mô hình phân loại Churn; hồi quy tuyến tính là phân tích bổ sung về phí hàng tháng |
| Xác nhận chéo 5 fold trên phần phát triển | Pipeline gốc chạy CV cho hai cấu hình Logistic; demo huấn luyện lại chạy CV cho cả Tree và Logistic | Nêu rõ CV áp dụng ở luồng nào, cho mô hình nào |
| Ưu tiên F1 để chọn rồi đánh giá trên test | Pipeline gốc lưu sẵn Logistic điều chỉnh; CV gốc đo Recall và Accuracy. Trang So sánh cho chọn tiêu chí, gồm F1, dựa trên chỉ số test đã lưu | Có so sánh theo F1 trên test; chưa có quy trình chọn mô hình theo F1 CV rồi kiểm thử cuối cùng độc lập |
| Lưu hồ sơ mới từ ứng dụng | Form dự đoán cho tải kết quả CSV; dữ liệu form ở session. Khi huấn luyện với CSV mới, có lưu `new_data.csv` trong thư mục lần chạy | Có xuất CSV dự đoán và lưu CSV mới của lần huấn luyện; chưa có kho hồ sơ dự đoán lưu bền vững |
| Cập nhật nhãn thực tế | Có thể nạp CSV đầy đủ đã sửa nhãn; khi trùng mã, bản ghi mới được ưu tiên | Cập nhật bằng CSV có nhãn; chưa có màn hình nhập nhãn thực tế cho từng hồ sơ đã dự đoán |
| Huấn luyện lại hàng tháng khi đủ dữ liệu | Người dùng bấm huấn luyện; có cấu hình và lưu lịch sử | Đã có huấn luyện lại theo đợt bằng thao tác người dùng; lịch tháng và điều kiện đủ dữ liệu là phần chưa triển khai |
| So sánh trước khi thay mô hình | Có bảng so sánh và nút chọn mô hình dùng dự đoán | Đã có cơ chế xem kết quả rồi chủ động kích hoạt mô hình; không tự động thay khi chạy xong |

Tên thuật toán viết đúng là **Linear Regression**, thay cho “Linner Regression”.

### 1.2 Hai luồng thực thi cần phân biệt

**Luồng phân tích gốc:** `run_pipeline.py` đọc CSV IBM, làm sạch, tạo EDA và kiểm định đặc trưng, chạy OLS, Decision Tree và hai cấu hình Logistic, rồi lưu kết quả trong `outputs/`. Bảng số liệu trong tài liệu lấy từ `outputs/metrics.json` và các bảng kết quả tương ứng.

**Luồng demo huấn luyện lại:** `app.py` gọi `src/retrain.py`, cho chọn dữ liệu, tiền xử lý, cấu hình mô hình, chạy huấn luyện, lưu từng lần vào `outputs/runs/`, so sánh và chọn mô hình. Tại thời điểm đối chiếu chưa có `run.json` trong thư mục này, nên không có số liệu thực nghiệm huấn luyện lại để đưa vào báo cáo. Chức năng được mô tả theo mã triển khai, không gán kết quả giả định.

## 2 Toàn bộ tiến trình của bài báo cáo

```text
Xác định bài toán và mục tiêu chăm sóc khách hàng
    → Đọc và mô tả IBM Telco Customer Churn
    → Làm sạch và khảo sát dữ liệu
    → Mã hóa và chọn bộ đặc trưng đã khai báo
    → Chia Train/Test
    → Cân bằng và chuẩn hóa theo từng mô hình
    → Huấn luyện và xác nhận chéo theo luồng thực thi
    → Đánh giá và giải thích kết quả
    → Dự đoán một khách hoặc một tệp CSV
    → Nạp CSV có nhãn để huấn luyện lại theo đợt
    → So sánh và chọn mô hình dùng cho dự đoán
```

Nhánh hồi quy tuyến tính sử dụng cùng dữ liệu khách hàng nhưng có mục tiêu riêng là phí hàng tháng. Nhánh này có thước đo riêng và không tham gia xếp hạng F1 của bài toán Churn.

## 3 Nội dung chi tiết từng slide

### Slide 1 Giới thiệu đề tài

**Nội dung đưa lên slide**

- Dự đoán khách hàng rời bỏ dịch vụ viễn thông.
- Bài toán phân loại nhị phân trên IBM Telco Customer Churn.
- Đầu ra: nhãn rời bỏ và điểm nguy cơ.
- Mục tiêu: hỗ trợ doanh nghiệp xác định hồ sơ cần ưu tiên chăm sóc.
- Tên môn học, nhóm, giảng viên: điền theo thông tin thực tế.

**Giải thích khi trình bày**

Nhóm sử dụng thông tin khách hàng, dịch vụ đăng ký, hợp đồng và thanh toán để học mối liên hệ với nhãn Churn. Ứng dụng trả về điểm nguy cơ để hỗ trợ sắp xếp danh sách cần xem xét. Kết quả là công cụ hỗ trợ ưu tiên, chưa phải bằng chứng rằng một chiến dịch chăm sóc sẽ làm khách ở lại.

**Minh họa:** ba khối “Hồ sơ khách hàng → Mô hình → Điểm và nhãn dự đoán”.

**Đối chiếu:** [predict.py](../../predict.py), [app.py](../../app.py).

### Slide 2 Phân công nhóm năm người

**Nội dung đưa lên slide**

| Thành viên | Phần việc theo phân công đề tài | Thành phần tương ứng |
|---|---|---|
| Thành viên 1 | Dữ liệu và tiền xử lý | Đọc CSV, làm sạch, mã hóa, EDA và khảo sát đặc trưng |
| Thành viên 2 | Decision Tree và Logistic Regression | Huấn luyện, cấu hình, xác nhận chéo phù hợp và giải thích mô hình |
| Thành viên 3 | Linear Regression và so sánh kết quả | Hồi quy phí hàng tháng; tổng hợp bảng so sánh phân loại riêng |
| Thành viên 4 | Giao diện ứng dụng | Dashboard Streamlit, form một khách và tải CSV |
| Thành viên 5 | Dữ liệu mới, huấn luyện lại và tích hợp demo | Gộp CSV có nhãn, lưu lần chạy, so sánh và kích hoạt mô hình |

**Giải thích khi trình bày**

Điền tên và mã sinh viên trước buổi báo cáo. Đây là phân công do đề tài cung cấp; không suy luận tác giả từng đoạn mã từ cấu trúc thư mục. Phần của thành viên 5 nên gọi là huấn luyện lại theo đợt, không gọi là hệ thống đã tự động chạy hàng tháng.

**Minh họa:** bảng năm dòng, mỗi người một nhiệm vụ chính.

### Slide 3 Xác định đầu vào đầu ra và mục tiêu

**Nội dung đưa lên slide**

| Thành phần | Nội dung |
|---|---|
| Đơn vị quan sát | Một hồ sơ khách hàng |
| Đầu vào | Thuộc tính khách hàng, dịch vụ, hợp đồng và chi phí tùy bộ đặc trưng |
| Nhãn học | `Churn`: `No = 0`, `Yes = 1` |
| Đầu ra ứng dụng | `churn_risk_score`, `predicted_churn`, `risk_group` |
| Cách sử dụng | Xếp điểm giảm dần, lọc nhóm rủi ro để ưu tiên xem xét |

**Giải thích khi trình bày**

Không dùng `customerID` làm đặc trưng học. Mã chỉ phục vụ nhận diện hồ sơ và đối chiếu dữ liệu. Nhãn Churn cũng bị loại khỏi đầu vào. Điểm nguy cơ được lấy từ `predict_proba` của mô hình phân loại, còn nhãn dự đoán được suy ra bằng ngưỡng lưu trong mô hình, hiện là 0,5.

Bộ Logistic điều chỉnh đang dùng mặc định không nhận trực tiếp hai cột phí vào mô hình. Vì vậy, nói “bộ dữ liệu có thông tin chi phí và một số cấu hình sử dụng chi phí” sẽ chính xác hơn “mọi dự đoán đều dùng chi phí”.

**Đối chiếu:** [src/schema.py](../../src/schema.py), [src/data.py](../../src/data.py), [predict.py](../../predict.py).

### Slide 4 Nguồn và quy mô dữ liệu

**Nội dung đưa lên slide**

- Bộ dữ liệu: IBM Telco Customer Churn.
- Ban đầu: **7.043 khách hàng, 21 cột**.
- Cấu trúc: 1 mã khách hàng, 19 thuộc tính còn lại và 1 nhãn Churn.
- Sau làm sạch: **7.032 hồ sơ**.
- Nguồn: [CSV trong kho IBM](https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/Telco-Customer-Churn.csv).

**Giải thích khi trình bày**

Dự án có script tải dữ liệu và kiểm tra SHA-256 để xác minh tệp nguồn. Dữ liệu huấn luyện nằm tại `data/raw/Telco-Customer-Churn.csv`; bản sau làm sạch nằm tại `data/processed/telco_clean.csv`. Hai tệp hiện có lần lượt đúng 7.043 và 7.032 dòng dữ liệu.

Dữ liệu mô tả hồ sơ và trạng thái Churn; chương trình chưa xây dựng chuỗi thời gian hay cửa sổ dự báo “rời bỏ trong 30 ngày tới”. Không gắn thêm thời hạn dự báo vào nhãn khi báo cáo.

**Minh họa:** thẻ số liệu 7.043, 21 và 7.032; ảnh trang “Mô tả dữ liệu”.

**Đối chiếu:** [download_data.py](../../download_data.py), [outputs/metrics.json](../../outputs/metrics.json).

### Slide 5 Các nhóm thuộc tính

**Nội dung đưa lên slide**

| Nhóm | Các cột | Ý nghĩa |
|---|---|---|
| Định danh | `customerID` | Theo dõi khách, không dùng để học |
| Khách hàng | `gender`, `SeniorCitizen`, `Partner`, `Dependents` | Giới tính, cao tuổi, bạn đời, người phụ thuộc |
| Thời gian sử dụng | `tenure` | Số tháng sử dụng dịch vụ |
| Điện thoại | `PhoneService`, `MultipleLines` | Điện thoại và nhiều đường dây |
| Internet và dịch vụ kèm | `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies` | Loại Internet và dịch vụ đăng ký |
| Hợp đồng và thanh toán | `Contract`, `PaperlessBilling`, `PaymentMethod` | Thời hạn hợp đồng, hóa đơn, phương thức trả tiền |
| Chi phí | `MonthlyCharges`, `TotalCharges` | Phí hàng tháng và tổng phí tích lũy |
| Nhãn | `Churn` | Đã rời bỏ hay chưa |

**Giải thích khi trình bày**

Các nhóm này giúp giải thích ý nghĩa dữ liệu trước khi mã hóa. Các cột phân loại không thể đưa nguyên chuỗi vào các mô hình đang dùng, nên cần chuyển thành biểu diễn số. Việc một cột xuất hiện trong dữ liệu không có nghĩa mọi cấu hình mô hình đều sử dụng cột đó.

**Đối chiếu:** [src/schema.py](../../src/schema.py).

### Slide 6 Làm sạch và kiểm tra chất lượng

**Nội dung đưa lên slide**

1. Kiểm tra đủ 21 cột bắt buộc.
2. Cắt khoảng trắng; chuyển chuỗi rỗng thành giá trị thiếu.
3. Chuyển các cột số, đặc biệt `TotalCharges`, sang kiểu số.
4. Kiểm tra bản ghi và mã khách trùng; loại mã trùng khi làm sạch.
5. Loại dòng thiếu trường bắt buộc; kiểm tra nhãn `Yes/No`.

| Chỉ tiêu dữ liệu IBM hiện có | Kết quả |
|---|---:|
| Số dòng ban đầu | 7.043 |
| Thiếu `TotalCharges` sau xử lý chuỗi/kiểu số | 11 |
| Dòng trùng hoàn toàn | 0 |
| Mã khách trùng | 0 |
| Số dòng bị loại | 11 |
| Số dòng hợp lệ | 7.032 |

**Giải thích khi trình bày**

Chương trình có xử lý trường hợp trùng, nhưng bộ IBM hiện tại không có dòng hay mã trùng. Không báo cáo “đã xóa dữ liệu trùng” khi số thực tế bằng 0. Hàm làm sạch giữ bản đầu tiên của mã trùng; riêng luồng gộp dữ liệu mới xử lý trước bằng quy tắc giữ bản mới nhất trong thứ tự ghép.

Không điền trung bình cho 11 giá trị thiếu. Không tự động xóa ngoại lệ theo IQR; dự án chỉ thống kê ngoại lệ trong EDA.

**Minh họa:** ảnh bảng record ở “2. Tiền xử lý”, chọn nhóm “Bị loại bỏ”.

**Đối chiếu:** `clean_dataset()` trong [src/data.py](../../src/data.py); `data_quality` trong [outputs/metrics.json](../../outputs/metrics.json).

### Slide 7 Khám phá dữ liệu và mất cân bằng nhãn

**Nội dung đưa lên slide**

- Ở lại: **5.163 khách**, khoảng **73,42%**.
- Rời bỏ: **1.869 khách**, khoảng **26,58%**.
- Có histogram và boxplot cho `tenure`, `MonthlyCharges`, `TotalCharges`.
- Phân tích tỷ lệ Churn theo hợp đồng, Internet, thanh toán và hỗ trợ kỹ thuật.

| Hợp đồng | Tổng khách | Khách rời bỏ | Tỷ lệ rời bỏ |
|---|---:|---:|---:|
| Theo tháng | 3.875 | 1.655 | 42,71% |
| Một năm | 1.472 | 166 | 11,28% |
| Hai năm | 1.685 | 48 | 2,85% |

**Giải thích khi trình bày**

Tỷ lệ ở mỗi dòng dùng mẫu số là tổng khách của chính nhóm đó. Nhóm hợp đồng theo tháng có tỷ lệ Churn quan sát cao hơn hai nhóm dài hạn. Đây là mối liên hệ trong dữ liệu, chưa chứng minh việc chuyển hợp đồng sẽ gây ra giảm Churn.

Vì lớp ở lại chiếm đa số, chỉ nhìn Accuracy có thể bỏ qua nhiều khách rời bỏ. Nếu luôn dự đoán ở lại, tỷ lệ đúng trên toàn bộ dữ liệu sạch đã khoảng 73,42%; đây là phép tính tham chiếu, không phải một mô hình baseline đã được huấn luyện trong code.

**Minh họa:** [phân bố Churn](../../outputs/figures/01_churn_distribution.png), [Churn theo hợp đồng](../../outputs/figures/05_churn_by_Contract.png).

**Đối chiếu:** [src/eda.py](../../src/eda.py), [eda_churn_by_category.csv](../../outputs/tables/eda_churn_by_category.csv), CSV sạch hiện có.

### Slide 8 Khảo sát mối liên hệ giữa đặc trưng và Churn

**Nội dung đưa lên slide**

| Phép khảo sát | Áp dụng | Kết quả tiêu biểu |
|---|---|---|
| ANOVA F | Ba biến liên tục theo hai lớp Churn | `tenure`: F ≈ 1.007,51; `TotalCharges`: 291,34; `MonthlyCharges`: 271,58 |
| Chi-square | Các biến chỉ báo không âm sau mã hóa | Bảng điểm và p-value theo từng biến |
| Mutual Information | Biến liên tục và rời rạc được khai báo tương ứng | Bảng mức thông tin với Churn |
| Spearman | Các biến số sau mã hóa so với Churn | Biểu đồ tương quan với nhãn |

**Giải thích khi trình bày**

Các phép khảo sát hỗ trợ hiểu dữ liệu. Chương trình không tự lấy top-k từ những bảng này để quyết định tập biến. Bộ biến của Tree, Logistic điều chỉnh và OLS điều chỉnh được khai báo sẵn trong `src/schema.py` theo báo cáo tham chiếu.

Các bảng khảo sát được tạo trên toàn bộ dữ liệu sạch trước khi chạy mô hình. Không gọi đây là lựa chọn đặc trưng đã fit riêng trong từng fold. Khi muốn dùng những kiểm định này để tự động chọn biến, cần đưa việc chọn biến vào phần train của quy trình đánh giá.

**Minh họa:** bảng ANOVA ngắn và [biểu đồ Spearman](../../outputs/figures/06_spearman_churn.png).

**Đối chiếu:** [src/feature_tests.py](../../src/feature_tests.py), [src/schema.py](../../src/schema.py).

### Slide 9 Mã hóa dữ liệu và các bộ đặc trưng

**Nội dung đưa lên slide**

- Bỏ `customerID` và `Churn` khỏi ma trận đầu vào.
- `Yes/No → 1/0`; `Male/Female → 1/0`.
- `No internet service`, `No phone service → No` ở các cột dịch vụ.
- One-hot encoding cho `InternetService`, `Contract`, `PaymentMethod`.
- Biểu diễn đầy đủ trên bộ IBM có **26 cột số** trước khi bỏ dummy tham chiếu.

| Cấu hình gốc | Số đặc trưng | Cách xác định |
|---|---:|---|
| Decision Tree | 7 | `TREE_SELECTED` |
| Logistic đầy đủ | 23 | 26 cột trừ 3 dummy tham chiếu |
| Logistic điều chỉnh | 16 | `LOGISTIC_SELECTED`, từ 12 trường gốc |
| OLS điều chỉnh | 10 | `LINEAR_SELECTED` |

**Giải thích khi trình bày**

Bỏ một dummy tham chiếu ở các nhóm giúp tránh biểu diễn dư thừa hoàn hảo trong mô hình có hệ số chặn. Ba cột tham chiếu là `InternetService_DSL`, `Contract_One year`, `PaymentMethod_Electronic check`. Tree dùng tập biến riêng, không áp dụng máy móc bộ đầy đủ.

Khi dự đoán CSV mới, các cột được đưa về đúng danh sách và thứ tự mà mô hình đã học. Cột dummy của một nhóm không xuất hiện trong batch được điền 0; thiếu trường gốc bắt buộc phải báo lỗi.

**Minh họa:** bảng “Trước mã hóa” và “Sau mã hóa” trên ứng dụng.

**Đối chiếu:** `encode_features()`, `prepare_prediction_features()` trong [src/data.py](../../src/data.py), [src/schema.py](../../src/schema.py).

### Slide 10 Chia tập huấn luyện và kiểm thử

**Nội dung đưa lên slide**

- Phân loại Churn dùng tỷ lệ **80/20**, `random_state=42`, `stratify=y` trong pipeline gốc.
- Train: **5.625 hồ sơ**; Test: **1.407 hồ sơ**.
- Test không tham gia fit mô hình, SMOTE hay StandardScaler.

| Tập phân loại gốc | Ở lại | Rời bỏ | Tổng |
|---|---:|---:|---:|
| Train | 4.130 | 1.495 | 5.625 |
| Test | 1.033 | 374 | 1.407 |

**Giải thích khi trình bày**

Chia phân tầng giúp duy trì tương đối tỷ lệ hai lớp. Các cấu hình phân loại gốc dùng cùng dữ liệu sạch và cùng seed nên có cùng tập khách kiểm thử, dù số đặc trưng khác nhau. OLS cũng chia 80/20 với seed 42 nhưng không phân tầng theo Churn vì mục tiêu là phí.

Trong demo huấn luyện lại, tỷ lệ kiểm thử có thể chỉnh từ 10% đến 40%; seed có thể cố định hoặc ngẫu nhiên mỗi lần. Để tái hiện bảng kết quả gốc, dùng 20% và seed 42 với đúng cấu hình gốc. Nếu đổi dữ liệu hoặc seed, số liệu có thể đổi.

**Đối chiếu:** `_split_for_churn()` trong [src/models.py](../../src/models.py), `train_classifier()` trong [src/retrain.py](../../src/retrain.py).

### Slide 11 Cân bằng lớp bằng SMOTE

**Nội dung đưa lên slide**

- Logistic gốc sử dụng `SMOTE(random_state=42, k_neighbors=5)`.
- Chỉ tạo mẫu trên phần huấn luyện.
- SMOTE nằm trong pipeline và được thực hiện lại bên trong mỗi fold CV.

| Giai đoạn | Ở lại | Rời bỏ | Tổng |
|---|---:|---:|---:|
| Train trước SMOTE | 4.130 | 1.495 | 5.625 |
| Train sau SMOTE | 4.130 | 4.130 | 8.260 |
| Test giữ nguyên | 1.033 | 374 | 1.407 |

**Giải thích khi trình bày**

SMOTE sinh thêm 2.635 mẫu lớp rời bỏ khi fit trên toàn bộ train gốc. Trong mỗi fold, SMOTE chỉ được fit trên phần học của fold đó, không dùng phần validation. Cách này ngăn mẫu sinh thêm được tạo từ dữ liệu validation rồi lọt ngược vào phần học.

Decision Tree trong pipeline gốc không dùng SMOTE. Demo huấn luyện lại cho chọn SMOTE, random oversampling, random undersampling, class weight hoặc không cân bằng cho các classifier. Các lựa chọn này là khả năng cấu hình; bảng kết quả gốc không phải kết quả thử hết năm phương án.

SMOTE hiện áp dụng trên dữ liệu đã mã hóa, có thể tạo giá trị trung gian ở cột chỉ báo. Chương trình chưa chuyển sang SMOTENC. Không tuyên bố đã xử lý riêng hình học của biến phân loại.

**Minh họa:** biểu đồ số mẫu trước/sau trên trang “2. Tiền xử lý”.

**Đối chiếu:** `_logistic_pipeline()` trong [src/models.py](../../src/models.py), `_sampler()` trong [src/retrain.py](../../src/retrain.py).

### Slide 12 Chuẩn hóa dữ liệu

**Nội dung đưa lên slide**

- Dùng StandardScaler với công thức `z = (x − μ) / σ`.
- Pipeline Logistic thực tế: **SMOTE → StandardScaler → Logistic Regression**.
- Fit scaler trên phần dữ liệu học sau cân bằng; dùng scaler đó để transform phần validation/test khi dự đoán.
- Decision Tree không sử dụng scaler trong pipeline huấn luyện.

**Giải thích khi trình bày**

Trong pipeline Logistic, scaler áp dụng cho toàn bộ ma trận đặc trưng đã chọn, gồm cả các cột chỉ báo. Tham số chuẩn hóa được học lại trong từng fold CV. Khi fit cuối, scaler được học trên train sau SMOTE và đi kèm classifier trong tệp joblib.

Bảng chuẩn hóa minh họa ở trang tiền xử lý chỉ dùng ba cột liên tục trên train gốc. Bảng này giúp hiểu tác động của chuẩn hóa nhưng không phải bộ tham số scaler đã học sau SMOTE của Logistic. Phân biệt hai phần để tránh trình bày sai quá trình thực thi.

Ở nhánh hồi quy phí, OLS không chuẩn hóa; Ridge/Lasso trong demo có StandardScaler trước bộ hồi quy.

**Đối chiếu:** [src/models.py](../../src/models.py), `preprocess_preview()` và `train_linear()` trong [src/retrain.py](../../src/retrain.py).

### Slide 13 Mô hình Decision Tree

**Nội dung đưa lên slide**

- Phân loại Churn bằng các quy tắc rẽ nhánh.
- Cấu hình gốc: `criterion="gini"`, `max_depth=4`, `random_state=42`.
- Không cân bằng lớp và không chuẩn hóa trong pipeline gốc.
- Bảy biến: hợp đồng theo tháng, tenure, hợp đồng hai năm, Internet cáp quang, phí hàng tháng, không Internet, thanh toán séc điện tử.
- Xuất hình cây, luật, độ quan trọng biến và thống kê các lá trên test.

**Giải thích khi trình bày**

Cây học các ngưỡng chia từ dữ liệu. Độ sâu tối đa 4 giới hạn độ phức tạp, thuận tiện giải thích. Trong kết quả đang lưu, chỉ báo hợp đồng theo tháng có độ quan trọng Gini khoảng 56,61%, tenure 17,93% và Internet cáp quang 16,39%.

Đây là độ quan trọng theo cấu trúc cây đã học, không phải trọng số nhân quả hay kết quả Permutation Feature Importance. Thống kê nhóm lá được tính trên khách test để mô tả rủi ro quan sát của từng nhóm.

**Minh họa:** [hình cây](../../outputs/figures/decision_tree.png); chỉ phóng to vài nút chính, không nhét toàn bộ cây quá nhỏ.

**Đối chiếu:** `run_decision_tree()` trong [src/models.py](../../src/models.py), [luật cây](../../outputs/tables/decision_tree_rules.txt), [độ quan trọng biến](../../outputs/tables/tree_feature_importance.csv).

### Slide 14 Mô hình Logistic Regression

**Nội dung đưa lên slide**

- Mô hình hóa điểm lớp rời bỏ bằng hàm sigmoid: `p = 1 / (1 + exp(−z))`.
- Hai cấu hình gốc: đầy đủ 23 đặc trưng và điều chỉnh 16 đặc trưng.
- Pipeline: SMOTE → StandardScaler → Logistic Regression.
- `max_iter=2000`, `random_state=42`; ngưỡng nhãn 0,5.
- Bản điều chỉnh được lưu làm mô hình dự đoán mặc định.

**Giải thích khi trình bày**

Hai cấu hình được huấn luyện và đánh giá riêng. Danh sách 16 đặc trưng được khai báo trước, không phải chương trình tự loại biến theo p-value ở mỗi lần chạy. Mô hình sklearn dùng để dự đoán khác với mô hình statsmodels dùng bổ sung cho suy diễn thống kê.

Mười hai trường gốc của Logistic điều chỉnh là `gender`, `Dependents`, `tenure`, `PhoneService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `PaperlessBilling`, `InternetService`, `PaymentMethod`, `Contract`. Sau khi tạo dummy và chọn cột, chúng thành 16 đặc trưng.

**Minh họa:** sơ đồ pipeline, công thức sigmoid và hai thẻ “23 đặc trưng” / “16 đặc trưng”.

**Đối chiếu:** `run_logistic_regression()` trong [src/models.py](../../src/models.py), `LOGISTIC_SELECTED` trong [src/schema.py](../../src/schema.py).

### Slide 15 Linear Regression cho phí hàng tháng

**Nội dung đưa lên slide**

- Vai trò hiện tại: giải thích/dự đoán **MonthlyCharges**.
- Không dự đoán Churn trong mã nguồn hiện tại.
- Loại `MonthlyCharges` khỏi X vì là mục tiêu; loại `TotalCharges` để tránh quan hệ tích lũy với phí hàng tháng.
- Pipeline gốc dùng statsmodels OLS, gồm bản đầy đủ và bản điều chỉnh 10 biến.

| Cấu hình OLS gốc | R² train | R² test | MAE test | RMSE test |
|---|---:|---:|---:|---:|
| Đầy đủ | 0,9989 | 0,9988 | 0,7835 | 1,0390 |
| Điều chỉnh | 0,9701 | 0,9689 | 3,5306 | 5,2402 |

**Giải thích khi trình bày**

R² và sai số ở đây đo mức phù hợp với phí hàng tháng, không đo phát hiện rời bỏ. Không đặt R² 0,9988 cạnh ROC-AUC của Logistic rồi kết luận OLS tốt hơn về Churn. MAE và RMSE theo đơn vị của `MonthlyCharges` trong dữ liệu.

Demo có thêm tùy chọn LinearRegression, Ridge và Lasso. Bộ kết quả đang lưu trong `outputs/metrics.json` là OLS của luồng phân tích gốc, chưa phải bảng thử nghiệm Ridge/Lasso. Ứng dụng chặn việc kích hoạt mô hình hồi quy tuyến tính làm mô hình dự đoán Churn.

**Đối chiếu:** `run_linear_regression()` trong [src/models.py](../../src/models.py), `train_linear()` và `set_active_model()` trong [src/retrain.py](../../src/retrain.py).

### Slide 16 Huấn luyện và xác nhận chéo

**Nội dung đưa lên slide**

1. Giữ riêng 20% test trong cấu hình gốc.
2. Với Logistic, chia train bằng `StratifiedKFold(5, shuffle=True, random_state=42)`.
3. Fit lại toàn bộ pipeline trên phần học của mỗi fold.
4. Tổng hợp chỉ số CV.
5. Fit pipeline trên toàn bộ train, sau đó đánh giá test.

| Luồng | Decision Tree | Logistic Regression | Linear Regression |
|---|---|---|---|
| Pipeline gốc | Fit train, đánh giá test; không CV | 5 fold cho Recall và Accuracy | Chia 80/20, đánh giá hồi quy; không CV |
| Demo huấn luyện lại | 5 fold cho Recall | 5 fold cho Recall | Chia train/test; không CV |

**Giải thích khi trình bày**

Recall CV trung bình của Logistic đầy đủ khoảng 79,46%, bản điều chỉnh khoảng 77,53%. Đây là Recall trên các fold train, tách biệt với Recall test lần lượt khoảng 78,07% và 76,20%.

Chưa có `scoring="f1"` trong CV, chưa có GridSearchCV hay quy trình tự động tìm cấu hình tốt nhất theo F1 CV. Giao diện cho điều chỉnh tham số và xem kết quả từng lần, nhưng không đồng nghĩa đã tối ưu siêu tham số bằng một nghiên cứu thực nghiệm đầy đủ.

**Đối chiếu:** [src/models.py](../../src/models.py), [src/retrain.py](../../src/retrain.py), [outputs/metrics.json](../../outputs/metrics.json).

### Slide 17 Các độ đo đánh giá

**Nội dung đưa lên slide**

Quy ước lớp dương là khách rời bỏ, `Churn=1`.

| Độ đo | Công thức hoặc ý nghĩa | Câu hỏi nghiệp vụ |
|---|---|---|
| Precision | `TP / (TP + FP)` | Trong các khách bị cảnh báo, bao nhiêu khách thực sự rời bỏ? |
| Recall | `TP / (TP + FN)` | Trong các khách thực sự rời bỏ, mô hình tìm được bao nhiêu? |
| F1 lớp 1 | `2PR / (P + R)` | Mức cân bằng giữa cảnh báo đúng và phát hiện đủ? |
| ROC-AUC | Đo khả năng xếp hạng lớp dương cao hơn lớp âm qua nhiều ngưỡng | Điểm có phân biệt tốt hai nhóm không? |
| Accuracy | `(TP + TN) / N` | Tổng thể có bao nhiêu dự đoán đúng? |

**Giải thích khi trình bày**

Theo mục tiêu đề tài, F1 lớp rời bỏ là tiêu chí ưu tiên để thảo luận, đồng thời cần nhìn Recall và Precision để thấy chi phí đánh đổi. Trong chương trình hiện tại, F1 đã được tính trên test; cơ chế chọn mô hình theo F1 CV trước khi mở test chưa được triển khai.

Không gọi Precision là Accuracy. Không gọi ROC-AUC là phần trăm khách được phân loại đúng. Hồi quy phí dùng R², MAE và RMSE, không sử dụng các độ đo lớp 1 trong bảng này.

**Đối chiếu:** [src/evaluation.py](../../src/evaluation.py), `_classification_scores()` trong [src/retrain.py](../../src/retrain.py).

### Slide 18 Kết quả so sánh phân loại trên test

**Nội dung đưa lên slide**

Kết quả đang lưu của pipeline gốc, trên cùng **1.407 khách test**; Precision, Recall, F1 đều tính cho lớp rời bỏ.

| Cấu hình | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Decision Tree | 0,7825 | 0,6133 | 0,4920 | 0,5460 | 0,8214 |
| Logistic đầy đủ | 0,7306 | 0,4958 | 0,7807 | 0,6064 | 0,8336 |
| Logistic điều chỉnh | 0,7385 | 0,5053 | 0,7620 | 0,6077 | 0,8273 |

**Giải thích khi trình bày**

Tree có Accuracy và Precision cao nhất trong ba cấu hình nhưng Recall chỉ khoảng 49,20%, bỏ sót khá nhiều khách rời bỏ. Logistic đầy đủ có Recall và AUC cao nhất. Logistic điều chỉnh có F1 test nhỉnh hơn bản đầy đủ khoảng 0,00124, tức 0,124 điểm phần trăm, với ít đặc trưng hơn.

Chênh lệch F1 giữa hai bản Logistic nhỏ; chưa có kiểm định hoặc khoảng tin cậy để khẳng định vượt trội ổn định. Tệp mặc định là Logistic điều chỉnh vì code lưu cấu hình này, không phải vì có bộ chọn tự động đã tối ưu F1 CV.

Không gọi đây là “ba thuật toán phân loại”; bảng có hai thuật toán, trong đó Logistic có hai cấu hình. Không lấy các kết quả test này làm bằng chứng hoàn thành quy trình chọn F1 trên phần phát triển.

**Minh họa:** bảng so sánh hoặc biểu đồ cột F1/Recall. Giữ bảng OLS ở slide riêng.

**Đối chiếu:** [outputs/metrics.json](../../outputs/metrics.json).

### Slide 19 Ma trận nhầm lẫn của Logistic điều chỉnh

**Nội dung đưa lên slide**

| Thực tế / Dự đoán | Ở lại | Rời bỏ |
|---|---:|---:|
| Ở lại | TN = 754 | FP = 279 |
| Rời bỏ | FN = 89 | TP = 285 |

- Phát hiện **285/374** khách rời bỏ, Recall ≈ **76,20%**.
- Bỏ sót **89** khách rời bỏ.
- Cảnh báo nhầm **279** khách ở lại.
- Có **564** cảnh báo, trong đó **285** đúng: Precision ≈ **50,53%**.

**Giải thích khi trình bày**

FN tương ứng khách rời bỏ nhưng không được cảnh báo, có thể mất cơ hội chăm sóc. FP tương ứng khách ở lại bị cảnh báo, có thể làm tốn nguồn lực rà soát. Mô hình hiện tăng khả năng tìm khách rời bỏ so với Tree nhưng phải xử lý nhiều cảnh báo nhầm hơn.

Các con số trên được đối chiếu từ metrics đủ độ chính xác và support trong classification report, không suy ngược từ số phần trăm đã làm tròn. Tổng bốn ô là 1.407, tổng hàng rời bỏ là 374.

**Minh họa:** [ma trận Logistic điều chỉnh](../../outputs/figures/confusion_logistic_selected.png).

**Đối chiếu:** [classification report](../../outputs/tables/classification_report_logistic_selected.txt), `confusion_from_report()` trong [src/dashboard.py](../../src/dashboard.py).

### Slide 20 Giải thích mô hình và điểm nguy cơ

**Nội dung đưa lên slide**

| Đặc trưng Logistic điều chỉnh | Hệ số sau chuẩn hóa | Chiều liên hệ trong mô hình |
|---|---:|---|
| Internet cáp quang | +0,5681 | Tăng log-odds dự đoán khi giữ các biến khác cố định |
| Hợp đồng theo tháng | +0,3960 | Tăng log-odds dự đoán |
| Tenure | −0,5566 | Giảm log-odds dự đoán |
| Bảo mật trực tuyến | −0,2538 | Giảm log-odds dự đoán |
| Hợp đồng hai năm | −0,2262 | Giảm log-odds dự đoán |

**Giải thích khi trình bày**

Hệ số lấy từ classifier sklearn trong pipeline có SMOTE và chuẩn hóa. Hệ số không trực tiếp là số điểm phần trăm thay đổi xác suất; cột dummy cũng được scaler biến đổi. Không biến hệ số thành hiệu quả của một biện pháp giữ chân.

Code còn ước lượng statsmodels Logit trên train gốc, không SMOTE, để xuất p-value, odds ratio và McFadden pseudo R². Đây là mô hình suy diễn riêng; không trộn hệ số của nó với hệ số sklearn. Pseudo R² 0,2782 không có nghĩa “giải thích 27,82% phương sai Churn” như cách đọc R² OLS.

Điểm ứng dụng là điểm mô hình chưa hiệu chuẩn, đặc biệt do thay đổi tỷ lệ lớp khi dùng SMOTE. Điểm 0,8 không nên diễn giải là xác suất thực tế 80% đã được xác nhận. Dự án hiện chưa có SHAP, PFI hay quy trình calibration.

**Minh họa:** biểu đồ hệ số có trục âm/dương hoặc bảng năm dòng trên.

**Đối chiếu:** [hệ số sklearn](../../outputs/tables/logistic_selected_coefficients.csv), [hệ số statsmodels](../../outputs/tables/logit_selected_statsmodels_coefficients.csv), [src/models.py](../../src/models.py).

### Slide 21 Cấu trúc ứng dụng Streamlit

**Nội dung đưa lên slide**

| Khu vực | Chức năng đã có |
|---|---|
| Mô tả dữ liệu | Hồ sơ dữ liệu, thuộc tính và chất lượng |
| Thống kê mô tả | Phân bố biến và tỷ lệ Churn theo nhóm |
| Kỹ thuật khai phá | Kết quả, bảng/biểu đồ mô hình từ pipeline gốc |
| Demo 1 đến 5 | Dữ liệu → Tiền xử lý → Huấn luyện → So sánh → Dự đoán |
| Hướng dẫn sử dụng | Xem và tải tài liệu hướng dẫn |

**Giải thích khi trình bày**

Ứng dụng dùng Python, pandas, scikit-learn, imbalanced-learn, statsmodels và Streamlit; biểu đồ tương tác dùng Altair. Mô hình lưu bằng joblib. Vue trong thư mục `slide/` phục vụ bộ slide trình chiếu, còn ứng dụng nghiệp vụ được triển khai bằng Streamlit.

Các trang phân tích đọc artifacts ở `outputs/`; phần so sánh huấn luyện lại đọc lịch sử `outputs/runs/`. Chọn mô hình mới cho dự đoán không tự viết lại toàn bộ bảng phân tích gốc. Người thuyết trình cần phân biệt kết quả báo cáo gốc với mô hình đang được kích hoạt.

**Minh họa:** ảnh menu và trang mô tả dữ liệu; sơ đồ thư mục rút gọn.

**Đối chiếu:** [app.py](../../app.py), [requirements.txt](../../requirements.txt), [slide/src/slides.js](../src/slides.js).

### Slide 22 Dữ liệu mới và huấn luyện lại theo đợt

**Nội dung đưa lên slide**

1. Chọn dữ liệu IBM, CSV khác hoặc chỉ dữ liệu mới.
2. Nạp một hoặc nhiều CSV đã có nhãn Churn và đủ 21 cột.
3. Ghép dữ liệu; mã khách trùng ưu tiên bản mới.
4. Làm sạch, mã hóa, chia tập và huấn luyện theo cấu hình.
5. Lưu mô hình, cấu hình và kết quả của từng lần chạy.
6. Xem So sánh, chọn tiêu chí rồi bấm dùng mô hình cho dự đoán.

**Giải thích khi trình bày**

Khi có dữ liệu mới, chương trình lưu bản CSV đầu vào của lần chạy tại `outputs/runs/<run_id>/new_data.csv`. Kết quả và cấu hình nằm trong `run.json`, mô hình nằm trong tệp joblib của từng thuật toán. Danh sách lần chạy được đọc lại từ đĩa để so sánh. Tệp `outputs/models/active.json` ghi mô hình đang được chọn; nếu không có lựa chọn hợp lệ, ứng dụng quay về Logistic điều chỉnh của pipeline gốc.

Trang So sánh có thể xếp theo Recall, Precision, F1, AUC hoặc Accuracy, và cho chủ động kích hoạt mô hình. Chỉ các classifier được dùng cho bước dự đoán Churn. Khi kết quả ở các lần chạy có seed hay dữ liệu khác nhau, tập test có thể khác nhau; so sánh đó là đối chiếu thực nghiệm, chưa phải đánh giá trên benchmark cố định.

Hiện chưa có lịch chạy hàng tháng, ngưỡng số hồ sơ mới để tự kích hoạt, cơ chế chấp nhận/từ chối tự động hoặc giao diện bổ sung nhãn thực tế từng khách. Có thể chuẩn bị CSV đã cập nhật nhãn rồi nạp lại; chương trình không tự thu thập kết quả thật từ doanh nghiệp. Dữ liệu gốc không tự được ghi đè thành kho tích lũy sau mỗi lần chạy.

**Minh họa:** quy trình năm bước trên menu. Chỉ thêm bảng số liệu lần huấn luyện lại sau khi thực sự chạy demo; hiện chưa có lịch sử để trích số.

**Đối chiếu:** [src/retrain.py](../../src/retrain.py), `page_data()`, `page_train()`, `page_compare()` trong [app.py](../../app.py).

### Slide 23 Demo dự đoán một khách và hàng loạt

**Nội dung đưa lên slide**

| Chế độ | Đầu vào | Đầu ra/chức năng |
|---|---|---|
| Một khách | Form thông tin hoặc hồ sơ mẫu | Điểm, nhãn, mức rủi ro, xem hồ sơ, tải CSV kết quả |
| Hàng loạt | CSV hoặc 3 khách mẫu có sẵn | Chấm điểm, sắp xếp/lọc danh sách, tìm mã nếu có, tải toàn bộ kết quả |

- `predicted_churn = Yes` khi điểm ≥ 0,5.
- Theo `pd.cut` hiện tại: **Low: 0–0,3; Medium: >0,3–0,6; High: >0,6–1**.
- Đây là ngưỡng nhóm minh họa, chưa tối ưu theo chi phí kinh doanh.

**Giải thích khi trình bày**

Nhóm nguy cơ và nhãn dự đoán dùng hai cách cắt khác nhau. Một khách có điểm 0,55 sẽ được dự đoán rời bỏ nhưng vẫn nằm nhóm Medium. Đúng tại 0,3 thuộc Low và đúng tại 0,6 thuộc Medium do khoảng mặc định của `pd.cut` đóng bên phải; mô tả trong slide cần theo code này.

Logistic điều chỉnh mặc định cần 12 trường gốc. Form hiện có thêm MonthlyCharges nhưng cột này không đi vào bộ 16 đặc trưng của cấu hình mặc định. Khi chọn classifier có nhiều trường hơn, CSV phải có đủ cột được mô hình yêu cầu. Form một khách hiện không có mọi trường của cấu hình “tất cả”, nên không tuyên bố form tương thích với mọi mô hình vừa huấn luyện.

Form không tự lưu hồ sơ vừa dự đoán vào tập huấn luyện. CSV kết quả chỉ có nhãn dự đoán, không tự trở thành nhãn thực tế để huấn luyện lại. Muốn nạp cho bước huấn luyện, cần hồ sơ đầy đủ và nhãn Churn thực đã được xác nhận.

**Kịch bản demo đề xuất khoảng 3 phút**

1. Mở “Mô tả dữ liệu”, chỉ ra 7.043 → 7.032 và 11 dòng thiếu TotalCharges.
2. Mở “Thống kê mô tả”, chọn Contract và giải thích tỷ lệ theo nhóm.
3. Mở “Kỹ thuật khai phá”, xem ma trận Logistic điều chỉnh và nêu 285 phát hiện, 89 bỏ sót, 279 cảnh báo nhầm.
4. Mở “5. Dự đoán”, chọn chế độ hàng loạt, bấm “Chạy thử 3 khách hàng mẫu”.
5. Quan sát điểm thật trả về, lọc nhóm rủi ro, tải CSV; không điền trước điểm mẫu khi chưa chạy đúng mô hình hiện hành.
6. Nếu còn thời gian, chuyển sang một khách, chọn hồ sơ mẫu và bấm dự đoán.

Demo huấn luyện lại nên chạy riêng sau phần này nếu thời gian cho phép. Giữ seed cố định để dễ giải thích; việc bật seed ngẫu nhiên ở trang huấn luyện có thể làm số liệu khác phần minh họa tiền xử lý dùng seed 42.

**Đối chiếu:** [predict.py](../../predict.py), `single_prediction()`, `batch_prediction()` trong [app.py](../../app.py), [src/dashboard.py](../../src/dashboard.py), [CSV mẫu](../../data/new_customers_example.csv).

### Slide 24 Kết quả đạt được và hướng hoàn thiện

**Nội dung đưa lên slide**

**Đã thực hiện**

- Chuẩn bị dữ liệu IBM, kiểm tra chất lượng, EDA và mã hóa.
- Phân loại Churn bằng Tree và Logistic; phân tích phí bằng hồi quy tuyến tính.
- Lưu kết quả test, ma trận nhầm lẫn, hệ số và quy tắc cây.
- Dự đoán một khách/CSV bằng Streamlit, xuất kết quả.
- Huấn luyện lại theo đợt, lưu lịch sử, so sánh và chọn classifier dùng dự đoán.

**Kết quả tiêu biểu**

- Logistic điều chỉnh: F1 test **0,6077**, Recall **0,7620**.
- Phát hiện **285/374** khách rời bỏ, có **279** cảnh báo nhầm.
- Điểm hỗ trợ ưu tiên rà soát; chưa hiệu chuẩn thành xác suất thực tế.

**Phần cần hoàn thiện theo đề cương**

- Chọn cấu hình bằng F1 trên CV/validation, sau đó kiểm thử cuối cùng độc lập.
- Lưu hồ sơ dự đoán bền vững và bổ sung nhãn thực tế.
- Bổ sung lịch huấn luyện tháng và điều kiện đủ dữ liệu.
- Đánh giá trên dữ liệu mới, hiệu chuẩn điểm và chọn ngưỡng theo nguồn lực.

**Giải thích khi trình bày**

Nhóm đã có một quy trình thực hành từ dữ liệu đến mô hình và ứng dụng hỗ trợ xem xét hồ sơ. Chất lượng phân loại có đánh đổi giữa bỏ sót và cảnh báo nhầm. Các chức năng vận hành bổ sung được nêu là hướng hoàn thiện, không phải kết quả đã triển khai. Chưa có đo lường hiệu quả chiến dịch, doanh thu giữ lại hoặc triển khai tích hợp với hệ thống khách hàng thực tế.

Kết thúc bằng lời cảm ơn và mời câu hỏi. Nếu cần một trang cảm ơn riêng, tách thành slide 25 mà không thêm nội dung kỹ thuật mới.

## 4 Phương án rút còn 15 slide theo cấu trúc tham khảo

| Slide ngắn | Nội dung gom từ bản chi tiết |
|---|---|
| 1 | Giới thiệu đề tài và mục tiêu, từ slide 1 và 3 |
| 2 | Phân công năm người, từ slide 2 |
| 3 | Nguồn, quy mô và chất lượng, từ slide 4 và 6 |
| 4 | Thuộc tính và EDA, từ slide 5 và 7 |
| 5 | Khảo sát đặc trưng, mã hóa, chia tập, từ slide 8–10 |
| 6 | Cân bằng lớp, từ slide 11 |
| 7 | Chuẩn hóa, từ slide 12 |
| 8 | Tree và Logistic, từ slide 13–14 |
| 9 | Huấn luyện, CV và độ đo, từ slide 16–17 |
| 10 | So sánh phân loại, từ slide 18 |
| 11 | Ma trận nhầm lẫn, từ slide 19 |
| 12 | Hệ số và phân tích OLS bổ sung, từ slide 20 và 15; tách hai mục tiêu rõ ràng |
| 13 | Huấn luyện lại theo đợt, từ slide 22 |
| 14 | Ứng dụng và demo, từ slide 21 và 23 |
| 15 | Kết quả, giới hạn, hướng hoàn thiện và hỏi đáp, từ slide 24 |

Trong bản 15 slide, đưa bảng OLS và danh sách đặc trưng đầy đủ vào phần dự phòng nếu slide 12 quá chật. Không bỏ chú thích rằng Linear Regression có mục tiêu khác.

## 5 Câu hỏi phản biện và cách trả lời

| Câu hỏi | Trả lời bám vào dự án |
|---|---|
| Nhóm có ba mô hình phân loại không? | Hiện có hai thuật toán phân loại Churn là Tree và Logistic. Linear Regression là nhánh hồi quy MonthlyCharges. Logistic được thử với hai cấu hình đặc trưng. |
| Vì sao chưa đúng yêu cầu ba mô hình cùng dự đoán Churn? | Mã hiện tại triển khai tuyến tính cho phí hàng tháng. Nếu bắt buộc ba mô hình cùng mục tiêu thì cần thay đổi triển khai; chưa thể trình bày như đã hoàn thành. |
| CV có dùng F1 không? | Chưa. Luồng gốc đo Recall và Accuracy cho Logistic; demo đo Recall cho Tree và Logistic. F1 hiện được tính trên test. |
| Có thể chọn mô hình theo F1 không? | Trang So sánh có thể xếp theo F1 test đã lưu và cho kích hoạt. Đây chưa phải chọn bằng F1 CV trước lần đánh giá test cuối cùng. |
| Vì sao dùng Logistic khi Tree có Accuracy cao hơn? | Tree bỏ sót 190/374 khách rời bỏ. Logistic điều chỉnh bỏ sót 89/374, nhưng đổi lại có nhiều cảnh báo nhầm hơn. |
| Logistic điều chỉnh có chắc tốt hơn bản đầy đủ không? | F1 test cao hơn rất ít; bản đầy đủ có Recall và AUC cao hơn. Chưa có kết luận thống kê về ưu thế ổn định. |
| Có rò rỉ do SMOTE không? | SMOTE nằm trong pipeline và chỉ fit ở phần học, kể cả bên trong CV. Tuy nhiên EDA và kiểm định đặc trưng hiện chạy toàn bộ dữ liệu sạch, không phải quy trình tự chọn biến trong CV. |
| Có xóa ngoại lệ và điền thiếu bằng trung bình không? | Không. Code thống kê IQR để khảo sát, không tự xóa ngoại lệ. Dòng thiếu trường bắt buộc bị loại; bộ IBM bị loại 11 dòng thiếu TotalCharges. |
| Điểm 80% có phải xác suất thực tế không? | Là điểm `predict_proba` chưa được hiệu chuẩn; không khẳng định xác suất thực tế 80%. |
| Tại sao điểm 0,55 là Medium nhưng nhãn rời bỏ? | Nhãn dùng ngưỡng 0,5; nhóm nguy cơ dùng các mốc 0,3 và 0,6. Hai đầu ra phục vụ hai cách đọc khác nhau. |
| Nhập hồ sơ dự đoán xong có tự học thêm không? | Không. Có thể tải CSV kết quả; huấn luyện lại cần CSV đầy đủ và nhãn thực, không lấy dự đoán làm nhãn thật. |
| Cập nhật nhãn thực tế thế nào? | Chuẩn bị CSV đủ cột và nhãn Churn đã xác nhận rồi nạp ở bước Dữ liệu; mã trùng ưu tiên bản mới. Chưa có màn hình sửa nhãn riêng. |
| Đã tự chạy lại mỗi tháng chưa? | Chưa có bộ lập lịch. Hiện người dùng bấm huấn luyện theo đợt. |
| Mô hình có tự được thay sau khi train không? | Không. Người dùng xem kết quả rồi bấm chọn mô hình. Con trỏ mô hình đang dùng được lưu vào active.json. |
| R² OLS gần 1 có nghĩa phân loại gần hoàn hảo không? | Không. OLS dự đoán phí, có đầu ra và thước đo khác với Churn. |
| Dự án đã chứng minh giảm tỷ lệ rời bỏ chưa? | Chưa có thử nghiệm can thiệp hay đo kết quả kinh doanh. Ứng dụng hiện hỗ trợ nhận diện và xếp ưu tiên. |

## 6 Danh mục bằng chứng để dựng slide

| Phần báo cáo | Mã nguồn hoặc dữ liệu | Bảng và hình phù hợp |
|---|---|---|
| Dữ liệu và làm sạch | `src/data.py`, `download_data.py`, `data/raw/`, `data/processed/` | `outputs/metrics.json` phần data_quality |
| Mô tả biến | `src/schema.py` | Bảng các nhóm thuộc tính trong tài liệu |
| EDA | `src/eda.py`, `src/dashboard.py` | `outputs/figures/01_*` đến `06_*`; các bảng `eda_*` |
| Khảo sát đặc trưng | `src/feature_tests.py` | `feature_anova.csv`, `feature_chi_square.csv`, `feature_mutual_information.csv` |
| Tree | `src/models.py` | `decision_tree.png`, `decision_tree_rules.txt`, `tree_feature_importance.csv`, `tree_risk_groups_test.csv` |
| Logistic | `src/models.py` | `metrics_logistic_*.json`, `classification_report_logistic_*.txt`, `logistic_*_coefficients.csv` |
| OLS | `src/models.py` | `ols_summary_*.txt`, `ols_coefficients_*.csv`, `ols_selected_vif.csv` |
| Ứng dụng và dự đoán | `app.py`, `predict.py`, `src/dashboard.py` | Ảnh chụp ứng dụng sau khi chạy với mô hình thực tế |
| Huấn luyện lại | `src/retrain.py` | `outputs/runs/<run_id>/run.json` và joblib sau khi thực sự chạy |
| Kiểm thử chức năng | `tests/test_pipeline.py`, `tests/test_dashboard.py`, `tests/test_retrain.py` | Không sử dụng dữ liệu giả lập của test làm kết quả nghiên cứu |

Các chỉ số trong tài liệu là kết quả đã lưu, đối chiếu thêm với CSV hiện có và classification report. Không phải kết quả của một lần huấn luyện mới trong quá trình soạn tài liệu. Môi trường `.venv` hiện tham chiếu Python 3.11 không tồn tại tại đường dẫn đã cấu hình; chưa chạy lại training hay bộ kiểm thử khi soạn bản này. Tên file kiểm thử cho biết nội dung kiểm tra hiện có, không đồng nghĩa tất cả kiểm thử vừa được chạy và đạt.

## 7 Những câu cần tránh trên slide

| Tránh viết | Thay bằng |
|---|---|
| Ba mô hình đều dự đoán khách rời bỏ | Tree và Logistic phân loại Churn; Linear Regression phân tích phí |
| Đã chọn mô hình tốt nhất bằng F1 CV | Đã tính F1 test; CV hiện dùng Recall và có thêm Accuracy ở Logistic gốc |
| Đã tối ưu siêu tham số tự động | Có giao diện cấu hình và so sánh các lần huấn luyện |
| Tự động huấn luyện mỗi tháng khi đủ dữ liệu | Huấn luyện lại theo đợt do người dùng khởi chạy |
| Form tự lưu hồ sơ và phản hồi nhãn thật | Có xuất CSV dự đoán; dữ liệu huấn luyện mới được nạp riêng bằng CSV có nhãn |
| SMOTE áp dụng cho toàn bộ dữ liệu | SMOTE chỉ áp dụng phần học trong pipeline |
| Đã tự chọn 16 biến tốt nhất bằng kiểm định | Bộ 16 biến đã được khai báo sẵn theo báo cáo tham chiếu |
| Điểm nguy cơ là xác suất thực tế đã chính xác | Điểm mô hình chưa được hiệu chuẩn |
| Hệ thống đã giúp doanh nghiệp giảm Churn | Hệ thống minh họa hỗ trợ xếp ưu tiên hồ sơ cần xem xét |
| Hình slide mẫu về tiểu đường là kết quả dự án | Chỉ tham khảo bố cục; toàn bộ đề tài, mô hình, hình và số liệu phải là Telco |

