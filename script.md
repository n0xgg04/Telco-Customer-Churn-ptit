# Kịch bản thuyết trình demo

Mỗi trang ghi hai phần. **Thao tác** là những gì cần bấm trên web. **Nói** là ý cần trình bày. Web chỉ hiện tiêu đề, biểu đồ và bảng (đánh số Biểu đồ n. / Bảng n. như báo cáo). Phần giải thích do người thuyết trình nói.

Thời lượng gợi ý: Báo cáo khoảng 5 phút, Demo huấn luyện lại khoảng 8 phút.

---

## Phần 1 · Báo cáo

### Mô tả dữ liệu (Chương 2–3)

**Thao tác:** Mở trang *Mô tả dữ liệu*. Ở Biểu đồ 1, lần lượt bấm *Số khách → Đã rời bỏ → Tỷ lệ rời bỏ*.

**Nói:**
- **Bảng 1 · Chất lượng dữ liệu:** bộ dữ liệu IBM Telco có 7.043 quan sát và 21 trường.
  - Giá trị thiếu: TotalCharges có 11 ô trống (0,16% < 5%), nên loại bỏ các dòng này.
  - Không có ngoại lai (IQR × 1,5) và không có dòng trùng lặp.
  - Sau làm sạch còn 7.032 quan sát.
- Tỷ lệ rời bỏ khoảng 26,5% (lớp 0 : lớp 1 ≈ 3 : 1), tức dữ liệu **mất cân bằng lớp**. Phần Demo sẽ xử lý việc này.
- **Biểu đồ 1 · tenure và Contract:** khách dùng dưới 12 tháng rời bỏ khoảng 49%, khách lâu năm chỉ khoảng 17%. Hợp đồng Month-to-month rời bỏ nhiều nhất, Two year gần như không rời bỏ.
- **Bảng 2 · Biến phân loại và biến Churn:** các nhóm rời bỏ cao nhất là Electronic check (45,3%), Month-to-month (42,7%) và Fiber optic (41,9%), khớp mục 4.2.3 của báo cáo.
- **Biểu đồ 2 · tenure × MonthlyCharges:** vùng đậm nhất là khách mới và trả phí tháng cao. Ô xám là nhóm dưới 10 khách nên không đọc tỷ lệ.

### Thống kê mô tả (Chương 4)

**Thao tác:** Lọc *Loại hợp đồng = Theo tháng*, rồi bấm *Đặt lại bộ lọc*. Mở tab *Biến liên tục và Churn*, chọn *tenure*. Mở mục *Tương quan với Churn trên toàn bộ dữ liệu*.

**Nói:**
- Bộ lọc chỉ để quan sát, không ảnh hưởng tới mô hình. Các biểu đồ được tính lại theo tập đang lọc.
- Tab *Biến phân loại và Churn* (mục 4.2.3):
  - Tỷ lệ rời bỏ gần như bằng nhau ở hai giới tính.
  - Khách cao tuổi rời bỏ nhiều hơn; khách có bạn đời hoặc người phụ thuộc rời bỏ ít hơn.
  - Fiber optic, Electronic check, hóa đơn điện tử, không dùng OnlineSecurity/TechSupport đều có tỷ lệ rời bỏ cao.
- Tab *Biến liên tục và Churn* (mục 4.1.2 và 4.2.1):
  - **Histogram:** tenure dồn ở hai đầu (khách mới và khách 60–72 tháng).
  - **Boxplot:** một nửa khách rời bỏ có tenure dưới 10 tháng; khách không rời bỏ có trung vị khoảng 38 tháng. Khách rời bỏ có MonthlyCharges cao hơn (trung vị ≈ 80 so với ≈ 64).
  - **Ma trận tương quan (mục 4.2.2):** tenure – TotalCharges 0,83; MonthlyCharges – TotalCharges 0,65; tenure – MonthlyCharges 0,25.
- Mục *Tương quan với Churn* (mục 4.2.3.2), tính trên toàn bộ dữ liệu:
  - **ANOVA F-test** (biến liên tục): tenure có F-score cao nhất.
  - **Chi-square test** (biến phân loại): Contract_Month-to-month, Contract_Two year, PaymentMethod_Electronic check cao nhất.
  - **Mutual Information:** Contract_Month-to-month, tenure, Contract_Two year cao nhất.
  - **Spearman:** Contract_Month-to-month tương quan dương mạnh nhất; tenure tương quan âm mạnh nhất.

### Kỹ thuật khai phá (Chương 6)

