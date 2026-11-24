# Hướng dẫn đọc và sử dụng Telco Churn

Dashboard giúp bạn trả lời ba câu hỏi: dữ liệu có gì, mô hình hoạt động ra sao và một khách hàng mới được mô hình chấm điểm như thế nào. Menu bên trái có năm mục. Nên đọc theo thứ tự **Mô tả dữ liệu → Thống kê mô tả → 1–5 Demo huấn luyện lại**; dùng mục **Hướng dẫn sử dụng** để tra cứu.

## 1. Phân biệt số liệu thực tế và dự đoán

**Churn** là việc khách hàng rời bỏ dịch vụ. Trong dữ liệu IBM, `Churn=Yes` là khách đã rời bỏ và `Churn=No` là khách ở lại. Đây là nhãn thực tế được ghi nhận trong bộ dữ liệu.

Các trang Mô tả dữ liệu và Thống kê mô tả thống kê những nhãn này. Trang 5. Dự đoán chấm điểm hồ sơ bạn nhập, chưa biết kết quả thực tế của khách hàng mới.

Một dòng dữ liệu tương ứng một khách hàng; `customerID` chỉ là mã nhận diện và không được dùng làm đặc trưng dự đoán. Dữ liệu là ảnh chụp một thời điểm, không cung cấp lịch sử đủ để dự báo khách sẽ rời bỏ sau bao nhiêu ngày/tháng.

## 2. Mục Mô tả dữ liệu

### Các thẻ số liệu

- **Khách hàng hợp lệ:** số dòng còn lại sau làm sạch. Với dữ liệu hiện tại là 7.032.
- **Đã rời bỏ:** số khách có nhãn thực tế `Yes`. Với dữ liệu hiện tại là 1.869.
- **Tỷ lệ rời bỏ:** số khách đã rời bỏ chia tổng số khách hợp lệ. Hiện tại khoảng 26,6%.
- **Recall mô hình:** khả năng phát hiện khách rời bỏ của Hồi quy logistic (sau điều chỉnh) trên tập kiểm tra. Hiện tại khoảng 75,9%; đây là chỉ số mô hình, không phải tỷ lệ rời bỏ của dữ liệu.

Các thẻ ở Mô tả dữ liệu dùng toàn bộ dữ liệu đã làm sạch. Bộ lọc của mục Thống kê mô tả không thay đổi các thẻ này.

### Chất lượng dữ liệu

Dữ liệu ban đầu có 7.043 dòng. Pipeline chuyển `TotalCharges` sang số, kiểm tra giá trị thiếu và mã khách trùng, sau đó loại các dòng không hợp lệ. Trong kết quả hiện tại, 11 dòng thiếu `TotalCharges` bị loại; không có mã khách trùng.

Biểu đồ tròn cho biết cơ cấu khách ở lại/rời bỏ. Biểu đồ theo hợp đồng thể hiện **tỷ lệ rời bỏ trong từng nhóm**. Ví dụ: nhóm A có 100 khách và 40 người rời bỏ thì tỷ lệ là 40%, không phải 40% tổng khách của cả bộ dữ liệu. Rê chuột để xem cả số khách và số người rời bỏ trong nhóm.

Tỷ lệ quan sát cao trong một nhóm chỉ cho thấy mối liên hệ trong dữ liệu. Không thể từ đó kết luận hợp đồng hay dịch vụ đó là nguyên nhân làm khách rời bỏ.

## 3. Mục Thống kê mô tả

### Bộ lọc

Bạn có thể chọn loại hợp đồng, loại Internet, trạng thái thực tế và khoảng thời gian sử dụng. Các điều kiện được kết hợp đồng thời. Bấm **Đặt lại bộ lọc** để trở về toàn bộ dữ liệu. Chọn rỗng một nhóm điều kiện sẽ cho tập rỗng; ứng dụng thông báo và không vẽ biểu đồ gây hiểu nhầm.

Bộ lọc chỉ thay đổi thống kê trên trang này. Nó không huấn luyện lại mô hình và không làm thay đổi các chỉ số kiểm tra đã lưu.

