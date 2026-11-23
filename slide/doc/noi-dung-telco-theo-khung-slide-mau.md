# Nội dung trình chiếu Telco Customer Churn theo khung slide mẫu

**Quy mô:** 15 slide, bám theo thứ tự và cách chia phần của `slide/learn/slide.pdf`.

**Đề tài:** Dự đoán khách hàng rời bỏ dịch vụ viễn thông.

**Ngày đối chiếu:** 23/11/2026. Số liệu lấy từ kết quả pipeline gốc đang lưu trong `outputs/metrics.json` và các bảng tương ứng. Kết quả của những lần huấn luyện lại trên giao diện có thể khác.

Mỗi slide gồm nội dung đưa lên màn hình, bố cục gợi ý và ghi chú dành cho người trình bày. Khi dựng slide, chỉ đưa phần “Nội dung trình chiếu” và hình minh họa lên màn hình. Các trường trong ngoặc vuông cần được điền bằng thông tin thực tế của nhóm.

## Slide 1. Báo cáo bài tập lớn: Telco Customer Churn

### Nội dung trình chiếu

**BÁO CÁO BÀI TẬP LỚN**  
**KHAI PHÁ DỮ LIỆU**

### Dự đoán khách hàng rời bỏ dịch vụ viễn thông

Ứng dụng khai phá dữ liệu để nhận diện khách hàng có nguy cơ rời bỏ và hỗ trợ ưu tiên chăm sóc.

| Giảng viên hướng dẫn | Nhóm thực hiện |
|---|---|
| [Họ tên giảng viên] | [Tên nhóm] - [Lớp] |

### Bố cục gợi ý

Giữ cách trình bày trang bìa của bài mẫu: tiêu đề lớn bên trái, tên đề tài màu xanh ngọc, thông tin giảng viên và nhóm ở phía dưới.

### Ghi chú thuyết trình

Đầu vào là hồ sơ khách hàng, dịch vụ sử dụng, hợp đồng và thanh toán. Đầu ra gồm nhãn Churn và điểm nguy cơ. Mục tiêu là hỗ trợ doanh nghiệp rà soát, sắp xếp thứ tự chăm sóc khách hàng.

## Slide 2. Thành viên nhóm và nhiệm vụ

### Nội dung trình chiếu

| Họ và tên | Mã sinh viên | Nhiệm vụ |
|---|---|---|
| [Thành viên 1] | [Mã SV] | Chuẩn bị dữ liệu, làm sạch, mã hóa và phân tích khám phá. |
| [Thành viên 2] | [Mã SV] | Xây dựng Decision Tree và Logistic Regression; đánh giá phân loại. |
| [Thành viên 3] | [Mã SV] | Phân tích Linear Regression; tổng hợp, so sánh kết quả. |
| [Thành viên 4] | [Mã SV] | Xây dựng dashboard và chức năng dự đoán trên Streamlit. |
| [Thành viên 5] | [Mã SV] | Tích hợp dữ liệu mới, huấn luyện lại và chuẩn bị demo. |

### Bố cục gợi ý

Bảng ba cột như slide 2 của bài mẫu. Đây là phân công gợi ý; điều chỉnh theo nhiệm vụ thực tế của nhóm.

## Slide 3. Mô tả dữ liệu: nguồn gốc và quy mô

### Nội dung trình chiếu

**NGUỒN GỐC VÀ QUY MÔ**

- Bộ dữ liệu mẫu **IBM Telco Customer Churn**.
- **7.043 khách hàng**, **21 trường dữ liệu** ban đầu.
- Sau làm sạch: **7.032 khách hàng**.
- Nhãn mục tiêu: **Churn**, gồm `No = 0` và `Yes = 1`.
- Tỷ lệ rời bỏ sau làm sạch: **26,58%**.

**CÁC THUỘC TÍNH CHÍNH**