**Thao tác:** Đổi *Chỉ số so sánh* sang Recall (lớp 1). Ở ô *Mô hình*, chọn *Hồi quy logistic (sau điều chỉnh)*, sau đó *Hồi quy logistic (ban đầu)* và *Cây quyết định*. Mở tab *Diễn giải kết quả* và mục *Hồi quy tuyến tính (MonthlyCharges) và thống kê*.

**Nói:**
- Ba kỹ thuật của nhóm, mỗi kỹ thuật một mục tiêu (mục 1.3):
  - **Hồi quy tuyến tính:** giải thích MonthlyCharges theo các dịch vụ.
  - **Cây quyết định:** tìm nhóm khách có nguy cơ rời bỏ cao / khả năng ở lại cao.
  - **Hồi quy logistic:** mô hình dự báo Churn.
- Quy trình: chia 80% huấn luyện / 20% kiểm tra, phân tầng theo Churn, random_state = 42. Hồi quy logistic dùng SMOTE → StandardScaler → huấn luyện; tập kiểm tra không SMOTE.
- Báo cáo phân loại tập trung vào **Recall của lớp 1**: hạn chế tối đa việc bỏ sót khách sắp rời bỏ, chấp nhận một số dự đoán sai.
- Tab *Báo cáo phân loại*, với hồi quy logistic (sau điều chỉnh):
  - Bảng báo cáo phân loại có cùng cấu trúc Bảng 9 trong báo cáo.
  - Lớp 1 đạt Recall 0,76, Precision 0,51, F1-score 0,61; Accuracy 0,74.
  - Cây quyết định có Accuracy cao hơn (0,78) nhưng Recall lớp 1 chỉ 0,49, nên nhóm chọn hồi quy logistic.
- Ma trận nhầm lẫn: hàng là True label, cột là Predicted label. TP là dự đoán đúng lớp 1, FN là bỏ sót lớp 1, FP là dự đoán sai lớp 1, TN là dự đoán đúng lớp 0.
- Stratified K-Fold Cross-Validation 5 fold: Recall các fold khá đều (0,74–0,79), mô hình không bị overfitting.
- Tab *Diễn giải kết quả*:
  - **Hệ số hồi quy logistic:** tenure có hệ số âm lớn nhất (dùng càng lâu càng ít rời bỏ). Fiber optic có hệ số dương; Two year, thanh toán tự động và OnlineSecurity có hệ số âm.
  - **Cây quyết định (max_depth = 4, gini):**
    - Nút gốc là Contract_Month-to-month, biến quan trọng nhất.
    - Nhóm có nguy cơ rời bỏ cao là Month-to-month + Fiber optic + tenure ≤ 1 tháng.
    - Nhóm có khả năng ở lại cao là hợp đồng dài hạn.
- Mục hồi quy tuyến tính:
  - Mô hình ban đầu có R-squared ≈ 0,999, nhưng các biến one-hot có VIF = inf (đa cộng tuyến hoàn hảo).
  - Sau khi điều chỉnh, R-squared ≈ 0,97 và VIF đều thấp.
  - Fiber optic, StreamingTV, StreamingMovies có hệ số lớn nhất với MonthlyCharges.
- McFadden's R-squared của hồi quy logistic khoảng 0,28 (báo cáo: 0,37). Mức 0,2–0,4 được xem là phù hợp tốt.
- Nếu được hỏi vì sao số liệu khác báo cáo một chút (Recall 0,76 so với 0,71): khi chạy lại, nhóm làm SMOTE bên trong từng fold và chỉ trên tập huấn luyện để tránh rò rỉ dữ liệu, nên các chỉ số lệch nhẹ. Kết luận vẫn giữ nguyên.

---

## Phần 2 · Demo huấn luyện lại

Ý chính cần nói trước: khi có dữ liệu khách mới, nhóm gộp vào và huấn luyện lại. Mỗi lần chia dữ liệu và mỗi thuật toán cho kết quả khác nhau, nên cần lưu lại để so sánh rồi chọn mô hình tốt nhất.

### Bước 1 · Dữ liệu

**Thao tác:** Chọn *IBM Telco* làm dữ liệu ban đầu, upload một file CSV vào *Dữ liệu mới* (có thể dùng nút *Tải file mẫu*), rồi bấm **Dùng dữ liệu này**.

**Nói:**
- Dữ liệu mới phải có đủ 21 cột như bộ IBM và có nhãn Churn, vì đây là dữ liệu dùng để huấn luyện.
- Có thể upload nhiều file một lúc.
- Bảng quy mô cho thấy số dòng và tỷ lệ rời bỏ của từng nguồn trước khi làm sạch.