Các thẻ dưới bộ lọc hiển thị số khách đang xem, tỷ lệ Churn, thời gian sử dụng trung bình và phí hàng tháng trung bình của đúng tập đang lọc. Nếu chỉ chọn nhãn Đã rời bỏ, tỷ lệ Churn sẽ là 100% do điều kiện lọc, không phải do toàn bộ khách hàng đều rời bỏ.

### Tab Nhóm khách hàng

Chọn một thuộc tính như hợp đồng, loại Internet, thanh toán hoặc hỗ trợ kỹ thuật để so sánh. Trục ngang là tỷ lệ Churn; trục dọc là các nhóm. Bảng cạnh biểu đồ bổ sung mẫu số và số người rời bỏ. Nhóm quá ít khách có thể cho tỷ lệ dao động lớn.

### Tab Phân bố & tương quan

- **Histogram:** chia giá trị thành các khoảng rồi đếm số khách trong mỗi khoảng. Màu phân biệt nhãn ở lại/rời bỏ. Đây là số lượng quan sát, không phải tỷ lệ Churn trong khoảng.
- **Boxplot:** đường giữa hộp là trung vị; hộp bao phủ khoảng tứ phân vị Q1 đến Q3, tức 50% quan sát ở giữa. Râu và điểm ngoài râu mô tả độ phân tán theo quy tắc boxplot. Điểm nằm xa chưa chắc là lỗi dữ liệu.
- **Tương quan Pearson:** đo liên hệ tuyến tính giữa `tenure`, `MonthlyCharges`, `TotalCharges`. Hệ số gần +1 là cùng chiều, gần -1 là ngược chiều; gần 0 là liên hệ tuyến tính yếu. Hệ số không thể hiện quan hệ nhân quả. Tổng phí tích lũy liên quan mạnh đến thời gian sử dụng là điều có thể hiểu được từ ý nghĩa hai biến.

Histogram, boxplot và Pearson được tính lại từ tập đang lọc. Khi quá ít quan sát hoặc một biến không thay đổi, tương quan có thể không xác định.

Các hình EDA và bảng kiểm định trong phần mở rộng là kết quả pipeline trên **toàn bộ dữ liệu**, được ghi nhãn riêng và không chạy lại theo bộ lọc:

- **Spearman với Churn:** đo liên hệ theo thứ hạng với nhãn 0/1. Dấu dương nghĩa là giá trị/đặc trưng cao hơn đi cùng Churn nhiều hơn; dấu âm là ngược lại. Giá trị phụ thuộc cách mã hóa đặc trưng.
- **ANOVA F:** kiểm tra sự khác biệt trung bình của biến số giữa hai nhóm Churn. F lớn thể hiện khác biệt mạnh hơn theo kiểm định; p-value nhỏ là bằng chứng chống giả thuyết không có khác biệt, không phải xác suất biến gây ra Churn.
- **Chi-square:** đo mức liên hệ giữa các đặc trưng đã mã hóa không âm và nhãn Churn bằng `sklearn.feature_selection.chi2` trong pipeline. P-value nhỏ thể hiện bằng chứng về liên hệ theo kiểm định; không đo hiệu quả của một chính sách giữ chân.
- **Mutual Information (MI):** lượng thông tin của một biến về nhãn, có thể bắt cả liên hệ phi tuyến. MI cao hơn cho thấy biến có nhiều thông tin hơn trong phép ước lượng này. MI không có dấu âm/dương và không phải phần trăm.

Đây là nhiều phép kiểm định thăm dò; không nên coi một p-value nhỏ riêng lẻ là kết luận kinh doanh hay bằng chứng nhân quả.

### Tab Dữ liệu chi tiết

Tìm theo mã khách hàng và chọn số dòng muốn xem. Nút tải CSV xuất **toàn bộ dữ liệu sau bộ lọc và tìm kiếm**, dù bảng chỉ hiển thị một số dòng. Bảng xem dùng tên tiếng Việt; CSV tải về giữ nguyên tên cột và giá trị tiếng Anh để có thể sử dụng lại trong chương trình.

## 4. Mục Dự đoán

### Dự đoán một khách hàng

