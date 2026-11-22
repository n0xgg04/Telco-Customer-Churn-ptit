# Telco Churn · Web trình chiếu

Web Vue 3 gồm 15 slide theo [kịch bản thuyết trình](doc/kich-ban.md). Khi mở trang, slide đầu hiển thị ngay trong khung 16:9 vừa với cửa sổ.

## Chạy trên máy

Mở terminal trong thư mục `slide`. Dùng Node.js 20.19+ hoặc 22.12+.

```powershell
npm.cmd install
npm.cmd run dev
```

Mở địa chỉ Vite in trong terminal, mặc định là [http://127.0.0.1:5173](http://127.0.0.1:5173).

- **← / →** hoặc **Page Up / Page Down** để đổi slide. **Space** chuyển tiếp khi con trỏ bàn phím ở nội dung slide. **Home / End** về slide đầu hoặc cuối.
- **F** bật hoặc tắt toàn màn hình của trình duyệt. **Esc** đóng ảnh, đóng bảng bên hoặc thoát toàn màn hình.
- **M** mở mục lục. **N** mở lời thoại. Đưa chuột xuống giữa mép dưới để hiện các nút điều khiển.
- Bấm vào ảnh để phóng to. Nút demo ở slide 14 mở Streamlit trên cổng `8501` theo mặc định. Có thể đặt `VITE_DASHBOARD_URL` trước khi chạy Vite nếu ứng dụng dùng địa chỉ khác.

Ảnh chụp lưu trong [images](images/). Để tạo bản build tĩnh, chạy `npm.cmd run build`. Có thể xem bản build bằng `npm.cmd run preview`.