### Bước 2 · Tiền xử lý

**Thao tác:** Giữ mặc định (tập kiểm tra 20%, seed 42, SMOTE). Cuộn qua từng mục 2.1 → 2.6. Sau đó đổi *Phương pháp cân bằng lớp* sang Random undersampling để so sánh, rồi chuyển về SMOTE.

**Nói từng mục:**

| Mục | Ý cần nói |
|---|---|
| 2.1 Gộp dữ liệu | Dữ liệu mới nối sau dữ liệu ban đầu. Nếu trùng customerID thì giữ bản ghi mới (thông tin cập nhật). |
| 2.2 Làm sạch dữ liệu | Đổi TotalCharges sang số; 11 ô trống trở thành giá trị thiếu. Đó là khách mới đăng ký (tenure = 0) nên chưa có tổng phí. Loại các dòng thiếu và mã trùng. |
| 2.3 Mã hóa dữ liệu (one-hot encoding) | Gộp "No internet service" và "No phone service" thành No. Yes/No → 1/0, Male → 1 và Female → 0. InternetService, Contract, PaymentMethod tách thành cột one-hot. So sánh cùng 3 khách trước và sau. |
| 2.4 Chia tập huấn luyện và tập kiểm tra | Chia phân tầng theo Churn để hai tập có cùng tỷ lệ rời bỏ (≈ 26,6%). Seed quyết định cách chia. |
| 2.5 Xử lý mất cân bằng lớp | Biểu đồ "Phân bố các lớp trong tập huấn luyện" giống Biểu đồ 21 của báo cáo. Chỉ xử lý trên **tập huấn luyện**; tập kiểm tra giữ tỷ lệ thật để đánh giá trung thực. Xem phương pháp ở bảng dưới. |
| 2.6 Chuẩn hóa (StandardScaler) | Học trung bình và độ lệch chuẩn trên tập huấn luyện, áp cho cả tập kiểm tra. Sau chuẩn hóa: trung bình 0, độ lệch chuẩn 1. Dùng cho hồi quy logistic, Ridge, Lasso; cây quyết định và OLS không cần. |

Các phương pháp cân bằng lớp:
- **SMOTE:** tạo mẫu rời bỏ mới bằng nội suy giữa một khách rời bỏ và một trong 5 láng giềng gần nhất. Biểu đồ điểm cho thấy mẫu sinh thêm (xám) nằm xen giữa các khách rời bỏ thật (cam), không phải sao chép.
- **Random oversampling:** lặp lại ngẫu nhiên khách rời bỏ cho tới khi hai lớp bằng nhau.
- **Random undersampling:** bỏ bớt mẫu lớp 0 (không rời bỏ), nên mất dữ liệu nhưng huấn luyện nhanh.
- **Class weight:** giữ nguyên dữ liệu, chỉ phạt nặng hơn khi đoán sai khách rời bỏ.

Cấu hình chọn ở bước này được dùng làm mặc định cho Bước 3.

### Bước 3 · Huấn luyện

**Thao tác:** Giữ mặc định (Seed = Cố định 42, đúng cấu hình báo cáo) và bấm **Huấn luyện**: kết quả khớp số liệu trong báo cáo. Sau đó đổi một lựa chọn (ví dụ độ sâu cây, hoặc cân bằng lớp của hồi quy logistic sang Class weight), chọn *Seed = Ngẫu nhiên mỗi lần* rồi bấm **Huấn luyện** thêm hai lần.

**Nói:**
- Ba mô hình nhóm chọn, tham số cố định đúng như báo cáo (các ô bị khóa):
  - **Cây quyết định (Decision Tree):** tiêu chí chia nhánh gini (cố định theo báo cáo), chọn độ sâu tối đa (mặc định 4) và phương pháp cân bằng lớp.
  - **Hồi quy logistic (Logistic Regression):** solver lbfgs, L2, C = 1 (cố định theo báo cáo); chọn phương pháp cân bằng lớp (mặc định SMOTE) và tập đặc trưng.
  - **Hồi quy tuyến tính (Linear Regression):** OLS (cố định theo báo cáo); chọn tập đặc trưng. Biến mục tiêu là MonthlyCharges, không phải Churn.