Chọn hồ sơ mẫu hoặc nhập thông tin trong ba nhóm: hồ sơ khách hàng, dịch vụ và thanh toán/hợp đồng. Nhãn lựa chọn đã được dịch sang tiếng Việt; chương trình chuyển về đúng giá trị mô hình cần.

`tenure` là **số tháng đã sử dụng dịch vụ**, không phải tuổi. Người phụ thuộc là thông tin về người phụ thuộc của khách. Các ô dịch vụ mô tả khách có đăng ký dịch vụ đó hay không. Nếu không có Internet, các dịch vụ bảo mật/sao lưu/bảo vệ thiết bị/hỗ trợ kỹ thuật không thể được chọn Có.

Bấm **Dự đoán nguy cơ** sau khi nhập xong. Các trường trong biểu mẫu chỉ được gửi khi bấm nút. Kết quả đang hiển thị gắn với hồ sơ ở lần gửi gần nhất; sửa ô nhập rồi chưa gửi sẽ chưa cập nhật kết quả.

Kết quả gồm ba thành phần:

| Thành phần | Ý nghĩa |
|---|---|
| Điểm rủi ro | Điểm từ 0 đến 1 do Hồi quy logistic (sau điều chỉnh) tạo ra; hiển thị dạng % để dễ đọc |
| Nhãn dự đoán | `Yes`/Rời bỏ khi điểm ≥0,5; `No`/Ở lại khi điểm <0,5 |
| Mức rủi ro | Thấp: điểm ≤0,3; Trung bình: 0,3 < điểm ≤0,6; Cao: điểm >0,6 |

Thanh điểm giúp thấy vị trí của điểm trong khoảng 0–1. Bảng hồ sơ dưới kết quả cho phép kiểm tra dữ liệu vừa gửi; nút tải CSV lưu kết quả của hồ sơ đó.

Ngưỡng nhãn 0,5 khác ngưỡng chia ba mức. Ví dụ điểm 0,55 được dự đoán Rời bỏ nhưng vẫn thuộc mức Trung bình. Phân nhóm Low/Medium/High là quy ước minh họa, chưa được tối ưu theo chi phí giữ chân.

**Điểm chưa được hiệu chuẩn xác suất sau SMOTE.** Điểm 90% không có nghĩa chắc chắn rằng 100 khách tương tự sẽ có 90 người rời bỏ. Mô hình cũng không cho biết thời hạn rời bỏ. Không dùng điểm này làm bằng chứng một khách chắc chắn sẽ rời bỏ hoặc một chính sách sẽ làm giảm Churn.

### Dự đoán hàng loạt

Bạn có thể bấm **Chạy thử 3 khách hàng mẫu**, hoặc tải CSV mẫu, sửa dữ liệu rồi tải lên. Sau khi chọn file, bấm **Phân tích CSV**. Kết quả có thẻ tổng số khách, số dự đoán rời bỏ và số khách mức cao. Bộ lọc mức rủi ro và ô tìm mã chỉ lọc bảng kết quả; thẻ tổng và file xuất toàn bộ vẫn thuộc toàn bộ lần dự đoán.

Bảng ưu tiên điểm cao trước. Nút **Tải toàn bộ kết quả CSV** xuất tất cả khách của lần dự đoán, không chỉ những dòng đang xem hoặc mức đang lọc. File xuất giữ các cột gốc và bổ sung `churn_risk_score`, `predicted_churn`, `risk_group`.

Nếu dữ liệu có sẵn `Churn`, cột này không được dùng để dự đoán. Trang dự đoán không tự tính lại độ chính xác từ cột đó. Một file có thêm cột văn bản ngoài schema có thể bị bộ mã hóa hiện tại từ chối; dùng đúng mẫu để tránh lỗi.

### Định dạng CSV bắt buộc