| Thuộc tính | Ý nghĩa |
|---|---|
| `Churn` | Khách hàng có rời bỏ dịch vụ hay không. |
| `tenure` | Số tháng khách hàng đã sử dụng dịch vụ. |
| `Contract` | Hợp đồng theo tháng, một năm hoặc hai năm. |
| `InternetService` | Dịch vụ DSL, cáp quang hoặc không dùng Internet. |
| `MonthlyCharges` | Phí dịch vụ hàng tháng. |
| `TotalCharges` | Tổng phí đã thanh toán. |

### Bố cục gợi ý

Hai cột: bên trái là nguồn dữ liệu và các số lớn **7.043 / 21 / 26,58%**; bên phải là bảng thuộc tính. Có thể sử dụng [ảnh mô tả dữ liệu](../images/streamlit-mo-ta-du-lieu.png).

### Ghi chú thuyết trình

21 trường bao gồm mã khách hàng và nhãn, không phải 21 đặc trưng đầu vào. Mỗi dòng đại diện một khách hàng. `customerID` dùng để nhận diện hồ sơ và không được đưa vào mô hình học.

## Slide 4. Chi tiết các nhóm thuộc tính dữ liệu

### Nội dung trình chiếu

| Nhóm | Thuộc tính | Ý nghĩa |
|---|---|---|
| Thông tin khách hàng | `gender`, `SeniorCitizen`, `Partner`, `Dependents` | Giới tính, nhóm cao tuổi, tình trạng có bạn đời và người phụ thuộc. |
| Dịch vụ điện thoại | `PhoneService`, `MultipleLines` | Sử dụng điện thoại và nhiều đường dây. |
| Dịch vụ Internet | `InternetService`, `OnlineSecurity`, `OnlineBackup` | Loại kết nối, bảo mật trực tuyến và sao lưu. |
| Hỗ trợ và bảo vệ | `DeviceProtection`, `TechSupport` | Bảo vệ thiết bị và hỗ trợ kỹ thuật. |
| Giải trí | `StreamingTV`, `StreamingMovies` | Dịch vụ xem truyền hình và phim trực tuyến. |
| Hợp đồng, thanh toán | `Contract`, `PaperlessBilling`, `PaymentMethod` | Thời hạn hợp đồng, hóa đơn điện tử và phương thức thanh toán. |
| Thời gian và chi phí | `tenure`, `MonthlyCharges`, `TotalCharges` | Thời gian gắn bó, phí hàng tháng và tổng phí. |

**Hai mục tiêu phân tích:**

- **Phân loại:** dự đoán `Churn` bằng Decision Tree và Logistic Regression.
- **Hồi quy bổ sung:** dự đoán `MonthlyCharges` bằng Linear Regression.

### Bố cục gợi ý

Bảng toàn chiều ngang như slide 4 của bài mẫu; đặt hai mục tiêu trong một dải nhấn ngắn phía dưới.

### Ghi chú thuyết trình

Hồi quy tuyến tính có biến đích khác với hai mô hình phân loại. Vì vậy, kết quả R² và RMSE được trình bày riêng, không xếp chung với Accuracy hoặc F1 của bài toán Churn.

## Slide 5. Tiền xử lý: làm sạch, mã hóa và chọn đặc trưng

### Nội dung trình chiếu

**LÀM SẠCH VÀ MÃ HÓA**

- Loại khoảng trắng; chuyển `TotalCharges` sang kiểu số.
- Loại **11 dòng thiếu dữ liệu**; còn **7.032 khách hàng**.
- Không phát hiện dòng hoặc mã khách hàng trùng trong dữ liệu gốc.
- Mã hóa Yes/No thành 1/0; one-hot encoding cho biến nhiều mức.
- Loại `customerID` và `Churn` khỏi đầu vào học.

**BỘ ĐẶC TRƯNG THEO MÔ HÌNH**

| Mô hình | Bộ đặc trưng điều chỉnh |
|---|---|
| Decision Tree | 7 biến sau mã hóa. |
| Logistic Regression | 16 biến sau mã hóa. |
| Linear Regression | 10 biến sau mã hóa. |