- Cân bằng lớp nằm trong pipeline nên được làm lại trong từng fold CV, không rò rỉ sang dữ liệu đánh giá.
- Seed ngẫu nhiên khiến mỗi lần chia tập huấn luyện / kiểm tra khác nhau, nên **hai lần bấm cho kết quả khác nhau**. Đây là lý do cần lưu và so sánh. Seed cố định cho kết quả giống hệt khi chạy lại.
- Đọc bảng kết quả và ma trận nhầm lẫn như ở trang Kỹ thuật khai phá.
- Có thể bấm *Dùng mô hình này để dự đoán* ngay tại đây.

### Bước 4 · So sánh

**Thao tác:** Mặc định trang so sánh **lần chạy mới nhất của từng mô hình** (cây quyết định và hồi quy logistic cùng một lần, cùng tập kiểm tra). Ở *Xếp hạng theo*, bấm lần lượt Recall, F1-score, ROC AUC và xem biểu đồ đổi thứ hạng. Bấm **Dùng mô hình tốt nhất**. Nếu muốn dùng mô hình khác, tích ô đầu hàng trong bảng xếp hạng rồi bấm nút *Dùng … cho Bước 5* hiện ra bên dưới.

**Nói:**
- Mặc định so sánh lần chạy mới nhất: hai mô hình phân loại được chấm trên cùng một tập kiểm tra nên công bằng. Chọn *Tất cả các lần chạy* để xem lịch sử học lại và chọn mô hình tốt nhất qua mọi lần.
- Mọi lần huấn luyện đều được lưu và đánh số Lần 1, 2, 3… Cột *Cấu hình* cho biết các lần khác nhau ở đâu: cách cân bằng lớp, số biến, độ sâu cây, seed, có thêm dữ liệu mới hay không.
- Cột *Ghi chú* đánh dấu ★ mô hình tốt nhất theo chỉ số đang chọn và ● mô hình đang được dùng ở Bước 5.
- Chọn chỉ số thì hệ thống tự tìm mô hình tốt nhất trên toàn bộ lịch sử. Nhóm ưu tiên Recall; nếu cần cân bằng cảnh báo sai thì dùng F1.
- Mỗi lần chạy có tập kiểm tra riêng, nên chênh lệch 1–2 điểm % có thể chỉ do cách chia chứ chưa chắc mô hình tốt hơn.
- Hồi quy tuyến tính được so riêng bằng R-squared, RMSE, MAE vì là bài toán hồi quy.
- Có thể tải bảng so sánh CSV để đưa vào báo cáo.

### Bước 5 · Dự đoán

**Thao tác:** Chọn hồ sơ *DEMO001 · thời gian ngắn* rồi bấm **Dự đoán nguy cơ**, sau đó làm lại với DEMO002. Chuyển sang *Hàng loạt qua CSV* và bấm *Chạy thử 3 khách hàng mẫu*.

**Nói:**
- Ô trên cùng ghi mô hình đang dùng, tức mô hình vừa chọn ở Bước 4.
- Điểm rủi ro là điểm của mô hình, không phải xác suất đã hiệu chuẩn. Mô hình học trên dữ liệu đã cân bằng nên điểm thường cao hơn xác suất thật.
- Ngưỡng 0,5 quyết định nhãn Rời bỏ / Không rời bỏ. Mức rủi ro: Thấp ≤ 0,3, Trung bình ≤ 0,6, Cao > 0,6. Vì hai ngưỡng khác nhau nên nhãn và mức có thể lệch (ví dụ điểm 0,55 là Rời bỏ nhưng mức Trung bình).
- Khách mới, hợp đồng theo tháng, cáp quang có điểm cao; khách hợp đồng 2 năm có điểm thấp. Kết quả khớp với phân tích ở phần Báo cáo.
- Không có Internet thì bốn dịch vụ đi kèm phải là Không.
- Dự đoán hàng loạt: file CSV giữ tên cột tiếng Anh như file mẫu, không cần cột Churn. Thêm customerID nếu muốn giữ mã khách. Kết quả tải về được dưới dạng CSV.
- Điểm này không cho biết khách sẽ rời bỏ khi nào.

---

## Kết luận (30 giây)

- Yếu tố liên quan mạnh nhất tới rời bỏ: hợp đồng theo tháng, thời gian dùng ngắn, Internet cáp quang, thanh toán séc điện tử.
- Hồi quy logistic với SMOTE cho Recall lớp 1 tốt nhất (~0,76), phù hợp mục tiêu giữ chân khách.
- Hệ thống cho phép thêm dữ liệu mới, huấn luyện lại với nhiều thuật toán, so sánh, chọn mô hình tốt nhất và trả kết quả dự đoán cho người dùng.