| Cột | Nội dung / giá trị chấp nhận |
|---|---|
| `customerID` | Mã khách, tùy chọn, không đưa vào mô hình |
| `gender` | `Female`, `Male` |
| `Dependents` | `Yes`, `No` |
| `tenure` | Số tháng nguyên không âm |
| `PhoneService` | `Yes`, `No` |
| `OnlineSecurity` | `Yes`, `No`; có thể dùng `No internet service` khi không có Internet |
| `OnlineBackup` | Tương tự `OnlineSecurity` |
| `DeviceProtection` | Tương tự `OnlineSecurity` |
| `TechSupport` | Tương tự `OnlineSecurity` |
| `PaperlessBilling` | `Yes`, `No` |
| `InternetService` | `DSL`, `Fiber optic`, `No` |
| `PaymentMethod` | `Electronic check`, `Mailed check`, `Bank transfer (automatic)`, `Credit card (automatic)` |
| `Contract` | `Month-to-month`, `One year`, `Two year` |

Giữ nguyên tên cột, viết hoa/thường như mẫu và không để trống 12 cột bắt buộc. Dùng CSV phân cách bằng dấu phẩy; không dán nguyên bảng phân cách dấu chấm phẩy. Không cần tự tạo 16 cột dummy: chương trình tự mã hóa và căn đúng các cột của mô hình.

### Từ điển các cột còn lại trong dữ liệu huấn luyện

| Cột | Ý nghĩa |
|---|---|
| `SeniorCitizen` | Cờ khách cao tuổi: 1 có, 0 không, theo nhãn của dữ liệu nguồn |
| `Partner` | Khách có bạn đời hay không |
| `MultipleLines` | Có nhiều đường điện thoại hay không; có thể là `No phone service` |
| `StreamingTV`, `StreamingMovies` | Dịch vụ truyền hình/phim trực tuyến; có thể là `No internet service` |
| `MonthlyCharges` | Phí hàng tháng; giữ đơn vị tiền của dữ liệu gốc, không tự quy đổi sang VND |
| `TotalCharges` | Tổng phí tích lũy; ô trống ở dữ liệu gốc được xử lý trong cleaning |
| `Churn` | Nhãn thực tế Yes/No, bắt buộc khi huấn luyện và không bắt buộc khi dự đoán |

12 cột dự đoán là đầu vào của Hồi quy logistic (sau điều chỉnh). Mô hình này không trực tiếp dùng `MonthlyCharges`, nên biểu mẫu không yêu cầu bạn nhập phí. Điều đó không có nghĩa phí không liên quan tới Churn trong dữ liệu hay trong mô hình đầy đủ/cây.

## 5. Chạy lại và kiểm tra kết quả

Mở PowerShell trong đúng thư mục dự án:

```powershell
cd D:\Telco_Churn_Project_PTIT\telco_churn_project
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Mở URL Terminal hiển thị, thường là `http://localhost:8501`. Nếu ứng dụng đang chạy khi bạn sửa mã, tải lại trang; khi cần dừng tiến trình do bạn khởi chạy trong Terminal, nhấn Ctrl+C.

Để tái tạo kết quả phân tích, chạy:

```powershell
.\.venv\Scripts\python.exe run_pipeline.py
```

Lệnh này ghi lại dữ liệu sạch, bảng, biểu đồ, metrics và mô hình. Sau đó tải lại dashboard. Không cần huấn luyện lại chỉ vì đổi bộ lọc hoặc nhập một hồ sơ mới.

| Tệp / thư mục | Nội dung |
|---|---|
| `data/raw/Telco-Customer-Churn.csv` | Dữ liệu gốc |
| `data/processed/telco_clean.csv` | Dữ liệu sau làm sạch |
| `outputs/metrics.json` | Chất lượng dữ liệu và chỉ số mô hình |
| `outputs/figures/` | Hình EDA, cây quyết định, ma trận nhầm lẫn |
| `outputs/tables/` | Kiểm định, hệ số, VIF, báo cáo phân loại, nhóm lá cây |
| `outputs/models/logistic_selected.joblib` | Pipeline dự đoán được lưu |

Khi thuyết trình, bạn có thể đi theo chuỗi: **bộ dữ liệu → làm sạch → hiện trạng Churn → so sánh các nhóm → đánh giá mô hình → thử dự đoán → giải thích giới hạn của điểm rủi ro**. Mỗi kết luận nên đi cùng mẫu số, phạm vi dữ liệu và chỉ số phù hợp.