**Chia dữ liệu phân loại:** 80% Train, 20% Test; giữ tỷ lệ nhãn bằng phân tầng.

### Bố cục gợi ý

Hai cột: quy trình làm sạch bên trái, bảng bộ đặc trưng và sơ đồ **7.032 → 5.625 Train + 1.407 Test** bên phải. Minh họa bằng [ảnh chia tập](../images/streamlit-chia-tap.png).

### Ghi chú thuyết trình

Các bộ biến điều chỉnh được khai báo trong `src/schema.py` theo báo cáo. Dự án có ANOVA, Chi-square và Mutual Information để khảo sát, nhưng pipeline gốc không tự động chọn các bộ biến trên bằng ngưỡng tương quan 0,05 như bài mẫu. Logistic và OLS có cả cấu hình đầy đủ và điều chỉnh. Nhánh OLS chia 80/20 riêng, không phân tầng theo Churn.

## Slide 6. Tiền xử lý: cân bằng dữ liệu bằng SMOTE

### Nội dung trình chiếu

**VẤN ĐỀ MẤT CÂN BẰNG**

- Khách ở lại: khoảng **73,42%**.
- Khách rời bỏ: khoảng **26,58%**.
- Mô hình có thể đạt Accuracy cao nhưng bỏ sót nhiều khách rời bỏ.

**GIẢI PHÁP TRONG PIPELINE LOGISTIC**

- Sử dụng **SMOTE** để bổ sung mẫu tổng hợp cho lớp thiểu số.
- Tạo mẫu bằng nội suy giữa các điểm thuộc lớp rời bỏ.
- Chỉ thực hiện trên dữ liệu huấn luyện.
- Trong xác nhận chéo, SMOTE được thực hiện riêng trong từng fold huấn luyện.
- Giữ nguyên tập Test để đánh giá.

### Bố cục gợi ý

Bên trái giải thích SMOTE; bên phải là phân bố lớp và biểu đồ trước/sau cân bằng. Có thể sử dụng [ảnh SMOTE](../images/streamlit-smote.png); kiểm tra cấu hình trong ảnh khi dựng slide.

### Ghi chú thuyết trình

Pipeline gốc chỉ áp dụng SMOTE cho Logistic; Decision Tree gốc không cân bằng mẫu. Giao diện huấn luyện lại cho phép chọn thêm các phương pháp cân bằng. Với dữ liệu one-hot, SMOTE có thể tạo giá trị trung gian ở biến nhị phân; cần đánh giá thêm các phương pháp phù hợp dữ liệu hỗn hợp khi mở rộng.

## Slide 7. Tiền xử lý: chuẩn hóa dữ liệu

### Nội dung trình chiếu

**STANDARD SCALER**

Đưa các đặc trưng về thang đo chuẩn hóa:

```text
z = (x - μ_train) / σ_train
```

- Giảm chênh lệch thang đo giữa các biến trong Logistic Regression.
- Pipeline Logistic gốc: **SMOTE → StandardScaler → Logistic Regression**.
- Học tham số chuẩn hóa trong phần huấn luyện; dùng lại khi biến đổi Test và dữ liệu mới.
- Decision Tree gốc không cần bước chuẩn hóa.

### Bố cục gợi ý

Công thức ở giữa; ba bước pipeline phía trên hoặc bên phải; bảng minh họa trước/sau chuẩn hóa phía dưới. Có thể sử dụng [ảnh chuẩn hóa](../images/streamlit-chuan-hoa.png).

### Ghi chú thuyết trình

Theo đúng thứ tự mã nguồn, StandardScaler của bộ phân loại Logistic được fit trên dữ liệu Train sau SMOTE. Toàn bộ pipeline được fit lại trong từng fold. Không fit scaler trên toàn bộ dữ liệu trước khi chia tập. Bảng xem trước chuẩn hóa trên giao diện là phần minh họa; cần phân biệt với thứ tự thực thi pipeline mô hình.

## Slide 8. Các thuật toán được sử dụng

### Nội dung trình chiếu

| Decision Tree | Logistic Regression | Linear Regression |
|---|---|---|
| Phân loại khách hàng thành ở lại hoặc rời bỏ. | Ước lượng điểm cho lớp rời bỏ từ tổ hợp các đặc trưng. | Dự đoán phí dịch vụ hàng tháng. |
| Chia nhánh bằng tiêu chí Gini. | Hàm sigmoid chuyển điểm tuyến tính về khoảng 0–1. | Ước lượng quan hệ tuyến tính bằng OLS. |
| Cấu hình gốc: `max_depth = 4`, 7 biến. | Cấu hình đầy đủ và điều chỉnh 16 biến; kết hợp SMOTE và chuẩn hóa. | Cấu hình đầy đủ và điều chỉnh 10 biến. |
| Ưu điểm: quan sát được luật phân nhánh. | Ưu điểm: có thể phân tích chiều tác động qua hệ số. | Đánh giá riêng bằng R², MAE và RMSE. |

```text
Logistic: score = 1 / (1 + exp(-(β₀ + β₁x₁ + ... + βₚxₚ)))
```

### Bố cục gợi ý

Ba khối ngang như slide thuật toán CatBoost của bài mẫu. Mỗi khối gồm mục tiêu, cơ chế và cấu hình chính.

### Ghi chú thuyết trình

Điểm Logistic sau SMOTE chưa được hiệu chuẩn thành xác suất rời bỏ thực tế. Trong nhánh OLS, không dùng `TotalCharges` để giải thích `MonthlyCharges`; `Churn` và mã khách hàng cũng không thuộc đầu vào.

## Slide 9. Xây dựng, huấn luyện và đánh giá mô hình

### Nội dung trình chiếu

**QUY TRÌNH THỰC HIỆN**

1. Làm sạch, mã hóa và lấy bộ đặc trưng của từng mô hình.
2. Chia Train/Test theo tỷ lệ 80/20; `random_state = 42`.
3. Huấn luyện Decision Tree và hai cấu hình Logistic.
4. Xác nhận chéo phân tầng **5 fold trên Train** cho Logistic.
5. Đánh giá trên Test; lưu mô hình, bảng kết quả và biểu đồ.

**ĐỘ ĐO PHÂN LOẠI**

| Độ đo | Ý nghĩa |
|---|---|
| Accuracy | Tỷ lệ dự đoán đúng trên toàn bộ khách hàng. |
| Precision | Trong số khách được cảnh báo rời bỏ, bao nhiêu thực sự rời bỏ? |
| Recall | Trong số khách thực sự rời bỏ, mô hình phát hiện được bao nhiêu? |
| F1-score | Trung bình điều hòa giữa Precision và Recall. |
| ROC AUC | Khả năng phân biệt hai lớp qua các ngưỡng điểm. |

### Bố cục gợi ý

Hai cột: quy trình bên trái, độ đo bên phải. Nếu cần hình minh họa, dùng [ảnh kiểm định chéo](../images/streamlit-kiem-dinh-cheo.png).

### Ghi chú thuyết trình

Precision, Recall và F1 trong bảng kết quả tiếp theo đều tính cho lớp `Churn = 1`. Pipeline gốc tính CV Recall và CV Accuracy cho Logistic; không mô tả đây là quy trình chọn mô hình bằng F1 CV. CV Recall trung bình của Logistic điều chỉnh là **77,53%**. Kết quả CV và Test có vai trò riêng, không trộn chung.

## Slide 10. Đánh giá kết quả và so sánh mô hình

### Nội dung trình chiếu

**LOGISTIC REGRESSION ĐIỀU CHỈNH**

| Test Recall | Test F1-score | Test ROC AUC |
|---|---|---|
| **76,20%** | **0,6077** | **0,8273** |

**SO SÁNH PHÂN LOẠI TRÊN TẬP TEST**

| Mô hình | Accuracy | Precision | Recall | F1-score | ROC AUC |
|---|---:|---:|---:|---:|---:|
| Decision Tree | 78,25% | 61,33% | 49,20% | 0,5460 | 0,8214 |
| Logistic đầy đủ + SMOTE | 73,06% | 49,58% | 78,07% | 0,6064 | 0,8336 |
| Logistic điều chỉnh + SMOTE | 73,85% | 50,53% | 76,20% | 0,6077 | 0,8273 |

**Nhận xét:** Decision Tree đạt Accuracy và Precision cao hơn; Logistic phát hiện được nhiều khách rời bỏ hơn. Logistic điều chỉnh có F1 nhỉnh hơn trong kết quả này và là mô hình mặc định của pipeline gốc.

**Phân tích phí hàng tháng:** OLS điều chỉnh đạt **R² Test = 0,9689**, **RMSE = 5,2402**.

### Bố cục gợi ý

Giữ kiểu slide 10 của bài mẫu: ba chỉ số lớn phía trên, bảng so sánh ở giữa và nhận xét ngắn phía dưới. Phần OLS đặt thành một dòng riêng.

### Ghi chú thuyết trình

Không khẳng định Logistic điều chỉnh tốt nhất trên mọi tiêu chí: Logistic đầy đủ có Recall và AUC cao hơn. Quyết định sử dụng mô hình còn phụ thuộc chi phí bỏ sót và chi phí chăm sóc nhầm. Không dùng tập Test đã xem nhiều lần làm bằng chứng kiểm thử cuối cùng khi tiếp tục tối ưu mô hình.

## Slide 11. Phân tích ma trận nhầm lẫn

### Nội dung trình chiếu

**LOGISTIC ĐIỀU CHỈNH — 1.407 KHÁCH HÀNG TEST**

| Thực tế / Dự đoán | Ở lại | Rời bỏ |
|---|---:|---:|
| Ở lại | **754 (TN)** | **279 (FP)** |
| Rời bỏ | **89 (FN)** | **285 (TP)** |

- **TP = 285:** phát hiện đúng khách rời bỏ.
- **TN = 754:** nhận diện đúng khách ở lại.
- **FP = 279:** cảnh báo khách thực tế ở lại, làm tăng chi phí rà soát hoặc chăm sóc.
- **FN = 89:** bỏ sót khách thực tế rời bỏ, làm mất cơ hội can thiệp sớm.

**Phát hiện 285/374 khách rời bỏ, tương ứng Recall 76,20%.**

### Bố cục gợi ý

Bên trái giải thích bốn tình huống; bên phải dùng [ma trận Logistic điều chỉnh](../../outputs/figures/confusion_logistic_selected.png). Nhấn màu vào FN và TP.

### Ghi chú thuyết trình

Precision = 285/(285 + 279) = 50,53%. Mô hình phát hiện được nhiều khách rời bỏ nhưng khoảng một nửa số cảnh báo là khách thực tế ở lại. Vì vậy cần kết hợp nguồn lực chăm sóc, tiêu chí kinh doanh và đánh giá ngưỡng phân loại phù hợp.

## Slide 12. Giải thích mô hình và các yếu tố liên quan đến Churn

### Nội dung trình chiếu

**MỨC QUAN TRỌNG TRONG DECISION TREE**

| Đặc trưng | Importance |
|---|---:|
| Hợp đồng theo tháng | 56,61% |
| Thời gian sử dụng `tenure` | 17,93% |
| Internet cáp quang | 16,39% |

**CHIỀU HỆ SỐ TRONG LOGISTIC ĐIỀU CHỈNH**

- Liên quan đến điểm nguy cơ cao hơn: **Internet cáp quang, hợp đồng theo tháng**.
- Liên quan đến điểm nguy cơ thấp hơn: **thời gian sử dụng dài, bảo mật trực tuyến, hợp đồng hai năm**.

**Quan sát dữ liệu:** tỷ lệ Churn của hợp đồng theo tháng là **42,71%**, một năm **11,28%**, hai năm **2,85%**.

### Bố cục gợi ý

Thay phần PFI của bài mẫu bằng giải thích mà dự án đã có: bên trái là ba đặc trưng quan trọng; bên phải là [biểu đồ Churn theo hợp đồng](../../outputs/figures/05_churn_by_Contract.png) hoặc [ảnh hệ số Logistic](../images/streamlit-he-so-logistic.png).

### Ghi chú thuyết trình

Importance của cây được tính từ mức giảm độ hỗn tạp, không phải PFI. Dấu hệ số Logistic mô tả quan hệ trong mô hình, có điều kiện theo các biến còn lại. Các tỷ lệ Churn theo hợp đồng là thống kê mô tả; không kết luận rằng đổi hợp đồng chắc chắn làm giảm Churn. Không đồng nhất hệ số của bộ phân loại sklearn sau SMOTE với hệ số và p-value của mô hình statsmodels fit trên Train gốc.

## Slide 13. Kịch bản bổ sung dữ liệu và huấn luyện lại theo đợt

### Nội dung trình chiếu

**QUY TRÌNH HUẤN LUYỆN LẠI**

1. Chuẩn bị CSV khách hàng mới có đủ thông tin và nhãn `Churn`.
2. Gộp với dữ liệu gốc; ưu tiên bản ghi mới khi trùng `customerID`.
3. Làm sạch, chọn cấu hình tiền xử lý và mô hình trên giao diện.
4. Bấm huấn luyện; lưu cấu hình, chỉ số và mô hình theo từng lần chạy.
5. So sánh kết quả và chủ động chọn mô hình dùng cho dự đoán.

**QUẢN LÝ KẾT QUẢ**

- `outputs/runs/<run_id>/`: hồ sơ và mô hình của từng lần huấn luyện.
- `run.json`: cấu hình, nguồn dữ liệu và kết quả đánh giá.
- `outputs/models/active.json`: lựa chọn mô hình đang dùng.

**Hiện tại:** huấn luyện lại do người dùng khởi chạy trên ứng dụng.

### Bố cục gợi ý

Hai cột như slide 13 của bài mẫu: bên trái là các bước đánh số; bên phải là kết quả lưu và cơ chế chọn mô hình. Dùng [ảnh huấn luyện](../images/streamlit-huan-luyen.png) nếu đủ chỗ.

### Ghi chú thuyết trình

Đây là batch training theo thao tác người dùng. Dự án chưa có lịch tự động hàng tháng hoặc điều kiện tự chạy khi đủ số bản ghi mới. Huấn luyện xong không tự động thay mô hình đang dùng. Dữ liệu mới để huấn luyện phải có nhãn thực tế; nhãn dự đoán không thay thế nhãn thực tế.

## Slide 14. Hệ thống demo và giao diện Streamlit

### Nội dung trình chiếu

| Khám phá dữ liệu | Huấn luyện và so sánh | Dự đoán khách hàng |
|---|---|---|
| Mô tả dữ liệu và chất lượng hồ sơ. | Chọn dữ liệu gốc hoặc bổ sung CSV có nhãn. | Nhập một hồ sơ hoặc tải CSV nhiều khách hàng. |
| Phân bố Churn và các thuộc tính. | Xem tiền xử lý, cấu hình và chạy huấn luyện. | Nhận điểm nguy cơ, nhãn dự đoán và nhóm rủi ro. |
| Phân tích theo hợp đồng, dịch vụ và chi phí. | So sánh kết quả, chọn mô hình dùng dự đoán. | Sắp xếp danh sách cần xem xét và tải kết quả CSV. |

**ĐẦU RA DỰ ĐOÁN**

- `churn_risk_score`: điểm nguy cơ trong khoảng 0–1.
- `predicted_churn`: nhãn Yes/No, ngưỡng mặc định **0,5**.
- `risk_group`: nhóm **Low / Medium / High**.

**Luồng demo:** Dữ liệu → Tiền xử lý → Huấn luyện → So sánh → Dự đoán.

### Bố cục gợi ý

Ba khối ngang như slide 14 của bài mẫu. Khi demo, mở ứng dụng Streamlit và đi theo năm bước trên. Có thể đặt một [ảnh trang dự đoán](../images/streamlit-du-doan.png) lớn thay cho mô tả dài.

### Ghi chú thuyết trình

Mô hình Logistic điều chỉnh mặc định cần 12 trường đầu vào gốc để tạo 16 biến sau mã hóa; yêu cầu đầu vào có thể thay đổi khi chọn mô hình khác. Điểm nguy cơ của Logistic sau SMOTE chưa được hiệu chuẩn xác suất. Các mốc nhóm rủi ro 0,3 và 0,6 hiện mang tính minh họa; theo cách chia khoảng trong mã, Low gồm điểm đến 0,3, Medium trên 0,3 đến 0,6, High trên 0,6. Ngưỡng dự đoán Yes/No được áp dụng trên điểm chưa làm tròn.

## Slide 15. Cảm ơn và hỏi đáp

### Nội dung trình chiếu

# CẢM ƠN!

**GIẢNG VIÊN VÀ CÁC BẠN ĐÃ LẮNG NGHE**

[Tên nhóm] - [Lớp]

**HỎI ĐÁP**

### Bố cục gợi ý

Giữ trang kết thúc đơn giản như bài mẫu: chữ lớn ở giữa, đường kẻ xanh ngọc và thông tin nhóm phía dưới.

### Ghi chú kết thúc

Nhóm đã xây dựng quy trình từ dữ liệu Telco đến mô hình và ứng dụng Streamlit. Kết quả cho thấy sự đánh đổi giữa phát hiện khách rời bỏ và số cảnh báo nhầm. Hướng phát triển là đánh giá ngưỡng theo chi phí kinh doanh, hiệu chuẩn điểm nguy cơ và kiểm thử trên dữ liệu mới.

## Nguồn đối chiếu trong dự án

- [Slide PDF tham khảo](../learn/slide.pdf): thứ tự 15 trang và kiểu bố cục.
- [Kết quả pipeline gốc](../../outputs/metrics.json): chất lượng dữ liệu, chỉ số phân loại, CV và hồi quy.
- [Khai báo đặc trưng](../../src/schema.py): các bộ biến 7/16/10 và trường đầu vào dự đoán.
- [Xử lý dữ liệu](../../src/data.py): làm sạch, mã hóa, loại mã và nhãn khỏi đặc trưng.
- [Huấn luyện mô hình gốc](../../src/models.py): chia tập, SMOTE, chuẩn hóa, CV và cấu hình thuật toán.
- [Báo cáo Logistic điều chỉnh](../../outputs/tables/classification_report_logistic_selected.txt) và [ma trận nhầm lẫn](../../outputs/figures/confusion_logistic_selected.png): đánh giá lớp Churn trên 1.407 mẫu Test.
- [Importance của cây](../../outputs/tables/tree_feature_importance.csv), [hệ số Logistic](../../outputs/tables/logistic_selected_coefficients.csv), [Churn theo nhóm](../../outputs/tables/eda_churn_by_category.csv): nội dung giải thích kết quả.
- [Huấn luyện lại](../../src/retrain.py), [dự đoán](../../predict.py), [ứng dụng Streamlit](../../app.py): chức năng cập nhật, chọn mô hình và giao diện demo.

## Lưu ý khi dựng bản trình chiếu

- Giữ nền trắng, tiêu đề xanh đậm và điểm nhấn xanh ngọc như bài mẫu; dùng một thông điệp chính trên mỗi trang.
- Ưu tiên biểu đồ và bảng kết quả thật; các đường dẫn ảnh ở trên là tài nguyên có sẵn trong dự án.
- Ảnh giao diện có thể thuộc lần chạy hoặc cấu hình khác; trước khi đưa vào slide, đối chiếu số hiển thị với bảng kết quả đã chọn.
- Giữ nguyên sự phân biệt giữa phân loại Churn và hồi quy phí hàng tháng; giữa kết quả pipeline gốc và kết quả huấn luyện lại.
- Điền thông tin giảng viên, nhóm và thành viên trước khi dựng bản cuối.
